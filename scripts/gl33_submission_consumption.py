from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PLACEHOLDER_TOKEN = "TEMPLATE_REQUIRED_"

DEFAULT_TEMPLATE_MANIFEST_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-manifest.template.json"
)
DEFAULT_REAL_SUBMISSIONS_INPUT_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-real-inputs.json"
)
DEFAULT_OUTPUT_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-consumption-report.json"
)
DEFAULT_SUMMARY_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-consumption-summary.md"
)
DEFAULT_CONSUMED_MANIFEST_OUTPUT_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "manifests"
    / "real-trial-backfill-submission-manifest.consumed.json"
)

REQUIRED_REAL_TRACE_FIELDS = [
    "loop_id",
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
            "Consume GL-31 pending backfill submission templates using real external Beta "
            "submission records and produce an ingestion-ready loop manifest."
        )
    )
    parser.add_argument("--submission-manifest-template", default=str(DEFAULT_TEMPLATE_MANIFEST_PATH))
    parser.add_argument("--real-submissions-input", default=str(DEFAULT_REAL_SUBMISSIONS_INPUT_PATH))
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help='Consumption report output path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--summary-output",
        default=str(DEFAULT_SUMMARY_PATH),
        help='Consumption summary output path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--consumed-manifest-output",
        default=str(DEFAULT_CONSUMED_MANIFEST_OUTPUT_PATH),
        help='Consumed real-loop manifest output path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--owner",
        default="controlled-beta-ops",
        help="Owner tag written into generated consumption outputs.",
    )
    parser.add_argument(
        "--fail-on-incomplete",
        action="store_true",
        help="Exit with code 1 when template consumption is incomplete.",
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


def _to_float(value: Any, *, default: float = 0.0) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return float(default)


def _to_bool(value: Any, *, default: bool = False) -> bool:
    if value is None:
        return bool(default)
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "y", "on"}:
            return True
        if normalized in {"0", "false", "no", "n", "off"}:
            return False
    return bool(default)


def _is_utc_timestamp(value: Any) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return False
    return parsed.tzinfo is not None


def _contains_template_placeholder(value: Any) -> bool:
    text = str(value or "").strip().upper()
    return bool(text) and TEMPLATE_PLACEHOLDER_TOKEN in text


def _normalize_template_loops(payload: dict[str, Any], *, source_path: Path) -> list[dict[str, Any]]:
    raw_loops = payload.get("loops")
    if not isinstance(raw_loops, list):
        raise ValueError("Template manifest loops must be a list: %s" % source_path)
    normalized_loops: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_loops, start=1):
        if not isinstance(raw, dict):
            raise ValueError("Template loop row at index %s must be an object." % index)
        slot_index = _to_int(raw.get("backfill_slot_index"), default=0)
        action_id = str(raw.get("backfill_action_id", "")).strip()
        modality = str(raw.get("modality", "")).strip().lower()
        if slot_index <= 0:
            raise ValueError("Template loop row at index %s missing valid backfill_slot_index." % index)
        if not action_id:
            raise ValueError("Template loop row at index %s missing backfill_action_id." % index)
        if not modality:
            raise ValueError("Template loop row at index %s missing modality." % index)
        normalized_loops.append(
            {
                "slot_index": slot_index,
                "action_id": action_id,
                "modality": modality,
                "template_loop": raw,
            }
        )
    return normalized_loops


def _normalize_submission_rows(payload: dict[str, Any], *, source_path: Path) -> list[dict[str, Any]]:
    rows = payload.get("submissions")
    if not isinstance(rows, list):
        raise ValueError("Real submissions input must include submissions list: %s" % source_path)
    normalized: list[dict[str, Any]] = []
    for index, raw in enumerate(rows, start=1):
        if not isinstance(raw, dict):
            normalized.append(
                {
                    "row_index": index,
                    "row": raw,
                    "invalid_reason": "submission_row_not_object",
                }
            )
            continue
        slot_index = _to_int(raw.get("backfill_slot_index"), default=0)
        action_id = str(raw.get("backfill_action_id", "")).strip()
        modality = str(raw.get("modality", "")).strip().lower()
        loop_id = str(raw.get("loop_id", "")).strip()
        source_system = str(raw.get("source_system", "")).strip()
        source_reference = str(raw.get("source_reference", "")).strip()
        collected_at_utc = str(raw.get("collected_at_utc", "")).strip()
        review_task_id = str(raw.get("review_task_id", "")).strip()
        reviewed_by = str(raw.get("reviewed_by", "")).strip()
        reviewed_at_utc = str(raw.get("reviewed_at_utc", "")).strip()
        submission = {
            "row_index": index,
            "action_id": action_id,
            "slot_index": slot_index if slot_index > 0 else None,
            "modality": modality,
            "loop_id": loop_id,
            "source_system": source_system,
            "source_reference": source_reference,
            "collected_at_utc": collected_at_utc,
            "review_task_id": review_task_id,
            "reviewed_by": reviewed_by,
            "reviewed_at_utc": reviewed_at_utc,
            "review_outcome": str(raw.get("review_outcome", "approved")).strip().lower() or "approved",
            "revisions_before_approval": _to_int(raw.get("revisions_before_approval"), default=0),
            "reviewer_edit_distance_pct": _to_float(raw.get("reviewer_edit_distance_pct"), default=0.0),
            "agent_smoke_result": str(raw.get("agent_smoke_result", "not_run")).strip().lower() or "not_run",
            "published_without_review": _to_bool(raw.get("published_without_review"), default=False),
            "critical_secret_or_pii_leak": _to_bool(raw.get("critical_secret_or_pii_leak"), default=False),
            "high_severity_incident": _to_bool(raw.get("high_severity_incident"), default=False),
            "latency_ms": _to_float(raw.get("latency_ms"), default=0.0),
            "provider_failure_count": _to_int(raw.get("provider_failure_count"), default=0),
            "provider_call_count": _to_int(raw.get("provider_call_count"), default=0),
            "retry_count": _to_int(raw.get("retry_count"), default=0),
            "artifact_count": _to_int(raw.get("artifact_count"), default=0),
            "estimated_cost_usd": _to_float(raw.get("estimated_cost_usd"), default=0.0),
            "raw": raw,
        }
        normalized.append(submission)
    return normalized


def _resolve_template_target(
    *,
    action_id: str,
    slot_index: int | None,
    template_by_action_id: dict[str, dict[str, Any]],
    template_by_slot_index: dict[int, dict[str, Any]],
) -> tuple[dict[str, Any] | None, str]:
    template_by_action = template_by_action_id.get(action_id) if action_id else None
    template_by_slot = template_by_slot_index.get(slot_index) if slot_index else None
    if template_by_action and template_by_slot:
        if template_by_action is template_by_slot:
            return template_by_action, "action_id_and_slot_index"
        return None, "action_slot_mismatch"
    if template_by_action:
        return template_by_action, "action_id_only"
    if template_by_slot:
        return template_by_slot, "slot_index_only"
    if not action_id and slot_index is None:
        return None, "missing_action_id_and_slot_index"
    if action_id and slot_index is not None:
        return None, "unknown_action_id_and_slot_index"
    if action_id:
        return None, "unknown_action_id"
    return None, "unknown_slot_index"


def _build_consumed_loop(template_loop: dict[str, Any], submission: dict[str, Any]) -> dict[str, Any]:
    consumed = dict(template_loop)
    consumed["loop_id"] = str(submission.get("loop_id", "")).strip()
    consumed["status"] = "complete"
    consumed["modality"] = str(consumed.get("modality", "")).strip().lower()
    consumed["evidence_origin"] = "real"
    consumed["launch_gate_eligible"] = True
    consumed["source_system"] = str(submission.get("source_system", "")).strip()
    consumed["source_reference"] = str(submission.get("source_reference", "")).strip()
    consumed["collected_at_utc"] = str(submission.get("collected_at_utc", "")).strip()
    consumed["review_task_id"] = str(submission.get("review_task_id", "")).strip()
    consumed["reviewed_by"] = str(submission.get("reviewed_by", "")).strip()
    consumed["reviewed_at_utc"] = str(submission.get("reviewed_at_utc", "")).strip()
    consumed["review_outcome"] = str(submission.get("review_outcome", "approved")).strip().lower() or "approved"
    consumed["revisions_before_approval"] = _to_int(submission.get("revisions_before_approval"), default=0)
    consumed["reviewer_edit_distance_pct"] = _to_float(submission.get("reviewer_edit_distance_pct"), default=0.0)
    consumed["agent_smoke_result"] = str(submission.get("agent_smoke_result", "not_run")).strip().lower() or "not_run"
    consumed["published_without_review"] = _to_bool(submission.get("published_without_review"), default=False)
    consumed["critical_secret_or_pii_leak"] = _to_bool(submission.get("critical_secret_or_pii_leak"), default=False)
    consumed["high_severity_incident"] = _to_bool(submission.get("high_severity_incident"), default=False)
    consumed["latency_ms"] = _to_float(submission.get("latency_ms"), default=0.0)
    consumed["provider_failure_count"] = _to_int(submission.get("provider_failure_count"), default=0)
    consumed["provider_call_count"] = _to_int(submission.get("provider_call_count"), default=0)
    consumed["retry_count"] = _to_int(submission.get("retry_count"), default=0)
    consumed["artifact_count"] = _to_int(submission.get("artifact_count"), default=0)
    consumed["estimated_cost_usd"] = _to_float(submission.get("estimated_cost_usd"), default=0.0)
    metadata = consumed.get("template_metadata")
    if not isinstance(metadata, dict):
        metadata = {}
    metadata["template_consumed"] = True
    metadata["template_consumed_at_utc"] = _utc_now_iso()
    metadata["template_consumed_by_owner"] = str(submission.get("owner", "")).strip() or ""
    metadata["template_submission_row_index"] = _to_int(submission.get("row_index"), default=0)
    consumed["template_metadata"] = metadata
    return consumed


def _validate_consumed_loop(loop: dict[str, Any]) -> tuple[bool, str, list[str]]:
    missing_fields: list[str] = []
    placeholder_fields: list[str] = []
    for field in REQUIRED_REAL_TRACE_FIELDS:
        value = loop.get(field)
        text = str(value or "").strip()
        if not text:
            missing_fields.append(field)
        elif _contains_template_placeholder(text):
            placeholder_fields.append(field)
    if missing_fields:
        return False, "missing_required_real_trace_fields", missing_fields
    if placeholder_fields:
        return False, "template_placeholders_not_replaced", placeholder_fields
    for ts_field in ("collected_at_utc", "reviewed_at_utc"):
        if not _is_utc_timestamp(loop.get(ts_field)):
            return False, "invalid_utc_timestamp_field", [ts_field]
    return True, "", []


def _build_consumption_outputs(
    *,
    template_manifest: dict[str, Any],
    submissions_input: dict[str, Any],
    template_manifest_path: Path,
    submissions_input_path: Path,
    owner: str,
    consumed_manifest_output_path: Path | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    template_rows = _normalize_template_loops(template_manifest, source_path=template_manifest_path)
    submission_rows = _normalize_submission_rows(submissions_input, source_path=submissions_input_path)

    template_by_action_id: dict[str, dict[str, Any]] = {}
    template_by_slot_index: dict[int, dict[str, Any]] = {}
    for row in template_rows:
        template_by_action_id[row["action_id"]] = row
        template_by_slot_index[row["slot_index"]] = row

    consumed_loops: list[dict[str, Any]] = []
    consumed_template_action_ids: set[str] = set()
    consumed_template_slot_indices: set[int] = set()
    unresolved_submissions: list[dict[str, Any]] = []
    invalid_submissions: list[dict[str, Any]] = []
    linkage_records: list[dict[str, Any]] = []

    for row in submission_rows:
        if not isinstance(row, dict):
            continue
        row_index = _to_int(row.get("row_index"), default=0)
        if row.get("invalid_reason"):
            invalid_submissions.append(
                {
                    "row_index": row_index,
                    "invalid_reason": str(row.get("invalid_reason")),
                }
            )
            continue

        required_missing: list[str] = []
        for field in REQUIRED_REAL_TRACE_FIELDS:
            value = str(row.get(field, "")).strip()
            if not value:
                required_missing.append(field)
        if required_missing:
            invalid_submissions.append(
                {
                    "row_index": row_index,
                    "invalid_reason": "missing_required_real_trace_fields",
                    "fields": required_missing,
                }
            )
            continue
        placeholder_fields = [
            field for field in REQUIRED_REAL_TRACE_FIELDS if _contains_template_placeholder(row.get(field))
        ]
        if placeholder_fields:
            invalid_submissions.append(
                {
                    "row_index": row_index,
                    "invalid_reason": "template_placeholders_not_replaced",
                    "fields": placeholder_fields,
                }
            )
            continue
        if not _is_utc_timestamp(row.get("collected_at_utc")) or not _is_utc_timestamp(row.get("reviewed_at_utc")):
            invalid_submissions.append(
                {
                    "row_index": row_index,
                    "invalid_reason": "invalid_utc_timestamp_field",
                    "fields": [
                        field
                        for field in ("collected_at_utc", "reviewed_at_utc")
                        if not _is_utc_timestamp(row.get(field))
                    ],
                }
            )
            continue

        target, resolution = _resolve_template_target(
            action_id=str(row.get("action_id", "")),
            slot_index=row.get("slot_index"),
            template_by_action_id=template_by_action_id,
            template_by_slot_index=template_by_slot_index,
        )
        if target is None:
            unresolved_submissions.append(
                {
                    "row_index": row_index,
                    "resolution": resolution,
                    "backfill_action_id": str(row.get("action_id", "")),
                    "backfill_slot_index": row.get("slot_index"),
                }
            )
            continue

        target_action_id = str(target.get("action_id", ""))
        target_slot_index = _to_int(target.get("slot_index"), default=0)
        if target_action_id in consumed_template_action_ids or target_slot_index in consumed_template_slot_indices:
            invalid_submissions.append(
                {
                    "row_index": row_index,
                    "invalid_reason": "duplicate_template_assignment",
                    "backfill_action_id": target_action_id,
                    "backfill_slot_index": target_slot_index,
                }
            )
            continue

        target_modality = str(target.get("modality", "")).strip().lower()
        provided_modality = str(row.get("modality", "")).strip().lower()
        if provided_modality and provided_modality != target_modality:
            invalid_submissions.append(
                {
                    "row_index": row_index,
                    "invalid_reason": "modality_mismatch_with_template",
                    "template_modality": target_modality,
                    "provided_modality": provided_modality,
                }
            )
            continue
        row["owner"] = owner
        consumed_loop = _build_consumed_loop(target.get("template_loop", {}), row)
        valid_loop, invalid_reason, invalid_fields = _validate_consumed_loop(consumed_loop)
        if not valid_loop:
            invalid_submissions.append(
                {
                    "row_index": row_index,
                    "invalid_reason": invalid_reason,
                    "fields": invalid_fields,
                    "backfill_action_id": target_action_id,
                    "backfill_slot_index": target_slot_index,
                }
            )
            continue

        consumed_loops.append(consumed_loop)
        consumed_template_action_ids.add(target_action_id)
        consumed_template_slot_indices.add(target_slot_index)
        linkage_records.append(
            {
                "row_index": row_index,
                "resolution": resolution,
                "backfill_action_id": target_action_id,
                "backfill_slot_index": target_slot_index,
                "loop_id": str(consumed_loop.get("loop_id", "")),
                "modality": str(consumed_loop.get("modality", "")),
            }
        )

    pending_template_rows = [
        {
            "backfill_action_id": str(item.get("action_id", "")),
            "backfill_slot_index": _to_int(item.get("slot_index"), default=0),
            "required_modality": str(item.get("modality", "")),
        }
        for item in template_rows
        if str(item.get("action_id", "")) not in consumed_template_action_ids
    ]

    template_loop_count = len(template_rows)
    submitted_row_count = len(submission_rows)
    consumed_loop_count = len(consumed_loops)
    pending_template_loop_count = len(pending_template_rows)
    invalid_submission_count = len(invalid_submissions)
    unresolved_submission_count = len(unresolved_submissions)

    if template_loop_count == 0:
        status = "NO_TEMPLATE_ROWS"
    elif submitted_row_count == 0:
        status = "NO_SUBMISSIONS_PROVIDED"
    elif pending_template_loop_count == 0 and invalid_submission_count == 0 and unresolved_submission_count == 0:
        status = "CONSUMED_MANIFEST_READY"
    else:
        status = "CONSUMPTION_INCOMPLETE"

    consumed_manifest = {
        "manifest_id": "gl33-real-backfill-submission-manifest-consumed",
        "manifest_version": "1.0",
        "generated_at_utc": _utc_now_iso(),
        "description": (
            "GL-33 consumed real submission manifest generated from GL-31 templates "
            "with placeholder fields fully replaced."
        ),
        "owner": owner,
        "source_template_manifest": str(template_manifest_path),
        "source_real_submissions_input": str(submissions_input_path),
        "loops": consumed_loops,
    }

    report = {
        "schema_version": "real_trial_backfill_submission_consumption.v1",
        "generated_at_utc": _utc_now_iso(),
        "input_paths": {
            "submission_manifest_template": str(template_manifest_path),
            "real_submissions_input": str(submissions_input_path),
        },
        "owner": owner,
        "consumption_status": status,
        "counts": {
            "template_loop_count": template_loop_count,
            "submitted_row_count": submitted_row_count,
            "consumed_loop_count": consumed_loop_count,
            "pending_template_loop_count": pending_template_loop_count,
            "invalid_submission_count": invalid_submission_count,
            "unresolved_submission_count": unresolved_submission_count,
        },
        "consumed_manifest_path": str(consumed_manifest_output_path) if consumed_manifest_output_path else "",
        "consumption_linkage_records": linkage_records,
        "pending_template_rows": pending_template_rows,
        "invalid_submissions": invalid_submissions,
        "unresolved_submissions": unresolved_submissions,
    }
    return report, consumed_manifest


def _render_summary(report: dict[str, Any]) -> str:
    counts = report.get("counts", {})
    if not isinstance(counts, dict):
        counts = {}
    lines = [
        "# Real Trial Backfill Submission Consumption Summary",
        "",
        "- Consumption status: `%s`" % str(report.get("consumption_status", "unknown")),
        "- Template loops: `%s`" % str(counts.get("template_loop_count", 0)),
        "- Submitted rows: `%s`" % str(counts.get("submitted_row_count", 0)),
        "- Consumed loops: `%s`" % str(counts.get("consumed_loop_count", 0)),
        "- Pending template loops: `%s`" % str(counts.get("pending_template_loop_count", 0)),
        "- Invalid submissions: `%s`" % str(counts.get("invalid_submission_count", 0)),
        "- Unresolved submissions: `%s`" % str(counts.get("unresolved_submission_count", 0)),
        "- Owner: `%s`" % str(report.get("owner", "")),
        "",
        "## Pending Template Rows",
    ]
    pending_rows = report.get("pending_template_rows", [])
    if isinstance(pending_rows, list) and pending_rows:
        for item in pending_rows:
            if not isinstance(item, dict):
                continue
            lines.append(
                "- `%s` slot=%s modality=%s"
                % (
                    str(item.get("backfill_action_id", "")),
                    str(item.get("backfill_slot_index", "")),
                    str(item.get("required_modality", "")),
                )
            )
    else:
        lines.append("- none")
    lines.extend(["", "## Invalid Submissions"])
    invalid_rows = report.get("invalid_submissions", [])
    if isinstance(invalid_rows, list) and invalid_rows:
        for item in invalid_rows:
            if not isinstance(item, dict):
                continue
            lines.append(
                "- row=%s reason=%s fields=%s"
                % (
                    str(item.get("row_index", "")),
                    str(item.get("invalid_reason", "")),
                    str(item.get("fields", [])),
                )
            )
    else:
        lines.append("- none")
    lines.extend(["", "## Unresolved Submissions"])
    unresolved_rows = report.get("unresolved_submissions", [])
    if isinstance(unresolved_rows, list) and unresolved_rows:
        for item in unresolved_rows:
            if not isinstance(item, dict):
                continue
            lines.append(
                "- row=%s resolution=%s action_id=%s slot_index=%s"
                % (
                    str(item.get("row_index", "")),
                    str(item.get("resolution", "")),
                    str(item.get("backfill_action_id", "")),
                    str(item.get("backfill_slot_index", "")),
                )
            )
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    template_manifest_path = Path(str(args.submission_manifest_template).strip()).resolve()
    submissions_input_path = Path(str(args.real_submissions_input).strip()).resolve()
    output_path = None if str(args.output).strip() == "-" else Path(str(args.output).strip()).resolve()
    summary_path = None if str(args.summary_output).strip() == "-" else Path(str(args.summary_output).strip()).resolve()
    consumed_manifest_output_path = (
        None if str(args.consumed_manifest_output).strip() == "-" else Path(str(args.consumed_manifest_output).strip()).resolve()
    )
    owner = str(args.owner).strip() or "controlled-beta-ops"

    try:
        if not template_manifest_path.is_file():
            raise ValueError("Submission manifest template path does not exist: %s" % template_manifest_path)
        if not submissions_input_path.is_file():
            raise ValueError("Real submissions input path does not exist: %s" % submissions_input_path)
        template_manifest = _read_json(template_manifest_path)
        submissions_input = _read_json(submissions_input_path)
        report, consumed_manifest = _build_consumption_outputs(
            template_manifest=template_manifest,
            submissions_input=submissions_input,
            template_manifest_path=template_manifest_path,
            submissions_input_path=submissions_input_path,
            owner=owner,
            consumed_manifest_output_path=consumed_manifest_output_path,
        )
        summary = _render_summary(report)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print("Real trial backfill submission consumption failed: %s" % exc, file=sys.stderr)
        return 2

    if output_path is not None:
        _write_text(output_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print("Real trial backfill submission consumption report written: %s" % output_path)
    if summary_path is not None:
        _write_text(summary_path, summary)
        print("Real trial backfill submission consumption summary written: %s" % summary_path)
    if consumed_manifest_output_path is not None:
        _write_text(consumed_manifest_output_path, json.dumps(consumed_manifest, ensure_ascii=False, indent=2) + "\n")
        print("Real trial backfill consumed manifest written: %s" % consumed_manifest_output_path)

    counts = report.get("counts", {})
    if not isinstance(counts, dict):
        counts = {}
    print(
        "Real trial backfill submission consumption status=%s consumed=%s/%s pending=%s invalid=%s unresolved=%s"
        % (
            str(report.get("consumption_status", "unknown")),
            _to_int(counts.get("consumed_loop_count"), default=0),
            _to_int(counts.get("template_loop_count"), default=0),
            _to_int(counts.get("pending_template_loop_count"), default=0),
            _to_int(counts.get("invalid_submission_count"), default=0),
            _to_int(counts.get("unresolved_submission_count"), default=0),
        )
    )

    if args.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    if bool(args.fail_on_incomplete) and str(report.get("consumption_status", "")).strip().upper() != "CONSUMED_MANIFEST_READY":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
