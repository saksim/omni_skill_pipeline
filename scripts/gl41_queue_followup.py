from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUBMISSION_QUEUE_COMMITMENT_CLOSURE_REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-commitment-closure-report.json"
)
DEFAULT_OUTPUT_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-report.json"
)
DEFAULT_SUMMARY_PATH = (
    REPO_ROOT
    / "docs"
    / "current"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-summary.md"
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate GL-41 owner follow-up execution records from GL-40 commitment-closure diagnostics."
        )
    )
    parser.add_argument(
        "--submission-queue-commitment-closure-report",
        default=str(DEFAULT_SUBMISSION_QUEUE_COMMITMENT_CLOSURE_REPORT_PATH),
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help='Follow-up report output path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--summary-output",
        default=str(DEFAULT_SUMMARY_PATH),
        help='Follow-up summary output path. Use "-" to skip writing file.',
    )
    parser.add_argument(
        "--owner",
        default="controlled-beta-ops",
        help="Fallback owner used when source rows do not define owner.",
    )
    parser.add_argument(
        "--fail-on-open",
        action="store_true",
        help="Exit with code 1 when open follow-up actions remain.",
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


def _normalize_owner(value: Any, *, fallback_owner: str) -> str:
    owner = str(value or "").strip()
    return owner or fallback_owner


def _normalize_stale_reason_codes(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return _unique_preserve_order([str(item).strip() for item in value if str(item).strip()])


def _build_open_action_row(
    *,
    source_row: dict[str, Any],
    fallback_owner: str,
    action_type: str,
    reason_code: str,
) -> dict[str, Any]:
    commitment_id = str(source_row.get("commitment_id", "")).strip()
    queue_item_id = str(source_row.get("queue_item_id", "")).strip()
    backfill_action_id = str(source_row.get("backfill_action_id", "")).strip()
    owner = _normalize_owner(source_row.get("owner", ""), fallback_owner=fallback_owner)
    action_suffix = commitment_id or backfill_action_id or queue_item_id or "unbound"
    return {
        "followup_action_id": "gl41-%s-%s" % (action_type, action_suffix),
        "followup_action_status": "open",
        "followup_action_type": action_type,
        "followup_reason_code": reason_code,
        "owner": owner,
        "commitment_id": commitment_id,
        "queue_item_id": queue_item_id,
        "backfill_action_id": backfill_action_id,
        "required_modality": str(source_row.get("required_modality", "")).strip().lower(),
        "priority_rank": _to_int(source_row.get("priority_rank", 0), default=0),
        "source_closure_state_gl40": str(source_row.get("closure_state", "")).strip().lower(),
        "source_commitment_status_gl39": str(source_row.get("commitment_status_gl39", "")).strip().lower(),
        "source_transition_state_gl38": str(source_row.get("transition_state_gl38", "")).strip().lower(),
        "source_stale_rollover": bool(source_row.get("stale_rollover", False)),
        "source_stale_reason_codes": _normalize_stale_reason_codes(source_row.get("stale_reason_codes", [])),
        "cycle_due_at_utc": str(source_row.get("cycle_due_at_utc", "")),
        "reason": str(source_row.get("reason", "")),
    }


def _build_closed_action_row(*, acknowledgement_row: dict[str, Any], fallback_owner: str) -> dict[str, Any]:
    commitment_id = str(acknowledgement_row.get("commitment_id", "")).strip()
    queue_item_id = str(acknowledgement_row.get("queue_item_id", "")).strip()
    backfill_action_id = str(acknowledgement_row.get("backfill_action_id", "")).strip()
    owner = _normalize_owner(acknowledgement_row.get("owner", ""), fallback_owner=fallback_owner)
    action_suffix = commitment_id or backfill_action_id or queue_item_id or "unbound"
    return {
        "followup_action_id": "gl41-acknowledgement-closure-recorded-%s" % action_suffix,
        "followup_action_status": "closed",
        "followup_action_type": "acknowledgement_closure_recorded",
        "followup_reason_code": "acknowledgement_closure_evidence_recorded",
        "owner": owner,
        "commitment_id": commitment_id,
        "queue_item_id": queue_item_id,
        "backfill_action_id": backfill_action_id,
        "required_modality": str(acknowledgement_row.get("required_modality", "")).strip().lower(),
        "priority_rank": 0,
        "source_closure_state_gl40": str(acknowledgement_row.get("closure_state", "")).strip().lower(),
        "source_commitment_status_gl39": "",
        "source_transition_state_gl38": "closed_with_acknowledgement",
        "source_stale_rollover": False,
        "source_stale_reason_codes": [],
        "cycle_due_at_utc": "",
        "reason": "acknowledgement_closure_recorded",
        "linked_submission_loop_id": str(acknowledgement_row.get("linked_submission_loop_id", "")).strip(),
        "linked_submission_review_task_id": str(
            acknowledgement_row.get("linked_submission_review_task_id", "")
        ).strip(),
        "linked_submission_reviewed_at_utc": str(
            acknowledgement_row.get("linked_submission_reviewed_at_utc", "")
        ).strip(),
    }


def _build_action_rows(
    *,
    closure_report: dict[str, Any],
    fallback_owner: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    closure_rows = closure_report.get("commitment_closure_rows", [])
    if not isinstance(closure_rows, list):
        closure_rows = []
    acknowledgement_rows = closure_report.get("closure_acknowledgement_rows", [])
    if not isinstance(acknowledgement_rows, list):
        acknowledgement_rows = []

    action_rows: list[dict[str, Any]] = []
    warning_codes: list[str] = []

    for row in closure_rows:
        if not isinstance(row, dict):
            continue
        closure_state = str(row.get("closure_state", "")).strip().lower()
        stale_rollover = bool(row.get("stale_rollover", False))

        if stale_rollover:
            action_rows.append(
                _build_open_action_row(
                    source_row=row,
                    fallback_owner=fallback_owner,
                    action_type="resolve_stale_rollover",
                    reason_code="stale_rollover_requires_followup",
                )
            )
            warning_codes.append("stale_rollover_followup_actions_required")
            continue

        if closure_state == "pending_acknowledgement":
            action_rows.append(
                _build_open_action_row(
                    source_row=row,
                    fallback_owner=fallback_owner,
                    action_type="complete_acknowledgement_closure",
                    reason_code="pending_acknowledgement_requires_closure",
                )
            )
            warning_codes.append("pending_acknowledgement_followup_actions_required")
            continue

        if closure_state == "blocked_submission_errors":
            action_rows.append(
                _build_open_action_row(
                    source_row=row,
                    fallback_owner=fallback_owner,
                    action_type="resolve_blocked_submission_errors",
                    reason_code="blocked_submission_errors_require_resolution",
                )
            )
            warning_codes.append("blocked_submission_errors_followup_actions_required")
            continue

        if closure_state == "escalation_required":
            action_rows.append(
                _build_open_action_row(
                    source_row=row,
                    fallback_owner=fallback_owner,
                    action_type="resolve_escalation_required_closure",
                    reason_code="escalation_required_followup_actions_required",
                )
            )
            warning_codes.append("escalation_required_followup_actions_required")
            continue

        if closure_state == "rebuild_required":
            action_rows.append(
                _build_open_action_row(
                    source_row=row,
                    fallback_owner=fallback_owner,
                    action_type="rebuild_commitment_closure_pipeline",
                    reason_code="rebuild_required_followup_actions_required",
                )
            )
            warning_codes.append("rebuild_required_followup_actions_required")

    for row in acknowledgement_rows:
        if not isinstance(row, dict):
            continue
        action_rows.append(_build_closed_action_row(acknowledgement_row=row, fallback_owner=fallback_owner))

    action_rows.sort(
        key=lambda row: (
            0 if str(row.get("followup_action_status", "")) == "open" else 1,
            0 if str(row.get("followup_action_type", "")) == "resolve_stale_rollover" else 1,
            0 if str(row.get("followup_action_type", "")) == "complete_acknowledgement_closure" else 1,
            _to_int(row.get("priority_rank", 0), default=0) <= 0,
            _to_int(row.get("priority_rank", 0), default=0),
            str(row.get("required_modality", "")),
            str(row.get("backfill_action_id", "")),
            str(row.get("queue_item_id", "")),
            str(row.get("followup_action_id", "")),
        )
    )
    return action_rows, _unique_preserve_order(warning_codes)


def _owner_counts(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        owner = _normalize_owner(row.get("owner", ""), fallback_owner="unassigned")
        action_type = str(row.get("followup_action_type", "")).strip()
        action_status = str(row.get("followup_action_status", "")).strip()
        bucket = counts.setdefault(
            owner,
            {
                "total_action_count": 0,
                "open_action_count": 0,
                "closed_action_count": 0,
                "stale_rollover_action_count": 0,
                "acknowledgement_completion_action_count": 0,
                "blocked_action_count": 0,
            },
        )
        bucket["total_action_count"] += 1
        if action_status == "open":
            bucket["open_action_count"] += 1
        elif action_status == "closed":
            bucket["closed_action_count"] += 1

        if action_type == "resolve_stale_rollover":
            bucket["stale_rollover_action_count"] += 1
        elif action_type == "complete_acknowledgement_closure":
            bucket["acknowledgement_completion_action_count"] += 1
        elif action_type in {
            "resolve_blocked_submission_errors",
            "resolve_escalation_required_closure",
            "rebuild_commitment_closure_pipeline",
        }:
            bucket["blocked_action_count"] += 1
    return counts


def _build_followup_status(
    *,
    closure_status_gl40: str,
    stale_rollover_action_count: int,
    blocked_action_count: int,
    acknowledgement_completion_action_count: int,
    open_action_count: int,
) -> str:
    if open_action_count == 0 and closure_status_gl40 in {"CLOSURE_NOT_REQUIRED", "CLOSURE_COMPLETED"}:
        return "FOLLOWUP_NOT_REQUIRED"
    if stale_rollover_action_count > 0:
        return "FOLLOWUP_STALE_ROLLOVER_ACTION_REQUIRED"
    if blocked_action_count > 0:
        return "FOLLOWUP_BLOCKED_BY_CLOSURE_STATE"
    if acknowledgement_completion_action_count > 0:
        return "FOLLOWUP_ACKNOWLEDGEMENT_CLOSURE_REQUIRED"
    if open_action_count > 0:
        return "FOLLOWUP_ACTIONS_OPEN"
    return "FOLLOWUP_ACTIONS_CLEARED"


def _build_report(
    *,
    closure_report: dict[str, Any],
    closure_report_path: Path,
    owner: str,
) -> dict[str, Any]:
    closure_status_gl40 = str(closure_report.get("commitment_closure_status", "unknown")).strip().upper() or "UNKNOWN"
    cadence_run_closure_status_gl40 = (
        str(closure_report.get("cadence_run_closure_status", "unknown")).strip().upper() or "UNKNOWN"
    )
    closure_warning_codes = closure_report.get("warning_codes", [])
    if not isinstance(closure_warning_codes, list):
        closure_warning_codes = []

    action_rows, warning_codes = _build_action_rows(closure_report=closure_report, fallback_owner=owner)
    open_actions = [
        row for row in action_rows if str(row.get("followup_action_status", "")).strip().lower() == "open"
    ]
    closed_actions = [
        row for row in action_rows if str(row.get("followup_action_status", "")).strip().lower() == "closed"
    ]
    stale_rollover_action_count = sum(
        1 for row in open_actions if str(row.get("followup_action_type", "")).strip() == "resolve_stale_rollover"
    )
    acknowledgement_completion_action_count = sum(
        1
        for row in open_actions
        if str(row.get("followup_action_type", "")).strip() == "complete_acknowledgement_closure"
    )
    blocked_action_count = sum(
        1
        for row in open_actions
        if str(row.get("followup_action_type", "")).strip()
        in {
            "resolve_blocked_submission_errors",
            "resolve_escalation_required_closure",
            "rebuild_commitment_closure_pipeline",
        }
    )
    acknowledgement_closed_action_count = sum(
        1
        for row in closed_actions
        if str(row.get("followup_action_type", "")).strip() == "acknowledgement_closure_recorded"
    )

    followup_status = _build_followup_status(
        closure_status_gl40=closure_status_gl40,
        stale_rollover_action_count=stale_rollover_action_count,
        blocked_action_count=blocked_action_count,
        acknowledgement_completion_action_count=acknowledgement_completion_action_count,
        open_action_count=len(open_actions),
    )
    if len(open_actions) > 0:
        warning_codes.append("open_followup_actions_present")
    warning_codes = _unique_preserve_order(warning_codes)

    return {
        "schema_version": "real_trial_submission_queue_followup.v1",
        "generated_at_utc": _utc_now_iso(),
        "owner": owner,
        "input_paths": {
            "submission_queue_commitment_closure_report": str(closure_report_path),
        },
        "commitment_closure_status_gl40": closure_status_gl40,
        "cadence_run_closure_status_gl40": cadence_run_closure_status_gl40,
        "followup_status": followup_status,
        "warning_codes": warning_codes,
        "closure_warning_codes_gl40": closure_warning_codes,
        "followup_counts": {
            "total_action_count": len(action_rows),
            "open_action_count": len(open_actions),
            "closed_action_count": len(closed_actions),
            "stale_rollover_action_count": stale_rollover_action_count,
            "acknowledgement_completion_action_count": acknowledgement_completion_action_count,
            "acknowledgement_closed_action_count": acknowledgement_closed_action_count,
            "blocked_action_count": blocked_action_count,
        },
        "owner_followup_counts": _owner_counts(action_rows),
        "followup_action_rows": action_rows,
    }


def _render_summary(report: dict[str, Any]) -> str:
    counts = report.get("followup_counts", {})
    if not isinstance(counts, dict):
        counts = {}
    warning_codes = report.get("warning_codes", [])
    if not isinstance(warning_codes, list):
        warning_codes = []
    action_rows = report.get("followup_action_rows", [])
    if not isinstance(action_rows, list):
        action_rows = []

    lines = [
        "# Real Trial Submission Queue Follow-Up Summary",
        "",
        "- Follow-up status: `%s`" % str(report.get("followup_status", "unknown")),
        "- GL-40 closure status: `%s`" % str(report.get("commitment_closure_status_gl40", "unknown")),
        "- GL-40 cadence run closure status: `%s`" % str(report.get("cadence_run_closure_status_gl40", "unknown")),
        "- Total actions: `%s`" % str(_to_int(counts.get("total_action_count", 0), default=0)),
        "- Open actions: `%s`" % str(_to_int(counts.get("open_action_count", 0), default=0)),
        "- Closed actions: `%s`" % str(_to_int(counts.get("closed_action_count", 0), default=0)),
        "- Stale-rollover actions: `%s`" % str(_to_int(counts.get("stale_rollover_action_count", 0), default=0)),
        "- Acknowledgement-completion actions: `%s`"
        % str(_to_int(counts.get("acknowledgement_completion_action_count", 0), default=0)),
        "- Blocked-state actions: `%s`" % str(_to_int(counts.get("blocked_action_count", 0), default=0)),
        "",
        "## Warning Codes",
    ]
    if warning_codes:
        for code in warning_codes:
            lines.append("- `%s`" % str(code))
    else:
        lines.append("- none")

    lines.extend(["", "## Follow-Up Actions"])
    if action_rows:
        for row in action_rows:
            if not isinstance(row, dict):
                continue
            lines.append(
                "- `%s` status=%s type=%s owner=%s action=%s modality=%s due=%s"
                % (
                    str(row.get("followup_action_id", "")),
                    str(row.get("followup_action_status", "")),
                    str(row.get("followup_action_type", "")),
                    str(row.get("owner", "")),
                    str(row.get("backfill_action_id", "")),
                    str(row.get("required_modality", "")),
                    str(row.get("cycle_due_at_utc", "")),
                )
            )
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    closure_report_path = Path(str(args.submission_queue_commitment_closure_report).strip()).resolve()
    output_path = None if str(args.output).strip() == "-" else Path(str(args.output).strip()).resolve()
    summary_path = None if str(args.summary_output).strip() == "-" else Path(str(args.summary_output).strip()).resolve()
    owner = str(args.owner).strip() or "controlled-beta-ops"

    try:
        if not closure_report_path.is_file():
            raise ValueError(
                "Submission queue commitment-closure report path does not exist: %s" % closure_report_path
            )
        closure_report = _read_json(closure_report_path)
        report = _build_report(
            closure_report=closure_report,
            closure_report_path=closure_report_path,
            owner=owner,
        )
        summary = _render_summary(report)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print("Real trial submission queue follow-up generation failed: %s" % exc, file=sys.stderr)
        return 2

    if output_path is not None:
        _write_text(output_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print("Real trial submission queue follow-up report written: %s" % output_path)
    if summary_path is not None:
        _write_text(summary_path, summary)
        print("Real trial submission queue follow-up summary written: %s" % summary_path)

    followup_counts = report.get("followup_counts", {})
    if not isinstance(followup_counts, dict):
        followup_counts = {}
    print(
        "Real trial submission queue follow-up status=%s open=%s closed=%s"
        % (
            str(report.get("followup_status", "unknown")),
            _to_int(followup_counts.get("open_action_count", 0), default=0),
            _to_int(followup_counts.get("closed_action_count", 0), default=0),
        )
    )
    if args.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    if bool(args.fail_on_open) and _to_int(followup_counts.get("open_action_count", 0), default=0) > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

