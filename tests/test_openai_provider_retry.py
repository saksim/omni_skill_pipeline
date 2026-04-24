from __future__ import annotations

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

from omni_skill_pipeline.providers.openai_provider import OpenAIAudioTranscriber, OpenAIVisionAnalyzer


class _TransientError(Exception):
    def __init__(self, message: str = 'transient failure', status_code: int = 429) -> None:
        super().__init__(message)
        self.status_code = status_code


def _build_settings() -> SimpleNamespace:
    return SimpleNamespace(
        openai_api_key='test-key',
        openai_base_url='https://example.invalid/v1',
        openai_timeout_seconds=42.0,
        openai_retry_max_attempts=3,
        openai_retry_base_delay_seconds=0.25,
        transcription_model='gpt-4o-transcribe',
        transcription_language='en',
        vision_model='gpt-4.1-mini',
        llm_model='gpt-4.1',
    )


class OpenAIProviderRetryTests(unittest.TestCase):
    def test_transcribe_retries_on_transient_failure(self) -> None:
        settings = _build_settings()
        calls = {'count': 0}

        def _create(**kwargs):
            calls['count'] += 1
            if calls['count'] == 1:
                raise _TransientError('rate limited', status_code=429)
            return SimpleNamespace(text='hello', segments=[], language='en', duration=1.0)

        fake_client = SimpleNamespace(
            audio=SimpleNamespace(
                transcriptions=SimpleNamespace(create=_create),
            )
        )
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as file_handle:
            file_handle.write(b'fake-audio')
            audio_path = Path(file_handle.name)
        self.addCleanup(lambda: audio_path.unlink(missing_ok=True))

        with (
            patch('omni_skill_pipeline.providers.openai_provider.OpenAI', return_value=fake_client),
            patch('omni_skill_pipeline.providers.openai_provider.time.sleep') as mocked_sleep,
        ):
            transcriber = OpenAIAudioTranscriber(settings)
            result = transcriber.transcribe(audio_path)

        self.assertEqual(result.text, 'hello')
        self.assertEqual(calls['count'], 2)
        mocked_sleep.assert_called_once_with(0.25)

    def test_responses_create_retries_for_vision_analyze(self) -> None:
        settings = _build_settings()
        calls = {'count': 0}

        def _create(**kwargs):
            calls['count'] += 1
            if calls['count'] == 1:
                raise _TransientError('upstream unavailable', status_code=503)
            return SimpleNamespace(output_text='detected entities')

        fake_client = SimpleNamespace(
            responses=SimpleNamespace(
                create=_create,
            )
        )
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as file_handle:
            file_handle.write(b'\x89PNG\r\n\x1a\n')
            image_path = Path(file_handle.name)
        self.addCleanup(lambda: image_path.unlink(missing_ok=True))

        with (
            patch('omni_skill_pipeline.providers.openai_provider.OpenAI', return_value=fake_client),
            patch('omni_skill_pipeline.providers.openai_provider.time.sleep') as mocked_sleep,
        ):
            analyzer = OpenAIVisionAnalyzer(settings)
            result = analyzer.analyze(image_path)

        self.assertEqual(result.summary, 'detected entities')
        self.assertEqual(calls['count'], 2)
        mocked_sleep.assert_called_once_with(0.25)

    def test_responses_parse_retries_for_vision_ocr(self) -> None:
        settings = _build_settings()
        calls = {'count': 0}

        def _parse(**kwargs):
            calls['count'] += 1
            if calls['count'] == 1:
                raise _TransientError('temporary gateway', status_code=502)
            parsed = SimpleNamespace(text='line-a\nline-b', lines=['line-a', 'line-b'])
            return SimpleNamespace(output_parsed=parsed)

        fake_client = SimpleNamespace(
            responses=SimpleNamespace(
                parse=_parse,
            )
        )
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as file_handle:
            file_handle.write(b'\x89PNG\r\n\x1a\n')
            image_path = Path(file_handle.name)
        self.addCleanup(lambda: image_path.unlink(missing_ok=True))

        with (
            patch('omni_skill_pipeline.providers.openai_provider.OpenAI', return_value=fake_client),
            patch('omni_skill_pipeline.providers.openai_provider.time.sleep') as mocked_sleep,
        ):
            analyzer = OpenAIVisionAnalyzer(settings)
            result = analyzer.extract(image_path)

        self.assertEqual(result.text, 'line-a\nline-b')
        self.assertEqual(calls['count'], 2)
        mocked_sleep.assert_called_once_with(0.25)


if __name__ == '__main__':
    unittest.main()
