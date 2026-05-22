from __future__ import annotations

from dataclasses import dataclass
from statistics import median
from typing import Any


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _to_non_negative_float(value: Any) -> float:
    return max(0.0, _to_float(value))


def _to_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _to_non_negative_int(value: Any) -> int:
    return max(0, _to_int(value))


def _to_ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def _round(value: float) -> float:
    return round(float(value), 4)


@dataclass(frozen=True, slots=True)
class TrialSuccessCriteriaThresholds:
    minimum_complete_loops: int = 10
    minimum_modalities: int = 4
    minimum_approval_rate_after_one_revision: float = 0.8
    maximum_median_reviewer_edit_distance_pct: float = 25.0
    minimum_agent_smoke_success_rate: float = 0.8
    maximum_provider_failure_rate: float = 0.05

    def to_dict(self) -> dict[str, float | int]:
        return {
            "minimum_complete_loops": int(self.minimum_complete_loops),
            "minimum_modalities": int(self.minimum_modalities),
            "minimum_approval_rate_after_one_revision": float(self.minimum_approval_rate_after_one_revision),
            "maximum_median_reviewer_edit_distance_pct": float(self.maximum_median_reviewer_edit_distance_pct),
            "minimum_agent_smoke_success_rate": float(self.minimum_agent_smoke_success_rate),
            "maximum_provider_failure_rate": float(self.maximum_provider_failure_rate),
        }


class TrialMetricsCollector(object):
    """Aggregate controlled-trial loop metrics and evaluate GA discussion blockers."""

    def __init__(self, thresholds: TrialSuccessCriteriaThresholds | None = None) -> None:
        self.thresholds = thresholds or TrialSuccessCriteriaThresholds()

    def collect(self, payload: dict[str, Any]) -> dict[str, Any]:
        loops_raw = payload.get("loops")
        if not isinstance(loops_raw, list) or not loops_raw:
            raise ValueError("Trial metrics payload requires non-empty loops list.")

        release_gate = payload.get("release_gate")
        if not isinstance(release_gate, dict):
            raise ValueError("Trial metrics payload requires release_gate object.")
        latest_release_decision = str(release_gate.get("latest_release_decision", "")).strip().upper()
        if latest_release_decision not in {"GO", "HOLD"}:
            raise ValueError("release_gate.latest_release_decision must be GO or HOLD.")

        operator_signoff = payload.get("operator_signoff")
        if not isinstance(operator_signoff, dict):
            raise ValueError("Trial metrics payload requires operator_signoff object.")
        cost_accepted_by_operator = bool(operator_signoff.get("cost_per_accepted_skill_accepted", False))

        complete_loops = 0
        complete_modalities: set[str] = set()
        unreviewed_published_count = 0
        critical_secret_pii_leak_count = 0
        high_severity_incident_count = 0

        review_outcome_counts: dict[str, int] = {}
        review_evaluable_count = 0
        approved_after_one_revision = 0
        approved_count = 0

        reviewer_edit_distances: list[float] = []
        latencies_ms: list[float] = []
        provider_failures_total = 0
        provider_calls_total = 0
        retry_count_total = 0
        artifact_count_total = 0
        approved_smoke_pass_count = 0
        approved_with_not_run_smoke_count = 0
        approved_costs: list[float] = []
        approved_missing_cost_count = 0

        for index, item in enumerate(loops_raw, start=1):
            if not isinstance(item, dict):
                raise ValueError("Loop #%s must be an object." % index)
            loop_id = str(item.get("loop_id", "")).strip()
            if not loop_id:
                raise ValueError("Loop #%s is missing loop_id." % index)

            modality = str(item.get("modality", "")).strip().lower()
            if not modality:
                raise ValueError("Loop %s is missing modality." % loop_id)

            status = str(item.get("status", "complete")).strip().lower()
            if status not in {"complete", "incomplete"}:
                raise ValueError("Loop %s status must be complete or incomplete." % loop_id)
            is_complete = status == "complete"
            if is_complete:
                complete_loops += 1
                complete_modalities.add(modality)

            review_outcome = str(item.get("review_outcome", "unknown")).strip().lower()
            if review_outcome:
                review_outcome_counts[review_outcome] = review_outcome_counts.get(review_outcome, 0) + 1

            revisions_before_approval = _to_non_negative_int(item.get("revisions_before_approval", 0))
            reviewer_edit_distance_pct = _to_non_negative_float(item.get("reviewer_edit_distance_pct", 0.0))
            reviewer_edit_distances.append(reviewer_edit_distance_pct)

            if review_outcome in {"approved", "rejected"}:
                review_evaluable_count += 1
            if review_outcome == "approved":
                approved_count += 1
                if revisions_before_approval <= 1:
                    approved_after_one_revision += 1

                smoke_result = str(item.get("agent_smoke_result", "not_run")).strip().lower()
                if smoke_result == "passed":
                    approved_smoke_pass_count += 1
                elif smoke_result == "not_run":
                    approved_with_not_run_smoke_count += 1

                raw_cost = item.get("estimated_cost_usd")
                if raw_cost is None or str(raw_cost).strip() == "":
                    approved_missing_cost_count += 1
                else:
                    approved_costs.append(_to_non_negative_float(raw_cost))

            if bool(item.get("published_without_review", False)):
                unreviewed_published_count += 1
            if bool(item.get("critical_secret_or_pii_leak", False)):
                critical_secret_pii_leak_count += 1
            if bool(item.get("high_severity_incident", False)):
                high_severity_incident_count += 1

            latencies_ms.append(_to_non_negative_float(item.get("latency_ms", 0.0)))
            provider_failures_total += _to_non_negative_int(item.get("provider_failure_count", 0))
            provider_calls_total += _to_non_negative_int(item.get("provider_call_count", 0))
            retry_count_total += _to_non_negative_int(item.get("retry_count", 0))
            artifact_count_total += _to_non_negative_int(item.get("artifact_count", 0))

        approval_rate_after_one_revision = _to_ratio(float(approved_after_one_revision), float(review_evaluable_count))
        median_reviewer_edit_distance_pct = float(median(reviewer_edit_distances)) if reviewer_edit_distances else 0.0
        agent_smoke_success_rate = _to_ratio(float(approved_smoke_pass_count), float(approved_count))
        provider_failure_rate = _to_ratio(float(provider_failures_total), float(provider_calls_total))
        avg_latency_ms = _to_ratio(float(sum(latencies_ms)), float(len(latencies_ms)))
        avg_retry_count = _to_ratio(float(retry_count_total), float(len(loops_raw)))
        avg_artifact_count = _to_ratio(float(artifact_count_total), float(len(loops_raw)))
        cost_per_accepted_skill = _to_ratio(sum(approved_costs), float(approved_count)) if approved_count > 0 else 0.0

        criteria = self._evaluate_success_criteria(
            latest_release_decision=latest_release_decision,
            complete_loops=complete_loops,
            complete_modalities=len(complete_modalities),
            unreviewed_published_count=unreviewed_published_count,
            critical_secret_pii_leak_count=critical_secret_pii_leak_count,
            high_severity_incident_count=high_severity_incident_count,
            approval_rate_after_one_revision=approval_rate_after_one_revision,
            median_reviewer_edit_distance_pct=median_reviewer_edit_distance_pct,
            agent_smoke_success_rate=agent_smoke_success_rate,
            provider_failure_rate=provider_failure_rate,
            approved_count=approved_count,
            approved_missing_cost_count=approved_missing_cost_count,
            cost_accepted_by_operator=cost_accepted_by_operator,
        )

        report = {
            "manifest_id": str(payload.get("manifest_id", "")).strip() or "unknown",
            "manifest_version": str(payload.get("manifest_version", "")).strip() or "unknown",
            "thresholds": self.thresholds.to_dict(),
            "trial_metrics": {
                "loop_count": len(loops_raw),
                "complete_loop_count": complete_loops,
                "complete_modalities": sorted(complete_modalities),
                "review_outcome_counts": review_outcome_counts,
                "reviewer_edit_distance_pct": {
                    "median": _round(median_reviewer_edit_distance_pct),
                    "samples": len(reviewer_edit_distances),
                },
                "latency_ms": {
                    "average": _round(avg_latency_ms),
                    "samples": len(latencies_ms),
                },
                "provider_runtime": {
                    "provider_failure_count_total": provider_failures_total,
                    "provider_call_count_total": provider_calls_total,
                    "provider_failure_rate": _round(provider_failure_rate),
                    "retry_count_total": retry_count_total,
                    "retry_count_average_per_loop": _round(avg_retry_count),
                },
                "artifact_count": {
                    "total": artifact_count_total,
                    "average_per_loop": _round(avg_artifact_count),
                },
                "cost_placeholder": {
                    "approved_skill_count": approved_count,
                    "approved_skill_missing_cost_count": approved_missing_cost_count,
                    "cost_per_accepted_skill_usd": _round(cost_per_accepted_skill),
                    "accepted_by_operator": cost_accepted_by_operator,
                },
                "safety": {
                    "unreviewed_published_count": unreviewed_published_count,
                    "critical_secret_or_pii_leak_count": critical_secret_pii_leak_count,
                    "high_severity_incident_count": high_severity_incident_count,
                },
                "review_quality": {
                    "review_evaluable_count": review_evaluable_count,
                    "approved_after_one_revision_count": approved_after_one_revision,
                    "approval_rate_after_one_revision": _round(approval_rate_after_one_revision),
                    "approved_with_not_run_smoke_count": approved_with_not_run_smoke_count,
                    "agent_smoke_success_rate": _round(agent_smoke_success_rate),
                },
            },
            "success_criteria": criteria,
            "ga_discussion_blocked": any(
                condition.get("critical_ga_gate", False) and condition.get("status") == "fail"
                for condition in criteria["conditions"]
            ),
            "overall_status": criteria["status"],
        }
        return report

    def _evaluate_success_criteria(
        self,
        *,
        latest_release_decision: str,
        complete_loops: int,
        complete_modalities: int,
        unreviewed_published_count: int,
        critical_secret_pii_leak_count: int,
        high_severity_incident_count: int,
        approval_rate_after_one_revision: float,
        median_reviewer_edit_distance_pct: float,
        agent_smoke_success_rate: float,
        provider_failure_rate: float,
        approved_count: int,
        approved_missing_cost_count: int,
        cost_accepted_by_operator: bool,
    ) -> dict[str, Any]:
        thresholds = self.thresholds
        conditions = [
            {
                "id": "release_run_go",
                "description": "Latest release run remains GO.",
                "critical_ga_gate": True,
                "status": "pass" if latest_release_decision == "GO" else "fail",
                "actual": latest_release_decision,
                "expected": "GO",
            },
            {
                "id": "loop_volume_and_modality_coverage",
                "description": "At least 10 complete loops across at least 4 modalities.",
                "critical_ga_gate": True,
                "status": (
                    "pass"
                    if complete_loops >= thresholds.minimum_complete_loops
                    and complete_modalities >= thresholds.minimum_modalities
                    else "fail"
                ),
                "actual": {
                    "complete_loops": complete_loops,
                    "modalities": complete_modalities,
                },
                "expected": {
                    "minimum_complete_loops": thresholds.minimum_complete_loops,
                    "minimum_modalities": thresholds.minimum_modalities,
                },
            },
            {
                "id": "no_unreviewed_publication",
                "description": "Zero unreviewed skills are published.",
                "critical_ga_gate": True,
                "status": "pass" if unreviewed_published_count == 0 else "fail",
                "actual": unreviewed_published_count,
                "expected": 0,
            },
            {
                "id": "no_critical_secret_or_pii_leak",
                "description": "Zero critical secret/PII leaks in generated artifacts.",
                "critical_ga_gate": True,
                "status": "pass" if critical_secret_pii_leak_count == 0 else "fail",
                "actual": critical_secret_pii_leak_count,
                "expected": 0,
            },
            {
                "id": "no_high_severity_trial_incident",
                "description": "Zero high-severity production incidents caused by trial.",
                "critical_ga_gate": False,
                "status": "pass" if high_severity_incident_count == 0 else "fail",
                "actual": high_severity_incident_count,
                "expected": 0,
            },
            {
                "id": "reviewer_approval_rate",
                "description": "Reviewer approval rate is at least 80% after no more than one revision.",
                "critical_ga_gate": False,
                "status": (
                    "pass"
                    if approval_rate_after_one_revision >= thresholds.minimum_approval_rate_after_one_revision
                    else "fail"
                ),
                "actual": _round(approval_rate_after_one_revision),
                "expected_min": float(thresholds.minimum_approval_rate_after_one_revision),
            },
            {
                "id": "median_reviewer_edit_distance",
                "description": "Median reviewer edit distance is at or below 25%.",
                "critical_ga_gate": False,
                "status": (
                    "pass"
                    if median_reviewer_edit_distance_pct <= thresholds.maximum_median_reviewer_edit_distance_pct
                    else "fail"
                ),
                "actual": _round(median_reviewer_edit_distance_pct),
                "expected_max": float(thresholds.maximum_median_reviewer_edit_distance_pct),
            },
            {
                "id": "agent_smoke_success_rate",
                "description": "Agent-native skill smoke success rate is at least 80% for approved skills.",
                "critical_ga_gate": False,
                "status": (
                    "pass"
                    if agent_smoke_success_rate >= thresholds.minimum_agent_smoke_success_rate
                    else "fail"
                ),
                "actual": _round(agent_smoke_success_rate),
                "expected_min": float(thresholds.minimum_agent_smoke_success_rate),
            },
            {
                "id": "provider_failure_rate",
                "description": "Provider/runtime failure rate stays below agreed pilot threshold.",
                "critical_ga_gate": False,
                "status": (
                    "pass"
                    if provider_failure_rate <= thresholds.maximum_provider_failure_rate
                    else "fail"
                ),
                "actual": _round(provider_failure_rate),
                "expected_max": float(thresholds.maximum_provider_failure_rate),
            },
            {
                "id": "cost_per_accepted_skill",
                "description": "Cost per accepted skill is recorded and accepted by operator.",
                "critical_ga_gate": False,
                "status": (
                    "pass"
                    if approved_count > 0 and approved_missing_cost_count == 0 and cost_accepted_by_operator
                    else "fail"
                ),
                "actual": {
                    "approved_skill_count": approved_count,
                    "approved_skill_missing_cost_count": approved_missing_cost_count,
                    "accepted_by_operator": cost_accepted_by_operator,
                },
                "expected": {
                    "approved_skill_count_gt": 0,
                    "approved_skill_missing_cost_count": 0,
                    "accepted_by_operator": True,
                },
            },
        ]

        failed_conditions = [item for item in conditions if item["status"] == "fail"]
        return {
            "status": "pass" if not failed_conditions else "fail",
            "passed_count": len(conditions) - len(failed_conditions),
            "failed_count": len(failed_conditions),
            "failed_conditions": [
                {
                    "id": item["id"],
                    "description": item["description"],
                }
                for item in failed_conditions
            ],
            "conditions": conditions,
        }


def render_trial_metrics_markdown_summary(report: dict[str, Any]) -> str:
    metrics = report.get("trial_metrics", {})
    criteria = report.get("success_criteria", {})
    failed_conditions = criteria.get("failed_conditions", [])
    lines = [
        "# Controlled Trial Metrics Summary",
        "",
        "- Overall status: `%s`" % str(report.get("overall_status", "unknown")),
        "- GA discussion blocked: `%s`" % ("yes" if bool(report.get("ga_discussion_blocked")) else "no"),
        "- Complete loops: `%s`" % str(metrics.get("complete_loop_count", 0)),
        "- Modalities covered: `%s`"
        % ", ".join(str(item) for item in metrics.get("complete_modalities", []) if str(item).strip()),
        "- Reviewer approval rate (<=1 revision): `%s`"
        % str(metrics.get("review_quality", {}).get("approval_rate_after_one_revision", 0.0)),
        "- Median reviewer edit distance (%%): `%s`"
        % str(metrics.get("reviewer_edit_distance_pct", {}).get("median", 0.0)),
        "- Agent smoke success rate: `%s`"
        % str(metrics.get("review_quality", {}).get("agent_smoke_success_rate", 0.0)),
        "- Provider/runtime failure rate: `%s`"
        % str(metrics.get("provider_runtime", {}).get("provider_failure_rate", 0.0)),
        "- Cost per accepted skill (USD): `%s`"
        % str(metrics.get("cost_placeholder", {}).get("cost_per_accepted_skill_usd", 0.0)),
        "",
        "## GA Condition Check",
    ]
    if not failed_conditions:
        lines.append("- All trial success criteria passed.")
    else:
        lines.append("- Failed conditions:")
        for item in failed_conditions:
            lines.append("  - `%s`: %s" % (str(item.get("id", "")), str(item.get("description", ""))))
    return "\n".join(lines).strip() + "\n"
