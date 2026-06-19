from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BACKFILL_PLAN_PATH = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-loop-backfill-plan.json"
)
DEFAULT_BACKFILL_EXECUTION_REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-execution-report.json"
)
DEFAULT_OUTPUT_PATH = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-intake-actions-report.json"
)
DEFAULT_SUMMARY_PATH = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-intake-actions-summary.md"
)

REQUIRED_CLOSURE_FIELDS = [
    "loop_id",
    "modality",
    "evidence_origin",
    "launch_gate_eligible",
    "source_system",
    "source_reference",
    "collected_at_utc",
    "review_task_id",
    "reviewed_by",
    "reviewed_at_utc",
]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate GL-23 operator-facing intake actions from GL-21 backfill slots "
            "and GL-22 slot execution progress."
        )
    )
    parser.add_argument("--backfill-plan", default=str(DEFAULT_BACKFILL_PLAN_PATH))
    parser.add_argument("--backfill-execution-report", default=str(DEFAULT_BACKFILL_EXECUTION_REPORT_PATH))
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help='Intake action report output path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--summary-output",
        default=str(DEFAULT_SUMMARY_PATH),
        help='Intake action summary output path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--owner",
        default="controlled-beta-ops",
        help="Operator owner tag written into generated actions.",
    )
    parser.add_argument(
        "--fail-on-pending",
        action="store_true",
        help="Exit with code 1 when any intake action is still pending.",
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


def _build_action_title(required_modality: str, reason: str) -> str:
    modality = required_modality or "unknown"
    if reason == "missing_target_launch_modality":
        return "Collect real %s loop for missing modality coverage" % modality
    return "Collect real %s loop for remaining volume threshold" % modality


def _build_execution_map(execution_records: list[Any]) -> dict[int, dict[str, Any]]:
    mapped: dict[int, dict[str, Any]] = {}
    for index, raw in enumerate(execution_records, start=1):
        if not isinstance(raw, dict):
            continue
        slot_index = _to_int(raw.get("slot_index"), default=index)
        if slot_index <= 0:
            slot_index = index
        mapped[slot_index] = raw
    return mapped


def _build_intake_report(
    *,
    backfill_plan: dict[str, Any],
    backfill_execution_report: dict[str, Any],
    backfill_plan_path: Path,
    backfill_execution_report_path: Path,
    owner: str,
) -> dict[str, Any]:
    thresholds = backfill_plan.get("thresholds", {})
    if not isinstance(thresholds, dict):
        thresholds = {}
    plan_slots = backfill_plan.get("recommended_backfill_slots", [])
    if not isinstance(plan_slots, list):
        plan_slots = []
    execution_records = backfill_execution_report.get("slot_execution_records", [])
    if not isinstance(execution_records, list):
        execution_records = []
    execution_slot_map = _build_execution_map(execution_records)

    actions: list[dict[str, Any]] = []
    pending_actions: list[dict[str, Any]] = []
    closed_action_count = 0
    for position, raw_slot in enumerate(plan_slots, start=1):
        if not isinstance(raw_slot, dict):
            continue
        slot_index = _to_int(raw_slot.get("slot_index"), default=position)
        if slot_index <= 0:
            slot_index = position
        required_modality = str(raw_slot.get("required_modality", "")).strip().lower()
        reason = str(raw_slot.get("reason", "")).strip() or "unknown_reason"
        execution_record = execution_slot_map.get(slot_index, {})
        if not isinstance(execution_record, dict):
            execution_record = {}
        execution_status = str(execution_record.get("execution_status", "pending")).strip().lower() or "pending"
        action_status = "closed" if execution_status == "fulfilled" else "pending"
        action_id = "gl23-slot-%03d-%s" % (slot_index, required_modality or "unknown")
        action = {
            "action_id": action_id,
            "slot_index": slot_index,
            "required_modality": required_modality,
            "reason": reason,
            "action_status": action_status,
            "execution_status": execution_status,
            "owner": owner,
            "title": _build_action_title(required_modality, reason),
            "operator_task": "Collect one launch-gate-eligible real %s loop and record full review trace."
            % (required_modality or "unknown"),
            "closure_evidence_requirements": {
                "required_loop_manifest_fields": REQUIRED_CLOSURE_FIELDS,
                "required_field_values": {
                    "evidence_origin": "real",
                    "launch_gate_eligible": True,
                    "status": "complete",
                    "modality": required_modality,
                },
                "validation_note": (
                    "Closure must appear in the next GL-12 collection report and GL-22 execution report "
                    "without relaxing launch-gate policy."
                ),
            },
            "closure_evidence_snapshot": {
                "available_modality_delta_before_assignment": _to_int(
                    execution_record.get("available_modality_delta_before_assignment"),
                    default=0,
                ),
                "consumed_modality_delta": _to_int(execution_record.get("consumed_modality_delta"), default=0),
                "linked_execution_record": execution_record,
            },
        }
        actions.append(action)
        if action_status == "closed":
            closed_action_count += 1
        else:
            pending_actions.append(action)

    total_actions = len(actions)
    pending_action_count = len(pending_actions)
    if total_actions == 0:
        intake_status = "NO_ACTION_REQUIRED"
    elif pending_action_count == 0:
        intake_status = "ALL_ACTIONS_CLOSED"
    else:
        intake_status = "ACTIONS_PENDING"

    slot_counts = backfill_execution_report.get("slot_counts", {})
    if not isinstance(slot_counts, dict):
        slot_counts = {}
    launch_gap_snapshot = backfill_execution_report.get("launch_gate_alignment_snapshot", {})
    if not isinstance(launch_gap_snapshot, dict):
        launch_gap_snapshot = {}

    return {
        "schema_version": "real_trial_backfill_intake_actions.v1",
        "generated_at_utc": _utc_now_iso(),
        "input_paths": {
            "backfill_plan": str(backfill_plan_path),
            "backfill_execution_report": str(backfill_execution_report_path),
        },
        "intake_status": intake_status,
        "thresholds": {
            "minimum_complete_loops": _to_int(thresholds.get("minimum_complete_loops"), default=10),
            "minimum_modalities": _to_int(thresholds.get("minimum_modalities"), default=4),
            "target_launch_modalities": thresholds.get("target_launch_modalities", []),
        },
        "action_counts": {
            "total_actions": total_actions,
            "pending_action_count": pending_action_count,
            "closed_action_count": closed_action_count,
        },
        "slot_progress_snapshot": {
            "execution_status": str(backfill_execution_report.get("execution_status", "unknown")),
            "total_slots": _to_int(slot_counts.get("total_slots"), default=0),
            "fulfilled_slot_count": _to_int(slot_counts.get("fulfilled_slot_count"), default=0),
            "remaining_slot_count": _to_int(slot_counts.get("remaining_slot_count"), default=0),
        },
        "launch_gap_snapshot": {
            "program_status": str(launch_gap_snapshot.get("program_status", "unknown")),
            "missing_complete_loops_to_threshold": _to_int(
                launch_gap_snapshot.get("missing_complete_loops_to_threshold"), default=0
            ),
            "missing_modalities_to_threshold": _to_int(
                launch_gap_snapshot.get("missing_modalities_to_threshold"), default=0
            ),
            "blockers": launch_gap_snapshot.get("blockers", []),
        },
        "actions": actions,
        "pending_actions": [
            {
                "action_id": item.get("action_id"),
                "slot_index": item.get("slot_index"),
                "required_modality": item.get("required_modality"),
                "reason": item.get("reason"),
                "owner": item.get("owner"),
            }
            for item in pending_actions
        ],
    }


def _render_summary(report: dict[str, Any]) -> str:
    action_counts = report.get("action_counts", {})
    if not isinstance(action_counts, dict):
        action_counts = {}
    launch_gap = report.get("launch_gap_snapshot", {})
    if not isinstance(launch_gap, dict):
        launch_gap = {}
    lines = [
        "# Real Trial Backfill Intake Actions Summary",
        "",
        "- Intake status: `%s`" % str(report.get("intake_status", "unknown")),
        "- Total actions: `%s`" % str(action_counts.get("total_actions", 0)),
        "- Pending actions: `%s`" % str(action_counts.get("pending_action_count", 0)),
        "- Closed actions: `%s`" % str(action_counts.get("closed_action_count", 0)),
        "- Launch-gap missing loops: `%s`" % str(launch_gap.get("missing_complete_loops_to_threshold", 0)),
        "- Launch-gap missing modalities: `%s`" % str(launch_gap.get("missing_modalities_to_threshold", 0)),
        "",
        "## Pending Actions",
    ]
    pending_actions = report.get("pending_actions", [])
    if isinstance(pending_actions, list) and pending_actions:
        for action in pending_actions:
            if not isinstance(action, dict):
                continue
            lines.append(
                "- `%s` slot=%s modality=%s reason=%s owner=%s"
                % (
                    str(action.get("action_id", "")),
                    str(action.get("slot_index", "")),
                    str(action.get("required_modality", "")),
                    str(action.get("reason", "")),
                    str(action.get("owner", "")),
                )
            )
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    backfill_plan_path = Path(str(args.backfill_plan).strip()).resolve()
    backfill_execution_report_path = Path(str(args.backfill_execution_report).strip()).resolve()
    output_path = None if str(args.output).strip() == "-" else Path(str(args.output).strip()).resolve()
    summary_path = None if str(args.summary_output).strip() == "-" else Path(str(args.summary_output).strip()).resolve()
    owner = str(args.owner).strip() or "controlled-beta-ops"

    try:
        if not backfill_plan_path.is_file():
            raise ValueError("Backfill plan path does not exist: %s" % backfill_plan_path)
        if not backfill_execution_report_path.is_file():
            raise ValueError("Backfill execution report path does not exist: %s" % backfill_execution_report_path)
        backfill_plan = _read_json(backfill_plan_path)
        backfill_execution_report = _read_json(backfill_execution_report_path)
        report = _build_intake_report(
            backfill_plan=backfill_plan,
            backfill_execution_report=backfill_execution_report,
            backfill_plan_path=backfill_plan_path,
            backfill_execution_report_path=backfill_execution_report_path,
            owner=owner,
        )
        summary = _render_summary(report)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print("Real trial backfill intake action generation failed: %s" % exc, file=sys.stderr)
        return 2

    if output_path is not None:
        _write_text(output_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print("Real trial backfill intake actions report written: %s" % output_path)
    if summary_path is not None:
        _write_text(summary_path, summary)
        print("Real trial backfill intake actions summary written: %s" % summary_path)

    action_counts = report.get("action_counts", {})
    if not isinstance(action_counts, dict):
        action_counts = {}
    print(
        "Real trial backfill intake actions status=%s pending=%s/%s"
        % (
            str(report.get("intake_status", "unknown")),
            _to_int(action_counts.get("pending_action_count"), default=0),
            _to_int(action_counts.get("total_actions"), default=0),
        )
    )
    if args.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    if bool(args.fail_on_pending) and _to_int(action_counts.get("pending_action_count"), default=0) > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
