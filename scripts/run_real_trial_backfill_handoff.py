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
    / "real-trial-backfill-handoff-report.json"
)
DEFAULT_SUMMARY_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-handoff-summary.md"
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate GL-24 machine-readable backfill handoff queue and closure "
            "acknowledgements from GL-23 intake actions plus GL-12 real-loop submissions."
        )
    )
    parser.add_argument("--intake-actions-report", default=str(DEFAULT_INTAKE_ACTIONS_REPORT_PATH))
    parser.add_argument("--collection-report", default=str(DEFAULT_COLLECTION_REPORT_PATH))
    parser.add_argument(
        "--acknowledgements-report",
        default="",
        help=(
            "Optional operator acknowledgement report JSON path. "
            "When provided, closure transitions require explicit submitted loop linkage "
            "and operator acknowledgement metadata."
        ),
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help='Backfill handoff report output path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--summary-output",
        default=str(DEFAULT_SUMMARY_PATH),
        help='Backfill handoff summary output path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--owner",
        default="controlled-beta-ops",
        help="Queue owner tag for generated handoff items.",
    )
    parser.add_argument(
        "--pending-ack-sla-hours",
        type=float,
        default=24.0,
        help=(
            "SLA threshold (hours) for submission-linked pending-ack queue items. "
            "Items at or above this age are marked as breached."
        ),
    )
    parser.add_argument(
        "--pending-ack-overdue-hours",
        type=float,
        default=72.0,
        help=(
            "Overdue escalation threshold (hours) for submission-linked pending-ack queue items. "
            "Items at or above this age are marked as overdue."
        ),
    )
    parser.add_argument(
        "--now-utc",
        default="",
        help=(
            "Optional UTC timestamp used for SLA aging evaluation. "
            "Defaults to current UTC clock when omitted."
        ),
    )
    parser.add_argument("--print-json", action="store_true")
    parser.add_argument(
        "--fail-on-open",
        action="store_true",
        help="Exit with code 1 when any handoff queue item is still open.",
    )
    parser.add_argument(
        "--fail-on-ack-overdue",
        action="store_true",
        help="Exit with code 1 when any submission-linked pending-ack queue item is overdue.",
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


def _utc_timestamp_to_epoch_seconds(value: Any) -> float | None:
    text = str(value or "").strip()
    if not text:
        return None
    normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.timestamp()


def _epoch_seconds_to_utc_iso(epoch_seconds: float | None) -> str:
    if epoch_seconds is None:
        return ""
    return (
        datetime.fromtimestamp(epoch_seconds, tz=timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _submission_sort_key(item: dict[str, Any]) -> tuple[str, str, str]:
    reviewed = str(item.get("reviewed_at_utc", "")).strip()
    collected = str(item.get("collected_at_utc", "")).strip()
    loop_id = str(item.get("loop_id", "")).strip()
    return (reviewed, collected, loop_id)


def _build_submission_pool(collection_report: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    rows = collection_report.get("collected_real_launch_gate_eligible_loops", [])
    if not isinstance(rows, list):
        rows = []
    buckets: dict[str, list[dict[str, Any]]] = {}
    for raw in rows:
        if not isinstance(raw, dict):
            continue
        modality = str(raw.get("modality", "")).strip().lower()
        if not modality:
            continue
        normalized = {
            "loop_id": str(raw.get("loop_id", "")),
            "modality": modality,
            "source_system": str(raw.get("source_system", "")),
            "source_reference": str(raw.get("source_reference", "")),
            "collected_at_utc": str(raw.get("collected_at_utc", "")),
            "review_task_id": str(raw.get("review_task_id", "")),
            "reviewed_by": str(raw.get("reviewed_by", "")),
            "reviewed_at_utc": str(raw.get("reviewed_at_utc", "")),
            "source_report_path": str(raw.get("source_report_path", "")),
        }
        buckets.setdefault(modality, []).append(normalized)
    for modality in list(buckets.keys()):
        buckets[modality] = sorted(buckets[modality], key=_submission_sort_key)
    return buckets


def _build_acknowledgement_index(
    acknowledgements_report: dict[str, Any] | None,
) -> tuple[dict[str, dict[str, Any]], dict[str, int], list[dict[str, Any]]]:
    if not isinstance(acknowledgements_report, dict):
        return {}, {"input_acknowledgement_count": 0, "valid_acknowledgement_count": 0, "invalid_acknowledgement_count": 0}, []
    rows = acknowledgements_report.get("acknowledgements", [])
    if not isinstance(rows, list):
        rows = []

    acknowledged_by_queue_item: dict[str, dict[str, Any]] = {}
    acknowledged_by_action_id: dict[str, dict[str, Any]] = {}
    invalid_records: list[dict[str, Any]] = []
    valid_row_count = 0

    def _ack_sort_key(row: dict[str, Any]) -> tuple[int, float]:
        epoch = _utc_timestamp_to_epoch_seconds(row.get("acknowledged_at_utc"))
        if epoch is None:
            return (0, -1.0)
        return (1, epoch)

    for raw in rows:
        if not isinstance(raw, dict):
            invalid_records.append({"reason": "row_not_object", "row": raw})
            continue
        queue_item_id = str(raw.get("queue_item_id", "")).strip()
        action_id = str(raw.get("action_id", "")).strip()
        submitted_loop_id = str(raw.get("submitted_loop_id", "")).strip()
        acknowledged_by = str(raw.get("acknowledged_by", "")).strip()
        acknowledged_at_utc = str(raw.get("acknowledged_at_utc", "")).strip()
        if not queue_item_id and not action_id:
            invalid_records.append(
                {
                    "reason": "missing_queue_item_or_action_id",
                    "row": raw,
                }
            )
            continue
        if not submitted_loop_id:
            invalid_records.append(
                {
                    "reason": "missing_submitted_loop_id",
                    "row": raw,
                }
            )
            continue
        if not acknowledged_by:
            invalid_records.append(
                {
                    "reason": "missing_acknowledged_by",
                    "row": raw,
                }
            )
            continue
        if not _is_utc_timestamp(acknowledged_at_utc):
            invalid_records.append(
                {
                    "reason": "invalid_acknowledged_at_utc",
                    "row": raw,
                }
            )
            continue

        normalized = {
            "acknowledgement_id": str(raw.get("acknowledgement_id", "")).strip(),
            "queue_item_id": queue_item_id,
            "action_id": action_id,
            "submitted_loop_id": submitted_loop_id,
            "submitted_modality": str(raw.get("submitted_modality", "")).strip().lower(),
            "acknowledged_by": acknowledged_by,
            "acknowledged_at_utc": acknowledged_at_utc,
            "notes": str(raw.get("notes", "")).strip(),
        }
        valid_row_count += 1

        if queue_item_id:
            existing = acknowledged_by_queue_item.get(queue_item_id)
            if existing is None or _ack_sort_key(normalized) > _ack_sort_key(existing):
                acknowledged_by_queue_item[queue_item_id] = normalized
        if action_id:
            existing = acknowledged_by_action_id.get(action_id)
            if existing is None or _ack_sort_key(normalized) > _ack_sort_key(existing):
                acknowledged_by_action_id[action_id] = normalized

    merged: dict[str, dict[str, Any]] = dict(acknowledged_by_queue_item)
    for action_id, row in acknowledged_by_action_id.items():
        merged.setdefault("action:%s" % action_id, row)

    return (
        merged,
        {
            "input_acknowledgement_count": len(rows),
            "valid_acknowledgement_count": valid_row_count,
            "invalid_acknowledgement_count": len(invalid_records),
        },
        invalid_records,
    )


def _build_handoff_report(
    *,
    intake_actions_report: dict[str, Any],
    collection_report: dict[str, Any],
    acknowledgements_report: dict[str, Any] | None,
    intake_actions_report_path: Path,
    collection_report_path: Path,
    acknowledgements_report_path: Path | None,
    owner: str,
    now_epoch_seconds: float,
    pending_ack_sla_hours: float,
    pending_ack_overdue_hours: float,
) -> dict[str, Any]:
    intake_actions = intake_actions_report.get("actions", [])
    if not isinstance(intake_actions, list):
        intake_actions = []
    submission_pool = _build_submission_pool(collection_report)
    acknowledgement_index, acknowledgement_counts, invalid_acknowledgement_records = _build_acknowledgement_index(
        acknowledgements_report
    )
    queue_items: list[dict[str, Any]] = []
    open_queue_items: list[dict[str, Any]] = []
    pending_ack_queue_items: list[dict[str, Any]] = []
    pending_ack_sla_breached_queue_items: list[dict[str, Any]] = []
    pending_ack_overdue_queue_items: list[dict[str, Any]] = []
    pending_ack_tracking_incomplete_queue_items: list[dict[str, Any]] = []
    closure_acknowledged_count = 0
    submission_linked_pending_ack_count = 0
    pending_ack_within_sla_count = 0
    pending_ack_sla_breached_count = 0
    pending_ack_overdue_count = 0
    pending_ack_missing_reference_timestamp_count = 0

    for index, raw_action in enumerate(intake_actions, start=1):
        if not isinstance(raw_action, dict):
            continue
        slot_index = _to_int(raw_action.get("slot_index"), default=index)
        if slot_index <= 0:
            slot_index = index
        action_id = str(raw_action.get("action_id", "")).strip() or "gl23-slot-%03d" % slot_index
        required_modality = str(raw_action.get("required_modality", "")).strip().lower()
        reason = str(raw_action.get("reason", "")).strip() or "unknown_reason"
        assignee = str(raw_action.get("owner", "")).strip() or owner
        intake_action_status = str(raw_action.get("action_status", "pending")).strip().lower() or "pending"
        queue_item_id = "gl24-queue-%s" % action_id

        submissions_for_modality = submission_pool.get(required_modality, [])
        matched_submission = submissions_for_modality.pop(0) if submissions_for_modality else None
        if matched_submission is not None:
            linked_submission = {
                "loop_id": matched_submission.get("loop_id"),
                "review_task_id": matched_submission.get("review_task_id"),
                "reviewed_by": matched_submission.get("reviewed_by"),
                "reviewed_at_utc": matched_submission.get("reviewed_at_utc"),
                "source_reference": matched_submission.get("source_reference"),
                "source_system": matched_submission.get("source_system"),
                "collected_at_utc": matched_submission.get("collected_at_utc"),
            }
            acknowledgement = acknowledgement_index.get(queue_item_id)
            if acknowledgement is None:
                acknowledgement = acknowledgement_index.get("action:%s" % action_id)
            submitted_loop_id = (
                str(acknowledgement.get("submitted_loop_id", "")).strip() if isinstance(acknowledgement, dict) else ""
            )
            if isinstance(acknowledgement, dict) and submitted_loop_id == str(matched_submission.get("loop_id", "")).strip():
                queue_status = "closure_acknowledged"
                closure_acknowledgement = {
                    "status": "acknowledged",
                    "acknowledgement_source": "submission_plus_operator_acknowledgement",
                    "linked_submission": linked_submission,
                    "operator_acknowledgement": acknowledgement,
                }
                closure_acknowledged_count += 1
            else:
                queue_status = "submission_linked_pending_ack"
                submission_linked_pending_ack_count += 1
                missing_reason = (
                    "Operator acknowledgement missing."
                    if not isinstance(acknowledgement, dict)
                    else "Operator acknowledgement submitted_loop_id does not match linked submission loop_id."
                )
                reviewed_reference = _utc_timestamp_to_epoch_seconds(matched_submission.get("reviewed_at_utc"))
                collected_reference = _utc_timestamp_to_epoch_seconds(matched_submission.get("collected_at_utc"))
                if reviewed_reference is not None:
                    pending_ack_reference_epoch = reviewed_reference
                    pending_ack_reference_type = "reviewed_at_utc"
                    pending_ack_reference_utc = str(matched_submission.get("reviewed_at_utc", "")).strip()
                elif collected_reference is not None:
                    pending_ack_reference_epoch = collected_reference
                    pending_ack_reference_type = "collected_at_utc"
                    pending_ack_reference_utc = str(matched_submission.get("collected_at_utc", "")).strip()
                else:
                    pending_ack_reference_epoch = None
                    pending_ack_reference_type = ""
                    pending_ack_reference_utc = ""

                if pending_ack_reference_epoch is None:
                    pending_ack_sla_state = "missing_reference_timestamp"
                    pending_ack_age_hours = None
                    pending_ack_sla_deadline_utc = ""
                    pending_ack_overdue_deadline_utc = ""
                    pending_ack_missing_reference_timestamp_count += 1
                else:
                    pending_ack_age_hours = max(0.0, (now_epoch_seconds - pending_ack_reference_epoch) / 3600.0)
                    pending_ack_sla_deadline_utc = _epoch_seconds_to_utc_iso(
                        pending_ack_reference_epoch + (pending_ack_sla_hours * 3600.0)
                    )
                    pending_ack_overdue_deadline_utc = _epoch_seconds_to_utc_iso(
                        pending_ack_reference_epoch + (pending_ack_overdue_hours * 3600.0)
                    )
                    if pending_ack_age_hours >= pending_ack_overdue_hours:
                        pending_ack_sla_state = "overdue"
                        pending_ack_overdue_count += 1
                    elif pending_ack_age_hours >= pending_ack_sla_hours:
                        pending_ack_sla_state = "sla_breached"
                        pending_ack_sla_breached_count += 1
                    else:
                        pending_ack_sla_state = "within_sla"
                        pending_ack_within_sla_count += 1

                if pending_ack_sla_state == "overdue":
                    escalation_action = "escalate_immediately"
                elif pending_ack_sla_state == "sla_breached":
                    escalation_action = "notify_owner_and_track_until_acknowledged"
                elif pending_ack_sla_state == "missing_reference_timestamp":
                    escalation_action = "backfill_reference_timestamp_for_sla_tracking"
                else:
                    escalation_action = "none"

                closure_acknowledgement = {
                    "status": "pending_operator_acknowledgement",
                    "missing_reason": missing_reason,
                    "linked_submission": linked_submission,
                    "pending_ack_sla_state": pending_ack_sla_state,
                    "pending_ack_age_hours": (
                        round(float(pending_ack_age_hours), 3) if pending_ack_age_hours is not None else None
                    ),
                    "pending_ack_reference_timestamp_type": pending_ack_reference_type,
                    "pending_ack_reference_timestamp_utc": pending_ack_reference_utc,
                    "pending_ack_sla_deadline_utc": pending_ack_sla_deadline_utc,
                    "pending_ack_overdue_deadline_utc": pending_ack_overdue_deadline_utc,
                    "escalation_action": escalation_action,
                }
                if isinstance(acknowledgement, dict):
                    closure_acknowledgement["operator_acknowledgement"] = acknowledgement
        else:
            queue_status = "open"
            closure_acknowledgement = {
                "status": "pending_submission",
                "missing_reason": "No unmatched launch-gate-eligible real submission available for required modality.",
                "required_modality": required_modality,
            }

        item = {
            "queue_item_id": queue_item_id,
            "action_id": action_id,
            "slot_index": slot_index,
            "required_modality": required_modality,
            "reason": reason,
            "assignee": assignee,
            "owner": owner,
            "intake_action_status": intake_action_status,
            "queue_status": queue_status,
            "title": str(raw_action.get("title", "")).strip(),
            "operator_task": str(raw_action.get("operator_task", "")).strip(),
            "closure_evidence_requirements": raw_action.get("closure_evidence_requirements", {}),
            "closure_acknowledgement": closure_acknowledgement,
        }
        queue_items.append(item)
        if queue_status == "open":
            open_queue_items.append(
                {
                    "queue_item_id": queue_item_id,
                    "action_id": action_id,
                    "slot_index": slot_index,
                    "required_modality": required_modality,
                    "reason": reason,
                    "assignee": assignee,
                    "owner": owner,
                }
            )
        elif queue_status == "submission_linked_pending_ack":
            pending_ack_queue_items.append(
                {
                    "queue_item_id": queue_item_id,
                    "action_id": action_id,
                    "slot_index": slot_index,
                    "required_modality": required_modality,
                    "reason": reason,
                    "assignee": assignee,
                    "owner": owner,
                    "pending_ack_sla_state": str(closure_acknowledgement.get("pending_ack_sla_state", "")),
                    "pending_ack_age_hours": closure_acknowledgement.get("pending_ack_age_hours"),
                    "pending_ack_sla_deadline_utc": str(closure_acknowledgement.get("pending_ack_sla_deadline_utc", "")),
                    "pending_ack_overdue_deadline_utc": str(
                        closure_acknowledgement.get("pending_ack_overdue_deadline_utc", "")
                    ),
                    "escalation_action": str(closure_acknowledgement.get("escalation_action", "")),
                }
            )
            pending_state = str(closure_acknowledgement.get("pending_ack_sla_state", "")).strip().lower()
            if pending_state == "overdue":
                pending_ack_overdue_queue_items.append(pending_ack_queue_items[-1])
            elif pending_state == "sla_breached":
                pending_ack_sla_breached_queue_items.append(pending_ack_queue_items[-1])
            elif pending_state == "missing_reference_timestamp":
                pending_ack_tracking_incomplete_queue_items.append(pending_ack_queue_items[-1])

    total_queue_item_count = len(queue_items)
    open_queue_item_count = len(open_queue_items)
    if total_queue_item_count == 0:
        handoff_status = "HANDOFF_NOT_REQUIRED"
    elif open_queue_item_count > 0:
        handoff_status = "HANDOFF_ACTIONS_PENDING"
    elif submission_linked_pending_ack_count > 0:
        handoff_status = "HANDOFF_OPERATOR_ACK_PENDING"
    elif open_queue_item_count == 0:
        handoff_status = "HANDOFF_CLOSURE_ACKNOWLEDGED"
    else:
        handoff_status = "HANDOFF_ACTIONS_PENDING"

    if submission_linked_pending_ack_count == 0:
        acknowledgement_sla_status = "ACK_SLA_NOT_REQUIRED"
    elif pending_ack_overdue_count > 0:
        acknowledgement_sla_status = "ACK_SLA_OVERDUE_ESCALATION"
    elif pending_ack_sla_breached_count > 0:
        acknowledgement_sla_status = "ACK_SLA_BREACH_PENDING_ACTION"
    elif pending_ack_missing_reference_timestamp_count > 0:
        acknowledgement_sla_status = "ACK_SLA_TRACKING_INCOMPLETE"
    else:
        acknowledgement_sla_status = "ACK_SLA_WITHIN_THRESHOLD"

    launch_gap_snapshot = intake_actions_report.get("launch_gap_snapshot", {})
    if not isinstance(launch_gap_snapshot, dict):
        launch_gap_snapshot = {}
    submission_count_by_modality = {
        modality: len(rows)
        for modality, rows in _build_submission_pool(collection_report).items()
    }

    return {
        "schema_version": "real_trial_backfill_handoff.v1",
        "generated_at_utc": _utc_now_iso(),
        "input_paths": {
            "intake_actions_report": str(intake_actions_report_path),
            "collection_report": str(collection_report_path),
            "acknowledgements_report": str(acknowledgements_report_path) if acknowledgements_report_path else "",
        },
        "handoff_status": handoff_status,
        "owner": owner,
        "queue_item_counts": {
            "total_queue_item_count": total_queue_item_count,
            "open_queue_item_count": open_queue_item_count,
            "submission_linked_pending_ack_count": submission_linked_pending_ack_count,
            "closure_acknowledged_count": closure_acknowledged_count,
        },
        "acknowledgement_snapshot": {
            "input_acknowledgement_count": _to_int(acknowledgement_counts.get("input_acknowledgement_count"), default=0),
            "valid_acknowledgement_count": _to_int(acknowledgement_counts.get("valid_acknowledgement_count"), default=0),
            "invalid_acknowledgement_count": _to_int(
                acknowledgement_counts.get("invalid_acknowledgement_count"), default=0
            ),
            "invalid_acknowledgement_records": invalid_acknowledgement_records,
        },
        "acknowledgement_sla_snapshot": {
            "evaluation_timestamp_utc": _epoch_seconds_to_utc_iso(now_epoch_seconds),
            "pending_ack_sla_hours": float(pending_ack_sla_hours),
            "pending_ack_overdue_hours": float(pending_ack_overdue_hours),
            "acknowledgement_sla_status": acknowledgement_sla_status,
            "pending_ack_within_sla_count": pending_ack_within_sla_count,
            "pending_ack_sla_breached_count": pending_ack_sla_breached_count,
            "pending_ack_overdue_count": pending_ack_overdue_count,
            "pending_ack_missing_reference_timestamp_count": pending_ack_missing_reference_timestamp_count,
            "pending_ack_sla_breached_queue_items": pending_ack_sla_breached_queue_items,
            "pending_ack_overdue_queue_items": pending_ack_overdue_queue_items,
            "pending_ack_tracking_incomplete_queue_items": pending_ack_tracking_incomplete_queue_items,
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
        "submission_snapshot": {
            "launch_gate_eligible_real_submission_count": sum(submission_count_by_modality.values()),
            "launch_gate_eligible_real_submission_count_by_modality": submission_count_by_modality,
        },
        "queue_items": queue_items,
        "open_queue_items": open_queue_items,
        "pending_ack_queue_items": pending_ack_queue_items,
        "pending_ack_sla_breached_queue_items": pending_ack_sla_breached_queue_items,
        "pending_ack_overdue_queue_items": pending_ack_overdue_queue_items,
        "pending_ack_tracking_incomplete_queue_items": pending_ack_tracking_incomplete_queue_items,
    }


def _render_summary(report: dict[str, Any]) -> str:
    queue_item_counts = report.get("queue_item_counts", {})
    if not isinstance(queue_item_counts, dict):
        queue_item_counts = {}
    launch_gap_snapshot = report.get("launch_gap_snapshot", {})
    if not isinstance(launch_gap_snapshot, dict):
        launch_gap_snapshot = {}
    acknowledgement_sla_snapshot = report.get("acknowledgement_sla_snapshot", {})
    if not isinstance(acknowledgement_sla_snapshot, dict):
        acknowledgement_sla_snapshot = {}
    lines = [
        "# Real Trial Backfill Handoff Summary",
        "",
        "- Handoff status: `%s`" % str(report.get("handoff_status", "unknown")),
        "- Queue owner: `%s`" % str(report.get("owner", "")),
        "- Total queue items: `%s`" % str(queue_item_counts.get("total_queue_item_count", 0)),
        "- Open queue items: `%s`" % str(queue_item_counts.get("open_queue_item_count", 0)),
        "- Submission-linked pending-ack items: `%s`"
        % str(queue_item_counts.get("submission_linked_pending_ack_count", 0)),
        "- Closure acknowledged items: `%s`" % str(queue_item_counts.get("closure_acknowledged_count", 0)),
        "- Ack SLA status: `%s`" % str(acknowledgement_sla_snapshot.get("acknowledgement_sla_status", "unknown")),
        "- Ack pending within SLA: `%s`"
        % str(acknowledgement_sla_snapshot.get("pending_ack_within_sla_count", 0)),
        "- Ack SLA breached: `%s`"
        % str(acknowledgement_sla_snapshot.get("pending_ack_sla_breached_count", 0)),
        "- Ack overdue escalation: `%s`"
        % str(acknowledgement_sla_snapshot.get("pending_ack_overdue_count", 0)),
        "- Ack tracking incomplete: `%s`"
        % str(acknowledgement_sla_snapshot.get("pending_ack_missing_reference_timestamp_count", 0)),
        "- Launch-gap missing loops: `%s`"
        % str(launch_gap_snapshot.get("missing_complete_loops_to_threshold", 0)),
        "- Launch-gap missing modalities: `%s`"
        % str(launch_gap_snapshot.get("missing_modalities_to_threshold", 0)),
        "",
        "## Open Queue Items",
    ]
    open_queue_items = report.get("open_queue_items", [])
    if isinstance(open_queue_items, list) and open_queue_items:
        for item in open_queue_items:
            if not isinstance(item, dict):
                continue
            lines.append(
                "- `%s` slot=%s modality=%s reason=%s assignee=%s"
                % (
                    str(item.get("queue_item_id", "")),
                    str(item.get("slot_index", "")),
                    str(item.get("required_modality", "")),
                    str(item.get("reason", "")),
                    str(item.get("assignee", "")),
                )
            )
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Submission Linked Pending Operator Ack",
        ]
    )
    pending_ack_queue_items = report.get("pending_ack_queue_items", [])
    if isinstance(pending_ack_queue_items, list) and pending_ack_queue_items:
        for item in pending_ack_queue_items:
            if not isinstance(item, dict):
                continue
            lines.append(
                "- `%s` slot=%s modality=%s reason=%s assignee=%s"
                % (
                    str(item.get("queue_item_id", "")),
                    str(item.get("slot_index", "")),
                    str(item.get("required_modality", "")),
                    str(item.get("reason", "")),
                    str(item.get("assignee", "")),
                )
            )
    else:
        lines.append("- none")
    lines.append("")
    lines.extend(
        [
            "## Pending Ack SLA Breached Items",
        ]
    )
    pending_ack_sla_breached_queue_items = report.get("pending_ack_sla_breached_queue_items", [])
    if isinstance(pending_ack_sla_breached_queue_items, list) and pending_ack_sla_breached_queue_items:
        for item in pending_ack_sla_breached_queue_items:
            if not isinstance(item, dict):
                continue
            lines.append(
                "- `%s` slot=%s modality=%s age_hours=%s action=%s assignee=%s"
                % (
                    str(item.get("queue_item_id", "")),
                    str(item.get("slot_index", "")),
                    str(item.get("required_modality", "")),
                    str(item.get("pending_ack_age_hours", "")),
                    str(item.get("escalation_action", "")),
                    str(item.get("assignee", "")),
                )
            )
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Pending Ack Overdue Escalation Items",
        ]
    )
    pending_ack_overdue_queue_items = report.get("pending_ack_overdue_queue_items", [])
    if isinstance(pending_ack_overdue_queue_items, list) and pending_ack_overdue_queue_items:
        for item in pending_ack_overdue_queue_items:
            if not isinstance(item, dict):
                continue
            lines.append(
                "- `%s` slot=%s modality=%s age_hours=%s action=%s assignee=%s"
                % (
                    str(item.get("queue_item_id", "")),
                    str(item.get("slot_index", "")),
                    str(item.get("required_modality", "")),
                    str(item.get("pending_ack_age_hours", "")),
                    str(item.get("escalation_action", "")),
                    str(item.get("assignee", "")),
                )
            )
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    intake_actions_report_path = Path(str(args.intake_actions_report).strip()).resolve()
    collection_report_path = Path(str(args.collection_report).strip()).resolve()
    acknowledgements_report_value = str(args.acknowledgements_report).strip()
    acknowledgements_report_path = Path(acknowledgements_report_value).resolve() if acknowledgements_report_value else None
    output_path = None if str(args.output).strip() == "-" else Path(str(args.output).strip()).resolve()
    summary_path = None if str(args.summary_output).strip() == "-" else Path(str(args.summary_output).strip()).resolve()
    owner = str(args.owner).strip() or "controlled-beta-ops"
    pending_ack_sla_hours = float(args.pending_ack_sla_hours)
    pending_ack_overdue_hours = float(args.pending_ack_overdue_hours)
    now_utc_value = str(args.now_utc).strip()

    try:
        if pending_ack_sla_hours <= 0:
            raise ValueError("--pending-ack-sla-hours must be > 0")
        if pending_ack_overdue_hours <= 0:
            raise ValueError("--pending-ack-overdue-hours must be > 0")
        if pending_ack_overdue_hours < pending_ack_sla_hours:
            raise ValueError("--pending-ack-overdue-hours must be >= --pending-ack-sla-hours")
        if now_utc_value and not _is_utc_timestamp(now_utc_value):
            raise ValueError("--now-utc must be a timezone-aware UTC timestamp")
        now_epoch_seconds = (
            _utc_timestamp_to_epoch_seconds(now_utc_value)
            if now_utc_value
            else datetime.now(timezone.utc).timestamp()
        )
        if now_epoch_seconds is None:
            raise ValueError("--now-utc could not be parsed as UTC timestamp")
        if not intake_actions_report_path.is_file():
            raise ValueError("Intake actions report path does not exist: %s" % intake_actions_report_path)
        if not collection_report_path.is_file():
            raise ValueError("Collection report path does not exist: %s" % collection_report_path)
        if acknowledgements_report_path is not None and not acknowledgements_report_path.is_file():
            raise ValueError("Acknowledgements report path does not exist: %s" % acknowledgements_report_path)
        intake_actions_report = _read_json(intake_actions_report_path)
        collection_report = _read_json(collection_report_path)
        acknowledgements_report = _read_json(acknowledgements_report_path) if acknowledgements_report_path else None
        report = _build_handoff_report(
            intake_actions_report=intake_actions_report,
            collection_report=collection_report,
            acknowledgements_report=acknowledgements_report,
            intake_actions_report_path=intake_actions_report_path,
            collection_report_path=collection_report_path,
            acknowledgements_report_path=acknowledgements_report_path,
            owner=owner,
            now_epoch_seconds=now_epoch_seconds,
            pending_ack_sla_hours=pending_ack_sla_hours,
            pending_ack_overdue_hours=pending_ack_overdue_hours,
        )
        summary = _render_summary(report)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print("Real trial backfill handoff generation failed: %s" % exc, file=sys.stderr)
        return 2

    if output_path is not None:
        _write_text(output_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print("Real trial backfill handoff report written: %s" % output_path)
    if summary_path is not None:
        _write_text(summary_path, summary)
        print("Real trial backfill handoff summary written: %s" % summary_path)

    queue_item_counts = report.get("queue_item_counts", {})
    if not isinstance(queue_item_counts, dict):
        queue_item_counts = {}
    print(
        "Real trial backfill handoff status=%s open=%s/%s ack_sla_status=%s ack_overdue=%s"
        % (
            str(report.get("handoff_status", "unknown")),
            _to_int(queue_item_counts.get("open_queue_item_count"), default=0),
            _to_int(queue_item_counts.get("total_queue_item_count"), default=0),
            str(
                (report.get("acknowledgement_sla_snapshot", {}) or {}).get("acknowledgement_sla_status", "unknown")
            ),
            _to_int(
                (report.get("acknowledgement_sla_snapshot", {}) or {}).get("pending_ack_overdue_count"), default=0
            ),
        )
    )
    if args.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    if bool(args.fail_on_open) and _to_int(queue_item_counts.get("open_queue_item_count"), default=0) > 0:
        return 1
    if bool(args.fail_on_ack_overdue) and _to_int(
        (report.get("acknowledgement_sla_snapshot", {}) or {}).get("pending_ack_overdue_count"), default=0
    ) > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
