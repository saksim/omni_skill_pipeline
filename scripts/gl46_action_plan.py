from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_THROUGHPUT_REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-throughput-report.json"
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
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-report.json"
)
DEFAULT_SUMMARY_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-summary.md"
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


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate GL-46 operator action plans from GL-45 escalation throughput diagnostics "
            "and current launch-gate loop coverage snapshots."
        )
    )
    parser.add_argument(
        "--submission-queue-followup-resolution-escalation-throughput-report",
        default=str(DEFAULT_THROUGHPUT_REPORT_PATH),
    )
    parser.add_argument("--collection-report", default=str(DEFAULT_COLLECTION_REPORT_PATH))
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help='GL-46 action-plan report output path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--summary-output",
        default=str(DEFAULT_SUMMARY_PATH),
        help='GL-46 action-plan summary output path. Use "-" to skip writing file.',
    )
    parser.add_argument("--owner", default="controlled-beta-ops")
    parser.add_argument(
        "--fail-on-open",
        action="store_true",
        help="Exit with code 1 when GL-46 action plan still has open actions.",
    )
    parser.add_argument("--print-json", action="store_true")
    return parser.parse_args()


def _build_action_plan_rows(
    *,
    throughput_report: dict[str, Any],
    collection_report: dict[str, Any],
    owner: str,
) -> tuple[list[dict[str, Any]], list[str], dict[str, int], str]:
    throughput_status = str(
        throughput_report.get("followup_resolution_escalation_throughput_status", "unknown")
    ).strip()
    warning_codes = throughput_report.get("warning_codes", [])
    if not isinstance(warning_codes, list):
        warning_codes = []

    delta = throughput_report.get("snapshot_delta", {})
    if not isinstance(delta, dict):
        delta = {}

    ack_snapshot = throughput_report.get("acknowledgement_snapshot", {})
    if not isinstance(ack_snapshot, dict):
        ack_snapshot = {}

    collection_snapshot = throughput_report.get("collection_snapshot", {})
    if not isinstance(collection_snapshot, dict):
        collection_snapshot = {}

    alignment = collection_report.get("launch_gate_alignment", {})
    if not isinstance(alignment, dict):
        alignment = {}

    recommended_backfill_slots = alignment.get("recommended_backfill_slots", [])
    if not isinstance(recommended_backfill_slots, list):
        recommended_backfill_slots = []

    unresolved_ack_loop_ids = throughput_report.get("unresolved_acknowledged_submission_loop_ids", [])
    if not isinstance(unresolved_ack_loop_ids, list):
        unresolved_ack_loop_ids = []

    open_actions: list[dict[str, Any]] = []

    for loop_id in unresolved_ack_loop_ids:
        loop_value = str(loop_id).strip()
        if not loop_value:
            continue
        open_actions.append(
            {
                "action_id": "gl46-unmapped-%s" % loop_value,
                "action_type": "resolve_acknowledged_loop_mapping_gap",
                "action_status": "open",
                "owner": owner,
                "required_modality": "",
                "linked_submission_loop_id": loop_value,
                "backfill_slot_index": 0,
                "reason": "resolved_acknowledgement_not_visible_in_launch_gate_eligible_loops",
                "source": "gl45.unresolved_acknowledged_submission_loop_ids",
            }
        )

    missing_loops = _to_int(collection_snapshot.get("missing_complete_loops_to_threshold", 0), default=0)
    missing_modalities = _to_int(collection_snapshot.get("missing_modalities_to_threshold", 0), default=0)
    slot_index = 1
    for raw_slot in recommended_backfill_slots:
        if not isinstance(raw_slot, dict):
            continue
        required_modality = str(raw_slot.get("required_modality", "")).strip().lower()
        reason = str(raw_slot.get("reason", "recommended_backfill_slot")).strip() or "recommended_backfill_slot"
        slot_value = _to_int(raw_slot.get("slot_index", 0), default=slot_index)
        if slot_value <= 0:
            slot_value = slot_index
        open_actions.append(
            {
                "action_id": "gl46-slot-%03d-%s" % (slot_value, required_modality or "unknown"),
                "action_type": "collect_launch_gate_eligible_real_loop",
                "action_status": "open",
                "owner": owner,
                "required_modality": required_modality,
                "linked_submission_loop_id": "",
                "backfill_slot_index": slot_value,
                "reason": reason,
                "source": "gl12.recommended_backfill_slots",
            }
        )
        slot_index = max(slot_index, slot_value + 1)

    if not open_actions and throughput_status == "ESCALATION_ACK_THROUGHPUT_THRESHOLD_MET":
        action_plan_status = "ACTION_PLAN_NOT_REQUIRED"
    elif not open_actions:
        action_plan_status = "ACTION_PLAN_REBUILD_REQUIRED"
    else:
        action_plan_status = "ACTION_PLAN_OPEN"

    counts = {
        "total_action_count": len(open_actions),
        "open_action_count": len(open_actions),
        "closed_action_count": 0,
        "unresolved_ack_mapping_action_count": sum(
            1 for item in open_actions if str(item.get("action_type", "")) == "resolve_acknowledged_loop_mapping_gap"
        ),
        "recommended_backfill_slot_action_count": sum(
            1 for item in open_actions if str(item.get("action_type", "")) == "collect_launch_gate_eligible_real_loop"
        ),
        "missing_complete_loops_to_threshold": missing_loops,
        "missing_modalities_to_threshold": missing_modalities,
        "net_new_launch_gate_eligible_loop_count_gl45": _to_int(
            delta.get("net_new_launch_gate_eligible_loop_count", 0),
            default=0,
        ),
        "net_new_resolved_acknowledged_item_count_gl45": _to_int(
            delta.get("net_new_resolved_acknowledged_item_count", 0),
            default=0,
        ),
        "open_acknowledgement_item_count_gl44": _to_int(ack_snapshot.get("open_item_count", 0), default=0),
    }

    warning_set = list(warning_codes)
    if action_plan_status == "ACTION_PLAN_OPEN" and counts["open_action_count"] > 0:
        warning_set.append("open_followup_resolution_escalation_action_plan_items_present")
    if action_plan_status == "ACTION_PLAN_REBUILD_REQUIRED":
        warning_set.append("followup_resolution_escalation_action_plan_rebuild_required")

    return open_actions, _unique_preserve_order(warning_set), counts, action_plan_status


def _build_report(
    *,
    throughput_report: dict[str, Any],
    throughput_report_path: Path,
    collection_report: dict[str, Any],
    collection_report_path: Path,
    owner: str,
) -> dict[str, Any]:
    action_rows, warning_codes, counts, action_plan_status = _build_action_plan_rows(
        throughput_report=throughput_report,
        collection_report=collection_report,
        owner=owner,
    )
    return {
        "schema_version": "real_trial_submission_queue_followup_resolution_escalation_action_plan.v1",
        "generated_at_utc": _utc_now_iso(),
        "owner": owner,
        "input_paths": {
            "submission_queue_followup_resolution_escalation_throughput_report": str(
                throughput_report_path
            ),
            "collection_report": str(collection_report_path),
        },
        "followup_resolution_escalation_throughput_status_gl45": str(
            throughput_report.get("followup_resolution_escalation_throughput_status", "unknown")
        ),
        "followup_resolution_escalation_action_plan_status": action_plan_status,
        "warning_codes": warning_codes,
        "followup_resolution_escalation_action_plan_counts": counts,
        "followup_resolution_escalation_action_plan_rows": action_rows,
    }


def _render_summary(report: dict[str, Any]) -> str:
    counts = report.get("followup_resolution_escalation_action_plan_counts", {})
    if not isinstance(counts, dict):
        counts = {}
    warning_codes = report.get("warning_codes", [])
    if not isinstance(warning_codes, list):
        warning_codes = []
    rows = report.get("followup_resolution_escalation_action_plan_rows", [])
    if not isinstance(rows, list):
        rows = []

    lines = [
        "# Real Trial Submission Queue Follow-Up Resolution Escalation Action Plan Summary",
        "",
        "- GL-45 throughput status: `%s`"
        % str(report.get("followup_resolution_escalation_throughput_status_gl45", "unknown")),
        "- GL-46 action-plan status: `%s`"
        % str(report.get("followup_resolution_escalation_action_plan_status", "unknown")),
        "- Total action items: `%s`" % str(_to_int(counts.get("total_action_count", 0), default=0)),
        "- Open action items: `%s`" % str(_to_int(counts.get("open_action_count", 0), default=0)),
        "- Missing loops to threshold: `%s`"
        % str(_to_int(counts.get("missing_complete_loops_to_threshold", 0), default=0)),
        "- Missing modalities to threshold: `%s`"
        % str(_to_int(counts.get("missing_modalities_to_threshold", 0), default=0)),
        "",
        "## Warning Codes",
    ]
    if warning_codes:
        for code in warning_codes:
            lines.append("- `%s`" % str(code))
    else:
        lines.append("- none")

    lines.extend(["", "## Action Items"])
    if rows:
        for row in rows:
            if not isinstance(row, dict):
                continue
            lines.append(
                "- `%s` type=%s modality=%s slot=%s reason=%s"
                % (
                    str(row.get("action_id", "")),
                    str(row.get("action_type", "")),
                    str(row.get("required_modality", "")),
                    str(_to_int(row.get("backfill_slot_index", 0), default=0)),
                    str(row.get("reason", "")),
                )
            )
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    throughput_report_path = Path(
        str(args.submission_queue_followup_resolution_escalation_throughput_report).strip()
    ).resolve()
    collection_report_path = Path(str(args.collection_report).strip()).resolve()
    output_path = None if str(args.output).strip() == "-" else Path(str(args.output).strip()).resolve()
    summary_path = None if str(args.summary_output).strip() == "-" else Path(str(args.summary_output).strip()).resolve()
    owner = str(args.owner).strip() or "controlled-beta-ops"

    try:
        if not throughput_report_path.is_file():
            raise ValueError("GL-45 throughput report path does not exist: %s" % throughput_report_path)
        if not collection_report_path.is_file():
            raise ValueError("GL-12 collection report path does not exist: %s" % collection_report_path)
        throughput_report = _read_json(throughput_report_path)
        collection_report = _read_json(collection_report_path)
        report = _build_report(
            throughput_report=throughput_report,
            throughput_report_path=throughput_report_path,
            collection_report=collection_report,
            collection_report_path=collection_report_path,
            owner=owner,
        )
        summary = _render_summary(report)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(
            "Real trial submission queue follow-up resolution escalation action plan generation failed: %s" % exc,
            file=sys.stderr,
        )
        return 2

    if output_path is not None:
        _write_text(output_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print(
            "Real trial submission queue follow-up resolution escalation action-plan report written: %s"
            % output_path
        )
    if summary_path is not None:
        _write_text(summary_path, summary)
        print(
            "Real trial submission queue follow-up resolution escalation action-plan summary written: %s"
            % summary_path
        )

    counts = report.get("followup_resolution_escalation_action_plan_counts", {})
    if not isinstance(counts, dict):
        counts = {}

    print(
        "Real trial submission queue follow-up resolution escalation action plan status=%s open_actions=%s"
        % (
            str(report.get("followup_resolution_escalation_action_plan_status", "unknown")),
            _to_int(counts.get("open_action_count", 0), default=0),
        )
    )
    if args.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    if bool(args.fail_on_open) and _to_int(counts.get("open_action_count", 0), default=0) > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
