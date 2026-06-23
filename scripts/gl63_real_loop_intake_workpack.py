from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
REAL_TRIAL_BASELINE_DIR = REPO_ROOT / "docs" / "working" / "status" / "baselines" / "real-trial-loop-collection"
DEFAULT_EVIDENCE_PACK_PATH = REAL_TRIAL_BASELINE_DIR / "real-trial-launch-evidence-pack.json"
DEFAULT_OUTPUT_PATH = REAL_TRIAL_BASELINE_DIR / "real-trial-loop-intake-workpack-report.json"
DEFAULT_SUMMARY_PATH = REAL_TRIAL_BASELINE_DIR / "real-trial-loop-intake-workpack-summary.md"
DEFAULT_MANIFEST_DIR = REAL_TRIAL_BASELINE_DIR / "manifests"

REQUIRED_TRACE_FIELDS = [
    "evidence_origin=real",
    "launch_gate_eligible=true",
    "source_bundle_ref",
    "source_hashes",
    "source_system",
    "source_reference",
    "collected_at_utc",
    "business_expectation_ref",
    "run_evidence_ref",
    "human_review_ref",
    "agent_smoke_ref",
    "generated_bundle_hash",
    "review_task_id",
    "reviewed_by",
    "reviewed_at_utc",
]
REQUIRED_QUALITY_FIELDS = [
    "status=complete",
    "review_outcome=approved",
    "redaction_status=passed",
    "pii_status=no_raw_pii_in_repo",
    "review_status=approved",
    "quality_gate_ref",
    "quality_gate_status=passed",
    "quality_scores.faithfulness>=4",
    "quality_scores.traceability>=4",
    "quality_scores.safety_redaction=5",
    "quality_scores.agent_usability>=4",
    "critical_issues=[]",
    "requires_human_review=true",
    "revisions_before_approval",
    "reviewer_edit_distance_pct",
    "agent_smoke_result=passed",
    "published_without_review=false",
    "critical_secret_or_pii_leak=false",
    "high_severity_incident=false",
    "latency_ms",
    "provider_failure_count",
    "provider_call_count",
    "retry_count",
    "artifact_count",
    "estimated_cost_usd",
]


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


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _resolve_pack_path(value: Any) -> Path:
    raw = str(value or "").strip()
    if not raw:
        return Path()
    path = Path(raw)
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def _display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return str(resolved)


def _normalize_modality(value: Any) -> str:
    return str(value or "").strip().lower()


def _gl62_rows_by_modality(gl62_report: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    rows = _as_list(
        gl62_report.get(
            "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_rows",
            [],
        )
    )
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        modality = _normalize_modality(row.get("required_modality_gl47"))
        grouped.setdefault(modality, []).append(row)
    return grouped


def _status_from_counts(*, open_item_count: int, gl62_report: dict[str, Any]) -> str:
    counts = _as_dict(
        gl62_report.get(
            "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_counts",
            {},
        )
    )
    if open_item_count <= 0:
        return "REAL_LOOP_INTAKE_NOT_REQUIRED"
    if _to_int(counts.get("blocked_overdue_stalled_item_count"), default=0) > 0:
        return "REAL_LOOP_INTAKE_ESCALATION_OVERDUE_STALLED"
    if _to_int(counts.get("due_item_count"), default=0) > 0:
        return "REAL_LOOP_INTAKE_ESCALATION_DUE"
    return "REAL_LOOP_INTAKE_ACTION_REQUIRED"


def _build_warning_codes(
    *,
    open_item_count: int,
    missing_modality_count: int,
    missing_loop_count: int,
    gl62_report: dict[str, Any],
) -> list[str]:
    warning_codes: list[str] = []
    if open_item_count > 0:
        warning_codes.append("real_loop_intake_items_required")
    if missing_modality_count > 0:
        warning_codes.append("real_loop_modality_gap_persists")
    if missing_loop_count > 0:
        warning_codes.append("real_loop_volume_gap_persists")

    gl62_warning_codes = _as_list(gl62_report.get("warning_codes", []))
    if "no_net_new_launch_gate_eligible_real_loops" in gl62_warning_codes:
        warning_codes.append("upstream_no_net_new_launch_gate_eligible_real_loops")
    return warning_codes


def _build_workpack(
    *,
    evidence_pack: dict[str, Any],
    evidence_pack_path: Path,
    gl62_report: dict[str, Any],
    gl62_report_path: Path | None,
    manifest_dir: Path,
    owner: str,
) -> dict[str, Any]:
    classification = _as_dict(evidence_pack.get("evidence_classification", {}))
    recommended_slots = _as_list(classification.get("recommended_backfill_slots", []))
    missing_modalities = [
        _normalize_modality(item) for item in _as_list(classification.get("missing_target_launch_modalities", []))
    ]
    target_modalities = [
        _normalize_modality(item) for item in _as_list(classification.get("target_launch_modalities", []))
    ]
    covered_modalities = [
        _normalize_modality(item)
        for item in _as_list(classification.get("launch_gate_eligible_complete_modalities", []))
    ]
    current_loop_count = _to_int(classification.get("launch_gate_eligible_complete_loop_count"), default=0)
    missing_loop_count = max(_to_int(classification.get("recommended_backfill_slot_count"), default=0), len(recommended_slots))
    missing_modality_count = len([item for item in missing_modalities if item])
    gl62_rows_by_modality = _gl62_rows_by_modality(gl62_report)

    work_items: list[dict[str, Any]] = []
    for index, slot in enumerate(recommended_slots, start=1):
        if not isinstance(slot, dict):
            continue
        slot_index = _to_int(slot.get("slot_index"), default=index)
        modality = _normalize_modality(slot.get("required_modality")) or "unknown"
        gl62_rows = gl62_rows_by_modality.get(modality, [])
        linked_gl62_row = gl62_rows[(slot_index - 1) % len(gl62_rows)] if gl62_rows else {}
        manifest_path = manifest_dir / ("real-loop-%03d-%s.json" % (slot_index, modality))

        work_items.append(
            {
                "intake_item_id": "gl63-real-loop-intake-slot-%03d-%s" % (slot_index, modality),
                "intake_item_status": "open",
                "owner": owner,
                "required_modality": modality,
                "slot_index": slot_index,
                "slot_reason": str(slot.get("reason", "")).strip(),
                "manifest_drop_path": _display_path(manifest_path),
                "required_trace_fields": REQUIRED_TRACE_FIELDS,
                "required_quality_fields": REQUIRED_QUALITY_FIELDS,
                "linked_gl62_escalation_item_id": str(linked_gl62_row.get("escalation_item_id", "")).strip(),
                "linked_gl62_escalation_action": str(linked_gl62_row.get("escalation_action", "")).strip(),
                "acceptance_rule": (
                    "The manifest loop must be real, complete, reviewed, source-traced, redacted, "
                    "quality-gate-passed, agent-smoke-tested, and launch_gate_eligible=true. "
                    "Fixture or simulated loops must stay launch_gate_eligible=false."
                ),
            }
        )

    modality_counts: dict[str, int] = {}
    for item in work_items:
        modality = str(item.get("required_modality", "")).strip()
        modality_counts[modality] = modality_counts.get(modality, 0) + 1

    status = _status_from_counts(open_item_count=len(work_items), gl62_report=gl62_report)
    warning_codes = _build_warning_codes(
        open_item_count=len(work_items),
        missing_modality_count=missing_modality_count,
        missing_loop_count=missing_loop_count,
        gl62_report=gl62_report,
    )

    return {
        "schema_version": "real_trial_loop_intake_workpack.v1",
        "generated_at_utc": _utc_now_iso(),
        "owner": owner,
        "status": status,
        "internal_only": False,
        "launch_gate_policy_unchanged": True,
        "input_paths": {
            "real_trial_launch_evidence_pack": _display_path(evidence_pack_path),
            "gl62_escalation_report": _display_path(gl62_report_path) if gl62_report_path else "",
            "operator_manifest_dir": _display_path(manifest_dir),
        },
        "current_launch_evidence": {
            "launch_decision": str(evidence_pack.get("launch_decision", "unknown")),
            "collection_program_status": str(classification.get("collection_program_status", "unknown")),
            "launch_gate_eligible_complete_loop_count": current_loop_count,
            "target_launch_modalities": target_modalities,
            "covered_launch_modalities": covered_modalities,
            "missing_target_launch_modalities": missing_modalities,
            "recommended_backfill_slot_count": missing_loop_count,
        },
        "counts": {
            "total_intake_item_count": len(work_items),
            "open_intake_item_count": len(work_items),
            "missing_loop_count": missing_loop_count,
            "missing_modality_count": missing_modality_count,
            "intake_item_count_by_modality": modality_counts,
        },
        "warning_codes": warning_codes,
        "operator_manifest_contract": {
            "drop_directory": _display_path(manifest_dir),
            "top_level_contract": "JSON object with a top-level loops list",
            "required_trace_fields": REQUIRED_TRACE_FIELDS,
            "required_quality_fields": REQUIRED_QUALITY_FIELDS,
            "evidence_reference_policy": (
                "source_bundle_ref may point to controlled local/object storage; business expectation, "
                "run evidence, human review, agent smoke, and quality gate refs must be sanitized, "
                "reviewable refs."
            ),
            "post_drop_command": (
                "python -B scripts\\gl13_launch_evidence.py --loop-manifest-dir "
                + _display_path(manifest_dir)
                + " --no-run-doc-sync --max-evidence-age-hours 0"
            ),
        },
        "work_items": work_items,
    }


def _render_summary(report: dict[str, Any]) -> str:
    current = _as_dict(report.get("current_launch_evidence", {}))
    counts = _as_dict(report.get("counts", {}))
    warning_codes = _as_list(report.get("warning_codes", []))
    work_items = _as_list(report.get("work_items", []))
    contract = _as_dict(report.get("operator_manifest_contract", {}))

    lines = [
        "# Real Trial Loop Intake Workpack Summary",
        "",
        "- Status: `%s`" % str(report.get("status", "unknown")),
        "- Launch decision remains: `%s`" % str(current.get("launch_decision", "unknown")),
        "- Collection status: `%s`" % str(current.get("collection_program_status", "unknown")),
        "- Current launch-gate-eligible real loops: `%s`"
        % str(_to_int(current.get("launch_gate_eligible_complete_loop_count"), default=0)),
        "- Missing modalities: `%s`" % ", ".join(str(item) for item in _as_list(current.get("missing_target_launch_modalities", []))),
        "- Open intake items: `%s`" % str(_to_int(counts.get("open_intake_item_count"), default=0)),
        "- Manifest drop directory: `%s`" % str(contract.get("drop_directory", "")),
        "",
        "## Warning Codes",
    ]
    if warning_codes:
        for warning_code in warning_codes:
            lines.append("- `%s`" % str(warning_code))
    else:
        lines.append("- none")

    lines.extend(["", "## Work Items"])
    if work_items:
        for item in work_items:
            if not isinstance(item, dict):
                continue
            lines.append(
                "- `%s` modality=%s reason=%s manifest=%s"
                % (
                    str(item.get("intake_item_id", "")),
                    str(item.get("required_modality", "")),
                    str(item.get("slot_reason", "")),
                    str(item.get("manifest_drop_path", "")),
                )
            )
    else:
        lines.append("- none")

    lines.extend(["", "## Next Command", "", "```powershell", str(contract.get("post_drop_command", "")), "```", ""])
    return "\n".join(lines)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate GL-63 real-loop intake workpack from current GL-13 evidence and GL-62 operator "
            "escalation diagnostics. This does not create or count real evidence."
        )
    )
    parser.add_argument("--evidence-pack", default=str(DEFAULT_EVIDENCE_PACK_PATH))
    parser.add_argument(
        "--gl62-escalation-report",
        default="",
        help="Optional GL-62 report path. When omitted, the script reads the path from the evidence pack.",
    )
    parser.add_argument("--manifest-dir", default=str(DEFAULT_MANIFEST_DIR))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH), help='Report output path. Use "-" to skip.')
    parser.add_argument(
        "--summary-output",
        default=str(DEFAULT_SUMMARY_PATH),
        help='Summary output path. Use "-" to skip.',
    )
    parser.add_argument("--owner", default="controlled-beta-ops")
    parser.add_argument("--fail-on-action-required", action="store_true")
    parser.add_argument("--print-json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    evidence_pack_path = Path(str(args.evidence_pack).strip()).resolve()
    output_path = None if str(args.output).strip() == "-" else Path(str(args.output).strip()).resolve()
    summary_path = None if str(args.summary_output).strip() == "-" else Path(str(args.summary_output).strip()).resolve()
    manifest_dir = Path(str(args.manifest_dir).strip()).resolve()
    owner = str(args.owner).strip() or "controlled-beta-ops"

    try:
        if not evidence_pack_path.is_file():
            raise ValueError("Evidence pack path does not exist: %s" % evidence_pack_path)
        evidence_pack = _read_json(evidence_pack_path)

        raw_gl62_path = str(args.gl62_escalation_report).strip()
        gl62_report_path: Path | None
        if raw_gl62_path:
            gl62_report_path = Path(raw_gl62_path).resolve()
        else:
            gl62_report_path = _resolve_pack_path(
                _as_dict(evidence_pack.get("evidence_paths", {})).get(
                    "real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_report",
                    "",
                )
            )
        gl62_report: dict[str, Any] = {}
        if gl62_report_path is not None and str(gl62_report_path) and gl62_report_path.is_file():
            gl62_report = _read_json(gl62_report_path)

        report = _build_workpack(
            evidence_pack=evidence_pack,
            evidence_pack_path=evidence_pack_path,
            gl62_report=gl62_report,
            gl62_report_path=gl62_report_path if gl62_report else None,
            manifest_dir=manifest_dir,
            owner=owner,
        )
        summary = _render_summary(report)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print("Real trial loop intake workpack generation failed: %s" % exc, file=sys.stderr)
        return 2

    if output_path is not None:
        _write_text(output_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print("Real trial loop intake workpack report written: %s" % output_path)
    if summary_path is not None:
        _write_text(summary_path, summary)
        print("Real trial loop intake workpack summary written: %s" % summary_path)

    print(
        "Real trial loop intake workpack status=%s open=%s missing_modalities=%s"
        % (
            str(report.get("status", "unknown")),
            _to_int(_as_dict(report.get("counts", {})).get("open_intake_item_count"), default=0),
            _to_int(_as_dict(report.get("counts", {})).get("missing_modality_count"), default=0),
        )
    )
    if args.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    if bool(args.fail_on_action_required) and str(report.get("status", "")).strip() != "REAL_LOOP_INTAKE_NOT_REQUIRED":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
