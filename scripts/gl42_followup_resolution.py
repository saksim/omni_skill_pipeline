from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUBMISSION_QUEUE_FOLLOWUP_REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-report.json"
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
DEFAULT_SUBMISSION_CONSUMPTION_REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-consumption-report.json"
)
DEFAULT_OUTPUT_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-report.json"
)
DEFAULT_SUMMARY_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-summary.md"
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate GL-42 follow-up resolution diagnostics by linking GL-41 open follow-up "
            "actions with GL-24 handoff queue state and GL-33 submission consumption evidence."
        )
    )
    parser.add_argument(
        "--submission-queue-followup-report",
        default=str(DEFAULT_SUBMISSION_QUEUE_FOLLOWUP_REPORT_PATH),
    )
    parser.add_argument("--handoff-report", default=str(DEFAULT_HANDOFF_REPORT_PATH))
    parser.add_argument(
        "--backfill-submission-consumption-report",
        default=str(DEFAULT_SUBMISSION_CONSUMPTION_REPORT_PATH),
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help='Follow-up resolution report output path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--summary-output",
        default=str(DEFAULT_SUMMARY_PATH),
        help='Follow-up resolution summary output path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--owner",
        default="controlled-beta-ops",
        help="Fallback owner used when follow-up rows do not provide owner.",
    )
    parser.add_argument(
        "--fail-on-unresolved",
        action="store_true",
        help="Exit with code 1 when unresolved open follow-up actions remain.",
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


def _handoff_by_action_id(handoff_report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = handoff_report.get("queue_items", [])
    if not isinstance(rows, list):
        rows = []
    index: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        action_id = str(row.get("action_id", "")).strip()
        if action_id and action_id not in index:
            index[action_id] = row
    return index


def _submission_by_action_id(consumption_report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = consumption_report.get("consumption_linkage_records", [])
    if not isinstance(rows, list):
        rows = []
    index: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        action_id = str(row.get("backfill_action_id", "")).strip()
        if action_id and action_id not in index:
            index[action_id] = row
    return index


def _row_resolution(
    *,
    row: dict[str, Any],
    fallback_owner: str,
    handoff_row: dict[str, Any] | None,
    consumption_row: dict[str, Any] | None,
) -> dict[str, Any]:
    action_status_gl41 = str(row.get("followup_action_status", "")).strip().lower()
    followup_action_type = str(row.get("followup_action_type", "")).strip()
    action_id = str(row.get("backfill_action_id", "")).strip()
    queue_status_gl24 = (
        str(handoff_row.get("queue_status", "")).strip().lower()
        if isinstance(handoff_row, dict)
        else ""
    )
    linked_loop_id = ""
    if isinstance(handoff_row, dict):
        closure_ack = handoff_row.get("closure_acknowledgement", {})
        if isinstance(closure_ack, dict):
            linked_submission = closure_ack.get("linked_submission", {})
            if isinstance(linked_submission, dict):
                linked_loop_id = str(linked_submission.get("loop_id", "")).strip()
    consumed_loop_id = str(consumption_row.get("loop_id", "")).strip() if isinstance(consumption_row, dict) else ""

    if action_status_gl41 != "open":
        resolution_state = "already_closed_in_gl41"
        resolution_status = "resolved"
    elif not action_id:
        resolution_state = "unresolved_missing_backfill_action_id"
        resolution_status = "unresolved"
    elif followup_action_type == "complete_acknowledgement_closure":
        if queue_status_gl24 == "closure_acknowledged":
            resolution_state = "resolved_closure_acknowledged"
            resolution_status = "resolved"
        elif queue_status_gl24 == "submission_linked_pending_ack":
            resolution_state = "in_progress_submission_linked_pending_ack"
            resolution_status = "in_progress"
        elif consumed_loop_id:
            resolution_state = "in_progress_submission_consumed_not_handed_off"
            resolution_status = "in_progress"
        else:
            resolution_state = "unresolved_no_submission_progress"
            resolution_status = "unresolved"
    elif followup_action_type == "resolve_stale_rollover":
        if queue_status_gl24 == "closure_acknowledged":
            resolution_state = "resolved_closure_acknowledged"
            resolution_status = "resolved"
        elif queue_status_gl24 == "submission_linked_pending_ack":
            resolution_state = "in_progress_submission_linked_pending_ack"
            resolution_status = "in_progress"
        elif consumed_loop_id:
            resolution_state = "in_progress_submission_consumed_not_handed_off"
            resolution_status = "in_progress"
        else:
            resolution_state = "unresolved_no_submission_progress"
            resolution_status = "unresolved"
    elif followup_action_type in {
        "resolve_blocked_submission_errors",
        "resolve_escalation_required_closure",
        "rebuild_commitment_closure_pipeline",
    }:
        if queue_status_gl24 == "closure_acknowledged":
            resolution_state = "resolved_closure_acknowledged"
            resolution_status = "resolved"
        elif queue_status_gl24 == "submission_linked_pending_ack":
            resolution_state = "in_progress_submission_linked_pending_ack"
            resolution_status = "in_progress"
        elif consumed_loop_id:
            resolution_state = "in_progress_submission_consumed_not_handed_off"
            resolution_status = "in_progress"
        else:
            resolution_state = "unresolved_blocker_persists"
            resolution_status = "unresolved"
    else:
        if queue_status_gl24 == "closure_acknowledged":
            resolution_state = "resolved_closure_acknowledged"
            resolution_status = "resolved"
        elif queue_status_gl24 == "submission_linked_pending_ack":
            resolution_state = "in_progress_submission_linked_pending_ack"
            resolution_status = "in_progress"
        elif consumed_loop_id:
            resolution_state = "in_progress_submission_consumed_not_handed_off"
            resolution_status = "in_progress"
        else:
            resolution_state = "unresolved_unknown_followup_type"
            resolution_status = "unresolved"

    owner = str(row.get("owner", "")).strip() or fallback_owner
    return {
        "followup_action_id": str(row.get("followup_action_id", "")).strip(),
        "owner": owner,
        "followup_action_type": followup_action_type,
        "followup_action_status_gl41": action_status_gl41,
        "followup_reason_code": str(row.get("followup_reason_code", "")).strip(),
        "queue_item_id": str(row.get("queue_item_id", "")).strip(),
        "backfill_action_id": action_id,
        "required_modality": str(row.get("required_modality", "")).strip().lower(),
        "priority_rank": _to_int(row.get("priority_rank", 0), default=0),
        "resolution_status": resolution_status,
        "resolution_state": resolution_state,
        "handoff_queue_status_gl24": queue_status_gl24,
        "submission_consumed_loop_id_gl33": consumed_loop_id,
        "handoff_linked_loop_id_gl24": linked_loop_id,
        "cycle_due_at_utc": str(row.get("cycle_due_at_utc", "")).strip(),
    }


def _owner_counts(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        owner = str(row.get("owner", "")).strip() or "unassigned"
        bucket = counts.setdefault(
            owner,
            {
                "total_action_count": 0,
                "open_action_count_gl41": 0,
                "resolved_action_count": 0,
                "in_progress_action_count": 0,
                "unresolved_action_count": 0,
            },
        )
        bucket["total_action_count"] += 1
        if str(row.get("followup_action_status_gl41", "")) == "open":
            bucket["open_action_count_gl41"] += 1
        resolution_status = str(row.get("resolution_status", "")).strip()
        if resolution_status in bucket:
            bucket[resolution_status] += 1
        elif resolution_status == "resolved":
            bucket["resolved_action_count"] += 1
        elif resolution_status == "in_progress":
            bucket["in_progress_action_count"] += 1
        elif resolution_status == "unresolved":
            bucket["unresolved_action_count"] += 1
    return counts


def _build_status(
    *,
    open_action_count: int,
    unresolved_action_count: int,
    in_progress_action_count: int,
    resolved_action_count: int,
    consumption_status: str,
    invalid_submission_count: int,
    unresolved_submission_count: int,
) -> str:
    if open_action_count == 0:
        return "FOLLOWUP_RESOLUTION_NOT_REQUIRED"
    if unresolved_action_count == 0 and in_progress_action_count == 0:
        return "FOLLOWUP_RESOLUTION_COMPLETE"
    if invalid_submission_count > 0 or unresolved_submission_count > 0:
        return "FOLLOWUP_RESOLUTION_BLOCKED_BY_SUBMISSION_ERRORS"
    if resolved_action_count > 0 or in_progress_action_count > 0:
        return "FOLLOWUP_RESOLUTION_IN_PROGRESS"
    if consumption_status in {"NO_TEMPLATE_ROWS", "NO_SUBMISSIONS_PROVIDED"}:
        return "FOLLOWUP_RESOLUTION_PENDING_SUBMISSIONS"
    return "FOLLOWUP_RESOLUTION_UNRESOLVED"


def _build_report(
    *,
    followup_report: dict[str, Any],
    followup_report_path: Path,
    handoff_report: dict[str, Any],
    handoff_report_path: Path,
    consumption_report: dict[str, Any],
    consumption_report_path: Path,
    owner: str,
) -> dict[str, Any]:
    followup_rows = followup_report.get("followup_action_rows", [])
    if not isinstance(followup_rows, list):
        followup_rows = []

    handoff_index = _handoff_by_action_id(handoff_report)
    consumption_index = _submission_by_action_id(consumption_report)
    consumption_counts = consumption_report.get("counts", {})
    if not isinstance(consumption_counts, dict):
        consumption_counts = {}

    resolution_rows: list[dict[str, Any]] = []
    warning_codes: list[str] = []

    for row in followup_rows:
        if not isinstance(row, dict):
            continue
        action_id = str(row.get("backfill_action_id", "")).strip()
        if not action_id:
            warning_codes.append("followup_action_missing_backfill_action_id")
        handoff_row = handoff_index.get(action_id)
        consumption_row = consumption_index.get(action_id)
        if str(row.get("followup_action_status", "")).strip().lower() == "open" and handoff_row is None:
            warning_codes.append("open_followup_action_missing_handoff_queue_row")
        resolution_rows.append(
            _row_resolution(
                row=row,
                fallback_owner=owner,
                handoff_row=handoff_row,
                consumption_row=consumption_row,
            )
        )

    resolution_rows.sort(
        key=lambda row: (
            0 if str(row.get("followup_action_status_gl41", "")) == "open" else 1,
            0 if str(row.get("resolution_status", "")) == "unresolved" else 1,
            0 if str(row.get("resolution_status", "")) == "in_progress" else 1,
            _to_int(row.get("priority_rank", 0), default=0) <= 0,
            _to_int(row.get("priority_rank", 0), default=0),
            str(row.get("required_modality", "")),
            str(row.get("backfill_action_id", "")),
            str(row.get("followup_action_id", "")),
        )
    )

    total_action_count = len(resolution_rows)
    open_action_count = sum(
        1
        for row in resolution_rows
        if str(row.get("followup_action_status_gl41", "")).strip() == "open"
    )
    closed_action_count_gl41 = sum(
        1
        for row in resolution_rows
        if str(row.get("followup_action_status_gl41", "")).strip() != "open"
    )
    resolved_action_count = sum(
        1
        for row in resolution_rows
        if str(row.get("resolution_status", "")).strip() == "resolved"
    )
    in_progress_action_count = sum(
        1
        for row in resolution_rows
        if str(row.get("resolution_status", "")).strip() == "in_progress"
    )
    unresolved_action_count = sum(
        1
        for row in resolution_rows
        if str(row.get("resolution_status", "")).strip() == "unresolved"
    )
    submission_linked_action_count = sum(
        1
        for row in resolution_rows
        if str(row.get("handoff_queue_status_gl24", "")).strip()
        in {"submission_linked_pending_ack", "closure_acknowledged"}
    )
    closure_acknowledged_action_count = sum(
        1
        for row in resolution_rows
        if str(row.get("handoff_queue_status_gl24", "")).strip() == "closure_acknowledged"
    )
    consumed_submission_action_count = sum(
        1
        for row in resolution_rows
        if str(row.get("submission_consumed_loop_id_gl33", "")).strip()
    )

    consumption_status = (
        str(consumption_report.get("consumption_status", "unknown")).strip().upper() or "UNKNOWN"
    )
    invalid_submission_count = _to_int(
        consumption_counts.get("invalid_submission_count", 0),
        default=0,
    )
    unresolved_submission_count = _to_int(
        consumption_counts.get("unresolved_submission_count", 0),
        default=0,
    )

    if unresolved_action_count > 0:
        warning_codes.append("open_followup_actions_unresolved")
    if consumption_status in {"NO_TEMPLATE_ROWS", "NO_SUBMISSIONS_PROVIDED"}:
        warning_codes.append("submission_consumption_not_ready")
    if invalid_submission_count > 0:
        warning_codes.append("submission_consumption_invalid_rows_present")
    if unresolved_submission_count > 0:
        warning_codes.append("submission_consumption_unresolved_rows_present")
    warning_codes = _unique_preserve_order(warning_codes)

    return {
        "schema_version": "real_trial_submission_queue_followup_resolution.v1",
        "generated_at_utc": _utc_now_iso(),
        "owner": owner,
        "input_paths": {
            "submission_queue_followup_report": str(followup_report_path),
            "handoff_report": str(handoff_report_path),
            "backfill_submission_consumption_report": str(consumption_report_path),
        },
        "followup_status_gl41": str(followup_report.get("followup_status", "unknown")),
        "commitment_closure_status_gl40": str(
            followup_report.get("commitment_closure_status_gl40", "unknown")
        ),
        "cadence_run_closure_status_gl40": str(
            followup_report.get("cadence_run_closure_status_gl40", "unknown")
        ),
        "handoff_status_gl24": str(handoff_report.get("handoff_status", "unknown")),
        "submission_consumption_status_gl33": consumption_status,
        "followup_resolution_status": _build_status(
            open_action_count=open_action_count,
            unresolved_action_count=unresolved_action_count,
            in_progress_action_count=in_progress_action_count,
            resolved_action_count=resolved_action_count,
            consumption_status=consumption_status,
            invalid_submission_count=invalid_submission_count,
            unresolved_submission_count=unresolved_submission_count,
        ),
        "warning_codes": warning_codes,
        "followup_resolution_counts": {
            "total_action_count": total_action_count,
            "open_action_count_gl41": open_action_count,
            "closed_action_count_gl41": closed_action_count_gl41,
            "resolved_action_count": resolved_action_count,
            "in_progress_action_count": in_progress_action_count,
            "unresolved_action_count": unresolved_action_count,
            "submission_linked_action_count": submission_linked_action_count,
            "closure_acknowledged_action_count": closure_acknowledged_action_count,
            "consumed_submission_action_count": consumed_submission_action_count,
            "submission_consumption_invalid_submission_count": invalid_submission_count,
            "submission_consumption_unresolved_submission_count": unresolved_submission_count,
        },
        "owner_followup_resolution_counts": _owner_counts(resolution_rows),
        "followup_resolution_rows": resolution_rows,
    }


def _render_summary(report: dict[str, Any]) -> str:
    counts = report.get("followup_resolution_counts", {})
    if not isinstance(counts, dict):
        counts = {}
    warnings = report.get("warning_codes", [])
    if not isinstance(warnings, list):
        warnings = []
    rows = report.get("followup_resolution_rows", [])
    if not isinstance(rows, list):
        rows = []

    lines = [
        "# Real Trial Submission Queue Follow-Up Resolution Summary",
        "",
        "- Follow-up resolution status: `%s`"
        % str(report.get("followup_resolution_status", "unknown")),
        "- GL-41 follow-up status: `%s`" % str(report.get("followup_status_gl41", "unknown")),
        "- GL-24 handoff status: `%s`" % str(report.get("handoff_status_gl24", "unknown")),
        "- GL-33 submission consumption status: `%s`"
        % str(report.get("submission_consumption_status_gl33", "unknown")),
        "- Total actions: `%s`" % str(_to_int(counts.get("total_action_count", 0), default=0)),
        "- Open actions (GL-41): `%s`" % str(_to_int(counts.get("open_action_count_gl41", 0), default=0)),
        "- Resolved actions: `%s`" % str(_to_int(counts.get("resolved_action_count", 0), default=0)),
        "- In-progress actions: `%s`" % str(_to_int(counts.get("in_progress_action_count", 0), default=0)),
        "- Unresolved actions: `%s`" % str(_to_int(counts.get("unresolved_action_count", 0), default=0)),
        "",
        "## Warning Codes",
    ]
    if warnings:
        for warning in warnings:
            lines.append("- `%s`" % str(warning))
    else:
        lines.append("- none")

    lines.extend(["", "## Resolution Rows"])
    if rows:
        for row in rows:
            if not isinstance(row, dict):
                continue
            lines.append(
                "- `%s` status_gl41=%s resolution=%s state=%s action=%s handoff=%s consumed_loop=%s"
                % (
                    str(row.get("followup_action_id", "")),
                    str(row.get("followup_action_status_gl41", "")),
                    str(row.get("resolution_status", "")),
                    str(row.get("resolution_state", "")),
                    str(row.get("backfill_action_id", "")),
                    str(row.get("handoff_queue_status_gl24", "")),
                    str(row.get("submission_consumed_loop_id_gl33", "")),
                )
            )
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    followup_report_path = Path(str(args.submission_queue_followup_report).strip()).resolve()
    handoff_report_path = Path(str(args.handoff_report).strip()).resolve()
    consumption_report_path = Path(str(args.backfill_submission_consumption_report).strip()).resolve()
    output_path = None if str(args.output).strip() == "-" else Path(str(args.output).strip()).resolve()
    summary_path = None if str(args.summary_output).strip() == "-" else Path(str(args.summary_output).strip()).resolve()
    owner = str(args.owner).strip() or "controlled-beta-ops"

    try:
        for path, label in (
            (followup_report_path, "submission queue follow-up report"),
            (handoff_report_path, "handoff report"),
            (consumption_report_path, "backfill submission consumption report"),
        ):
            if not path.is_file():
                raise ValueError("%s path does not exist: %s" % (label, path))
        followup_report = _read_json(followup_report_path)
        handoff_report = _read_json(handoff_report_path)
        consumption_report = _read_json(consumption_report_path)
        report = _build_report(
            followup_report=followup_report,
            followup_report_path=followup_report_path,
            handoff_report=handoff_report,
            handoff_report_path=handoff_report_path,
            consumption_report=consumption_report,
            consumption_report_path=consumption_report_path,
            owner=owner,
        )
        summary = _render_summary(report)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print("Real trial submission queue follow-up resolution generation failed: %s" % exc, file=sys.stderr)
        return 2

    if output_path is not None:
        _write_text(output_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print("Real trial submission queue follow-up resolution report written: %s" % output_path)
    if summary_path is not None:
        _write_text(summary_path, summary)
        print("Real trial submission queue follow-up resolution summary written: %s" % summary_path)

    counts = report.get("followup_resolution_counts", {})
    if not isinstance(counts, dict):
        counts = {}
    unresolved_count = _to_int(counts.get("unresolved_action_count", 0), default=0)
    print(
        "Real trial submission queue follow-up resolution status=%s unresolved=%s"
        % (
            str(report.get("followup_resolution_status", "unknown")),
            unresolved_count,
        )
    )
    if args.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    if bool(args.fail_on_unresolved) and unresolved_count > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
