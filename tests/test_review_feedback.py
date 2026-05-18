from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.models import ReviewDecision, ReviewStatus, ReviewTask
from omni_skill_pipeline.quality.feedback import ReviewFeedbackEngine


class ReviewFeedbackEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = ReviewFeedbackEngine()

    def test_feedback_maps_traceability_and_actionability_to_structured_actions(self) -> None:
        task = ReviewTask(
            skill_id="skill-1",
            decision=ReviewDecision.REVIEW_REQUIRED,
            reason_codes=["Q_TRACEABILITY_LOW", "Q_ACTIONABILITY_LOW"],
            revision_suggestions=["S_ADD_TRACEABLE_EVIDENCE", "S_REWRITE_ACTIONABLE_STEPS"],
            status=ReviewStatus.REVIEW_PENDING,
        )
        payload = self.engine.build(task).to_dict()
        self.assertIn("missing_evidence", payload["categories"])
        self.assertIn("non_actionable_steps", payload["categories"])
        atom_action_codes = {item["action_code"] for item in payload["atom_actions"]}
        graph_action_codes = {item["action_code"] for item in payload["graph_actions"]}
        self.assertIn("ATOM_ADD_EVIDENCE_GROUNDED", atom_action_codes)
        self.assertIn("GRAPH_REWRITE_NON_ACTIONABLE_STEPS", graph_action_codes)
        self.assertIn("CHECK_TRACEABILITY_CHAIN", payload["follow_up_checks"])
        self.assertIn("CHECK_STEP_ACTIONABILITY", payload["follow_up_checks"])

    def test_feedback_maps_reject_to_noise_and_consistency_remediation(self) -> None:
        task = ReviewTask(
            skill_id="skill-2",
            decision=ReviewDecision.REJECT,
            reason_codes=["R_NOISE_CRITICAL", "R_CONSISTENCY_CRITICAL"],
            revision_suggestions=["S_FILTER_NOISY_EVIDENCE", "S_RESOLVE_CONFLICTING_STATEMENTS"],
            status=ReviewStatus.REJECTED,
        )
        payload = self.engine.build(task).to_dict()
        self.assertIn("noise", payload["categories"])
        self.assertIn("incomplete_rules", payload["categories"])
        policy_action_codes = {item["action_code"] for item in payload["policy_actions"]}
        self.assertIn("POLICY_RAISE_NOISE_THRESHOLD", policy_action_codes)
        self.assertIn("POLICY_RAISE_CONSISTENCY_THRESHOLD", policy_action_codes)

    def test_feedback_auto_publish_generates_publish_ready_signal(self) -> None:
        task = ReviewTask(
            skill_id="skill-3",
            decision=ReviewDecision.AUTO_PUBLISH,
            reason_codes=["A_MEETS_ALL_THRESHOLDS"],
            revision_suggestions=["S_MONITOR_POST_PUBLISH"],
            status=ReviewStatus.PUBLISHED,
        )
        payload = self.engine.build(task).to_dict()
        self.assertEqual(payload["decision"], "auto_publish")
        self.assertIn("publish_ready", payload["categories"])
        policy_action_codes = {item["action_code"] for item in payload["policy_actions"]}
        self.assertIn("POLICY_CAPTURE_SUCCESS_PATTERN", policy_action_codes)


if __name__ == "__main__":
    unittest.main()
