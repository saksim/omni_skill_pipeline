from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RELEASE_GATE_REPORT = (
    REPO_ROOT / "docs" / "working" / "status" / "baselines" / "e13-release-gate-validation-plan.json"
)
DEFAULT_LAUNCH_READINESS_REPORT = (
    REPO_ROOT / "docs" / "working" / "status" / "baselines" / "broad-launch-readiness-report.json"
)
DEFAULT_DOC_SYNC_REPORT = (
    REPO_ROOT / "docs" / "working" / "status" / "baselines" / "e13-doc-sync-check-report.json"
)
DEFAULT_LAUNCH_BETA_RUNBOOK = (
    REPO_ROOT / "docs" / "latest" / "operations" / "runbooks" / "launch-beta.md"
)
DEFAULT_DOCKER_ZERO_TO_RELEASE_RUNBOOK = (
    REPO_ROOT / "docs" / "latest" / "operations" / "runbooks" / "docker-zero-to-release.md"
)
DEFAULT_PRODUCTION_OPS_RUNBOOK = (
    REPO_ROOT / "docs" / "latest" / "operations" / "runbooks" / "production-operations-baseline.md"
)
DEFAULT_OUTPUT_PATH = (
    REPO_ROOT / "docs" / "working" / "status" / "baselines" / "operations-readiness-report.json"
)
DEFAULT_SUMMARY_OUTPUT_PATH = (
    REPO_ROOT / "docs" / "working" / "status" / "baselines" / "operations-readiness-summary.md"
)

EXPECTED_RELEASE_GATE_STAGES = {"beta_gate", "ga_gate", "roadmap_gate"}
EXPECTED_LAUNCH_DECISIONS = {
    "HOLD",
    "READY_FOR_CONTROLLED_BETA",
    "READY_FOR_GA_REVIEW",
    "READY_FOR_PLATFORM_BETA",
}
PRODUCTION_OPS_REQUIRED_HEADINGS = (
    "## Deploy Workflow",
    "## Validation Workflow",
    "## Rollback Workflow",
    "## Backup Workflow",
    "## Restore Workflow",
    "## Incident Response Workflow",
    "## Log Inspection Workflow",
    "## Alert Workflow",
    "## Evidence Collection Workflow",
)
PRODUCTION_OPS_REQUIRED_MARKERS = (
    "python scripts/release_gate.py",
    "python scripts/launch_gate.py",
    "python scripts/ops_evidence.py",
    "python scripts/doc_sync.py --output",
    "docker logs",
    "docker run --rm -d",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build production-operations readiness evidence bound to release and launch gates.",
    )
    parser.add_argument("--release-gate-report", default=str(DEFAULT_RELEASE_GATE_REPORT))
    parser.add_argument("--launch-readiness-report", default=str(DEFAULT_LAUNCH_READINESS_REPORT))
    parser.add_argument("--doc-sync-report", default=str(DEFAULT_DOC_SYNC_REPORT))
    parser.add_argument("--launch-beta-runbook", default=str(DEFAULT_LAUNCH_BETA_RUNBOOK))
    parser.add_argument(
        "--docker-zero-to-release-runbook",
        default=str(DEFAULT_DOCKER_ZERO_TO_RELEASE_RUNBOOK),
    )
    parser.add_argument(
        "--production-ops-runbook",
        default=str(DEFAULT_PRODUCTION_OPS_RUNBOOK),
    )
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH), help='Use "-" to skip writing.')
    parser.add_argument(
        "--summary-output",
        default=str(DEFAULT_SUMMARY_OUTPUT_PATH),
        help='Use "-" to skip writing.',
    )
    parser.add_argument("--print-json", action="store_true")
    parser.add_argument("--print-summary", action="store_true")
    return parser.parse_args()


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("JSON root must be an object: %s" % path)
    return payload


def _make_check(
    check_id: str,
    status: str,
    *,
    actual: Any,
    expected: Any,
    details: str = "",
) -> dict[str, Any]:
    return {
        "id": check_id,
        "status": status,
        "actual": actual,
        "expected": expected,
        "details": details,
    }


def _check_required_file(path: Path, *, check_id: str) -> dict[str, Any]:
    exists = path.is_file()
    return _make_check(
        check_id,
        "pass" if exists else "fail",
        actual=str(path) if exists else "missing",
        expected="readable file",
        details="Required operations evidence file must exist.",
    )


def _check_release_gate_contract(report: dict[str, Any]) -> dict[str, Any]:
    stages = report.get("stages", [])
    if not isinstance(stages, list):
        stages = []
    stage_names = [str(stage.get("name", "")) for stage in stages if isinstance(stage, dict)]
    stage_name_set = {name for name in stage_names if name}
    missing_stages = sorted(EXPECTED_RELEASE_GATE_STAGES - stage_name_set)
    invalid_command_stages: list[str] = []
    for stage in stages:
        if not isinstance(stage, dict):
            continue
        stage_name = str(stage.get("name", ""))
        command = stage.get("command", [])
        if not isinstance(command, list):
            invalid_command_stages.append(stage_name)
            continue
        joined = " ".join(str(token) for token in command)
        if "scripts/linux_validate.py" not in joined:
            invalid_command_stages.append(stage_name)
    status = "pass" if not missing_stages and not invalid_command_stages else "fail"
    return _make_check(
        "release_gate_operations_binding",
        status,
        actual={
            "stage_names": stage_names,
            "invalid_command_stages": invalid_command_stages,
        },
        expected={
            "required_stage_names": sorted(EXPECTED_RELEASE_GATE_STAGES),
            "command_contains": "scripts/linux_validate.py",
        },
        details="Operations readiness must bind to existing release-gate stage packs.",
    )


def _check_launch_readiness_contract(report: dict[str, Any]) -> dict[str, Any]:
    decision = str(report.get("decision", "")).strip().upper()
    checks = report.get("checks", [])
    if not isinstance(checks, list):
        checks = []
    check_map = {
        str(item.get("id")): str(item.get("status", "")).strip().lower()
        for item in checks
        if isinstance(item, dict) and item.get("id")
    }
    release_check_status = check_map.get("release_switch_go", "")
    evidence_strictness_check_status = check_map.get("no_dry_run_relaxed_or_skipped_evidence", "")
    status = "pass"
    if decision not in EXPECTED_LAUNCH_DECISIONS:
        status = "fail"
    if release_check_status != "pass":
        status = "fail"
    if evidence_strictness_check_status != "pass":
        status = "fail"
    return _make_check(
        "launch_readiness_operations_binding",
        status,
        actual={
            "decision": decision,
            "release_switch_go_status": release_check_status or "missing",
            "strict_evidence_status": evidence_strictness_check_status or "missing",
        },
        expected={
            "decision_in": sorted(EXPECTED_LAUNCH_DECISIONS),
            "release_switch_go_status": "pass",
            "strict_evidence_status": "pass",
        },
        details="Operations evidence must stay bound to launch-readiness strict-evidence contracts.",
    )


def _check_doc_sync_contract(report: dict[str, Any]) -> dict[str, Any]:
    status_value = str(report.get("status", "")).strip().lower()
    failed_count = int(report.get("failed_count") or 0)
    status = "pass" if status_value == "pass" and failed_count == 0 else "fail"
    return _make_check(
        "doc_sync_contract",
        status,
        actual={"status": status_value, "failed_count": failed_count},
        expected={"status": "pass", "failed_count": 0},
        details="Doc-sync must pass before operations evidence can be treated as launch-claimable.",
    )


def _check_production_ops_runbook(content: str) -> dict[str, Any]:
    missing_headings = [item for item in PRODUCTION_OPS_REQUIRED_HEADINGS if item not in content]
    missing_markers = [item for item in PRODUCTION_OPS_REQUIRED_MARKERS if item not in content]
    status = "pass" if not missing_headings and not missing_markers else "fail"
    return _make_check(
        "production_ops_runbook_contract",
        status,
        actual={
            "missing_headings": missing_headings,
            "missing_markers": missing_markers,
        },
        expected={
            "required_headings": list(PRODUCTION_OPS_REQUIRED_HEADINGS),
            "required_markers": list(PRODUCTION_OPS_REQUIRED_MARKERS),
        },
        details="Production operations baseline runbook must define deploy/rollback/backup/restore/incident/alert workflows.",
    )


def _build_report(args: argparse.Namespace) -> dict[str, Any]:
    release_gate_report_path = Path(args.release_gate_report).resolve()
    launch_readiness_report_path = Path(args.launch_readiness_report).resolve()
    doc_sync_report_path = Path(args.doc_sync_report).resolve()
    launch_beta_runbook_path = Path(args.launch_beta_runbook).resolve()
    docker_zero_to_release_runbook_path = Path(args.docker_zero_to_release_runbook).resolve()
    production_ops_runbook_path = Path(args.production_ops_runbook).resolve()

    checks: list[dict[str, Any]] = []
    required_paths = {
        "release_gate_report_file": release_gate_report_path,
        "launch_readiness_report_file": launch_readiness_report_path,
        "doc_sync_report_file": doc_sync_report_path,
        "launch_beta_runbook_file": launch_beta_runbook_path,
        "docker_zero_to_release_runbook_file": docker_zero_to_release_runbook_path,
        "production_ops_runbook_file": production_ops_runbook_path,
    }
    for check_id, path in required_paths.items():
        checks.append(_check_required_file(path, check_id=check_id))

    release_report: dict[str, Any] = {}
    launch_report: dict[str, Any] = {}
    doc_sync_report: dict[str, Any] = {}
    production_ops_runbook_text = ""

    if release_gate_report_path.is_file():
        try:
            release_report = _read_json(release_gate_report_path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            checks.append(
                _make_check(
                    "release_gate_report_json",
                    "fail",
                    actual=str(exc),
                    expected="valid json object",
                    details="Release-gate report must be readable JSON.",
                )
            )
    if launch_readiness_report_path.is_file():
        try:
            launch_report = _read_json(launch_readiness_report_path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            checks.append(
                _make_check(
                    "launch_readiness_report_json",
                    "fail",
                    actual=str(exc),
                    expected="valid json object",
                    details="Launch-readiness report must be readable JSON.",
                )
            )
    if doc_sync_report_path.is_file():
        try:
            doc_sync_report = _read_json(doc_sync_report_path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            checks.append(
                _make_check(
                    "doc_sync_report_json",
                    "fail",
                    actual=str(exc),
                    expected="valid json object",
                    details="Doc-sync report must be readable JSON.",
                )
            )
    if production_ops_runbook_path.is_file():
        try:
            production_ops_runbook_text = production_ops_runbook_path.read_text(
                encoding="utf-8",
                errors="replace",
            )
        except OSError as exc:
            checks.append(
                _make_check(
                    "production_ops_runbook_read",
                    "fail",
                    actual=str(exc),
                    expected="readable utf-8 text",
                    details="Production operations runbook must be readable.",
                )
            )

    if release_report:
        checks.append(_check_release_gate_contract(release_report))
    if launch_report:
        checks.append(_check_launch_readiness_contract(launch_report))
    if doc_sync_report:
        checks.append(_check_doc_sync_contract(doc_sync_report))
    if production_ops_runbook_text:
        checks.append(_check_production_ops_runbook(production_ops_runbook_text))

    failed_checks = [check["id"] for check in checks if check.get("status") != "pass"]
    overall_status = "pass" if not failed_checks else "fail"
    return {
        "schema_version": "operations_readiness.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "overall_status": overall_status,
        "check_count": len(checks),
        "pass_count": len([check for check in checks if check.get("status") == "pass"]),
        "fail_count": len([check for check in checks if check.get("status") != "pass"]),
        "failed_checks": failed_checks,
        "checks": checks,
        "evidence_paths": {
            "release_gate_report": str(release_gate_report_path),
            "launch_readiness_report": str(launch_readiness_report_path),
            "doc_sync_report": str(doc_sync_report_path),
            "launch_beta_runbook": str(launch_beta_runbook_path),
            "docker_zero_to_release_runbook": str(docker_zero_to_release_runbook_path),
            "production_ops_runbook": str(production_ops_runbook_path),
        },
    }


def _render_summary(report: dict[str, Any]) -> str:
    lines = [
        "# Operations Readiness Summary",
        "",
        "- Status: `%s`" % report.get("overall_status", "fail"),
        "- Checks: `%s`" % report.get("check_count", 0),
        "- Passed: `%s`" % report.get("pass_count", 0),
        "- Failed: `%s`" % report.get("fail_count", 0),
        "- Failed checks: `%s`" % (", ".join(report.get("failed_checks", [])) or "none"),
        "",
        "## Check Results",
        "",
    ]
    for check in report.get("checks", []):
        lines.append("- `%s`: `%s`" % (check.get("id"), check.get("status")))
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    try:
        report = _build_report(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print("Failed to build operations readiness report: %s" % exc, file=sys.stderr)
        return 2

    summary = _render_summary(report)
    output_value = str(args.output or "").strip()
    summary_output_value = str(args.summary_output or "").strip()
    if output_value and output_value != "-":
        output_path = Path(output_value).resolve()
        _write_text(output_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print("Operations readiness report written: %s" % output_path)
    if summary_output_value and summary_output_value != "-":
        summary_path = Path(summary_output_value).resolve()
        _write_text(summary_path, summary)
        print("Operations readiness summary written: %s" % summary_path)

    print(
        "Operations readiness status=%s checks=%s pass=%s fail=%s"
        % (
            report.get("overall_status", "fail"),
            report.get("check_count", 0),
            report.get("pass_count", 0),
            report.get("fail_count", 0),
        )
    )
    if report.get("failed_checks"):
        print("Failed checks: %s" % ", ".join(report["failed_checks"]))
    else:
        print("Failed checks: none")

    if args.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.print_summary:
        print(summary.rstrip())
    return 0 if report.get("overall_status") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
