from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INTAKE_ACTIONS_REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-intake-actions-report.json"
)
DEFAULT_OUTPUT_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-templates-report.json"
)
DEFAULT_SUMMARY_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-templates-summary.md"
)
DEFAULT_MANIFEST_TEMPLATE_OUTPUT_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-manifest.template.json"
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate GL-31 operator-ready real-loop submission manifest templates "
            "from pending GL-23 backfill intake actions."
        )
    )
    parser.add_argument("--intake-actions-report", default=str(DEFAULT_INTAKE_ACTIONS_REPORT_PATH))
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help='Template report output path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--summary-output",
        default=str(DEFAULT_SUMMARY_PATH),
        help='Template summary output path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--manifest-template-output",
        default=str(DEFAULT_MANIFEST_TEMPLATE_OUTPUT_PATH),
        help='Template manifest output path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--owner",
        default="controlled-beta-ops",
        help="Owner tag recorded on generated submission templates.",
    )
    parser.add_argument(
        "--fail-on-missing-template",
        action="store_true",
        help="Exit with code 1 when any pending action cannot produce a valid template row.",
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


def _build_manifest_loop_template(action: dict[str, Any]) -> tuple[dict[str, Any] | None, str]:
    action_id = str(action.get("action_id", "")).strip()
    required_modality = str(action.get("required_modality", "")).strip().lower()
    slot_index = _to_int(action.get("slot_index"), default=0)
    if not action_id:
        return None, "missing_action_id"
    if not required_modality:
        return None, "missing_required_modality"
    if slot_index <= 0:
        return None, "invalid_slot_index"

    return (
        {
            "loop_id": "real-%s-slot-%03d-template" % (required_modality, slot_index),
            "status": "complete",
            "modality": required_modality,
            "evidence_origin": "real",
            "launch_gate_eligible": True,
            "source_system": "TEMPLATE_REQUIRED_REPLACE_WITH_REAL_SOURCE_SYSTEM",
            "source_reference": "TEMPLATE_REQUIRED_REPLACE_WITH_REAL_SOURCE_REFERENCE",
            "collected_at_utc": "TEMPLATE_REQUIRED_REPLACE_WITH_UTC_TIMESTAMP",
            "review_task_id": "TEMPLATE_REQUIRED_REPLACE_WITH_REVIEW_TASK_ID",
            "reviewed_by": "TEMPLATE_REQUIRED_REPLACE_WITH_REVIEWER",
            "reviewed_at_utc": "TEMPLATE_REQUIRED_REPLACE_WITH_UTC_TIMESTAMP",
            "review_outcome": "approved",
            "revisions_before_approval": 0,
            "reviewer_edit_distance_pct": 0.0,
            "agent_smoke_result": "not_run",
            "published_without_review": False,
            "critical_secret_or_pii_leak": False,
            "high_severity_incident": False,
            "latency_ms": 0.0,
            "provider_failure_count": 0,
            "provider_call_count": 0,
            "retry_count": 0,
            "artifact_count": 0,
            "estimated_cost_usd": 0.0,
            "backfill_slot_index": slot_index,
            "backfill_action_id": action_id,
            "template_metadata": {
                "template_kind": "gl31_pending_backfill_submission_template",
                "template_action_id": action_id,
                "template_slot_index": slot_index,
                "template_required_modality": required_modality,
                "template_note": (
                    "Replace TEMPLATE_REQUIRED_* fields with real controlled external Beta evidence "
                    "before collecting via GL-12/GL-13."
                ),
            },
        },
        "",
    )


def _build_template_report(
    *,
    intake_actions_report: dict[str, Any],
    intake_actions_report_path: Path,
    owner: str,
    manifest_template_output_path: Path | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    actions = intake_actions_report.get("actions", [])
    if not isinstance(actions, list):
        actions = []
    pending_actions = [
        item
        for item in actions
        if isinstance(item, dict)
        and str(item.get("action_status", "")).strip().lower() == "pending"
    ]
    closed_actions = [
        item
        for item in actions
        if isinstance(item, dict)
        and str(item.get("action_status", "")).strip().lower() == "closed"
    ]

    generated_templates: list[dict[str, Any]] = []
    missing_template_actions: list[dict[str, Any]] = []
    template_manifest_loops: list[dict[str, Any]] = []
    for raw_action in pending_actions:
        if not isinstance(raw_action, dict):
            continue
        action_id = str(raw_action.get("action_id", "")).strip()
        slot_index = _to_int(raw_action.get("slot_index"), default=0)
        required_modality = str(raw_action.get("required_modality", "")).strip().lower()
        reason = str(raw_action.get("reason", "")).strip() or "unknown_reason"
        template_row, missing_reason = _build_manifest_loop_template(raw_action)
        if template_row is None:
            missing_template_actions.append(
                {
                    "action_id": action_id,
                    "slot_index": slot_index,
                    "required_modality": required_modality,
                    "reason": reason,
                    "missing_template_reason": missing_reason,
                }
            )
            continue
        template_manifest_loops.append(template_row)
        generated_templates.append(
            {
                "action_id": action_id,
                "slot_index": slot_index,
                "required_modality": required_modality,
                "reason": reason,
                "owner": str(raw_action.get("owner", "")).strip() or owner,
                "template_loop_id": str(template_row.get("loop_id", "")),
            }
        )

    pending_action_count = len(pending_actions)
    generated_template_count = len(generated_templates)
    missing_template_action_count = len(missing_template_actions)
    if pending_action_count == 0:
        template_status = "NO_PENDING_ACTIONS"
    elif missing_template_action_count > 0:
        template_status = "TEMPLATE_FIELDS_MISSING"
    else:
        template_status = "TEMPLATES_READY"

    manifest_template = {
        "manifest_id": "gl31-real-backfill-submission-template",
        "manifest_version": "1.0",
        "generated_at_utc": _utc_now_iso(),
        "description": (
            "GL-31 template manifest generated from pending backfill intake actions. "
            "Replace TEMPLATE_REQUIRED_* values with real evidence before ingestion."
        ),
        "owner": owner,
        "source_report": str(intake_actions_report_path),
        "loops": template_manifest_loops,
    }

    report = {
        "schema_version": "real_trial_backfill_submission_templates.v1",
        "generated_at_utc": _utc_now_iso(),
        "input_paths": {
            "intake_actions_report": str(intake_actions_report_path),
        },
        "owner": owner,
        "template_status": template_status,
        "action_counts": {
            "total_action_count": len(actions),
            "pending_action_count": pending_action_count,
            "closed_action_count": len(closed_actions),
        },
        "template_counts": {
            "generated_template_count": generated_template_count,
            "missing_template_action_count": missing_template_action_count,
        },
        "missing_template_actions": missing_template_actions,
        "generated_templates": generated_templates,
        "manifest_template_path": str(manifest_template_output_path) if manifest_template_output_path else "",
        "launch_gap_snapshot": intake_actions_report.get("launch_gap_snapshot", {}),
    }
    return report, manifest_template


def _render_summary(report: dict[str, Any]) -> str:
    action_counts = report.get("action_counts", {})
    if not isinstance(action_counts, dict):
        action_counts = {}
    template_counts = report.get("template_counts", {})
    if not isinstance(template_counts, dict):
        template_counts = {}
    lines = [
        "# Real Trial Backfill Submission Templates Summary",
        "",
        "- Template status: `%s`" % str(report.get("template_status", "unknown")),
        "- Total actions: `%s`" % str(action_counts.get("total_action_count", 0)),
        "- Pending actions: `%s`" % str(action_counts.get("pending_action_count", 0)),
        "- Closed actions: `%s`" % str(action_counts.get("closed_action_count", 0)),
        "- Generated templates: `%s`" % str(template_counts.get("generated_template_count", 0)),
        "- Missing templates: `%s`" % str(template_counts.get("missing_template_action_count", 0)),
        "- Owner: `%s`" % str(report.get("owner", "")),
        "",
        "## Pending Template Rows",
    ]
    generated_templates = report.get("generated_templates", [])
    if isinstance(generated_templates, list) and generated_templates:
        for item in generated_templates:
            if not isinstance(item, dict):
                continue
            lines.append(
                "- `%s` slot=%s modality=%s template_loop_id=%s"
                % (
                    str(item.get("action_id", "")),
                    str(item.get("slot_index", "")),
                    str(item.get("required_modality", "")),
                    str(item.get("template_loop_id", "")),
                )
            )
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Missing Template Actions",
        ]
    )
    missing_actions = report.get("missing_template_actions", [])
    if isinstance(missing_actions, list) and missing_actions:
        for item in missing_actions:
            if not isinstance(item, dict):
                continue
            lines.append(
                "- `%s` slot=%s modality=%s reason=%s"
                % (
                    str(item.get("action_id", "")),
                    str(item.get("slot_index", "")),
                    str(item.get("required_modality", "")),
                    str(item.get("missing_template_reason", "")),
                )
            )
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    intake_actions_report_path = Path(str(args.intake_actions_report).strip()).resolve()
    output_path = None if str(args.output).strip() == "-" else Path(str(args.output).strip()).resolve()
    summary_path = None if str(args.summary_output).strip() == "-" else Path(str(args.summary_output).strip()).resolve()
    manifest_template_output_path = (
        None
        if str(args.manifest_template_output).strip() == "-"
        else Path(str(args.manifest_template_output).strip()).resolve()
    )
    owner = str(args.owner).strip() or "controlled-beta-ops"

    try:
        if not intake_actions_report_path.is_file():
            raise ValueError("Intake actions report path does not exist: %s" % intake_actions_report_path)
        intake_actions_report = _read_json(intake_actions_report_path)
        report, manifest_template = _build_template_report(
            intake_actions_report=intake_actions_report,
            intake_actions_report_path=intake_actions_report_path,
            owner=owner,
            manifest_template_output_path=manifest_template_output_path,
        )
        summary = _render_summary(report)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print("Real trial backfill submission template generation failed: %s" % exc, file=sys.stderr)
        return 2

    if output_path is not None:
        _write_text(output_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print("Real trial backfill submission templates report written: %s" % output_path)
    if summary_path is not None:
        _write_text(summary_path, summary)
        print("Real trial backfill submission templates summary written: %s" % summary_path)
    if manifest_template_output_path is not None:
        _write_text(manifest_template_output_path, json.dumps(manifest_template, ensure_ascii=False, indent=2) + "\n")
        print("Real trial backfill submission manifest template written: %s" % manifest_template_output_path)

    template_counts = report.get("template_counts", {})
    if not isinstance(template_counts, dict):
        template_counts = {}
    action_counts = report.get("action_counts", {})
    if not isinstance(action_counts, dict):
        action_counts = {}
    print(
        "Real trial backfill submission templates status=%s generated=%s/%s"
        % (
            str(report.get("template_status", "unknown")),
            _to_int(template_counts.get("generated_template_count"), default=0),
            _to_int(action_counts.get("pending_action_count"), default=0),
        )
    )
    if args.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    if bool(args.fail_on_missing_template) and _to_int(
        template_counts.get("missing_template_action_count"), default=0
    ) > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
