from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATIONS_REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalations-report.json"
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
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-acknowledgements-report.json"
)
DEFAULT_SUMMARY_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-acknowledgements-summary.md"
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate GL-44 acknowledgement-closure diagnostics for GL-43 escalation rows "
            "using GL-24 handoff queue state."
        )
    )
    parser.add_argument(
        "--submission-queue-followup-resolution-escalations-report",
        default=str(DEFAULT_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATIONS_REPORT_PATH),
    )
    parser.add_argument("--handoff-report", default=str(DEFAULT_HANDOFF_REPORT_PATH))
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help='Acknowledgement report output path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--summary-output",
        default=str(DEFAULT_SUMMARY_PATH),
        help='Acknowledgement summary output path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--owner",
        default="controlled-beta-ops",
        help="Fallback owner used when row owner is missing.",
    )
    parser.add_argument(
        "--fail-on-open",
        action="store_true",
        help="Exit with code 1 when open acknowledgement items remain.",
    )
    parser.add_argument(
        "--fail-on-blocked",
        action="store_true",
        help="Exit with code 1 when blocked acknowledgement items remain.",
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


def _normalize_owner(value: Any, *, fallback_owner: str) -> str:
    owner = str(value or "").strip()
    return owner or fallback_owner


def _handoff_indexes(
    handoff_report: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    rows = handoff_report.get("queue_items", [])
    if not isinstance(rows, list):
        rows = []
    by_queue_item_id: dict[str, dict[str, Any]] = {}
    by_action_id: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        queue_item_id = str(row.get("queue_item_id", "")).strip()
        action_id = str(row.get("action_id", "")).strip()
        if queue_item_id and queue_item_id not in by_queue_item_id:
            by_queue_item_id[queue_item_id] = row
        if action_id and action_id not in by_action_id:
            by_action_id[action_id] = row
    return by_queue_item_id, by_action_id


def _resolve_handoff_row(
    escalation_row: dict[str, Any],
    *,
    by_queue_item_id: dict[str, dict[str, Any]],
    by_action_id: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any] | None, str]:
    queue_item_id = str(escalation_row.get("queue_item_id", "")).strip()
    if queue_item_id and queue_item_id in by_queue_item_id:
        return by_queue_item_id[queue_item_id], "queue_item_id"
    action_id = str(escalation_row.get("backfill_action_id", "")).strip()
    if action_id and action_id in by_action_id:
        return by_action_id[action_id], "backfill_action_id"
    return None, "none"


def _build_ack_row(
    *,
    escalation_row: dict[str, Any],
    handoff_row: dict[str, Any] | None,
    handoff_match_strategy: str,
    fallback_owner: str,
) -> tuple[dict[str, Any], str]:
    escalation_item_id = str(escalation_row.get("escalation_item_id", "")).strip()
    queue_item_id = str(escalation_row.get("queue_item_id", "")).strip()
    action_id = str(escalation_row.get("backfill_action_id", "")).strip()
    owner = _normalize_owner(escalation_row.get("owner", ""), fallback_owner=fallback_owner)

    handoff_queue_status = ""
    closure_ack_status = ""
    linked_submission_loop_id = ""
    linked_submission_review_task_id = ""
    linked_submission_reviewed_at_utc = ""
    acknowledged_by = ""
    acknowledged_at_utc = ""
    acknowledged_loop_id = ""

    if isinstance(handoff_row, dict):
        handoff_queue_status = str(handoff_row.get("queue_status", "")).strip().lower()
        closure_ack = handoff_row.get("closure_acknowledgement", {})
        if isinstance(closure_ack, dict):
            closure_ack_status = str(closure_ack.get("status", "")).strip().lower()
            linked_submission = closure_ack.get("linked_submission", {})
            if isinstance(linked_submission, dict):
                linked_submission_loop_id = str(linked_submission.get("loop_id", "")).strip()
                linked_submission_review_task_id = str(
                    linked_submission.get("review_task_id", "")
                ).strip()
                linked_submission_reviewed_at_utc = str(
                    linked_submission.get("reviewed_at_utc", "")
                ).strip()
            operator_ack = closure_ack.get("operator_acknowledgement", {})
            if isinstance(operator_ack, dict):
                acknowledged_by = str(operator_ack.get("acknowledged_by", "")).strip()
                acknowledged_at_utc = str(operator_ack.get("acknowledged_at_utc", "")).strip()
                acknowledged_loop_id = str(operator_ack.get("submitted_loop_id", "")).strip()

    if not isinstance(handoff_row, dict):
        ack_state = "blocked_missing_handoff_queue_item"
        ack_status = "blocked"
        item_status = "open"
    elif handoff_queue_status == "closure_acknowledged" or closure_ack_status == "acknowledged":
        ack_state = "resolved_closure_acknowledged"
        ack_status = "resolved_acknowledged"
        item_status = "closed"
    elif handoff_queue_status == "submission_linked_pending_ack" or closure_ack_status == "pending_operator_acknowledgement":
        ack_state = "pending_operator_acknowledgement"
        ack_status = "pending_ack"
        item_status = "open"
    elif handoff_queue_status == "open" or closure_ack_status == "pending_submission":
        ack_state = "blocked_submission_not_linked"
        ack_status = "blocked"
        item_status = "open"
    else:
        ack_state = "blocked_unknown_handoff_state"
        ack_status = "blocked"
        item_status = "open"

    item_id_suffix = escalation_item_id or queue_item_id or action_id or "unbound"
    row = {
        "acknowledgement_item_id": "gl44-ack-%s" % item_id_suffix,
        "acknowledgement_item_status": item_status,
        "acknowledgement_status": ack_status,
        "acknowledgement_state": ack_state,
        "owner": owner,
        "escalation_item_id_gl43": escalation_item_id,
        "escalation_item_status_gl43": str(escalation_row.get("escalation_item_status", "")).strip().lower(),
        "escalation_severity_gl43": str(escalation_row.get("escalation_severity", "")).strip().lower(),
        "escalation_reason_code_gl43": str(escalation_row.get("escalation_reason_code", "")).strip(),
        "escalation_action_gl43": str(escalation_row.get("escalation_action", "")).strip(),
        "followup_action_id_gl41": str(escalation_row.get("followup_action_id", "")).strip(),
        "queue_item_id": queue_item_id,
        "backfill_action_id": action_id,
        "required_modality": str(escalation_row.get("required_modality", "")).strip().lower(),
        "priority_rank": _to_int(escalation_row.get("priority_rank", 0), default=0),
        "handoff_match_strategy_gl24": handoff_match_strategy,
        "handoff_queue_status_gl24": handoff_queue_status,
        "closure_acknowledgement_status_gl24": closure_ack_status,
        "linked_submission_loop_id_gl24": linked_submission_loop_id,
        "linked_submission_review_task_id_gl24": linked_submission_review_task_id,
        "linked_submission_reviewed_at_utc_gl24": linked_submission_reviewed_at_utc,
        "operator_acknowledged_by_gl24": acknowledged_by,
        "operator_acknowledged_at_utc_gl24": acknowledged_at_utc,
        "operator_acknowledged_loop_id_gl24": acknowledged_loop_id,
        "cycle_due_at_utc": str(escalation_row.get("cycle_due_at_utc", "")).strip(),
    }
    return row, ack_status


def _build_ack_rows(
    *,
    escalation_report: dict[str, Any],
    handoff_report: dict[str, Any],
    fallback_owner: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    escalation_rows = escalation_report.get("followup_resolution_escalation_rows", [])
    if not isinstance(escalation_rows, list):
        escalation_rows = []
    by_queue_item_id, by_action_id = _handoff_indexes(handoff_report)

    rows: list[dict[str, Any]] = []
    warning_codes: list[str] = []
    for escalation_row in escalation_rows:
        if not isinstance(escalation_row, dict):
            continue
        handoff_row, handoff_match_strategy = _resolve_handoff_row(
            escalation_row,
            by_queue_item_id=by_queue_item_id,
            by_action_id=by_action_id,
        )
        row, ack_status = _build_ack_row(
            escalation_row=escalation_row,
            handoff_row=handoff_row,
            handoff_match_strategy=handoff_match_strategy,
            fallback_owner=fallback_owner,
        )
        rows.append(row)
        if handoff_row is None:
            warning_codes.append("escalation_ack_missing_handoff_row")
        if ack_status == "pending_ack":
            warning_codes.append("escalation_ack_pending_operator_acknowledgement")
        if ack_status == "blocked":
            warning_codes.append("escalation_ack_blocked")

    rows.sort(
        key=lambda row: (
            0 if str(row.get("acknowledgement_status", "")) == "blocked" else 1,
            0 if str(row.get("acknowledgement_status", "")) == "pending_ack" else 1,
            _to_int(row.get("priority_rank", 0), default=0) <= 0,
            _to_int(row.get("priority_rank", 0), default=0),
            str(row.get("required_modality", "")),
            str(row.get("backfill_action_id", "")),
            str(row.get("acknowledgement_item_id", "")),
        )
    )
    return rows, _unique_preserve_order(warning_codes)


def _owner_counts(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        owner = str(row.get("owner", "")).strip() or "unassigned"
        ack_status = str(row.get("acknowledgement_status", "")).strip().lower()
        bucket = counts.setdefault(
            owner,
            {
                "total_item_count": 0,
                "open_item_count": 0,
                "resolved_acknowledged_item_count": 0,
                "pending_ack_item_count": 0,
                "blocked_item_count": 0,
            },
        )
        bucket["total_item_count"] += 1
        if str(row.get("acknowledgement_item_status", "")).strip().lower() == "open":
            bucket["open_item_count"] += 1
        if ack_status == "resolved_acknowledged":
            bucket["resolved_acknowledged_item_count"] += 1
        elif ack_status == "pending_ack":
            bucket["pending_ack_item_count"] += 1
        elif ack_status == "blocked":
            bucket["blocked_item_count"] += 1
    return counts


def _build_ack_status(
    *,
    total_item_count: int,
    pending_ack_item_count: int,
    blocked_item_count: int,
) -> str:
    if total_item_count == 0:
        return "FOLLOWUP_RESOLUTION_ESCALATION_ACK_NOT_REQUIRED"
    if blocked_item_count > 0:
        return "FOLLOWUP_RESOLUTION_ESCALATION_ACK_BLOCKED_ACTION_REQUIRED"
    if pending_ack_item_count > 0:
        return "FOLLOWUP_RESOLUTION_ESCALATION_ACK_PENDING_ACTION_REQUIRED"
    return "FOLLOWUP_RESOLUTION_ESCALATION_ACK_COMPLETE"


def _build_report(
    *,
    escalation_report: dict[str, Any],
    escalation_report_path: Path,
    handoff_report: dict[str, Any],
    handoff_report_path: Path,
    owner: str,
) -> dict[str, Any]:
    rows, warning_codes = _build_ack_rows(
        escalation_report=escalation_report,
        handoff_report=handoff_report,
        fallback_owner=owner,
    )
    total_item_count = len(rows)
    open_item_count = sum(
        1
        for row in rows
        if str(row.get("acknowledgement_item_status", "")).strip().lower() == "open"
    )
    resolved_acknowledged_item_count = sum(
        1
        for row in rows
        if str(row.get("acknowledgement_status", "")).strip().lower() == "resolved_acknowledged"
    )
    pending_ack_item_count = sum(
        1
        for row in rows
        if str(row.get("acknowledgement_status", "")).strip().lower() == "pending_ack"
    )
    blocked_item_count = sum(
        1
        for row in rows
        if str(row.get("acknowledgement_status", "")).strip().lower() == "blocked"
    )
    if open_item_count > 0:
        warning_codes.append("open_escalation_acknowledgement_items_present")
    warning_codes = _unique_preserve_order(warning_codes)

    return {
        "schema_version": "real_trial_submission_queue_followup_resolution_escalation_acknowledgements.v1",
        "generated_at_utc": _utc_now_iso(),
        "owner": owner,
        "input_paths": {
            "submission_queue_followup_resolution_escalations_report": str(escalation_report_path),
            "handoff_report": str(handoff_report_path),
        },
        "followup_resolution_escalation_status_gl43": str(
            escalation_report.get("followup_resolution_escalation_status", "unknown")
        ),
        "handoff_status_gl24": str(handoff_report.get("handoff_status", "unknown")),
        "followup_resolution_escalation_acknowledgement_status": _build_ack_status(
            total_item_count=total_item_count,
            pending_ack_item_count=pending_ack_item_count,
            blocked_item_count=blocked_item_count,
        ),
        "warning_codes": warning_codes,
        "followup_resolution_escalation_acknowledgement_counts": {
            "total_item_count": total_item_count,
            "open_item_count": open_item_count,
            "resolved_acknowledged_item_count": resolved_acknowledged_item_count,
            "pending_ack_item_count": pending_ack_item_count,
            "blocked_item_count": blocked_item_count,
        },
        "owner_followup_resolution_escalation_acknowledgement_counts": _owner_counts(rows),
        "followup_resolution_escalation_acknowledgement_rows": rows,
    }


def _render_summary(report: dict[str, Any]) -> str:
    counts = report.get("followup_resolution_escalation_acknowledgement_counts", {})
    if not isinstance(counts, dict):
        counts = {}
    warning_codes = report.get("warning_codes", [])
    if not isinstance(warning_codes, list):
        warning_codes = []
    rows = report.get("followup_resolution_escalation_acknowledgement_rows", [])
    if not isinstance(rows, list):
        rows = []

    lines = [
        "# Real Trial Submission Queue Follow-Up Resolution Escalation Acknowledgements Summary",
        "",
        "- GL-43 escalation status: `%s`"
        % str(report.get("followup_resolution_escalation_status_gl43", "unknown")),
        "- GL-24 handoff status: `%s`" % str(report.get("handoff_status_gl24", "unknown")),
        "- GL-44 acknowledgement status: `%s`"
        % str(report.get("followup_resolution_escalation_acknowledgement_status", "unknown")),
        "- Total acknowledgement items: `%s`"
        % str(_to_int(counts.get("total_item_count", 0), default=0)),
        "- Open acknowledgement items: `%s`"
        % str(_to_int(counts.get("open_item_count", 0), default=0)),
        "- Resolved acknowledgement items: `%s`"
        % str(_to_int(counts.get("resolved_acknowledged_item_count", 0), default=0)),
        "- Pending-ack acknowledgement items: `%s`"
        % str(_to_int(counts.get("pending_ack_item_count", 0), default=0)),
        "- Blocked acknowledgement items: `%s`"
        % str(_to_int(counts.get("blocked_item_count", 0), default=0)),
        "",
        "## Warning Codes",
    ]
    if warning_codes:
        for code in warning_codes:
            lines.append("- `%s`" % str(code))
    else:
        lines.append("- none")

    lines.extend(["", "## Acknowledgement Items"])
    if rows:
        for row in rows:
            if not isinstance(row, dict):
                continue
            lines.append(
                "- `%s` ack=%s handoff=%s action=%s owner=%s modality=%s"
                % (
                    str(row.get("acknowledgement_item_id", "")),
                    str(row.get("acknowledgement_status", "")),
                    str(row.get("handoff_queue_status_gl24", "")),
                    str(row.get("backfill_action_id", "")),
                    str(row.get("owner", "")),
                    str(row.get("required_modality", "")),
                )
            )
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    escalation_report_path = Path(
        str(args.submission_queue_followup_resolution_escalations_report).strip()
    ).resolve()
    handoff_report_path = Path(str(args.handoff_report).strip()).resolve()
    output_path = None if str(args.output).strip() == "-" else Path(str(args.output).strip()).resolve()
    summary_path = (
        None if str(args.summary_output).strip() == "-" else Path(str(args.summary_output).strip()).resolve()
    )
    owner = str(args.owner).strip() or "controlled-beta-ops"

    try:
        for path, label in (
            (escalation_report_path, "submission queue follow-up resolution escalations report"),
            (handoff_report_path, "handoff report"),
        ):
            if not path.is_file():
                raise ValueError("%s path does not exist: %s" % (label, path))
        escalation_report = _read_json(escalation_report_path)
        handoff_report = _read_json(handoff_report_path)
        report = _build_report(
            escalation_report=escalation_report,
            escalation_report_path=escalation_report_path,
            handoff_report=handoff_report,
            handoff_report_path=handoff_report_path,
            owner=owner,
        )
        summary = _render_summary(report)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(
            "Real trial submission queue follow-up resolution escalation acknowledgement generation failed: %s"
            % exc,
            file=sys.stderr,
        )
        return 2

    if output_path is not None:
        _write_text(output_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print(
            "Real trial submission queue follow-up resolution escalation acknowledgements report written: %s"
            % output_path
        )
    if summary_path is not None:
        _write_text(summary_path, summary)
        print(
            "Real trial submission queue follow-up resolution escalation acknowledgements summary written: %s"
            % summary_path
        )

    counts = report.get("followup_resolution_escalation_acknowledgement_counts", {})
    if not isinstance(counts, dict):
        counts = {}
    open_count = _to_int(counts.get("open_item_count", 0), default=0)
    blocked_count = _to_int(counts.get("blocked_item_count", 0), default=0)
    print(
        "Real trial submission queue follow-up resolution escalation acknowledgements status=%s open=%s blocked=%s"
        % (
            str(report.get("followup_resolution_escalation_acknowledgement_status", "unknown")),
            open_count,
            blocked_count,
        )
    )
    if args.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    if bool(args.fail_on_open) and open_count > 0:
        return 1
    if bool(args.fail_on_blocked) and blocked_count > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

