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

TARGET_AGENTS = ("codex", "claude-code", "opencode")
SMOKE_STATUSES = ("agent_smoke_passed", "agent_smoke_failed", "not_run")
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
    parser.add_argument("--skill-id", default="", help="Stable skill identifier.")
    parser.add_argument(
        "--agent",
        default="",
        choices=["", *TARGET_AGENTS],
        help="Agent target.",
    )
    parser.add_argument(
        "--status",
        default="",
        choices=["", *SMOKE_STATUSES],
        help="Smoke status for this skill/agent pair.",
    )
    parser.add_argument(
        "--reason",
        default="",
        help="Reason or evidence note for the selected status.",
    )
    parser.add_argument(
        "--trigger-prompt",
        default="",
        help="Prompt used to trigger the skill in the live agent workflow.",
    )
    parser.add_argument(
        "--expected-skill-selection",
        default="",
        help="Expected selected skill package name or identity.",
    )
    parser.add_argument(
        "--expected-task-output",
        default="",
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
        "--validate-matrix",
        action="store_true",
        help=(
            "Read --report and validate that every required skill has one recorded "
            "status for Codex, Claude Code, and OpenCode. This does not create live-agent evidence."
        ),
    )
    parser.add_argument(
        "--required-skill-id",
        action="append",
        default=[],
        help=(
            "Skill id that must appear in the smoke matrix. Repeat or use comma-separated values. "
            "When omitted, skill ids are derived from the report records."
        ),
    )
    parser.add_argument(
        "--target-agent",
        action="append",
        choices=list(TARGET_AGENTS),
        default=[],
        help="Target agent required in matrix validation. Repeat to override the default full matrix.",
    )
    parser.add_argument(
        "--fail-on-incomplete",
        action="store_true",
        help="In matrix validation mode, exit 1 when required cells are missing or malformed.",
    )
    parser.add_argument(
        "--print-json",
        action="store_true",
        help="Print full report JSON after write, or matrix JSON in --validate-matrix mode.",
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


def _require_non_empty(name: str, value: Any) -> str:
    text = "" if value is None else str(value).strip()
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

    _require_non_empty("skill-id", args.skill_id)
    _require_non_empty("agent", args.agent)
    _require_non_empty("status", args.status)
    _require_non_empty("reason", args.reason)
    _require_non_empty("trigger-prompt", args.trigger_prompt)
    _require_non_empty("expected-skill-selection", args.expected_skill_selection)
    _require_non_empty("expected-task-output", args.expected_task_output)

    if status not in STATUS_TO_METRICS_RESULT:
        raise ValueError("`--status` must be one of: %s." % ", ".join(SMOKE_STATUSES))

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


def _split_values(values: list[str]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for raw in values:
        for token in str(raw or "").split(","):
            text = token.strip()
            if not text or text in seen:
                continue
            seen.add(text)
            ordered.append(text)
    return ordered


def _record_failure_codes(record: dict[str, Any]) -> list[str]:
    codes: list[str] = []
    status = str(record.get("status", "")).strip().lower()
    agent = str(record.get("agent", "")).strip().lower()

    for field in [
        "skill_id",
        "agent",
        "status",
        "reason",
        "trigger_prompt",
        "expected_skill_selection",
        "expected_task_output",
    ]:
        if not str(record.get(field, "")).strip():
            codes.append("missing_required_field:%s" % field)

    if agent and agent not in TARGET_AGENTS:
        codes.append("unsupported_agent:%s" % agent)
    if status and status not in SMOKE_STATUSES:
        codes.append("unsupported_status:%s" % status)

    if status in {"agent_smoke_passed", "agent_smoke_failed"}:
        if not str(record.get("selected_skill", "")).strip():
            codes.append("missing_observed_field:selected_skill")
        if not str(record.get("observed_task_output", "")).strip():
            codes.append("missing_observed_field:observed_task_output")
    if status == "agent_smoke_failed" and not str(record.get("failure_code", "")).strip():
        codes.append("missing_failure_code")
    if status == "not_run" and (
        str(record.get("selected_skill", "")).strip() or str(record.get("observed_task_output", "")).strip()
    ):
        codes.append("not_run_has_observed_fields")
    return codes


def _target_agents(raw_agents: list[str]) -> list[str]:
    agents = _split_values(raw_agents)
    return agents if agents else list(TARGET_AGENTS)


def _required_skill_ids(report: dict[str, Any], raw_skill_ids: list[str]) -> list[str]:
    explicit = _split_values(raw_skill_ids)
    if explicit:
        return explicit

    records = report.get("records", [])
    if not isinstance(records, list):
        return []
    return sorted(
        {
            str(record.get("skill_id", "")).strip()
            for record in records
            if isinstance(record, dict) and str(record.get("skill_id", "")).strip()
        }
    )


def build_matrix_report(
    report: dict[str, Any],
    *,
    required_skill_ids: list[str],
    target_agents: list[str],
) -> dict[str, Any]:
    records = report.get("records", [])
    if not isinstance(records, list):
        raise ValueError("Report field `records` must be a list.")

    latest_records: dict[tuple[str, str], dict[str, Any]] = {}
    invalid_records: list[dict[str, Any]] = []
    duplicate_count = 0
    passed_count = 0
    failed_count = 0
    not_run_count = 0

    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            invalid_records.append({"record_index": index, "failure_codes": ["record_not_object"]})
            continue
        failure_codes = _record_failure_codes(record)
        skill_id = str(record.get("skill_id", "")).strip()
        agent = str(record.get("agent", "")).strip().lower()
        status = str(record.get("status", "")).strip().lower()
        if failure_codes:
            invalid_records.append(
                {
                    "record_index": index,
                    "skill_id": skill_id,
                    "agent": agent,
                    "failure_codes": failure_codes,
                }
            )
            continue
        key = (skill_id, agent)
        if key in latest_records:
            duplicate_count += 1
        latest_records[key] = record
        if status == "agent_smoke_passed":
            passed_count += 1
        elif status == "agent_smoke_failed":
            failed_count += 1
        elif status == "not_run":
            not_run_count += 1

    missing_cells: list[dict[str, str]] = []
    matrix_rows: list[dict[str, Any]] = []
    for skill_id in required_skill_ids:
        row = {"skill_id": skill_id, "agents": {}}
        for agent in target_agents:
            record = latest_records.get((skill_id, agent))
            if record is None:
                missing_cells.append({"skill_id": skill_id, "agent": agent})
                row["agents"][agent] = {"status": "missing"}
                continue
            row["agents"][agent] = {
                "status": str(record.get("status", "")).strip().lower(),
                "reason": str(record.get("reason", "")).strip(),
                "failure_code": str(record.get("failure_code", "")).strip(),
            }
        matrix_rows.append(row)

    expected_cell_count = len(required_skill_ids) * len(target_agents)
    recorded_cell_count = expected_cell_count - len(missing_cells)
    status = "AGENT_SMOKE_MATRIX_READY"
    if expected_cell_count <= 0:
        status = "AGENT_SMOKE_MATRIX_EMPTY"
    elif missing_cells or invalid_records:
        status = "AGENT_SMOKE_MATRIX_INCOMPLETE"

    return {
        "schema_version": "cbt12.agent_smoke_matrix.v1",
        "generated_at_utc": _utc_now_iso(),
        "status": status,
        "target_agents": target_agents,
        "required_skill_ids": required_skill_ids,
        "counts": {
            "required_skill_count": len(required_skill_ids),
            "target_agent_count": len(target_agents),
            "expected_cell_count": expected_cell_count,
            "recorded_cell_count": recorded_cell_count,
            "missing_cell_count": len(missing_cells),
            "invalid_record_count": len(invalid_records),
            "duplicate_record_count": duplicate_count,
            "passed_record_count": passed_count,
            "failed_record_count": failed_count,
            "not_run_record_count": not_run_count,
        },
        "missing_cells": missing_cells,
        "invalid_records": invalid_records,
        "matrix": matrix_rows,
    }


def main() -> int:
    args = _parse_args()
    report_path = Path(args.report).resolve()

    try:
        report = _read_report(report_path)
        if bool(args.validate_matrix):
            matrix_report = build_matrix_report(
                report,
                required_skill_ids=_required_skill_ids(report, args.required_skill_id),
                target_agents=_target_agents(args.target_agent),
            )
            counts = matrix_report.get("counts", {})
            print(
                "Agent smoke matrix status=%s skills=%s expected=%s recorded=%s missing=%s invalid=%s"
                % (
                    str(matrix_report.get("status", "unknown")),
                    int(counts.get("required_skill_count", 0) or 0),
                    int(counts.get("expected_cell_count", 0) or 0),
                    int(counts.get("recorded_cell_count", 0) or 0),
                    int(counts.get("missing_cell_count", 0) or 0),
                    int(counts.get("invalid_record_count", 0) or 0),
                )
            )
            if args.print_json:
                print(json.dumps(matrix_report, ensure_ascii=False, indent=2))
            if bool(args.fail_on_incomplete) and str(matrix_report.get("status")) != "AGENT_SMOKE_MATRIX_READY":
                return 1
            return 0

        _validate_argument_contract(args)
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
