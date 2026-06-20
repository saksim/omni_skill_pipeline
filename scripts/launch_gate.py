from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent_smoke import TARGET_AGENTS, build_matrix_report


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CURRENT_STATUS_DOC = REPO_ROOT / "docs" / "working" / "status" / "CURRENT_STATUS.md"
DEFAULT_RELEASE_SWITCH_REPORT = (
    REPO_ROOT / "docs" / "working" / "status" / "baselines" / "e13-release-switch-decision-report.json"
)
DEFAULT_TRIAL_METRICS_REPORT = (
    REPO_ROOT / "docs" / "working" / "status" / "baselines" / "controlled-trial" / "trial-metrics-report.json"
)
DEFAULT_CONTROLLED_TRIAL_RUN_REPORT = (
    REPO_ROOT / "docs" / "working" / "status" / "baselines" / "controlled-trial" / "controlled-trial-run-report.json"
)
DEFAULT_AGENT_SMOKE_REPORT = (
    REPO_ROOT / "docs" / "working" / "status" / "baselines" / "controlled-trial" / "agent-smoke-report.json"
)
DEFAULT_DOC_SYNC_REPORT = (
    REPO_ROOT / "docs" / "working" / "status" / "baselines" / "e13-doc-sync-check-report.json"
)
DEFAULT_OPERATIONS_READINESS_REPORT = (
    REPO_ROOT / "docs" / "working" / "status" / "baselines" / "operations-readiness-report.json"
)
DEFAULT_OUTPUT_PATH = (
    REPO_ROOT / "docs" / "working" / "status" / "baselines" / "broad-launch-readiness-report.json"
)
DEFAULT_SUMMARY_PATH = (
    REPO_ROOT / "docs" / "working" / "status" / "baselines" / "broad-launch-readiness-summary.md"
)

DECISIONS = (
    "HOLD",
    "READY_FOR_CONTROLLED_BETA",
    "READY_FOR_GA_REVIEW",
    "READY_FOR_PLATFORM_BETA",
)
LAUNCH_LEVELS = {
    "READY_FOR_CONTROLLED_BETA": {
        "name": "Controlled External Beta",
        "target": "1-3 friendly users, teams, or workflows with mandatory review.",
    },
    "READY_FOR_GA_REVIEW": {
        "name": "Single-Team GA Review",
        "target": "One team can use the system as an ongoing production workflow.",
    },
    "READY_FOR_PLATFORM_BETA": {
        "name": "Platform Beta / SaaS Candidate",
        "target": "Multiple organizations can use the product with tenant isolation.",
    },
}
FORBIDDEN_CLI_FLAGS = (
    "--dry-run",
    "--allow-regression",
    "--no-coverage",
    "--container-skip-build",
    "--container-skip-run",
    "--allow-secondary-failures",
    "--skip-security",
    "--skip-doc-sync",
)
FORBIDDEN_TRUTHY_KEYS = (
    "dry_run",
    "dryrun",
    "relaxed",
    "allow_regression",
    "no_coverage",
    "container_skip_build",
    "container_skip_run",
    "allow_secondary_failures",
    "skip_security",
    "skip_doc_sync",
    "security_skipped",
    "doc_sync_skipped",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate broad product launch readiness from release, trial, smoke, security, and docs evidence.",
    )
    parser.add_argument("--release-switch-report", default=str(DEFAULT_RELEASE_SWITCH_REPORT))
    parser.add_argument("--current-status-doc", default=str(DEFAULT_CURRENT_STATUS_DOC))
    parser.add_argument("--trial-metrics-report", default=str(DEFAULT_TRIAL_METRICS_REPORT))
    parser.add_argument("--controlled-trial-run-report", default=str(DEFAULT_CONTROLLED_TRIAL_RUN_REPORT))
    parser.add_argument("--agent-smoke-report", default=str(DEFAULT_AGENT_SMOKE_REPORT))
    parser.add_argument("--security-gate-report", default="")
    parser.add_argument("--doc-sync-report", default=str(DEFAULT_DOC_SYNC_REPORT))
    parser.add_argument("--operations-readiness-report", default=str(DEFAULT_OPERATIONS_READINESS_REPORT))
    parser.add_argument("--run-doc-sync", dest="run_doc_sync", action="store_true", default=True)
    parser.add_argument("--no-run-doc-sync", dest="run_doc_sync", action="store_false")
    parser.add_argument("--minimum-complete-loops", type=int, default=10)
    parser.add_argument("--minimum-modalities", type=int, default=4)
    parser.add_argument("--minimum-agent-smoke-success-rate", type=float, default=0.8)
    parser.add_argument("--maximum-provider-failure-rate", type=float, default=0.05)
    parser.add_argument(
        "--max-evidence-age-hours",
        type=float,
        default=336.0,
        help="Maximum evidence file age. Set <=0 to disable local mtime freshness checks.",
    )
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH), help='JSON report output path. Use "-" to skip.')
    parser.add_argument(
        "--summary-output",
        default=str(DEFAULT_SUMMARY_PATH),
        help='Markdown summary output path. Use "-" to skip.',
    )
    parser.add_argument("--print-json", action="store_true")
    parser.add_argument("--print-summary", action="store_true")
    parser.add_argument("--fail-on-hold", action="store_true")
    return parser.parse_args()


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("JSON evidence root must be an object: %s" % path)
    return payload


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() not in ("", "0", "false", "no", "none", "null")
    return value is not None


def _status_is_pass(value: Any) -> bool:
    return str(value or "").strip().lower() in {
        "pass",
        "passed",
        "ok",
        "success",
        "go",
        "agent_smoke_passed",
    }


def _status_is_go(value: Any) -> bool:
    return str(value or "").strip().upper() == "GO"


def _normalise_key(key: str) -> str:
    return key.strip().lower().replace("-", "_").replace(" ", "_")


def _find_forbidden_markers(payload: Any, *, source: str, path: str = "$") -> list[dict[str, str]]:
    markers: list[dict[str, str]] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            normalised = _normalise_key(str(key))
            if normalised == "disabled_checks" and isinstance(value, list) and value:
                markers.append({"source": source, "path": "%s.%s" % (path, key), "reason": "disabled_checks"})
            if normalised in FORBIDDEN_TRUTHY_KEYS and _truthy(value):
                markers.append({"source": source, "path": "%s.%s" % (path, key), "reason": normalised})
            markers.extend(_find_forbidden_markers(value, source=source, path="%s.%s" % (path, key)))
    elif isinstance(payload, list):
        for index, item in enumerate(payload):
            markers.extend(_find_forbidden_markers(item, source=source, path="%s[%s]" % (path, index)))
    elif isinstance(payload, str):
        lowered = payload.lower()
        for flag in FORBIDDEN_CLI_FLAGS:
            if flag in lowered:
                markers.append({"source": source, "path": path, "reason": flag})
    return markers


def _condition_by_id(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    criteria = report.get("success_criteria", {})
    if not isinstance(criteria, dict):
        return {}
    conditions = criteria.get("conditions", [])
    if not isinstance(conditions, list):
        return {}
    output: dict[str, dict[str, Any]] = {}
    for item in conditions:
        if isinstance(item, dict) and item.get("id"):
            output[str(item["id"])] = item
    return output


def _make_check(
    check_id: str,
    status: str,
    actual: Any,
    expected: Any,
    *,
    blocking: bool = True,
    details: str = "",
) -> dict[str, Any]:
    return {
        "id": check_id,
        "status": status,
        "blocking": blocking,
        "actual": actual,
        "expected": expected,
        "details": details,
    }


def _extract_release_decision(
    *,
    release_report: dict[str, Any] | None,
    trial_metrics_report: dict[str, Any] | None,
    current_status_path: Path,
) -> tuple[str | None, str]:
    if release_report is not None:
        for key in ("decision", "release_switch_decision", "latest_release_decision"):
            if release_report.get(key):
                return str(release_report[key]).strip().upper(), "release_switch_report.%s" % key
        gate_rows = release_report.get("gate_rows", [])
        if isinstance(gate_rows, list) and gate_rows:
            hold_rows = [
                item
                for item in gate_rows
                if isinstance(item, dict) and str(item.get("status", "")).strip().lower() not in ("pass", "passed")
            ]
            return ("HOLD" if hold_rows else "GO"), "release_switch_report.gate_rows"

    if trial_metrics_report is not None:
        release_condition = _condition_by_id(trial_metrics_report).get("release_run_go")
        if release_condition:
            actual = release_condition.get("actual")
            if actual:
                return str(actual).strip().upper(), "trial_metrics.release_run_go"

    if current_status_path.is_file():
        text = current_status_path.read_text(encoding="utf-8", errors="replace")
        if "Release switch decision" in text and "`GO`" in text:
            return "GO", "CURRENT_STATUS.md"
        if "release run" in text.lower() and "`GO`" in text:
            return "GO", "CURRENT_STATUS.md"
    return None, "missing"


def _evaluate_trial_metrics(report: dict[str, Any], *, minimum_loops: int, minimum_modalities: int) -> list[dict[str, Any]]:
    metrics = report.get("trial_metrics", {})
    if not isinstance(metrics, dict):
        metrics = {}
    conditions = _condition_by_id(report)
    complete_loop_count_total = int(metrics.get("complete_loop_count") or 0)
    complete_modalities_total = metrics.get("complete_modalities", [])
    modality_count_total = len(complete_modalities_total) if isinstance(complete_modalities_total, list) else 0

    launch_gate_evidence = metrics.get("launch_gate_evidence", {})
    if not isinstance(launch_gate_evidence, dict):
        launch_gate_evidence = {}
    if "complete_loop_count" in launch_gate_evidence:
        complete_loop_count = int(launch_gate_evidence.get("complete_loop_count") or 0)
    else:
        complete_loop_count = complete_loop_count_total
    if "complete_modalities" in launch_gate_evidence:
        complete_modalities = launch_gate_evidence.get("complete_modalities", [])
    else:
        complete_modalities = complete_modalities_total
    modality_count = len(complete_modalities) if isinstance(complete_modalities, list) else modality_count_total
    unlabeled_loop_count = int(launch_gate_evidence.get("unlabeled_loop_count") or 0)

    coverage_condition = conditions.get("launch_gate_eligible_loop_volume_and_modality_coverage")
    coverage_status = (
        str(coverage_condition.get("status", "")).lower() == "pass"
        if coverage_condition is not None
        else complete_loop_count >= minimum_loops and modality_count >= minimum_modalities
    )

    checks = [
        _make_check(
            "trial_loop_volume_and_modality_coverage",
            "pass" if coverage_status else "fail",
            {
                "launch_gate_eligible_complete_loops": complete_loop_count,
                "launch_gate_eligible_modalities": modality_count,
                "total_complete_loops": complete_loop_count_total,
                "total_modalities": modality_count_total,
            },
            {
                "minimum_complete_loops": minimum_loops,
                "minimum_modalities": minimum_modalities,
                "evidence_origin": "real",
            },
            details="Controlled external Beta requires enough real launch-gate-eligible loop and modality coverage.",
        )
    ]
    evidence_origin_condition = conditions.get("loop_evidence_origin_labeled")
    evidence_origin_status = (
        str(evidence_origin_condition.get("status", "")).lower() == "pass"
        if evidence_origin_condition is not None
        else unlabeled_loop_count == 0
    )
    checks.append(
        _make_check(
            "trial_loop_evidence_origin_labeled",
            "pass" if evidence_origin_status else "fail",
            {"unlabeled_loop_count": unlabeled_loop_count},
            {"unlabeled_loop_count": 0},
            details="Each loop must explicitly label evidence_origin and launch_gate_eligible semantics.",
        )
    )
    real_evidence_source_trace_condition = conditions.get("real_evidence_source_trace_complete")
    real_evidence_missing_source_trace_count = int(
        launch_gate_evidence.get("real_evidence_missing_source_trace_count") or 0
    )
    real_evidence_source_trace_status = (
        str(real_evidence_source_trace_condition.get("status", "")).lower() == "pass"
        if real_evidence_source_trace_condition is not None
        else real_evidence_missing_source_trace_count == 0
    )
    checks.append(
        _make_check(
            "trial_real_evidence_source_trace_complete",
            "pass" if real_evidence_source_trace_status else "fail",
            {"missing_source_trace_count": real_evidence_missing_source_trace_count},
            {"missing_source_trace_count": 0},
            details="Every real-evidence loop must include source_system/source_reference/collected_at_utc trace.",
        )
    )
    real_evidence_review_trace_condition = conditions.get("real_evidence_review_trace_complete")
    real_evidence_missing_review_trace_count = int(
        launch_gate_evidence.get("real_evidence_missing_review_trace_count") or 0
    )
    real_evidence_review_trace_status = (
        str(real_evidence_review_trace_condition.get("status", "")).lower() == "pass"
        if real_evidence_review_trace_condition is not None
        else real_evidence_missing_review_trace_count == 0
    )
    checks.append(
        _make_check(
            "trial_real_evidence_review_trace_complete",
            "pass" if real_evidence_review_trace_status else "fail",
            {"missing_review_trace_count": real_evidence_missing_review_trace_count},
            {"missing_review_trace_count": 0},
            details="Every real-evidence loop must include review_task_id/reviewed_by/reviewed_at_utc trace.",
        )
    )
    real_evidence_template_placeholders_condition = conditions.get("real_evidence_template_placeholders_replaced")
    real_evidence_template_placeholder_loop_count = int(
        launch_gate_evidence.get("real_evidence_template_placeholder_loop_count") or 0
    )
    real_evidence_template_placeholder_field_count = int(
        launch_gate_evidence.get("real_evidence_template_placeholder_field_count") or 0
    )
    real_evidence_template_placeholders_status = (
        str(real_evidence_template_placeholders_condition.get("status", "")).lower() == "pass"
        if real_evidence_template_placeholders_condition is not None
        else real_evidence_template_placeholder_loop_count == 0
    )
    checks.append(
        _make_check(
            "trial_real_evidence_template_placeholders_replaced",
            "pass" if real_evidence_template_placeholders_status else "fail",
            {
                "placeholder_loop_count": real_evidence_template_placeholder_loop_count,
                "placeholder_field_count": real_evidence_template_placeholder_field_count,
            },
            {
                "placeholder_loop_count": 0,
                "placeholder_field_count": 0,
            },
            details=(
                "Every real-evidence loop must replace GL-31 TEMPLATE_REQUIRED_* placeholders "
                "before launch-gate eligibility."
            ),
        )
    )

    safety = metrics.get("safety", {})
    if not isinstance(safety, dict):
        safety = {}
    unreviewed = int(safety.get("unreviewed_published_count") or 0)
    critical_leaks = int(safety.get("critical_secret_or_pii_leak_count") or 0)
    high_incidents = int(safety.get("high_severity_incident_count") or 0)
    checks.append(
        _make_check(
            "trial_safety_counts",
            "pass" if unreviewed == 0 and critical_leaks == 0 and high_incidents == 0 else "fail",
            {
                "unreviewed_published_count": unreviewed,
                "critical_secret_or_pii_leak_count": critical_leaks,
                "high_severity_incident_count": high_incidents,
            },
            {
                "unreviewed_published_count": 0,
                "critical_secret_or_pii_leak_count": 0,
                "high_severity_incident_count": 0,
            },
            details="Launch cannot proceed with unreviewed publication, critical leaks, or high-severity incidents.",
        )
    )

    condition_ids = (
        "reviewer_approval_rate",
        "median_reviewer_edit_distance",
        "provider_failure_rate",
        "cost_per_accepted_skill",
    )
    failed_conditions = [
        condition_id
        for condition_id in condition_ids
        if condition_id in conditions and str(conditions[condition_id].get("status", "")).lower() != "pass"
    ]
    checks.append(
        _make_check(
            "trial_quality_conditions",
            "pass" if not failed_conditions else "fail",
            failed_conditions,
            "all quality/cost/provider conditions pass",
            details="Reviewer, provider, and cost conditions must remain within launch thresholds.",
        )
    )
    return checks


def _evaluate_security_evidence(
    *,
    security_report: dict[str, Any] | None,
    trial_metrics_report: dict[str, Any] | None,
    trial_run_report: dict[str, Any] | None,
) -> dict[str, Any]:
    if security_report is not None:
        status = security_report.get("status", security_report.get("overall_status"))
        failure_codes = security_report.get("failure_codes", [])
        return _make_check(
            "security_gate_evidence",
            "pass" if _status_is_pass(status) and not failure_codes else "fail",
            {"status": status, "failure_codes": failure_codes},
            {"status": "pass", "failure_codes": []},
            details="Explicit trial security gate report.",
        )

    if trial_metrics_report is not None:
        conditions = _condition_by_id(trial_metrics_report)
        condition = conditions.get("no_critical_secret_or_pii_leak")
        if condition is not None:
            return _make_check(
                "security_gate_evidence",
                "pass" if str(condition.get("status", "")).lower() == "pass" else "fail",
                condition.get("actual"),
                condition.get("expected", 0),
                details="Security evidence inferred from trial metrics condition no_critical_secret_or_pii_leak.",
            )

    if trial_run_report is not None:
        samples = trial_run_report.get("samples", [])
        evidence_count = 0
        critical_leak_count = 0
        validator_fail_count = 0
        if isinstance(samples, list):
            for sample in samples:
                if not isinstance(sample, dict):
                    continue
                loop_metrics = sample.get("loop_metrics", {})
                if isinstance(loop_metrics, dict) and "critical_secret_or_pii_leak" in loop_metrics:
                    evidence_count += 1
                    if bool(loop_metrics.get("critical_secret_or_pii_leak")):
                        critical_leak_count += 1
                validator_reports = sample.get("validator_reports", [])
                if isinstance(validator_reports, list) and validator_reports:
                    evidence_count += len(validator_reports)
                    validator_fail_count += sum(
                        1
                        for report in validator_reports
                        if isinstance(report, dict) and not _status_is_pass(report.get("status"))
                    )
        if evidence_count:
            return _make_check(
                "security_gate_evidence",
                "pass" if critical_leak_count == 0 and validator_fail_count == 0 else "fail",
                {
                    "security_evidence_count": evidence_count,
                    "critical_leak_count": critical_leak_count,
                    "validator_fail_count": validator_fail_count,
                },
                {"critical_leak_count": 0, "validator_fail_count": 0},
                details="Security evidence inferred from controlled-trial run artifacts.",
            )

    return _make_check(
        "security_gate_evidence",
        "fail",
        "missing",
        "security gate report or equivalent trial security evidence",
        details="Missing security evidence keeps launch decision at HOLD.",
    )


def _evaluate_agent_smoke(report: dict[str, Any], *, minimum_success_rate: float) -> dict[str, Any]:
    records = report.get("records", [])
    if not isinstance(records, list) or not records:
        return _make_check(
            "agent_smoke_success_rate",
            "fail",
            {"record_count": 0, "success_rate": 0.0},
            {"minimum_success_rate": minimum_success_rate},
            details="Agent smoke report must include at least one executable record.",
        )
    passed = 0
    for record in records:
        if not isinstance(record, dict):
            continue
        if _status_is_pass(record.get("metrics_agent_smoke_result")) or _status_is_pass(record.get("status")):
            passed += 1
    success_rate = passed / len(records)
    return _make_check(
        "agent_smoke_success_rate",
        "pass" if success_rate >= minimum_success_rate else "fail",
        {"record_count": len(records), "passed": passed, "success_rate": success_rate},
        {"minimum_success_rate": minimum_success_rate},
        details="Approved skills must work in the target agent smoke matrix.",
    )


def _agent_smoke_required_skill_ids(report: dict[str, Any]) -> list[str]:
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


def _evaluate_agent_smoke_matrix(report: dict[str, Any]) -> dict[str, Any]:
    matrix_report = build_matrix_report(
        report,
        required_skill_ids=_agent_smoke_required_skill_ids(report),
        target_agents=list(TARGET_AGENTS),
    )
    counts = matrix_report.get("counts", {})
    status = str(matrix_report.get("status", "")).strip()
    return _make_check(
        "agent_smoke_matrix_coverage",
        "pass" if status == "AGENT_SMOKE_MATRIX_READY" else "fail",
        {
            "matrix_status": status,
            "required_skill_count": int(counts.get("required_skill_count", 0) or 0),
            "target_agents": matrix_report.get("target_agents", []),
            "expected_cell_count": int(counts.get("expected_cell_count", 0) or 0),
            "recorded_cell_count": int(counts.get("recorded_cell_count", 0) or 0),
            "missing_cell_count": int(counts.get("missing_cell_count", 0) or 0),
            "invalid_record_count": int(counts.get("invalid_record_count", 0) or 0),
            "missing_cells": matrix_report.get("missing_cells", []),
            "invalid_records": matrix_report.get("invalid_records", []),
        },
        {
            "matrix_status": "AGENT_SMOKE_MATRIX_READY",
            "target_agents": list(TARGET_AGENTS),
        },
        details=(
            "Each approved skill in the agent smoke report must have a valid Codex, "
            "Claude Code, and OpenCode record."
        ),
    )


def _run_doc_sync() -> tuple[dict[str, Any] | None, str]:
    script = REPO_ROOT / "scripts" / "doc_sync.py"
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "doc-sync-report.json"
        completed = subprocess.run(
            [sys.executable, str(script), "--output", str(output_path)],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            if output_path.is_file():
                try:
                    return _read_json(output_path), completed.stdout + completed.stderr
                except (OSError, json.JSONDecodeError, ValueError):
                    pass
            return None, completed.stdout + completed.stderr
        return _read_json(output_path), completed.stdout + completed.stderr


def _evaluate_doc_sync(*, report: dict[str, Any] | None, source: str) -> dict[str, Any]:
    if report is None:
        return _make_check(
            "doc_sync_status",
            "fail",
            "missing",
            "doc sync status pass",
            details="Missing doc-sync evidence keeps launch decision at HOLD.",
        )
    status = report.get("status")
    failed_count = int(report.get("failed_count") or 0)
    return _make_check(
        "doc_sync_status",
        "pass" if _status_is_pass(status) and failed_count == 0 else "fail",
        {"status": status, "failed_count": failed_count, "source": source},
        {"status": "pass", "failed_count": 0},
        details="Documentation entry points must match current source surfaces.",
    )


def _evaluate_freshness(paths: dict[str, Path], *, max_age_hours: float) -> dict[str, Any]:
    if max_age_hours <= 0:
        return _make_check(
            "evidence_freshness",
            "pass",
            "disabled",
            "fresh evidence",
            blocking=True,
            details="Freshness check disabled by CLI.",
        )
    now = datetime.now(timezone.utc)
    stale: list[dict[str, Any]] = []
    checked: list[str] = []
    for name, path in paths.items():
        if not path.is_file():
            continue
        checked.append(name)
        modified = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
        age_hours = (now - modified).total_seconds() / 3600.0
        if age_hours > max_age_hours:
            stale.append({"name": name, "path": str(path), "age_hours": round(age_hours, 3)})
    return _make_check(
        "evidence_freshness",
        "pass" if not stale else "fail",
        {"checked": checked, "stale": stale},
        {"max_age_hours": max_age_hours, "stale": []},
        details="Stale local evidence cannot support launch readiness.",
    )


def _evaluate_operations_readiness(report: dict[str, Any] | None) -> dict[str, Any]:
    if report is None:
        return _make_check(
            "operations_readiness_status",
            "fail",
            "missing",
            {"overall_status": "pass", "fail_count": 0},
            details="Missing operations-readiness evidence keeps launch decision at HOLD.",
        )
    status = str(report.get("overall_status", "")).strip().lower()
    fail_count = int(report.get("fail_count") or 0)
    return _make_check(
        "operations_readiness_status",
        "pass" if status == "pass" and fail_count == 0 else "fail",
        {"overall_status": status, "fail_count": fail_count},
        {"overall_status": "pass", "fail_count": 0},
        details="Production operations evidence must pass before GA-review readiness can be claimed.",
    )


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _render_markdown(report: dict[str, Any]) -> str:
    failed = report.get("failed_checks", [])
    lines = [
        "# Broad Launch Readiness Summary",
        "",
        "- Decision: `%s`" % report.get("decision", "HOLD"),
        "- Controlled Beta status: `%s`" % ("ready" if report.get("decision") != "HOLD" else "blocked"),
        "- Trial coverage: `%s/%s` complete loops, `%s/%s` modalities"
        % (
            report.get("summary", {}).get("complete_loops", 0),
            report.get("summary", {}).get("minimum_complete_loops", 10),
            report.get("summary", {}).get("modalities", 0),
            report.get("summary", {}).get("minimum_modalities", 4),
        ),
        "- Blocking checks: `%s`" % (", ".join(failed) if failed else "none"),
        "",
        "## Checks",
        "",
    ]
    for check in report.get("checks", []):
        lines.append("- `%s`: `%s`" % (check.get("id"), check.get("status")))
    lines.append("")
    return "\n".join(lines)


def _build_report(args: argparse.Namespace) -> dict[str, Any]:
    release_report_path = Path(args.release_switch_report).resolve()
    current_status_path = Path(args.current_status_doc).resolve()
    trial_metrics_path = Path(args.trial_metrics_report).resolve()
    trial_run_path = Path(args.controlled_trial_run_report).resolve()
    agent_smoke_path = Path(args.agent_smoke_report).resolve()
    doc_sync_path = Path(args.doc_sync_report).resolve()
    operations_readiness_path = Path(args.operations_readiness_report).resolve()
    security_report_path = Path(args.security_gate_report).resolve() if str(args.security_gate_report).strip() else None

    loaded: dict[str, Any] = {}
    evidence_paths = {
        "release_switch_report": str(release_report_path),
        "current_status_doc": str(current_status_path),
        "trial_metrics_report": str(trial_metrics_path),
        "controlled_trial_run_report": str(trial_run_path),
        "agent_smoke_report": str(agent_smoke_path),
        "security_gate_report": str(security_report_path) if security_report_path else "",
        "doc_sync_report": str(doc_sync_path),
        "operations_readiness_report": str(operations_readiness_path),
    }
    checks: list[dict[str, Any]] = []

    release_report = _read_json(release_report_path) if release_report_path.is_file() else None
    if release_report is not None:
        loaded["release_switch_report"] = release_report

    try:
        trial_metrics_report = _read_json(trial_metrics_path)
        loaded["trial_metrics_report"] = trial_metrics_report
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        trial_metrics_report = None
        checks.append(
            _make_check(
                "trial_metrics_evidence",
                "fail",
                str(exc),
                "readable trial metrics report",
                details="Trial metrics evidence is required.",
            )
        )

    trial_run_report = None
    if trial_run_path.is_file():
        try:
            trial_run_report = _read_json(trial_run_path)
            loaded["controlled_trial_run_report"] = trial_run_report
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            checks.append(
                _make_check(
                    "controlled_trial_run_evidence",
                    "fail",
                    str(exc),
                    "readable controlled trial run report",
                    details="Run report is needed for security fallback evidence.",
                )
            )

    security_report = None
    if security_report_path is not None and security_report_path.is_file():
        security_report = _read_json(security_report_path)
        loaded["security_gate_report"] = security_report

    if agent_smoke_path.is_file():
        try:
            agent_smoke_report = _read_json(agent_smoke_path)
            loaded["agent_smoke_report"] = agent_smoke_report
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            agent_smoke_report = None
            checks.append(
                _make_check(
                    "agent_smoke_evidence",
                    "fail",
                    str(exc),
                    "readable agent smoke report",
                    details="Agent smoke evidence is required.",
                )
            )
    else:
        agent_smoke_report = None
        checks.append(
            _make_check(
                "agent_smoke_evidence",
                "fail",
                "missing",
                "readable agent smoke report",
                details="Agent smoke evidence is required.",
            )
        )

    if args.run_doc_sync:
        doc_sync_report, doc_sync_log = _run_doc_sync()
        loaded["doc_sync_report"] = doc_sync_report or {"status": "fail", "log": doc_sync_log}
        doc_sync_source = "doc_sync.py"
    elif doc_sync_path.is_file():
        doc_sync_report = _read_json(doc_sync_path)
        loaded["doc_sync_report"] = doc_sync_report
        doc_sync_source = str(doc_sync_path)
    else:
        doc_sync_report = None
        doc_sync_source = "missing"

    if operations_readiness_path.is_file():
        try:
            operations_readiness_report = _read_json(operations_readiness_path)
            loaded["operations_readiness_report"] = operations_readiness_report
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            operations_readiness_report = None
            checks.append(
                _make_check(
                    "operations_readiness_evidence",
                    "fail",
                    str(exc),
                    "readable operations readiness report",
                    details="Operations readiness evidence is required for broad launch operations claims.",
                )
            )
    else:
        operations_readiness_report = None
        checks.append(
            _make_check(
                "operations_readiness_evidence",
                "fail",
                "missing",
                "readable operations readiness report",
                details="Operations readiness evidence is required for broad launch operations claims.",
            )
        )

    release_decision, release_source = _extract_release_decision(
        release_report=release_report,
        trial_metrics_report=trial_metrics_report,
        current_status_path=current_status_path,
    )
    checks.append(
        _make_check(
            "release_switch_go",
            "pass" if _status_is_go(release_decision) else "fail",
            {"decision": release_decision, "source": release_source},
            "GO",
            details="Latest strict release switch evidence must remain GO.",
        )
    )

    if trial_metrics_report is not None:
        checks.append(
            _make_check(
                "trial_metrics_evidence",
                "pass",
                str(trial_metrics_path),
                "readable trial metrics report",
                details="Trial metrics report is present.",
            )
        )
        checks.extend(
            _evaluate_trial_metrics(
                trial_metrics_report,
                minimum_loops=max(1, int(args.minimum_complete_loops)),
                minimum_modalities=max(1, int(args.minimum_modalities)),
            )
        )

    checks.append(
        _evaluate_security_evidence(
            security_report=security_report,
            trial_metrics_report=trial_metrics_report,
            trial_run_report=trial_run_report,
        )
    )

    if agent_smoke_report is not None:
        checks.append(
            _evaluate_agent_smoke(
                agent_smoke_report,
                minimum_success_rate=max(0.0, min(1.0, float(args.minimum_agent_smoke_success_rate))),
            )
        )
        checks.append(_evaluate_agent_smoke_matrix(agent_smoke_report))

    checks.append(_evaluate_doc_sync(report=doc_sync_report, source=doc_sync_source))
    checks.append(_evaluate_operations_readiness(operations_readiness_report))

    forbidden_markers: list[dict[str, str]] = []
    for source, payload in loaded.items():
        forbidden_markers.extend(_find_forbidden_markers(payload, source=source))
    checks.append(
        _make_check(
            "no_dry_run_relaxed_or_skipped_evidence",
            "pass" if not forbidden_markers else "fail",
            forbidden_markers,
            [],
            details="Launch evidence cannot rely on dry-run, relaxed flags, disabled checks, or skipped gates.",
        )
    )

    freshness_paths = {
        "current_status_doc": current_status_path,
        "trial_metrics_report": trial_metrics_path,
        "controlled_trial_run_report": trial_run_path,
        "agent_smoke_report": agent_smoke_path,
    }
    if release_report_path.is_file():
        freshness_paths["release_switch_report"] = release_report_path
    if security_report_path is not None and security_report_path.is_file():
        freshness_paths["security_gate_report"] = security_report_path
    if not args.run_doc_sync:
        freshness_paths["doc_sync_report"] = doc_sync_path
    if operations_readiness_path.is_file():
        freshness_paths["operations_readiness_report"] = operations_readiness_path
    checks.append(_evaluate_freshness(freshness_paths, max_age_hours=float(args.max_evidence_age_hours)))

    failed_checks = [check["id"] for check in checks if check.get("blocking") and check.get("status") != "pass"]
    metrics = trial_metrics_report.get("trial_metrics", {}) if isinstance(trial_metrics_report, dict) else {}
    complete_modalities = metrics.get("complete_modalities", []) if isinstance(metrics, dict) else []
    launch_gate_evidence = metrics.get("launch_gate_evidence", {}) if isinstance(metrics, dict) else {}
    launch_gate_modalities = (
        launch_gate_evidence.get("complete_modalities", [])
        if isinstance(launch_gate_evidence, dict)
        else []
    )
    summary = {
        "complete_loops_total": int(metrics.get("complete_loop_count") or 0) if isinstance(metrics, dict) else 0,
        "complete_loops": (
            int(launch_gate_evidence.get("complete_loop_count") or 0)
            if isinstance(launch_gate_evidence, dict)
            else 0
        ),
        "minimum_complete_loops": max(1, int(args.minimum_complete_loops)),
        "modalities_total": len(complete_modalities) if isinstance(complete_modalities, list) else 0,
        "modalities": len(launch_gate_modalities) if isinstance(launch_gate_modalities, list) else 0,
        "minimum_modalities": max(1, int(args.minimum_modalities)),
    }
    decision = "HOLD" if failed_checks else "READY_FOR_CONTROLLED_BETA"
    return {
        "schema_version": "broad_launch_readiness.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "decision_code": DECISIONS.index(decision),
        "launch_levels": LAUNCH_LEVELS,
        "summary": summary,
        "failed_checks": failed_checks,
        "check_count": len(checks),
        "pass_count": len([check for check in checks if check.get("status") == "pass"]),
        "fail_count": len([check for check in checks if check.get("status") != "pass"]),
        "checks": checks,
        "evidence_paths": evidence_paths,
    }


def main() -> int:
    args = _parse_args()
    try:
        report = _build_report(args)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print("Launch readiness gate failed: %s" % exc, file=sys.stderr)
        return 2

    summary = _render_markdown(report)
    output_value = str(args.output or "").strip()
    summary_output_value = str(args.summary_output or "").strip()
    if output_value and output_value != "-":
        output_path = Path(output_value).resolve()
        _write_text(output_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print("Launch readiness report written: %s" % output_path)
    if summary_output_value and summary_output_value != "-":
        summary_path = Path(summary_output_value).resolve()
        _write_text(summary_path, summary)
        print("Launch readiness summary written: %s" % summary_path)

    print(
        "Launch readiness decision=%s checks=%s pass=%s fail=%s"
        % (report["decision"], report["check_count"], report["pass_count"], report["fail_count"])
    )
    if report["failed_checks"]:
        print("Blocking checks: %s" % ", ".join(report["failed_checks"]))
    else:
        print("Blocking checks: none")
    if args.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.print_summary:
        print(summary.rstrip())
    if args.fail_on_hold and report.get("decision") == "HOLD":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
