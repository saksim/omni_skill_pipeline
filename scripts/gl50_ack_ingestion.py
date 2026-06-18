from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CLOSURE_CADENCE_ESCALATIONS_REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalations-report.json"
)
DEFAULT_HANDOFF_REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-handoff-report.json"
)
DEFAULT_OUTPUT_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-ingestion-report.json"
)
DEFAULT_SUMMARY_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-ingestion-summary.md"
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate GL-50 acknowledgement-ingestion diagnostics by mapping GL-49 "
            "closure-cadence escalation rows to GL-24 handoff queue items plus optional "
            "GL-25 raw acknowledgement input records."
        )
    )
    parser.add_argument(
        "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalations-report",
        default=str(DEFAULT_CLOSURE_CADENCE_ESCALATIONS_REPORT_PATH),
    )
    parser.add_argument("--handoff-report", default=str(DEFAULT_HANDOFF_REPORT_PATH))
    parser.add_argument(
        "--acknowledgements-report",
        default="",
        help=(
            "Optional raw acknowledgement input report path (GL-25). "
            "When omitted, script uses `handoff_report.input_paths.acknowledgements_report` if present."
        ),
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help='GL-50 report output path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--summary-output",
        default=str(DEFAULT_SUMMARY_PATH),
        help='GL-50 summary output path. Use "-" to skip writing file.',
    )
    parser.add_argument("--owner", default="controlled-beta-ops")
    parser.add_argument(
        "--fail-on-gap",
        action="store_true",
        help="Exit with code 1 when GL-50 status is not NOT_REQUIRED/READY.",
    )
    parser.add_argument("--print-json", action="store_true")
    return parser.parse_args()


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(_path_for_io(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("JSON root must be an object: %s" % path)
    return payload


def _write_text(path: Path, content: str) -> None:
    io_path = _path_for_io(path)
    io_path.parent.mkdir(parents=True, exist_ok=True)
    io_path.write_text(content, encoding="utf-8")


def _path_for_io(path: Path) -> Path:
    resolved = path.resolve()
    if os.name != "nt":
        return resolved
    text = str(resolved)
    if text.startswith("\\\\?\\"):
        return Path(text)
    if text.startswith("\\\\"):
        return Path("\\\\?\\UNC\\" + text[2:])
    return Path("\\\\?\\" + text)


def _to_int(value: Any, *, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return int(default)


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


def _normalize_modality(value: Any) -> str:
    return str(value or "").strip().lower()


def _parse_slot_index_from_gl46_action_id(action_id: str) -> int:
    text = str(action_id or "").strip()
    matched = re.match(r"^gl46-slot-(\d+)-[a-z0-9_]+$", text)
    if not matched:
        return 0
    return _to_int(matched.group(1), default=0)


def _handoff_indexes(
    handoff_report: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    rows = _normalize_rows(handoff_report.get("queue_items", []))
    by_queue_item_id: dict[str, dict[str, Any]] = {}
    by_action_id: dict[str, dict[str, Any]] = {}
    by_slot_modality: dict[str, dict[str, Any]] = {}
    by_linked_submission_loop_id: dict[str, dict[str, Any]] = {}

    for row in rows:
        queue_item_id = str(row.get("queue_item_id", "")).strip()
        action_id = str(row.get("action_id", "")).strip()
        slot_index = _to_int(row.get("slot_index", 0), default=0)
        required_modality = _normalize_modality(row.get("required_modality", ""))

        closure_ack = row.get("closure_acknowledgement", {})
        linked_submission = closure_ack.get("linked_submission", {}) if isinstance(closure_ack, dict) else {}
        linked_loop_id = str(linked_submission.get("loop_id", "")).strip() if isinstance(linked_submission, dict) else ""

        if queue_item_id and queue_item_id not in by_queue_item_id:
            by_queue_item_id[queue_item_id] = row
        if action_id and action_id not in by_action_id:
            by_action_id[action_id] = row
        if slot_index > 0 and required_modality:
            key = "%s|%s" % (slot_index, required_modality)
            by_slot_modality.setdefault(key, row)
        if linked_loop_id:
            by_linked_submission_loop_id.setdefault(linked_loop_id, row)

    return by_queue_item_id, by_action_id, by_slot_modality, by_linked_submission_loop_id


def _resolve_handoff_row(
    escalation_row: dict[str, Any],
    *,
    by_action_id: dict[str, dict[str, Any]],
    by_slot_modality: dict[str, dict[str, Any]],
    by_linked_submission_loop_id: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any] | None, str]:
    action_id_gl48 = str(escalation_row.get("action_id_gl48", "")).strip()
    required_modality = _normalize_modality(escalation_row.get("required_modality_gl47", ""))
    linked_submission_loop_id = str(escalation_row.get("linked_submission_loop_id_gl47", "")).strip()

    if linked_submission_loop_id and linked_submission_loop_id in by_linked_submission_loop_id:
        return by_linked_submission_loop_id[linked_submission_loop_id], "linked_submission_loop_id"

    translated_action_id = ""
    if action_id_gl48.startswith("gl46-slot-"):
        translated_action_id = "gl23-slot-%s" % action_id_gl48[len("gl46-slot-") :]
        if translated_action_id in by_action_id:
            return by_action_id[translated_action_id], "translated_action_id"

    if action_id_gl48 in by_action_id:
        return by_action_id[action_id_gl48], "action_id_exact"

    slot_index = _parse_slot_index_from_gl46_action_id(action_id_gl48)
    if slot_index > 0 and required_modality:
        slot_key = "%s|%s" % (slot_index, required_modality)
        if slot_key in by_slot_modality:
            return by_slot_modality[slot_key], "slot_index_and_modality"

    return None, "none"


def _normalize_acknowledgements(
    report: dict[str, Any] | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    if not isinstance(report, dict):
        return [], [], {}, {}
    rows = report.get("acknowledgements", [])
    if not isinstance(rows, list):
        return [], [{"reason": "acknowledgements_not_list", "row": rows}], {}, {}

    valid_rows: list[dict[str, Any]] = []
    invalid_rows: list[dict[str, Any]] = []
    by_queue_item_id: dict[str, dict[str, Any]] = {}
    by_action_id: dict[str, dict[str, Any]] = {}

    for index, raw in enumerate(rows, start=1):
        if not isinstance(raw, dict):
            invalid_rows.append({"reason": "row_not_object", "row": raw})
            continue
        queue_item_id = str(raw.get("queue_item_id", "")).strip()
        action_id = str(raw.get("action_id", "")).strip()
        submitted_loop_id = str(raw.get("submitted_loop_id", "")).strip()
        acknowledged_by = str(raw.get("acknowledged_by", "")).strip()
        acknowledged_at_utc = str(raw.get("acknowledged_at_utc", "")).strip()

        if not queue_item_id and not action_id:
            invalid_rows.append({"reason": "missing_queue_item_or_action_id", "row": raw})
            continue
        if not submitted_loop_id:
            invalid_rows.append({"reason": "missing_submitted_loop_id", "row": raw})
            continue
        if not acknowledged_by:
            invalid_rows.append({"reason": "missing_acknowledged_by", "row": raw})
            continue
        if not _is_utc_timestamp(acknowledged_at_utc):
            invalid_rows.append({"reason": "invalid_acknowledged_at_utc", "row": raw})
            continue

        normalized = {
            "_row_key": str(raw.get("acknowledgement_id", "")).strip() or "row-%03d" % index,
            "acknowledgement_id": str(raw.get("acknowledgement_id", "")).strip(),
            "queue_item_id": queue_item_id,
            "action_id": action_id,
            "submitted_loop_id": submitted_loop_id,
            "submitted_modality": _normalize_modality(raw.get("submitted_modality", "")),
            "acknowledged_by": acknowledged_by,
            "acknowledged_at_utc": acknowledged_at_utc,
            "notes": str(raw.get("notes", "")).strip(),
        }
        valid_rows.append(normalized)

        if queue_item_id and queue_item_id not in by_queue_item_id:
            by_queue_item_id[queue_item_id] = normalized
        if action_id and action_id not in by_action_id:
            by_action_id[action_id] = normalized

    return valid_rows, invalid_rows, by_queue_item_id, by_action_id


def _build_ingestion_row(
    *,
    escalation_row: dict[str, Any],
    handoff_row: dict[str, Any] | None,
    handoff_match_strategy: str,
    acknowledgement_input_present: bool,
    ack_by_queue_item_id: dict[str, dict[str, Any]],
    ack_by_action_id: dict[str, dict[str, Any]],
    fallback_owner: str,
    used_ack_row_keys: set[str],
    acknowledgement_source_report_path: str,
) -> tuple[dict[str, Any], str]:
    escalation_item_id_gl49 = str(escalation_row.get("escalation_item_id", "")).strip()
    action_id_gl48 = str(escalation_row.get("action_id_gl48", "")).strip()
    required_modality_gl47 = _normalize_modality(escalation_row.get("required_modality_gl47", ""))
    owner = str(escalation_row.get("owner", "")).strip() or fallback_owner

    handoff_queue_item_id = ""
    handoff_action_id = ""
    handoff_queue_status = ""
    linked_submission_loop_id_gl24 = ""
    linked_submission_review_task_id_gl24 = ""
    linked_submission_reviewed_at_utc_gl24 = ""
    if isinstance(handoff_row, dict):
        handoff_queue_item_id = str(handoff_row.get("queue_item_id", "")).strip()
        handoff_action_id = str(handoff_row.get("action_id", "")).strip()
        handoff_queue_status = _normalize_modality(handoff_row.get("queue_status", ""))
        closure_ack = handoff_row.get("closure_acknowledgement", {})
        linked_submission = closure_ack.get("linked_submission", {}) if isinstance(closure_ack, dict) else {}
        if isinstance(linked_submission, dict):
            linked_submission_loop_id_gl24 = str(linked_submission.get("loop_id", "")).strip()
            linked_submission_review_task_id_gl24 = str(linked_submission.get("review_task_id", "")).strip()
            linked_submission_reviewed_at_utc_gl24 = str(linked_submission.get("reviewed_at_utc", "")).strip()

    ack_record: dict[str, Any] | None = None
    acknowledgement_match_strategy = "none"
    if isinstance(handoff_row, dict):
        if handoff_queue_item_id and handoff_queue_item_id in ack_by_queue_item_id:
            ack_record = ack_by_queue_item_id[handoff_queue_item_id]
            acknowledgement_match_strategy = "queue_item_id"
        elif handoff_action_id and handoff_action_id in ack_by_action_id:
            ack_record = ack_by_action_id[handoff_action_id]
            acknowledgement_match_strategy = "action_id"

    state = ""
    row_status = "open"
    loop_matches = False
    if not acknowledgement_input_present:
        state = "ack_input_missing"
    elif not isinstance(handoff_row, dict):
        state = "missing_handoff_queue_item"
    elif ack_record is None:
        state = "ack_missing"
    else:
        if linked_submission_loop_id_gl24:
            ack_loop_id = str(ack_record.get("submitted_loop_id", "")).strip()
            loop_matches = ack_loop_id == linked_submission_loop_id_gl24
            if loop_matches:
                state = "ack_valid_linked"
                row_status = "closed"
            else:
                state = "ack_loop_mismatch"
        else:
            state = "ack_present_submission_unlinked"

    if isinstance(ack_record, dict):
        used_ack_row_keys.add(str(ack_record.get("_row_key", "")).strip())

    row = {
        "acknowledgement_ingestion_item_id": "gl50-ack-ingestion-%s"
        % (action_id_gl48 or escalation_item_id_gl49 or "unbound"),
        "acknowledgement_ingestion_item_status": row_status,
        "acknowledgement_ingestion_state": state,
        "owner": owner,
        "escalation_item_id_gl49": escalation_item_id_gl49,
        "action_id_gl48": action_id_gl48,
        "required_modality_gl47": required_modality_gl47,
        "handoff_match_strategy_gl24": handoff_match_strategy,
        "handoff_queue_item_id_gl24": handoff_queue_item_id,
        "handoff_action_id_gl24": handoff_action_id,
        "handoff_queue_status_gl24": handoff_queue_status,
        "linked_submission_loop_id_gl24": linked_submission_loop_id_gl24,
        "linked_submission_review_task_id_gl24": linked_submission_review_task_id_gl24,
        "linked_submission_reviewed_at_utc_gl24": linked_submission_reviewed_at_utc_gl24,
        "acknowledgement_match_strategy_gl25": acknowledgement_match_strategy,
        "acknowledgement_id_gl25": str(ack_record.get("acknowledgement_id", "")).strip()
        if isinstance(ack_record, dict)
        else "",
        "acknowledged_by_gl25": str(ack_record.get("acknowledged_by", "")).strip()
        if isinstance(ack_record, dict)
        else "",
        "acknowledged_at_utc_gl25": str(ack_record.get("acknowledged_at_utc", "")).strip()
        if isinstance(ack_record, dict)
        else "",
        "acknowledged_submitted_loop_id_gl25": str(ack_record.get("submitted_loop_id", "")).strip()
        if isinstance(ack_record, dict)
        else "",
        "acknowledgement_loop_matches_linked_submission": loop_matches,
        "acknowledgement_source_report_path_gl25": acknowledgement_source_report_path,
    }
    return row, state


def _state_sort_key(state: str) -> int:
    normalized = str(state or "").strip().lower()
    order = {
        "missing_handoff_queue_item": 0,
        "ack_input_missing": 1,
        "ack_missing": 2,
        "ack_loop_mismatch": 3,
        "ack_present_submission_unlinked": 4,
        "ack_valid_linked": 5,
    }
    return order.get(normalized, 99)


def _build_status(
    *,
    total_item_count: int,
    acknowledgement_input_present: bool,
    valid_acknowledgement_count: int,
    open_item_count: int,
) -> str:
    if total_item_count <= 0:
        return "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_NOT_REQUIRED"
    if not acknowledgement_input_present:
        return "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_INPUT_MISSING"
    if valid_acknowledgement_count <= 0:
        return "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_INPUT_INVALID"
    if open_item_count > 0:
        return "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_ACTION_REQUIRED"
    return "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_READY"


def _build_report(
    *,
    escalation_report: dict[str, Any],
    escalation_report_path: Path,
    handoff_report: dict[str, Any],
    handoff_report_path: Path,
    acknowledgement_report: dict[str, Any] | None,
    acknowledgement_report_path: Path | None,
    owner: str,
) -> dict[str, Any]:
    escalation_rows = _normalize_rows(
        escalation_report.get("followup_resolution_escalation_action_plan_closure_cadence_escalation_rows", [])
    )
    handoff_by_queue_item_id, handoff_by_action_id, handoff_by_slot_modality, handoff_by_linked_submission_loop = (
        _handoff_indexes(handoff_report)
    )

    valid_ack_rows, invalid_ack_rows, ack_by_queue_item_id, ack_by_action_id = _normalize_acknowledgements(
        acknowledgement_report
    )
    acknowledgement_input_present = acknowledgement_report_path is not None
    acknowledgement_input_path = str(acknowledgement_report_path) if acknowledgement_report_path else ""

    used_ack_row_keys: set[str] = set()
    rows: list[dict[str, Any]] = []
    state_counts: dict[str, int] = {}

    for escalation_row in escalation_rows:
        handoff_row, handoff_match_strategy = _resolve_handoff_row(
            escalation_row,
            by_action_id=handoff_by_action_id,
            by_slot_modality=handoff_by_slot_modality,
            by_linked_submission_loop_id=handoff_by_linked_submission_loop,
        )
        row, state = _build_ingestion_row(
            escalation_row=escalation_row,
            handoff_row=handoff_row,
            handoff_match_strategy=handoff_match_strategy,
            acknowledgement_input_present=acknowledgement_input_present,
            ack_by_queue_item_id=ack_by_queue_item_id,
            ack_by_action_id=ack_by_action_id,
            fallback_owner=owner,
            used_ack_row_keys=used_ack_row_keys,
            acknowledgement_source_report_path=acknowledgement_input_path,
        )
        rows.append(row)
        state_counts[state] = state_counts.get(state, 0) + 1

    rows.sort(
        key=lambda row: (
            _state_sort_key(str(row.get("acknowledgement_ingestion_state", ""))),
            str(row.get("required_modality_gl47", "")),
            str(row.get("action_id_gl48", "")),
            str(row.get("acknowledgement_ingestion_item_id", "")),
        )
    )

    unreferenced_acknowledgement_records = [
        {
            "acknowledgement_id": str(item.get("acknowledgement_id", "")).strip(),
            "queue_item_id": str(item.get("queue_item_id", "")).strip(),
            "action_id": str(item.get("action_id", "")).strip(),
            "submitted_loop_id": str(item.get("submitted_loop_id", "")).strip(),
            "acknowledged_by": str(item.get("acknowledged_by", "")).strip(),
            "acknowledged_at_utc": str(item.get("acknowledged_at_utc", "")).strip(),
        }
        for item in valid_ack_rows
        if str(item.get("_row_key", "")).strip() not in used_ack_row_keys
    ]

    total_item_count = len(rows)
    open_item_count = sum(
        1
        for row in rows
        if str(row.get("acknowledgement_ingestion_item_status", "")).strip().lower() == "open"
    )
    closed_item_count = max(0, total_item_count - open_item_count)

    warning_codes: list[str] = []
    if total_item_count > 0 and open_item_count > 0:
        warning_codes.append("open_action_plan_closure_cadence_escalation_acknowledgement_ingestion_items_present")
    if total_item_count > 0 and not acknowledgement_input_present:
        warning_codes.append("acknowledgement_input_missing")
    if acknowledgement_input_present and total_item_count > 0 and len(valid_ack_rows) <= 0:
        warning_codes.append("no_valid_acknowledgement_records")
    if len(invalid_ack_rows) > 0:
        warning_codes.append("invalid_acknowledgement_records_present")
    if _to_int(state_counts.get("missing_handoff_queue_item", 0), default=0) > 0:
        warning_codes.append("escalation_rows_missing_handoff_queue_item")
    if _to_int(state_counts.get("ack_missing", 0), default=0) > 0:
        warning_codes.append("escalation_rows_missing_acknowledgement_record")
    if _to_int(state_counts.get("ack_loop_mismatch", 0), default=0) > 0:
        warning_codes.append("escalation_rows_acknowledgement_loop_mismatch")
    if len(unreferenced_acknowledgement_records) > 0:
        warning_codes.append("unreferenced_acknowledgement_records_present")
    escalation_warning_codes = escalation_report.get("warning_codes", [])
    if isinstance(escalation_warning_codes, list):
        warning_codes.extend(str(item).strip() for item in escalation_warning_codes if str(item).strip())
    warning_codes = _unique_preserve_order(warning_codes)

    status = _build_status(
        total_item_count=total_item_count,
        acknowledgement_input_present=acknowledgement_input_present,
        valid_acknowledgement_count=len(valid_ack_rows),
        open_item_count=open_item_count,
    )

    owner_counts: dict[str, dict[str, int]] = {}
    for row in rows:
        owner_key = str(row.get("owner", "")).strip() or "unassigned"
        state = str(row.get("acknowledgement_ingestion_state", "")).strip().lower()
        bucket = owner_counts.setdefault(
            owner_key,
            {
                "total_item_count": 0,
                "open_item_count": 0,
                "closed_item_count": 0,
                "ack_missing_item_count": 0,
                "ack_loop_mismatch_item_count": 0,
                "missing_handoff_queue_item_count": 0,
            },
        )
        bucket["total_item_count"] += 1
        if str(row.get("acknowledgement_ingestion_item_status", "")).strip().lower() == "open":
            bucket["open_item_count"] += 1
        else:
            bucket["closed_item_count"] += 1
        if state == "ack_missing":
            bucket["ack_missing_item_count"] += 1
        elif state == "ack_loop_mismatch":
            bucket["ack_loop_mismatch_item_count"] += 1
        elif state == "missing_handoff_queue_item":
            bucket["missing_handoff_queue_item_count"] += 1

    counts = {
        "total_item_count": total_item_count,
        "open_item_count": open_item_count,
        "closed_item_count": closed_item_count,
        "escalation_rows_with_acknowledgement_record_count": _to_int(
            state_counts.get("ack_valid_linked", 0),
            default=0,
        )
        + _to_int(state_counts.get("ack_loop_mismatch", 0), default=0)
        + _to_int(state_counts.get("ack_present_submission_unlinked", 0), default=0),
        "escalation_rows_with_matching_ack_loop_count": _to_int(
            state_counts.get("ack_valid_linked", 0),
            default=0,
        ),
        "escalation_rows_with_mismatched_ack_loop_count": _to_int(
            state_counts.get("ack_loop_mismatch", 0),
            default=0,
        ),
        "escalation_rows_missing_acknowledgement_record_count": _to_int(
            state_counts.get("ack_missing", 0),
            default=0,
        ),
        "escalation_rows_without_handoff_queue_item_count": _to_int(
            state_counts.get("missing_handoff_queue_item", 0),
            default=0,
        ),
        "unreferenced_acknowledgement_record_count": len(unreferenced_acknowledgement_records),
    }

    return {
        "schema_version": "real_trial_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion.v1",
        "generated_at_utc": _utc_now_iso(),
        "owner": owner,
        "input_paths": {
            "submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_report": str(
                escalation_report_path
            ),
            "handoff_report": str(handoff_report_path),
            "acknowledgements_report": acknowledgement_input_path,
        },
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_status_gl49": str(
            escalation_report.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_status",
                "unknown",
            )
        ),
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_status": status,
        "warning_codes": warning_codes,
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_counts": counts,
        "owner_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_counts": owner_counts,
        "acknowledgement_input_snapshot": {
            "input_present": acknowledgement_input_present,
            "input_path": acknowledgement_input_path,
            "input_acknowledgement_count": len(valid_ack_rows) + len(invalid_ack_rows),
            "valid_acknowledgement_count": len(valid_ack_rows),
            "invalid_acknowledgement_count": len(invalid_ack_rows),
            "invalid_acknowledgement_records": invalid_ack_rows,
            "unreferenced_acknowledgement_records": unreferenced_acknowledgement_records,
        },
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_rows": rows,
    }


def _render_summary(report: dict[str, Any]) -> str:
    counts = report.get(
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_counts",
        {},
    )
    if not isinstance(counts, dict):
        counts = {}
    warnings = report.get("warning_codes", [])
    if not isinstance(warnings, list):
        warnings = []
    snapshot = report.get("acknowledgement_input_snapshot", {})
    if not isinstance(snapshot, dict):
        snapshot = {}
    rows = report.get(
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_rows",
        [],
    )
    if not isinstance(rows, list):
        rows = []

    lines = [
        "# Real Trial Submission Queue Follow-Up Resolution Escalation Action Plan Closure Cadence Escalation Acknowledgement Ingestion Summary",
        "",
        "- GL-49 status: `%s`"
        % str(
            report.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_status_gl49",
                "unknown",
            )
        ),
        "- GL-50 status: `%s`"
        % str(
            report.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_status",
                "unknown",
            )
        ),
        "- Total ingestion items: `%s`" % str(_to_int(counts.get("total_item_count", 0), default=0)),
        "- Open ingestion items: `%s`" % str(_to_int(counts.get("open_item_count", 0), default=0)),
        "- Closed ingestion items: `%s`" % str(_to_int(counts.get("closed_item_count", 0), default=0)),
        "- Acknowledgement input present: `%s`" % str(bool(snapshot.get("input_present", False))).lower(),
        "- Acknowledgement input rows: `%s`"
        % str(_to_int(snapshot.get("input_acknowledgement_count", 0), default=0)),
        "- Valid acknowledgement rows: `%s`"
        % str(_to_int(snapshot.get("valid_acknowledgement_count", 0), default=0)),
        "- Invalid acknowledgement rows: `%s`"
        % str(_to_int(snapshot.get("invalid_acknowledgement_count", 0), default=0)),
        "",
        "## Warning Codes",
    ]
    if warnings:
        for warning in warnings:
            lines.append("- `%s`" % str(warning))
    else:
        lines.append("- none")

    lines.extend(["", "## Ingestion Rows"])
    if rows:
        for row in rows:
            if not isinstance(row, dict):
                continue
            lines.append(
                "- `%s` state=%s status=%s action=%s modality=%s queue_item=%s"
                % (
                    str(row.get("acknowledgement_ingestion_item_id", "")),
                    str(row.get("acknowledgement_ingestion_state", "")),
                    str(row.get("acknowledgement_ingestion_item_status", "")),
                    str(row.get("action_id_gl48", "")),
                    str(row.get("required_modality_gl47", "")),
                    str(row.get("handoff_queue_item_id_gl24", "")),
                )
            )
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    escalation_report_path = Path(
        str(
            args.submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_report
        ).strip()
    ).resolve()
    handoff_report_path = Path(str(args.handoff_report).strip()).resolve()
    output_path = None if str(args.output).strip() == "-" else Path(str(args.output).strip()).resolve()
    summary_path = None if str(args.summary_output).strip() == "-" else Path(str(args.summary_output).strip()).resolve()
    owner = str(args.owner).strip() or "controlled-beta-ops"

    try:
        if not escalation_report_path.is_file():
            raise ValueError("GL-49 escalation report path does not exist: %s" % escalation_report_path)
        if not handoff_report_path.is_file():
            raise ValueError("GL-24 handoff report path does not exist: %s" % handoff_report_path)

        escalation_report = _read_json(escalation_report_path)
        handoff_report = _read_json(handoff_report_path)

        acknowledgements_report_path: Path | None = None
        acknowledgements_report: dict[str, Any] | None = None

        explicit_ack_path = str(args.acknowledgements_report).strip()
        if explicit_ack_path:
            acknowledgements_report_path = Path(explicit_ack_path).resolve()
        else:
            handoff_input_paths = handoff_report.get("input_paths", {})
            if isinstance(handoff_input_paths, dict):
                handoff_ack_path = str(handoff_input_paths.get("acknowledgements_report", "")).strip()
                if handoff_ack_path:
                    acknowledgements_report_path = Path(handoff_ack_path).resolve()

        if acknowledgements_report_path is not None:
            if not acknowledgements_report_path.is_file():
                raise ValueError("GL-25 acknowledgement report path does not exist: %s" % acknowledgements_report_path)
            acknowledgements_report = _read_json(acknowledgements_report_path)

        report = _build_report(
            escalation_report=escalation_report,
            escalation_report_path=escalation_report_path,
            handoff_report=handoff_report,
            handoff_report_path=handoff_report_path,
            acknowledgement_report=acknowledgements_report,
            acknowledgement_report_path=acknowledgements_report_path,
            owner=owner,
        )
        summary = _render_summary(report)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(
            "Real trial submission queue follow-up resolution escalation action-plan closure cadence escalation acknowledgement ingestion generation failed: %s"
            % exc,
            file=sys.stderr,
        )
        return 2

    if output_path is not None:
        _write_text(output_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print(
            "Real trial submission queue follow-up resolution escalation action-plan closure cadence escalation acknowledgement ingestion report written: %s"
            % output_path
        )
    if summary_path is not None:
        _write_text(summary_path, summary)
        print(
            "Real trial submission queue follow-up resolution escalation action-plan closure cadence escalation acknowledgement ingestion summary written: %s"
            % summary_path
        )

    counts = report.get(
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_counts",
        {},
    )
    if not isinstance(counts, dict):
        counts = {}
    print(
        "Real trial submission queue follow-up resolution escalation action-plan closure cadence escalation acknowledgement ingestion status=%s open=%s mismatched=%s missing_ack=%s"
        % (
            str(
                report.get(
                    "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_status",
                    "unknown",
                )
            ),
            _to_int(counts.get("open_item_count", 0), default=0),
            _to_int(counts.get("escalation_rows_with_mismatched_ack_loop_count", 0), default=0),
            _to_int(counts.get("escalation_rows_missing_acknowledgement_record_count", 0), default=0),
        )
    )

    if args.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    if bool(args.fail_on_gap) and str(
        report.get(
            "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_status",
            "",
        )
    ).strip().upper() not in {
        "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_NOT_REQUIRED",
        "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_READY",
    }:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
