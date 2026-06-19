from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HANDOFF_REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-handoff-report.json"
)
DEFAULT_OUTPUT_PATH = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-handoff-escalations-report.json"
)
DEFAULT_SUMMARY_PATH = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-handoff-escalations-summary.md"
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate GL-27 operator-facing escalation exports for "
            "submission-linked pending-ack handoff cohorts."
        )
    )
    parser.add_argument("--handoff-report", default=str(DEFAULT_HANDOFF_REPORT_PATH))
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help='Escalation report output path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--summary-output",
        default=str(DEFAULT_SUMMARY_PATH),
        help='Escalation summary output path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--owner",
        default="controlled-beta-ops",
        help="Escalation owner tag written into exported escalation items.",
    )
    parser.add_argument(
        "--fail-on-overdue",
        action="store_true",
        help="Exit with code 1 when overdue escalation items exist.",
    )
    parser.add_argument(
        "--fail-on-breached",
        action="store_true",
        help="Exit with code 1 when SLA-breached escalation items exist.",
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


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_escalation_items(
    rows: Any,
    *,
    owner: str,
    severity: str,
) -> list[dict[str, Any]]:
    if not isinstance(rows, list):
        return []
    normalized: list[dict[str, Any]] = []
    for raw in rows:
        if not isinstance(raw, dict):
            continue
        queue_item_id = str(raw.get("queue_item_id", "")).strip()
        if not queue_item_id:
            continue
        normalized.append(
            {
                "queue_item_id": queue_item_id,
                "action_id": str(raw.get("action_id", "")).strip(),
                "slot_index": _to_int(raw.get("slot_index"), default=0),
                "required_modality": str(raw.get("required_modality", "")).strip().lower(),
                "reason": str(raw.get("reason", "")).strip(),
                "assignee": str(raw.get("assignee", "")).strip(),
                "owner": str(raw.get("owner", "")).strip() or owner,
                "pending_ack_age_hours": _to_float(raw.get("pending_ack_age_hours")),
                "pending_ack_sla_deadline_utc": str(raw.get("pending_ack_sla_deadline_utc", "")).strip(),
                "pending_ack_overdue_deadline_utc": str(raw.get("pending_ack_overdue_deadline_utc", "")).strip(),
                "escalation_action": str(raw.get("escalation_action", "")).strip(),
                "escalation_severity": severity,
            }
        )
    return normalized


def _build_report(
    *,
    handoff_report: dict[str, Any],
    handoff_report_path: Path,
    owner: str,
) -> dict[str, Any]:
    handoff_status = str(handoff_report.get("handoff_status", "unknown"))
    acknowledgement_sla_snapshot = handoff_report.get("acknowledgement_sla_snapshot", {})
    if not isinstance(acknowledgement_sla_snapshot, dict):
        acknowledgement_sla_snapshot = {}

    breached_items = _normalize_escalation_items(
        handoff_report.get("pending_ack_sla_breached_queue_items", []),
        owner=owner,
        severity="sla_breached",
    )
    overdue_items = _normalize_escalation_items(
        handoff_report.get("pending_ack_overdue_queue_items", []),
        owner=owner,
        severity="overdue",
    )
    tracking_incomplete_items = _normalize_escalation_items(
        handoff_report.get("pending_ack_tracking_incomplete_queue_items", []),
        owner=owner,
        severity="tracking_incomplete",
    )
    pending_ack_items = _normalize_escalation_items(
        handoff_report.get("pending_ack_queue_items", []),
        owner=owner,
        severity="pending_ack",
    )

    breached_count = len(breached_items)
    overdue_count = len(overdue_items)
    tracking_incomplete_count = len(tracking_incomplete_items)
    total_escalation_count = breached_count + overdue_count + tracking_incomplete_count

    if overdue_count > 0:
        escalation_status = "ESCALATION_OVERDUE_ACTION_REQUIRED"
    elif breached_count > 0:
        escalation_status = "ESCALATION_BREACH_ACTION_REQUIRED"
    elif tracking_incomplete_count > 0:
        escalation_status = "ESCALATION_TRACKING_INCOMPLETE"
    else:
        escalation_status = "ESCALATION_NOT_REQUIRED"

    return {
        "schema_version": "real_trial_backfill_handoff_escalations.v1",
        "generated_at_utc": _utc_now_iso(),
        "input_paths": {
            "handoff_report": str(handoff_report_path),
        },
        "owner": owner,
        "handoff_status": handoff_status,
        "acknowledgement_sla_status": str(acknowledgement_sla_snapshot.get("acknowledgement_sla_status", "unknown")),
        "escalation_status": escalation_status,
        "escalation_counts": {
            "total_escalation_item_count": total_escalation_count,
            "sla_breached_item_count": breached_count,
            "overdue_item_count": overdue_count,
            "tracking_incomplete_item_count": tracking_incomplete_count,
            "pending_ack_queue_item_count": len(pending_ack_items),
        },
        "escalation_exports": {
            "sla_breached_items": breached_items,
            "overdue_items": overdue_items,
            "tracking_incomplete_items": tracking_incomplete_items,
        },
    }


def _render_summary(report: dict[str, Any]) -> str:
    counts = report.get("escalation_counts", {})
    if not isinstance(counts, dict):
        counts = {}
    exports = report.get("escalation_exports", {})
    if not isinstance(exports, dict):
        exports = {}
    lines = [
        "# Real Trial Backfill Handoff Escalations Summary",
        "",
        "- Handoff status: `%s`" % str(report.get("handoff_status", "unknown")),
        "- Ack SLA status: `%s`" % str(report.get("acknowledgement_sla_status", "unknown")),
        "- Escalation status: `%s`" % str(report.get("escalation_status", "unknown")),
        "- Total escalation items: `%s`" % str(counts.get("total_escalation_item_count", 0)),
        "- SLA-breached items: `%s`" % str(counts.get("sla_breached_item_count", 0)),
        "- Overdue items: `%s`" % str(counts.get("overdue_item_count", 0)),
        "- Tracking-incomplete items: `%s`" % str(counts.get("tracking_incomplete_item_count", 0)),
        "",
        "## Overdue Escalations",
    ]
    overdue_items = exports.get("overdue_items", [])
    if isinstance(overdue_items, list) and overdue_items:
        for item in overdue_items:
            if not isinstance(item, dict):
                continue
            lines.append(
                "- `%s` slot=%s modality=%s assignee=%s action=%s"
                % (
                    str(item.get("queue_item_id", "")),
                    str(item.get("slot_index", "")),
                    str(item.get("required_modality", "")),
                    str(item.get("assignee", "")),
                    str(item.get("escalation_action", "")),
                )
            )
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## SLA-Breached Escalations",
        ]
    )
    breached_items = exports.get("sla_breached_items", [])
    if isinstance(breached_items, list) and breached_items:
        for item in breached_items:
            if not isinstance(item, dict):
                continue
            lines.append(
                "- `%s` slot=%s modality=%s assignee=%s action=%s"
                % (
                    str(item.get("queue_item_id", "")),
                    str(item.get("slot_index", "")),
                    str(item.get("required_modality", "")),
                    str(item.get("assignee", "")),
                    str(item.get("escalation_action", "")),
                )
            )
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    handoff_report_path = Path(str(args.handoff_report).strip()).resolve()
    output_path = None if str(args.output).strip() == "-" else Path(str(args.output).strip()).resolve()
    summary_path = None if str(args.summary_output).strip() == "-" else Path(str(args.summary_output).strip()).resolve()
    owner = str(args.owner).strip() or "controlled-beta-ops"

    try:
        if not handoff_report_path.is_file():
            raise ValueError("Handoff report path does not exist: %s" % handoff_report_path)
        handoff_report = _read_json(handoff_report_path)
        report = _build_report(
            handoff_report=handoff_report,
            handoff_report_path=handoff_report_path,
            owner=owner,
        )
        summary = _render_summary(report)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print("Real trial backfill handoff escalation export failed: %s" % exc, file=sys.stderr)
        return 2

    if output_path is not None:
        _write_text(output_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print("Real trial backfill handoff escalations report written: %s" % output_path)
    if summary_path is not None:
        _write_text(summary_path, summary)
        print("Real trial backfill handoff escalations summary written: %s" % summary_path)

    counts = report.get("escalation_counts", {})
    if not isinstance(counts, dict):
        counts = {}
    print(
        "Real trial backfill handoff escalations status=%s overdue=%s breached=%s total=%s"
        % (
            str(report.get("escalation_status", "unknown")),
            _to_int(counts.get("overdue_item_count"), default=0),
            _to_int(counts.get("sla_breached_item_count"), default=0),
            _to_int(counts.get("total_escalation_item_count"), default=0),
        )
    )
    if args.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    if bool(args.fail_on_overdue) and _to_int(counts.get("overdue_item_count"), default=0) > 0:
        return 1
    if bool(args.fail_on_breached) and _to_int(counts.get("sla_breached_item_count"), default=0) > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
