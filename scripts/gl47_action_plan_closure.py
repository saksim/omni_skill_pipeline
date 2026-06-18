from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ACTION_PLAN_REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-report.json"
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
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-report.json"
)
DEFAULT_SUMMARY_PATH = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-summary.md"
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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


def _normalize_action_rows(rows: Any) -> list[dict[str, Any]]:
    if not isinstance(rows, list):
        return []
    normalized: list[dict[str, Any]] = []
    for row in rows:
        if isinstance(row, dict):
            normalized.append(row)
    return normalized


def _normalize_action_id(value: Any) -> str:
    return str(value or "").strip()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate GL-47 action-plan-closure diagnostics by comparing GL-46 action-plan "
            "snapshots across cycles and binding to GL-12 launch-gate coverage."
        )
    )
    parser.add_argument(
        "--submission-queue-followup-resolution-escalation-action-plan-report",
        default=str(DEFAULT_ACTION_PLAN_REPORT_PATH),
    )
    parser.add_argument(
        "--collection-report",
        default=str(DEFAULT_COLLECTION_REPORT_PATH),
    )
    parser.add_argument(
        "--previous-action-plan-closure-report",
        default="",
        help=(
            "Optional previous GL-47 report. When omitted, script attempts to read existing "
            "--output before writing."
        ),
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help='GL-47 report output path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--summary-output",
        default=str(DEFAULT_SUMMARY_PATH),
        help='GL-47 summary output path. Use "-" to skip writing file.',
    )
    parser.add_argument("--owner", default="controlled-beta-ops")
    parser.add_argument(
        "--fail-on-stalled",
        action="store_true",
        help="Exit with code 1 when closure status is ACTION_PLAN_CLOSURE_STALLED.",
    )
    parser.add_argument("--print-json", action="store_true")
    return parser.parse_args()


def _action_plan_snapshot(action_plan_report: dict[str, Any]) -> dict[str, Any]:
    status = str(
        action_plan_report.get("followup_resolution_escalation_action_plan_status", "unknown")
    ).strip()
    rows = _normalize_action_rows(action_plan_report.get("followup_resolution_escalation_action_plan_rows", []))
    counts = action_plan_report.get("followup_resolution_escalation_action_plan_counts", {})
    if not isinstance(counts, dict):
        counts = {}

    open_action_ids: list[str] = []
    normalized_rows: list[dict[str, Any]] = []
    for row in rows:
        action_id = _normalize_action_id(row.get("action_id", ""))
        action_status = str(row.get("action_status", "")).strip().lower() or "open"
        if action_status == "open" and action_id:
            open_action_ids.append(action_id)
        normalized_rows.append(
            {
                "action_id": action_id,
                "action_status": action_status,
                "action_type": str(row.get("action_type", "")).strip(),
                "required_modality": str(row.get("required_modality", "")).strip().lower(),
                "reason": str(row.get("reason", "")).strip(),
                "owner": str(row.get("owner", "")).strip(),
                "backfill_slot_index": _to_int(row.get("backfill_slot_index", 0), default=0),
                "linked_submission_loop_id": str(row.get("linked_submission_loop_id", "")).strip(),
                "source": str(row.get("source", "")).strip(),
            }
        )

    return {
        "status": status,
        "warning_codes": action_plan_report.get("warning_codes", []),
        "rows": normalized_rows,
        "total_action_count": _to_int(counts.get("total_action_count", len(normalized_rows)), default=0),
        "open_action_count": _to_int(
            counts.get(
                "open_action_count",
                len([item for item in normalized_rows if item.get("action_status") == "open"]),
            ),
            default=0,
        ),
        "closed_action_count": _to_int(counts.get("closed_action_count", 0), default=0),
        "open_action_ids": sorted(set(open_action_ids)),
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
                "open_action_count": 0,
                "open_action_ids": [],
            },
            {
                "launch_gate_eligible_complete_loop_count": 0,
                "launch_gate_eligible_loop_ids": [],
            },
        )

    action_plan_snapshot = previous_report.get("action_plan_snapshot", {})
    if not isinstance(action_plan_snapshot, dict):
        action_plan_snapshot = {}
    collection_snapshot = previous_report.get("collection_snapshot", {})
    if not isinstance(collection_snapshot, dict):
        collection_snapshot = {}

    return (
        {
            "open_action_count": _to_int(action_plan_snapshot.get("open_action_count", 0), default=0),
            "open_action_ids": sorted(
                set(
                    _normalize_action_id(item)
                    for item in action_plan_snapshot.get("open_action_ids", [])
                    if _normalize_action_id(item)
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
    action_plan_status_gl46: str,
    previous_available: bool,
    open_action_count: int,
    previous_open_action_count: int,
    net_new_closed_action_count: int,
    net_new_launch_gate_eligible_loop_count: int,
) -> str:
    status = action_plan_status_gl46.strip().upper()
    if status == "ACTION_PLAN_NOT_REQUIRED" and open_action_count <= 0:
        return "ACTION_PLAN_CLOSURE_NOT_REQUIRED"
    if open_action_count <= 0:
        if previous_available and previous_open_action_count > 0:
            return "ACTION_PLAN_CLOSURE_COMPLETE"
        return "ACTION_PLAN_CLOSURE_CLEARED"
    if not previous_available:
        return "ACTION_PLAN_CLOSURE_BASELINE_INITIALIZED"
    if net_new_closed_action_count > 0 or net_new_launch_gate_eligible_loop_count > 0:
        return "ACTION_PLAN_CLOSURE_PROGRESSING"
    return "ACTION_PLAN_CLOSURE_STALLED"


def _build_rows(
    *,
    current_action_rows: list[dict[str, Any]],
    previous_open_action_ids: set[str],
    closed_since_previous_action_ids: list[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in current_action_rows:
        action_id = _normalize_action_id(row.get("action_id", ""))
        closure_state = "open_new"
        if action_id and action_id in previous_open_action_ids:
            closure_state = "open_carried"
        rows.append(
            {
                "action_id": action_id,
                "closure_state": closure_state,
                "action_status_gl46": str(row.get("action_status", "")).strip(),
                "action_type_gl46": str(row.get("action_type", "")).strip(),
                "required_modality_gl46": str(row.get("required_modality", "")).strip().lower(),
                "reason_gl46": str(row.get("reason", "")).strip(),
                "owner_gl46": str(row.get("owner", "")).strip(),
                "backfill_slot_index_gl46": _to_int(row.get("backfill_slot_index", 0), default=0),
                "linked_submission_loop_id_gl46": str(row.get("linked_submission_loop_id", "")).strip(),
                "source_gl46": str(row.get("source", "")).strip(),
            }
        )
    for action_id in closed_since_previous_action_ids:
        rows.append(
            {
                "action_id": action_id,
                "closure_state": "closed_since_previous_cycle",
                "action_status_gl46": "closed",
                "action_type_gl46": "",
                "required_modality_gl46": "",
                "reason_gl46": "",
                "owner_gl46": "",
                "backfill_slot_index_gl46": 0,
                "linked_submission_loop_id_gl46": "",
                "source_gl46": "previous_action_plan_snapshot",
            }
        )
    rows.sort(
        key=lambda item: (
            0 if str(item.get("closure_state", "")) == "open_carried" else 1,
            0 if str(item.get("closure_state", "")) == "open_new" else 1,
            str(item.get("required_modality_gl46", "")),
            str(item.get("action_id", "")),
        )
    )
    return rows


def _build_report(
    *,
    action_plan_report: dict[str, Any],
    action_plan_report_path: Path,
    collection_report: dict[str, Any],
    collection_report_path: Path,
    previous_closure_report: dict[str, Any] | None,
    previous_closure_report_path: Path | None,
    owner: str,
) -> dict[str, Any]:
    action_plan_snapshot = _action_plan_snapshot(action_plan_report)
    collection_snapshot = _collection_snapshot(collection_report)
    previous_available = isinstance(previous_closure_report, dict)
    previous_action_plan_snapshot, previous_collection_snapshot = _previous_snapshot(previous_closure_report)

    current_open_action_ids = set(action_plan_snapshot.get("open_action_ids", []))
    previous_open_action_ids = set(previous_action_plan_snapshot.get("open_action_ids", []))
    closed_since_previous_action_ids = sorted(previous_open_action_ids - current_open_action_ids)
    carried_open_action_ids = sorted(current_open_action_ids & previous_open_action_ids)

    current_loop_ids = set(collection_snapshot.get("launch_gate_eligible_loop_ids", []))
    previous_loop_ids = set(previous_collection_snapshot.get("launch_gate_eligible_loop_ids", []))
    net_new_loop_ids = sorted(current_loop_ids - previous_loop_ids)

    counts = {
        "total_action_count": _to_int(action_plan_snapshot.get("total_action_count", 0), default=0),
        "open_action_count": _to_int(action_plan_snapshot.get("open_action_count", 0), default=0),
        "closed_action_count": _to_int(action_plan_snapshot.get("closed_action_count", 0), default=0),
        "carried_open_action_count": len(carried_open_action_ids),
        "net_new_closed_action_count": len(closed_since_previous_action_ids),
        "stale_open_action_count": len(carried_open_action_ids),
        "net_new_launch_gate_eligible_loop_count": len(net_new_loop_ids),
        "open_action_count_delta": _to_int(action_plan_snapshot.get("open_action_count", 0), default=0)
        - _to_int(previous_action_plan_snapshot.get("open_action_count", 0), default=0),
    }

    status = _build_status(
        action_plan_status_gl46=str(action_plan_snapshot.get("status", "unknown")),
        previous_available=previous_available,
        open_action_count=counts["open_action_count"],
        previous_open_action_count=_to_int(previous_action_plan_snapshot.get("open_action_count", 0), default=0),
        net_new_closed_action_count=counts["net_new_closed_action_count"],
        net_new_launch_gate_eligible_loop_count=counts["net_new_launch_gate_eligible_loop_count"],
    )

    warning_codes: list[str] = []
    if counts["open_action_count"] > 0:
        warning_codes.append("open_followup_resolution_escalation_action_plan_items_present")
    if previous_available and counts["net_new_closed_action_count"] <= 0:
        warning_codes.append("no_net_new_closed_action_plan_items")
    if previous_available and counts["net_new_launch_gate_eligible_loop_count"] <= 0:
        warning_codes.append("no_net_new_launch_gate_eligible_real_loops")
    if counts["stale_open_action_count"] > 0:
        warning_codes.append("stale_open_action_plan_items_present")
    warning_codes.extend(
        str(item).strip()
        for item in action_plan_snapshot.get("warning_codes", [])
        if str(item).strip()
    )
    warning_codes = _unique_preserve_order(warning_codes)

    return {
        "schema_version": "real_trial_submission_queue_followup_resolution_escalation_action_plan_closure.v1",
        "generated_at_utc": _utc_now_iso(),
        "owner": owner,
        "input_paths": {
            "submission_queue_followup_resolution_escalation_action_plan_report": str(action_plan_report_path),
            "collection_report": str(collection_report_path),
            "previous_action_plan_closure_report": str(previous_closure_report_path)
            if previous_closure_report_path is not None and previous_available
            else "",
        },
        "followup_resolution_escalation_action_plan_status_gl46": str(
            action_plan_snapshot.get("status", "unknown")
        ),
        "collection_program_status_gl12": str(collection_snapshot.get("program_status", "unknown")),
        "followup_resolution_escalation_action_plan_closure_status": status,
        "warning_codes": warning_codes,
        "action_plan_snapshot": action_plan_snapshot,
        "collection_snapshot": collection_snapshot,
        "snapshot_delta": {
            "open_action_count_delta": counts["open_action_count_delta"],
            "net_new_closed_action_count": counts["net_new_closed_action_count"],
            "net_new_launch_gate_eligible_loop_count": counts["net_new_launch_gate_eligible_loop_count"],
            "carried_open_action_count": counts["carried_open_action_count"],
            "stale_open_action_count": counts["stale_open_action_count"],
        },
        "net_new_closed_action_ids": closed_since_previous_action_ids,
        "carried_open_action_ids": carried_open_action_ids,
        "net_new_launch_gate_eligible_loop_ids": net_new_loop_ids,
        "followup_resolution_escalation_action_plan_closure_counts": counts,
        "followup_resolution_escalation_action_plan_closure_rows": _build_rows(
            current_action_rows=action_plan_snapshot.get("rows", []),
            previous_open_action_ids=previous_open_action_ids,
            closed_since_previous_action_ids=closed_since_previous_action_ids,
        ),
    }


def _render_summary(report: dict[str, Any]) -> str:
    counts = report.get("followup_resolution_escalation_action_plan_closure_counts", {})
    if not isinstance(counts, dict):
        counts = {}
    warning_codes = report.get("warning_codes", [])
    if not isinstance(warning_codes, list):
        warning_codes = []
    rows = report.get("followup_resolution_escalation_action_plan_closure_rows", [])
    if not isinstance(rows, list):
        rows = []
    lines = [
        "# Real Trial Submission Queue Follow-Up Resolution Escalation Action Plan Closure Summary",
        "",
        "- GL-46 action-plan status: `%s`"
        % str(report.get("followup_resolution_escalation_action_plan_status_gl46", "unknown")),
        "- GL-47 closure status: `%s`"
        % str(report.get("followup_resolution_escalation_action_plan_closure_status", "unknown")),
        "- Total action items: `%s`" % str(_to_int(counts.get("total_action_count", 0), default=0)),
        "- Open action items: `%s`" % str(_to_int(counts.get("open_action_count", 0), default=0)),
        "- Net-new closed action items: `%s`"
        % str(_to_int(counts.get("net_new_closed_action_count", 0), default=0)),
        "- Stale open action items: `%s`" % str(_to_int(counts.get("stale_open_action_count", 0), default=0)),
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
    lines.extend(["", "## Action Plan Closure Rows"])
    if rows:
        for row in rows:
            if not isinstance(row, dict):
                continue
            lines.append(
                "- `%s` closure=%s type=%s modality=%s"
                % (
                    str(row.get("action_id", "")),
                    str(row.get("closure_state", "")),
                    str(row.get("action_type_gl46", "")),
                    str(row.get("required_modality_gl46", "")),
                )
            )
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    action_plan_report_path = Path(
        str(args.submission_queue_followup_resolution_escalation_action_plan_report).strip()
    ).resolve()
    collection_report_path = Path(str(args.collection_report).strip()).resolve()
    output_path = None if str(args.output).strip() == "-" else Path(str(args.output).strip()).resolve()
    summary_path = None if str(args.summary_output).strip() == "-" else Path(str(args.summary_output).strip()).resolve()
    owner = str(args.owner).strip() or "controlled-beta-ops"

    try:
        if not action_plan_report_path.is_file():
            raise ValueError("GL-46 action-plan report path does not exist: %s" % action_plan_report_path)
        if not collection_report_path.is_file():
            raise ValueError("GL-12 collection report path does not exist: %s" % collection_report_path)
        action_plan_report = _read_json(action_plan_report_path)
        collection_report = _read_json(collection_report_path)

        previous_report_path: Path | None = None
        previous_report: dict[str, Any] | None = None
        previous_arg = str(args.previous_action_plan_closure_report).strip()
        if previous_arg:
            previous_report_path = Path(previous_arg).resolve()
        elif output_path is not None:
            previous_report_path = output_path
        if previous_report_path is not None and previous_report_path.is_file():
            previous_report = _read_json(previous_report_path)

        report = _build_report(
            action_plan_report=action_plan_report,
            action_plan_report_path=action_plan_report_path,
            collection_report=collection_report,
            collection_report_path=collection_report_path,
            previous_closure_report=previous_report,
            previous_closure_report_path=previous_report_path,
            owner=owner,
        )
        summary = _render_summary(report)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(
            "Real trial follow-up resolution escalation action-plan closure generation failed: %s"
            % exc,
            file=sys.stderr,
        )
        return 2

    if output_path is not None:
        _write_text(output_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print(
            "Real trial follow-up resolution escalation action-plan closure report written: %s"
            % output_path
        )
    if summary_path is not None:
        _write_text(summary_path, summary)
        print(
            "Real trial follow-up resolution escalation action-plan closure summary written: %s"
            % summary_path
        )

    delta = report.get("snapshot_delta", {})
    if not isinstance(delta, dict):
        delta = {}
    print(
        "Real trial follow-up resolution escalation action-plan closure status=%s net_new_closed=%s net_new_real_loops=%s"
        % (
            str(report.get("followup_resolution_escalation_action_plan_closure_status", "unknown")),
            _to_int(delta.get("net_new_closed_action_count", 0), default=0),
            _to_int(delta.get("net_new_launch_gate_eligible_loop_count", 0), default=0),
        )
    )
    if args.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    if bool(args.fail_on_stalled) and str(
        report.get("followup_resolution_escalation_action_plan_closure_status", "")
    ).strip().upper() == "ACTION_PLAN_CLOSURE_STALLED":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
