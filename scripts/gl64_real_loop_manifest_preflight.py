from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
REAL_TRIAL_BASELINE_DIR = REPO_ROOT / "docs" / "working" / "status" / "baselines" / "real-trial-loop-collection"
DEFAULT_WORKPACK_PATH = REAL_TRIAL_BASELINE_DIR / "real-trial-loop-intake-workpack-report.json"
DEFAULT_OUTPUT_PATH = REAL_TRIAL_BASELINE_DIR / "real-trial-loop-manifest-preflight-report.json"
DEFAULT_SUMMARY_PATH = REAL_TRIAL_BASELINE_DIR / "real-trial-loop-manifest-preflight-summary.md"

STATUS_NOT_REQUIRED = "REAL_LOOP_MANIFEST_PREFLIGHT_NOT_REQUIRED"
STATUS_READY = "REAL_LOOP_MANIFEST_PREFLIGHT_READY"
STATUS_PENDING = "REAL_LOOP_MANIFEST_PREFLIGHT_PENDING"
STATUS_INVALID = "REAL_LOOP_MANIFEST_PREFLIGHT_INVALID"

REQUIRED_TEXT_FIELDS = [
    "source_system",
    "source_reference",
    "collected_at_utc",
    "review_task_id",
    "reviewed_by",
    "reviewed_at_utc",
    "review_outcome",
    "agent_smoke_result",
]
REQUIRED_NUMERIC_FIELDS = [
    "revisions_before_approval",
    "reviewer_edit_distance_pct",
    "latency_ms",
    "provider_failure_count",
    "provider_call_count",
    "retry_count",
    "artifact_count",
    "estimated_cost_usd",
]
REQUIRED_FALSE_FIELDS = [
    "published_without_review",
    "critical_secret_or_pii_leak",
    "high_severity_incident",
]
TRACE_IDENTITY_FIELDS = [
    "loop_id",
    "source_system",
    "source_reference",
    "review_task_id",
    "reviewed_by",
]
PLACEHOLDER_TOKENS = {
    "",
    "example",
    "fixture",
    "fixme",
    "mock",
    "n/a",
    "na",
    "none",
    "null",
    "placeholder",
    "sample",
    "synthetic",
    "tbd",
    "todo",
    "unknown",
}
SIMULATED_TOKENS = ("fixture", "synthetic", "simulated", "mock", "dummy", "example", "sample")


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


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _to_int(value: Any, *, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _resolve_path(raw: Any) -> Path:
    text = str(raw or "").strip()
    if not text:
        return Path()
    path = Path(text)
    if path.is_absolute():
        return path.resolve()
    return (REPO_ROOT / path).resolve()


def _display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return str(resolved)


def _normalize_modality(value: Any) -> str:
    return str(value or "").strip().lower()


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def _is_placeholder_text(value: Any) -> bool:
    text = _normalize_text(value)
    lowered = text.lower()
    if lowered in PLACEHOLDER_TOKENS:
        return True
    if "{{" in text or "}}" in text:
        return True
    if text.startswith("<") and text.endswith(">"):
        return True
    return False


def _contains_simulated_token(value: Any) -> bool:
    lowered = _normalize_text(value).lower()
    return any(token in lowered for token in SIMULATED_TOKENS)


def _is_true(value: Any) -> bool:
    if isinstance(value, bool):
        return value is True
    return str(value).strip().lower() in {"true", "1", "yes"}


def _is_false(value: Any) -> bool:
    if isinstance(value, bool):
        return value is False
    return str(value).strip().lower() in {"false", "0", "no"}


def _parse_utc_timestamp(value: Any) -> bool:
    text = _normalize_text(value)
    if _is_placeholder_text(text):
        return False
    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return False
    return parsed.tzinfo is not None


def _manifest_dir_from_workpack(workpack: dict[str, Any]) -> Path:
    input_paths = _as_dict(workpack.get("input_paths", {}))
    raw = input_paths.get("operator_manifest_dir")
    if raw:
        return _resolve_path(raw)

    for item in _as_list(workpack.get("work_items", [])):
        if not isinstance(item, dict):
            continue
        path = _resolve_path(item.get("manifest_drop_path"))
        if str(path):
            return path.parent
    return REAL_TRIAL_BASELINE_DIR / "manifests"


def _expected_manifest_path(item: dict[str, Any], *, manifest_dir_override: Path | None) -> Path:
    path = _resolve_path(item.get("manifest_drop_path"))
    if manifest_dir_override is None:
        return path
    return (manifest_dir_override / path.name).resolve()


def _json_manifest_count(manifest_dir: Path) -> int:
    if not manifest_dir.is_dir():
        return 0
    return len([path for path in manifest_dir.glob("*.json") if path.is_file()])


def _add_unique(target: list[str], code: str) -> None:
    if code not in target:
        target.append(code)


def _validate_loop(
    loop: dict[str, Any],
    *,
    required_modality: str,
    required_slot_index: int,
    accepted_backfill_action_ids: list[str],
) -> tuple[bool, list[str]]:
    failure_codes: list[str] = []
    loop_id = _normalize_text(loop.get("loop_id"))

    if not loop_id or _is_placeholder_text(loop_id):
        _add_unique(failure_codes, "loop_id_missing_or_placeholder")

    if _normalize_modality(loop.get("modality")) != required_modality:
        _add_unique(failure_codes, "required_modality_mismatch")

    if _normalize_text(loop.get("status")).lower() != "complete":
        _add_unique(failure_codes, "status_not_complete")

    evidence_origin = _normalize_text(loop.get("evidence_origin")).lower()
    if evidence_origin != "real":
        _add_unique(failure_codes, "evidence_origin_not_real")
        if evidence_origin in {"fixture", "synthetic", "simulated", "mock"}:
            _add_unique(failure_codes, "fixture_or_simulated_loop_rejected")

    if not _is_true(loop.get("launch_gate_eligible")):
        _add_unique(failure_codes, "launch_gate_eligible_not_true")

    raw_backfill_slot_index = loop.get("backfill_slot_index")
    if raw_backfill_slot_index in (None, ""):
        _add_unique(failure_codes, "backfill_slot_index_missing")
    else:
        parsed_backfill_slot_index = _to_int(raw_backfill_slot_index, default=0)
        if parsed_backfill_slot_index <= 0:
            _add_unique(failure_codes, "backfill_slot_index_invalid")
        elif required_slot_index > 0 and parsed_backfill_slot_index != required_slot_index:
            _add_unique(failure_codes, "backfill_slot_index_mismatch")

    backfill_action_id = _normalize_text(loop.get("backfill_action_id"))
    if not backfill_action_id or _is_placeholder_text(backfill_action_id):
        _add_unique(failure_codes, "backfill_action_id_missing_or_placeholder")
    elif accepted_backfill_action_ids and backfill_action_id not in set(accepted_backfill_action_ids):
        _add_unique(failure_codes, "backfill_action_id_mismatch")

    for field in REQUIRED_TEXT_FIELDS:
        value = loop.get(field)
        if _is_placeholder_text(value):
            _add_unique(failure_codes, "required_text_field_missing_or_placeholder:%s" % field)
        if field in {"collected_at_utc", "reviewed_at_utc"} and not _parse_utc_timestamp(value):
            _add_unique(failure_codes, "required_timestamp_field_invalid:%s" % field)

    agent_smoke = _normalize_text(loop.get("agent_smoke_result")).lower()
    if agent_smoke in {"not_run", "not-run", "skipped", "skip"}:
        _add_unique(failure_codes, "agent_smoke_result_not_executed")

    for field in REQUIRED_NUMERIC_FIELDS:
        if field not in loop:
            _add_unique(failure_codes, "required_numeric_field_missing:%s" % field)
            continue
        number = _to_float(loop.get(field))
        if number is None:
            _add_unique(failure_codes, "required_numeric_field_invalid:%s" % field)
            continue
        if number < 0:
            _add_unique(failure_codes, "required_numeric_field_negative:%s" % field)
        if field in {"latency_ms", "provider_call_count", "artifact_count"} and number <= 0:
            _add_unique(failure_codes, "required_numeric_field_not_positive:%s" % field)
        if field == "reviewer_edit_distance_pct" and number > 100:
            _add_unique(failure_codes, "reviewer_edit_distance_pct_out_of_range")

    for field in REQUIRED_FALSE_FIELDS:
        if field not in loop or not _is_false(loop.get(field)):
            _add_unique(failure_codes, "required_false_field_not_false:%s" % field)

    for field in TRACE_IDENTITY_FIELDS:
        if _contains_simulated_token(loop.get(field)):
            _add_unique(failure_codes, "fixture_or_simulated_loop_rejected")

    return not failure_codes, failure_codes


def _preflight_item(item: dict[str, Any], *, manifest_dir_override: Path | None) -> dict[str, Any]:
    required_modality = _normalize_modality(item.get("required_modality"))
    slot_index = _to_int(item.get("slot_index"), default=0)
    intake_item_id = _normalize_text(item.get("intake_item_id"))
    accepted_backfill_action_ids = [
        value
        for value in [
            intake_item_id,
            "gl23-slot-%03d-%s" % (slot_index, required_modality) if slot_index > 0 and required_modality else "",
        ]
        if value
    ]
    manifest_path = _expected_manifest_path(item, manifest_dir_override=manifest_dir_override)
    base = {
        "intake_item_id": intake_item_id,
        "required_modality": required_modality,
        "slot_index": slot_index,
        "accepted_backfill_action_ids": accepted_backfill_action_ids,
        "expected_manifest_path": _display_path(manifest_path),
        "accepted_loop_ids": [],
        "ignored_loop_ids": [],
        "failure_codes": [],
        "loop_failures": [],
    }

    if not manifest_path.is_file():
        base["preflight_status"] = "missing"
        base["failure_codes"] = ["manifest_file_missing"]
        return base

    try:
        manifest = _read_json(manifest_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        base["preflight_status"] = "invalid"
        base["failure_codes"] = ["manifest_json_invalid"]
        base["failure_message"] = str(exc)
        return base

    loops = manifest.get("loops")
    if not isinstance(loops, list):
        base["preflight_status"] = "invalid"
        base["failure_codes"] = ["manifest_loops_not_list"]
        return base

    accepted_loop_ids: list[str] = []
    rejected_matching_loop_count = 0
    loop_failures: list[dict[str, Any]] = []
    ignored_loop_ids: list[str] = []
    for index, loop in enumerate(loops, start=1):
        if not isinstance(loop, dict):
            rejected_matching_loop_count += 1
            loop_failures.append(
                {
                    "loop_index": index,
                    "loop_id": "",
                    "failure_codes": ["loop_row_not_object"],
                }
            )
            continue

        loop_id = _normalize_text(loop.get("loop_id")) or "loop-%03d" % index
        if _normalize_modality(loop.get("modality")) != required_modality:
            ignored_loop_ids.append(loop_id)
            loop_failures.append(
                {
                    "loop_index": index,
                    "loop_id": loop_id,
                    "failure_codes": ["non_slot_loop_in_manifest"],
                }
            )
            continue

        is_valid, failure_codes = _validate_loop(
            loop,
            required_modality=required_modality,
            required_slot_index=slot_index,
            accepted_backfill_action_ids=accepted_backfill_action_ids,
        )
        if is_valid:
            accepted_loop_ids.append(loop_id)
        else:
            rejected_matching_loop_count += 1
            loop_failures.append(
                {
                    "loop_index": index,
                    "loop_id": loop_id,
                    "failure_codes": failure_codes,
                }
            )

    failure_codes: list[str] = []
    if not accepted_loop_ids:
        _add_unique(failure_codes, "required_modality_loop_missing")
    if rejected_matching_loop_count > 0:
        _add_unique(failure_codes, "required_modality_loop_invalid")
        for loop_failure in loop_failures:
            for code in _as_list(loop_failure.get("failure_codes", [])):
                _add_unique(failure_codes, str(code))
    if len(accepted_loop_ids) > 1:
        _add_unique(failure_codes, "multiple_required_modality_loops")
    if ignored_loop_ids:
        _add_unique(failure_codes, "manifest_contains_non_slot_loop")
        _add_unique(failure_codes, "non_slot_loop_in_manifest")

    base["accepted_loop_ids"] = accepted_loop_ids
    base["ignored_loop_ids"] = ignored_loop_ids
    base["loop_failures"] = loop_failures
    base["failure_codes"] = failure_codes
    base["preflight_status"] = "valid" if not failure_codes else "invalid"
    return base


def _status_from_counts(*, total: int, invalid: int, missing: int) -> str:
    if total <= 0:
        return STATUS_NOT_REQUIRED
    if invalid > 0:
        return STATUS_INVALID
    if missing > 0:
        return STATUS_PENDING
    return STATUS_READY


def _warning_codes(*, invalid: int, missing: int, accepted: int, total: int, items: list[dict[str, Any]]) -> list[str]:
    warnings: list[str] = []
    if missing > 0:
        warnings.append("real_loop_manifests_missing")
    if invalid > 0:
        warnings.append("real_loop_manifests_invalid")
    if total > 0 and accepted < total:
        warnings.append("real_loop_manifest_preflight_not_ready")
    if missing > 0 or invalid > 0:
        warnings.append("real_loop_slot_gap_action_plan_required")
    for item in items:
        for code in _as_list(item.get("failure_codes", [])):
            if str(code).startswith("fixture_or_simulated_loop_rejected"):
                _add_unique(warnings, "fixture_or_simulated_loop_rejected")
            if str(code) in {"manifest_contains_non_slot_loop", "multiple_required_modality_loops"}:
                _add_unique(warnings, "real_loop_manifest_slot_contamination")
    return warnings


def _target_launch_modalities(workpack: dict[str, Any], items: list[dict[str, Any]]) -> list[str]:
    current_launch_evidence = _as_dict(workpack.get("current_launch_evidence", {}))
    raw_targets = _as_list(current_launch_evidence.get("target_launch_modalities", []))
    targets: list[str] = []
    for value in raw_targets:
        modality = _normalize_modality(value)
        if modality:
            _add_unique(targets, modality)
    if targets:
        return targets

    for item in items:
        modality = _normalize_modality(item.get("required_modality"))
        if modality:
            _add_unique(targets, modality)
    return targets


def _count_by_modality(items: list[dict[str, Any]], *, status: str | None = None) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        if status is not None and str(item.get("preflight_status", "")) != status:
            continue
        modality = _normalize_modality(item.get("required_modality"))
        if not modality:
            modality = "unknown"
        counts[modality] = counts.get(modality, 0) + 1
    return dict(sorted(counts.items()))


def _slot_action(item: dict[str, Any]) -> str:
    status = str(item.get("preflight_status", ""))
    if status == "missing":
        return "drop_real_manifest"
    if status == "invalid":
        return "repair_real_manifest"
    if status == "valid":
        return "ready_for_gl13"
    return "inspect_manifest"


def _build_slot_readiness(items: list[dict[str, Any]]) -> dict[str, Any]:
    valid_items = [item for item in items if item.get("preflight_status") == "valid"]
    missing_items = [item for item in items if item.get("preflight_status") == "missing"]
    invalid_items = [item for item in items if item.get("preflight_status") == "invalid"]
    blocking_items = missing_items + invalid_items
    first_blocking_slot = None
    if blocking_items:
        first = sorted(blocking_items, key=lambda item: _to_int(item.get("slot_index"), default=0))[0]
        first_blocking_slot = {
            "slot_index": _to_int(first.get("slot_index"), default=0),
            "required_modality": _normalize_modality(first.get("required_modality")),
            "preflight_status": str(first.get("preflight_status", "")),
            "expected_manifest_path": str(first.get("expected_manifest_path", "")),
            "failure_codes": _as_list(first.get("failure_codes", [])),
        }

    return {
        "required_slot_count": len(items),
        "ready_slot_count": len(valid_items),
        "missing_slot_count": len(missing_items),
        "invalid_slot_count": len(invalid_items),
        "blocked_slot_count": len(blocking_items),
        "ready_manifest_paths": [str(item.get("expected_manifest_path", "")) for item in valid_items],
        "missing_manifest_paths": [str(item.get("expected_manifest_path", "")) for item in missing_items],
        "invalid_manifest_paths": [str(item.get("expected_manifest_path", "")) for item in invalid_items],
        "first_blocking_slot": first_blocking_slot,
    }


def _build_modality_readiness(workpack: dict[str, Any], items: list[dict[str, Any]]) -> dict[str, Any]:
    target_modalities = _target_launch_modalities(workpack, items)
    required_counts = _count_by_modality(items)
    ready_counts = _count_by_modality(items, status="valid")
    missing_counts = _count_by_modality(items, status="missing")
    invalid_counts = _count_by_modality(items, status="invalid")

    for modality in target_modalities:
        required_counts.setdefault(modality, 0)
        ready_counts.setdefault(modality, 0)
        missing_counts.setdefault(modality, 0)
        invalid_counts.setdefault(modality, 0)

    modality_rows: list[dict[str, Any]] = []
    covered_targets = [modality for modality in target_modalities if int(ready_counts.get(modality, 0)) > 0]
    missing_targets = [modality for modality in target_modalities if int(ready_counts.get(modality, 0)) <= 0]
    all_modalities = sorted(set(required_counts) | set(target_modalities))
    for modality in all_modalities:
        ready_count = int(ready_counts.get(modality, 0))
        is_target = modality in target_modalities
        modality_rows.append(
            {
                "modality": modality,
                "is_target_launch_modality": is_target,
                "required_slot_count": int(required_counts.get(modality, 0)),
                "ready_slot_count": ready_count,
                "missing_slot_count": int(missing_counts.get(modality, 0)),
                "invalid_slot_count": int(invalid_counts.get(modality, 0)),
                "readiness_status": "covered" if ready_count > 0 else "missing",
            }
        )

    return {
        "target_launch_modalities": target_modalities,
        "covered_target_launch_modalities": covered_targets,
        "missing_target_launch_modalities": missing_targets,
        "required_slot_count_by_modality": dict(sorted(required_counts.items())),
        "ready_slot_count_by_modality": dict(sorted(ready_counts.items())),
        "missing_slot_count_by_modality": dict(sorted(missing_counts.items())),
        "invalid_slot_count_by_modality": dict(sorted(invalid_counts.items())),
        "modalities": modality_rows,
    }


def _build_operator_action_plan(items: list[dict[str, Any]], *, manifest_dir: Path) -> dict[str, Any]:
    pending_items = [item for item in items if item.get("preflight_status") != "valid"]
    next_actions = []
    for item in sorted(pending_items, key=lambda value: _to_int(value.get("slot_index"), default=0)):
        next_actions.append(
            {
                "action": _slot_action(item),
                "slot_index": _to_int(item.get("slot_index"), default=0),
                "required_modality": _normalize_modality(item.get("required_modality")),
                "intake_item_id": str(item.get("intake_item_id", "")),
                "expected_manifest_path": str(item.get("expected_manifest_path", "")),
                "accepted_backfill_action_ids": _as_list(item.get("accepted_backfill_action_ids", [])),
                "failure_codes": _as_list(item.get("failure_codes", [])),
            }
        )

    return {
        "status": "action_required" if next_actions else "ready_for_gl13",
        "pending_action_count": len(next_actions),
        "next_actions": next_actions,
        "next_commands": {
            "placeholder_scan": (
                "rg -n \"TEMPLATE_REQUIRED|placeholder|fixture|mock\" "
                + _display_path(manifest_dir)
            ),
            "gl64_preflight": "python -B scripts\\gl64_real_loop_manifest_preflight.py --fail-on-invalid --fail-on-pending",
            "gl13_ingestion": (
                "python -B scripts\\gl13_launch_evidence.py --loop-manifest-dir "
                + _display_path(manifest_dir)
                + " --strict-loop-manifest-contract --no-run-doc-sync --max-evidence-age-hours 0"
            ),
        },
        "policy_reminder": (
            "Do not convert fixture, mock, template, placeholder, or unreviewed loops into "
            "launch_gate_eligible=true evidence."
        ),
    }


def build_preflight_report(
    *,
    workpack: dict[str, Any],
    workpack_path: Path,
    manifest_dir_override: Path | None = None,
) -> dict[str, Any]:
    work_items = [item for item in _as_list(workpack.get("work_items", [])) if isinstance(item, dict)]
    manifest_dir = manifest_dir_override if manifest_dir_override is not None else _manifest_dir_from_workpack(workpack)
    item_results = [
        _preflight_item(item, manifest_dir_override=manifest_dir_override)
        for item in work_items
    ]

    total = len(item_results)
    valid = len([item for item in item_results if item.get("preflight_status") == "valid"])
    invalid = len([item for item in item_results if item.get("preflight_status") == "invalid"])
    missing = len([item for item in item_results if item.get("preflight_status") == "missing"])
    accepted_loops = sum(len(_as_list(item.get("accepted_loop_ids", []))) for item in item_results)
    status = _status_from_counts(total=total, invalid=invalid, missing=missing)
    slot_readiness = _build_slot_readiness(item_results)
    modality_readiness = _build_modality_readiness(workpack, item_results)
    operator_action_plan = _build_operator_action_plan(item_results, manifest_dir=manifest_dir)

    return {
        "schema_version": "real_trial_loop_manifest_preflight.v1",
        "generated_at_utc": _utc_now_iso(),
        "status": status,
        "internal_only": False,
        "launch_gate_policy_unchanged": True,
        "input_paths": {
            "gl63_intake_workpack": _display_path(workpack_path),
            "operator_manifest_dir": _display_path(manifest_dir),
        },
        "counts": {
            "total_intake_item_count": total,
            "submitted_manifest_count": _json_manifest_count(manifest_dir),
            "valid_item_count": valid,
            "invalid_item_count": invalid,
            "missing_item_count": missing,
            "accepted_loop_count": accepted_loops,
            "pending_item_count": missing,
        },
        "warning_codes": _warning_codes(
            invalid=invalid,
            missing=missing,
            accepted=valid,
            total=total,
            items=item_results,
        ),
        "slot_readiness": slot_readiness,
        "modality_readiness": modality_readiness,
        "operator_action_plan": operator_action_plan,
        "manifest_acceptance_contract": {
            "source": "GL-63 operator manifest contract",
            "accepted_status": "valid",
            "accepted_loop_requirements": [
                "exactly one slot loop per expected manifest file",
                "no non-slot or extra loop rows in the slot manifest",
                "status=complete",
                "modality matches GL-63 work item",
                "evidence_origin=real",
                "launch_gate_eligible=true",
                "source_system/source_reference/collected_at_utc present",
                "review_task_id/reviewed_by/reviewed_at_utc present",
                "agent_smoke_result executed",
                "backfill_slot_index matches GL-63 work item",
                "backfill_action_id links to GL-63 or GL-23 intake action",
                "published_without_review=false",
                "critical_secret_or_pii_leak=false",
                "high_severity_incident=false",
            ],
            "post_preflight_command": (
                "python -B scripts\\gl13_launch_evidence.py --loop-manifest-dir "
                + _display_path(manifest_dir)
                + " --strict-loop-manifest-contract --no-run-doc-sync --max-evidence-age-hours 0"
            ),
        },
        "items": item_results,
    }


def render_summary(report: dict[str, Any]) -> str:
    counts = _as_dict(report.get("counts", {}))
    input_paths = _as_dict(report.get("input_paths", {}))
    warnings = _as_list(report.get("warning_codes", []))
    items = _as_list(report.get("items", []))
    contract = _as_dict(report.get("manifest_acceptance_contract", {}))
    slot_readiness = _as_dict(report.get("slot_readiness", {}))
    modality_readiness = _as_dict(report.get("modality_readiness", {}))
    operator_action_plan = _as_dict(report.get("operator_action_plan", {}))
    first_blocking_slot = _as_dict(slot_readiness.get("first_blocking_slot", {}))

    lines = [
        "# Real Trial Loop Manifest Preflight Summary",
        "",
        "- Status: `%s`" % str(report.get("status", "unknown")),
        "- Launch gate policy unchanged: `%s`" % str(report.get("launch_gate_policy_unchanged", False)).lower(),
        "- GL-63 workpack: `%s`" % str(input_paths.get("gl63_intake_workpack", "")),
        "- Manifest directory: `%s`" % str(input_paths.get("operator_manifest_dir", "")),
        "- Valid items: `%s/%s`"
        % (
            str(_to_int(counts.get("valid_item_count"), default=0)),
            str(_to_int(counts.get("total_intake_item_count"), default=0)),
        ),
        "- Missing items: `%s`" % str(_to_int(counts.get("missing_item_count"), default=0)),
        "- Invalid items: `%s`" % str(_to_int(counts.get("invalid_item_count"), default=0)),
        "- Accepted loop rows: `%s`" % str(_to_int(counts.get("accepted_loop_count"), default=0)),
        "",
        "## Slot Readiness",
        "- Required slots: `%s`" % str(_to_int(slot_readiness.get("required_slot_count"), default=0)),
        "- Ready slots: `%s`" % str(_to_int(slot_readiness.get("ready_slot_count"), default=0)),
        "- Blocked slots: `%s`" % str(_to_int(slot_readiness.get("blocked_slot_count"), default=0)),
        "- Missing slot files: `%s`" % str(_to_int(slot_readiness.get("missing_slot_count"), default=0)),
        "- Invalid slot files: `%s`" % str(_to_int(slot_readiness.get("invalid_slot_count"), default=0)),
    ]
    if first_blocking_slot:
        lines.extend(
            [
                "- First blocking slot: `%s` `%s` `%s`"
                % (
                    str(first_blocking_slot.get("slot_index", "")),
                    str(first_blocking_slot.get("required_modality", "")),
                    str(first_blocking_slot.get("expected_manifest_path", "")),
                ),
            ]
        )

    lines.extend(
        [
            "",
            "## Modality Readiness",
            "- Target launch modalities: `%s`"
            % ", ".join(str(item) for item in _as_list(modality_readiness.get("target_launch_modalities", []))),
            "- Covered target modalities: `%s`"
            % (
                ", ".join(str(item) for item in _as_list(modality_readiness.get("covered_target_launch_modalities", [])))
                or "none"
            ),
            "- Missing target modalities: `%s`"
            % (
                ", ".join(str(item) for item in _as_list(modality_readiness.get("missing_target_launch_modalities", [])))
                or "none"
            ),
            "",
            "## Operator Action Plan",
            "- Status: `%s`" % str(operator_action_plan.get("status", "unknown")),
            "- Pending actions: `%s`" % str(_to_int(operator_action_plan.get("pending_action_count"), default=0)),
        ]
    )
    next_actions = _as_list(operator_action_plan.get("next_actions", []))
    if next_actions:
        for action in next_actions:
            if not isinstance(action, dict):
                continue
            lines.append(
                "- `%s` slot=%s modality=%s manifest=%s failures=%s"
                % (
                    str(action.get("action", "")),
                    str(action.get("slot_index", "")),
                    str(action.get("required_modality", "")),
                    str(action.get("expected_manifest_path", "")),
                    ", ".join(str(code) for code in _as_list(action.get("failure_codes", []))) or "none",
                )
            )
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Warning Codes",
        ]
    )
    if warnings:
        lines.extend("- `%s`" % str(item) for item in warnings)
    else:
        lines.append("- none")

    lines.extend(["", "## Item Preflight"])
    if items:
        for item in items:
            if not isinstance(item, dict):
                continue
            failure_codes = _as_list(item.get("failure_codes", []))
            failure_text = ", ".join(str(code) for code in failure_codes) if failure_codes else "none"
            lines.append(
                "- `%s` status=%s modality=%s manifest=%s accepted=%s failures=%s"
                % (
                    str(item.get("intake_item_id", "")),
                    str(item.get("preflight_status", "")),
                    str(item.get("required_modality", "")),
                    str(item.get("expected_manifest_path", "")),
                    str(len(_as_list(item.get("accepted_loop_ids", [])))),
                    failure_text,
                )
            )
    else:
        lines.append("- none")

    lines.extend(["", "## Next Command", "", "```powershell", str(contract.get("post_preflight_command", "")), "```", ""])
    return "\n".join(lines)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Preflight GL-63 operator real-loop manifests before GL-13 evidence ingestion. "
            "This validates manifest readiness without creating or counting real launch evidence."
        )
    )
    parser.add_argument("--workpack", default=str(DEFAULT_WORKPACK_PATH))
    parser.add_argument(
        "--manifest-dir",
        default="",
        help="Optional override for expected manifest directory. Basenames from GL-63 manifest_drop_path are used.",
    )
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH), help='Report output path. Use "-" to skip.')
    parser.add_argument("--summary-output", default=str(DEFAULT_SUMMARY_PATH), help='Summary output path. Use "-" to skip.')
    parser.add_argument("--fail-on-invalid", action="store_true")
    parser.add_argument("--fail-on-pending", action="store_true")
    parser.add_argument("--print-json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    workpack_path = Path(str(args.workpack).strip()).resolve()
    output_path = None if str(args.output).strip() == "-" else Path(str(args.output).strip()).resolve()
    summary_path = None if str(args.summary_output).strip() == "-" else Path(str(args.summary_output).strip()).resolve()
    manifest_dir_override = None
    if str(args.manifest_dir).strip():
        manifest_dir_override = Path(str(args.manifest_dir).strip()).resolve()

    try:
        if not workpack_path.is_file():
            raise ValueError("GL-63 intake workpack path does not exist: %s" % workpack_path)
        workpack = _read_json(workpack_path)
        report = build_preflight_report(
            workpack=workpack,
            workpack_path=workpack_path,
            manifest_dir_override=manifest_dir_override,
        )
        summary = render_summary(report)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print("Real trial loop manifest preflight failed: %s" % exc, file=sys.stderr)
        return 2

    if output_path is not None:
        _write_text(output_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print("Real trial loop manifest preflight report written: %s" % output_path)
    if summary_path is not None:
        _write_text(summary_path, summary)
        print("Real trial loop manifest preflight summary written: %s" % summary_path)

    counts = _as_dict(report.get("counts", {}))
    print(
        "Real trial loop manifest preflight status=%s valid=%s invalid=%s missing=%s"
        % (
            str(report.get("status", "unknown")),
            _to_int(counts.get("valid_item_count"), default=0),
            _to_int(counts.get("invalid_item_count"), default=0),
            _to_int(counts.get("missing_item_count"), default=0),
        )
    )
    if args.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    if bool(args.fail_on_invalid) and _to_int(counts.get("invalid_item_count"), default=0) > 0:
        return 1
    if bool(args.fail_on_pending) and _to_int(counts.get("missing_item_count"), default=0) > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
