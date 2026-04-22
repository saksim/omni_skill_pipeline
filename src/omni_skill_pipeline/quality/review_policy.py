from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True, slots=True)
class ReviewPolicyThresholds:
    auto_publish_min_overall: float = 0.82
    auto_publish_min_traceability: float = 0.78
    auto_publish_min_actionability: float = 0.72
    auto_publish_min_coverage: float = 0.7
    auto_publish_min_consistency: float = 0.78
    auto_publish_min_noise: float = 0.68
    auto_publish_min_novelty: float = 0.55

    reject_max_overall: float = 0.35
    reject_max_traceability: float = 0.2
    reject_max_actionability: float = 0.22
    reject_max_coverage: float = 0.18
    reject_max_consistency: float = 0.3
    reject_max_noise: float = 0.22

    def to_dict(self) -> dict[str, float]:
        return {
            "auto_publish_min_overall": self.auto_publish_min_overall,
            "auto_publish_min_traceability": self.auto_publish_min_traceability,
            "auto_publish_min_actionability": self.auto_publish_min_actionability,
            "auto_publish_min_coverage": self.auto_publish_min_coverage,
            "auto_publish_min_consistency": self.auto_publish_min_consistency,
            "auto_publish_min_noise": self.auto_publish_min_noise,
            "auto_publish_min_novelty": self.auto_publish_min_novelty,
            "reject_max_overall": self.reject_max_overall,
            "reject_max_traceability": self.reject_max_traceability,
            "reject_max_actionability": self.reject_max_actionability,
            "reject_max_coverage": self.reject_max_coverage,
            "reject_max_consistency": self.reject_max_consistency,
            "reject_max_noise": self.reject_max_noise,
        }


@dataclass(frozen=True, slots=True)
class ReviewPolicyDecision:
    decision: str
    reason_codes: list[str] = field(default_factory=list)
    thresholds: dict[str, float] = field(default_factory=dict)
    score_snapshot: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "decision": self.decision,
            "reason_codes": list(self.reason_codes),
            "thresholds": dict(self.thresholds),
            "score_snapshot": dict(self.score_snapshot),
        }


class ReviewPolicy(object):
    """TP-E7-02 review decision policy with explicit thresholds and reason codes."""

    def __init__(self, thresholds: ReviewPolicyThresholds | None = None) -> None:
        self.thresholds = thresholds or ReviewPolicyThresholds()

    def decide(self, quality_scores: Mapping[str, object]) -> ReviewPolicyDecision:
        score_snapshot = self._coerce_scores(quality_scores)
        reject_codes = self._reject_reason_codes(score_snapshot)
        if reject_codes:
            return ReviewPolicyDecision(
                decision="reject",
                reason_codes=reject_codes,
                thresholds=self.thresholds.to_dict(),
                score_snapshot=score_snapshot,
            )

        if self._can_auto_publish(score_snapshot):
            codes = ["A_MEETS_ALL_THRESHOLDS"]
            if score_snapshot.get("novelty_score", 0.0) >= 0.8:
                codes.append("A_HIGH_NOVELTY")
            return ReviewPolicyDecision(
                decision="auto_publish",
                reason_codes=codes,
                thresholds=self.thresholds.to_dict(),
                score_snapshot=score_snapshot,
            )

        review_codes = self._review_reason_codes(score_snapshot)
        if not review_codes:
            review_codes = ["Q_MANUAL_REVIEW_DEFAULT"]
        return ReviewPolicyDecision(
            decision="review_required",
            reason_codes=review_codes,
            thresholds=self.thresholds.to_dict(),
            score_snapshot=score_snapshot,
        )

    def _coerce_scores(self, quality_scores: Mapping[str, object]) -> dict[str, float]:
        def _to_float(name: str) -> float:
            raw = quality_scores.get(name, 0.0)
            try:
                value = float(raw)
            except (TypeError, ValueError):
                value = 0.0
            return max(0.0, min(1.0, value))

        return {
            "traceability_score": _to_float("traceability_score"),
            "actionability_score": _to_float("actionability_score"),
            "coverage_score": _to_float("coverage_score"),
            "consistency_score": _to_float("consistency_score"),
            "noise_score": _to_float("noise_score"),
            "novelty_score": _to_float("novelty_score"),
            "overall_score": _to_float("overall_score"),
        }

    def _reject_reason_codes(self, scores: Mapping[str, float]) -> list[str]:
        codes: list[str] = []
        if scores["overall_score"] <= self.thresholds.reject_max_overall:
            codes.append("R_LOW_OVERALL")
        if scores["traceability_score"] <= self.thresholds.reject_max_traceability:
            codes.append("R_TRACEABILITY_CRITICAL")
        if scores["actionability_score"] <= self.thresholds.reject_max_actionability:
            codes.append("R_ACTIONABILITY_CRITICAL")
        if scores["coverage_score"] <= self.thresholds.reject_max_coverage:
            codes.append("R_COVERAGE_CRITICAL")
        if scores["consistency_score"] <= self.thresholds.reject_max_consistency:
            codes.append("R_CONSISTENCY_CRITICAL")
        if scores["noise_score"] <= self.thresholds.reject_max_noise:
            codes.append("R_NOISE_CRITICAL")
        return codes

    def _can_auto_publish(self, scores: Mapping[str, float]) -> bool:
        return (
            scores["overall_score"] >= self.thresholds.auto_publish_min_overall
            and scores["traceability_score"] >= self.thresholds.auto_publish_min_traceability
            and scores["actionability_score"] >= self.thresholds.auto_publish_min_actionability
            and scores["coverage_score"] >= self.thresholds.auto_publish_min_coverage
            and scores["consistency_score"] >= self.thresholds.auto_publish_min_consistency
            and scores["noise_score"] >= self.thresholds.auto_publish_min_noise
            and scores["novelty_score"] >= self.thresholds.auto_publish_min_novelty
        )

    def _review_reason_codes(self, scores: Mapping[str, float]) -> list[str]:
        codes: list[str] = []
        if scores["traceability_score"] < self.thresholds.auto_publish_min_traceability:
            codes.append("Q_TRACEABILITY_LOW")
        if scores["actionability_score"] < self.thresholds.auto_publish_min_actionability:
            codes.append("Q_ACTIONABILITY_LOW")
        if scores["coverage_score"] < self.thresholds.auto_publish_min_coverage:
            codes.append("Q_COVERAGE_LOW")
        if scores["consistency_score"] < self.thresholds.auto_publish_min_consistency:
            codes.append("Q_CONSISTENCY_LOW")
        if scores["noise_score"] < self.thresholds.auto_publish_min_noise:
            codes.append("Q_NOISE_HIGH")
        if scores["novelty_score"] < self.thresholds.auto_publish_min_novelty:
            codes.append("Q_NOVELTY_LOW")
        if scores["overall_score"] < self.thresholds.auto_publish_min_overall:
            codes.append("Q_OVERALL_BELOW_AUTO")
        return codes
