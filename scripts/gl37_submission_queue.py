from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_THROUGHPUT_REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-throughput-report.json"
)
DEFAULT_OUTPUT_PATH = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-report.json"
)
DEFAULT_SUMMARY_PATH = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-summary.md"
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate GL-37 operator-facing submission queue artifacts from GL-36 "
            "throughput execution-focus diagnostics."
        )
    )
    parser.add_argument("--throughput-report", default=str(DEFAULT_THROUGHPUT_REPORT_PATH))
    parser.add_argument(
        "--previous-queue-report",
        default="",
        help=(
            "Optional previous submission-queue report for cadence comparison. "
            "When omitted, script attempts to read existing --output path."
        ),
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help='Submission queue report output path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--summary-output",
        default=str(DEFAULT_SUMMARY_PATH),
        help='Submission queue summary output path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--owner",
        default="controlled-beta-ops",
        help="Queue owner tag written into queue artifacts.",
    )
    parser.add_argument(
        "--refresh-interval-hours",
        type=float,
        default=24.0,
        help="Expected evidence refresh cadence interval in hours (default: 24).",
    )
    parser.add_argument(
        "--now-utc",
        default="",
        help=(
            "Optional UTC timestamp for deterministic cadence evaluation. "
            "Defaults to current UTC clock when omitted."
        ),
    )
    parser.add_argument("--print-json", action="store_true")
    parser.add_argument(
        "--fail-on-blocked",
        action="store_true",
        help="Exit with code 1 when queue status is QUEUE_BLOCKED_BY_SUBMISSION_ERRORS.",
    )
    parser.add_argument(
        "--fail-on-cadence-due",
        action="store_true",
        help="Exit with code 1 when cadence status is CADENCE_DUE.",
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


def _to_float(value: Any, *, default: float = 0.0) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return float(default)


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


def _normalize_identifier(text: str) -> str:
    raw = str(text or "").strip().lower()
    normalized = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in raw)
    while "--" in normalized:
        normalized = normalized.replace("--", "-")
    return normalized.strip("-_")


def _normalize_actions(rows: Any) -> list[dict[str, Any]]:
    if not isinstance(rows, list):
        return []
    normalized: list[dict[str, Any]] = []
    for raw in rows:
        if not isinstance(raw, dict):
            continue
        slot_index = _to_int(raw.get("backfill_slot_index"), default=0)
        required_modality = str(raw.get("required_modality", "")).strip().lower()
        action_id = str(raw.get("backfill_action_id", "")).strip()
        if not required_modality and slot_index <= 0 and not action_id:
            continue
        normalized.append(
            {
                "backfill_action_id": action_id,
                "backfill_slot_index": slot_index,
                "required_modality": required_modality,
                "reason": str(raw.get("reason", "")).strip() or "pending_template_submission_required",
            }
        )
    normalized.sort(
        key=lambda row: (
            _to_int(row.get("backfill_slot_index"), default=0) <= 0,
            _to_int(row.get("backfill_slot_index"), default=0),
            str(row.get("backfill_action_id", "")),
            str(row.get("required_modality", "")),
        )
    )
    return normalized


def _build_queue_items(
    *,
    actions: list[dict[str, Any]],
    priority_modalities: list[dict[str, Any]],
    queue_status: str,
    owner: str,
) -> tuple[list[dict[str, Any]], dict[str, int], dict[str, int]]:
    modality_priority_rank: dict[str, int] = {}
    for index, row in enumerate(priority_modalities, start=1):
        if not isinstance(row, dict):
            continue
        modality = str(row.get("modality", "")).strip().lower()
        if modality and modality not in modality_priority_rank:
            modality_priority_rank[modality] = index

    blocked = queue_status == "QUEUE_BLOCKED_BY_SUBMISSION_ERRORS"
    pending_counts: dict[str, int] = {}
    blocked_counts: dict[str, int] = {}
    queue_items: list[dict[str, Any]] = []
    for index, row in enumerate(actions, start=1):
        if not isinstance(row, dict):
            continue
        slot_index = _to_int(row.get("backfill_slot_index"), default=0)
        required_modality = str(row.get("required_modality", "")).strip().lower()
        action_id = str(row.get("backfill_action_id", "")).strip()
        queue_item_seed = action_id or (
            "slot-%03d-%s" % (slot_index, required_modality or "unknown")
            if slot_index > 0
            else "idx-%03d-%s" % (index, required_modality or "unknown")
        )
        queue_item_id = "gl37-submission-queue-%s" % (_normalize_identifier(queue_item_seed) or ("idx-%03d" % index))
        queue_item_status = "blocked_by_submission_errors" if blocked else "pending_submission"
        if required_modality:
            if blocked:
                blocked_counts[required_modality] = blocked_counts.get(required_modality, 0) + 1
            else:
                pending_counts[required_modality] = pending_counts.get(required_modality, 0) + 1
        queue_items.append(
            {
                "queue_item_id": queue_item_id,
                "queue_item_status": queue_item_status,
                "owner": owner,
                "priority_rank": modality_priority_rank.get(required_modality, 0),
                "backfill_action_id": action_id,
                "backfill_slot_index": slot_index,
                "required_modality": required_modality,
                "reason": str(row.get("reason", "")).strip(),
            }
        )
    return queue_items, pending_counts, blocked_counts


def _build_cadence(
    *,
    queue_status: str,
    refresh_interval_hours: float,
    now_epoch_seconds: float,
    previous_queue_report: dict[str, Any] | None,
) -> dict[str, Any]:
    if queue_status == "QUEUE_NOT_REQUIRED":
        return {
            "refresh_interval_hours": float(refresh_interval_hours),
            "cadence_status": "CADENCE_NOT_REQUIRED",
            "previous_queue_generated_at_utc": "",
            "next_refresh_due_utc": "",
            "due_in_hours": 0.0,
            "evaluated_at_utc": _epoch_seconds_to_utc_iso(now_epoch_seconds),
        }

    previous_generated_at_utc = ""
    previous_epoch_seconds = None
    if isinstance(previous_queue_report, dict):
        previous_generated_at_utc = str(previous_queue_report.get("generated_at_utc", "")).strip()
        previous_epoch_seconds = _utc_timestamp_to_epoch_seconds(previous_generated_at_utc)

    if previous_epoch_seconds is None:
        next_refresh_due_epoch = now_epoch_seconds + (refresh_interval_hours * 3600.0)
        cadence_status = "CADENCE_BASELINE_INITIALIZED"
    else:
        next_refresh_due_epoch = previous_epoch_seconds + (refresh_interval_hours * 3600.0)
        cadence_status = "CADENCE_DUE" if now_epoch_seconds >= next_refresh_due_epoch else "CADENCE_ON_SCHEDULE"

    due_in_hours = round((next_refresh_due_epoch - now_epoch_seconds) / 3600.0, 3)
    return {
        "refresh_interval_hours": float(refresh_interval_hours),
        "cadence_status": cadence_status,
        "previous_queue_generated_at_utc": previous_generated_at_utc,
        "next_refresh_due_utc": _epoch_seconds_to_utc_iso(next_refresh_due_epoch),
        "due_in_hours": due_in_hours,
        "evaluated_at_utc": _epoch_seconds_to_utc_iso(now_epoch_seconds),
    }


def _build_report(
    *,
    throughput_report: dict[str, Any],
    throughput_report_path: Path,
    previous_queue_report: dict[str, Any] | None,
    previous_queue_report_path: Path | None,
    owner: str,
    refresh_interval_hours: float,
    now_epoch_seconds: float,
) -> dict[str, Any]:
    execution_focus = throughput_report.get("execution_focus", {})
    if not isinstance(execution_focus, dict):
        execution_focus = {}
    action_plan_status = str(execution_focus.get("action_plan_status", "unknown")).strip().upper() or "UNKNOWN"
    action_plan_blockers = execution_focus.get("action_plan_blockers", [])
    if not isinstance(action_plan_blockers, list):
        action_plan_blockers = []
    priority_modalities = execution_focus.get("priority_modalities", [])
    if not isinstance(priority_modalities, list):
        priority_modalities = []
    actions = _normalize_actions(execution_focus.get("recommended_submission_actions", []))
    pending_submission_action_count = _to_int(
        execution_focus.get("pending_submission_action_count", 0),
        default=len(actions),
    )
    recommended_submission_action_count = _to_int(
        execution_focus.get("recommended_submission_action_count", 0),
        default=len(actions),
    )
    if recommended_submission_action_count < len(actions):
        recommended_submission_action_count = len(actions)
    if pending_submission_action_count < len(actions):
        pending_submission_action_count = len(actions)

    if action_plan_status == "ACTION_PLAN_NOT_REQUIRED":
        queue_status = "QUEUE_NOT_REQUIRED"
    elif action_plan_status == "ACTION_PLAN_BLOCKED_BY_SUBMISSION_ERRORS":
        queue_status = "QUEUE_BLOCKED_BY_SUBMISSION_ERRORS"
    elif action_plan_status == "ACTION_PLAN_REBUILD_REQUIRED":
        queue_status = "QUEUE_REBUILD_REQUIRED"
    else:
        queue_status = "QUEUE_ACTIVE"

    queue_items, pending_counts, blocked_counts = _build_queue_items(
        actions=actions,
        priority_modalities=priority_modalities,
        queue_status=queue_status,
        owner=owner,
    )
    if queue_status == "QUEUE_NOT_REQUIRED":
        queue_items = []
        pending_counts = {}
        blocked_counts = {}

    blocked_item_count = len(queue_items) if queue_status == "QUEUE_BLOCKED_BY_SUBMISSION_ERRORS" else 0
    pending_item_count = len(queue_items) if queue_status != "QUEUE_BLOCKED_BY_SUBMISSION_ERRORS" else 0
    cadence = _build_cadence(
        queue_status=queue_status,
        refresh_interval_hours=refresh_interval_hours,
        now_epoch_seconds=now_epoch_seconds,
        previous_queue_report=previous_queue_report,
    )
    warning_codes = throughput_report.get("warning_codes", [])
    if not isinstance(warning_codes, list):
        warning_codes = []
    if queue_status == "QUEUE_BLOCKED_BY_SUBMISSION_ERRORS":
        warning_codes = warning_codes + ["submission_queue_blocked_by_submission_errors"]
    if queue_status in {"QUEUE_ACTIVE", "QUEUE_BLOCKED_BY_SUBMISSION_ERRORS", "QUEUE_REBUILD_REQUIRED"}:
        warning_codes = warning_codes + ["submission_queue_refresh_required_until_threshold_met"]
    warning_codes = list(dict.fromkeys(str(item).strip() for item in warning_codes if str(item).strip()))

    return {
        "schema_version": "real_trial_submission_queue.v1",
        "generated_at_utc": _epoch_seconds_to_utc_iso(now_epoch_seconds),
        "owner": owner,
        "input_paths": {
            "throughput_report": str(throughput_report_path),
            "previous_queue_report": str(previous_queue_report_path) if previous_queue_report_path else "",
        },
        "queue_status": queue_status,
        "warning_codes": warning_codes,
        "queue_summary": {
            "total_item_count": len(queue_items),
            "pending_item_count": pending_item_count,
            "blocked_item_count": blocked_item_count,
            "closed_item_count": 0,
            "pending_item_count_by_modality": pending_counts,
            "blocked_item_count_by_modality": blocked_counts,
            "action_plan_status": action_plan_status,
            "action_plan_blockers": action_plan_blockers,
            "priority_modalities": priority_modalities,
            "pending_submission_action_count": pending_submission_action_count,
            "recommended_submission_action_count": recommended_submission_action_count,
            "throughput_status": str(throughput_report.get("throughput_status", "unknown")),
            "throughput_threshold_met": bool(throughput_report.get("threshold_met", False)),
            "throughput_warning_codes": throughput_report.get("warning_codes", []),
            "submission_consumption_status": str(execution_focus.get("submission_consumption_status", "unknown")),
            "submission_consumption_template_loop_count": _to_int(
                execution_focus.get("submission_consumption_template_loop_count", 0),
                default=0,
            ),
            "submission_consumption_pending_template_loop_count": _to_int(
                execution_focus.get("submission_consumption_pending_template_loop_count", 0),
                default=0,
            ),
            "submission_consumption_invalid_submission_count": _to_int(
                execution_focus.get("submission_consumption_invalid_submission_count", 0),
                default=0,
            ),
            "submission_consumption_unresolved_submission_count": _to_int(
                execution_focus.get("submission_consumption_unresolved_submission_count", 0),
                default=0,
            ),
        },
        "refresh_cadence": cadence,
        "queue_items": queue_items,
    }


def _render_summary(report: dict[str, Any]) -> str:
    queue_summary = report.get("queue_summary", {})
    if not isinstance(queue_summary, dict):
        queue_summary = {}
    refresh_cadence = report.get("refresh_cadence", {})
    if not isinstance(refresh_cadence, dict):
        refresh_cadence = {}
    warning_codes = report.get("warning_codes", [])
    if not isinstance(warning_codes, list):
        warning_codes = []
    queue_items = report.get("queue_items", [])
    if not isinstance(queue_items, list):
        queue_items = []
    lines = [
        "# Real Trial Submission Queue Summary",
        "",
        "- Queue status: `%s`" % str(report.get("queue_status", "unknown")),
        "- Action-plan status: `%s`" % str(queue_summary.get("action_plan_status", "unknown")),
        "- Throughput status: `%s`" % str(queue_summary.get("throughput_status", "unknown")),
        "- Total queue items: `%s`" % str(_to_int(queue_summary.get("total_item_count", 0), default=0)),
        "- Pending queue items: `%s`" % str(_to_int(queue_summary.get("pending_item_count", 0), default=0)),
        "- Blocked queue items: `%s`" % str(_to_int(queue_summary.get("blocked_item_count", 0), default=0)),
        "- Cadence status: `%s`" % str(refresh_cadence.get("cadence_status", "unknown")),
        "- Refresh interval hours: `%s`" % str(_to_float(refresh_cadence.get("refresh_interval_hours", 0.0))),
        "- Next refresh due UTC: `%s`" % str(refresh_cadence.get("next_refresh_due_utc", "")),
        "- Due in hours: `%s`" % str(_to_float(refresh_cadence.get("due_in_hours", 0.0))),
        "",
        "## Warning Codes",
    ]
    if warning_codes:
        for warning_code in warning_codes:
            lines.append("- `%s`" % str(warning_code))
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Queue Items",
        ]
    )
    if queue_items:
        for item in queue_items:
            if not isinstance(item, dict):
                continue
            lines.append(
                "- `%s` status=%s slot=%s modality=%s reason=%s"
                % (
                    str(item.get("queue_item_id", "")),
                    str(item.get("queue_item_status", "")),
                    str(_to_int(item.get("backfill_slot_index", 0), default=0)),
                    str(item.get("required_modality", "")),
                    str(item.get("reason", "")),
                )
            )
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    throughput_report_path = Path(str(args.throughput_report).strip()).resolve()
    output_path = None if str(args.output).strip() == "-" else Path(str(args.output).strip()).resolve()
    summary_path = None if str(args.summary_output).strip() == "-" else Path(str(args.summary_output).strip()).resolve()
    owner = str(args.owner).strip() or "controlled-beta-ops"
    refresh_interval_hours = float(args.refresh_interval_hours)
    now_utc_value = str(args.now_utc).strip()

    try:
        if refresh_interval_hours <= 0:
            raise ValueError("--refresh-interval-hours must be > 0")
        if now_utc_value and not _is_utc_timestamp(now_utc_value):
            raise ValueError("--now-utc must be a timezone-aware UTC timestamp")
        now_epoch_seconds = (
            _utc_timestamp_to_epoch_seconds(now_utc_value)
            if now_utc_value
            else datetime.now(timezone.utc).timestamp()
        )
        if now_epoch_seconds is None:
            raise ValueError("--now-utc could not be parsed as UTC timestamp")
        if not throughput_report_path.is_file():
            raise ValueError("Throughput report path does not exist: %s" % throughput_report_path)
        throughput_report = _read_json(throughput_report_path)

        previous_queue_report_path: Path | None = None
        previous_queue_report: dict[str, Any] | None = None
        previous_arg = str(args.previous_queue_report).strip()
        if previous_arg:
            previous_queue_report_path = Path(previous_arg).resolve()
        elif output_path is not None:
            previous_queue_report_path = output_path
        if previous_queue_report_path is not None and previous_queue_report_path.is_file():
            previous_queue_report = _read_json(previous_queue_report_path)

        report = _build_report(
            throughput_report=throughput_report,
            throughput_report_path=throughput_report_path,
            previous_queue_report=previous_queue_report,
            previous_queue_report_path=previous_queue_report_path if previous_queue_report is not None else None,
            owner=owner,
            refresh_interval_hours=refresh_interval_hours,
            now_epoch_seconds=now_epoch_seconds,
        )
        summary = _render_summary(report)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print("Real trial submission queue generation failed: %s" % exc, file=sys.stderr)
        return 2

    if output_path is not None:
        _write_text(output_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print("Real trial submission queue report written: %s" % output_path)
    if summary_path is not None:
        _write_text(summary_path, summary)
        print("Real trial submission queue summary written: %s" % summary_path)

    queue_summary = report.get("queue_summary", {})
    if not isinstance(queue_summary, dict):
        queue_summary = {}
    refresh_cadence = report.get("refresh_cadence", {})
    if not isinstance(refresh_cadence, dict):
        refresh_cadence = {}
    print(
        "Real trial submission queue status=%s pending=%s blocked=%s cadence=%s"
        % (
            str(report.get("queue_status", "unknown")),
            _to_int(queue_summary.get("pending_item_count", 0), default=0),
            _to_int(queue_summary.get("blocked_item_count", 0), default=0),
            str(refresh_cadence.get("cadence_status", "unknown")),
        )
    )
    if args.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    if bool(args.fail_on_blocked) and str(report.get("queue_status", "")).strip() == "QUEUE_BLOCKED_BY_SUBMISSION_ERRORS":
        return 1
    if bool(args.fail_on_cadence_due) and str(refresh_cadence.get("cadence_status", "")).strip() == "CADENCE_DUE":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
