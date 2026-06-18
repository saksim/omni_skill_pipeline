from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUBMISSION_QUEUE_COMMITMENTS_REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-commitments-report.json"
)
DEFAULT_SUBMISSION_QUEUE_COMPLETION_REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-completion-report.json"
)
DEFAULT_OUTPUT_PATH = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-commitment-closure-report.json"
)
DEFAULT_SUMMARY_PATH = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-commitment-closure-summary.md"
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate GL-40 commitment-closure evidence by binding GL-39 commitments to "
            "GL-38 transition rows and emitting stale-rollover diagnostics."
        )
    )
    parser.add_argument(
        "--submission-queue-commitments-report",
        default=str(DEFAULT_SUBMISSION_QUEUE_COMMITMENTS_REPORT_PATH),
    )
    parser.add_argument(
        "--submission-queue-completion-report",
        default=str(DEFAULT_SUBMISSION_QUEUE_COMPLETION_REPORT_PATH),
    )
    parser.add_argument(
        "--previous-commitment-closure-report",
        default="",
        help=(
            "Optional previous GL-40 report. When omitted, script attempts to read existing "
            "--output path before writing."
        ),
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help='Commitment-closure report output path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--summary-output",
        default=str(DEFAULT_SUMMARY_PATH),
        help='Commitment-closure summary output path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--owner",
        default="controlled-beta-ops",
        help="Fallback owner used when source rows do not provide owner.",
    )
    parser.add_argument(
        "--fail-on-stale-rollover",
        action="store_true",
        help="Exit with code 1 when stale rollover commitments are detected.",
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


def _completion_transition_index(
    completion_report: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    rows = completion_report.get("queue_transition_records", [])
    if not isinstance(rows, list):
        rows = []
    by_queue_item: dict[str, dict[str, Any]] = {}
    by_action_id: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        queue_item_id = str(row.get("queue_item_id", "")).strip()
        action_id = str(row.get("backfill_action_id", "")).strip()
        if queue_item_id and queue_item_id not in by_queue_item:
            by_queue_item[queue_item_id] = row
        if action_id and action_id not in by_action_id:
            by_action_id[action_id] = row
    return by_queue_item, by_action_id


def _resolve_completion_transition(
    commitment_row: dict[str, Any],
    *,
    by_queue_item: dict[str, dict[str, Any]],
    by_action_id: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any] | None, str]:
    queue_item_id = str(commitment_row.get("queue_item_id", "")).strip()
    if queue_item_id and queue_item_id in by_queue_item:
        return by_queue_item[queue_item_id], "queue_item_id"
    action_id = str(commitment_row.get("backfill_action_id", "")).strip()
    if action_id and action_id in by_action_id:
        return by_action_id[action_id], "backfill_action_id"
    return None, "none"


def _previous_closure_index(previous_report: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not isinstance(previous_report, dict):
        return {}
    rows = previous_report.get("commitment_closure_rows", [])
    if not isinstance(rows, list):
        rows = []
    index: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        commitment_id = str(row.get("commitment_id", "")).strip()
        if commitment_id and commitment_id not in index:
            index[commitment_id] = row
    return index


def _build_commitment_closure_rows(
    *,
    commitments_report: dict[str, Any],
    completion_report: dict[str, Any],
    previous_closure_report: dict[str, Any] | None,
    fallback_owner: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    commitment_rows = commitments_report.get("commitment_rows", [])
    if not isinstance(commitment_rows, list):
        commitment_rows = []
    queue_cadence_status = str(
        (commitments_report.get("cycle_snapshot", {}) or {}).get("queue_cadence_status", "unknown")
    ).strip().upper() or "UNKNOWN"
    cadence_due = queue_cadence_status == "CADENCE_DUE"

    completion_by_queue_item, completion_by_action_id = _completion_transition_index(completion_report)
    previous_index = _previous_closure_index(previous_closure_report)

    rows: list[dict[str, Any]] = []
    acknowledgement_rows: list[dict[str, Any]] = []
    stale_rollover_rows: list[dict[str, Any]] = []
    warning_codes: list[str] = []

    for commitment in commitment_rows:
        if not isinstance(commitment, dict):
            continue
        commitment_id = str(commitment.get("commitment_id", "")).strip() or "unbound-commitment"
        queue_item_id = str(commitment.get("queue_item_id", "")).strip()
        action_id = str(commitment.get("backfill_action_id", "")).strip()
        required_modality = str(commitment.get("required_modality", "")).strip().lower()
        owner = str(commitment.get("owner", "")).strip() or fallback_owner
        commitment_status_gl39 = str(commitment.get("commitment_status", "")).strip().lower()

        transition, transition_match_strategy = _resolve_completion_transition(
            commitment,
            by_queue_item=completion_by_queue_item,
            by_action_id=completion_by_action_id,
        )
        transition_state = (
            str(transition.get("transition_state", "")).strip().lower()
            if isinstance(transition, dict)
            else ""
        )
        completion_queue_item_status = (
            str(transition.get("queue_item_status_gl37", "")).strip().lower()
            if isinstance(transition, dict)
            else ""
        )
        completion_handoff_queue_status = (
            str(transition.get("handoff_queue_status_gl24", "")).strip().lower()
            if isinstance(transition, dict)
            else ""
        )

        if commitment_status_gl39 == "rebuild_required":
            closure_state = "rebuild_required"
        elif commitment_status_gl39 == "blocked_submission_errors":
            closure_state = "blocked_submission_errors"
        elif commitment_status_gl39 == "escalation_required":
            closure_state = "escalation_required"
        elif transition_state == "closed_with_acknowledgement":
            closure_state = "closed_with_acknowledgement"
        elif commitment_status_gl39 == "pending_acknowledgement" or transition_state == "submitted_pending_ack":
            closure_state = "pending_acknowledgement"
        elif commitment_status_gl39 == "completed":
            closure_state = "completed_without_acknowledgement"
        else:
            closure_state = "open_commitment"

        closure_acknowledged = closure_state == "closed_with_acknowledgement"
        stale_rollover = False
        stale_reason_codes: list[str] = []
        previous_row = previous_index.get(commitment_id)
        if not closure_acknowledged and isinstance(previous_row, dict):
            previous_closure_state = str(previous_row.get("closure_state", "")).strip().lower()
            previous_transition_state = str(previous_row.get("transition_state_gl38", "")).strip().lower()
            previous_commitment_status = str(previous_row.get("commitment_status_gl39", "")).strip().lower()
            previous_closed = bool(previous_row.get("closure_acknowledged", False)) or previous_closure_state in {
                "closed_with_acknowledgement",
                "completed_without_acknowledgement",
            }
            if (
                not previous_closed
                and previous_closure_state == closure_state
                and previous_transition_state == transition_state
                and previous_commitment_status == commitment_status_gl39
            ):
                stale_rollover = True
                stale_reason_codes.append("unchanged_open_commitment_across_cycles")
                if cadence_due:
                    stale_reason_codes.append("cadence_due_stale_rollover")

        row = {
            "commitment_id": commitment_id,
            "queue_item_id": queue_item_id,
            "backfill_action_id": action_id,
            "required_modality": required_modality,
            "owner": owner,
            "priority_rank": _to_int(commitment.get("priority_rank", 0), default=0),
            "commitment_type": str(commitment.get("commitment_type", "")),
            "commitment_status_gl39": commitment_status_gl39,
            "source_transition_state_gl39": str(commitment.get("source_transition_state", "")),
            "transition_match_strategy": transition_match_strategy,
            "transition_state_gl38": transition_state,
            "completion_queue_item_status_gl37": completion_queue_item_status,
            "completion_handoff_queue_status_gl24": completion_handoff_queue_status,
            "closure_state": closure_state,
            "closure_acknowledged": closure_acknowledged,
            "stale_rollover": stale_rollover,
            "stale_reason_codes": stale_reason_codes,
            "linked_submission_loop_id": str(transition.get("linked_submission_loop_id", ""))
            if isinstance(transition, dict)
            else "",
            "linked_submission_review_task_id": str(transition.get("linked_submission_review_task_id", ""))
            if isinstance(transition, dict)
            else "",
            "linked_submission_reviewed_at_utc": str(transition.get("linked_submission_reviewed_at_utc", ""))
            if isinstance(transition, dict)
            else "",
            "cycle_due_at_utc": str(commitment.get("cycle_due_at_utc", "")),
            "reason": str(commitment.get("reason", "")),
            "escalation_severity": str(commitment.get("escalation_severity", "")),
        }
        rows.append(row)

        if closure_acknowledged:
            acknowledgement_rows.append(
                {
                    "commitment_id": commitment_id,
                    "queue_item_id": queue_item_id,
                    "backfill_action_id": action_id,
                    "required_modality": required_modality,
                    "owner": owner,
                    "linked_submission_loop_id": row["linked_submission_loop_id"],
                    "linked_submission_review_task_id": row["linked_submission_review_task_id"],
                    "linked_submission_reviewed_at_utc": row["linked_submission_reviewed_at_utc"],
                    "closure_state": closure_state,
                }
            )

        if stale_rollover:
            stale_rollover_rows.append(
                {
                    "commitment_id": commitment_id,
                    "queue_item_id": queue_item_id,
                    "backfill_action_id": action_id,
                    "required_modality": required_modality,
                    "owner": owner,
                    "closure_state": closure_state,
                    "transition_state_gl38": transition_state,
                    "commitment_status_gl39": commitment_status_gl39,
                    "stale_reason_codes": stale_reason_codes,
                    "cycle_due_at_utc": str(commitment.get("cycle_due_at_utc", "")),
                }
            )

        if transition is None:
            warning_codes.append("commitment_row_without_completion_transition")
        if closure_state == "pending_acknowledgement":
            warning_codes.append("pending_acknowledgement_closure_required")

    return rows, acknowledgement_rows, stale_rollover_rows, _unique_preserve_order(warning_codes)


def _build_report(
    *,
    commitments_report: dict[str, Any],
    commitments_report_path: Path,
    completion_report: dict[str, Any],
    completion_report_path: Path,
    previous_closure_report: dict[str, Any] | None,
    previous_closure_report_path: Path | None,
    owner: str,
) -> dict[str, Any]:
    commitment_status_gl39 = str(commitments_report.get("commitment_status", "unknown")).strip().upper() or "UNKNOWN"
    cadence_run_obligation_status_gl39 = (
        str(commitments_report.get("cadence_run_obligation_status", "unknown")).strip().upper() or "UNKNOWN"
    )
    cycle_snapshot = commitments_report.get("cycle_snapshot", {})
    if not isinstance(cycle_snapshot, dict):
        cycle_snapshot = {}
    queue_cadence_status = str(cycle_snapshot.get("queue_cadence_status", "unknown")).strip().upper() or "UNKNOWN"
    queue_status = str(cycle_snapshot.get("queue_status", "unknown")).strip().upper() or "UNKNOWN"
    unresolved_execution_blockers = commitments_report.get("unresolved_execution_blockers", [])
    if not isinstance(unresolved_execution_blockers, list):
        unresolved_execution_blockers = []

    rows, acknowledgement_rows, stale_rollover_rows, warning_codes = _build_commitment_closure_rows(
        commitments_report=commitments_report,
        completion_report=completion_report,
        previous_closure_report=previous_closure_report,
        fallback_owner=owner,
    )

    active_states = {
        "open_commitment",
        "pending_acknowledgement",
        "blocked_submission_errors",
        "escalation_required",
        "rebuild_required",
    }
    active_rows = [row for row in rows if str(row.get("closure_state", "")) in active_states]
    blocked_rows = [row for row in rows if str(row.get("closure_state", "")) == "blocked_submission_errors"]
    escalation_rows = [row for row in rows if str(row.get("closure_state", "")) == "escalation_required"]
    rebuild_rows = [row for row in rows if str(row.get("closure_state", "")) == "rebuild_required"]
    pending_ack_rows = [row for row in rows if str(row.get("closure_state", "")) == "pending_acknowledgement"]
    stale_rows = [row for row in rows if bool(row.get("stale_rollover", False))]

    previous_closure_counts = {}
    previous_snapshot_available = isinstance(previous_closure_report, dict)
    previous_generated_at_utc = ""
    if previous_snapshot_available:
        previous_generated_at_utc = str(previous_closure_report.get("generated_at_utc", ""))
        previous_closure_counts = previous_closure_report.get("closure_counts", {})
        if not isinstance(previous_closure_counts, dict):
            previous_closure_counts = {}
    previous_closed_count = _to_int(
        previous_closure_counts.get("closed_with_acknowledgement_count", 0),
        default=0,
    )
    closed_count = len(acknowledgement_rows)
    net_new_closed_count = closed_count - previous_closed_count
    newly_open_commitment_count = len(active_rows) - len(stale_rows)

    if len(stale_rows) > 0:
        warning_codes.append("commitment_stale_rollover_detected")
    if len(blocked_rows) > 0:
        warning_codes.append("blocked_submission_errors_require_resolution")
    if len(escalation_rows) > 0:
        warning_codes.append("escalation_required_commitments_present")
    if len(rebuild_rows) > 0:
        warning_codes.append("rebuild_required_commitments_present")
    if queue_cadence_status == "CADENCE_DUE" and len(active_rows) > 0:
        warning_codes.append("cadence_due_with_open_commitments")
    if queue_cadence_status == "CADENCE_DUE" and len(stale_rows) > 0:
        warning_codes.append("cadence_due_with_stale_rollover")
    warning_codes = _unique_preserve_order(warning_codes)

    if commitment_status_gl39 == "COMMITMENTS_NOT_REQUIRED" and len(rows) == 0:
        commitment_closure_status = "CLOSURE_NOT_REQUIRED"
    elif len(rebuild_rows) > 0 or commitment_status_gl39 == "COMMITMENTS_REBUILD_REQUIRED":
        commitment_closure_status = "CLOSURE_REBUILD_REQUIRED"
    elif len(blocked_rows) > 0 or commitment_status_gl39 == "COMMITMENTS_BLOCKED_BY_SUBMISSION_ERRORS":
        commitment_closure_status = "CLOSURE_BLOCKED_BY_SUBMISSION_ERRORS"
    elif len(escalation_rows) > 0 or commitment_status_gl39 == "COMMITMENTS_ESCALATION_REQUIRED":
        commitment_closure_status = "CLOSURE_ESCALATION_REQUIRED"
    elif len(stale_rows) > 0:
        commitment_closure_status = "CLOSURE_STALE_ROLLOVER_REQUIRED"
    elif len(rows) > 0 and len(active_rows) == 0:
        commitment_closure_status = "CLOSURE_COMPLETED"
    else:
        commitment_closure_status = "CLOSURE_IN_PROGRESS"

    if commitment_closure_status == "CLOSURE_NOT_REQUIRED":
        cadence_run_closure_status = "CLOSURE_RUN_NOT_REQUIRED"
    elif queue_cadence_status == "CADENCE_DUE" and len(stale_rows) > 0:
        cadence_run_closure_status = "CLOSURE_RUN_DUE_WITH_STALE_ROLLOVER"
    elif len(rows) > 0 and len(active_rows) == 0:
        cadence_run_closure_status = "CLOSURE_RUN_CLEARED"
    else:
        cadence_run_closure_status = "CLOSURE_RUN_ACTIVE"

    return {
        "schema_version": "real_trial_submission_queue_commitment_closure.v1",
        "generated_at_utc": _utc_now_iso(),
        "owner": owner,
        "input_paths": {
            "submission_queue_commitments_report": str(commitments_report_path),
            "submission_queue_completion_report": str(completion_report_path),
            "previous_commitment_closure_report": str(previous_closure_report_path)
            if previous_closure_report_path is not None and previous_snapshot_available
            else "",
        },
        "queue_status": queue_status,
        "queue_cadence_status": queue_cadence_status,
        "commitment_status_gl39": commitment_status_gl39,
        "cadence_run_obligation_status_gl39": cadence_run_obligation_status_gl39,
        "commitment_closure_status": commitment_closure_status,
        "cadence_run_closure_status": cadence_run_closure_status,
        "warning_codes": warning_codes,
        "unresolved_execution_blockers": unresolved_execution_blockers,
        "closure_counts": {
            "total_commitment_count": len(rows),
            "closed_with_acknowledgement_count": closed_count,
            "active_commitment_count": len(active_rows),
            "pending_acknowledgement_count": len(pending_ack_rows),
            "blocked_submission_errors_count": len(blocked_rows),
            "escalation_required_count": len(escalation_rows),
            "rebuild_required_count": len(rebuild_rows),
            "stale_rollover_count": len(stale_rows),
            "net_new_closed_with_acknowledgement_count": net_new_closed_count,
            "unchanged_open_commitment_count": len(stale_rows),
            "newly_open_commitment_count": max(newly_open_commitment_count, 0),
        },
        "previous_cycle_snapshot": {
            "available": previous_snapshot_available,
            "generated_at_utc": previous_generated_at_utc,
            "closed_with_acknowledgement_count": previous_closed_count,
        },
        "commitment_closure_rows": rows,
        "closure_acknowledgement_rows": acknowledgement_rows,
        "stale_rollover_rows": stale_rollover_rows,
    }


def _render_summary(report: dict[str, Any]) -> str:
    counts = report.get("closure_counts", {})
    if not isinstance(counts, dict):
        counts = {}
    warnings = report.get("warning_codes", [])
    if not isinstance(warnings, list):
        warnings = []
    stale_rows = report.get("stale_rollover_rows", [])
    if not isinstance(stale_rows, list):
        stale_rows = []
    acknowledgement_rows = report.get("closure_acknowledgement_rows", [])
    if not isinstance(acknowledgement_rows, list):
        acknowledgement_rows = []

    lines = [
        "# Real Trial Submission Queue Commitment Closure Summary",
        "",
        "- Commitment closure status: `%s`" % str(report.get("commitment_closure_status", "unknown")),
        "- Cadence run closure status: `%s`" % str(report.get("cadence_run_closure_status", "unknown")),
        "- Queue status: `%s`" % str(report.get("queue_status", "unknown")),
        "- Queue cadence status: `%s`" % str(report.get("queue_cadence_status", "unknown")),
        "- Total commitments: `%s`" % str(_to_int(counts.get("total_commitment_count", 0), default=0)),
        "- Closed with acknowledgement: `%s`"
        % str(_to_int(counts.get("closed_with_acknowledgement_count", 0), default=0)),
        "- Active commitments: `%s`" % str(_to_int(counts.get("active_commitment_count", 0), default=0)),
        "- Stale rollover commitments: `%s`" % str(_to_int(counts.get("stale_rollover_count", 0), default=0)),
        "- Net-new closed with acknowledgement: `%s`"
        % str(_to_int(counts.get("net_new_closed_with_acknowledgement_count", 0), default=0)),
        "",
        "## Warning Codes",
    ]
    if warnings:
        for warning in warnings:
            lines.append("- `%s`" % str(warning))
    else:
        lines.append("- none")

    lines.extend(["", "## Closure Acknowledgements"])
    if acknowledgement_rows:
        for row in acknowledgement_rows:
            if not isinstance(row, dict):
                continue
            lines.append(
                "- `%s` action=%s loop=%s review_task=%s reviewed_at=%s"
                % (
                    str(row.get("commitment_id", "")),
                    str(row.get("backfill_action_id", "")),
                    str(row.get("linked_submission_loop_id", "")),
                    str(row.get("linked_submission_review_task_id", "")),
                    str(row.get("linked_submission_reviewed_at_utc", "")),
                )
            )
    else:
        lines.append("- none")

    lines.extend(["", "## Stale Rollover Rows"])
    if stale_rows:
        for row in stale_rows:
            if not isinstance(row, dict):
                continue
            lines.append(
                "- `%s` action=%s closure_state=%s reasons=%s"
                % (
                    str(row.get("commitment_id", "")),
                    str(row.get("backfill_action_id", "")),
                    str(row.get("closure_state", "")),
                    ",".join(str(item) for item in row.get("stale_reason_codes", []) or []),
                )
            )
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    commitments_report_path = Path(str(args.submission_queue_commitments_report).strip()).resolve()
    completion_report_path = Path(str(args.submission_queue_completion_report).strip()).resolve()
    output_path = None if str(args.output).strip() == "-" else Path(str(args.output).strip()).resolve()
    summary_path = None if str(args.summary_output).strip() == "-" else Path(str(args.summary_output).strip()).resolve()
    owner = str(args.owner).strip() or "controlled-beta-ops"

    try:
        if not commitments_report_path.is_file():
            raise ValueError("Submission queue commitments report path does not exist: %s" % commitments_report_path)
        if not completion_report_path.is_file():
            raise ValueError("Submission queue completion report path does not exist: %s" % completion_report_path)
        commitments_report = _read_json(commitments_report_path)
        completion_report = _read_json(completion_report_path)

        previous_report_path: Path | None = None
        previous_report: dict[str, Any] | None = None
        previous_arg = str(args.previous_commitment_closure_report).strip()
        if previous_arg:
            previous_report_path = Path(previous_arg).resolve()
        elif output_path is not None:
            previous_report_path = output_path
        if previous_report_path is not None and previous_report_path.is_file():
            previous_report = _read_json(previous_report_path)

        report = _build_report(
            commitments_report=commitments_report,
            commitments_report_path=commitments_report_path,
            completion_report=completion_report,
            completion_report_path=completion_report_path,
            previous_closure_report=previous_report,
            previous_closure_report_path=previous_report_path,
            owner=owner,
        )
        summary = _render_summary(report)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print("Real trial commitment closure generation failed: %s" % exc, file=sys.stderr)
        return 2

    if output_path is not None:
        _write_text(output_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print("Real trial submission queue commitment-closure report written: %s" % output_path)
    if summary_path is not None:
        _write_text(summary_path, summary)
        print("Real trial submission queue commitment-closure summary written: %s" % summary_path)

    counts = report.get("closure_counts", {})
    if not isinstance(counts, dict):
        counts = {}
    print(
        "Real trial commitment closure status=%s total=%s closed=%s stale=%s"
        % (
            str(report.get("commitment_closure_status", "unknown")),
            _to_int(counts.get("total_commitment_count", 0), default=0),
            _to_int(counts.get("closed_with_acknowledgement_count", 0), default=0),
            _to_int(counts.get("stale_rollover_count", 0), default=0),
        )
    )

    if args.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    if bool(args.fail_on_stale_rollover) and _to_int(counts.get("stale_rollover_count", 0), default=0) > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
