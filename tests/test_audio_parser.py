from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.adapters.audio import AudioAdapter
from omni_skill_pipeline.extraction.modality.audio_parser import AudioSemanticParser
from omni_skill_pipeline.models import AudioDistillRequest, DistillGoal


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


if __name__ == "__main__":
    unittest.main()
