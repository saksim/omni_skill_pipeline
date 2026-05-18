from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from omni_skill_pipeline.models import ReviewDecision, ReviewTask
from omni_skill_pipeline.utils import unique_preserve_order


@dataclass(frozen=True, slots=True)
class ReviewFeedback:
    review_task_id: str
    skill_id: str
    decision: str
    status: str
    reason_codes: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    atom_actions: list[dict[str, Any]] = field(default_factory=list)
    graph_actions: list[dict[str, Any]] = field(default_factory=list)
    policy_actions: list[dict[str, Any]] = field(default_factory=list)
    revision_suggestions: list[str] = field(default_factory=list)
    follow_up_checks: list[str] = field(default_factory=list)
    score_snapshot: dict[str, float] = field(default_factory=dict)
    thresholds: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "review_task_id": self.review_task_id,
            "skill_id": self.skill_id,
            "decision": self.decision,
            "status": self.status,
            "reason_codes": list(self.reason_codes),
            "categories": list(self.categories),
            "atom_actions": [dict(item) for item in self.atom_actions],
            "graph_actions": [dict(item) for item in self.graph_actions],
            "policy_actions": [dict(item) for item in self.policy_actions],
            "revision_suggestions": list(self.revision_suggestions),
            "follow_up_checks": list(self.follow_up_checks),
            "score_snapshot": dict(self.score_snapshot),
            "thresholds": dict(self.thresholds),
        }


class ReviewFeedbackEngine(object):
    """TP-E7-04: translate review result into structured remediation signals."""

    def build(self, review_task: ReviewTask) -> ReviewFeedback:
        categories: list[str] = []
        atom_actions: list[dict[str, Any]] = []
        graph_actions: list[dict[str, Any]] = []
        policy_actions: list[dict[str, Any]] = []
        follow_up_checks: list[str] = []

        for reason_code in unique_preserve_order(review_task.reason_codes):
            self._collect_reason_actions(
                reason_code=reason_code,
                categories=categories,
                atom_actions=atom_actions,
                graph_actions=graph_actions,
                policy_actions=policy_actions,
                follow_up_checks=follow_up_checks,
            )

        if not categories:
            self._collect_default_actions(
                decision=review_task.decision,
                categories=categories,
                policy_actions=policy_actions,
                follow_up_checks=follow_up_checks,
            )

        atom_actions = self._dedupe_actions(atom_actions)
        graph_actions = self._dedupe_actions(graph_actions)
        policy_actions = self._dedupe_actions(policy_actions)

        return ReviewFeedback(
            review_task_id=review_task.review_task_id,
            skill_id=review_task.skill_id,
            decision=review_task.decision.value,
            status=review_task.status.value,
            reason_codes=unique_preserve_order(review_task.reason_codes),
            categories=unique_preserve_order(categories),
            atom_actions=atom_actions,
            graph_actions=graph_actions,
            policy_actions=policy_actions,
            revision_suggestions=unique_preserve_order(review_task.revision_suggestions),
            follow_up_checks=unique_preserve_order(follow_up_checks),
            score_snapshot=dict(review_task.score_snapshot),
            thresholds=dict(review_task.thresholds),
        )

    def _collect_reason_actions(
        self,
        *,
        reason_code: str,
        categories: list[str],
        atom_actions: list[dict[str, Any]],
        graph_actions: list[dict[str, Any]],
        policy_actions: list[dict[str, Any]],
        follow_up_checks: list[str],
    ) -> None:
        if reason_code in {"R_NOISE_CRITICAL", "Q_NOISE_HIGH"}:
            categories.append("noise")
            atom_actions.append(
                {
                    "action_code": "ATOM_REMOVE_NOISY",
                    "target": "atom",
                    "intent": "remove_atom",
                    "reason_code": reason_code,
                    "params": {"strategy": "low_confidence_or_short_text"},
                }
            )
            graph_actions.append(
                {
                    "action_code": "GRAPH_DOWNWEIGHT_NOISY_EVIDENCE",
                    "target": "graph",
                    "intent": "adjust_assembly_policy",
                    "reason_code": reason_code,
                    "params": {"policy_key": "noise_penalty"},
                }
            )
            policy_actions.append(
                {
                    "action_code": "POLICY_RAISE_NOISE_THRESHOLD",
                    "target": "policy",
                    "intent": "increase_review_threshold",
                    "reason_code": reason_code,
                    "params": {"metric": "noise_score"},
                }
            )
            follow_up_checks.append("CHECK_NOISE_REDUCTION")
            return

        if reason_code in {"R_TRACEABILITY_CRITICAL", "Q_TRACEABILITY_LOW", "R_COVERAGE_CRITICAL", "Q_COVERAGE_LOW"}:
            categories.append("missing_evidence")
            atom_actions.append(
                {
                    "action_code": "ATOM_ADD_EVIDENCE_GROUNDED",
                    "target": "atom",
                    "intent": "add_atom",
                    "reason_code": reason_code,
                    "params": {"strategy": "backfill_missing_evidence_refs"},
                }
            )
            graph_actions.append(
                {
                    "action_code": "GRAPH_BACKFILL_EVIDENCE_REFS",
                    "target": "graph",
                    "intent": "adjust_assembly_policy",
                    "reason_code": reason_code,
                    "params": {"policy_key": "force_evidence_per_step"},
                }
            )
            follow_up_checks.append("CHECK_TRACEABILITY_CHAIN")
            return

        if reason_code in {"R_ACTIONABILITY_CRITICAL", "Q_ACTIONABILITY_LOW"}:
            categories.append("non_actionable_steps")
            graph_actions.append(
                {
                    "action_code": "GRAPH_REWRITE_NON_ACTIONABLE_STEPS",
                    "target": "graph",
                    "intent": "rewrite_steps",
                    "reason_code": reason_code,
                    "params": {"require_action_verb": True, "require_expected_outcome": True},
                }
            )
            follow_up_checks.append("CHECK_STEP_ACTIONABILITY")
            return

        if reason_code in {"R_CONSISTENCY_CRITICAL", "Q_CONSISTENCY_LOW"}:
            categories.append("incomplete_rules")
            graph_actions.append(
                {
                    "action_code": "GRAPH_FILL_DECISION_RULES",
                    "target": "graph",
                    "intent": "complete_rules",
                    "reason_code": reason_code,
                    "params": {"resolve_conflict_edges": True},
                }
            )
            policy_actions.append(
                {
                    "action_code": "POLICY_RAISE_CONSISTENCY_THRESHOLD",
                    "target": "policy",
                    "intent": "increase_review_threshold",
                    "reason_code": reason_code,
                    "params": {"metric": "consistency_score"},
                }
            )
            follow_up_checks.append("CHECK_RULE_CONSISTENCY")
            return

        if reason_code in {"Q_NOVELTY_LOW", "Q_OVERALL_BELOW_AUTO", "R_LOW_OVERALL"}:
            categories.append("stale_version")
            policy_actions.append(
                {
                    "action_code": "POLICY_ADJUST_ASSEMBLY_POLICY",
                    "target": "policy",
                    "intent": "adjust_assembly_policy",
                    "reason_code": reason_code,
                    "params": {"strategy": "merge_with_latest_lineage_or_refresh_context"},
                }
            )
            follow_up_checks.append("CHECK_VERSION_FRESHNESS")
            return

        if reason_code in {"A_MEETS_ALL_THRESHOLDS", "A_HIGH_NOVELTY"}:
            categories.append("publish_ready")
            policy_actions.append(
                {
                    "action_code": "POLICY_CAPTURE_SUCCESS_PATTERN",
                    "target": "policy",
                    "intent": "capture_pattern",
                    "reason_code": reason_code,
                    "params": {"reuse_for_future_routing": True},
                }
            )
            follow_up_checks.append("CHECK_POST_PUBLISH_MONITORING")

    def _collect_default_actions(
        self,
        *,
        decision: ReviewDecision,
        categories: list[str],
        policy_actions: list[dict[str, Any]],
        follow_up_checks: list[str],
    ) -> None:
        if decision == ReviewDecision.AUTO_PUBLISH:
            categories.append("publish_ready")
            policy_actions.append(
                {
                    "action_code": "POLICY_CAPTURE_SUCCESS_PATTERN",
                    "target": "policy",
                    "intent": "capture_pattern",
                    "reason_code": "AUTO_PUBLISH_FALLBACK",
                    "params": {"reuse_for_future_routing": True},
                }
            )
            follow_up_checks.append("CHECK_POST_PUBLISH_MONITORING")
            return
        if decision == ReviewDecision.REJECT:
            categories.append("missing_evidence")
            policy_actions.append(
                {
                    "action_code": "POLICY_ESCALATE_REJECTION_REVIEW",
                    "target": "policy",
                    "intent": "escalate_manual_review",
                    "reason_code": "REJECT_FALLBACK",
                    "params": {"priority": "high"},
                }
            )
            follow_up_checks.append("CHECK_REJECTION_ROOT_CAUSE")
            return
        categories.append("manual_review")
        policy_actions.append(
            {
                "action_code": "POLICY_ESCALATE_MANUAL_REVIEW",
                "target": "policy",
                "intent": "escalate_manual_review",
                "reason_code": "MANUAL_REVIEW_FALLBACK",
                "params": {"priority": "medium"},
            }
        )
        follow_up_checks.append("CHECK_MANUAL_REVIEW_OUTCOME")

    def _dedupe_actions(self, actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        output: list[dict[str, Any]] = []
        seen: set[str] = set()
        for action in actions:
            key = str(action.get("action_code", "")).strip()
            if not key or key in seen:
                continue
            seen.add(key)
            output.append(dict(action))
        return output
