from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.quality.review_policy import ReviewPolicy


class ReviewPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = ReviewPolicy()

    def test_auto_publish_when_all_scores_high(self) -> None:
        decision = self.policy.decide(
            {
                "traceability_score": 0.92,
                "actionability_score": 0.9,
                "coverage_score": 0.88,
                "consistency_score": 0.9,
                "noise_score": 0.85,
                "novelty_score": 0.82,
                "overall_score": 0.89,
            }
        ).to_dict()
        self.assertEqual(decision["decision"], "auto_publish")
        self.assertIn("A_MEETS_ALL_THRESHOLDS", decision["reason_codes"])

    def test_reject_when_scores_are_critical(self) -> None:
        decision = self.policy.decide(
            {
                "traceability_score": 0.1,
                "actionability_score": 0.18,
                "coverage_score": 0.12,
                "consistency_score": 0.2,
                "noise_score": 0.15,
                "novelty_score": 0.25,
                "overall_score": 0.2,
            }
        ).to_dict()
        self.assertEqual(decision["decision"], "reject")
        self.assertIn("R_LOW_OVERALL", decision["reason_codes"])
        self.assertIn("R_NOISE_CRITICAL", decision["reason_codes"])

    def test_review_required_when_between_auto_and_reject(self) -> None:
        decision = self.policy.decide(
            {
                "traceability_score": 0.72,
                "actionability_score": 0.63,
                "coverage_score": 0.7,
                "consistency_score": 0.74,
                "noise_score": 0.71,
                "novelty_score": 0.41,
                "overall_score": 0.69,
            }
        ).to_dict()
        self.assertEqual(decision["decision"], "review_required")
        self.assertIn("Q_OVERALL_BELOW_AUTO", decision["reason_codes"])
        self.assertIn("Q_NOVELTY_LOW", decision["reason_codes"])
        self.assertIn("thresholds", decision)
        self.assertIn("score_snapshot", decision)


if __name__ == "__main__":
    unittest.main()
