from __future__ import annotations

import importlib
import sys
import unittest
from pathlib import Path
from typing import Callable
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.exceptions import (
    MediaProcessingError,
    ProviderExecutionError,
    ProviderUnavailableError,
)

try:
    from fastapi.testclient import TestClient
except ImportError:  # pragma: no cover
    TestClient = None


class _StubBundle(object):
    def to_dict(self) -> dict[str, bool]:
        return {'ok': True}


class _StubService(object):
    def __init__(self, error_factories: dict[str, Callable[[], Exception]] | None = None):
        self._error_factories = error_factories or {}

    def _maybe_raise(self, method_name: str) -> None:
        factory = self._error_factories.get(method_name)
        if factory is not None:
            raise factory()

    def distill_text(self, request):
        self._maybe_raise('distill_text')
        return _StubBundle()

    def distill_audio(self, request):
        self._maybe_raise('distill_audio')
        return _StubBundle()

    def distill_image(self, request):
        self._maybe_raise('distill_image')
        return _StubBundle()

    def distill_tabular(self, request):
        self._maybe_raise('distill_tabular')
        return _StubBundle()

    def distill_video(self, request):
        self._maybe_raise('distill_video')
        return _StubBundle()


def _build_client(service: _StubService):
    with patch('omni_skill_pipeline.service.build_service', return_value=service):
        module = importlib.import_module('omni_skill_pipeline.api_app')
        module = importlib.reload(module)
        app = module.create_app()
    return TestClient(app)


@unittest.skipIf(TestClient is None, 'fastapi testclient is not installed')
class ApiErrorMappingTests(unittest.TestCase):
    def _assert_error_shape(
        self,
        response,
        *,
        expected_status: int,
        expected_type: str,
        expected_code: str,
    ) -> None:
        self.assertEqual(response.status_code, expected_status)
        payload = response.json()
        self.assertIn('error', payload)
        self.assertEqual(payload['error']['type'], expected_type)
        self.assertEqual(payload['error']['code'], expected_code)
        self.assertIn('message', payload['error'])
        self.assertIn('details', payload['error'])

    def test_validation_error_returns_422_with_stable_shape(self) -> None:
        client = _build_client(_StubService())
        response = client.post('/v1/distill/text', json={})
        self._assert_error_shape(
            response,
            expected_status=422,
            expected_type='validation',
            expected_code='validation_error',
        )
        self.assertIsInstance(response.json()['error']['details'], list)

    def test_provider_unavailable_error_maps_to_503(self) -> None:
        client = _build_client(
            _StubService(
                {
                    'distill_text': lambda: ProviderUnavailableError('No provider configured.'),
                }
            )
        )
        response = client.post('/v1/distill/text', json={'content': 'timeline'})
        self._assert_error_shape(
            response,
            expected_status=503,
            expected_type='provider',
            expected_code='provider_unavailable',
        )

    def test_provider_execution_error_maps_to_502(self) -> None:
        client = _build_client(
            _StubService(
                {
                    'distill_audio': lambda: ProviderExecutionError('Transcription backend failed.'),
                }
            )
        )
        response = client.post('/v1/distill/audio', json={'transcript': 'recovery'})
        self._assert_error_shape(
            response,
            expected_status=502,
            expected_type='provider',
            expected_code='provider_execution_error',
        )

    def test_media_processing_error_maps_to_502(self) -> None:
        client = _build_client(
            _StubService(
                {
                    'distill_video': lambda: MediaProcessingError('ffmpeg failed.'),
                }
            )
        )
        response = client.post('/v1/distill/video', json={'video_path': 'demo.mp4'})
        self._assert_error_shape(
            response,
            expected_status=502,
            expected_type='provider',
            expected_code='media_processing_error',
        )

    def test_value_error_maps_to_400(self) -> None:
        client = _build_client(
            _StubService(
                {
                    'distill_tabular': lambda: ValueError('Invalid series configuration.'),
                }
            )
        )
        response = client.post('/v1/distill/tabular', json={'file_path': 'metrics.csv'})
        self._assert_error_shape(
            response,
            expected_status=400,
            expected_type='validation',
            expected_code='bad_request',
        )

    def test_runtime_error_maps_to_500(self) -> None:
        client = _build_client(
            _StubService(
                {
                    'distill_image': lambda: RuntimeError('Unexpected renderer crash.'),
                }
            )
        )
        response = client.post('/v1/distill/image', json={'image_path': 'diagram.png'})
        self._assert_error_shape(
            response,
            expected_status=500,
            expected_type='runtime',
            expected_code='runtime_error',
        )


if __name__ == '__main__':
    unittest.main()
