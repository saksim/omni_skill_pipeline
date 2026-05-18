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
from omni_skill_pipeline.quality.feedback_consumer import ReviewFeedbackConsumer


class ReviewFeedbackConsumerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.feedback_engine = ReviewFeedbackEngine()
        self.consumer = ReviewFeedbackConsumer()

    def test_consumer_translates_review_required_feedback_to_remediation_plan(self) -> None:
        task = ReviewTask(
            skill_id="skill-feedback-1",
            decision=ReviewDecision.REVIEW_REQUIRED,
            reason_codes=["Q_TRACEABILITY_LOW", "Q_ACTIONABILITY_LOW"],
            revision_suggestions=["S_ADD_TRACEABLE_EVIDENCE", "S_REWRITE_ACTIONABLE_STEPS"],
            status=ReviewStatus.REVIEW_PENDING,
        )
        feedback = self.feedback_engine.build(task)

        plan = self.consumer.consume(feedback)
        payload = plan.to_dict()

        self.assertEqual(payload["review_task_id"], task.review_task_id)
        self.assertEqual(payload["skill_id"], task.skill_id)
        self.assertEqual(payload["next_action"], "run_targeted_remediation")
        self.assertIn("missing_evidence", payload["categories"])
        self.assertIn("non_actionable_steps", payload["categories"])
        self.assertGreaterEqual(len(payload["steps"]), 2)
        action_codes = {item["action_code"] for item in payload["steps"]}
        self.assertIn("ATOM_ADD_EVIDENCE_GROUNDED", action_codes)
        self.assertIn("GRAPH_REWRITE_NON_ACTIONABLE_STEPS", action_codes)

    def test_consumer_auto_publish_feedback_routes_to_monitor_action(self) -> None:
        task = ReviewTask(
            skill_id="skill-feedback-2",
            decision=ReviewDecision.AUTO_PUBLISH,
            reason_codes=["A_MEETS_ALL_THRESHOLDS"],
            revision_suggestions=["S_MONITOR_POST_PUBLISH"],
            status=ReviewStatus.PUBLISHED,
        )
        feedback = self.feedback_engine.build(task)

        payload = self.consumer.consume(feedback).to_dict()

        self.assertEqual(payload["decision"], "auto_publish")
        self.assertEqual(payload["next_action"], "monitor_post_publish")
        self.assertTrue(payload["steps"])

    def test_consumer_falls_back_to_manual_plan_when_feedback_has_no_actions(self) -> None:
        payload = {
            "review_task_id": "task-empty-feedback",
            "skill_id": "skill-feedback-3",
            "decision": "review_required",
            "status": "review_pending",
            "reason_codes": ["Q_MANUAL_REVIEW_DEFAULT"],
            "categories": ["manual_review"],
            "atom_actions": [],
            "graph_actions": [],
            "policy_actions": [],
            "revision_suggestions": [],
            "follow_up_checks": [],
        }

        plan = self.consumer.consume(payload).to_dict()

        self.assertEqual(plan["next_action"], "run_targeted_remediation")
        self.assertEqual(len(plan["steps"]), 1)
        self.assertEqual(plan["steps"][0]["action_code"], "PLAN_MANUAL_REVIEW")
        self.assertEqual(plan["steps"][0]["intent"], "escalate_manual_review")


if __name__ == "__main__":
    unittest.main()
