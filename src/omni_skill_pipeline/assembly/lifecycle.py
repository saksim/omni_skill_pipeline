from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from omni_skill_pipeline.models import LifecycleDecision, LifecycleDecisionType
from omni_skill_pipeline.retrieval.similarity import SimilarityResult
from omni_skill_pipeline.utils import unique_preserve_order


def _clamp_score(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass(frozen=True, slots=True)
class LifecyclePolicyThresholds:
    revise_min_similarity: float = 0.78
    merge_min_similarity: float = 0.9
    supersede_min_similarity: float = 0.95
    supersede_min_overall: float = 0.8
    supersede_min_novelty: float = 0.65
    reject_max_overall: float = 0.4
    reject_min_noise: float = 0.9
    reject_max_consistency: float = 0.35

    def to_dict(self) -> dict[str, float]:
        return {
            'revise_min_similarity': self.revise_min_similarity,
            'merge_min_similarity': self.merge_min_similarity,
            'supersede_min_similarity': self.supersede_min_similarity,
            'supersede_min_overall': self.supersede_min_overall,
            'supersede_min_novelty': self.supersede_min_novelty,
            'reject_max_overall': self.reject_max_overall,
            'reject_min_noise': self.reject_min_noise,
            'reject_max_consistency': self.reject_max_consistency,
        }


class LifecycleDecisionEngine(object):
    """TP-E9-02: Decide new/revise/merge/supersede/reject from similarity + quality."""

    def __init__(self, thresholds: LifecyclePolicyThresholds | None = None) -> None:
        self.thresholds = thresholds or LifecyclePolicyThresholds()

    def decide(
        self,
        *,
        similarity_results: Sequence[SimilarityResult],
        quality_scores: Mapping[str, float] | None = None,
        evidence_conflict: bool = False,
    ) -> LifecycleDecision:
        ranked = sorted(similarity_results, key=lambda item: (-float(item.score), str(item.skill_id)))
        quality = self._normalize_quality_scores(quality_scores)

        rejection_reason = self._resolve_reject_reason(quality, evidence_conflict)
        if rejection_reason:
            return self._build_decision(
                decision=LifecycleDecisionType.REJECT,
                reason=rejection_reason,
                related_graph_ids=[item.skill_id for item in ranked[:3]],
                confidence=max(quality['noise_score'], 1.0 - quality['overall_score']),
                quality=quality,
                ranked=ranked,
            )

        if not ranked:
            return self._build_decision(
                decision=LifecycleDecisionType.NEW,
                reason='No similar skill candidates were retrieved.',
                related_graph_ids=[],
                confidence=0.78,
                quality=quality,
                ranked=ranked,
            )

        top = ranked[0]
        top_score = _clamp_score(float(top.score))
        merge_candidates = [item for item in ranked if _clamp_score(item.score) >= self.thresholds.merge_min_similarity]
        revise_candidates = [item for item in ranked if _clamp_score(item.score) >= self.thresholds.revise_min_similarity]

        if (
            top_score >= self.thresholds.supersede_min_similarity
            and quality['overall_score'] >= self.thresholds.supersede_min_overall
            and quality['novelty_score'] >= self.thresholds.supersede_min_novelty
        ):
            return self._build_decision(
                decision=LifecycleDecisionType.SUPERSEDE,
                reason='Top match is near-identical and new output quality/novelty justifies replacement.',
                related_graph_ids=[top.skill_id],
                confidence=top_score,
                quality=quality,
                ranked=ranked,
            )

        if len(merge_candidates) >= 2:
            return self._build_decision(
                decision=LifecycleDecisionType.MERGE,
                reason='Multiple high-similarity skills indicate duplicate branches that should be merged.',
                related_graph_ids=[item.skill_id for item in merge_candidates[:5]],
                confidence=min(0.95, top_score),
                quality=quality,
                ranked=ranked,
            )

        if revise_candidates:
            return self._build_decision(
                decision=LifecycleDecisionType.REVISE,
                reason='A similar skill exists; update the existing branch instead of creating a new one.',
                related_graph_ids=[revise_candidates[0].skill_id],
                confidence=top_score,
                quality=quality,
                ranked=ranked,
            )

        return self._build_decision(
            decision=LifecycleDecisionType.NEW,
            reason='Similarity is below revise threshold; create a new skill branch.',
            related_graph_ids=[],
            confidence=max(0.55, 1.0 - top_score),
            quality=quality,
            ranked=ranked,
        )

    def _resolve_reject_reason(self, quality: dict[str, float], evidence_conflict: bool) -> str:
        if evidence_conflict:
            return 'Evidence conflict detected; lifecycle decision rejected pending manual review.'
        if quality['noise_score'] >= self.thresholds.reject_min_noise:
            return 'Noise score is above reject threshold; evidence is too noisy.'
        if quality['consistency_score'] <= self.thresholds.reject_max_consistency:
            return 'Consistency score is below reject threshold; statements are conflicting.'
        if quality['overall_score'] <= self.thresholds.reject_max_overall:
            return 'Overall quality score is below reject threshold.'
        return ''

    def _normalize_quality_scores(self, quality_scores: Mapping[str, float] | None) -> dict[str, float]:
        payload = quality_scores or {}
        return {
            'overall_score': _clamp_score(float(payload.get('overall_score', 0.7))),
            'noise_score': _clamp_score(float(payload.get('noise_score', 0.2))),
            'consistency_score': _clamp_score(float(payload.get('consistency_score', 0.75))),
            'novelty_score': _clamp_score(float(payload.get('novelty_score', 0.5))),
        }

    def _build_decision(
        self,
        *,
        decision: LifecycleDecisionType,
        reason: str,
        related_graph_ids: Sequence[str],
        confidence: float,
        quality: dict[str, float],
        ranked: Sequence[SimilarityResult],
    ) -> LifecycleDecision:
        return LifecycleDecision(
            decision=decision,
            reason=reason.strip(),
            related_graph_ids=unique_preserve_order(item for item in related_graph_ids if str(item).strip()),
            confidence=_clamp_score(confidence),
            metadata={
                'thresholds': self.thresholds.to_dict(),
                'quality_scores': quality,
                'top_candidates': [
                    {
                        'skill_id': item.skill_id,
                        'score': round(_clamp_score(item.score), 4),
                        'backend': item.backend,
                    }
                    for item in ranked[:5]
                ],
            },
        )
