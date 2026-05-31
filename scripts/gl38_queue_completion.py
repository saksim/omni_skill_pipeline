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
DEFAULT_SUBMISSION_THROUGHPUT_REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-throughput-report.json"
)
DEFAULT_HANDOFF_REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-handoff-report.json"
)
DEFAULT_OUTPUT_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-completion-report.json"
)
DEFAULT_SUMMARY_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-completion-summary.md"
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate GL-38 machine-readable operator completion evidence from GL-37 queue "
            "artifacts, GL-24 handoff transitions, and GL-35 net-new movement diagnostics."
        )
    )
    parser.add_argument("--submission-queue-report", default=str(DEFAULT_SUBMISSION_QUEUE_REPORT_PATH))
    parser.add_argument("--submission-throughput-report", default=str(DEFAULT_SUBMISSION_THROUGHPUT_REPORT_PATH))
    parser.add_argument("--handoff-report", default=str(DEFAULT_HANDOFF_REPORT_PATH))
    parser.add_argument(
        "--previous-completion-report",
        default="",
        help=(
            "Optional previous GL-38 completion report. When omitted, script attempts to read "
            "existing --output path before writing."
        ),
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help='Queue-completion report output path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--summary-output",
        default=str(DEFAULT_SUMMARY_PATH),
        help='Queue-completion summary output path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--owner",
        default="controlled-beta-ops",
        help="Owner tag written into queue-completion artifacts.",
    )
    parser.add_argument(
        "--fail-on-stalled",
        action="store_true",
        help="Exit with code 1 when completion progress status is COMPLETION_STALLED.",
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


def _is_truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    text = str(value).strip().lower()
    return text in {"1", "true", "yes", "y", "on"}


def _unique_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for raw in items:
        item = str(raw).strip()
        if not item or item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def _handoff_item_index(handoff_report: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    queue_rows = handoff_report.get("queue_items", [])
    if not isinstance(queue_rows, list):
        queue_rows = []
    by_action_id: dict[str, dict[str, Any]] = {}
    by_slot_modality: dict[str, dict[str, Any]] = {}
    for row in queue_rows:
        if not isinstance(row, dict):
            continue
        action_id = str(row.get("action_id", "")).strip()
        if action_id and action_id not in by_action_id:
            by_action_id[action_id] = row
        slot_index = _to_int(row.get("slot_index"), default=0)
        modality = str(row.get("required_modality", "")).strip().lower()
        if slot_index > 0 and modality:
            key = "%s|%s" % (slot_index, modality)
            if key not in by_slot_modality:
                by_slot_modality[key] = row
    return by_action_id, by_slot_modality


def _resolve_handoff_item(
    queue_item: dict[str, Any],
    *,
    by_action_id: dict[str, dict[str, Any]],
    by_slot_modality: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any] | None, str]:
    action_id = str(queue_item.get("backfill_action_id", "")).strip()
    if action_id and action_id in by_action_id:
        return by_action_id[action_id], "action_id"
    slot_index = _to_int(queue_item.get("backfill_slot_index"), default=0)
    modality = str(queue_item.get("required_modality", "")).strip().lower()
    if slot_index > 0 and modality:
        key = "%s|%s" % (slot_index, modality)
        if key in by_slot_modality:
            return by_slot_modality[key], "slot_modality"
    return None, "none"


def _build_transition_records(
    *,
    submission_queue_report: dict[str, Any],
    handoff_report: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, int], list[str]]:
    queue_items = submission_queue_report.get("queue_items", [])
    if not isinstance(queue_items, list):
        queue_items = []
    queue_status = str(submission_queue_report.get("queue_status", "unknown")).strip().upper() or "UNKNOWN"
    handoff_by_action, handoff_by_slot_modality = _handoff_item_index(handoff_report)

    transitions: list[dict[str, Any]] = []
    submitted_count = 0
    closed_count = 0
    open_count = 0
    blocked_count = 0
    missing_handoff_count = 0
    unknown_count = 0
    warnings: list[str] = []

    for row in queue_items:
        if not isinstance(row, dict):
            continue
        handoff_item, handoff_match_strategy = _resolve_handoff_item(
            row,
            by_action_id=handoff_by_action,
            by_slot_modality=handoff_by_slot_modality,
        )
        queue_item_id = str(row.get("queue_item_id", "")).strip()
        queue_item_status = str(row.get("queue_item_status", "")).strip().lower()
        handoff_status = (
            str(handoff_item.get("queue_status", "")).strip().lower() if isinstance(handoff_item, dict) else ""
        )
        closure_ack = handoff_item.get("closure_acknowledgement", {}) if isinstance(handoff_item, dict) else {}
        if not isinstance(closure_ack, dict):
            closure_ack = {}
        linked_submission = closure_ack.get("linked_submission", {})
        if not isinstance(linked_submission, dict):
            linked_submission = {}
        linked_loop_id = str(linked_submission.get("loop_id", "")).strip()

        if queue_status == "QUEUE_BLOCKED_BY_SUBMISSION_ERRORS" or queue_item_status == "blocked_by_submission_errors":
            transition_state = "blocked_by_submission_errors"
            blocked_count += 1
        elif handoff_status == "closure_acknowledged":
            transition_state = "closed_with_acknowledgement"
            closed_count += 1
            submitted_count += 1
        elif handoff_status == "submission_linked_pending_ack":
            transition_state = "submitted_pending_ack"
            submitted_count += 1
        elif handoff_status == "open" or queue_item_status == "pending_submission":
            transition_state = "pending_submission"
            open_count += 1
        elif queue_status == "QUEUE_NOT_REQUIRED":
            transition_state = "not_required"
        else:
            transition_state = "unknown_transition_state"
            unknown_count += 1

        if handoff_item is None and queue_status != "QUEUE_NOT_REQUIRED":
            missing_handoff_count += 1
            warnings.append("queue_item_without_handoff_transition_row")

        transitions.append(
            {
                "queue_item_id": queue_item_id,
                "queue_item_status_gl37": queue_item_status,
                "handoff_match_strategy": handoff_match_strategy,
                "handoff_queue_status_gl24": handoff_status,
                "transition_state": transition_state,
                "backfill_action_id": str(row.get("backfill_action_id", "")),
                "backfill_slot_index": _to_int(row.get("backfill_slot_index"), default=0),
                "required_modality": str(row.get("required_modality", "")).strip().lower(),
                "reason": str(row.get("reason", "")),
                "owner": str(row.get("owner", "")),
                "linked_submission_loop_id": linked_loop_id,
                "linked_submission_review_task_id": str(linked_submission.get("review_task_id", "")),
                "linked_submission_reviewed_at_utc": str(linked_submission.get("reviewed_at_utc", "")),
            }
        )

    counts = {
        "queue_total_item_count": len(transitions),
        "submitted_item_count": submitted_count,
        "closed_item_count": closed_count,
        "open_item_count": open_count,
        "blocked_item_count": blocked_count,
        "missing_handoff_item_count": missing_handoff_count,
        "unknown_transition_item_count": unknown_count,
    }
    return transitions, counts, _unique_preserve_order(warnings)


def _build_completion_status(
    *,
    queue_status: str,
    queue_total_item_count: int,
    open_item_count: int,
    submitted_item_count: int,
    closed_item_count: int,
    blocked_item_count: int,
) -> str:
    if queue_status == "QUEUE_NOT_REQUIRED":
        return "COMPLETION_NOT_REQUIRED"
    if queue_status == "QUEUE_BLOCKED_BY_SUBMISSION_ERRORS" or blocked_item_count > 0:
        return "COMPLETION_BLOCKED_BY_SUBMISSION_ERRORS"
    if queue_status == "QUEUE_REBUILD_REQUIRED":
        return "COMPLETION_REBUILD_REQUIRED"
    if queue_total_item_count <= 0:
        return "COMPLETION_NOT_REQUIRED"
    if open_item_count == 0 and closed_item_count == queue_total_item_count:
        return "COMPLETION_CLOSED"
    if submitted_item_count > 0:
        return "COMPLETION_SUBMISSION_LINKED"
    return "COMPLETION_IN_PROGRESS"


def _build_cycle_verification(
    *,
    queue_status: str,
    cadence_status: str,
    threshold_met: bool,
    net_new_loop_count: int,
    previous_completion_available: bool,
) -> str:
    if queue_status == "QUEUE_NOT_REQUIRED" and threshold_met:
        return "CYCLE_NOT_REQUIRED"
    if cadence_status == "CADENCE_BASELINE_INITIALIZED" and not previous_completion_available:
        return "CYCLE_BASELINE_INITIALIZED"
    if net_new_loop_count > 0:
        return "CYCLE_NET_NEW_VERIFIED"
    return "CYCLE_NO_NET_NEW_MOVEMENT"


def _build_progress_status(
    *,
    completion_status: str,
    cycle_verification_status: str,
    submitted_item_delta: int,
    closed_item_delta: int,
    net_new_loop_count: int,
) -> str:
    if completion_status == "COMPLETION_NOT_REQUIRED":
        return "COMPLETION_NOT_REQUIRED"
    if completion_status in {"COMPLETION_BLOCKED_BY_SUBMISSION_ERRORS", "COMPLETION_REBUILD_REQUIRED"}:
        return "COMPLETION_BLOCKED"
    if cycle_verification_status == "CYCLE_BASELINE_INITIALIZED":
        return "COMPLETION_BASELINE_INITIALIZED"
    if closed_item_delta > 0 or submitted_item_delta > 0 or net_new_loop_count > 0:
        return "COMPLETION_PROGRESSING"
    return "COMPLETION_STALLED"


def _build_report(
    *,
    submission_queue_report: dict[str, Any],
    submission_queue_report_path: Path,
    submission_throughput_report: dict[str, Any],
    submission_throughput_report_path: Path,
    handoff_report: dict[str, Any],
    handoff_report_path: Path,
    previous_completion_report: dict[str, Any] | None,
    previous_completion_report_path: Path | None,
    owner: str,
) -> dict[str, Any]:
    queue_status = str(submission_queue_report.get("queue_status", "unknown")).strip().upper() or "UNKNOWN"
    queue_summary = submission_queue_report.get("queue_summary", {})
    if not isinstance(queue_summary, dict):
        queue_summary = {}
    queue_refresh = submission_queue_report.get("refresh_cadence", {})
    if not isinstance(queue_refresh, dict):
        queue_refresh = {}
    queue_warning_codes = submission_queue_report.get("warning_codes", [])
    if not isinstance(queue_warning_codes, list):
        queue_warning_codes = []

    throughput_snapshot = submission_throughput_report.get("snapshot", {})
    if not isinstance(throughput_snapshot, dict):
        throughput_snapshot = {}
    throughput_delta = throughput_snapshot.get("delta", {})
    if not isinstance(throughput_delta, dict):
        throughput_delta = {}
    throughput_threshold_met = _is_truthy(submission_throughput_report.get("threshold_met"))
    throughput_net_new_ids = throughput_snapshot.get("net_new_launch_gate_eligible_real_loop_ids", [])
    if not isinstance(throughput_net_new_ids, list):
        throughput_net_new_ids = []
    throughput_net_new_loop_count = _to_int(
        throughput_delta.get("net_new_launch_gate_eligible_real_loop_count", 0),
        default=len(throughput_net_new_ids),
    )

    transitions, transition_counts, transition_warnings = _build_transition_records(
        submission_queue_report=submission_queue_report,
        handoff_report=handoff_report,
    )

    previous_completion_counts = {}
    previous_completion_available = isinstance(previous_completion_report, dict)
    if previous_completion_available:
        previous_completion_counts = previous_completion_report.get("queue_completion_counts", {})
        if not isinstance(previous_completion_counts, dict):
            previous_completion_counts = {}

    submitted_item_delta = transition_counts["submitted_item_count"] - _to_int(
        previous_completion_counts.get("submitted_item_count", 0),
        default=0,
    )
    closed_item_delta = transition_counts["closed_item_count"] - _to_int(
        previous_completion_counts.get("closed_item_count", 0),
        default=0,
    )
    open_item_delta = transition_counts["open_item_count"] - _to_int(
        previous_completion_counts.get("open_item_count", 0),
        default=0,
    )

    completion_status = _build_completion_status(
        queue_status=queue_status,
        queue_total_item_count=transition_counts["queue_total_item_count"],
        open_item_count=transition_counts["open_item_count"],
        submitted_item_count=transition_counts["submitted_item_count"],
        closed_item_count=transition_counts["closed_item_count"],
        blocked_item_count=transition_counts["blocked_item_count"],
    )
    cadence_status = str(queue_refresh.get("cadence_status", "unknown")).strip().upper() or "UNKNOWN"
    cycle_verification_status = _build_cycle_verification(
        queue_status=queue_status,
        cadence_status=cadence_status,
        threshold_met=throughput_threshold_met,
        net_new_loop_count=throughput_net_new_loop_count,
        previous_completion_available=previous_completion_available,
    )
    completion_progress_status = _build_progress_status(
        completion_status=completion_status,
        cycle_verification_status=cycle_verification_status,
        submitted_item_delta=submitted_item_delta,
        closed_item_delta=closed_item_delta,
        net_new_loop_count=throughput_net_new_loop_count,
    )

    warning_codes: list[str] = [str(item) for item in queue_warning_codes if str(item).strip()]
    warning_codes.extend(transition_warnings)
    if transition_counts["missing_handoff_item_count"] > 0:
        warning_codes.append("queue_completion_missing_handoff_transition_rows")
    if cadence_status == "CADENCE_DUE" and throughput_net_new_loop_count <= 0 and not throughput_threshold_met:
        warning_codes.append("queue_cycle_due_without_net_new_eligible_real_loops")
    if (
        transition_counts["submitted_item_count"] > 0
        and throughput_net_new_loop_count <= 0
        and not throughput_threshold_met
    ):
        warning_codes.append("submitted_or_closed_queue_items_without_net_new_eligible_real_loops")
    if completion_progress_status == "COMPLETION_STALLED":
        warning_codes.append("queue_completion_progress_stalled")
    warning_codes = _unique_preserve_order(warning_codes)

    return {
        "schema_version": "real_trial_submission_queue_completion.v1",
        "generated_at_utc": _utc_now_iso(),
        "owner": owner,
        "input_paths": {
            "submission_queue_report": str(submission_queue_report_path),
            "submission_throughput_report": str(submission_throughput_report_path),
            "handoff_report": str(handoff_report_path),
            "previous_completion_report": str(previous_completion_report_path) if previous_completion_report_path else "",
        },
        "queue_status": queue_status,
        "completion_status": completion_status,
        "completion_progress_status": completion_progress_status,
        "cycle_verification_status": cycle_verification_status,
        "warning_codes": warning_codes,
        "queue_completion_counts": {
            "queue_total_item_count": transition_counts["queue_total_item_count"],
            "queue_pending_item_count": _to_int(queue_summary.get("pending_item_count", 0), default=0),
            "queue_blocked_item_count": _to_int(queue_summary.get("blocked_item_count", 0), default=0),
            "submitted_item_count": transition_counts["submitted_item_count"],
            "closed_item_count": transition_counts["closed_item_count"],
            "open_item_count": transition_counts["open_item_count"],
            "blocked_item_count": transition_counts["blocked_item_count"],
            "missing_handoff_item_count": transition_counts["missing_handoff_item_count"],
            "unknown_transition_item_count": transition_counts["unknown_transition_item_count"],
        },
        "cycle_movement_verification": {
            "cadence_status": cadence_status,
            "cadence_refresh_interval_hours": float(queue_refresh.get("refresh_interval_hours", 0.0) or 0.0),
            "cadence_previous_queue_generated_at_utc": str(
                queue_refresh.get("previous_queue_generated_at_utc", "")
            ),
            "cadence_next_refresh_due_utc": str(queue_refresh.get("next_refresh_due_utc", "")),
            "cadence_due_in_hours": float(queue_refresh.get("due_in_hours", 0.0) or 0.0),
            "cadence_evaluated_at_utc": str(queue_refresh.get("evaluated_at_utc", "")),
            "throughput_status": str(submission_throughput_report.get("throughput_status", "unknown")),
            "throughput_threshold_met": throughput_threshold_met,
            "throughput_net_new_loop_count": throughput_net_new_loop_count,
            "throughput_net_new_loop_ids": throughput_net_new_ids,
            "throughput_previous_snapshot_available": bool(
                throughput_snapshot.get("previous_snapshot_available", False)
            ),
            "net_new_movement_verified": throughput_net_new_loop_count > 0 or throughput_threshold_met,
            "submitted_item_delta_from_previous_cycle": submitted_item_delta,
            "closed_item_delta_from_previous_cycle": closed_item_delta,
            "open_item_delta_from_previous_cycle": open_item_delta,
            "previous_completion_snapshot_available": previous_completion_available,
        },
        "queue_transition_records": transitions,
    }


def _render_summary(report: dict[str, Any]) -> str:
    counts = report.get("queue_completion_counts", {})
    if not isinstance(counts, dict):
        counts = {}
    cycle = report.get("cycle_movement_verification", {})
    if not isinstance(cycle, dict):
        cycle = {}
    warnings = report.get("warning_codes", [])
    if not isinstance(warnings, list):
        warnings = []
    transition_rows = report.get("queue_transition_records", [])
    if not isinstance(transition_rows, list):
        transition_rows = []

    lines = [
        "# Real Trial Submission Queue Completion Summary",
        "",
        "- Queue status: `%s`" % str(report.get("queue_status", "unknown")),
        "- Completion status: `%s`" % str(report.get("completion_status", "unknown")),
        "- Completion progress status: `%s`" % str(report.get("completion_progress_status", "unknown")),
        "- Cycle verification status: `%s`" % str(report.get("cycle_verification_status", "unknown")),
        "- Queue total items: `%s`" % str(_to_int(counts.get("queue_total_item_count", 0), default=0)),
        "- Submitted items: `%s`" % str(_to_int(counts.get("submitted_item_count", 0), default=0)),
        "- Closed items: `%s`" % str(_to_int(counts.get("closed_item_count", 0), default=0)),
        "- Open items: `%s`" % str(_to_int(counts.get("open_item_count", 0), default=0)),
        "- Missing handoff items: `%s`" % str(_to_int(counts.get("missing_handoff_item_count", 0), default=0)),
        "- Cadence status: `%s`" % str(cycle.get("cadence_status", "unknown")),
        "- Throughput net-new loops: `%s`" % str(_to_int(cycle.get("throughput_net_new_loop_count", 0), default=0)),
        "- Net-new movement verified: `%s`" % str(_is_truthy(cycle.get("net_new_movement_verified"))).lower(),
        "",
        "## Warning Codes",
    ]
    if warnings:
        for warning in warnings:
            lines.append("- `%s`" % str(warning))
    else:
        lines.append("- none")
    lines.extend(["", "## Queue Transition Records"])
    if transition_rows:
        for row in transition_rows:
            if not isinstance(row, dict):
                continue
            lines.append(
                "- `%s` transition=%s queue_status=%s handoff_status=%s modality=%s action=%s loop=%s"
                % (
                    str(row.get("queue_item_id", "")),
                    str(row.get("transition_state", "")),
                    str(row.get("queue_item_status_gl37", "")),
                    str(row.get("handoff_queue_status_gl24", "")),
                    str(row.get("required_modality", "")),
                    str(row.get("backfill_action_id", "")),
                    str(row.get("linked_submission_loop_id", "")),
                )
            )
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    submission_queue_report_path = Path(str(args.submission_queue_report).strip()).resolve()
    submission_throughput_report_path = Path(str(args.submission_throughput_report).strip()).resolve()
    handoff_report_path = Path(str(args.handoff_report).strip()).resolve()
    output_path = None if str(args.output).strip() == "-" else Path(str(args.output).strip()).resolve()
    summary_path = None if str(args.summary_output).strip() == "-" else Path(str(args.summary_output).strip()).resolve()
    owner = str(args.owner).strip() or "controlled-beta-ops"

    try:
        if not submission_queue_report_path.is_file():
            raise ValueError("Submission queue report path does not exist: %s" % submission_queue_report_path)
        if not submission_throughput_report_path.is_file():
            raise ValueError(
                "Submission throughput report path does not exist: %s" % submission_throughput_report_path
            )
        if not handoff_report_path.is_file():
            raise ValueError("Handoff report path does not exist: %s" % handoff_report_path)
        submission_queue_report = _read_json(submission_queue_report_path)
        submission_throughput_report = _read_json(submission_throughput_report_path)
        handoff_report = _read_json(handoff_report_path)

        previous_completion_report_path: Path | None = None
        previous_completion_report: dict[str, Any] | None = None
        previous_arg = str(args.previous_completion_report).strip()
        if previous_arg:
            previous_completion_report_path = Path(previous_arg).resolve()
        elif output_path is not None:
            previous_completion_report_path = output_path
        if previous_completion_report_path is not None and previous_completion_report_path.is_file():
            previous_completion_report = _read_json(previous_completion_report_path)

        report = _build_report(
            submission_queue_report=submission_queue_report,
            submission_queue_report_path=submission_queue_report_path,
            submission_throughput_report=submission_throughput_report,
            submission_throughput_report_path=submission_throughput_report_path,
            handoff_report=handoff_report,
            handoff_report_path=handoff_report_path,
            previous_completion_report=previous_completion_report,
            previous_completion_report_path=previous_completion_report_path
            if previous_completion_report is not None
            else None,
            owner=owner,
        )
        summary = _render_summary(report)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print("Real trial submission queue completion generation failed: %s" % exc, file=sys.stderr)
        return 2

    if output_path is not None:
        _write_text(output_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print("Real trial submission queue completion report written: %s" % output_path)
    if summary_path is not None:
        _write_text(summary_path, summary)
        print("Real trial submission queue completion summary written: %s" % summary_path)

    counts = report.get("queue_completion_counts", {})
    if not isinstance(counts, dict):
        counts = {}
    cycle = report.get("cycle_movement_verification", {})
    if not isinstance(cycle, dict):
        cycle = {}
    print(
        "Real trial submission queue completion status=%s progress=%s submitted=%s closed=%s net_new=%s cycle=%s"
        % (
            str(report.get("completion_status", "unknown")),
            str(report.get("completion_progress_status", "unknown")),
            _to_int(counts.get("submitted_item_count", 0), default=0),
            _to_int(counts.get("closed_item_count", 0), default=0),
            _to_int(cycle.get("throughput_net_new_loop_count", 0), default=0),
            str(report.get("cycle_verification_status", "unknown")),
        )
    )
    if args.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    if bool(args.fail_on_stalled) and str(report.get("completion_progress_status", "")).strip() == "COMPLETION_STALLED":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

