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
from omni_skill_pipeline.models import (
    Asset,
    DistillBundle,
    DistillGoal,
    Modality,
    Publication,
    PublicationType,
    ReviewTask,
    SkillDocument,
    SkillGraph,
    StepNode,
    TextDistillRequest,
)
from omni_skill_pipeline.service import DistillationService


class _WorkerTraceProbeService(object):
    def distill_text(self, request):
        logging.getLogger('omni_skill_pipeline.service').info(
            'Service trace probe.',
            extra={'event': 'service_trace_probe'},
        )
        return SimpleNamespace()

    def distill_audio(self, request):  # pragma: no cover - defensive guard
        raise AssertionError('Unexpected distill_audio call')

    def distill_image(self, request):  # pragma: no cover - defensive guard
        raise AssertionError('Unexpected distill_image call')

    def distill_tabular(self, request):  # pragma: no cover - defensive guard
        raise AssertionError('Unexpected distill_tabular call')

    def distill_video(self, request):  # pragma: no cover - defensive guard
        raise AssertionError('Unexpected distill_video call')

    def distill_corpus(self, request):  # pragma: no cover - defensive guard
        raise AssertionError('Unexpected distill_corpus call')


def _write_pending_job(jobs_root: Path, filename: str, payload: dict) -> Path:
    pending_dir = jobs_root / 'pending'
    pending_dir.mkdir(parents=True, exist_ok=True)
    job_path = pending_dir / filename
    job_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return job_path


class TraceObservabilityTpE12Tests(unittest.TestCase):
    def _build_service(self) -> DistillationService:
        return DistillationService(
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

    def test_service_generates_context_and_emits_chain_fields(self) -> None:
        service = self._build_service()
        request = TextDistillRequest(content='incident timeline', goal=DistillGoal(domain='ops'))
        skill = SkillDocument(name='trace-skill', goal='ops', source_modality=Modality.TEXT)
        graph = SkillGraph(
            name='trace-graph',
            goal='ops',
            source_modalities=[Modality.TEXT],
            steps=[StepNode(step=1, action='triage signal')],
        )
        publication = Publication(
            publication_type=PublicationType.SKILL_MARKDOWN,
            content={'text': '# trace'},
        )
        review_task = ReviewTask.from_review_policy(
            skill_id=skill.skill_id,
            review_policy={
                'decision': 'review_required',
                'reason_codes': ['Q_TRACEABILITY_LOW'],
            },
        )
        bundle = DistillBundle(
            asset=Asset(modality=Modality.TEXT, source_uri='inline://trace'),
            evidence_units=[],
            insights=[],
            skill=skill,
            skill_markdown='# trace',
            skill_graph=graph,
            publications=[publication],
            review_task=review_task,
        )

        with (
            patch('omni_skill_pipeline.service.logger') as logger_mock,
            patch.object(service, '_distill', return_value=bundle),
        ):
            result = service.distill_text(request)

        self.assertIs(result, bundle)
        events = [call.kwargs['extra'] for call in logger_mock.info.call_args_list]
        start_event = next(item for item in events if item.get('event') == 'distill_start')
        complete_event = next(item for item in events if item.get('event') == 'distill_complete')

        self.assertTrue(start_event.get('request_id'))
        self.assertTrue(start_event.get('trace_id'))
        self.assertEqual(start_event.get('trace_id'), start_event.get('request_id'))
        self.assertEqual(complete_event.get('request_id'), start_event.get('request_id'))
        self.assertEqual(complete_event.get('trace_id'), start_event.get('trace_id'))
        self.assertEqual(complete_event.get('graph_id'), graph.graph_id)
        self.assertEqual(complete_event.get('publication_count'), 1)
        self.assertEqual(complete_event.get('publication_types'), ['skill_markdown'])
        self.assertEqual(complete_event.get('asset_id'), bundle.asset.asset_id)

    def test_worker_propagates_job_context_to_service_logs(self) -> None:
        stream = io.StringIO()
        worker_module = importlib.import_module('omni_skill_pipeline.worker')
        worker_module = importlib.reload(worker_module)
        worker_module.configure_logging = lambda *, service_name: configure_logging(
            service_name=service_name,
            stream=stream,
            force=True,
            log_format='json',
        )
        service = _WorkerTraceProbeService()

        with tempfile.TemporaryDirectory() as temp_dir:
            jobs_root = Path(temp_dir) / 'jobs'
            _write_pending_job(
                jobs_root,
                'job-trace.json',
                {
                    'kind': 'text',
                    'content': 'trace me',
                },
            )
            with patch.object(worker_module, 'build_service', return_value=service):
                worker = worker_module.LocalJobWorker(jobs_root)
                processed = worker.run_once()

        self.assertEqual(processed, 1)
        events = [json.loads(line) for line in stream.getvalue().splitlines() if line.strip()]
        worker_event = next(item for item in events if item.get('event') == 'worker_job_start')
        service_event = next(item for item in events if item.get('event') == 'service_trace_probe')

        self.assertTrue(worker_event.get('request_id'))
        self.assertTrue(worker_event.get('trace_id'))
        self.assertEqual(worker_event.get('trace_id'), worker_event.get('request_id'))
        self.assertEqual(service_event.get('request_id'), worker_event.get('request_id'))
        self.assertEqual(service_event.get('trace_id'), worker_event.get('trace_id'))

    def test_worker_prefers_payload_context_values(self) -> None:
        stream = io.StringIO()
        worker_module = importlib.import_module('omni_skill_pipeline.worker')
        worker_module = importlib.reload(worker_module)
        worker_module.configure_logging = lambda *, service_name: configure_logging(
            service_name=service_name,
            stream=stream,
            force=True,
            log_format='json',
        )
        service = _WorkerTraceProbeService()

        with tempfile.TemporaryDirectory() as temp_dir:
            jobs_root = Path(temp_dir) / 'jobs'
            _write_pending_job(
                jobs_root,
                'job-trace-explicit.json',
                {
                    'kind': 'text',
                    'content': 'trace me',
                    'request_id': 'req-explicit-001',
                    'trace_id': 'trace-explicit-001',
                },
            )
            with patch.object(worker_module, 'build_service', return_value=service):
                worker = worker_module.LocalJobWorker(jobs_root)
                processed = worker.run_once()

        self.assertEqual(processed, 1)
        events = [json.loads(line) for line in stream.getvalue().splitlines() if line.strip()]
        worker_event = next(item for item in events if item.get('event') == 'worker_job_start')
        service_event = next(item for item in events if item.get('event') == 'service_trace_probe')

        self.assertEqual(worker_event.get('request_id'), 'req-explicit-001')
        self.assertEqual(worker_event.get('trace_id'), 'trace-explicit-001')
        self.assertEqual(service_event.get('request_id'), 'req-explicit-001')
        self.assertEqual(service_event.get('trace_id'), 'trace-explicit-001')


if __name__ == '__main__':
    unittest.main()
