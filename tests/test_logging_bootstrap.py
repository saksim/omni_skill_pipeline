from __future__ import annotations

import importlib
import io
import json
import logging
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.logging_utils import configure_logging
from omni_skill_pipeline.models import DistillGoal, TextDistillRequest
from omni_skill_pipeline.service import DistillationService

try:
    from fastapi.testclient import TestClient
except ImportError:  # pragma: no cover
    TestClient = None


class _StubService(object):
    def distill_text(self, request):
        return SimpleNamespace(to_dict=lambda: {'ok': True})

    def distill_audio(self, request):
        return SimpleNamespace(to_dict=lambda: {'ok': True})

    def distill_image(self, request):
        return SimpleNamespace(to_dict=lambda: {'ok': True})

    def distill_tabular(self, request):
        return SimpleNamespace(to_dict=lambda: {'ok': True})

    def distill_video(self, request):
        return SimpleNamespace(to_dict=lambda: {'ok': True})


class _WorkerStubService(object):
    def __init__(self) -> None:
        self.called = False

    def distill_text(self, request):
        self.called = True
        return SimpleNamespace()

    def distill_audio(self, request):  # pragma: no cover - unused in this smoke test
        return SimpleNamespace()

    def distill_image(self, request):  # pragma: no cover - unused in this smoke test
        return SimpleNamespace()

    def distill_tabular(self, request):  # pragma: no cover - unused in this smoke test
        return SimpleNamespace()

    def distill_video(self, request):  # pragma: no cover - unused in this smoke test
        return SimpleNamespace()


class LoggingBootstrapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root_logger = logging.getLogger()
        self._previous_handlers = list(self.root_logger.handlers)
        self._previous_level = self.root_logger.level
        self._previous_signature = getattr(self.root_logger, '_omni_logging_signature', None)

    def tearDown(self) -> None:
        self.root_logger.handlers = self._previous_handlers
        self.root_logger.setLevel(self._previous_level)
        if self._previous_signature is None:
            if hasattr(self.root_logger, '_omni_logging_signature'):
                delattr(self.root_logger, '_omni_logging_signature')
        else:
            self.root_logger._omni_logging_signature = self._previous_signature

    def test_configure_logging_emits_structured_json(self) -> None:
        stream = io.StringIO()
        configure_logging(
            service_name='api',
            level='INFO',
            log_format='json',
            stream=stream,
            force=True,
        )
        logger = logging.getLogger('tests.logging')
        logger.info(
            'logging smoke',
            extra={
                'event': 'logging_smoke',
                'status_code': 200,
            },
        )

        lines = [line for line in stream.getvalue().splitlines() if line.strip()]
        self.assertTrue(lines)
        payload = json.loads(lines[-1])
        self.assertEqual(payload['service'], 'api')
        self.assertEqual(payload['event'], 'logging_smoke')
        self.assertEqual(payload['status_code'], 200)
        self.assertEqual(payload['message'], 'logging smoke')

    def test_configure_logging_is_idempotent_for_same_signature(self) -> None:
        stream = io.StringIO()
        configure_logging(service_name='worker', stream=stream, force=True)
        first_handler = self.root_logger.handlers[0]
        configure_logging(service_name='worker', stream=stream, force=False)
        self.assertEqual(len(self.root_logger.handlers), 1)
        self.assertIs(self.root_logger.handlers[0], first_handler)

    @unittest.skipIf(TestClient is None, 'fastapi testclient is not installed')
    def test_api_app_logs_request_lifecycle_event(self) -> None:
        stream = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            template_path = root / 'SKILL.template.md'
            template_path.write_text('# template', encoding='utf-8')
            draft_dir = root / 'drafts'
            draft_dir.mkdir(parents=True, exist_ok=True)
            settings = SimpleNamespace(
                api_key='',
                rate_limit_requests=0,
                rate_limit_window_seconds=60,
                template_path=template_path,
                draft_dir=draft_dir,
            )

            with (
                patch('omni_skill_pipeline.service.build_service', return_value=_StubService()),
                patch('omni_skill_pipeline.config.load_settings', return_value=settings),
            ):
                module = importlib.import_module('omni_skill_pipeline.api_app')
                module = importlib.reload(module)
                module.configure_logging = lambda *, service_name: configure_logging(
                    service_name=service_name,
                    stream=stream,
                    force=True,
                    log_format='json',
                )
                app = module.create_app()
            client = TestClient(app)
            response = client.get('/healthz')
            self.assertIn(response.status_code, (200, 503))

        events = [json.loads(line) for line in stream.getvalue().splitlines() if line.strip()]
        self.assertTrue(any(item.get('event') == 'api_request_completed' for item in events))

    def test_worker_logs_job_lifecycle_events(self) -> None:
        stream = io.StringIO()
        stub_service = _WorkerStubService()
        module = importlib.import_module('omni_skill_pipeline.worker')
        module = importlib.reload(module)
        module.configure_logging = lambda *, service_name: configure_logging(
            service_name=service_name,
            stream=stream,
            force=True,
            log_format='json',
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            jobs_root = Path(tmp_dir) / 'jobs'
            pending = jobs_root / 'pending'
            pending.mkdir(parents=True, exist_ok=True)
            (pending / 'job_001.json').write_text(
                json.dumps({'kind': 'text', 'content': 'incident timeline'}, ensure_ascii=False),
                encoding='utf-8',
            )
            with patch('omni_skill_pipeline.worker.build_service', return_value=stub_service):
                worker = module.LocalJobWorker(jobs_root)
                processed = worker.run_once()

            self.assertEqual(processed, 1)
            self.assertTrue(stub_service.called)

        events = [json.loads(line) for line in stream.getvalue().splitlines() if line.strip()]
        self.assertTrue(any(item.get('event') == 'worker_job_start' for item in events))
        self.assertTrue(any(item.get('event') == 'worker_job_complete' and item.get('status') == 'completed' for item in events))

    def test_service_emits_start_and_complete_log_events(self) -> None:
        service = DistillationService(
            repository=Mock(),
            text_adapter=Mock(),
            audio_adapter=Mock(),
            image_adapter=Mock(),
            tabular_adapter=Mock(),
            video_adapter=Mock(),
            insight_extractor=Mock(),
            skill_composer=Mock(),
            evidence_builder=Mock(),
            atom_extractor=Mock(),
            skill_graph_builder=Mock(),
            publication_builder=Mock(),
            quality_scorer=Mock(),
            review_policy=Mock(),
            review_feedback_engine=Mock(),
        )
        request = TextDistillRequest(content='incident timeline', goal=DistillGoal(domain='ops'))
        result_bundle = SimpleNamespace(
            skill=SimpleNamespace(skill_id='skill-1'),
            evidence_units=[1, 2, 3],
            publications=[],
            skill_graph=None,
            review_task=None,
            asset=SimpleNamespace(asset_id='asset-1', modality=SimpleNamespace(value='text')),
        )

        with (
            patch('omni_skill_pipeline.service.logger') as logger_mock,
            patch.object(service, '_distill', return_value=result_bundle),
        ):
            bundle = service.distill_text(request)

        self.assertIs(bundle, result_bundle)
        events = [call.kwargs['extra']['event'] for call in logger_mock.info.call_args_list]
        self.assertIn('distill_start', events)
        self.assertIn('distill_complete', events)


if __name__ == '__main__':
    unittest.main()
