from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COLLECTION_REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-loop-collection-report.json"
)
DEFAULT_BACKFILL_EXECUTION_REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-execution-report.json"
)
DEFAULT_BACKFILL_SUBMISSION_CONSUMPTION_REPORT_PATH = (
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
    / "real-trial-backfill-submission-throughput-report.json"
)
DEFAULT_SUMMARY_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-throughput-summary.md"
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compute GL-35 sustained real-submission throughput diagnostics by comparing "
            "current launch-gate-eligible real-loop coverage with the previous snapshot."
        )
    )
    parser.add_argument("--collection-report", default=str(DEFAULT_COLLECTION_REPORT_PATH))
    parser.add_argument("--backfill-execution-report", default=str(DEFAULT_BACKFILL_EXECUTION_REPORT_PATH))
    parser.add_argument(
        "--backfill-submission-consumption-report",
        default=str(DEFAULT_BACKFILL_SUBMISSION_CONSUMPTION_REPORT_PATH),
    )
    parser.add_argument(
        "--previous-throughput-report",
        default="",
        help=(
            "Optional previous throughput report path used for delta comparison. "
            "When omitted, script attempts to read existing --output file before writing."
        ),
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help='Throughput report output path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--summary-output",
        default=str(DEFAULT_SUMMARY_PATH),
        help='Throughput summary output path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--owner",
        default="controlled-beta-ops",
        help="Owner tag written into throughput diagnostics artifacts.",
    )
    parser.add_argument("--print-json", action="store_true")
    parser.add_argument(
        "--fail-on-stalled",
        action="store_true",
        help="Exit with code 1 when throughput status is THROUGHPUT_STALLED.",
    )
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


def _to_bool(value: Any, *, default: bool = False) -> bool:
    if value is None:
        return bool(default)
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off"}:
        return False
    return bool(default)


def _unique_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        item = str(value).strip()
        if not item or item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def _normalize_loop_ids(rows: Any) -> list[str]:
    if not isinstance(rows, list):
        return []
    values: list[str] = []
    for row in rows:
        if isinstance(row, dict):
            loop_id = str(row.get("loop_id", "")).strip()
        else:
            loop_id = str(row).strip()
        if loop_id:
            values.append(loop_id)
    # Deterministic set semantics for delta comparison.
    return sorted(set(values))


def _normalize_snapshot_from_report(report: dict[str, Any]) -> dict[str, Any]:
    snapshot = report.get("snapshot", {})
    if isinstance(snapshot, dict):
        current = snapshot.get("current", {})
        if isinstance(current, dict):
            return current
    # Backward-safe fallback: treat report itself as snapshot-like.
    return report


def _build_current_snapshot(
    *,
    collection_report: dict[str, Any],
    backfill_execution_report: dict[str, Any],
    backfill_submission_consumption_report: dict[str, Any],
) -> dict[str, Any]:
    alignment = collection_report.get("launch_gate_alignment", {})
    if not isinstance(alignment, dict):
        alignment = {}
    backfill_slot_counts = backfill_execution_report.get("slot_counts", {})
    if not isinstance(backfill_slot_counts, dict):
        backfill_slot_counts = {}
    submission_backed_slot_counts = backfill_execution_report.get("submission_backed_slot_counts", {})
    if not isinstance(submission_backed_slot_counts, dict):
        submission_backed_slot_counts = {}
    consumption_counts = backfill_submission_consumption_report.get("counts", {})
    if not isinstance(consumption_counts, dict):
        consumption_counts = {}
    recommended_backfill_slots = alignment.get("recommended_backfill_slots", [])
    if not isinstance(recommended_backfill_slots, list):
        recommended_backfill_slots = []
    missing_target_launch_modalities = alignment.get("missing_target_launch_modalities", [])
    if not isinstance(missing_target_launch_modalities, list):
        missing_target_launch_modalities = []
    pending_template_rows = backfill_submission_consumption_report.get("pending_template_rows", [])
    if not isinstance(pending_template_rows, list):
        pending_template_rows = []

    loop_ids = _normalize_loop_ids(collection_report.get("collected_real_launch_gate_eligible_loops", []))
    return {
        "launch_gate_eligible_complete_loop_count": _to_int(
            alignment.get("launch_gate_eligible_complete_loop_count", 0),
            default=len(loop_ids),
        ),
        "launch_gate_eligible_modality_count": _to_int(
            alignment.get("launch_gate_eligible_modality_count", 0),
            default=0,
        ),
        "missing_complete_loops_to_threshold": _to_int(
            alignment.get("missing_complete_loops_to_threshold", 0),
            default=0,
        ),
        "missing_modalities_to_threshold": _to_int(
            alignment.get("missing_modalities_to_threshold", 0),
            default=0,
        ),
        "recommended_backfill_slot_count": _to_int(
            alignment.get("recommended_backfill_slot_count", 0),
            default=0,
        ),
        "backfill_execution_remaining_slot_count": _to_int(
            backfill_slot_counts.get("remaining_slot_count", 0),
            default=0,
        ),
        "backfill_execution_submission_backed_remaining_slot_count": _to_int(
            submission_backed_slot_counts.get("submission_backed_remaining_slot_count", 0),
            default=0,
        ),
        "submission_consumption_consumed_loop_count": _to_int(
            consumption_counts.get("consumed_loop_count", 0),
            default=0,
        ),
        "submission_consumption_status": str(
            backfill_submission_consumption_report.get("consumption_status", "unknown")
        ).strip(),
        "submission_consumption_template_loop_count": _to_int(
            consumption_counts.get("template_loop_count", 0),
            default=0,
        ),
        "submission_consumption_pending_template_loop_count": _to_int(
            consumption_counts.get("pending_template_loop_count", 0),
            default=0,
        ),
        "submission_consumption_invalid_submission_count": _to_int(
            consumption_counts.get("invalid_submission_count", 0),
            default=0,
        ),
        "submission_consumption_unresolved_submission_count": _to_int(
            consumption_counts.get("unresolved_submission_count", 0),
            default=0,
        ),
        "submission_consumption_pending_template_rows": pending_template_rows,
        "target_launch_modality_loop_counts": alignment.get("target_launch_modality_loop_counts", {}),
        "missing_target_launch_modalities": missing_target_launch_modalities,
        "recommended_backfill_slots": recommended_backfill_slots,
        "launch_gate_eligible_real_loop_ids": loop_ids,
    }


def _empty_snapshot() -> dict[str, Any]:
    return {
        "launch_gate_eligible_complete_loop_count": 0,
        "launch_gate_eligible_modality_count": 0,
        "missing_complete_loops_to_threshold": 0,
        "missing_modalities_to_threshold": 0,
        "recommended_backfill_slot_count": 0,
        "backfill_execution_remaining_slot_count": 0,
        "backfill_execution_submission_backed_remaining_slot_count": 0,
        "submission_consumption_consumed_loop_count": 0,
        "submission_consumption_status": "unknown",
        "submission_consumption_template_loop_count": 0,
        "submission_consumption_pending_template_loop_count": 0,
        "submission_consumption_invalid_submission_count": 0,
        "submission_consumption_unresolved_submission_count": 0,
        "submission_consumption_pending_template_rows": [],
        "target_launch_modality_loop_counts": {},
        "missing_target_launch_modalities": [],
        "recommended_backfill_slots": [],
        "launch_gate_eligible_real_loop_ids": [],
    }


def _build_execution_focus(*, current: dict[str, Any], throughput_status: str, threshold_met: bool) -> dict[str, Any]:
    recommended_slots = current.get("recommended_backfill_slots", [])
    if not isinstance(recommended_slots, list):
        recommended_slots = []
    pending_template_rows = current.get("submission_consumption_pending_template_rows", [])
    if not isinstance(pending_template_rows, list):
        pending_template_rows = []

    recommended_submission_actions: list[dict[str, Any]] = []
    priority_modality_counts: dict[str, int] = {}

    for row in pending_template_rows:
        if not isinstance(row, dict):
            continue
        modality = str(row.get("required_modality", "")).strip().lower()
        action_id = str(row.get("backfill_action_id", "")).strip()
        slot_index = _to_int(row.get("backfill_slot_index", 0), default=0)
        if not modality:
            continue
        priority_modality_counts[modality] = priority_modality_counts.get(modality, 0) + 1
        recommended_submission_actions.append(
            {
                "backfill_action_id": action_id or ("gl23-slot-%03d-%s" % (slot_index, modality) if slot_index > 0 else ""),
                "backfill_slot_index": slot_index,
                "required_modality": modality,
                "reason": "pending_template_submission_required",
            }
        )

    if not recommended_submission_actions:
        for slot in recommended_slots:
            if not isinstance(slot, dict):
                continue
            modality = str(slot.get("required_modality", "")).strip().lower()
            if not modality:
                continue
            slot_index = _to_int(slot.get("slot_index", 0), default=0)
            action_id = str(slot.get("expected_action_id", "")).strip()
            reason = str(slot.get("reason", "recommended_backfill_slot")).strip() or "recommended_backfill_slot"
            priority_modality_counts[modality] = priority_modality_counts.get(modality, 0) + 1
            recommended_submission_actions.append(
                {
                    "backfill_action_id": action_id or ("gl23-slot-%03d-%s" % (slot_index, modality) if slot_index > 0 else ""),
                    "backfill_slot_index": slot_index,
                    "required_modality": modality,
                    "reason": reason,
                }
            )

    if not priority_modality_counts:
        missing_modalities = current.get("missing_target_launch_modalities", [])
        if isinstance(missing_modalities, list):
            for raw_modality in missing_modalities:
                modality = str(raw_modality).strip().lower()
                if modality:
                    priority_modality_counts[modality] = priority_modality_counts.get(modality, 0) + 1

    recommended_submission_actions.sort(
        key=lambda row: (
            _to_int(row.get("backfill_slot_index", 0), default=0) <= 0,
            _to_int(row.get("backfill_slot_index", 0), default=0),
            str(row.get("backfill_action_id", "")),
        )
    )
    priority_modalities = [
        {"modality": modality, "pending_slot_count": count}
        for modality, count in sorted(
            priority_modality_counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    ]

    missing_loops_to_threshold = _to_int(current.get("missing_complete_loops_to_threshold", 0), default=0)
    missing_modalities_to_threshold = _to_int(current.get("missing_modalities_to_threshold", 0), default=0)
    pending_template_loop_count = _to_int(
        current.get("submission_consumption_pending_template_loop_count", 0),
        default=0,
    )
    invalid_submission_count = _to_int(
        current.get("submission_consumption_invalid_submission_count", 0),
        default=0,
    )
    unresolved_submission_count = _to_int(
        current.get("submission_consumption_unresolved_submission_count", 0),
        default=0,
    )
    pending_submission_action_count = max(pending_template_loop_count, len(recommended_submission_actions))
    consumption_status = str(current.get("submission_consumption_status", "unknown")).strip().upper() or "UNKNOWN"

    if threshold_met:
        return {
            "action_plan_status": "ACTION_PLAN_NOT_REQUIRED",
            "action_plan_blockers": [],
            "pending_submission_action_count": 0,
            "recommended_submission_action_count": 0,
            "priority_modalities": [],
            "recommended_submission_actions": [],
            "submission_consumption_status": consumption_status,
            "submission_consumption_template_loop_count": _to_int(
                current.get("submission_consumption_template_loop_count", 0),
                default=0,
            ),
            "submission_consumption_pending_template_loop_count": pending_template_loop_count,
            "submission_consumption_invalid_submission_count": invalid_submission_count,
            "submission_consumption_unresolved_submission_count": unresolved_submission_count,
        }

    action_plan_blockers: list[str] = []
    if missing_loops_to_threshold > 0:
        action_plan_blockers.append("real_loop_volume_below_threshold")
    if missing_modalities_to_threshold > 0:
        action_plan_blockers.append("real_loop_modality_coverage_below_threshold")
    if throughput_status in {"THROUGHPUT_BASELINE_INITIALIZED", "THROUGHPUT_STALLED"}:
        action_plan_blockers.append("throughput_not_progressing")
    if consumption_status == "NO_SUBMISSIONS_PROVIDED":
        action_plan_blockers.append("no_real_submissions_provided")
    if invalid_submission_count > 0:
        action_plan_blockers.append("invalid_submission_rows_present")
    if unresolved_submission_count > 0:
        action_plan_blockers.append("unresolved_submission_rows_present")
    action_plan_blockers = _unique_preserve_order(action_plan_blockers)

    if invalid_submission_count > 0 or unresolved_submission_count > 0:
        action_plan_status = "ACTION_PLAN_BLOCKED_BY_SUBMISSION_ERRORS"
    elif pending_submission_action_count > 0:
        action_plan_status = "ACTION_PLAN_WAITING_FOR_SUBMISSIONS"
    else:
        action_plan_status = "ACTION_PLAN_REBUILD_REQUIRED"

    return {
        "action_plan_status": action_plan_status,
        "action_plan_blockers": action_plan_blockers,
        "pending_submission_action_count": pending_submission_action_count,
        "recommended_submission_action_count": len(recommended_submission_actions),
        "priority_modalities": priority_modalities,
        "recommended_submission_actions": recommended_submission_actions,
        "submission_consumption_status": consumption_status,
        "submission_consumption_template_loop_count": _to_int(
            current.get("submission_consumption_template_loop_count", 0),
            default=0,
        ),
        "submission_consumption_pending_template_loop_count": pending_template_loop_count,
        "submission_consumption_invalid_submission_count": invalid_submission_count,
        "submission_consumption_unresolved_submission_count": unresolved_submission_count,
    }


def _build_report(
    *,
    owner: str,
    collection_report: dict[str, Any],
    backfill_execution_report: dict[str, Any],
    backfill_submission_consumption_report: dict[str, Any],
    collection_report_path: Path,
    backfill_execution_report_path: Path,
    backfill_submission_consumption_report_path: Path,
    previous_throughput_report: dict[str, Any] | None,
    previous_throughput_report_path: Path | None,
) -> dict[str, Any]:
    current = _build_current_snapshot(
        collection_report=collection_report,
        backfill_execution_report=backfill_execution_report,
        backfill_submission_consumption_report=backfill_submission_consumption_report,
    )
    previous_available = isinstance(previous_throughput_report, dict)
    previous = _normalize_snapshot_from_report(previous_throughput_report) if previous_available else _empty_snapshot()

    current_loop_ids = set(_normalize_loop_ids(current.get("launch_gate_eligible_real_loop_ids", [])))
    previous_loop_ids = set(_normalize_loop_ids(previous.get("launch_gate_eligible_real_loop_ids", [])))
    net_new_loop_ids = sorted(current_loop_ids - previous_loop_ids)
    dropped_loop_ids = sorted(previous_loop_ids - current_loop_ids)
    retained_loop_ids = sorted(current_loop_ids & previous_loop_ids)

    delta = {
        "launch_gate_eligible_complete_loop_count": _to_int(current.get("launch_gate_eligible_complete_loop_count", 0))
        - _to_int(previous.get("launch_gate_eligible_complete_loop_count", 0)),
        "launch_gate_eligible_modality_count": _to_int(current.get("launch_gate_eligible_modality_count", 0))
        - _to_int(previous.get("launch_gate_eligible_modality_count", 0)),
        "missing_complete_loops_to_threshold": _to_int(current.get("missing_complete_loops_to_threshold", 0))
        - _to_int(previous.get("missing_complete_loops_to_threshold", 0)),
        "missing_modalities_to_threshold": _to_int(current.get("missing_modalities_to_threshold", 0))
        - _to_int(previous.get("missing_modalities_to_threshold", 0)),
        "recommended_backfill_slot_count": _to_int(current.get("recommended_backfill_slot_count", 0))
        - _to_int(previous.get("recommended_backfill_slot_count", 0)),
        "backfill_execution_remaining_slot_count": _to_int(
            current.get("backfill_execution_remaining_slot_count", 0)
        )
        - _to_int(previous.get("backfill_execution_remaining_slot_count", 0)),
        "backfill_execution_submission_backed_remaining_slot_count": _to_int(
            current.get("backfill_execution_submission_backed_remaining_slot_count", 0)
        )
        - _to_int(previous.get("backfill_execution_submission_backed_remaining_slot_count", 0)),
        "submission_consumption_consumed_loop_count": _to_int(
            current.get("submission_consumption_consumed_loop_count", 0)
        )
        - _to_int(previous.get("submission_consumption_consumed_loop_count", 0)),
        "net_new_launch_gate_eligible_real_loop_count": len(net_new_loop_ids),
        "dropped_launch_gate_eligible_real_loop_count": len(dropped_loop_ids),
    }

    threshold_met = (
        _to_int(current.get("missing_complete_loops_to_threshold", 0)) == 0
        and _to_int(current.get("missing_modalities_to_threshold", 0)) == 0
    )

    warning_codes: list[str] = []
    if dropped_loop_ids:
        warning_codes.append("historical_real_loops_missing_from_current_snapshot")
    if previous_available and _to_int(delta["net_new_launch_gate_eligible_real_loop_count"]) == 0 and not threshold_met:
        warning_codes.append("no_net_new_launch_gate_eligible_real_loops")
    if (
        previous_available
        and _to_int(current.get("submission_consumption_consumed_loop_count", 0)) > 0
        and _to_int(delta["net_new_launch_gate_eligible_real_loop_count"]) == 0
    ):
        warning_codes.append("consumed_submission_without_net_new_real_loop")
    if _to_int(current.get("missing_modalities_to_threshold", 0)) > 0:
        warning_codes.append("modality_gap_persists")

    if threshold_met:
        throughput_status = "THROUGHPUT_THRESHOLD_MET"
    elif not previous_available:
        throughput_status = "THROUGHPUT_BASELINE_INITIALIZED"
    else:
        has_progress_signal = (
            _to_int(delta["net_new_launch_gate_eligible_real_loop_count"]) > 0
            or _to_int(delta["missing_complete_loops_to_threshold"]) < 0
            or _to_int(delta["missing_modalities_to_threshold"]) < 0
            or _to_int(delta["backfill_execution_remaining_slot_count"]) < 0
            or _to_int(delta["backfill_execution_submission_backed_remaining_slot_count"]) < 0
        )
        throughput_status = "THROUGHPUT_PROGRESSING" if has_progress_signal else "THROUGHPUT_STALLED"

    if _to_int(current.get("submission_consumption_invalid_submission_count", 0), default=0) > 0:
        warning_codes.append("invalid_submission_rows_present")
    if _to_int(current.get("submission_consumption_unresolved_submission_count", 0), default=0) > 0:
        warning_codes.append("unresolved_submission_rows_present")
    warning_codes = _unique_preserve_order(warning_codes)

    execution_focus = _build_execution_focus(
        current=current,
        throughput_status=throughput_status,
        threshold_met=threshold_met,
    )

    return {
        "schema_version": "real_trial_submission_throughput.v1",
        "generated_at_utc": _utc_now_iso(),
        "owner": owner,
        "input_paths": {
            "collection_report": str(collection_report_path),
            "backfill_execution_report": str(backfill_execution_report_path),
            "backfill_submission_consumption_report": str(backfill_submission_consumption_report_path),
            "previous_throughput_report": str(previous_throughput_report_path) if previous_throughput_report_path else "",
        },
        "throughput_status": throughput_status,
        "threshold_met": threshold_met,
        "warning_codes": warning_codes,
        "execution_focus": execution_focus,
        "snapshot": {
            "previous_snapshot_available": previous_available,
            "previous": previous,
            "current": current,
            "delta": delta,
            "net_new_launch_gate_eligible_real_loop_ids": net_new_loop_ids,
            "retained_launch_gate_eligible_real_loop_ids": retained_loop_ids,
            "dropped_launch_gate_eligible_real_loop_ids": dropped_loop_ids,
        },
    }


def _render_summary(report: dict[str, Any]) -> str:
    snapshot = report.get("snapshot", {})
    if not isinstance(snapshot, dict):
        snapshot = {}
    current = snapshot.get("current", {})
    if not isinstance(current, dict):
        current = {}
    previous = snapshot.get("previous", {})
    if not isinstance(previous, dict):
        previous = {}
    delta = snapshot.get("delta", {})
    if not isinstance(delta, dict):
        delta = {}
    warning_codes = report.get("warning_codes", [])
    if not isinstance(warning_codes, list):
        warning_codes = []
    execution_focus = report.get("execution_focus", {})
    if not isinstance(execution_focus, dict):
        execution_focus = {}

    lines = [
        "# Real Trial Submission Throughput Summary",
        "",
        "- Throughput status: `%s`" % str(report.get("throughput_status", "unknown")),
        "- Threshold met: `%s`" % str(_to_bool(report.get("threshold_met", False))).lower(),
        "- Previous snapshot available: `%s`"
        % str(_to_bool(snapshot.get("previous_snapshot_available", False))).lower(),
        "- Current eligible real loops: `%s`"
        % str(_to_int(current.get("launch_gate_eligible_complete_loop_count", 0))),
        "- Previous eligible real loops: `%s`"
        % str(_to_int(previous.get("launch_gate_eligible_complete_loop_count", 0))),
        "- Net new eligible real loops: `%s`"
        % str(_to_int(delta.get("net_new_launch_gate_eligible_real_loop_count", 0))),
        "- Current missing loops to threshold: `%s`"
        % str(_to_int(current.get("missing_complete_loops_to_threshold", 0))),
        "- Current missing modalities to threshold: `%s`"
        % str(_to_int(current.get("missing_modalities_to_threshold", 0))),
        "- Current remaining backfill slots: `%s`"
        % str(_to_int(current.get("backfill_execution_remaining_slot_count", 0))),
        "- Current submission-backed remaining slots: `%s`"
        % str(_to_int(current.get("backfill_execution_submission_backed_remaining_slot_count", 0))),
        "- Current consumed submission loops: `%s`"
        % str(_to_int(current.get("submission_consumption_consumed_loop_count", 0))),
        "- Execution focus status: `%s`" % str(execution_focus.get("action_plan_status", "unknown")),
        "- Pending submission actions: `%s`"
        % str(_to_int(execution_focus.get("pending_submission_action_count", 0), default=0)),
        "",
        "## Warning Codes",
    ]
    if warning_codes:
        for warning in warning_codes:
            lines.append("- `%s`" % str(warning))
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Priority Modalities",
        ]
    )
    priority_modalities = execution_focus.get("priority_modalities", [])
    if isinstance(priority_modalities, list) and priority_modalities:
        for row in priority_modalities:
            if not isinstance(row, dict):
                continue
            lines.append(
                "- `%s` pending_slots=%s"
                % (
                    str(row.get("modality", "")),
                    str(_to_int(row.get("pending_slot_count", 0), default=0)),
                )
            )
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Recommended Submission Actions",
        ]
    )
    recommended_actions = execution_focus.get("recommended_submission_actions", [])
    if isinstance(recommended_actions, list) and recommended_actions:
        for row in recommended_actions:
            if not isinstance(row, dict):
                continue
            lines.append(
                "- action=%s slot=%s modality=%s reason=%s"
                % (
                    str(row.get("backfill_action_id", "")),
                    str(_to_int(row.get("backfill_slot_index", 0), default=0)),
                    str(row.get("required_modality", "")),
                    str(row.get("reason", "")),
                )
            )
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Net New Loop IDs",
        ]
    )
    net_new_loop_ids = snapshot.get("net_new_launch_gate_eligible_real_loop_ids", [])
    if isinstance(net_new_loop_ids, list) and net_new_loop_ids:
        for loop_id in net_new_loop_ids:
            lines.append("- `%s`" % str(loop_id))
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    collection_report_path = Path(str(args.collection_report).strip()).resolve()
    backfill_execution_report_path = Path(str(args.backfill_execution_report).strip()).resolve()
    backfill_submission_consumption_report_path = Path(
        str(args.backfill_submission_consumption_report).strip()
    ).resolve()
    output_path = None if str(args.output).strip() == "-" else Path(str(args.output).strip()).resolve()
    summary_path = None if str(args.summary_output).strip() == "-" else Path(str(args.summary_output).strip()).resolve()
    owner = str(args.owner).strip() or "controlled-beta-ops"

    try:
        if not collection_report_path.is_file():
            raise ValueError("Collection report path does not exist: %s" % collection_report_path)
        if not backfill_execution_report_path.is_file():
            raise ValueError("Backfill execution report path does not exist: %s" % backfill_execution_report_path)
        if not backfill_submission_consumption_report_path.is_file():
            raise ValueError(
                "Backfill submission consumption report path does not exist: %s"
                % backfill_submission_consumption_report_path
            )

        collection_report = _read_json(collection_report_path)
        backfill_execution_report = _read_json(backfill_execution_report_path)
        backfill_submission_consumption_report = _read_json(backfill_submission_consumption_report_path)

        previous_throughput_report_path: Path | None = None
        previous_throughput_report: dict[str, Any] | None = None
        previous_arg_value = str(args.previous_throughput_report).strip()
        if previous_arg_value:
            previous_throughput_report_path = Path(previous_arg_value).resolve()
        elif output_path is not None:
            previous_throughput_report_path = output_path
        if previous_throughput_report_path is not None and previous_throughput_report_path.is_file():
            previous_throughput_report = _read_json(previous_throughput_report_path)

        report = _build_report(
            owner=owner,
            collection_report=collection_report,
            backfill_execution_report=backfill_execution_report,
            backfill_submission_consumption_report=backfill_submission_consumption_report,
            collection_report_path=collection_report_path,
            backfill_execution_report_path=backfill_execution_report_path,
            backfill_submission_consumption_report_path=backfill_submission_consumption_report_path,
            previous_throughput_report=previous_throughput_report,
            previous_throughput_report_path=previous_throughput_report_path
            if previous_throughput_report is not None
            else None,
        )
        summary = _render_summary(report)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print("Real trial submission throughput diagnostics failed: %s" % exc, file=sys.stderr)
        return 2

    if output_path is not None:
        _write_text(output_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print("Real trial submission throughput report written: %s" % output_path)
    if summary_path is not None:
        _write_text(summary_path, summary)
        print("Real trial submission throughput summary written: %s" % summary_path)

    snapshot = report.get("snapshot", {})
    if not isinstance(snapshot, dict):
        snapshot = {}
    delta = snapshot.get("delta", {})
    if not isinstance(delta, dict):
        delta = {}
    current = snapshot.get("current", {})
    if not isinstance(current, dict):
        current = {}
    print(
        "Real trial submission throughput status=%s net_new_loops=%s current_loops=%s missing_loops=%s"
        % (
            str(report.get("throughput_status", "unknown")),
            _to_int(delta.get("net_new_launch_gate_eligible_real_loop_count", 0)),
            _to_int(current.get("launch_gate_eligible_complete_loop_count", 0)),
            _to_int(current.get("missing_complete_loops_to_threshold", 0)),
        )
    )
    if args.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    if bool(args.fail_on_stalled) and str(report.get("throughput_status", "")).strip().upper() == "THROUGHPUT_STALLED":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
