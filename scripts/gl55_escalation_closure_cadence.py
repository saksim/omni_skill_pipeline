from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ESCALATION_CLOSURE_REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-report.json"
)
DEFAULT_OUTPUT_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-report.json"
)
DEFAULT_SUMMARY_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-summary.md"
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
            "Generate GL-55 escalation-closure-cadence diagnostics by binding GL-54 "
            "escalation-closure status to refresh SLA timing and stalled-cycle accumulation."
        )
    )
    parser.add_argument(
        "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-report",
        default=str(DEFAULT_ESCALATION_CLOSURE_REPORT_PATH),
    )
    parser.add_argument(
        "--previous-escalation-closure-cadence-report",
        default="",
        help=(
            "Optional previous GL-55 report. When omitted, script attempts to read existing "
            "--output path before writing."
        ),
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help='GL-55 report output path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--summary-output",
        default=str(DEFAULT_SUMMARY_PATH),
        help='GL-55 summary output path. Use "-" to skip writing file.',
    )
    parser.add_argument("--owner", default="controlled-beta-ops")
    parser.add_argument(
        "--refresh-interval-hours",
        type=float,
        default=24.0,
        help="Refresh cadence interval for GL-55 timing diagnostics (default: 24).",
    )
    parser.add_argument(
        "--overdue-stalled-cycles",
        type=int,
        default=2,
        help="Stalled-cycle threshold that escalates from DUE to OVERDUE_STALLED (default: 2).",
    )
    parser.add_argument(
        "--now-utc",
        default="",
        help="Optional UTC timestamp for deterministic cadence evaluation.",
    )
    parser.add_argument(
        "--fail-on-overdue-stalled",
        action="store_true",
        help=(
            "Exit with code 1 when status is "
            "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_OVERDUE_STALLED."
        ),
    )
    parser.add_argument("--print-json", action="store_true")
    return parser.parse_args()


def _build_report(
    *,
    escalation_closure_report: dict[str, Any],
    escalation_closure_report_path: Path,
    previous_report: dict[str, Any] | None,
    previous_report_path: Path | None,
    owner: str,
    refresh_interval_hours: float,
    overdue_stalled_cycles: int,
    now_utc: datetime,
) -> dict[str, Any]:
    escalation_closure_counts = escalation_closure_report.get(
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_counts",
        {},
    )
    if not isinstance(escalation_closure_counts, dict):
        escalation_closure_counts = {}

    escalation_closure_rows = escalation_closure_report.get(
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_rows",
        [],
    )
    if not isinstance(escalation_closure_rows, list):
        escalation_closure_rows = []

    escalation_closure_status_gl54 = str(
        escalation_closure_report.get(
            "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_status",
            "unknown",
        )
    ).strip()
    escalation_closure_warning_codes = escalation_closure_report.get("warning_codes", [])
    if not isinstance(escalation_closure_warning_codes, list):
        escalation_closure_warning_codes = []

    previous_generated_at_utc = ""
    previous_generated_at_dt: datetime | None = None
    previous_stall_cycle_count = 0
    previous_available = isinstance(previous_report, dict)
    if previous_available and previous_report is not None:
        previous_generated_at_utc = str(previous_report.get("generated_at_utc", "")).strip()
        previous_generated_at_dt = _utc_timestamp_to_datetime(previous_generated_at_utc)
        previous_counts = previous_report.get(
            "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_counts",
            {},
        )
        if isinstance(previous_counts, dict):
            previous_stall_cycle_count = _to_int(previous_counts.get("stall_cycle_count", 0), default=0)

    open_item_count = _to_int(escalation_closure_counts.get("open_item_count", 0), default=0)
    total_item_count = _to_int(escalation_closure_counts.get("total_item_count", 0), default=0)
    stale_open_item_count = _to_int(escalation_closure_counts.get("stale_open_item_count", 0), default=0)
    net_new_closed_item_count_gl54 = _to_int(
        escalation_closure_counts.get("net_new_closed_item_count", 0),
        default=0,
    )
    net_new_closed_backed_by_ack_ingestion_item_count_gl50 = _to_int(
        escalation_closure_counts.get("net_new_closed_backed_by_ack_ingestion_item_count_gl50", 0),
        default=0,
    )

    not_required = (
        open_item_count <= 0
        and escalation_closure_status_gl54.upper()
        in {
            "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_NOT_REQUIRED",
            "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CLEARED",
        }
    )

    if (
        escalation_closure_status_gl54.upper()
        == "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_STALLED"
        and open_item_count > 0
    ):
        stall_cycle_count = previous_stall_cycle_count + 1
    else:
        stall_cycle_count = 0

    if not_required:
        cadence_status = "CADENCE_NOT_REQUIRED"
        next_refresh_due_dt = None
        due_in_hours = 0.0
    elif previous_generated_at_dt is None:
        cadence_status = "CADENCE_BASELINE_INITIALIZED"
        next_refresh_due_dt = now_utc + timedelta(hours=refresh_interval_hours)
        due_in_hours = round(refresh_interval_hours, 3)
    else:
        next_refresh_due_dt = previous_generated_at_dt + timedelta(hours=refresh_interval_hours)
        due_in_hours = round((next_refresh_due_dt - now_utc).total_seconds() / 3600.0, 3)
        if now_utc >= next_refresh_due_dt:
            if (
                escalation_closure_status_gl54.upper()
                == "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_STALLED"
                and stall_cycle_count >= overdue_stalled_cycles
            ):
                cadence_status = "CADENCE_OVERDUE_STALLED"
            else:
                cadence_status = "CADENCE_DUE"
        else:
            cadence_status = "CADENCE_ON_SCHEDULE"

    if cadence_status == "CADENCE_NOT_REQUIRED":
        top_level_status = "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_NOT_REQUIRED"
    elif cadence_status == "CADENCE_BASELINE_INITIALIZED":
        top_level_status = "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_BASELINE_INITIALIZED"
    elif cadence_status == "CADENCE_ON_SCHEDULE":
        top_level_status = "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ON_SCHEDULE"
    elif cadence_status == "CADENCE_OVERDUE_STALLED":
        top_level_status = "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_OVERDUE_STALLED"
    else:
        top_level_status = "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_DUE"

    warning_codes: list[str] = []
    if open_item_count > 0:
        warning_codes.append(
            "open_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_items_present"
        )
    if cadence_status == "CADENCE_DUE":
        warning_codes.append("acknowledgement_closure_cadence_escalation_closure_cadence_due")
    if cadence_status == "CADENCE_OVERDUE_STALLED":
        warning_codes.append("acknowledgement_closure_cadence_escalation_closure_cadence_overdue_stalled")
    if (
        escalation_closure_status_gl54.upper()
        == "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_STALLED"
    ):
        warning_codes.append("acknowledgement_closure_cadence_escalation_closure_stalled")
    warning_codes.extend(
        str(item).strip() for item in escalation_closure_warning_codes if str(item).strip()
    )
    warning_codes = _unique_preserve_order(warning_codes)

    cadence_rows: list[dict[str, Any]] = []
    for row in escalation_closure_rows:
        if not isinstance(row, dict):
            continue
        closure_item_status_gl54 = str(row.get("closure_item_status", "")).strip().lower()
        if closure_item_status_gl54 != "open":
            continue

        closure_progress_state_gl54 = str(row.get("closure_progress_state", "")).strip().lower()
        if closure_progress_state_gl54 in {"carried_open", "net_new_open"}:
            if cadence_status in {"CADENCE_DUE", "CADENCE_OVERDUE_STALLED"}:
                cadence_item_status = "refresh_due"
            elif cadence_status == "CADENCE_BASELINE_INITIALIZED":
                cadence_item_status = "baseline_open"
            else:
                cadence_item_status = "on_schedule"
        elif closure_progress_state_gl54 == "closed_since_previous_cycle":
            cadence_item_status = "closed_since_previous_cycle"
        else:
            cadence_item_status = "closed"

        cadence_rows.append(
            {
                "closure_item_id_gl54": str(row.get("closure_item_id", "")).strip(),
                "closure_progress_state_gl54": closure_progress_state_gl54,
                "closure_item_status_gl54": closure_item_status_gl54,
                "owner_gl54": str(row.get("owner", "")).strip() or owner,
                "required_modality_gl47": str(row.get("required_modality_gl47", "")).strip().lower(),
                "action_id_gl48": str(row.get("action_id_gl48", "")).strip(),
                "escalation_item_id_gl53": str(row.get("escalation_item_id_gl53", "")).strip(),
                "acknowledgement_ingestion_item_id_gl52": str(
                    row.get("acknowledgement_ingestion_item_id_gl52", "")
                ).strip(),
                "acknowledgement_ingestion_state_gl50": str(
                    row.get("acknowledgement_ingestion_state_gl50", "")
                ).strip(),
                "cadence_item_status": cadence_item_status,
                "next_refresh_due_utc_gl55": _datetime_to_utc_iso(next_refresh_due_dt),
            }
        )

    return {
        "schema_version": "real_trial_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence.v1",
        "generated_at_utc": _datetime_to_utc_iso(now_utc),
        "owner": owner,
        "input_paths": {
            "submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_report": str(
                escalation_closure_report_path
            ),
            "previous_escalation_closure_cadence_report": str(previous_report_path)
            if previous_report_path is not None and previous_available
            else "",
        },
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_status_gl54": escalation_closure_status_gl54,
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_status": top_level_status,
        "warning_codes": warning_codes,
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_counts": {
            "total_item_count": total_item_count,
            "open_item_count": open_item_count,
            "stale_open_item_count": stale_open_item_count,
            "net_new_closed_item_count_gl54": net_new_closed_item_count_gl54,
            "net_new_closed_backed_by_ack_ingestion_item_count_gl50": net_new_closed_backed_by_ack_ingestion_item_count_gl50,
            "stall_cycle_count": stall_cycle_count,
            "overdue_stalled_cycles_threshold": overdue_stalled_cycles,
        },
        "refresh_cadence": {
            "refresh_interval_hours": float(refresh_interval_hours),
            "cadence_status": cadence_status,
            "previous_generated_at_utc": previous_generated_at_utc,
            "next_refresh_due_utc": _datetime_to_utc_iso(next_refresh_due_dt),
            "due_in_hours": due_in_hours,
            "evaluated_at_utc": _datetime_to_utc_iso(now_utc),
        },
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_rows": cadence_rows,
    }


def _render_summary(report: dict[str, Any]) -> str:
    counts = report.get(
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_counts",
        {},
    )
    if not isinstance(counts, dict):
        counts = {}
    cadence = report.get("refresh_cadence", {})
    if not isinstance(cadence, dict):
        cadence = {}
    warning_codes = report.get("warning_codes", [])
    if not isinstance(warning_codes, list):
        warning_codes = []
    rows = report.get(
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_rows",
        [],
    )
    if not isinstance(rows, list):
        rows = []

    lines = [
        "# Real Trial Submission Queue Follow-Up Resolution Escalation Action Plan Closure Cadence Escalation Acknowledgement Closure Cadence Escalation Closure Cadence Summary",
        "",
        "- GL-54 escalation-closure status: `%s`"
        % str(
            report.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_status_gl54",
                "unknown",
            )
        ),
        "- GL-55 escalation-closure-cadence status: `%s`"
        % str(
            report.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_status",
                "unknown",
            )
        ),
        "- Cadence state: `%s`" % str(cadence.get("cadence_status", "unknown")),
        "- Open items: `%s`" % str(_to_int(counts.get("open_item_count", 0), default=0)),
        "- Stale open items: `%s`" % str(_to_int(counts.get("stale_open_item_count", 0), default=0)),
        "- Stall cycle count: `%s`" % str(_to_int(counts.get("stall_cycle_count", 0), default=0)),
        "- Next refresh due UTC: `%s`" % str(cadence.get("next_refresh_due_utc", "")),
        "- Due in hours: `%s`" % str(_to_float(cadence.get("due_in_hours", 0.0), default=0.0)),
        "",
        "## Warning Codes",
    ]
    if warning_codes:
        for warning_code in warning_codes:
            lines.append("- `%s`" % str(warning_code))
    else:
        lines.append("- none")

    lines.extend(["", "## Cadence Rows"])
    if rows:
        for row in rows:
            if not isinstance(row, dict):
                continue
            lines.append(
                "- `%s` closure=%s cadence=%s modality=%s"
                % (
                    str(row.get("closure_item_id_gl54", "")),
                    str(row.get("closure_progress_state_gl54", "")),
                    str(row.get("cadence_item_status", "")),
                    str(row.get("required_modality_gl47", "")),
                )
            )
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    escalation_closure_report_path = Path(
        str(
            args.submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_report
        ).strip()
    ).resolve()
    output_path = None if str(args.output).strip() == "-" else Path(str(args.output).strip()).resolve()
    summary_path = None if str(args.summary_output).strip() == "-" else Path(str(args.summary_output).strip()).resolve()
    owner = str(args.owner).strip() or "controlled-beta-ops"
    refresh_interval_hours = float(args.refresh_interval_hours)
    overdue_stalled_cycles = max(1, int(args.overdue_stalled_cycles))
    now_utc_text = str(args.now_utc).strip()

    try:
        if refresh_interval_hours <= 0:
            raise ValueError("--refresh-interval-hours must be > 0")
        now_utc = _utc_timestamp_to_datetime(now_utc_text) if now_utc_text else datetime.now(timezone.utc)
        if now_utc is None:
            raise ValueError("--now-utc must be a timezone-aware UTC timestamp")

        if not escalation_closure_report_path.is_file():
            raise ValueError(
                "GL-54 escalation-closure report path does not exist: %s"
                % escalation_closure_report_path
            )
        escalation_closure_report = _read_json(escalation_closure_report_path)

        previous_report_path: Path | None = None
        previous_report: dict[str, Any] | None = None
        previous_arg = str(args.previous_escalation_closure_cadence_report).strip()
        if previous_arg:
            previous_report_path = Path(previous_arg).resolve()
        elif output_path is not None:
            previous_report_path = output_path
        if previous_report_path is not None and previous_report_path.is_file():
            previous_report = _read_json(previous_report_path)

        report = _build_report(
            escalation_closure_report=escalation_closure_report,
            escalation_closure_report_path=escalation_closure_report_path,
            previous_report=previous_report,
            previous_report_path=previous_report_path if previous_report is not None else None,
            owner=owner,
            refresh_interval_hours=refresh_interval_hours,
            overdue_stalled_cycles=overdue_stalled_cycles,
            now_utc=now_utc,
        )
        summary = _render_summary(report)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(
            "Real trial follow-up resolution escalation action-plan closure cadence escalation acknowledgement closure cadence escalation closure cadence generation failed: %s"
            % exc,
            file=sys.stderr,
        )
        return 2

    if output_path is not None:
        _write_text(output_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print(
            "Real trial follow-up resolution escalation action-plan closure cadence escalation acknowledgement closure cadence escalation closure cadence report written: %s"
            % output_path
        )
    if summary_path is not None:
        _write_text(summary_path, summary)
        print(
            "Real trial follow-up resolution escalation action-plan closure cadence escalation acknowledgement closure cadence escalation closure cadence summary written: %s"
            % summary_path
        )

    counts = report.get(
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_counts",
        {},
    )
    if not isinstance(counts, dict):
        counts = {}

    print(
        "Real trial follow-up resolution escalation action-plan closure cadence escalation acknowledgement closure cadence escalation closure cadence status=%s open_items=%s stall_cycles=%s"
        % (
            str(
                report.get(
                    "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_status",
                    "unknown",
                )
            ),
            _to_int(counts.get("open_item_count", 0), default=0),
            _to_int(counts.get("stall_cycle_count", 0), default=0),
        )
    )
    if args.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    if bool(args.fail_on_overdue_stalled) and str(
        report.get(
            "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_status",
            "",
        )
    ).strip().upper() == (
        "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_OVERDUE_STALLED"
    ):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
