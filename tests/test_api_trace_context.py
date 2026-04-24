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
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.logging_utils import configure_logging

try:
    from fastapi.testclient import TestClient
except ImportError:  # pragma: no cover
    TestClient = None


class _StubBundle(object):
    def to_dict(self) -> dict[str, bool]:
        return {'ok': True}


class _TracingService(object):
    def distill_text(self, request):
        logging.getLogger('omni_skill_pipeline.service').info(
            'Tracing service distill invoked.',
            extra={'event': 'distill_start'},
        )
        return _StubBundle()

    def distill_audio(self, request):  # pragma: no cover - unused in this test module
        return _StubBundle()

    def distill_image(self, request):  # pragma: no cover - unused in this test module
        return _StubBundle()

    def distill_tabular(self, request):  # pragma: no cover - unused in this test module
        return _StubBundle()

    def distill_video(self, request):  # pragma: no cover - unused in this test module
        return _StubBundle()


def _build_client(stream: io.StringIO):
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
            patch('omni_skill_pipeline.service.build_service', return_value=_TracingService()),
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
    return TestClient(app)


@unittest.skipIf(TestClient is None, 'fastapi testclient is not installed')
class ApiTraceContextTests(unittest.TestCase):
    def test_request_and_trace_id_headers_propagate_to_logs(self) -> None:
        stream = io.StringIO()
        client = _build_client(stream)

        response = client.post(
            '/v1/distill/text',
            headers={
                'X-Request-ID': 'req-test-001',
                'X-Trace-ID': 'trace-test-001',
            },
            json={'content': 'incident timeline'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get('X-Request-ID'), 'req-test-001')
        self.assertEqual(response.headers.get('X-Trace-ID'), 'trace-test-001')

        events = [json.loads(line) for line in stream.getvalue().splitlines() if line.strip()]
        api_event = next(item for item in events if item.get('event') == 'api_request_completed')
        service_event = next(item for item in events if item.get('event') == 'distill_start')

        self.assertEqual(api_event.get('request_id'), 'req-test-001')
        self.assertEqual(api_event.get('trace_id'), 'trace-test-001')
        self.assertEqual(service_event.get('request_id'), 'req-test-001')
        self.assertEqual(service_event.get('trace_id'), 'trace-test-001')

    def test_request_and_trace_id_are_generated_when_missing(self) -> None:
        stream = io.StringIO()
        client = _build_client(stream)

        response = client.post('/v1/distill/text', json={'content': 'incident timeline'})
        self.assertEqual(response.status_code, 200)

        request_id = str(response.headers.get('X-Request-ID') or '').strip()
        trace_id = str(response.headers.get('X-Trace-ID') or '').strip()
        self.assertTrue(request_id)
        self.assertEqual(trace_id, request_id)

        events = [json.loads(line) for line in stream.getvalue().splitlines() if line.strip()]
        service_event = next(item for item in events if item.get('event') == 'distill_start')
        self.assertEqual(service_event.get('request_id'), request_id)
        self.assertEqual(service_event.get('trace_id'), trace_id)


if __name__ == '__main__':
    unittest.main()
