from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_SCHEMA_VERSION = "observability_readiness.v1"
LIVE_EVIDENCE_SCHEMA_VERSION = "observability_live_evidence.v1"

DEFAULT_TRIAL_METRICS_REPORT = (
    REPO_ROOT / "docs" / "working" / "status" / "baselines" / "controlled-trial" / "trial-metrics-report.json"
)
DEFAULT_AGENT_SMOKE_REPORT = (
    REPO_ROOT / "docs" / "working" / "status" / "baselines" / "controlled-trial" / "agent-smoke-report.json"
)
DEFAULT_RELEASE_GATE_PLAN = REPO_ROOT / "docs" / "working" / "status" / "baselines" / "e13-release-gate-validation-plan.json"
DEFAULT_LAUNCH_GATE_REPORT = REPO_ROOT / "docs" / "working" / "status" / "baselines" / "broad-launch-readiness-report.json"
DEFAULT_CONSOLE_SOURCE = REPO_ROOT / "src" / "omni_skill_pipeline" / "platform_console.py"
DEFAULT_TESTING_DOC = REPO_ROOT / "docs" / "latest" / "operations" / "testing.md"
DEFAULT_SCRIPT_MAP = REPO_ROOT / "docs" / "latest" / "operations" / "script-name-map.md"
DEFAULT_OPERATIONS_RUNBOOK = REPO_ROOT / "docs" / "latest" / "operations" / "runbooks" / "production-operations-baseline.md"
DEFAULT_LIVE_EVIDENCE = REPO_ROOT / "docs" / "working" / "status" / "baselines" / "observability-live-evidence.json"
DEFAULT_OUTPUT = REPO_ROOT / "docs" / "working" / "status" / "baselines" / "observability-readiness-report.json"
DEFAULT_SUMMARY_OUTPUT = REPO_ROOT / "docs" / "working" / "status" / "baselines" / "observability-readiness-summary.md"

REQUIRED_TRIAL_METRIC_PATHS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("trial_metrics.loop_count", ("trial_metrics", "loop_count")),
    ("trial_metrics.complete_loop_count", ("trial_metrics", "complete_loop_count")),
    ("trial_metrics.complete_modalities", ("trial_metrics", "complete_modalities")),
    ("trial_metrics.latency_ms.average", ("trial_metrics", "latency_ms", "average")),
    ("trial_metrics.latency_ms.samples", ("trial_metrics", "latency_ms", "samples")),
    ("trial_metrics.provider_runtime.provider_failure_count_total", ("trial_metrics", "provider_runtime", "provider_failure_count_total")),
    ("trial_metrics.provider_runtime.provider_call_count_total", ("trial_metrics", "provider_runtime", "provider_call_count_total")),
    ("trial_metrics.provider_runtime.provider_failure_rate", ("trial_metrics", "provider_runtime", "provider_failure_rate")),
    ("trial_metrics.provider_runtime.retry_count_total", ("trial_metrics", "provider_runtime", "retry_count_total")),
    (
        "trial_metrics.provider_runtime.retry_count_average_per_loop",
        ("trial_metrics", "provider_runtime", "retry_count_average_per_loop"),
    ),
    ("trial_metrics.review_outcome_counts", ("trial_metrics", "review_outcome_counts")),
    ("trial_metrics.reviewer_edit_distance_pct.median", ("trial_metrics", "reviewer_edit_distance_pct", "median")),
    ("trial_metrics.reviewer_edit_distance_pct.samples", ("trial_metrics", "reviewer_edit_distance_pct", "samples")),
    ("trial_metrics.review_quality.review_evaluable_count", ("trial_metrics", "review_quality", "review_evaluable_count")),
    (
        "trial_metrics.review_quality.approval_rate_after_one_revision",
        ("trial_metrics", "review_quality", "approval_rate_after_one_revision"),
    ),
    ("trial_metrics.review_quality.agent_smoke_success_rate", ("trial_metrics", "review_quality", "agent_smoke_success_rate")),
    ("trial_metrics.safety.critical_secret_or_pii_leak_count", ("trial_metrics", "safety", "critical_secret_or_pii_leak_count")),
    ("trial_metrics.safety.unreviewed_published_count", ("trial_metrics", "safety", "unreviewed_published_count")),
    ("trial_metrics.launch_gate_evidence.complete_loop_count", ("trial_metrics", "launch_gate_evidence", "complete_loop_count")),
    ("trial_metrics.launch_gate_evidence.complete_modalities", ("trial_metrics", "launch_gate_evidence", "complete_modalities")),
    ("trial_metrics.launch_gate_evidence.evidence_origin_counts", ("trial_metrics", "launch_gate_evidence", "evidence_origin_counts")),
)
REQUIRED_CONSOLE_MARKERS = (
    "job_runtime",
    "modality_success",
    "human_review_scores",
    "agent_smoke",
    "release_artifact_evidence",
    "redaction_secret_failures",
)
REQUIRED_RELEASE_MARKERS = (
    "scripts/release_artifacts.py",
    "scripts/release_consumer_smoke.py",
    "release_artifacts.json",
    "release_consumer_smoke.json",
    "container_smoke",
    "doc_sync",
    "quality_regression",
    "perf_cost_baseline",
)
REQUIRED_RUNBOOK_MARKERS = (
    "job duration",
    "job success/fail",
    "retry",
    "modality success rate",
    "human review scores",
    "release artifact build pass/fail",
    "agent smoke pass/fail",
    "redaction/secret access failures",
    "python scripts/observability_readiness.py",
)
REQUIRED_LIVE_STATUS_FIELDS = (
    "job_duration_status",
    "job_success_failure_status",
    "retry_status",
    "modality_success_status",
    "human_review_scores_status",
    "release_artifact_status",
    "agent_smoke_status",
    "redaction_secret_failure_status",
    "dashboard_status",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate the P2 observability readiness contract without claiming live production telemetry.",
    )
    parser.add_argument("--trial-metrics-report", default=str(DEFAULT_TRIAL_METRICS_REPORT))
    parser.add_argument("--agent-smoke-report", default=str(DEFAULT_AGENT_SMOKE_REPORT))
    parser.add_argument("--release-gate-plan", default=str(DEFAULT_RELEASE_GATE_PLAN))
    parser.add_argument("--launch-gate-report", default=str(DEFAULT_LAUNCH_GATE_REPORT))
    parser.add_argument("--console-source", default=str(DEFAULT_CONSOLE_SOURCE))
    parser.add_argument("--testing-doc", default=str(DEFAULT_TESTING_DOC))
    parser.add_argument("--script-map", default=str(DEFAULT_SCRIPT_MAP))
    parser.add_argument("--operations-runbook", default=str(DEFAULT_OPERATIONS_RUNBOOK))
    parser.add_argument("--live-evidence", default=str(DEFAULT_LIVE_EVIDENCE))
    parser.add_argument(
        "--require-live-evidence",
        action="store_true",
        help="Require external dashboard/transcript evidence for the observability workflow.",
    )
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help='JSON report output. Use "-" to skip writing.')
    parser.add_argument("--summary-output", default=str(DEFAULT_SUMMARY_OUTPUT), help='Markdown output. Use "-" to skip.')
    parser.add_argument("--print-json", action="store_true")
    parser.add_argument("--print-summary", action="store_true")
    parser.add_argument("--fail-on-blocked", action="store_true")
    return parser.parse_args()


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("JSON root must be an object: %s" % path)
    return payload


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _check(check_id: str, status: str, actual: Any, expected: Any, details: str = "") -> dict[str, Any]:
    return {
        "id": check_id,
        "status": status,
        "actual": actual,
        "expected": expected,
        "details": details,
    }


def _status_pass(value: Any) -> bool:
    return str(value or "").strip().lower() in {"pass", "passed", "ready", "ok", "true"}


def _as_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _path_present(payload: dict[str, Any], keys: tuple[str, ...]) -> bool:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return False
        current = current[key]
    return True


def _get_path(payload: dict[str, Any], keys: tuple[str, ...]) -> Any:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _check_trial_metrics_contract(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return _check("observability_trial_metrics_contract", "fail", "missing", str(path))
    try:
        payload = _read_json(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return _check("observability_trial_metrics_contract", "fail", str(exc), "valid JSON object")

    missing = [name for name, keys in REQUIRED_TRIAL_METRIC_PATHS if not _path_present(payload, keys)]
    invalid: list[str] = []
    if _as_int(_get_path(payload, ("trial_metrics", "loop_count"))) <= 0:
        invalid.append("trial_metrics.loop_count_non_positive")
    if _as_int(_get_path(payload, ("trial_metrics", "latency_ms", "samples"))) <= 0:
        invalid.append("trial_metrics.latency_ms.samples_non_positive")
    if _as_int(_get_path(payload, ("trial_metrics", "review_quality", "review_evaluable_count"))) <= 0:
        invalid.append("trial_metrics.review_quality.review_evaluable_count_non_positive")
    return _check(
        "observability_trial_metrics_contract",
        "pass" if not missing and not invalid else "fail",
        {"missing_paths": missing, "invalid": invalid},
        {"missing_paths": [], "invalid": []},
        details=(
            "Trial metrics must expose job duration, job success/fail, retry, modality, "
            "human review, agent smoke, and redaction/secret failure counters."
        ),
    )


def _check_agent_smoke_contract(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return _check("observability_agent_smoke_contract", "fail", "missing", str(path))
    try:
        payload = _read_json(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return _check("observability_agent_smoke_contract", "fail", str(exc), "valid JSON object")

    records = payload.get("records")
    records = records if isinstance(records, list) else []
    status_counts: dict[str, int] = {"passed": 0, "failed": 0, "not_run": 0, "unknown": 0}
    malformed = 0
    for item in records:
        if not isinstance(item, dict):
            malformed += 1
            continue
        if not str(item.get("agent", "")).strip():
            malformed += 1
        raw = str(item.get("metrics_agent_smoke_result") or item.get("status") or "").strip().lower()
        if raw in {"passed", "pass", "agent_smoke_passed"}:
            status_counts["passed"] += 1
        elif raw in {"failed", "fail", "agent_smoke_failed"}:
            status_counts["failed"] += 1
        elif raw == "not_run":
            status_counts["not_run"] += 1
        else:
            status_counts["unknown"] += 1
    invalid = []
    if not records:
        invalid.append("records_missing")
    if malformed:
        invalid.append("malformed_records")
    if status_counts["passed"] + status_counts["failed"] <= 0:
        invalid.append("no_executed_pass_fail_record")
    return _check(
        "observability_agent_smoke_contract",
        "pass" if not invalid else "fail",
        {"record_count": len(records), "status_counts": status_counts, "invalid": invalid},
        {"record_count": ">=1", "executed_pass_fail_record": ">=1", "invalid": []},
        details="Agent smoke observability must preserve pass/fail/not_run counts instead of only a boolean.",
    )


def _read_existing_text(paths: tuple[Path, ...]) -> tuple[str, list[str]]:
    chunks: list[str] = []
    missing: list[str] = []
    for path in paths:
        if path.is_file():
            chunks.append(_read_text(path))
        else:
            missing.append(str(path))
    return "\n".join(chunks), missing


def _check_console_contract(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return _check("observability_console_contract", "fail", "missing", str(path))
    text = _read_text(path)
    missing = [marker for marker in REQUIRED_CONSOLE_MARKERS if marker not in text]
    return _check(
        "observability_console_contract",
        "pass" if not missing else "fail",
        {"missing_markers": missing},
        {"missing_markers": []},
        details="Platform console metrics view must aggregate observability fields from existing evidence files.",
    )


def _check_release_artifact_contract(release_gate_plan: Path, script_map: Path) -> dict[str, Any]:
    text, missing_docs = _read_existing_text((release_gate_plan, script_map))
    missing_markers = [marker for marker in REQUIRED_RELEASE_MARKERS if marker not in text]
    return _check(
        "observability_release_artifact_contract",
        "pass" if not missing_docs and not missing_markers else "fail",
        {"missing_docs": missing_docs, "missing_markers": missing_markers},
        {"missing_docs": [], "missing_markers": []},
        details="Release artifact build pass/fail must remain tied to release artifact and consumer smoke evidence.",
    )


def _check_launch_security_contract(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return _check("observability_launch_security_contract", "fail", "missing", str(path))
    try:
        payload = _read_json(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return _check("observability_launch_security_contract", "fail", str(exc), "valid JSON object")

    checks = payload.get("checks")
    checks = checks if isinstance(checks, list) else []
    check_ids = [str(item.get("id", "")) for item in checks if isinstance(item, dict)]
    text = json.dumps(payload, ensure_ascii=False).lower()
    missing = []
    if "security_gate_evidence" not in check_ids:
        missing.append("security_gate_evidence_check")
    for marker in ("secret", "pii"):
        if marker not in text:
            missing.append("%s_marker" % marker)
    return _check(
        "observability_launch_security_contract",
        "pass" if not missing else "fail",
        {"missing": missing},
        {"missing": []},
        details="Launch evidence must preserve redaction, secret, and PII failure counters for observability.",
    )


def _check_runbook_contract(testing_doc: Path, operations_runbook: Path, script_map: Path) -> dict[str, Any]:
    text, missing_docs = _read_existing_text((testing_doc, operations_runbook, script_map))
    lowered = text.lower()
    missing_markers = [marker for marker in REQUIRED_RUNBOOK_MARKERS if marker.lower() not in lowered]
    return _check(
        "observability_runbook_contract",
        "pass" if not missing_docs and not missing_markers else "fail",
        {"missing_docs": missing_docs, "missing_markers": missing_markers},
        {"missing_docs": [], "missing_markers": []},
        details="Operators need a documented workflow for the observability readiness report and strict evidence mode.",
    )


def _check_live_evidence(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return _check(
            "observability_live_evidence",
            "fail",
            "missing",
            str(path),
            details="Strict observability readiness requires external dashboard or transcript evidence.",
        )
    try:
        payload = _read_json(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return _check("observability_live_evidence", "fail", str(exc), "valid JSON object")

    failure_codes: list[str] = []
    if payload.get("schema_version") != LIVE_EVIDENCE_SCHEMA_VERSION:
        failure_codes.append("schema_version_mismatch")
    if not _status_pass(payload.get("status")):
        failure_codes.append("status_not_pass")
    for field in REQUIRED_LIVE_STATUS_FIELDS:
        if not _status_pass(payload.get(field)):
            failure_codes.append("%s_not_pass" % field)
    if not str(payload.get("operator_dashboard_ref") or payload.get("evidence_bundle_ref") or "").strip():
        failure_codes.append("operator_dashboard_or_evidence_bundle_ref_missing")
    if not str(payload.get("created_at", "")).strip():
        failure_codes.append("created_at_missing")
    return _check(
        "observability_live_evidence",
        "pass" if not failure_codes else "fail",
        {"failure_codes": failure_codes},
        {"schema_version": LIVE_EVIDENCE_SCHEMA_VERSION, "all_status_fields": "pass"},
        details=(
            "Live evidence must cover job duration, success/fail, retry, modality, review, "
            "release artifact, agent smoke, redaction/secret failures, and dashboard review."
        ),
    )


def _build_report(args: argparse.Namespace) -> dict[str, Any]:
    trial_metrics_report = Path(args.trial_metrics_report).resolve()
    agent_smoke_report = Path(args.agent_smoke_report).resolve()
    release_gate_plan = Path(args.release_gate_plan).resolve()
    launch_gate_report = Path(args.launch_gate_report).resolve()
    console_source = Path(args.console_source).resolve()
    testing_doc = Path(args.testing_doc).resolve()
    script_map = Path(args.script_map).resolve()
    operations_runbook = Path(args.operations_runbook).resolve()
    live_evidence = Path(args.live_evidence).resolve()

    checks = [
        _check_trial_metrics_contract(trial_metrics_report),
        _check_agent_smoke_contract(agent_smoke_report),
        _check_console_contract(console_source),
        _check_release_artifact_contract(release_gate_plan, script_map),
        _check_launch_security_contract(launch_gate_report),
        _check_runbook_contract(testing_doc, operations_runbook, script_map),
    ]
    if bool(args.require_live_evidence):
        checks.append(_check_live_evidence(live_evidence))

    failed_checks = [check["id"] for check in checks if check.get("status") != "pass"]
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        "status": "OBSERVABILITY_READINESS_READY" if not failed_checks else "OBSERVABILITY_READINESS_BLOCKED",
        "live_evidence_required": bool(args.require_live_evidence),
        "required_trial_metric_paths": [name for name, _ in REQUIRED_TRIAL_METRIC_PATHS],
        "required_console_markers": list(REQUIRED_CONSOLE_MARKERS),
        "required_live_status_fields": list(REQUIRED_LIVE_STATUS_FIELDS),
        "check_count": len(checks),
        "pass_count": len([check for check in checks if check.get("status") == "pass"]),
        "fail_count": len([check for check in checks if check.get("status") != "pass"]),
        "failed_checks": failed_checks,
        "checks": checks,
        "evidence_paths": {
            "trial_metrics_report": str(trial_metrics_report),
            "agent_smoke_report": str(agent_smoke_report),
            "release_gate_plan": str(release_gate_plan),
            "launch_gate_report": str(launch_gate_report),
            "console_source": str(console_source),
            "testing_doc": str(testing_doc),
            "script_map": str(script_map),
            "operations_runbook": str(operations_runbook),
            "live_evidence": str(live_evidence),
        },
    }


def _render_summary(report: dict[str, Any]) -> str:
    lines = [
        "# Observability Readiness Summary",
        "",
        "- Status: `%s`" % report.get("status", "OBSERVABILITY_READINESS_BLOCKED"),
        "- Live evidence required: `%s`" % report.get("live_evidence_required", False),
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
        print("Observability readiness failed: %s" % exc, file=sys.stderr)
        return 2

    summary = _render_summary(report)
    output_value = str(args.output or "").strip()
    summary_output_value = str(args.summary_output or "").strip()
    if output_value and output_value != "-":
        _write_text(Path(output_value), json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print("Observability readiness report written: %s" % output_value)
    if summary_output_value and summary_output_value != "-":
        _write_text(Path(summary_output_value), summary)
        print("Observability readiness summary written: %s" % summary_output_value)
    if args.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.print_summary:
        print(summary)
    print(
        "Observability readiness status=%s checks=%s pass=%s fail=%s"
        % (
            report.get("status"),
            report.get("check_count"),
            report.get("pass_count"),
            report.get("fail_count"),
        )
    )
    if args.fail_on_blocked and report.get("status") != "OBSERVABILITY_READINESS_READY":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
