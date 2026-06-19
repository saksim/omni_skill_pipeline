from __future__ import annotations

import importlib
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

try:
    from fastapi.testclient import TestClient
except ImportError:  # pragma: no cover
    TestClient = None


class _StubBundle(object):
    def to_dict(self) -> dict[str, bool]:
        return {'ok': True}


class _StubService(object):
    def distill_text(self, request):  # pragma: no cover - request shape handled by app validation
        return _StubBundle()

    def distill_audio(self, request):  # pragma: no cover - request shape handled by app validation
        return _StubBundle()

    def distill_image(self, request):  # pragma: no cover - request shape handled by app validation
        return _StubBundle()

    def distill_tabular(self, request):  # pragma: no cover - request shape handled by app validation
        return _StubBundle()

    def distill_video(self, request):  # pragma: no cover - request shape handled by app validation
        return _StubBundle()

    def distill_corpus(self, request):  # pragma: no cover - request shape handled by app validation
        return _StubBundle()

    repository = object()


def _build_settings():
    return SimpleNamespace(
        api_key='',
        rate_limit_requests=0,
        rate_limit_window_seconds=60,
        tenant_access_json='',
        tenant_access_file='',
        template_path=REPO_ROOT / 'docs' / 'latest' / 'contracts' / 'SKILL.template.md',
        draft_dir=REPO_ROOT / 'skills' / 'drafts',
    )


def _build_client():
    with (
        patch('omni_skill_pipeline.service.build_service', return_value=_StubService()),
        patch('omni_skill_pipeline.config.load_settings', return_value=_build_settings()),
    ):
        module = importlib.import_module('omni_skill_pipeline.api_app')
        module = importlib.reload(module)
        app = module.create_app()
    return TestClient(app)


@unittest.skipIf(TestClient is None, 'fastapi testclient is not installed')
class ApiAppValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = _build_client()

    def _assert_4xx(self, path: str, payload: dict) -> int:
        response = self.client.post(path, json=payload)
        self.assertGreaterEqual(response.status_code, 400)
        self.assertLess(response.status_code, 500)
        return response.status_code

    def test_invalid_payloads_are_rejected_with_4xx(self) -> None:
        invalid_cases = (
            ('/v1/distill/text', {}),
            ('/v1/distill/audio', {}),
            ('/v1/distill/image', {}),
            ('/v1/distill/tabular', {'file_path': 'metrics.csv', 'max_series': 0}),
            ('/v1/distill/video', {'video_path': 'capture.mp4', 'scene_threshold': 1.5}),
            ('/v1/distill/corpus', {}),
        )
        for path, payload in invalid_cases:
            self._assert_4xx(path, payload)

    def test_schema_validation_failures_return_422(self) -> None:
        invalid_cases = (
            ('/v1/distill/text', {}),
            ('/v1/distill/audio', {}),
            ('/v1/distill/image', {}),
            ('/v1/distill/tabular', {'file_path': 'metrics.csv', 'max_series': 0}),
            ('/v1/distill/video', {'video_path': 'capture.mp4', 'scene_threshold': 1.5}),
            ('/v1/distill/corpus', {}),
        )
        for path, payload in invalid_cases:
            self.assertEqual(self._assert_4xx(path, payload), 422)

    def test_openapi_request_body_uses_schema_models(self) -> None:
        openapi = self.client.app.openapi()

        expected_paths = (
            ('/v1/distill/text', 'TextDistillRequestSchema'),
            ('/v1/distill/audio', 'AudioDistillRequestSchema'),
            ('/v1/distill/image', 'ImageDistillRequestSchema'),
            ('/v1/distill/tabular', 'TabularDistillRequestSchema'),
            ('/v1/distill/video', 'VideoDistillRequestSchema'),
            ('/v1/distill/corpus', 'CorpusDistillRequestSchema'),
        )
        for path, schema_name in expected_paths:
            ref = openapi['paths'][path]['post']['requestBody']['content']['application/json']['schema']['$ref']
            self.assertIn(schema_name, ref)

    def test_valid_payloads_keep_endpoint_callable(self) -> None:
        valid_cases = (
            ('/v1/distill/text', {'content': 'incident timeline'}),
            ('/v1/distill/audio', {'transcript': 'verify recovery'}),
            ('/v1/distill/image', {'image_path': 'artifacts/diagram.png'}),
            ('/v1/distill/tabular', {'file_path': 'artifacts/latency.csv'}),
            ('/v1/distill/video', {'video_path': 'artifacts/demo.mp4'}),
            (
                '/v1/distill/corpus',
                {
                    'name': 'release-readiness',
                    'assets': [
                        {'source_uri': 'file://examples/text_note.md', 'modality': 'text'},
                        {'source_uri': 'file://examples/audio_transcript.srt', 'modality': 'audio', 'role': 'supporting'},
                    ],
                },
            ),
        )
        for path, payload in valid_cases:
            response = self.client.post(path, json=payload)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {'ok': True})


if __name__ == '__main__':
    unittest.main()
