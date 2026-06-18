from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "controlled-trial"
    / "agent-smoke-report.json"
)

STATUS_TO_METRICS_RESULT = {
    "agent_smoke_passed": "passed",
    "agent_smoke_failed": "failed",
    "not_run": "not_run",
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Record CBT-12 agent smoke status for one approved skill on one target agent "
            "(Codex, Claude Code, OpenCode)."
        )
    )
    parser.add_argument(
        "--report",
        default=str(DEFAULT_REPORT_PATH),
        help="Agent smoke report JSON path.",
    )
    parser.add_argument("--skill-id", required=True, help="Stable skill identifier.")
    parser.add_argument(
        "--agent",
        required=True,
        choices=["codex", "claude-code", "opencode"],
        help="Agent target.",
    )
    parser.add_argument(
        "--status",
        required=True,
        choices=["agent_smoke_passed", "agent_smoke_failed", "not_run"],
        help="Smoke status for this skill/agent pair.",
    )
    parser.add_argument(
        "--reason",
        required=True,
        help="Reason or evidence note for the selected status.",
    )
    parser.add_argument(
        "--trigger-prompt",
        required=True,
        help="Prompt used to trigger the skill in the live agent workflow.",
    )
    parser.add_argument(
        "--expected-skill-selection",
        required=True,
        help="Expected selected skill package name or identity.",
    )
    parser.add_argument(
        "--expected-task-output",
        required=True,
        help="Expected output behavior for the smoke task.",
    )
    parser.add_argument(
        "--selected-skill",
        default="",
        help="Observed selected skill identity from the live run.",
    )
    parser.add_argument(
        "--observed-task-output",
        default="",
        help="Observed task output summary from the live run.",
    )
    parser.add_argument(
        "--failure-code",
        default="",
        help="Optional failure code when status is agent_smoke_failed.",
    )
    parser.add_argument(
        "--notes",
        default="",
        help="Optional operator notes.",
    )
    parser.add_argument(
        "--print-json",
        action="store_true",
        help="Print full report JSON to stdout after write.",
    )
    return parser.parse_args()


def _read_report(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "schema_version": "cbt12.agent_smoke_report.v1",
            "updated_at_utc": _utc_now_iso(),
            "records": [],
        }
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Report root must be a JSON object.")
    records = payload.get("records", [])
    if not isinstance(records, list):
        raise ValueError("Report field `records` must be a list.")
    payload["records"] = records
    return payload


def _write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _require_non_empty(name: str, value: str) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError("`%s` cannot be empty." % name)
    return text


def _normalize_optional(value: str) -> str:
    return str(value).strip()


def _validate_argument_contract(args: argparse.Namespace) -> None:
    status = str(args.status).strip().lower()
    selected_skill = _normalize_optional(args.selected_skill)
    observed_task_output = _normalize_optional(args.observed_task_output)
    failure_code = _normalize_optional(args.failure_code)

    if status == "agent_smoke_passed":
        if not selected_skill:
            raise ValueError("`--selected-skill` is required when status=agent_smoke_passed.")
        if not observed_task_output:
            raise ValueError("`--observed-task-output` is required when status=agent_smoke_passed.")
    if status == "agent_smoke_failed":
        if not selected_skill:
            raise ValueError("`--selected-skill` is required when status=agent_smoke_failed.")
        if not observed_task_output:
            raise ValueError("`--observed-task-output` is required when status=agent_smoke_failed.")
        if not failure_code:
            raise ValueError("`--failure-code` is required when status=agent_smoke_failed.")
    if status == "not_run":
        if selected_skill or observed_task_output:
            raise ValueError("Do not pass observed run fields when status=not_run.")


def _build_record(args: argparse.Namespace) -> dict[str, Any]:
    status = str(args.status).strip().lower()
    return {
        "recorded_at_utc": _utc_now_iso(),
        "skill_id": _require_non_empty("skill-id", args.skill_id),
        "agent": _require_non_empty("agent", args.agent),
        "status": status,
        "metrics_agent_smoke_result": STATUS_TO_METRICS_RESULT[status],
        "reason": _require_non_empty("reason", args.reason),
        "trigger_prompt": _require_non_empty("trigger-prompt", args.trigger_prompt),
        "expected_skill_selection": _require_non_empty("expected-skill-selection", args.expected_skill_selection),
        "expected_task_output": _require_non_empty("expected-task-output", args.expected_task_output),
        "selected_skill": _normalize_optional(args.selected_skill),
        "observed_task_output": _normalize_optional(args.observed_task_output),
        "failure_code": _normalize_optional(args.failure_code),
        "notes": _normalize_optional(args.notes),
    }


def _upsert_record(report: dict[str, Any], record: dict[str, Any]) -> str:
    records = report["records"]
    skill_id = str(record.get("skill_id", "")).strip()
    agent = str(record.get("agent", "")).strip()
    for index, item in enumerate(records):
        if not isinstance(item, dict):
            continue
        if str(item.get("skill_id", "")).strip() == skill_id and str(item.get("agent", "")).strip() == agent:
            records[index] = record
            return "updated"
    records.append(record)
    return "created"


def main() -> int:
    args = _parse_args()
    report_path = Path(args.report).resolve()

    try:
        _validate_argument_contract(args)
        report = _read_report(report_path)
        record = _build_record(args)
        operation = _upsert_record(report, record)
        report["schema_version"] = "cbt12.agent_smoke_report.v1"
        report["updated_at_utc"] = _utc_now_iso()
        report["record_count"] = len(report["records"])
        _write_report(report_path, report)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print("Agent smoke record failed: %s" % exc, file=sys.stderr)
        return 2

    print(
        "Agent smoke record %s: skill_id=%s agent=%s status=%s report=%s"
        % (
            operation,
            record["skill_id"],
            record["agent"],
            record["status"],
            report_path,
        )
    )
    if args.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
