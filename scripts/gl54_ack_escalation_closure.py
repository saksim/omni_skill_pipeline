from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ACK_CLOSURE_CADENCE_ESCALATIONS_REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalations-report.json"
)
DEFAULT_ACK_INGESTION_REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-ingestion-report.json"
)
DEFAULT_OUTPUT_PATH = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-report.json"
)
DEFAULT_SUMMARY_PATH = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-summary.md"
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate GL-54 acknowledgement-closure-cadence-escalation closure diagnostics by "
            "comparing GL-53 escalation snapshots cycle-to-cycle and reconciling net-new closed "
            "escalation items against GL-50 acknowledgement-ingestion states."
        )
    )
    parser.add_argument(
        "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalations-report",
        default=str(DEFAULT_ACK_CLOSURE_CADENCE_ESCALATIONS_REPORT_PATH),
    )
    parser.add_argument(
        "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-ingestion-report",
        default=str(DEFAULT_ACK_INGESTION_REPORT_PATH),
    )
    parser.add_argument(
        "--previous-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-report",
        default="",
        help=(
            "Optional previous GL-54 report path. When omitted, script attempts to read "
            "existing --output path before writing."
        ),
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help='GL-54 report output path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--summary-output",
        default=str(DEFAULT_SUMMARY_PATH),
        help='GL-54 summary output path. Use "-" to skip writing file.',
    )
    parser.add_argument("--owner", default="controlled-beta-ops")
    parser.add_argument(
        "--fail-on-stalled",
        action="store_true",
        help=(
            "Exit with code 1 when status is "
            "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_STALLED."
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


def _normalize_rows(rows: Any) -> list[dict[str, Any]]:
    if not isinstance(rows, list):
        return []
    normalized: list[dict[str, Any]] = []
    for row in rows:
        if isinstance(row, dict):
            normalized.append(row)
    return normalized


def _escalation_rows_snapshot(report: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    rows = _normalize_rows(
        report.get(
            "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_rows",
            [],
        )
    )
    open_rows: list[dict[str, Any]] = []
    open_ids: list[str] = []
    for row in rows:
        item_id = str(row.get("escalation_item_id", "")).strip()
        item_status = str(row.get("escalation_item_status", "")).strip().lower() or "open"
        if item_status != "open":
            continue
        open_rows.append(row)
        if item_id:
            open_ids.append(item_id)
    return open_rows, sorted(set(open_ids))


def _ack_ingestion_snapshot(report: dict[str, Any]) -> tuple[set[str], set[str], dict[str, dict[str, Any]]]:
    rows = _normalize_rows(
        report.get(
            "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_rows",
            [],
        )
    )
    closed_ids: set[str] = set()
    open_ids: set[str] = set()
    by_item_id: dict[str, dict[str, Any]] = {}
    for row in rows:
        item_id = str(row.get("acknowledgement_ingestion_item_id", "")).strip()
        if not item_id:
            continue
        status = str(row.get("acknowledgement_ingestion_item_status", "")).strip().lower()
        by_item_id[item_id] = row
        if status == "closed":
            closed_ids.add(item_id)
        else:
            open_ids.add(item_id)
    return closed_ids, open_ids, by_item_id


def _previous_snapshot(previous_report: dict[str, Any] | None) -> tuple[list[dict[str, Any]], list[str]]:
    if not isinstance(previous_report, dict):
        return [], []
    rows = _normalize_rows(
        previous_report.get(
            "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_rows",
            [],
        )
    )
    open_ids: list[str] = []
    open_rows: list[dict[str, Any]] = []
    for row in rows:
        if str(row.get("closure_item_status", "")).strip().lower() != "open":
            continue
        escalation_item_id = str(row.get("escalation_item_id_gl53", "")).strip()
        if escalation_item_id:
            open_ids.append(escalation_item_id)
        open_rows.append(row)
    return open_rows, sorted(set(open_ids))


def _build_status(
    *,
    escalation_status_gl53: str,
    current_open_item_count: int,
    previous_open_item_count: int,
    previous_available: bool,
    net_new_open_item_count: int,
    net_new_closed_item_count: int,
) -> str:
    status_gl53 = str(escalation_status_gl53).strip().upper()
    if (
        status_gl53
        == "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_NOT_REQUIRED"
        and current_open_item_count <= 0
    ):
        return "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_NOT_REQUIRED"
    if not previous_available:
        return "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_BASELINE_INITIALIZED"
    if (
        net_new_closed_item_count > 0
        or net_new_open_item_count > 0
        or current_open_item_count != previous_open_item_count
    ):
        return "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_PROGRESSING"
    if current_open_item_count > 0:
        return "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_STALLED"
    return "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CLEARED"


def _build_report(
    *,
    escalation_report: dict[str, Any],
    escalation_report_path: Path,
    acknowledgement_ingestion_report: dict[str, Any],
    acknowledgement_ingestion_report_path: Path,
    previous_report: dict[str, Any] | None,
    previous_report_path: Path | None,
    owner: str,
) -> dict[str, Any]:
    escalation_status_gl53 = str(
        escalation_report.get(
            "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_status",
            "unknown",
        )
    ).strip()
    escalation_warnings_gl53 = escalation_report.get("warning_codes", [])
    if not isinstance(escalation_warnings_gl53, list):
        escalation_warnings_gl53 = []

    acknowledgement_ingestion_status_gl50 = str(
        acknowledgement_ingestion_report.get(
            "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_status",
            "unknown",
        )
    ).strip()
    acknowledgement_ingestion_warnings_gl50 = acknowledgement_ingestion_report.get("warning_codes", [])
    if not isinstance(acknowledgement_ingestion_warnings_gl50, list):
        acknowledgement_ingestion_warnings_gl50 = []

    current_open_rows, current_open_ids = _escalation_rows_snapshot(escalation_report)
    previous_open_rows, previous_open_ids = _previous_snapshot(previous_report)
    previous_available = isinstance(previous_report, dict)

    current_open_set = set(current_open_ids)
    previous_open_set = set(previous_open_ids)
    carried_open_item_ids = sorted(current_open_set & previous_open_set)
    net_new_open_item_ids = sorted(current_open_set - previous_open_set)
    net_new_closed_item_ids = sorted(previous_open_set - current_open_set)

    closed_ack_ingestion_item_ids_gl50, open_ack_ingestion_item_ids_gl50, ack_ingestion_row_by_id_gl50 = (
        _ack_ingestion_snapshot(acknowledgement_ingestion_report)
    )

    previous_open_row_by_escalation_id: dict[str, dict[str, Any]] = {}
    for row in previous_open_rows:
        escalation_item_id = str(row.get("escalation_item_id_gl53", "")).strip()
        if escalation_item_id and escalation_item_id not in previous_open_row_by_escalation_id:
            previous_open_row_by_escalation_id[escalation_item_id] = row

    net_new_closed_backed_by_ack_ingestion_item_ids_gl50: list[str] = []
    net_new_closed_without_ack_ingestion_item_ids_gl50: list[str] = []
    for escalation_item_id in net_new_closed_item_ids:
        previous_row = previous_open_row_by_escalation_id.get(escalation_item_id, {})
        ack_ingestion_item_id_gl52 = str(
            previous_row.get("acknowledgement_ingestion_item_id_gl52", "")
        ).strip()
        if ack_ingestion_item_id_gl52 and ack_ingestion_item_id_gl52 in closed_ack_ingestion_item_ids_gl50:
            net_new_closed_backed_by_ack_ingestion_item_ids_gl50.append(escalation_item_id)
        else:
            net_new_closed_without_ack_ingestion_item_ids_gl50.append(escalation_item_id)

    rows: list[dict[str, Any]] = []
    owner_counts: dict[str, dict[str, int]] = {}
    for row in current_open_rows:
        escalation_item_id = str(row.get("escalation_item_id", "")).strip()
        ack_ingestion_item_id_gl52 = str(
            row.get("acknowledgement_ingestion_item_id_gl52", "")
        ).strip()
        row_owner = str(row.get("owner", "")).strip() or owner
        is_carried_open = escalation_item_id in previous_open_set
        progress_state = "carried_open" if is_carried_open else "net_new_open"
        ack_ingestion_state_gl50 = ""
        ack_ingestion_item_status_gl50 = ""
        if ack_ingestion_item_id_gl52 and ack_ingestion_item_id_gl52 in ack_ingestion_row_by_id_gl50:
            ack_row = ack_ingestion_row_by_id_gl50[ack_ingestion_item_id_gl52]
            ack_ingestion_state_gl50 = str(
                ack_row.get("acknowledgement_ingestion_state", "")
            ).strip().lower()
            ack_ingestion_item_status_gl50 = str(
                ack_row.get("acknowledgement_ingestion_item_status", "")
            ).strip().lower()

        rows.append(
            {
                "closure_item_id": "gl54-ack-closure-cadence-escalation-closure-%s"
                % (
                    escalation_item_id
                    or str(row.get("action_id_gl48", "")).strip()
                    or str(row.get("acknowledgement_ingestion_item_id_gl52", "")).strip()
                    or "unbound"
                ),
                "closure_item_status": "open",
                "closure_progress_state": progress_state,
                "owner": row_owner,
                "escalation_item_id_gl53": escalation_item_id,
                "acknowledgement_ingestion_item_id_gl52": ack_ingestion_item_id_gl52,
                "action_id_gl48": str(row.get("action_id_gl48", "")).strip(),
                "required_modality_gl47": str(row.get("required_modality_gl47", "")).strip().lower(),
                "escalation_severity_gl53": str(row.get("escalation_severity", "")).strip().lower(),
                "escalation_item_status_gl53": str(row.get("escalation_item_status", "")).strip().lower(),
                "escalation_action_gl53": str(row.get("escalation_action", "")).strip(),
                "linked_submission_loop_id_gl24": str(row.get("linked_submission_loop_id_gl24", "")).strip(),
                "next_refresh_due_utc_gl52": str(row.get("next_refresh_due_utc_gl52", "")).strip(),
                "acknowledgement_ingestion_status_gl50": acknowledgement_ingestion_status_gl50,
                "acknowledgement_ingestion_item_status_gl50": ack_ingestion_item_status_gl50,
                "acknowledgement_ingestion_state_gl50": ack_ingestion_state_gl50,
            }
        )

        owner_bucket = owner_counts.setdefault(
            row_owner,
            {
                "total_item_count": 0,
                "open_item_count": 0,
                "carried_open_item_count": 0,
                "net_new_open_item_count": 0,
            },
        )
        owner_bucket["total_item_count"] += 1
        owner_bucket["open_item_count"] += 1
        if is_carried_open:
            owner_bucket["carried_open_item_count"] += 1
        else:
            owner_bucket["net_new_open_item_count"] += 1

    rows.sort(
        key=lambda item: (
            0 if str(item.get("closure_progress_state", "")).strip() == "carried_open" else 1,
            0 if str(item.get("escalation_severity_gl53", "")).strip() == "blocked_overdue_stalled" else 1,
            0 if str(item.get("escalation_severity_gl53", "")).strip() in {"due", "due_breached"} else 1,
            str(item.get("required_modality_gl47", "")),
            str(item.get("action_id_gl48", "")),
            str(item.get("escalation_item_id_gl53", "")),
        )
    )

    stale_open_item_count = 0
    if previous_available and len(current_open_ids) > 0 and not net_new_open_item_ids and not net_new_closed_item_ids:
        stale_open_item_count = len(current_open_ids)

    status = _build_status(
        escalation_status_gl53=escalation_status_gl53,
        current_open_item_count=len(current_open_ids),
        previous_open_item_count=len(previous_open_ids),
        previous_available=previous_available,
        net_new_open_item_count=len(net_new_open_item_ids),
        net_new_closed_item_count=len(net_new_closed_item_ids),
    )

    warning_codes: list[str] = []
    if len(current_open_ids) > 0:
        warning_codes.append(
            "open_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_items_present"
        )
    if stale_open_item_count > 0:
        warning_codes.append("acknowledgement_closure_cadence_escalation_closure_stalled")
    if len(net_new_closed_without_ack_ingestion_item_ids_gl50) > 0:
        warning_codes.append("net_new_closed_escalation_items_without_ack_ingestion_closure_evidence")
    warning_codes.extend(str(item).strip() for item in escalation_warnings_gl53 if str(item).strip())
    warning_codes.extend(
        str(item).strip() for item in acknowledgement_ingestion_warnings_gl50 if str(item).strip()
    )
    warning_codes = _unique_preserve_order(warning_codes)

    counts = {
        "total_item_count": len(current_open_ids),
        "open_item_count": len(current_open_ids),
        "previous_open_item_count": len(previous_open_ids),
        "carried_open_item_count": len(carried_open_item_ids),
        "stale_open_item_count": stale_open_item_count,
        "net_new_open_item_count": len(net_new_open_item_ids),
        "net_new_closed_item_count": len(net_new_closed_item_ids),
        "net_new_closed_backed_by_ack_ingestion_item_count_gl50": len(
            net_new_closed_backed_by_ack_ingestion_item_ids_gl50
        ),
        "net_new_closed_without_ack_ingestion_item_count_gl50": len(
            net_new_closed_without_ack_ingestion_item_ids_gl50
        ),
        "ack_ingestion_closed_item_count_gl50": len(closed_ack_ingestion_item_ids_gl50),
        "ack_ingestion_open_item_count_gl50": len(open_ack_ingestion_item_ids_gl50),
    }

    return {
        "schema_version": "real_trial_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure.v1",
        "generated_at_utc": _utc_now_iso(),
        "owner": owner,
        "input_paths": {
            "submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_report": str(
                escalation_report_path
            ),
            "submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_report": str(
                acknowledgement_ingestion_report_path
            ),
            "previous_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_report": str(
                previous_report_path
            )
            if previous_report_path is not None and previous_available
            else "",
        },
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_status_gl53": escalation_status_gl53,
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_status_gl50": acknowledgement_ingestion_status_gl50,
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_status": status,
        "warning_codes": warning_codes,
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_counts": counts,
        "owner_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_counts": owner_counts,
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_carried_open_item_ids": carried_open_item_ids,
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_net_new_open_item_ids": net_new_open_item_ids,
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_net_new_closed_item_ids": net_new_closed_item_ids,
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_net_new_closed_backed_by_ack_ingestion_item_ids_gl50": net_new_closed_backed_by_ack_ingestion_item_ids_gl50,
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_net_new_closed_without_ack_ingestion_item_ids_gl50": net_new_closed_without_ack_ingestion_item_ids_gl50,
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_rows": rows,
    }


def _render_summary(report: dict[str, Any]) -> str:
    counts = report.get(
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_counts",
        {},
    )
    if not isinstance(counts, dict):
        counts = {}
    warning_codes = report.get("warning_codes", [])
    if not isinstance(warning_codes, list):
        warning_codes = []
    rows = report.get(
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_rows",
        [],
    )
    if not isinstance(rows, list):
        rows = []

    lines = [
        "# Real Trial Submission Queue Follow-Up Resolution Escalation Action Plan Closure Cadence Escalation Acknowledgement Closure Cadence Escalation Closure Summary",
        "",
        "- GL-53 escalation status: `%s`"
        % str(
            report.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_status_gl53",
                "unknown",
            )
        ),
        "- GL-50 acknowledgement-ingestion status: `%s`"
        % str(
            report.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_status_gl50",
                "unknown",
            )
        ),
        "- GL-54 escalation-closure status: `%s`"
        % str(
            report.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_status",
                "unknown",
            )
        ),
        "- Open closure items: `%s`" % str(_to_int(counts.get("open_item_count", 0), default=0)),
        "- Previous open closure items: `%s`"
        % str(_to_int(counts.get("previous_open_item_count", 0), default=0)),
        "- Net-new closed escalation items: `%s`"
        % str(_to_int(counts.get("net_new_closed_item_count", 0), default=0)),
        "- Net-new closed backed by GL-50 closed ingestion items: `%s`"
        % str(
            _to_int(
                counts.get("net_new_closed_backed_by_ack_ingestion_item_count_gl50", 0),
                default=0,
            )
        ),
        "",
        "## Warning Codes",
    ]
    if warning_codes:
        for warning_code in warning_codes:
            lines.append("- `%s`" % str(warning_code))
    else:
        lines.append("- none")

    lines.extend(["", "## Open Closure Rows"])
    if rows:
        for row in rows:
            if not isinstance(row, dict):
                continue
            lines.append(
                "- `%s` state=%s severity_gl53=%s modality=%s action=%s ack_state_gl50=%s"
                % (
                    str(row.get("closure_item_id", "")),
                    str(row.get("closure_progress_state", "")),
                    str(row.get("escalation_severity_gl53", "")),
                    str(row.get("required_modality_gl47", "")),
                    str(row.get("action_id_gl48", "")),
                    str(row.get("acknowledgement_ingestion_state_gl50", "")),
                )
            )
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    escalation_report_path = Path(
        str(
            args.submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_report
        ).strip()
    ).resolve()
    acknowledgement_ingestion_report_path = Path(
        str(
            args.submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_report
        ).strip()
    ).resolve()
    output_path = None if str(args.output).strip() == "-" else Path(str(args.output).strip()).resolve()
    summary_path = None if str(args.summary_output).strip() == "-" else Path(str(args.summary_output).strip()).resolve()
    owner = str(args.owner).strip() or "controlled-beta-ops"

    try:
        if not escalation_report_path.is_file():
            raise ValueError("GL-53 escalation report path does not exist: %s" % escalation_report_path)
        if not acknowledgement_ingestion_report_path.is_file():
            raise ValueError(
                "GL-50 acknowledgement-ingestion report path does not exist: %s"
                % acknowledgement_ingestion_report_path
            )

        escalation_report = _read_json(escalation_report_path)
        acknowledgement_ingestion_report = _read_json(acknowledgement_ingestion_report_path)

        previous_report_path: Path | None = None
        previous_report: dict[str, Any] | None = None
        previous_arg = str(
            args.previous_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_report
        ).strip()
        if previous_arg:
            previous_report_path = Path(previous_arg).resolve()
        elif output_path is not None:
            previous_report_path = output_path
        if previous_report_path is not None and previous_report_path.is_file():
            previous_report = _read_json(previous_report_path)

        report = _build_report(
            escalation_report=escalation_report,
            escalation_report_path=escalation_report_path,
            acknowledgement_ingestion_report=acknowledgement_ingestion_report,
            acknowledgement_ingestion_report_path=acknowledgement_ingestion_report_path,
            previous_report=previous_report,
            previous_report_path=previous_report_path,
            owner=owner,
        )
        summary = _render_summary(report)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(
            "Real trial submission queue follow-up resolution escalation action-plan closure cadence escalation acknowledgement closure cadence escalation closure generation failed: %s"
            % exc,
            file=sys.stderr,
        )
        return 2

    if output_path is not None:
        _write_text(output_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print(
            "Real trial submission queue follow-up resolution escalation action-plan closure cadence escalation acknowledgement closure cadence escalation closure report written: %s"
            % output_path
        )
    if summary_path is not None:
        _write_text(summary_path, summary)
        print(
            "Real trial submission queue follow-up resolution escalation action-plan closure cadence escalation acknowledgement closure cadence escalation closure summary written: %s"
            % summary_path
        )

    counts = report.get(
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_counts",
        {},
    )
    if not isinstance(counts, dict):
        counts = {}
    print(
        "Real trial submission queue follow-up resolution escalation action-plan closure cadence escalation acknowledgement closure cadence escalation closure status=%s open=%s carried_open=%s net_new_closed=%s"
        % (
            str(
                report.get(
                    "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_status",
                    "unknown",
                )
            ),
            _to_int(counts.get("open_item_count", 0), default=0),
            _to_int(counts.get("carried_open_item_count", 0), default=0),
            _to_int(counts.get("net_new_closed_item_count", 0), default=0),
        )
    )
    if args.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    if bool(args.fail_on_stalled) and str(
        report.get(
            "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_status",
            "",
        )
    ).strip().upper() == (
        "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_STALLED"
    ):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

