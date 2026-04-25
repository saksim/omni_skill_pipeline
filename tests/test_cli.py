from __future__ import annotations

import importlib
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.models import CorpusDistillRequest


class _StubBundle(object):
    def __init__(self) -> None:
        self.artifacts = {'skill_markdown': 'skills/drafts/demo-corpus/SKILL.md'}


class _CapturingService(object):
    def __init__(self) -> None:
        self.corpus_requests: list[CorpusDistillRequest] = []

    def distill_corpus(self, request: CorpusDistillRequest) -> _StubBundle:
        self.corpus_requests.append(request)
        return _StubBundle()

    def distill_text(self, request):  # pragma: no cover - not used in this test module
        raise AssertionError('Unexpected distill_text call')

    def distill_audio(self, request):  # pragma: no cover - not used in this test module
        raise AssertionError('Unexpected distill_audio call')

    def distill_image(self, request):  # pragma: no cover - not used in this test module
        raise AssertionError('Unexpected distill_image call')

    def distill_tabular(self, request):  # pragma: no cover - not used in this test module
        raise AssertionError('Unexpected distill_tabular call')

    def distill_video(self, request):  # pragma: no cover - not used in this test module
        raise AssertionError('Unexpected distill_video call')


def _run_cli(argv: list[str], service: _CapturingService) -> tuple[int, str]:
    with patch('omni_skill_pipeline.cli.build_service', return_value=service):
        module = importlib.import_module('omni_skill_pipeline.cli')
        module = importlib.reload(module)
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = module.main(argv)
    return exit_code, stdout.getvalue()


class CliCorpusCommandTests(unittest.TestCase):
    def test_distill_corpus_accepts_multiple_asset_args(self) -> None:
        service = _CapturingService()
        exit_code, output = _run_cli(
            [
                'distill-corpus',
                '--name',
                'beta-corpus',
                '--asset',
                'text=examples/text_note.md',
                '--asset',
                'audio=examples/audio_transcript.srt',
                '--tag',
                'beta',
                '--tag',
                'ops',
                '--domain',
                'operations',
            ],
            service,
        )

        self.assertEqual(exit_code, 0)
        self.assertIn('skills/drafts/demo-corpus/SKILL.md', output)
        self.assertEqual(len(service.corpus_requests), 1)
        request = service.corpus_requests[0]
        self.assertIsInstance(request, CorpusDistillRequest)
        self.assertEqual(request.name, 'beta-corpus')
        self.assertEqual(len(request.assets), 2)
        self.assertEqual(request.assets[0].modality.value, 'text')
        self.assertEqual(request.assets[0].source_uri, 'examples/text_note.md')
        self.assertEqual(request.assets[0].role, 'primary')
        self.assertEqual(request.assets[1].modality.value, 'audio')
        self.assertEqual(request.assets[1].source_uri, 'examples/audio_transcript.srt')
        self.assertEqual(request.assets[1].role, 'supporting')
        self.assertEqual(request.goal.domain, 'operations')
        self.assertEqual(request.tags, ['beta', 'ops'])

    def test_distill_corpus_accepts_payload_file(self) -> None:
        payload = {
            'name': 'payload-corpus',
            'assets': [
                {'source_uri': 'file://examples/text_note.md', 'modality': 'text', 'role': 'primary'},
                {'source_uri': 'file://examples/audio_transcript.srt', 'modality': 'audio', 'role': 'supporting'},
            ],
            'goal': {'domain': 'incident-response'},
            'tags': ['payload'],
            'metadata': {'source': 'test'},
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            payload_path = Path(temp_dir) / 'corpus_payload.json'
            payload_path.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')

            service = _CapturingService()
            exit_code, output = _run_cli(
                [
                    'distill-corpus',
                    '--payload-file',
                    str(payload_path),
                ],
                service,
            )

        self.assertEqual(exit_code, 0)
        self.assertIn('skills/drafts/demo-corpus/SKILL.md', output)
        self.assertEqual(len(service.corpus_requests), 1)
        request = service.corpus_requests[0]
        self.assertEqual(request.name, 'payload-corpus')
        self.assertEqual(request.goal.domain, 'incident-response')
        self.assertEqual(len(request.assets), 2)
        self.assertEqual(request.assets[0].modality.value, 'text')
        self.assertEqual(request.assets[1].modality.value, 'audio')
        self.assertEqual(request.tags, ['payload'])
        self.assertEqual(request.metadata, {'source': 'test'})


if __name__ == '__main__':
    unittest.main()
