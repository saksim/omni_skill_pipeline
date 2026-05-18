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
    CorpusDistillRequest,
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

    def distill_corpus(self, request):
        return self._capture('corpus', request)


class _FailingService(_CapturingService):
    def __init__(self, failing_modality: str, failure: Exception) -> None:
        super().__init__()
        self.failing_modality = failing_modality
        self.failure = failure

    def _capture(self, modality: str, request: object) -> _StubBundle:
        if modality == self.failing_modality:
            raise self.failure
        return super()._capture(modality, request)


class _V2StubBundle(object):
    def __init__(self, *, include_review_task: bool) -> None:
        self.include_review_task = include_review_task

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            'asset': {'asset_id': 'asset-1', 'modality': 'text', 'source_uri': 'file://examples/text_note.md', 'metadata': {}},
            'evidence_units': [],
            'insights': [],
            'skill': {
                'skill_id': 'skill-1',
                'name': 'Incident triage',
                'goal': 'convert signals to action',
                'source_modality': 'text',
                'review_status': 'draft',
            },
            'skill_markdown': '# Incident triage\n',
            'skill_graph': {
                'graph_id': 'graph-1',
                'name': 'Incident triage graph',
                'version': '0.1.0',
                'review_status': 'review_pending',
                'steps': [{'node_id': 'step-1'}],
                'decisions': [{'node_id': 'decision-1'}],
                'verifications': [],
                'risks': [],
                'examples': [],
                'variables': [],
                'edges': [{'edge_id': 'edge-1'}],
            },
            'publications': [
                {
                    'publication_type': 'skill_markdown',
                    'path': 'SKILL.md',
                    'publication_id': 'pub-1',
                },
                {
                    'publication_type': 'checklist_json',
                    'path': 'checklist.json',
                    'publication_id': 'pub-2',
                },
            ],
            'adapter_metadata': {
                'lifecycle_decision': {
                    'decision': 'revise',
                    'reason': 'Found similar graph branch.',
                    'related_graph_ids': ['graph-existing-1'],
                    'confidence': 0.91,
                }
            },
            'artifacts': {'skill_markdown': '/tmp/SKILL.md'},
        }
        if self.include_review_task:
            payload['review_task'] = {'status': 'review_pending', 'decision': 'review_required'}
        return payload


class _V2CapturingService(_CapturingService):
    def __init__(self, *, include_review_task: bool = True) -> None:
        super().__init__()
        self.include_review_task = include_review_task

    def distill_corpus(self, request):
        self.requests['corpus'] = request
        return _V2StubBundle(include_review_task=self.include_review_task)


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

    def test_corpus_endpoint_happy_path_with_two_assets(self) -> None:
        request = self._post_and_get_request(
            path='/v1/distill/corpus',
            modality='corpus',
            payload={
                'name': 'beta-ops-corpus',
                'assets': [
                    {
                        'source_uri': 'file://examples/text_note.md',
                        'modality': 'text',
                        'title_hint': 'runbook notes',
                        'role': 'primary',
                        'metadata': {'team': 'sre'},
                    },
                    {
                        'source_uri': 'file://examples/audio_transcript.srt',
                        'modality': 'audio',
                        'title_hint': 'incident call',
                        'role': 'supporting',
                        'metadata': {'lang': 'en'},
                    },
                ],
                'tags': ['beta', 'ops'],
                'metadata': {'source': 'integration-suite'},
                'goal': {'domain': 'operations'},
            },
        )
        self.assertIsInstance(request, CorpusDistillRequest)
        self.assertEqual(request.name, 'beta-ops-corpus')
        self.assertEqual(len(request.assets), 2)
        self.assertEqual(request.assets[0].source_uri, 'file://examples/text_note.md')
        self.assertEqual(request.assets[0].modality.value, 'text')
        self.assertEqual(request.assets[0].role, 'primary')
        self.assertEqual(request.assets[1].source_uri, 'file://examples/audio_transcript.srt')
        self.assertEqual(request.assets[1].modality.value, 'audio')
        self.assertEqual(request.assets[1].role, 'supporting')
        self.assertEqual(request.tags, ['beta', 'ops'])
        self.assertEqual(request.metadata, {'source': 'integration-suite'})
        self.assertEqual(request.goal.domain, 'operations')


@unittest.skipIf(TestClient is None, 'fastapi testclient is not installed')
class ApiAppV2OutputContractTests(unittest.TestCase):
    def _post_corpus(self, client: TestClient):
        return client.post(
            '/v1/distill/corpus',
            json={
                'name': 'v2-contract-corpus',
                'assets': [{'source_uri': 'file://examples/text_note.md', 'modality': 'text'}],
                'goal': {'domain': 'incident_response'},
            },
        )

    def test_corpus_endpoint_returns_v2_summary_fields_and_keeps_legacy_markdown(self) -> None:
        client = _build_client(_V2CapturingService(include_review_task=True))
        response = self._post_corpus(client)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['skill_markdown'], '# Incident triage\n')
        self.assertEqual(payload['graph_metadata']['graph_id'], 'graph-1')
        self.assertEqual(payload['graph_metadata']['node_counts']['steps'], 1)
        self.assertEqual(payload['graph_metadata']['node_counts']['decisions'], 1)
        self.assertEqual(payload['graph_metadata']['node_counts']['edges'], 1)
        self.assertEqual(
            payload['available_publications'],
            [
                {
                    'publication_type': 'skill_markdown',
                    'path': 'SKILL.md',
                    'publication_id': 'pub-1',
                },
                {
                    'publication_type': 'checklist_json',
                    'path': 'checklist.json',
                    'publication_id': 'pub-2',
                },
            ],
        )
        self.assertEqual(payload['review_status'], 'review_pending')
        self.assertEqual(payload['lifecycle_decision']['decision'], 'revise')

    def test_review_status_falls_back_to_skill_review_status_when_review_task_missing(self) -> None:
        client = _build_client(_V2CapturingService(include_review_task=False))
        response = self._post_corpus(client)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['review_status'], 'draft')
        self.assertEqual(payload['skill']['review_status'], 'draft')


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
