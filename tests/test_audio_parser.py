from __future__ import annotations

import shutil
import sys
import unittest
from pathlib import Path
from uuid import uuid4

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.adapters.audio import AudioAdapter
from omni_skill_pipeline.extraction.modality.audio_parser import AudioSemanticParser
from omni_skill_pipeline.providers.base import TranscriptSegment, TranscriptionResult
from omni_skill_pipeline.models import AudioDistillRequest, DistillGoal


class _FakeTranscriber(object):
    def transcribe(self, audio_path: Path, *, language: str | None = None, prompt: str | None = None) -> TranscriptionResult:
        return TranscriptionResult(
            text='provider transcript line',
            segments=[TranscriptSegment(text='provider transcript line', start=0.0, end=1.0, confidence=0.9)],
            language=language,
            model_name='fake-transcriber-v1',
        )


class AudioSemanticParserTests(unittest.TestCase):
    def test_parser_distinguishes_question_decision_action_and_context(self) -> None:
        parser = AudioSemanticParser()

        question = parser.parse("Why is latency still high?", "Host")
        decision = parser.parse("We decided to rollback the release.", "PM")
        action_item = parser.parse("Action item: assign Alice to validate metrics.", "Oncall")
        context = parser.parse("The dashboard showed elevated p95 overnight.", "Analyst")

        self.assertEqual(question.utterance_act, "question")
        self.assertEqual(decision.utterance_act, "decision")
        self.assertEqual(action_item.utterance_act, "action_item")
        self.assertEqual(context.utterance_act, "context")
        self.assertEqual(question.speaker_role, "moderator")
        self.assertEqual(decision.speaker_role, "manager")
        self.assertEqual(action_item.speaker_role, "oncall")
        self.assertEqual(context.speaker_role, "participant")

    def test_audio_adapter_emits_semantic_tags_and_counts(self) -> None:
        adapter = AudioAdapter()
        request = AudioDistillRequest(
            title="incident call",
            transcript={
                "segments": [
                    {"speaker": "Host", "text": "Can we confirm the blast radius?"},
                    {"speaker": "PM", "text": "We decided to pause the deploy."},
                    {"speaker": "Oncall", "text": "Action item: assign Bob to patch the alert rule."},
                    {"speaker": "Engineer", "text": "Service recovered after config rollback."},
                ]
            },
            goal=DistillGoal.from_dict({"domain": "incident_response"}),
        )
        loaded = adapter.load(request)

        all_tags = {tag for unit in loaded.evidence_units for tag in unit.tags}
        self.assertIn("utterance_act:question", all_tags)
        self.assertIn("utterance_act:decision", all_tags)
        self.assertIn("utterance_act:action_item", all_tags)
        self.assertIn("utterance_act:context", all_tags)
        self.assertIn("speaker_role:moderator", all_tags)
        self.assertIn("speaker_role:manager", all_tags)
        self.assertIn("speaker_role:oncall", all_tags)
        self.assertIn("speaker_role:engineer", all_tags)

        counts = loaded.adapter_metadata.get("utterance_act_counts", {})
        self.assertEqual(counts.get("question"), 1)
        self.assertEqual(counts.get("decision"), 1)
        self.assertEqual(counts.get("action_item"), 1)
        self.assertEqual(counts.get("context"), 1)

    def test_audio_adapter_ignores_ambiguous_same_stem_text_when_transcriber_available(self) -> None:
        workspace = REPO_ROOT / 'tests' / '.tmp_runtime' / uuid4().hex
        workspace.mkdir(parents=True, exist_ok=True)
        self.addCleanup(lambda: shutil.rmtree(workspace, ignore_errors=True))
        audio_path = workspace / 'incident.wav'
        sidecar_path = workspace / 'incident.md'
        audio_path.write_bytes(b'fake-wav')
        sidecar_path.write_text('primary text asset should not be treated as transcript', encoding='utf-8')

        adapter = AudioAdapter(transcriber=_FakeTranscriber())
        request = AudioDistillRequest(audio_path=str(audio_path), goal=DistillGoal.from_dict({'domain': 'ops'}))
        loaded = adapter.load(request)

        self.assertEqual(loaded.adapter_metadata.get('transcript_source'), 'provider:fake-transcriber-v1')
        self.assertTrue(loaded.adapter_metadata.get('provider_calls'))
        self.assertEqual(loaded.adapter_metadata['provider_calls'][0]['provider'], 'fake-transcriber-v1')

    def test_audio_adapter_prefers_explicit_transcript_sidecar_over_transcriber(self) -> None:
        workspace = REPO_ROOT / 'tests' / '.tmp_runtime' / uuid4().hex
        workspace.mkdir(parents=True, exist_ok=True)
        self.addCleanup(lambda: shutil.rmtree(workspace, ignore_errors=True))
        audio_path = workspace / 'incident.wav'
        sidecar_path = workspace / 'incident.transcript.md'
        audio_path.write_bytes(b'fake-wav')
        sidecar_path.write_text('explicit transcript sidecar', encoding='utf-8')

        adapter = AudioAdapter(transcriber=_FakeTranscriber())
        request = AudioDistillRequest(audio_path=str(audio_path), goal=DistillGoal.from_dict({'domain': 'ops'}))
        loaded = adapter.load(request)

        self.assertEqual(loaded.adapter_metadata.get('transcript_source'), 'incident.transcript.md')
        self.assertFalse(loaded.adapter_metadata.get('provider_calls'))
        self.assertEqual(loaded.evidence_units[0].content, 'explicit transcript sidecar')


if __name__ == "__main__":
    unittest.main()
