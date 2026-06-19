from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FOLLOWUP_RESOLUTION_REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-report.json"
)
DEFAULT_FOLLOWUP_REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-report.json"
)
DEFAULT_OUTPUT_PATH = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalations-report.json"
)
DEFAULT_SUMMARY_PATH = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalations-summary.md"
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate GL-43 escalation exports from GL-42 follow-up-resolution diagnostics."
        )
    )
    parser.add_argument(
        "--submission-queue-followup-resolution-report",
        default=str(DEFAULT_FOLLOWUP_RESOLUTION_REPORT_PATH),
    )
    parser.add_argument(
        "--submission-queue-followup-report",
        default=str(DEFAULT_FOLLOWUP_REPORT_PATH),
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help='Escalation report output path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--summary-output",
        default=str(DEFAULT_SUMMARY_PATH),
        help='Escalation summary output path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--owner",
        default="controlled-beta-ops",
        help="Escalation owner used when row owner is missing.",
    )
    parser.add_argument(
        "--fail-on-open",
        action="store_true",
        help="Exit with code 1 when open escalation items exist.",
    )
    parser.add_argument(
        "--fail-on-blocked",
        action="store_true",
        help="Exit with code 1 when blocked escalation items exist.",
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


def _build_escalation_row(
    *,
    resolution_row: dict[str, Any],
    followup_row: dict[str, Any] | None,
    fallback_owner: str,
    severity: str,
    escalation_reason_code: str,
    escalation_action: str,
) -> dict[str, Any]:
    followup_action_id = str(resolution_row.get("followup_action_id", "")).strip()
    followup_action_type = str(resolution_row.get("followup_action_type", "")).strip()
    followup_reason_code = str(resolution_row.get("followup_reason_code", "")).strip()
    queue_item_id = str(resolution_row.get("queue_item_id", "")).strip()
    backfill_action_id = str(resolution_row.get("backfill_action_id", "")).strip()
    required_modality = str(resolution_row.get("required_modality", "")).strip().lower()
    resolution_status = str(resolution_row.get("resolution_status", "")).strip().lower()
    resolution_state = str(resolution_row.get("resolution_state", "")).strip().lower()
    queue_status_gl24 = str(resolution_row.get("handoff_queue_status_gl24", "")).strip().lower()
    consumed_loop_id = str(resolution_row.get("submission_consumed_loop_id_gl33", "")).strip()
    linked_loop_id = str(resolution_row.get("handoff_linked_loop_id_gl24", "")).strip()
    cycle_due_at_utc = str(resolution_row.get("cycle_due_at_utc", "")).strip()

    owner = _normalize_owner(
        resolution_row.get("owner", ""),
        fallback_owner=fallback_owner,
    )
    if isinstance(followup_row, dict):
        owner = _normalize_owner(followup_row.get("owner", owner), fallback_owner=fallback_owner)

    priority_rank = _to_int(resolution_row.get("priority_rank", 0), default=0)
    if priority_rank <= 0 and isinstance(followup_row, dict):
        priority_rank = _to_int(followup_row.get("priority_rank", 0), default=0)

    source_stale_rollover = bool(
        followup_row.get("source_stale_rollover", False) if isinstance(followup_row, dict) else False
    )
    source_closure_state_gl40 = (
        str(followup_row.get("source_closure_state_gl40", "")).strip().lower()
        if isinstance(followup_row, dict)
        else ""
    )
    source_commitment_status_gl39 = (
        str(followup_row.get("source_commitment_status_gl39", "")).strip().lower()
        if isinstance(followup_row, dict)
        else ""
    )
    source_transition_state_gl38 = (
        str(followup_row.get("source_transition_state_gl38", "")).strip().lower()
        if isinstance(followup_row, dict)
        else ""
    )
    source_stale_reason_codes = (
        _unique_preserve_order(
            [
                str(item).strip()
                for item in followup_row.get("source_stale_reason_codes", [])
                if str(item).strip()
            ]
        )
        if isinstance(followup_row, dict) and isinstance(followup_row.get("source_stale_reason_codes", []), list)
        else []
    )

    return {
        "escalation_item_id": "gl43-escalation-%s" % (followup_action_id or backfill_action_id or queue_item_id or "unbound"),
        "escalation_item_status": "open",
        "escalation_severity": severity,
        "escalation_reason_code": escalation_reason_code,
        "escalation_action": escalation_action,
        "owner": owner,
        "followup_action_id": followup_action_id,
        "followup_action_type": followup_action_type,
        "followup_reason_code_gl41": followup_reason_code,
        "queue_item_id": queue_item_id,
        "backfill_action_id": backfill_action_id,
        "required_modality": required_modality,
        "priority_rank": priority_rank,
        "resolution_status_gl42": resolution_status,
        "resolution_state_gl42": resolution_state,
        "handoff_queue_status_gl24": queue_status_gl24,
        "submission_consumed_loop_id_gl33": consumed_loop_id,
        "handoff_linked_loop_id_gl24": linked_loop_id,
        "cycle_due_at_utc": cycle_due_at_utc,
        "source_stale_rollover_gl41": source_stale_rollover,
        "source_closure_state_gl40": source_closure_state_gl40,
        "source_commitment_status_gl39": source_commitment_status_gl39,
        "source_transition_state_gl38": source_transition_state_gl38,
        "source_stale_reason_codes_gl40": source_stale_reason_codes,
    }


def _followup_by_action_id(followup_report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = followup_report.get("followup_action_rows", [])
    if not isinstance(rows, list):
        rows = []
    index: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        action_id = str(row.get("followup_action_id", "")).strip()
        if action_id and action_id not in index:
            index[action_id] = row
    return index


def _build_escalation_rows(
    *,
    resolution_report: dict[str, Any],
    followup_report: dict[str, Any],
    fallback_owner: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    resolution_rows = resolution_report.get("followup_resolution_rows", [])
    if not isinstance(resolution_rows, list):
        resolution_rows = []
    followup_index = _followup_by_action_id(followup_report)

    escalation_rows: list[dict[str, Any]] = []
    warning_codes: list[str] = []

    for resolution_row in resolution_rows:
        if not isinstance(resolution_row, dict):
            continue
        followup_action_id = str(resolution_row.get("followup_action_id", "")).strip()
        followup_row = followup_index.get(followup_action_id)
        resolution_status = str(resolution_row.get("resolution_status", "")).strip().lower()
        resolution_state = str(resolution_row.get("resolution_state", "")).strip().lower()

        if resolution_status == "resolved":
            continue

        if resolution_status == "unresolved":
            escalation_rows.append(
                _build_escalation_row(
                    resolution_row=resolution_row,
                    followup_row=followup_row,
                    fallback_owner=fallback_owner,
                    severity="blocked",
                    escalation_reason_code="followup_resolution_unresolved",
                    escalation_action="escalate_unresolved_followup_action",
                )
            )
            warning_codes.append("followup_resolution_unresolved_escalations_required")
            continue

        if resolution_status == "in_progress":
            if resolution_state in {
                "in_progress_submission_linked_pending_ack",
                "in_progress_submission_consumed_not_handed_off",
            }:
                escalation_rows.append(
                    _build_escalation_row(
                        resolution_row=resolution_row,
                        followup_row=followup_row,
                        fallback_owner=fallback_owner,
                        severity="pending_ack",
                        escalation_reason_code="followup_resolution_in_progress_pending_ack",
                        escalation_action="track_submission_linked_acknowledgement_closure",
                    )
                )
                warning_codes.append("followup_resolution_in_progress_pending_ack_escalations_required")
            else:
                escalation_rows.append(
                    _build_escalation_row(
                        resolution_row=resolution_row,
                        followup_row=followup_row,
                        fallback_owner=fallback_owner,
                        severity="active",
                        escalation_reason_code="followup_resolution_in_progress",
                        escalation_action="track_in_progress_followup_resolution",
                    )
                )
                warning_codes.append("followup_resolution_in_progress_escalations_required")
            continue

        escalation_rows.append(
            _build_escalation_row(
                resolution_row=resolution_row,
                followup_row=followup_row,
                fallback_owner=fallback_owner,
                severity="blocked",
                escalation_reason_code="followup_resolution_unknown_state",
                escalation_action="escalate_unknown_followup_resolution_state",
            )
        )
        warning_codes.append("followup_resolution_unknown_state_escalations_required")

    escalation_rows.sort(
        key=lambda row: (
            0 if str(row.get("escalation_severity", "")) == "blocked" else 1,
            0 if str(row.get("escalation_severity", "")) == "pending_ack" else 1,
            0 if str(row.get("escalation_severity", "")) == "active" else 1,
            _to_int(row.get("priority_rank", 0), default=0) <= 0,
            _to_int(row.get("priority_rank", 0), default=0),
            str(row.get("required_modality", "")),
            str(row.get("backfill_action_id", "")),
            str(row.get("followup_action_id", "")),
        )
    )
    return escalation_rows, _unique_preserve_order(warning_codes)


def _owner_counts(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        owner = str(row.get("owner", "")).strip() or "unassigned"
        severity = str(row.get("escalation_severity", "")).strip().lower()
        bucket = counts.setdefault(
            owner,
            {
                "total_item_count": 0,
                "open_item_count": 0,
                "blocked_item_count": 0,
                "pending_ack_item_count": 0,
                "active_item_count": 0,
            },
        )
        bucket["total_item_count"] += 1
        if str(row.get("escalation_item_status", "")).strip().lower() == "open":
            bucket["open_item_count"] += 1
        if severity == "blocked":
            bucket["blocked_item_count"] += 1
        elif severity == "pending_ack":
            bucket["pending_ack_item_count"] += 1
        elif severity == "active":
            bucket["active_item_count"] += 1
    return counts


def _build_escalation_status(
    *,
    followup_resolution_status_gl42: str,
    total_item_count: int,
    blocked_item_count: int,
    pending_ack_item_count: int,
) -> str:
    status = str(followup_resolution_status_gl42).strip().upper()
    if total_item_count == 0:
        if status == "FOLLOWUP_RESOLUTION_NOT_REQUIRED":
            return "FOLLOWUP_RESOLUTION_ESCALATION_NOT_REQUIRED"
        return "FOLLOWUP_RESOLUTION_ESCALATION_CLEARED"
    if blocked_item_count > 0:
        return "FOLLOWUP_RESOLUTION_ESCALATION_BLOCKED_ACTION_REQUIRED"
    if pending_ack_item_count > 0:
        return "FOLLOWUP_RESOLUTION_ESCALATION_PENDING_ACK_ACTION_REQUIRED"
    return "FOLLOWUP_RESOLUTION_ESCALATION_ACTIVE"


def _build_report(
    *,
    resolution_report: dict[str, Any],
    resolution_report_path: Path,
    followup_report: dict[str, Any],
    followup_report_path: Path,
    owner: str,
) -> dict[str, Any]:
    escalation_rows, warning_codes = _build_escalation_rows(
        resolution_report=resolution_report,
        followup_report=followup_report,
        fallback_owner=owner,
    )

    total_item_count = len(escalation_rows)
    open_item_count = sum(
        1
        for row in escalation_rows
        if str(row.get("escalation_item_status", "")).strip().lower() == "open"
    )
    blocked_item_count = sum(
        1
        for row in escalation_rows
        if str(row.get("escalation_severity", "")).strip().lower() == "blocked"
    )
    pending_ack_item_count = sum(
        1
        for row in escalation_rows
        if str(row.get("escalation_severity", "")).strip().lower() == "pending_ack"
    )
    active_item_count = sum(
        1
        for row in escalation_rows
        if str(row.get("escalation_severity", "")).strip().lower() == "active"
    )

    if open_item_count > 0:
        warning_codes.append("open_followup_resolution_escalation_items_present")
    warning_codes = _unique_preserve_order(warning_codes)

    followup_resolution_status_gl42 = str(
        resolution_report.get("followup_resolution_status", "unknown")
    ).strip()
    followup_status_gl41 = str(followup_report.get("followup_status", "unknown")).strip()

    return {
        "schema_version": "real_trial_submission_queue_followup_resolution_escalations.v1",
        "generated_at_utc": _utc_now_iso(),
        "owner": owner,
        "input_paths": {
            "submission_queue_followup_resolution_report": str(resolution_report_path),
            "submission_queue_followup_report": str(followup_report_path),
        },
        "followup_resolution_status_gl42": followup_resolution_status_gl42,
        "followup_status_gl41": followup_status_gl41,
        "followup_resolution_escalation_status": _build_escalation_status(
            followup_resolution_status_gl42=followup_resolution_status_gl42,
            total_item_count=total_item_count,
            blocked_item_count=blocked_item_count,
            pending_ack_item_count=pending_ack_item_count,
        ),
        "warning_codes": warning_codes,
        "followup_resolution_escalation_counts": {
            "total_item_count": total_item_count,
            "open_item_count": open_item_count,
            "blocked_item_count": blocked_item_count,
            "pending_ack_item_count": pending_ack_item_count,
            "active_item_count": active_item_count,
        },
        "owner_followup_resolution_escalation_counts": _owner_counts(escalation_rows),
        "followup_resolution_escalation_rows": escalation_rows,
    }


def _render_summary(report: dict[str, Any]) -> str:
    counts = report.get("followup_resolution_escalation_counts", {})
    if not isinstance(counts, dict):
        counts = {}
    warning_codes = report.get("warning_codes", [])
    if not isinstance(warning_codes, list):
        warning_codes = []
    rows = report.get("followup_resolution_escalation_rows", [])
    if not isinstance(rows, list):
        rows = []

    lines = [
        "# Real Trial Submission Queue Follow-Up Resolution Escalations Summary",
        "",
        "- GL-42 follow-up resolution status: `%s`"
        % str(report.get("followup_resolution_status_gl42", "unknown")),
        "- GL-43 escalation status: `%s`"
        % str(report.get("followup_resolution_escalation_status", "unknown")),
        "- Total escalation items: `%s`"
        % str(_to_int(counts.get("total_item_count", 0), default=0)),
        "- Open escalation items: `%s`"
        % str(_to_int(counts.get("open_item_count", 0), default=0)),
        "- Blocked escalation items: `%s`"
        % str(_to_int(counts.get("blocked_item_count", 0), default=0)),
        "- Pending-ack escalation items: `%s`"
        % str(_to_int(counts.get("pending_ack_item_count", 0), default=0)),
        "- Active escalation items: `%s`"
        % str(_to_int(counts.get("active_item_count", 0), default=0)),
        "",
        "## Warning Codes",
    ]
    if warning_codes:
        for code in warning_codes:
            lines.append("- `%s`" % str(code))
    else:
        lines.append("- none")

    lines.extend(["", "## Escalation Items"])
    if rows:
        for row in rows:
            if not isinstance(row, dict):
                continue
            lines.append(
                "- `%s` severity=%s resolution_state=%s action=%s owner=%s modality=%s"
                % (
                    str(row.get("escalation_item_id", "")),
                    str(row.get("escalation_severity", "")),
                    str(row.get("resolution_state_gl42", "")),
                    str(row.get("escalation_action", "")),
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
    resolution_report_path = Path(str(args.submission_queue_followup_resolution_report).strip()).resolve()
    followup_report_path = Path(str(args.submission_queue_followup_report).strip()).resolve()
    output_path = None if str(args.output).strip() == "-" else Path(str(args.output).strip()).resolve()
    summary_path = None if str(args.summary_output).strip() == "-" else Path(str(args.summary_output).strip()).resolve()
    owner = str(args.owner).strip() or "controlled-beta-ops"

    try:
        for path, label in (
            (resolution_report_path, "submission queue follow-up resolution report"),
            (followup_report_path, "submission queue follow-up report"),
        ):
            if not path.is_file():
                raise ValueError("%s path does not exist: %s" % (label, path))
        resolution_report = _read_json(resolution_report_path)
        followup_report = _read_json(followup_report_path)
        report = _build_report(
            resolution_report=resolution_report,
            resolution_report_path=resolution_report_path,
            followup_report=followup_report,
            followup_report_path=followup_report_path,
            owner=owner,
        )
        summary = _render_summary(report)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print("Real trial submission queue follow-up resolution escalations generation failed: %s" % exc, file=sys.stderr)
        return 2

    if output_path is not None:
        _write_text(output_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print("Real trial submission queue follow-up resolution escalations report written: %s" % output_path)
    if summary_path is not None:
        _write_text(summary_path, summary)
        print("Real trial submission queue follow-up resolution escalations summary written: %s" % summary_path)

    counts = report.get("followup_resolution_escalation_counts", {})
    if not isinstance(counts, dict):
        counts = {}
    open_count = _to_int(counts.get("open_item_count", 0), default=0)
    blocked_count = _to_int(counts.get("blocked_item_count", 0), default=0)
    print(
        "Real trial submission queue follow-up resolution escalations status=%s open=%s blocked=%s"
        % (
            str(report.get("followup_resolution_escalation_status", "unknown")),
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

