from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ACK_CLOSURE_CADENCE_REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-report.json"
)
DEFAULT_OUTPUT_PATH = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalations-report.json"
)
DEFAULT_SUMMARY_PATH = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalations-summary.md"
)


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


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("JSON root must be an object: %s" % path)
    return payload


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


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


def _utc_timestamp_to_datetime(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _datetime_to_utc_iso(value: datetime | None) -> str:
    if value is None:
        return ""
    return value.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate GL-53 escalation diagnostics from GL-52 acknowledgement-closure-cadence "
            "reports by exporting monitor/due/overdue-stalled cadence escalation rows."
        )
    )
    parser.add_argument(
        "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-report",
        default=str(DEFAULT_ACK_CLOSURE_CADENCE_REPORT_PATH),
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help='GL-53 report output path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--summary-output",
        default=str(DEFAULT_SUMMARY_PATH),
        help='GL-53 summary output path. Use "-" to skip writing file.',
    )
    parser.add_argument("--owner", default="controlled-beta-ops")
    parser.add_argument(
        "--escalate-after-due-hours",
        type=float,
        default=24.0,
        help="Escalation threshold (hours) after due timestamp for due cadence rows.",
    )
    parser.add_argument(
        "--now-utc",
        default="",
        help="Optional UTC timestamp for deterministic escalation timing.",
    )
    parser.add_argument(
        "--fail-on-open",
        action="store_true",
        help="Exit with code 1 when escalation rows remain open.",
    )
    parser.add_argument(
        "--fail-on-overdue-stalled",
        action="store_true",
        help=(
            "Exit with code 1 when status is "
            "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_OVERDUE_STALLED."
        ),
    )
    parser.add_argument("--print-json", action="store_true")
    return parser.parse_args()


def _status_from_inputs(
    *,
    cadence_status_gl52: str,
    open_item_count: int,
    blocked_overdue_stalled_count: int,
    escalation_due_count: int,
) -> str:
    status = cadence_status_gl52.strip().upper()
    if (
        status
        == "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_NOT_REQUIRED"
        and open_item_count <= 0
    ):
        return "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_NOT_REQUIRED"
    if blocked_overdue_stalled_count > 0:
        return "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_OVERDUE_STALLED"
    if escalation_due_count > 0:
        return "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_DUE"
    if open_item_count > 0:
        return "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_MONITORING"
    return "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLEARED"


def _build_report(
    *,
    ack_closure_cadence_report: dict[str, Any],
    ack_closure_cadence_report_path: Path,
    owner: str,
    now_utc: datetime,
    escalate_after_due_hours: float,
) -> dict[str, Any]:
    cadence_status_gl52 = str(
        ack_closure_cadence_report.get(
            "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_status",
            "unknown",
        )
    ).strip()
    cadence_warning_codes = ack_closure_cadence_report.get("warning_codes", [])
    if not isinstance(cadence_warning_codes, list):
        cadence_warning_codes = []

    cadence_counts = ack_closure_cadence_report.get(
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_counts",
        {},
    )
    if not isinstance(cadence_counts, dict):
        cadence_counts = {}

    cadence_refresh = ack_closure_cadence_report.get("refresh_cadence", {})
    if not isinstance(cadence_refresh, dict):
        cadence_refresh = {}

    cadence_rows = ack_closure_cadence_report.get(
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_rows",
        [],
    )
    if not isinstance(cadence_rows, list):
        cadence_rows = []

    escalation_rows: list[dict[str, Any]] = []
    blocked_overdue_stalled_count = 0
    escalation_due_count = 0
    owner_counts: dict[str, dict[str, int]] = {}

    due_in_hours = _to_float(cadence_refresh.get("due_in_hours", 0.0), default=0.0)
    overdue_by_hours = abs(due_in_hours) if due_in_hours < 0 else 0.0

    for row in cadence_rows:
        if not isinstance(row, dict):
            continue

        cadence_item_status = str(row.get("cadence_item_status", "")).strip().lower()
        if cadence_item_status in {"closed", "closed_since_previous_cycle"}:
            continue

        action_id = str(row.get("action_id_gl48", "")).strip()
        acknowledgement_ingestion_item_id = str(
            row.get("acknowledgement_ingestion_item_id", "")
        ).strip()
        row_owner = str(row.get("owner_gl51", "")).strip() or owner

        escalation_severity = "monitor"
        escalation_reason_code = "acknowledgement_closure_cadence_monitoring"
        escalation_action = "continue_cadence_monitoring"

        if cadence_status_gl52.upper().endswith("_OVERDUE_STALLED"):
            escalation_severity = "blocked_overdue_stalled"
            escalation_reason_code = "acknowledgement_closure_cadence_overdue_stalled"
            escalation_action = "escalate_operator_immediately"
            blocked_overdue_stalled_count += 1
        elif cadence_item_status == "refresh_due":
            if overdue_by_hours >= escalate_after_due_hours:
                escalation_severity = "due_breached"
                escalation_reason_code = "acknowledgement_closure_cadence_due_breached"
                escalation_action = "escalate_due_breach"
            else:
                escalation_severity = "due"
                escalation_reason_code = "acknowledgement_closure_cadence_due"
                escalation_action = "execute_due_refresh_cycle"
            escalation_due_count += 1
        elif cadence_item_status == "baseline_open":
            escalation_severity = "baseline_open"
            escalation_reason_code = "acknowledgement_closure_cadence_baseline_initialized"
            escalation_action = "start_first_refresh_cycle"
        elif cadence_item_status == "on_schedule":
            escalation_severity = "on_schedule"
            escalation_reason_code = "acknowledgement_closure_cadence_on_schedule"
            escalation_action = "monitor_until_due"

        escalation_rows.append(
            {
                "escalation_item_id": "gl53-ack-closure-cadence-escalation-%s"
                % (action_id or acknowledgement_ingestion_item_id or "unbound"),
                "escalation_item_status": "open",
                "escalation_severity": escalation_severity,
                "escalation_reason_code": escalation_reason_code,
                "escalation_action": escalation_action,
                "owner": row_owner,
                "acknowledgement_ingestion_item_id_gl52": acknowledgement_ingestion_item_id,
                "action_id_gl48": action_id,
                "required_modality_gl47": str(row.get("required_modality_gl47", "")).strip().lower(),
                "cadence_item_status_gl52": cadence_item_status,
                "closure_state_gl51": str(row.get("closure_state_gl51", "")).strip().lower(),
                "acknowledgement_ingestion_state_gl50": str(
                    row.get("acknowledgement_ingestion_state_gl50", "")
                ).strip().lower(),
                "linked_submission_loop_id_gl24": str(
                    row.get("linked_submission_loop_id_gl24", "")
                ).strip(),
                "next_refresh_due_utc_gl52": str(row.get("next_refresh_due_utc_gl52", "")).strip(),
                "escalation_evaluated_at_utc": _datetime_to_utc_iso(now_utc),
            }
        )

        owner_bucket = owner_counts.setdefault(
            row_owner,
            {
                "total_item_count": 0,
                "open_item_count": 0,
                "blocked_overdue_stalled_item_count": 0,
                "due_item_count": 0,
                "monitor_item_count": 0,
            },
        )
        owner_bucket["total_item_count"] += 1
        owner_bucket["open_item_count"] += 1
        if escalation_severity == "blocked_overdue_stalled":
            owner_bucket["blocked_overdue_stalled_item_count"] += 1
        elif escalation_severity in {"due", "due_breached"}:
            owner_bucket["due_item_count"] += 1
        else:
            owner_bucket["monitor_item_count"] += 1

    escalation_rows.sort(
        key=lambda item: (
            0 if str(item.get("escalation_severity", "")).strip() == "blocked_overdue_stalled" else 1,
            0 if str(item.get("escalation_severity", "")).strip() in {"due_breached", "due"} else 1,
            str(item.get("required_modality_gl47", "")),
            str(item.get("action_id_gl48", "")),
            str(item.get("acknowledgement_ingestion_item_id_gl52", "")),
        )
    )

    open_item_count = len(escalation_rows)
    status = _status_from_inputs(
        cadence_status_gl52=cadence_status_gl52,
        open_item_count=open_item_count,
        blocked_overdue_stalled_count=blocked_overdue_stalled_count,
        escalation_due_count=escalation_due_count,
    )

    warning_codes: list[str] = []
    if open_item_count > 0:
        warning_codes.append(
            "open_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_items_present"
        )
    if blocked_overdue_stalled_count > 0:
        warning_codes.append("acknowledgement_closure_cadence_overdue_stalled_escalation_required")
    if escalation_due_count > 0:
        warning_codes.append("acknowledgement_closure_cadence_due_escalation_required")
    warning_codes.extend(str(item).strip() for item in cadence_warning_codes if str(item).strip())
    warning_codes = _unique_preserve_order(warning_codes)

    counts = {
        "total_item_count": open_item_count,
        "open_item_count": open_item_count,
        "blocked_overdue_stalled_item_count": blocked_overdue_stalled_count,
        "due_item_count": escalation_due_count,
        "monitor_item_count": max(0, open_item_count - blocked_overdue_stalled_count - escalation_due_count),
        "cadence_stall_cycle_count_gl52": _to_int(cadence_counts.get("stall_cycle_count", 0), default=0),
        "cadence_overdue_stalled_cycles_threshold_gl52": _to_int(
            cadence_counts.get("overdue_stalled_cycles_threshold", 0),
            default=0,
        ),
        "escalate_after_due_hours": float(escalate_after_due_hours),
    }

    return {
        "schema_version": "real_trial_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations.v1",
        "generated_at_utc": _datetime_to_utc_iso(now_utc),
        "owner": owner,
        "input_paths": {
            "submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_report": str(
                ack_closure_cadence_report_path
            ),
        },
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_status_gl52": cadence_status_gl52,
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_status": status,
        "warning_codes": warning_codes,
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_counts": counts,
        "owner_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_counts": owner_counts,
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_rows": escalation_rows,
    }


def _render_summary(report: dict[str, Any]) -> str:
    counts = report.get(
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_counts",
        {},
    )
    if not isinstance(counts, dict):
        counts = {}
    warning_codes = report.get("warning_codes", [])
    if not isinstance(warning_codes, list):
        warning_codes = []
    rows = report.get(
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_rows",
        [],
    )
    if not isinstance(rows, list):
        rows = []

    lines = [
        "# Real Trial Submission Queue Follow-Up Resolution Escalation Action Plan Closure Cadence Escalation Acknowledgement Closure Cadence Escalations Summary",
        "",
        "- GL-52 acknowledgement-closure-cadence status: `%s`"
        % str(
            report.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_status_gl52",
                "unknown",
            )
        ),
        "- GL-53 escalation status: `%s`"
        % str(
            report.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_status",
                "unknown",
            )
        ),
        "- Total escalation items: `%s`" % str(_to_int(counts.get("total_item_count", 0), default=0)),
        "- Open escalation items: `%s`" % str(_to_int(counts.get("open_item_count", 0), default=0)),
        "- Overdue-stalled escalation items: `%s`"
        % str(_to_int(counts.get("blocked_overdue_stalled_item_count", 0), default=0)),
        "- Due escalation items: `%s`" % str(_to_int(counts.get("due_item_count", 0), default=0)),
        "",
        "## Warning Codes",
    ]

    if warning_codes:
        for warning_code in warning_codes:
            lines.append("- `%s`" % str(warning_code))
    else:
        lines.append("- none")

    lines.extend(["", "## Escalation Rows"])
    if rows:
        for row in rows:
            if not isinstance(row, dict):
                continue
            lines.append(
                "- `%s` severity=%s cadence_item=%s modality=%s action=%s"
                % (
                    str(row.get("escalation_item_id", "")),
                    str(row.get("escalation_severity", "")),
                    str(row.get("cadence_item_status_gl52", "")),
                    str(row.get("required_modality_gl47", "")),
                    str(row.get("escalation_action", "")),
                )
            )
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    ack_closure_cadence_report_path = Path(
        str(
            args.submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_report
        ).strip()
    ).resolve()
    output_path = None if str(args.output).strip() == "-" else Path(str(args.output).strip()).resolve()
    summary_path = None if str(args.summary_output).strip() == "-" else Path(str(args.summary_output).strip()).resolve()
    owner = str(args.owner).strip() or "controlled-beta-ops"

    try:
        if not ack_closure_cadence_report_path.is_file():
            raise ValueError("GL-52 acknowledgement-closure-cadence report path does not exist: %s" % ack_closure_cadence_report_path)
        ack_closure_cadence_report = _read_json(ack_closure_cadence_report_path)

        now_utc_text = str(args.now_utc).strip()
        now_utc = _utc_timestamp_to_datetime(now_utc_text) if now_utc_text else datetime.now(timezone.utc)
        if now_utc is None:
            raise ValueError("--now-utc must be a timezone-aware UTC timestamp")

        escalate_after_due_hours = float(args.escalate_after_due_hours)
        if escalate_after_due_hours < 0:
            raise ValueError("--escalate-after-due-hours must be >= 0")

        report = _build_report(
            ack_closure_cadence_report=ack_closure_cadence_report,
            ack_closure_cadence_report_path=ack_closure_cadence_report_path,
            owner=owner,
            now_utc=now_utc,
            escalate_after_due_hours=escalate_after_due_hours,
        )
        summary = _render_summary(report)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(
            "Real trial submission queue follow-up resolution escalation action-plan closure cadence escalation acknowledgement closure cadence escalation generation failed: %s"
            % exc,
            file=sys.stderr,
        )
        return 2

    if output_path is not None:
        _write_text(output_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print(
            "Real trial submission queue follow-up resolution escalation action-plan closure cadence escalation acknowledgement closure cadence escalations report written: %s"
            % output_path
        )
    if summary_path is not None:
        _write_text(summary_path, summary)
        print(
            "Real trial submission queue follow-up resolution escalation action-plan closure cadence escalation acknowledgement closure cadence escalations summary written: %s"
            % summary_path
        )

    counts = report.get(
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_counts",
        {},
    )
    if not isinstance(counts, dict):
        counts = {}

    print(
        "Real trial submission queue follow-up resolution escalation action-plan closure cadence escalation acknowledgement closure cadence escalations status=%s open=%s overdue_stalled=%s"
        % (
            str(
                report.get(
                    "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_status",
                    "unknown",
                )
            ),
            _to_int(counts.get("open_item_count", 0), default=0),
            _to_int(counts.get("blocked_overdue_stalled_item_count", 0), default=0),
        )
    )
    if args.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    if bool(args.fail_on_open) and _to_int(counts.get("open_item_count", 0), default=0) > 0:
        return 1
    if bool(args.fail_on_overdue_stalled) and str(
        report.get(
            "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_status",
            "",
        )
    ).strip().upper() == "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_OVERDUE_STALLED":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

