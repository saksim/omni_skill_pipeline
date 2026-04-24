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

from omni_skill_pipeline.exceptions import ProviderExecutionError
from omni_skill_pipeline.models import (
    AudioDistillRequest,
    ImageDistillRequest,
    TabularDistillRequest,
    TextDistillRequest,
    VideoDistillRequest,
)

try:
    from fastapi.testclient import TestClient
except ImportError:  # pragma: no cover
    TestClient = None


class _StubBundle(object):
    def __init__(self, modality: str) -> None:
        self.modality = modality

    def to_dict(self) -> dict[str, object]:
        return {'ok': True, 'modality': self.modality}


class _CapturingService(object):
    def __init__(self) -> None:
        self.requests: dict[str, object] = {}

    def _capture(self, modality: str, request: object) -> _StubBundle:
        self.requests[modality] = request
        return _StubBundle(modality)

    def distill_text(self, request):
        return self._capture('text', request)

    def distill_audio(self, request):
        return self._capture('audio', request)

    def distill_image(self, request):
        return self._capture('image', request)

    def distill_tabular(self, request):
        return self._capture('tabular', request)

    def distill_video(self, request):
        return self._capture('video', request)


class _FailingService(_CapturingService):
    def __init__(self, failing_modality: str, failure: Exception) -> None:
        super().__init__()
        self.failing_modality = failing_modality
        self.failure = failure

    def _capture(self, modality: str, request: object) -> _StubBundle:
        if modality == self.failing_modality:
            raise self.failure
        return super()._capture(modality, request)


def _build_settings(
    *,
    api_key: str = '',
    rate_limit_requests: int = 0,
    rate_limit_window_seconds: int = 60,
) -> SimpleNamespace:
    return SimpleNamespace(
        api_key=api_key,
        rate_limit_requests=rate_limit_requests,
        rate_limit_window_seconds=rate_limit_window_seconds,
        template_path=REPO_ROOT / 'docs' / 'current' / 'contracts' / 'SKILL.template.md',
        draft_dir=REPO_ROOT / 'skills' / 'drafts',
    )


def _build_client(
    service: _CapturingService,
    *,
    api_key: str = '',
    rate_limit_requests: int = 0,
    rate_limit_window_seconds: int = 60,
):
    with (
        patch('omni_skill_pipeline.service.build_service', return_value=service),
        patch(
            'omni_skill_pipeline.config.load_settings',
            return_value=_build_settings(
                api_key=api_key,
                rate_limit_requests=rate_limit_requests,
                rate_limit_window_seconds=rate_limit_window_seconds,
            ),
        ),
    ):
        module = importlib.import_module('omni_skill_pipeline.api_app')
        module = importlib.reload(module)
        app = module.create_app()
    return TestClient(app)


@unittest.skipIf(TestClient is None, 'fastapi testclient is not installed')
class ApiAppHappyPathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.service = _CapturingService()
        cls.client = _build_client(cls.service)

    def _post_and_get_request(self, *, path: str, payload: dict[str, object], modality: str):
        response = self.client.post(path, json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'ok': True, 'modality': modality})
        self.assertIn(modality, self.service.requests)
        return self.service.requests[modality]

    def test_text_endpoint_happy_path(self) -> None:
        request = self._post_and_get_request(
            path='/v1/distill/text',
            modality='text',
            payload={
                'title': 'Shard-1 incident timeline',
                'content': 'CPU spike after deploy.',
                'goal': {'domain': 'sre'},
            },
        )
        self.assertIsInstance(request, TextDistillRequest)
        self.assertEqual(request.title, 'Shard-1 incident timeline')
        self.assertEqual(request.content, 'CPU spike after deploy.')
        self.assertIsNone(request.file_path)
        self.assertEqual(request.goal.domain, 'sre')

    def test_audio_endpoint_happy_path(self) -> None:
        request = self._post_and_get_request(
            path='/v1/distill/audio',
            modality='audio',
            payload={
                'title': 'War-room call',
                'audio_path': 'captures/war-room.wav',
                'transcript': 'Rollback completed.',
                'language': 'en',
                'prompt': 'extract checklist',
                'goal': {'domain': 'incident-response'},
            },
        )
        self.assertIsInstance(request, AudioDistillRequest)
        self.assertEqual(request.title, 'War-room call')
        self.assertEqual(request.audio_path, 'captures/war-room.wav')
        self.assertEqual(request.transcript, 'Rollback completed.')
        self.assertEqual(request.language, 'en')
        self.assertEqual(request.prompt, 'extract checklist')
        self.assertEqual(request.goal.domain, 'incident-response')

    def test_image_endpoint_happy_path(self) -> None:
        request = self._post_and_get_request(
            path='/v1/distill/image',
            modality='image',
            payload={
                'title': 'Error dashboard screenshot',
                'image_path': 'captures/dashboard.png',
                'goal': {'domain': 'observability'},
            },
        )
        self.assertIsInstance(request, ImageDistillRequest)
        self.assertEqual(request.title, 'Error dashboard screenshot')
        self.assertEqual(request.image_path, 'captures/dashboard.png')
        self.assertEqual(request.goal.domain, 'observability')

    def test_tabular_endpoint_happy_path(self) -> None:
        request = self._post_and_get_request(
            path='/v1/distill/tabular',
            modality='tabular',
            payload={
                'title': 'Latency trend',
                'file_path': 'captures/latency.csv',
                'time_column': 'ts',
                'value_columns': ['p95', 'p99'],
                'entity_columns': ['region'],
                'max_series': 4,
                'goal': {'domain': 'performance'},
            },
        )
        self.assertIsInstance(request, TabularDistillRequest)
        self.assertEqual(request.title, 'Latency trend')
        self.assertEqual(request.file_path, 'captures/latency.csv')
        self.assertEqual(request.time_column, 'ts')
        self.assertEqual(request.value_columns, ['p95', 'p99'])
        self.assertEqual(request.entity_columns, ['region'])
        self.assertEqual(request.max_series, 4)
        self.assertEqual(request.goal.domain, 'performance')

    def test_video_endpoint_happy_path(self) -> None:
        request = self._post_and_get_request(
            path='/v1/distill/video',
            modality='video',
            payload={
                'title': 'Failover recording',
                'video_path': 'captures/failover.mp4',
                'transcript': 'Traffic shifted to standby.',
                'language': 'en',
                'prompt': 'extract timeline',
                'keyframe_interval_seconds': 5,
                'max_keyframes': 8,
                'scene_threshold': 0.4,
                'dedupe_distance': 3,
                'goal': {'domain': 'resilience'},
            },
        )
        self.assertIsInstance(request, VideoDistillRequest)
        self.assertEqual(request.title, 'Failover recording')
        self.assertEqual(request.video_path, 'captures/failover.mp4')
        self.assertEqual(request.transcript, 'Traffic shifted to standby.')
        self.assertEqual(request.language, 'en')
        self.assertEqual(request.prompt, 'extract timeline')
        self.assertEqual(request.keyframe_interval_seconds, 5)
        self.assertEqual(request.max_keyframes, 8)
        self.assertAlmostEqual(float(request.scene_threshold), 0.4, places=3)
        self.assertEqual(request.dedupe_distance, 3)
        self.assertEqual(request.goal.domain, 'resilience')


@unittest.skipIf(TestClient is None, 'fastapi testclient is not installed')
class ApiAppErrorPathTests(unittest.TestCase):
    def test_bad_payload_returns_422_validation_error_shape(self) -> None:
        client = _build_client(_CapturingService())
        response = client.post('/v1/distill/text', json={})

        self.assertEqual(response.status_code, 422)
        payload = response.json()['error']
        self.assertEqual(payload['type'], 'validation')
        self.assertEqual(payload['code'], 'validation_error')
        self.assertIn('Request validation failed', payload['message'])

    def test_missing_auth_returns_401_when_api_key_required(self) -> None:
        client = _build_client(_CapturingService(), api_key='top-secret')
        response = client.post('/v1/distill/text', json={'content': 'incident timeline'})

        self.assertEqual(response.status_code, 401)
        payload = response.json()['error']
        self.assertEqual(payload['type'], 'http')
        self.assertEqual(payload['code'], 'http_error')
        self.assertEqual(payload['message'], 'Missing API key.')

    def test_provider_failure_returns_502_with_stable_error_code(self) -> None:
        service = _FailingService(
            failing_modality='audio',
            failure=ProviderExecutionError('transcription backend failed'),
        )
        client = _build_client(service)
        response = client.post('/v1/distill/audio', json={'transcript': 'rollback complete'})

        self.assertEqual(response.status_code, 502)
        payload = response.json()['error']
        self.assertEqual(payload['type'], 'provider')
        self.assertEqual(payload['code'], 'provider_execution_error')
        self.assertIn('transcription backend failed', payload['message'])


if __name__ == '__main__':
    unittest.main()
