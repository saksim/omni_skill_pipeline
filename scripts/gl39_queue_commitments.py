from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUBMISSION_QUEUE_REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-report.json"
)
DEFAULT_SUBMISSION_QUEUE_COMPLETION_REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-completion-report.json"
)
DEFAULT_HANDOFF_ESCALATIONS_REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-handoff-escalations-report.json"
)
DEFAULT_SUBMISSION_THROUGHPUT_REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-throughput-report.json"
)
DEFAULT_OUTPUT_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-commitments-report.json"
)
DEFAULT_SUMMARY_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-commitments-summary.md"
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate GL-39 owner-scoped cadence-run execution commitments from "
            "GL-37 queue, GL-38 completion, GL-27 escalation, and GL-35 throughput diagnostics."
        )
    )
    parser.add_argument("--submission-queue-report", default=str(DEFAULT_SUBMISSION_QUEUE_REPORT_PATH))
    parser.add_argument(
        "--submission-queue-completion-report",
        default=str(DEFAULT_SUBMISSION_QUEUE_COMPLETION_REPORT_PATH),
    )
    parser.add_argument(
        "--handoff-escalations-report",
        default=str(DEFAULT_HANDOFF_ESCALATIONS_REPORT_PATH),
    )
    parser.add_argument(
        "--submission-throughput-report",
        default=str(DEFAULT_SUBMISSION_THROUGHPUT_REPORT_PATH),
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help='Commitments report output path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--summary-output",
        default=str(DEFAULT_SUMMARY_PATH),
        help='Commitments summary output path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--owner",
        default="controlled-beta-ops",
        help="Fallback owner for synthetic commitments when source rows lack owner.",
    )
    parser.add_argument(
        "--fail-on-unresolved",
        action="store_true",
        help=(
            "Exit with code 1 when cadence-run obligations still have unresolved "
            "execution blockers."
        ),
    )
    parser.add_argument("--print-json", action="store_true")
    return parser.parse_args()


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("JSON root must be an object: %s" % path)
    return payload


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _to_int(value: Any, *, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return int(default)


def _to_float(value: Any, *, default: float = 0.0) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return float(default)


def _is_truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    text = str(value).strip().lower()
    return text in {"1", "true", "yes", "y", "on"}


def _unique_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for raw in values:
        value = str(raw).strip()
        if not value or value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def _transition_index(completion_report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = completion_report.get("queue_transition_records", [])
    if not isinstance(rows, list):
        rows = []
    index: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        queue_item_id = str(row.get("queue_item_id", "")).strip()
        if queue_item_id and queue_item_id not in index:
            index[queue_item_id] = row
    return index


def _escalation_severity_map(
    escalations_report: dict[str, Any],
) -> tuple[dict[str, str], dict[str, str]]:
    exports = escalations_report.get("escalation_exports", {})
    if not isinstance(exports, dict):
        exports = {}
    mapping_by_queue_item: dict[str, str] = {}
    mapping_by_action_id: dict[str, str] = {}

    def _consume(key: str, severity: str) -> None:
        rows = exports.get(key, [])
        if not isinstance(rows, list):
            return
        for row in rows:
            if not isinstance(row, dict):
                continue
            queue_item_id = str(row.get("queue_item_id", "")).strip()
            action_id = str(row.get("action_id", "")).strip()
            if queue_item_id and queue_item_id not in mapping_by_queue_item:
                mapping_by_queue_item[queue_item_id] = severity
            if action_id and action_id not in mapping_by_action_id:
                mapping_by_action_id[action_id] = severity

    _consume("overdue_items", "overdue")
    _consume("sla_breached_items", "sla_breached")
    _consume("tracking_incomplete_items", "tracking_incomplete")
    return mapping_by_queue_item, mapping_by_action_id


def _build_commitment_rows(
    *,
    queue_report: dict[str, Any],
    completion_report: dict[str, Any],
    escalations_report: dict[str, Any],
    throughput_report: dict[str, Any],
    fallback_owner: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    queue_status = str(queue_report.get("queue_status", "unknown")).strip().upper() or "UNKNOWN"
    queue_rows = queue_report.get("queue_items", [])
    if not isinstance(queue_rows, list):
        queue_rows = []

    transition_by_queue_item = _transition_index(completion_report)
    escalation_by_queue_item, escalation_by_action_id = _escalation_severity_map(escalations_report)

    refresh = queue_report.get("refresh_cadence", {})
    if not isinstance(refresh, dict):
        refresh = {}
    next_due_utc = str(refresh.get("next_refresh_due_utc", "")).strip()

    execution_focus = throughput_report.get("execution_focus", {})
    if not isinstance(execution_focus, dict):
        execution_focus = {}

    rows: list[dict[str, Any]] = []
    unresolved_blockers: list[str] = []

    if queue_status == "QUEUE_REBUILD_REQUIRED":
        rows.append(
            {
                "commitment_id": "gl39-queue-rebuild-required",
                "owner": fallback_owner,
                "queue_item_id": "",
                "backfill_action_id": "",
                "required_modality": "",
                "priority_rank": 0,
                "commitment_type": "rebuild_submission_queue",
                "commitment_status": "rebuild_required",
                "reason": "submission_queue_rebuild_required",
                "source_transition_state": "",
                "escalation_severity": "",
                "cycle_due_at_utc": next_due_utc,
            }
        )
        unresolved_blockers.append("submission_queue_rebuild_required")

    for queue_row in queue_rows:
        if not isinstance(queue_row, dict):
            continue
        queue_item_id = str(queue_row.get("queue_item_id", "")).strip()
        queue_item_status = str(queue_row.get("queue_item_status", "")).strip().lower()
        action_id = str(queue_row.get("backfill_action_id", "")).strip()
        required_modality = str(queue_row.get("required_modality", "")).strip().lower()
        priority_rank = _to_int(queue_row.get("priority_rank", 0), default=0)
        owner = str(queue_row.get("owner", "")).strip() or fallback_owner
        reason = str(queue_row.get("reason", "")).strip()

        transition = transition_by_queue_item.get(queue_item_id, {})
        transition_state = str(transition.get("transition_state", "")).strip().lower()
        escalation_severity = escalation_by_queue_item.get(queue_item_id, "") or escalation_by_action_id.get(
            action_id, ""
        )

        commitment_type = "submit_real_loop_evidence"
        commitment_status = "pending_submission"

        if escalation_severity:
            commitment_type = "resolve_acknowledgement_escalation"
            commitment_status = "escalation_required"
        elif queue_item_status == "blocked_by_submission_errors":
            commitment_type = "resolve_submission_errors"
            commitment_status = "blocked_submission_errors"
        elif transition_state == "submitted_pending_ack":
            commitment_type = "close_submission_linked_pending_ack"
            commitment_status = "pending_acknowledgement"
        elif transition_state == "closed_with_acknowledgement":
            commitment_type = "commitment_closed"
            commitment_status = "completed"

        if commitment_status != "completed":
            rows.append(
                {
                    "commitment_id": "gl39-%s" % (queue_item_id or action_id or "unbound-item"),
                    "owner": owner,
                    "queue_item_id": queue_item_id,
                    "backfill_action_id": action_id,
                    "required_modality": required_modality,
                    "priority_rank": priority_rank,
                    "commitment_type": commitment_type,
                    "commitment_status": commitment_status,
                    "reason": reason,
                    "source_transition_state": transition_state,
                    "escalation_severity": escalation_severity,
                    "cycle_due_at_utc": next_due_utc,
                }
            )

        if commitment_status == "escalation_required":
            unresolved_blockers.append("submission_queue_acknowledgement_escalation_required")
        elif commitment_status == "blocked_submission_errors":
            unresolved_blockers.append("submission_queue_blocked_by_submission_errors")
        elif commitment_status == "pending_acknowledgement":
            unresolved_blockers.append("submission_linked_pending_ack_not_closed")
        elif commitment_status == "pending_submission":
            unresolved_blockers.append("pending_submission_actions_remain")

    # Escalations may contain rows not present in queue report snapshot.
    for queue_item_id, escalation_severity in escalation_by_queue_item.items():
        queue_item_linked = any(str(row.get("queue_item_id", "")).strip() == queue_item_id for row in rows)
        action_id = ""
        if queue_item_id.startswith("gl24-queue-"):
            action_id = queue_item_id.removeprefix("gl24-queue-")
        action_linked = bool(action_id) and any(
            str(row.get("backfill_action_id", "")).strip() == action_id for row in rows
        )
        if queue_item_linked or action_linked:
            continue
        rows.append(
            {
                "commitment_id": "gl39-%s" % queue_item_id,
                "owner": fallback_owner,
                "queue_item_id": queue_item_id,
                "backfill_action_id": "",
                "required_modality": "",
                "priority_rank": 0,
                "commitment_type": "resolve_acknowledgement_escalation",
                "commitment_status": "escalation_required",
                "reason": "escalation_export_row_without_queue_item_snapshot",
                "source_transition_state": "",
                "escalation_severity": escalation_severity,
                "cycle_due_at_utc": next_due_utc,
            }
        )
        unresolved_blockers.append("submission_queue_acknowledgement_escalation_required")

    action_plan_status = str(execution_focus.get("action_plan_status", "unknown")).strip().upper() or "UNKNOWN"
    if action_plan_status == "ACTION_PLAN_REBUILD_REQUIRED":
        unresolved_blockers.append("submission_action_plan_rebuild_required")
    elif action_plan_status == "ACTION_PLAN_BLOCKED_BY_SUBMISSION_ERRORS":
        unresolved_blockers.append("submission_action_plan_blocked_by_submission_errors")
    elif action_plan_status == "ACTION_PLAN_WAITING_FOR_SUBMISSIONS":
        unresolved_blockers.append("submission_action_plan_waiting_for_submissions")

    rows.sort(
        key=lambda row: (
            0 if str(row.get("commitment_status", "")) == "escalation_required" else 1,
            0 if str(row.get("commitment_status", "")) == "blocked_submission_errors" else 1,
            0 if str(row.get("commitment_status", "")) == "pending_acknowledgement" else 1,
            _to_int(row.get("priority_rank", 0), default=0) <= 0,
            _to_int(row.get("priority_rank", 0), default=0),
            str(row.get("required_modality", "")),
            str(row.get("backfill_action_id", "")),
            str(row.get("queue_item_id", "")),
        )
    )
    return rows, _unique_preserve_order(unresolved_blockers)


def _aggregate_owner_rows(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    owner_counts: dict[str, dict[str, int]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        owner = str(row.get("owner", "")).strip() or "unassigned"
        status = str(row.get("commitment_status", "")).strip() or "unknown"
        owner_bucket = owner_counts.setdefault(
            owner,
            {
                "total_commitment_count": 0,
                "pending_submission_count": 0,
                "pending_acknowledgement_count": 0,
                "blocked_submission_errors_count": 0,
                "escalation_required_count": 0,
                "rebuild_required_count": 0,
            },
        )
        owner_bucket["total_commitment_count"] += 1
        if status in owner_bucket:
            owner_bucket[status] += 1
        elif status == "pending_submission":
            owner_bucket["pending_submission_count"] += 1
        elif status == "pending_acknowledgement":
            owner_bucket["pending_acknowledgement_count"] += 1
        elif status == "blocked_submission_errors":
            owner_bucket["blocked_submission_errors_count"] += 1
        elif status == "escalation_required":
            owner_bucket["escalation_required_count"] += 1
        elif status == "rebuild_required":
            owner_bucket["rebuild_required_count"] += 1
    return owner_counts


def _build_commitment_status(
    *,
    queue_report: dict[str, Any],
    completion_report: dict[str, Any],
    throughput_report: dict[str, Any],
    escalation_report: dict[str, Any],
    rows: list[dict[str, Any]],
    unresolved_blockers: list[str],
) -> tuple[str, str]:
    queue_status = str(queue_report.get("queue_status", "unknown")).strip().upper() or "UNKNOWN"
    completion_status = str(completion_report.get("completion_status", "unknown")).strip().upper() or "UNKNOWN"
    completion_progress_status = str(completion_report.get("completion_progress_status", "unknown")).strip().upper() or "UNKNOWN"
    cadence_status = str((queue_report.get("refresh_cadence", {}) or {}).get("cadence_status", "unknown")).strip().upper() or "UNKNOWN"
    escalation_status = str(escalation_report.get("escalation_status", "unknown")).strip().upper() or "UNKNOWN"
    threshold_met = _is_truthy(throughput_report.get("threshold_met", False))

    has_escalation = any(str(row.get("commitment_status", "")) == "escalation_required" for row in rows)
    has_blocked = any(str(row.get("commitment_status", "")) == "blocked_submission_errors" for row in rows)
    has_rebuild = any(str(row.get("commitment_status", "")) == "rebuild_required" for row in rows)

    if queue_status == "QUEUE_NOT_REQUIRED" and completion_status == "COMPLETION_NOT_REQUIRED" and threshold_met and not rows:
        commitment_status = "COMMITMENTS_NOT_REQUIRED"
    elif has_escalation or escalation_status in {
        "ESCALATION_OVERDUE_ACTION_REQUIRED",
        "ESCALATION_BREACH_ACTION_REQUIRED",
        "ESCALATION_TRACKING_INCOMPLETE",
    }:
        commitment_status = "COMMITMENTS_ESCALATION_REQUIRED"
    elif has_blocked or queue_status == "QUEUE_BLOCKED_BY_SUBMISSION_ERRORS":
        commitment_status = "COMMITMENTS_BLOCKED_BY_SUBMISSION_ERRORS"
    elif has_rebuild or queue_status == "QUEUE_REBUILD_REQUIRED":
        commitment_status = "COMMITMENTS_REBUILD_REQUIRED"
    else:
        commitment_status = "COMMITMENTS_ACTIVE"

    if commitment_status == "COMMITMENTS_NOT_REQUIRED":
        cadence_obligation_status = "RUN_NOT_REQUIRED"
    elif cadence_status == "CADENCE_DUE" and unresolved_blockers:
        cadence_obligation_status = "RUN_DUE_WITH_UNRESOLVED_BLOCKERS"
    elif cadence_status == "CADENCE_DUE":
        cadence_obligation_status = "RUN_DUE"
    elif cadence_status in {"CADENCE_ON_SCHEDULE", "CADENCE_BASELINE_INITIALIZED"} and completion_progress_status in {
        "COMPLETION_PROGRESSING",
        "COMPLETION_IN_PROGRESS",
        "COMPLETION_BASELINE_INITIALIZED",
        "COMPLETION_STALLED",
        "COMPLETION_BLOCKED",
    }:
        cadence_obligation_status = "RUN_ON_SCHEDULE_WITH_OPEN_COMMITMENTS"
    else:
        cadence_obligation_status = "RUN_STATUS_UNSPECIFIED"

    return commitment_status, cadence_obligation_status


def _build_report(
    *,
    queue_report: dict[str, Any],
    queue_report_path: Path,
    completion_report: dict[str, Any],
    completion_report_path: Path,
    escalations_report: dict[str, Any],
    escalations_report_path: Path,
    throughput_report: dict[str, Any],
    throughput_report_path: Path,
    owner: str,
) -> dict[str, Any]:
    completion_cycle = completion_report.get("cycle_movement_verification", {})
    if not isinstance(completion_cycle, dict):
        completion_cycle = {}

    execution_focus = throughput_report.get("execution_focus", {})
    if not isinstance(execution_focus, dict):
        execution_focus = {}

    queue_refresh = queue_report.get("refresh_cadence", {})
    if not isinstance(queue_refresh, dict):
        queue_refresh = {}

    rows, unresolved_blockers = _build_commitment_rows(
        queue_report=queue_report,
        completion_report=completion_report,
        escalations_report=escalations_report,
        throughput_report=throughput_report,
        fallback_owner=owner,
    )
    owner_counts = _aggregate_owner_rows(rows)
    commitment_status, cadence_obligation_status = _build_commitment_status(
        queue_report=queue_report,
        completion_report=completion_report,
        throughput_report=throughput_report,
        escalation_report=escalations_report,
        rows=rows,
        unresolved_blockers=unresolved_blockers,
    )

    return {
        "schema_version": "real_trial_submission_queue_commitments.v1",
        "generated_at_utc": _utc_now_iso(),
        "owner": owner,
        "input_paths": {
            "submission_queue_report": str(queue_report_path),
            "submission_queue_completion_report": str(completion_report_path),
            "handoff_escalations_report": str(escalations_report_path),
            "submission_throughput_report": str(throughput_report_path),
        },
        "commitment_status": commitment_status,
        "cadence_run_obligation_status": cadence_obligation_status,
        "commitment_counts": {
            "total_commitment_count": len(rows),
            "pending_submission_count": sum(
                1 for row in rows if str(row.get("commitment_status", "")) == "pending_submission"
            ),
            "pending_acknowledgement_count": sum(
                1 for row in rows if str(row.get("commitment_status", "")) == "pending_acknowledgement"
            ),
            "blocked_submission_errors_count": sum(
                1 for row in rows if str(row.get("commitment_status", "")) == "blocked_submission_errors"
            ),
            "escalation_required_count": sum(
                1 for row in rows if str(row.get("commitment_status", "")) == "escalation_required"
            ),
            "rebuild_required_count": sum(
                1 for row in rows if str(row.get("commitment_status", "")) == "rebuild_required"
            ),
        },
        "owner_commitment_counts": owner_counts,
        "unresolved_execution_blockers": unresolved_blockers,
        "cycle_snapshot": {
            "queue_status": str(queue_report.get("queue_status", "unknown")),
            "queue_cadence_status": str(queue_refresh.get("cadence_status", "unknown")),
            "queue_next_refresh_due_utc": str(queue_refresh.get("next_refresh_due_utc", "")),
            "queue_due_in_hours": _to_float(queue_refresh.get("due_in_hours", 0.0), default=0.0),
            "completion_status": str(completion_report.get("completion_status", "unknown")),
            "completion_progress_status": str(completion_report.get("completion_progress_status", "unknown")),
            "completion_cycle_verification_status": str(completion_report.get("cycle_verification_status", "unknown")),
            "completion_submitted_item_delta_from_previous_cycle": _to_int(
                completion_cycle.get("submitted_item_delta_from_previous_cycle", 0),
                default=0,
            ),
            "completion_closed_item_delta_from_previous_cycle": _to_int(
                completion_cycle.get("closed_item_delta_from_previous_cycle", 0),
                default=0,
            ),
            "completion_open_item_delta_from_previous_cycle": _to_int(
                completion_cycle.get("open_item_delta_from_previous_cycle", 0),
                default=0,
            ),
            "throughput_status": str(throughput_report.get("throughput_status", "unknown")),
            "throughput_threshold_met": _is_truthy(throughput_report.get("threshold_met", False)),
            "throughput_net_new_loop_count": _to_int(
                completion_cycle.get("throughput_net_new_loop_count", 0),
                default=0,
            ),
            "throughput_net_new_loop_ids": completion_cycle.get("throughput_net_new_loop_ids", []),
            "submission_action_plan_status": str(execution_focus.get("action_plan_status", "unknown")),
            "submission_action_plan_blockers": execution_focus.get("action_plan_blockers", []),
            "escalation_status": str(escalations_report.get("escalation_status", "unknown")),
        },
        "commitment_rows": rows,
    }


def _render_summary(report: dict[str, Any]) -> str:
    counts = report.get("commitment_counts", {})
    if not isinstance(counts, dict):
        counts = {}
    cycle = report.get("cycle_snapshot", {})
    if not isinstance(cycle, dict):
        cycle = {}
    blockers = report.get("unresolved_execution_blockers", [])
    if not isinstance(blockers, list):
        blockers = []
    rows = report.get("commitment_rows", [])
    if not isinstance(rows, list):
        rows = []

    lines = [
        "# Real Trial Submission Queue Commitments Summary",
        "",
        "- Commitment status: `%s`" % str(report.get("commitment_status", "unknown")),
        "- Cadence run obligation status: `%s`" % str(report.get("cadence_run_obligation_status", "unknown")),
        "- Queue status: `%s`" % str(cycle.get("queue_status", "unknown")),
        "- Queue cadence status: `%s`" % str(cycle.get("queue_cadence_status", "unknown")),
        "- Completion progress status: `%s`" % str(cycle.get("completion_progress_status", "unknown")),
        "- Throughput status: `%s`" % str(cycle.get("throughput_status", "unknown")),
        "- Total commitments: `%s`" % str(_to_int(counts.get("total_commitment_count", 0), default=0)),
        "- Pending submissions: `%s`" % str(_to_int(counts.get("pending_submission_count", 0), default=0)),
        "- Pending acknowledgements: `%s`" % str(_to_int(counts.get("pending_acknowledgement_count", 0), default=0)),
        "- Blocked by submission errors: `%s`"
        % str(_to_int(counts.get("blocked_submission_errors_count", 0), default=0)),
        "- Escalation required: `%s`" % str(_to_int(counts.get("escalation_required_count", 0), default=0)),
        "- Rebuild required: `%s`" % str(_to_int(counts.get("rebuild_required_count", 0), default=0)),
        "",
        "## Unresolved Blockers",
    ]
    if blockers:
        for blocker in blockers:
            lines.append("- `%s`" % str(blocker))
    else:
        lines.append("- none")

    lines.extend(["", "## Commitment Rows"])
    if rows:
        for row in rows:
            if not isinstance(row, dict):
                continue
            lines.append(
                "- `%s` owner=%s status=%s type=%s modality=%s action=%s due=%s"
                % (
                    str(row.get("queue_item_id", "")) or str(row.get("commitment_id", "")),
                    str(row.get("owner", "")),
                    str(row.get("commitment_status", "")),
                    str(row.get("commitment_type", "")),
                    str(row.get("required_modality", "")),
                    str(row.get("backfill_action_id", "")),
                    str(row.get("cycle_due_at_utc", "")),
                )
            )
    else:
        lines.append("- none")

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    queue_report_path = Path(str(args.submission_queue_report).strip()).resolve()
    completion_report_path = Path(str(args.submission_queue_completion_report).strip()).resolve()
    escalations_report_path = Path(str(args.handoff_escalations_report).strip()).resolve()
    throughput_report_path = Path(str(args.submission_throughput_report).strip()).resolve()
    output_path = None if str(args.output).strip() == "-" else Path(str(args.output).strip()).resolve()
    summary_path = None if str(args.summary_output).strip() == "-" else Path(str(args.summary_output).strip()).resolve()
    owner = str(args.owner).strip() or "controlled-beta-ops"

    try:
        for path, label in (
            (queue_report_path, "submission queue report"),
            (completion_report_path, "submission queue completion report"),
            (escalations_report_path, "handoff escalations report"),
            (throughput_report_path, "submission throughput report"),
        ):
            if not path.is_file():
                raise ValueError("%s path does not exist: %s" % (label, path))

        queue_report = _read_json(queue_report_path)
        completion_report = _read_json(completion_report_path)
        escalations_report = _read_json(escalations_report_path)
        throughput_report = _read_json(throughput_report_path)

        report = _build_report(
            queue_report=queue_report,
            queue_report_path=queue_report_path,
            completion_report=completion_report,
            completion_report_path=completion_report_path,
            escalations_report=escalations_report,
            escalations_report_path=escalations_report_path,
            throughput_report=throughput_report,
            throughput_report_path=throughput_report_path,
            owner=owner,
        )
        summary = _render_summary(report)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print("Real trial submission queue commitments generation failed: %s" % exc, file=sys.stderr)
        return 2

    if output_path is not None:
        _write_text(output_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print("Real trial submission queue commitments report written: %s" % output_path)
    if summary_path is not None:
        _write_text(summary_path, summary)
        print("Real trial submission queue commitments summary written: %s" % summary_path)

    counts = report.get("commitment_counts", {})
    if not isinstance(counts, dict):
        counts = {}
    blockers = report.get("unresolved_execution_blockers", [])
    if not isinstance(blockers, list):
        blockers = []

    print(
        "Real trial submission queue commitments status=%s obligations=%s blockers=%s"
        % (
            str(report.get("commitment_status", "unknown")),
            _to_int(counts.get("total_commitment_count", 0), default=0),
            len(blockers),
        )
    )

    if args.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    if bool(args.fail_on_unresolved) and str(report.get("commitment_status", "")).strip() != "COMMITMENTS_NOT_REQUIRED":
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
