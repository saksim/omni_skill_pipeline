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
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-loop-backfill-plan.json"
)
DEFAULT_COLLECTION_REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-loop-collection-report.json"
)
DEFAULT_OUTPUT_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-execution-report.json"
)
DEFAULT_SUMMARY_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-execution-summary.md"
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Execute GL-21 real-loop backfill plan against current GL-12 collection coverage "
            "and emit machine-readable progress."
        )
    )
    parser.add_argument("--backfill-plan", default=str(DEFAULT_BACKFILL_PLAN_PATH))
    parser.add_argument("--collection-report", default=str(DEFAULT_COLLECTION_REPORT_PATH))
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help='Backfill execution report output path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--summary-output",
        default=str(DEFAULT_SUMMARY_PATH),
        help='Backfill execution summary output path. Use "-" to skip writing file.',
    )
    parser.add_argument("--print-json", action="store_true")
    parser.add_argument(
        "--fail-on-incomplete",
        action="store_true",
        help="Exit with code 1 when backfill slots are still pending.",
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


def _normalize_count_map(raw: Any) -> dict[str, int]:
    if not isinstance(raw, dict):
        return {}
    normalized: dict[str, int] = {}
    for key, value in raw.items():
        modality = str(key).strip().lower()
        if not modality:
            continue
        try:
            count = int(value or 0)
        except (TypeError, ValueError):
            count = 0
        normalized[modality] = max(0, count)
    return normalized


def _build_execution_report(
    *,
    backfill_plan: dict[str, Any],
    collection_report: dict[str, Any],
    backfill_plan_path: Path,
    collection_report_path: Path,
) -> dict[str, Any]:
    thresholds = backfill_plan.get("thresholds", {})
    if not isinstance(thresholds, dict):
        thresholds = {}
    current_coverage = backfill_plan.get("current_coverage", {})
    if not isinstance(current_coverage, dict):
        current_coverage = {}
    plan_slots = backfill_plan.get("recommended_backfill_slots", [])
    if not isinstance(plan_slots, list):
        plan_slots = []

    collection_alignment = collection_report.get("launch_gate_alignment", {})
    if not isinstance(collection_alignment, dict):
        collection_alignment = {}

    target_launch_modalities_raw = thresholds.get("target_launch_modalities", [])
    target_launch_modalities = []
    if isinstance(target_launch_modalities_raw, list):
        for item in target_launch_modalities_raw:
            token = str(item).strip().lower()
            if token:
                target_launch_modalities.append(token)
    if not target_launch_modalities:
        alignment_targets = collection_alignment.get("target_launch_modalities", [])
        if isinstance(alignment_targets, list):
            target_launch_modalities = [
                str(item).strip().lower() for item in alignment_targets if str(item).strip()
            ]

    baseline_counts = _normalize_count_map(current_coverage.get("target_launch_modality_loop_counts", {}))
    current_counts = _normalize_count_map(collection_alignment.get("target_launch_modality_loop_counts", {}))

    modality_keys = set(target_launch_modalities)
    modality_keys.update(baseline_counts.keys())
    modality_keys.update(current_counts.keys())
    ordered_modalities = sorted(modality_keys)

    gained_counts: dict[str, int] = {}
    remaining_gained_counts: dict[str, int] = {}
    for modality in ordered_modalities:
        baseline = baseline_counts.get(modality, 0)
        current = current_counts.get(modality, 0)
        gained = max(0, current - baseline)
        gained_counts[modality] = gained
        remaining_gained_counts[modality] = gained

    slot_execution_records: list[dict[str, Any]] = []
    submission_linked_slot_indices: set[int] = set()
    submission_linked_action_ids: set[str] = set()
    submission_linkage_records: list[dict[str, Any]] = []
    unmatched_submission_linkages: list[dict[str, Any]] = []
    collected_real_loops = collection_report.get("collected_real_launch_gate_eligible_loops", [])
    if isinstance(collected_real_loops, list):
        for raw_loop in collected_real_loops:
            if not isinstance(raw_loop, dict):
                continue
            raw_slot_index = raw_loop.get("backfill_slot_index")
            try:
                slot_index = int(raw_slot_index or 0)
            except (TypeError, ValueError):
                slot_index = 0
            action_id = str(raw_loop.get("backfill_action_id", "")).strip()
            if slot_index > 0:
                submission_linked_slot_indices.add(slot_index)
            if action_id:
                submission_linked_action_ids.add(action_id)

    fulfilled_slot_count = 0
    for index, raw_slot in enumerate(plan_slots, start=1):
        if not isinstance(raw_slot, dict):
            continue
        slot_index = int(raw_slot.get("slot_index", index) or index)
        required_modality = str(raw_slot.get("required_modality", "")).strip().lower()
        reason = str(raw_slot.get("reason", "")).strip()
        expected_action_id = "gl23-slot-%03d-%s" % (slot_index, required_modality or "unknown")
        available_delta = int(remaining_gained_counts.get(required_modality, 0) or 0)
        linked_by_slot = slot_index in submission_linked_slot_indices
        linked_by_action = expected_action_id in submission_linked_action_ids
        submission_linked = linked_by_slot or linked_by_action
        if required_modality and available_delta > 0:
            execution_status = "fulfilled"
            remaining_gained_counts[required_modality] = available_delta - 1
            consumed_delta = 1
            fulfilled_slot_count += 1
        else:
            execution_status = "pending"
            consumed_delta = 0
        if submission_linked:
            linkage_resolution = "slot_index_and_action_id" if linked_by_slot and linked_by_action else (
                "slot_index_only" if linked_by_slot else "action_id_only"
            )
            submission_linkage_records.append(
                {
                    "slot_index": slot_index,
                    "required_modality": required_modality,
                    "expected_action_id": expected_action_id,
                    "linked_by_slot_index": linked_by_slot,
                    "linked_by_action_id": linked_by_action,
                    "linkage_resolution": linkage_resolution,
                }
            )
        slot_execution_records.append(
            {
                "slot_index": slot_index,
                "required_modality": required_modality,
                "reason": reason,
                "expected_action_id": expected_action_id,
                "execution_status": execution_status,
                "available_modality_delta_before_assignment": available_delta,
                "consumed_modality_delta": consumed_delta,
                "submission_linked": submission_linked,
                "submission_linkage_resolution": (
                    "slot_index_and_action_id"
                    if linked_by_slot and linked_by_action
                    else ("slot_index_only" if linked_by_slot else ("action_id_only" if linked_by_action else "none"))
                ),
            }
        )
    known_slot_indices = {int(item.get("slot_index", 0) or 0) for item in slot_execution_records}
    known_action_ids = {str(item.get("expected_action_id", "")).strip() for item in slot_execution_records}
    if isinstance(collected_real_loops, list):
        for raw_loop in collected_real_loops:
            if not isinstance(raw_loop, dict):
                continue
            raw_slot_index = raw_loop.get("backfill_slot_index")
            try:
                slot_index = int(raw_slot_index or 0)
            except (TypeError, ValueError):
                slot_index = 0
            action_id = str(raw_loop.get("backfill_action_id", "")).strip()
            if slot_index > 0 and slot_index not in known_slot_indices:
                unmatched_submission_linkages.append(
                    {
                        "loop_id": str(raw_loop.get("loop_id", "")),
                        "reason": "slot_index_not_in_backfill_plan",
                        "backfill_slot_index": slot_index,
                        "backfill_action_id": action_id,
                    }
                )
            if action_id and action_id not in known_action_ids:
                unmatched_submission_linkages.append(
                    {
                        "loop_id": str(raw_loop.get("loop_id", "")),
                        "reason": "action_id_not_in_backfill_plan",
                        "backfill_slot_index": slot_index if slot_index > 0 else None,
                        "backfill_action_id": action_id,
                    }
                )

    total_slots = len(slot_execution_records)
    remaining_slot_count = max(0, total_slots - fulfilled_slot_count)
    submission_backed_fulfilled_slot_count = 0
    fulfilled_without_submission_linkage_count = 0
    submission_linked_without_modality_delta_count = 0
    for record in slot_execution_records:
        if not isinstance(record, dict):
            continue
        linked = bool(record.get("submission_linked"))
        fulfilled = str(record.get("execution_status", "")).strip().lower() == "fulfilled"
        if linked:
            submission_backed_fulfilled_slot_count += 1
        if fulfilled and not linked:
            fulfilled_without_submission_linkage_count += 1
        if linked and not fulfilled:
            submission_linked_without_modality_delta_count += 1
    submission_backed_remaining_slot_count = max(0, total_slots - submission_backed_fulfilled_slot_count)
    plan_status = str(backfill_plan.get("plan_status", "ACTION_REQUIRED")).strip().upper() or "ACTION_REQUIRED"
    if plan_status == "ALREADY_THRESHOLD_READY" or total_slots == 0:
        execution_status = "NO_ACTION_REQUIRED"
    elif remaining_slot_count == 0:
        execution_status = "BACKFILL_COMPLETE"
    else:
        execution_status = "BACKFILL_IN_PROGRESS"
    if plan_status == "ALREADY_THRESHOLD_READY" or total_slots == 0:
        submission_backed_execution_status = "NO_ACTION_REQUIRED"
    elif submission_backed_remaining_slot_count == 0:
        submission_backed_execution_status = "SUBMISSION_BACKED_COMPLETE"
    else:
        submission_backed_execution_status = "SUBMISSION_BACKED_IN_PROGRESS"

    return {
        "schema_version": "real_trial_backfill_execution.v1",
        "generated_at_utc": _utc_now_iso(),
        "input_paths": {
            "backfill_plan": str(backfill_plan_path),
            "collection_report": str(collection_report_path),
        },
        "plan_status": plan_status,
        "execution_status": execution_status,
        "target_launch_modalities": target_launch_modalities,
        "slot_counts": {
            "total_slots": total_slots,
            "fulfilled_slot_count": fulfilled_slot_count,
            "remaining_slot_count": remaining_slot_count,
        },
        "submission_backed_execution_status": submission_backed_execution_status,
        "submission_backed_slot_counts": {
            "total_slots": total_slots,
            "submission_backed_fulfilled_slot_count": submission_backed_fulfilled_slot_count,
            "submission_backed_remaining_slot_count": submission_backed_remaining_slot_count,
            "fulfilled_without_submission_linkage_count": fulfilled_without_submission_linkage_count,
            "submission_linked_without_modality_delta_count": submission_linked_without_modality_delta_count,
        },
        "submission_linkage_counts": {
            "slot_linked_count": len({item["slot_index"] for item in submission_linkage_records}),
            "action_linked_count": len(
                {item["expected_action_id"] for item in submission_linkage_records if str(item["expected_action_id"]).strip()}
            ),
            "submission_linked_slot_count": len(submission_linkage_records),
            "unmatched_submission_linkage_count": len(unmatched_submission_linkages),
        },
        "coverage_delta": {
            "baseline_target_launch_modality_loop_counts": baseline_counts,
            "current_target_launch_modality_loop_counts": current_counts,
            "gained_target_launch_modality_loop_counts": gained_counts,
            "unconsumed_gained_target_launch_modality_loop_counts": remaining_gained_counts,
        },
        "slot_execution_records": slot_execution_records,
        "submission_linkage_records": submission_linkage_records,
        "unmatched_submission_linkages": unmatched_submission_linkages,
        "launch_gate_alignment_snapshot": {
            "program_status": str(collection_alignment.get("program_status", "unknown")),
            "launch_gate_eligible_complete_loop_count": int(
                collection_alignment.get("launch_gate_eligible_complete_loop_count", 0) or 0
            ),
            "launch_gate_eligible_modality_count": int(
                collection_alignment.get("launch_gate_eligible_modality_count", 0) or 0
            ),
            "missing_complete_loops_to_threshold": int(
                collection_alignment.get("missing_complete_loops_to_threshold", 0) or 0
            ),
            "missing_modalities_to_threshold": int(
                collection_alignment.get("missing_modalities_to_threshold", 0) or 0
            ),
            "blockers": collection_alignment.get("blockers", []),
        },
    }


def _render_summary(report: dict[str, Any]) -> str:
    slot_counts = report.get("slot_counts", {})
    if not isinstance(slot_counts, dict):
        slot_counts = {}
    submission_backed_slot_counts = report.get("submission_backed_slot_counts", {})
    if not isinstance(submission_backed_slot_counts, dict):
        submission_backed_slot_counts = {}
    alignment = report.get("launch_gate_alignment_snapshot", {})
    if not isinstance(alignment, dict):
        alignment = {}
    coverage_delta = report.get("coverage_delta", {})
    if not isinstance(coverage_delta, dict):
        coverage_delta = {}
    submission_linkage_counts = report.get("submission_linkage_counts", {})
    if not isinstance(submission_linkage_counts, dict):
        submission_linkage_counts = {}
    lines = [
        "# Real Trial Backfill Execution Summary",
        "",
        "- Plan status: `%s`" % str(report.get("plan_status", "unknown")),
        "- Execution status: `%s`" % str(report.get("execution_status", "unknown")),
        "- Submission-backed execution status: `%s`"
        % str(report.get("submission_backed_execution_status", "unknown")),
        "- Total slots: `%s`" % str(slot_counts.get("total_slots", 0)),
        "- Fulfilled slots: `%s`" % str(slot_counts.get("fulfilled_slot_count", 0)),
        "- Remaining slots: `%s`" % str(slot_counts.get("remaining_slot_count", 0)),
        "- Submission-backed fulfilled slots: `%s`"
        % str(submission_backed_slot_counts.get("submission_backed_fulfilled_slot_count", 0)),
        "- Submission-backed remaining slots: `%s`"
        % str(submission_backed_slot_counts.get("submission_backed_remaining_slot_count", 0)),
        "- Fulfilled slots without submission linkage: `%s`"
        % str(submission_backed_slot_counts.get("fulfilled_without_submission_linkage_count", 0)),
        "- Submission-linked slots without modality delta: `%s`"
        % str(submission_backed_slot_counts.get("submission_linked_without_modality_delta_count", 0)),
        "- Gained target modality loop counts: `%s`"
        % str(coverage_delta.get("gained_target_launch_modality_loop_counts", {})),
        "- Submission-linked slots: `%s`"
        % str(submission_linkage_counts.get("submission_linked_slot_count", 0)),
        "- Submission linkages by slot index: `%s`" % str(submission_linkage_counts.get("slot_linked_count", 0)),
        "- Submission linkages by action id: `%s`" % str(submission_linkage_counts.get("action_linked_count", 0)),
        "- Unmatched submission linkages: `%s`"
        % str(submission_linkage_counts.get("unmatched_submission_linkage_count", 0)),
        "- Collection program status: `%s`" % str(alignment.get("program_status", "unknown")),
        "- Launch-gate missing loops: `%s`" % str(alignment.get("missing_complete_loops_to_threshold", 0)),
        "- Launch-gate missing modalities: `%s`" % str(alignment.get("missing_modalities_to_threshold", 0)),
        "",
        "## Blockers",
    ]
    blockers = alignment.get("blockers", [])
    if isinstance(blockers, list) and blockers:
        for blocker in blockers:
            lines.append("- `%s`" % str(blocker))
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    backfill_plan_path = Path(str(args.backfill_plan).strip()).resolve()
    collection_report_path = Path(str(args.collection_report).strip()).resolve()
    output_path = None if str(args.output).strip() == "-" else Path(str(args.output).strip()).resolve()
    summary_path = None if str(args.summary_output).strip() == "-" else Path(str(args.summary_output).strip()).resolve()

    try:
        if not backfill_plan_path.is_file():
            raise ValueError("Backfill plan path does not exist: %s" % backfill_plan_path)
        if not collection_report_path.is_file():
            raise ValueError("Collection report path does not exist: %s" % collection_report_path)
        backfill_plan = _read_json(backfill_plan_path)
        collection_report = _read_json(collection_report_path)
        report = _build_execution_report(
            backfill_plan=backfill_plan,
            collection_report=collection_report,
            backfill_plan_path=backfill_plan_path,
            collection_report_path=collection_report_path,
        )
        summary = _render_summary(report)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print("Real trial backfill execution failed: %s" % exc, file=sys.stderr)
        return 2

    if output_path is not None:
        _write_text(output_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print("Real trial backfill execution report written: %s" % output_path)
    if summary_path is not None:
        _write_text(summary_path, summary)
        print("Real trial backfill execution summary written: %s" % summary_path)

    slot_counts = report.get("slot_counts", {})
    print(
        "Real trial backfill execution status=%s fulfilled_slots=%s/%s"
        % (
            str(report.get("execution_status", "unknown")),
            int(slot_counts.get("fulfilled_slot_count", 0) or 0),
            int(slot_counts.get("total_slots", 0) or 0),
        )
    )
    if args.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    if bool(args.fail_on_incomplete) and str(report.get("execution_status", "")).strip().upper() == "BACKFILL_IN_PROGRESS":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
