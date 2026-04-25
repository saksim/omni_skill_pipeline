from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.assembly.lifecycle import LifecycleDecisionEngine, LifecyclePolicyThresholds
from omni_skill_pipeline.models import LifecycleDecisionType
from omni_skill_pipeline.retrieval.similarity import SimilarityResult


def _candidate(skill_id: str, score: float) -> SimilarityResult:
    return SimilarityResult(
        skill_id=skill_id,
        score=score,
        backend='inmemory',
        metadata={},
    )


class LifecycleDecisionEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = LifecycleDecisionEngine()

    def test_engine_returns_new_when_no_similar_candidates(self) -> None:
        decision = self.engine.decide(similarity_results=[])

        self.assertEqual(decision.decision, LifecycleDecisionType.NEW)
        self.assertEqual(decision.related_graph_ids, [])
        self.assertIn('No similar skill candidates', decision.reason)

    def test_engine_returns_revise_for_single_high_similarity_match(self) -> None:
        decision = self.engine.decide(
            similarity_results=[
                _candidate('skill-existing-1', 0.84),
                _candidate('skill-existing-2', 0.42),
            ]
        )

        self.assertEqual(decision.decision, LifecycleDecisionType.REVISE)
        self.assertEqual(decision.related_graph_ids, ['skill-existing-1'])
        self.assertGreater(decision.confidence, 0.8)

    def test_engine_returns_merge_for_multiple_high_similarity_matches(self) -> None:
        decision = self.engine.decide(
            similarity_results=[
                _candidate('skill-a', 0.93),
                _candidate('skill-b', 0.9),
                _candidate('skill-c', 0.61),
            ]
        )

        self.assertEqual(decision.decision, LifecycleDecisionType.MERGE)
        self.assertEqual(decision.related_graph_ids, ['skill-a', 'skill-b'])
        self.assertIn('duplicate branches', decision.reason)

    def test_engine_returns_supersede_for_near_identical_high_quality_match(self) -> None:
        decision = self.engine.decide(
            similarity_results=[
                _candidate('skill-legacy', 0.97),
                _candidate('skill-alt', 0.65),
            ],
            quality_scores={
                'overall_score': 0.88,
                'noise_score': 0.1,
                'consistency_score': 0.86,
                'novelty_score': 0.72,
            },
        )

        self.assertEqual(decision.decision, LifecycleDecisionType.SUPERSEDE)
        self.assertEqual(decision.related_graph_ids, ['skill-legacy'])
        self.assertIn('replacement', decision.reason)

    def test_engine_returns_reject_for_noisy_or_conflicting_signal(self) -> None:
        noisy_decision = self.engine.decide(
            similarity_results=[_candidate('skill-noisy', 0.96)],
            quality_scores={
                'overall_score': 0.82,
                'noise_score': 0.95,
                'consistency_score': 0.8,
                'novelty_score': 0.7,
            },
        )
        self.assertEqual(noisy_decision.decision, LifecycleDecisionType.REJECT)
        self.assertIn('Noise score', noisy_decision.reason)

        conflict_decision = self.engine.decide(
            similarity_results=[_candidate('skill-conflict', 0.94)],
            evidence_conflict=True,
        )
        self.assertEqual(conflict_decision.decision, LifecycleDecisionType.REJECT)
        self.assertIn('Evidence conflict', conflict_decision.reason)

    def test_engine_allows_threshold_override(self) -> None:
        custom_engine = LifecycleDecisionEngine(
            thresholds=LifecyclePolicyThresholds(
                revise_min_similarity=0.7,
                merge_min_similarity=0.85,
                supersede_min_similarity=0.99,
                supersede_min_overall=0.95,
                supersede_min_novelty=0.9,
                reject_max_overall=0.2,
                reject_min_noise=0.98,
                reject_max_consistency=0.1,
            )
        )

        decision = custom_engine.decide(similarity_results=[_candidate('skill-custom', 0.72)])
        self.assertEqual(decision.decision, LifecycleDecisionType.REVISE)
        self.assertEqual(decision.metadata['thresholds']['revise_min_similarity'], 0.7)


if __name__ == '__main__':
    unittest.main()
