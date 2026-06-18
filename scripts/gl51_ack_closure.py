from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ACK_INGESTION_REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-ingestion-report.json"
)
DEFAULT_COLLECTION_REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-loop-collection-report.json"
)
DEFAULT_OUTPUT_PATH = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-report.json"
)
DEFAULT_SUMMARY_PATH = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-summary.md"
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _to_int(value: Any, *, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return int(default)


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


def _normalize_rows(rows: Any) -> list[dict[str, Any]]:
    if not isinstance(rows, list):
        return []
    normalized: list[dict[str, Any]] = []
    for row in rows:
        if isinstance(row, dict):
            normalized.append(row)
    return normalized


def _normalize_item_id(value: Any) -> str:
    return str(value or "").strip()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate GL-51 acknowledgement-closure diagnostics by comparing GL-50 "
            "acknowledgement-ingestion snapshots across cycles and correlating closure "
            "progress with launch-gate-eligible real-loop movement."
        )
    )
    parser.add_argument(
        "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-ingestion-report",
        default=str(DEFAULT_ACK_INGESTION_REPORT_PATH),
    )
    parser.add_argument(
        "--collection-report",
        default=str(DEFAULT_COLLECTION_REPORT_PATH),
    )
    parser.add_argument(
        "--previous-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-report",
        default="",
        help=(
            "Optional previous GL-51 report path. When omitted, script attempts to read "
            "existing --output before writing."
        ),
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help='GL-51 report output path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--summary-output",
        default=str(DEFAULT_SUMMARY_PATH),
        help='GL-51 summary output path. Use "-" to skip writing file.',
    )
    parser.add_argument("--owner", default="controlled-beta-ops")
    parser.add_argument(
        "--fail-on-stalled",
        action="store_true",
        help="Exit with code 1 when GL-51 status is ACKNOWLEDGEMENT_CLOSURE_STALLED.",
    )
    parser.add_argument("--print-json", action="store_true")
    return parser.parse_args()


def _ack_ingestion_snapshot(ack_ingestion_report: dict[str, Any]) -> dict[str, Any]:
    status = str(
        ack_ingestion_report.get(
            "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_status",
            "unknown",
        )
    ).strip()
    rows = _normalize_rows(
        ack_ingestion_report.get(
            "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_rows",
            [],
        )
    )
    counts = ack_ingestion_report.get(
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_counts",
        {},
    )
    if not isinstance(counts, dict):
        counts = {}

    normalized_rows: list[dict[str, Any]] = []
    open_item_ids: list[str] = []
    for row in rows:
        item_id = _normalize_item_id(row.get("acknowledgement_ingestion_item_id", ""))
        item_status = str(row.get("acknowledgement_ingestion_item_status", "")).strip().lower() or "open"
        item_state = (
            str(row.get("acknowledgement_ingestion_state", "")).strip().lower() or "ack_input_missing"
        )
        if item_status == "open" and item_id:
            open_item_ids.append(item_id)
        normalized_rows.append(
            {
                "acknowledgement_ingestion_item_id": item_id,
                "acknowledgement_ingestion_item_status": item_status,
                "acknowledgement_ingestion_state": item_state,
                "owner": str(row.get("owner", "")).strip(),
                "action_id_gl48": str(row.get("action_id_gl48", "")).strip(),
                "required_modality_gl47": str(row.get("required_modality_gl47", "")).strip().lower(),
                "handoff_queue_item_id_gl24": str(row.get("handoff_queue_item_id_gl24", "")).strip(),
                "linked_submission_loop_id_gl24": str(row.get("linked_submission_loop_id_gl24", "")).strip(),
                "acknowledged_submitted_loop_id_gl25": str(
                    row.get("acknowledged_submitted_loop_id_gl25", "")
                ).strip(),
                "acknowledgement_loop_matches_linked_submission": bool(
                    row.get("acknowledgement_loop_matches_linked_submission", False)
                ),
            }
        )

    return {
        "status": status,
        "warning_codes": ack_ingestion_report.get("warning_codes", []),
        "rows": normalized_rows,
        "total_item_count": _to_int(counts.get("total_item_count", len(normalized_rows)), default=0),
        "open_item_count": _to_int(
            counts.get(
                "open_item_count",
                len([item for item in normalized_rows if item.get("acknowledgement_ingestion_item_status") == "open"]),
            ),
            default=0,
        ),
        "closed_item_count": _to_int(counts.get("closed_item_count", 0), default=0),
        "ack_loop_mismatch_item_count": _to_int(
            counts.get("escalation_rows_with_mismatched_ack_loop_count", 0),
            default=0,
        ),
        "missing_ack_record_item_count": _to_int(
            counts.get("escalation_rows_missing_acknowledgement_record_count", 0),
            default=0,
        ),
        "missing_handoff_queue_item_count": _to_int(
            counts.get("escalation_rows_without_handoff_queue_item_count", 0),
            default=0,
        ),
        "open_item_ids": sorted(set(open_item_ids)),
    }


def _collection_snapshot(collection_report: dict[str, Any]) -> dict[str, Any]:
    alignment = collection_report.get("launch_gate_alignment", {})
    if not isinstance(alignment, dict):
        alignment = {}

    loop_rows = collection_report.get("collected_real_launch_gate_eligible_loops", [])
    if not isinstance(loop_rows, list):
        loop_rows = []
    loop_ids: list[str] = []
    for row in loop_rows:
        if not isinstance(row, dict):
            continue
        loop_id = str(row.get("loop_id", "")).strip()
        if loop_id:
            loop_ids.append(loop_id)

    return {
        "program_status": str(alignment.get("program_status", "unknown")).strip(),
        "launch_gate_eligible_complete_loop_count": _to_int(
            alignment.get("launch_gate_eligible_complete_loop_count", len(loop_ids)),
            default=len(loop_ids),
        ),
        "missing_complete_loops_to_threshold": _to_int(
            alignment.get("missing_complete_loops_to_threshold", 0),
            default=0,
        ),
        "missing_modalities_to_threshold": _to_int(
            alignment.get("missing_modalities_to_threshold", 0),
            default=0,
        ),
        "launch_gate_eligible_loop_ids": sorted(set(loop_ids)),
    }


def _previous_snapshot(previous_report: dict[str, Any] | None) -> tuple[dict[str, Any], dict[str, Any]]:
    if not isinstance(previous_report, dict):
        return (
            {
                "open_item_count": 0,
                "open_item_ids": [],
            },
            {
                "launch_gate_eligible_complete_loop_count": 0,
                "launch_gate_eligible_loop_ids": [],
            },
        )

    ack_snapshot = previous_report.get("acknowledgement_ingestion_snapshot", {})
    if not isinstance(ack_snapshot, dict):
        ack_snapshot = {}
    collection_snapshot = previous_report.get("collection_snapshot", {})
    if not isinstance(collection_snapshot, dict):
        collection_snapshot = {}

    return (
        {
            "open_item_count": _to_int(ack_snapshot.get("open_item_count", 0), default=0),
            "open_item_ids": sorted(
                set(
                    _normalize_item_id(item)
                    for item in ack_snapshot.get("open_item_ids", [])
                    if _normalize_item_id(item)
                )
            ),
        },
        {
            "launch_gate_eligible_complete_loop_count": _to_int(
                collection_snapshot.get("launch_gate_eligible_complete_loop_count", 0),
                default=0,
            ),
            "launch_gate_eligible_loop_ids": sorted(
                set(
                    str(item).strip()
                    for item in collection_snapshot.get("launch_gate_eligible_loop_ids", [])
                    if str(item).strip()
                )
            ),
        },
    )


def _build_status(
    *,
    ack_ingestion_status_gl50: str,
    previous_available: bool,
    open_item_count: int,
    previous_open_item_count: int,
    net_new_closed_item_count: int,
    net_new_launch_gate_eligible_loop_count: int,
) -> str:
    status = ack_ingestion_status_gl50.strip().upper()
    if status == "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_NOT_REQUIRED" and open_item_count <= 0:
        return "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_NOT_REQUIRED"
    if open_item_count <= 0:
        if previous_available and previous_open_item_count > 0:
            return "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_COMPLETE"
        return "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CLEARED"
    if not previous_available:
        return "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_BASELINE_INITIALIZED"
    if net_new_closed_item_count > 0 or net_new_launch_gate_eligible_loop_count > 0:
        return "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_PROGRESSING"
    return "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_STALLED"


def _build_rows(
    *,
    current_rows: list[dict[str, Any]],
    previous_open_item_ids: set[str],
    closed_since_previous_item_ids: list[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in current_rows:
        item_id = _normalize_item_id(row.get("acknowledgement_ingestion_item_id", ""))
        item_status = str(row.get("acknowledgement_ingestion_item_status", "")).strip().lower()

        closure_state = "closed_current"
        if item_status == "open":
            if item_id and item_id in previous_open_item_ids:
                closure_state = "open_carried"
            else:
                closure_state = "open_new"

        rows.append(
            {
                "acknowledgement_ingestion_item_id": item_id,
                "closure_state": closure_state,
                "acknowledgement_ingestion_item_status_gl50": item_status,
                "acknowledgement_ingestion_state_gl50": str(
                    row.get("acknowledgement_ingestion_state", "")
                ).strip(),
                "owner_gl50": str(row.get("owner", "")).strip(),
                "action_id_gl48": str(row.get("action_id_gl48", "")).strip(),
                "required_modality_gl47": str(row.get("required_modality_gl47", "")).strip().lower(),
                "handoff_queue_item_id_gl24": str(row.get("handoff_queue_item_id_gl24", "")).strip(),
                "linked_submission_loop_id_gl24": str(row.get("linked_submission_loop_id_gl24", "")).strip(),
                "acknowledged_submitted_loop_id_gl25": str(
                    row.get("acknowledged_submitted_loop_id_gl25", "")
                ).strip(),
                "acknowledgement_loop_matches_linked_submission_gl50": bool(
                    row.get("acknowledgement_loop_matches_linked_submission", False)
                ),
            }
        )

    for item_id in closed_since_previous_item_ids:
        rows.append(
            {
                "acknowledgement_ingestion_item_id": item_id,
                "closure_state": "closed_since_previous_cycle",
                "acknowledgement_ingestion_item_status_gl50": "closed_or_removed",
                "acknowledgement_ingestion_state_gl50": "",
                "owner_gl50": "",
                "action_id_gl48": "",
                "required_modality_gl47": "",
                "handoff_queue_item_id_gl24": "",
                "linked_submission_loop_id_gl24": "",
                "acknowledged_submitted_loop_id_gl25": "",
                "acknowledgement_loop_matches_linked_submission_gl50": False,
            }
        )

    state_rank = {
        "open_carried": 0,
        "open_new": 1,
        "closed_current": 2,
        "closed_since_previous_cycle": 3,
    }
    rows.sort(
        key=lambda item: (
            state_rank.get(str(item.get("closure_state", "")), 99),
            str(item.get("required_modality_gl47", "")),
            str(item.get("acknowledgement_ingestion_item_id", "")),
        )
    )
    return rows


def _build_report(
    *,
    ack_ingestion_report: dict[str, Any],
    ack_ingestion_report_path: Path,
    collection_report: dict[str, Any],
    collection_report_path: Path,
    previous_closure_report: dict[str, Any] | None,
    previous_closure_report_path: Path | None,
    owner: str,
) -> dict[str, Any]:
    ack_snapshot = _ack_ingestion_snapshot(ack_ingestion_report)
    collection_snapshot = _collection_snapshot(collection_report)
    previous_available = isinstance(previous_closure_report, dict)
    previous_ack_snapshot, previous_collection_snapshot = _previous_snapshot(previous_closure_report)

    current_open_item_ids = set(ack_snapshot.get("open_item_ids", []))
    previous_open_item_ids = set(previous_ack_snapshot.get("open_item_ids", []))
    closed_since_previous_item_ids = sorted(previous_open_item_ids - current_open_item_ids)
    carried_open_item_ids = sorted(current_open_item_ids & previous_open_item_ids)

    current_loop_ids = set(collection_snapshot.get("launch_gate_eligible_loop_ids", []))
    previous_loop_ids = set(previous_collection_snapshot.get("launch_gate_eligible_loop_ids", []))
    net_new_loop_ids = sorted(current_loop_ids - previous_loop_ids)

    current_rows = ack_snapshot.get("rows", [])
    if not isinstance(current_rows, list):
        current_rows = []
    open_rows = [
        row
        for row in current_rows
        if str(row.get("acknowledgement_ingestion_item_status", "")).strip().lower() == "open"
    ]

    counts = {
        "total_item_count": _to_int(ack_snapshot.get("total_item_count", 0), default=0),
        "open_item_count": _to_int(ack_snapshot.get("open_item_count", 0), default=0),
        "closed_item_count": _to_int(ack_snapshot.get("closed_item_count", 0), default=0),
        "previous_open_item_count_gl50": _to_int(previous_ack_snapshot.get("open_item_count", 0), default=0),
        "carried_open_item_count": len(carried_open_item_ids),
        "stale_open_item_count": len(carried_open_item_ids),
        "net_new_closed_item_count": len(closed_since_previous_item_ids),
        "ack_loop_mismatch_open_item_count": sum(
            1
            for row in open_rows
            if str(row.get("acknowledgement_ingestion_state", "")).strip().lower() == "ack_loop_mismatch"
        ),
        "ack_missing_open_item_count": sum(
            1
            for row in open_rows
            if str(row.get("acknowledgement_ingestion_state", "")).strip().lower() == "ack_missing"
        ),
        "missing_handoff_open_item_count": sum(
            1
            for row in open_rows
            if str(row.get("acknowledgement_ingestion_state", "")).strip().lower() == "missing_handoff_queue_item"
        ),
        "net_new_launch_gate_eligible_loop_count": len(net_new_loop_ids),
        "open_item_count_delta": _to_int(ack_snapshot.get("open_item_count", 0), default=0)
        - _to_int(previous_ack_snapshot.get("open_item_count", 0), default=0),
    }

    status = _build_status(
        ack_ingestion_status_gl50=str(ack_snapshot.get("status", "unknown")),
        previous_available=previous_available,
        open_item_count=counts["open_item_count"],
        previous_open_item_count=counts["previous_open_item_count_gl50"],
        net_new_closed_item_count=counts["net_new_closed_item_count"],
        net_new_launch_gate_eligible_loop_count=counts["net_new_launch_gate_eligible_loop_count"],
    )

    warning_codes: list[str] = []
    if counts["open_item_count"] > 0:
        warning_codes.append(
            "open_action_plan_closure_cadence_escalation_acknowledgement_ingestion_closure_items_present"
        )
    if previous_available and counts["net_new_closed_item_count"] <= 0:
        warning_codes.append("no_net_new_closed_acknowledgement_ingestion_items")
    if previous_available and counts["net_new_launch_gate_eligible_loop_count"] <= 0:
        warning_codes.append("no_net_new_launch_gate_eligible_real_loops")
    if counts["stale_open_item_count"] > 0:
        warning_codes.append("stale_open_acknowledgement_ingestion_items_present")
    warning_codes.extend(
        str(item).strip() for item in ack_snapshot.get("warning_codes", []) if str(item).strip()
    )
    warning_codes = _unique_preserve_order(warning_codes)

    return {
        "schema_version": "real_trial_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure.v1",
        "generated_at_utc": _utc_now_iso(),
        "owner": owner,
        "input_paths": {
            "submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_report": str(
                ack_ingestion_report_path
            ),
            "collection_report": str(collection_report_path),
            "previous_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_report": str(
                previous_closure_report_path
            )
            if previous_closure_report_path is not None and previous_available
            else "",
        },
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_status_gl50": str(
            ack_snapshot.get("status", "unknown")
        ),
        "collection_program_status_gl12": str(collection_snapshot.get("program_status", "unknown")),
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_status": status,
        "warning_codes": warning_codes,
        "acknowledgement_ingestion_snapshot": ack_snapshot,
        "collection_snapshot": collection_snapshot,
        "snapshot_delta": {
            "open_item_count_delta": counts["open_item_count_delta"],
            "net_new_closed_item_count": counts["net_new_closed_item_count"],
            "net_new_launch_gate_eligible_loop_count": counts["net_new_launch_gate_eligible_loop_count"],
            "carried_open_item_count": counts["carried_open_item_count"],
            "stale_open_item_count": counts["stale_open_item_count"],
        },
        "carried_open_acknowledgement_ingestion_item_ids": carried_open_item_ids,
        "net_new_closed_acknowledgement_ingestion_item_ids": closed_since_previous_item_ids,
        "net_new_launch_gate_eligible_loop_ids": net_new_loop_ids,
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_counts": counts,
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_rows": _build_rows(
            current_rows=current_rows,
            previous_open_item_ids=previous_open_item_ids,
            closed_since_previous_item_ids=closed_since_previous_item_ids,
        ),
    }


def _render_summary(report: dict[str, Any]) -> str:
    counts = report.get(
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_counts",
        {},
    )
    if not isinstance(counts, dict):
        counts = {}
    warning_codes = report.get("warning_codes", [])
    if not isinstance(warning_codes, list):
        warning_codes = []
    rows = report.get(
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_rows",
        [],
    )
    if not isinstance(rows, list):
        rows = []

    lines = [
        "# Real Trial Submission Queue Follow-Up Resolution Escalation Action Plan Closure Cadence Escalation Acknowledgement Closure Summary",
        "",
        "- GL-50 acknowledgement-ingestion status: `%s`"
        % str(
            report.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_status_gl50",
                "unknown",
            )
        ),
        "- GL-51 acknowledgement-closure status: `%s`"
        % str(
            report.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_status",
                "unknown",
            )
        ),
        "- Total items: `%s`" % str(_to_int(counts.get("total_item_count", 0), default=0)),
        "- Open items: `%s`" % str(_to_int(counts.get("open_item_count", 0), default=0)),
        "- Net-new closed items: `%s`" % str(_to_int(counts.get("net_new_closed_item_count", 0), default=0)),
        "- Stale open items: `%s`" % str(_to_int(counts.get("stale_open_item_count", 0), default=0)),
        "- Net-new launch-gate-eligible loops: `%s`"
        % str(_to_int(counts.get("net_new_launch_gate_eligible_loop_count", 0), default=0)),
        "",
        "## Warning Codes",
    ]
    if warning_codes:
        for code in warning_codes:
            lines.append("- `%s`" % str(code))
    else:
        lines.append("- none")

    lines.extend(["", "## Closure Rows"])
    if rows:
        for row in rows:
            if not isinstance(row, dict):
                continue
            lines.append(
                "- `%s` closure=%s state=%s modality=%s"
                % (
                    str(row.get("acknowledgement_ingestion_item_id", "")),
                    str(row.get("closure_state", "")),
                    str(row.get("acknowledgement_ingestion_state_gl50", "")),
                    str(row.get("required_modality_gl47", "")),
                )
            )
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    ack_ingestion_report_path = Path(
        str(
            args.submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_report
        ).strip()
    ).resolve()
    collection_report_path = Path(str(args.collection_report).strip()).resolve()
    output_path = None if str(args.output).strip() == "-" else Path(str(args.output).strip()).resolve()
    summary_path = None if str(args.summary_output).strip() == "-" else Path(str(args.summary_output).strip()).resolve()
    owner = str(args.owner).strip() or "controlled-beta-ops"

    try:
        if not ack_ingestion_report_path.is_file():
            raise ValueError("GL-50 acknowledgement-ingestion report path does not exist: %s" % ack_ingestion_report_path)
        if not collection_report_path.is_file():
            raise ValueError("GL-12 collection report path does not exist: %s" % collection_report_path)

        ack_ingestion_report = _read_json(ack_ingestion_report_path)
        collection_report = _read_json(collection_report_path)

        previous_report_path: Path | None = None
        previous_report: dict[str, Any] | None = None
        previous_arg = str(
            args.previous_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_report
        ).strip()
        if previous_arg:
            previous_report_path = Path(previous_arg).resolve()
        elif output_path is not None:
            previous_report_path = output_path
        if previous_report_path is not None and previous_report_path.is_file():
            previous_report = _read_json(previous_report_path)

        report = _build_report(
            ack_ingestion_report=ack_ingestion_report,
            ack_ingestion_report_path=ack_ingestion_report_path,
            collection_report=collection_report,
            collection_report_path=collection_report_path,
            previous_closure_report=previous_report,
            previous_closure_report_path=previous_report_path,
            owner=owner,
        )
        summary = _render_summary(report)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(
            "Real trial submission queue follow-up resolution escalation action-plan closure cadence escalation acknowledgement closure generation failed: %s"
            % exc,
            file=sys.stderr,
        )
        return 2

    if output_path is not None:
        _write_text(output_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print(
            "Real trial submission queue follow-up resolution escalation action-plan closure cadence escalation acknowledgement closure report written: %s"
            % output_path
        )
    if summary_path is not None:
        _write_text(summary_path, summary)
        print(
            "Real trial submission queue follow-up resolution escalation action-plan closure cadence escalation acknowledgement closure summary written: %s"
            % summary_path
        )

    delta = report.get("snapshot_delta", {})
    if not isinstance(delta, dict):
        delta = {}
    print(
        "Real trial submission queue follow-up resolution escalation action-plan closure cadence escalation acknowledgement closure status=%s net_new_closed=%s net_new_real_loops=%s"
        % (
            str(
                report.get(
                    "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_status",
                    "unknown",
                )
            ),
            _to_int(delta.get("net_new_closed_item_count", 0), default=0),
            _to_int(delta.get("net_new_launch_gate_eligible_loop_count", 0), default=0),
        )
    )
    if args.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    if bool(args.fail_on_stalled) and str(
        report.get(
            "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_status",
            "",
        )
    ).strip().upper() == "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_STALLED":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
