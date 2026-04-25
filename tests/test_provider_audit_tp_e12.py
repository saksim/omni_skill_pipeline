from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.adapters.audio import AudioAdapter
from omni_skill_pipeline.adapters.text import TextAdapter
from omni_skill_pipeline.models import CorpusAssetInput, CorpusDistillRequest, DistillGoal, Modality
from omni_skill_pipeline.pipeline import HeuristicInsightExtractor, HeuristicSkillComposer
from omni_skill_pipeline.providers.base import TranscriptSegment, TranscriptionResult
from omni_skill_pipeline.providers.openai_provider import OpenAIVisionAnalyzer
from omni_skill_pipeline.repository import FileArtifactRepository
from omni_skill_pipeline.service import DistillationService


class _TransientError(Exception):
    def __init__(self, message: str, *, status_code: int = 503) -> None:
        super().__init__(message)
        self.status_code = status_code


class _FakeTranscriber(object):
    def transcribe(self, audio_path: Path, *, language: str | None = None, prompt: str | None = None) -> TranscriptionResult:
        return TranscriptionResult(
            text='Rebuild incident timeline and verify recovery.',
            segments=[
                TranscriptSegment(text='Rebuild incident timeline.', start=0.0, end=2.0, confidence=0.9),
                TranscriptSegment(text='Verify recovery and watch error rate.', start=2.0, end=4.0, confidence=0.88),
            ],
            language=language,
            model_name='fake-transcriber-v1',
        )


class _UnsupportedAdapter(object):
    def load(self, request):  # pragma: no cover - guard path
        raise AssertionError('Unexpected adapter invocation in provider audit tests.')


def _build_openai_settings() -> SimpleNamespace:
    return SimpleNamespace(
        openai_api_key='test-key',
        openai_base_url='https://example.invalid/v1',
        openai_timeout_seconds=25.0,
        openai_retry_max_attempts=3,
        openai_retry_base_delay_seconds=0.1,
        openai_circuit_breaker_consecutive_failures=3,
        openai_circuit_breaker_cooldown_seconds=30.0,
        openai_failure_budget_max_failures=6,
        openai_failure_budget_window_seconds=60.0,
        transcription_model='gpt-4o-transcribe',
        transcription_language='en',
        vision_model='gpt-4.1-mini',
        llm_model='gpt-4.1',
    )


class ProviderAuditTpE12Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace = REPO_ROOT / 'tests' / '.tmp_runtime' / uuid4().hex
        self.workspace.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.workspace, ignore_errors=True)

    def test_openai_mixin_emits_provider_call_audit_snapshot(self) -> None:
        settings = _build_openai_settings()
        calls = {'count': 0}

        def _create(**kwargs):
            calls['count'] += 1
            if calls['count'] == 1:
                raise _TransientError('temporary provider issue', status_code=503)
            return SimpleNamespace(output_text='image summary')

        fake_client = SimpleNamespace(
            responses=SimpleNamespace(create=_create),
        )

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as file_handle:
            file_handle.write(b'\x89PNG\r\n\x1a\n')
            image_path = Path(file_handle.name)
        self.addCleanup(lambda: image_path.unlink(missing_ok=True))

        with (
            patch('omni_skill_pipeline.providers.openai_provider.OpenAI', return_value=fake_client),
            patch('omni_skill_pipeline.providers.openai_provider.time.sleep'),
        ):
            analyzer = OpenAIVisionAnalyzer(settings)
            analyzer.analyze(image_path)
            snapshot = analyzer.provider_call_audit_snapshot()

        self.assertEqual(snapshot['provider'], 'openai')
        self.assertEqual(snapshot['component'], 'OpenAIVisionAnalyzer')
        self.assertEqual(snapshot['totals']['calls'], 1)
        self.assertEqual(snapshot['totals']['attempts'], 2)
        self.assertEqual(snapshot['totals']['retries'], 1)
        self.assertEqual(snapshot['totals']['successes'], 1)
        self.assertEqual(snapshot['totals']['failures'], 0)
        self.assertIn('vision analysis', snapshot['operations'])
        self.assertEqual(snapshot['operations']['vision analysis']['attempts'], 2)
        self.assertEqual(snapshot['operations']['vision analysis']['successes'], 1)

    def test_service_distill_corpus_emits_provider_footprint(self) -> None:
        text_file = self.workspace / 'incident.md'
        text_file.write_text(
            '\n'.join(
                [
                    '# Incident Timeline',
                    '1. Build the timeline from logs.',
                    '2. Verify recovery with latency and error budget.',
                ]
            ),
            encoding='utf-8',
        )
        audio_file = self.workspace / 'incident.wav'
        audio_file.write_bytes(b'fake-wav')

        service = DistillationService(
            repository=FileArtifactRepository(self.workspace / 'drafts'),
            text_adapter=TextAdapter(),
            audio_adapter=AudioAdapter(transcriber=_FakeTranscriber()),
            image_adapter=_UnsupportedAdapter(),
            tabular_adapter=_UnsupportedAdapter(),
            video_adapter=_UnsupportedAdapter(),
            insight_extractor=HeuristicInsightExtractor(),
            skill_composer=HeuristicSkillComposer(),
        )
        request = CorpusDistillRequest(
            name='provider-audit-corpus',
            assets=[
                CorpusAssetInput(source_uri=str(text_file), modality=Modality.TEXT, role='primary'),
                CorpusAssetInput(source_uri=str(audio_file), modality=Modality.AUDIO, role='context'),
            ],
            goal=DistillGoal.from_dict({'domain': 'incident_response'}),
        )

        bundle = service.distill_corpus(request)
        footprint = bundle.adapter_metadata['provider_footprint']

        self.assertEqual(footprint['corpus_id'], bundle.corpus.corpus_id if bundle.corpus is not None else '')
        self.assertEqual(len(footprint['asset_breakdown']), 2)
        self.assertGreaterEqual(footprint['summary']['total_calls'], 1)
        self.assertIn('fake-transcriber-v1', footprint['summary']['providers'])
        self.assertGreaterEqual(footprint['summary']['providers']['fake-transcriber-v1']['calls'], 1)
        audio_assets = [item for item in footprint['asset_breakdown'] if item.get('modality') == 'audio']
        self.assertEqual(len(audio_assets), 1)
        self.assertTrue(audio_assets[0]['provider_calls'])
        self.assertTrue(any(item.get('provider') == 'fake-transcriber-v1' for item in audio_assets[0]['provider_calls']))


if __name__ == '__main__':
    unittest.main()
