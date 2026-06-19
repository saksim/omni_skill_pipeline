from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "ci.yml"
DEFAULT_LAUNCH_GATE_REPORT = (
    REPO_ROOT / "docs" / "working" / "status" / "baselines" / "broad-launch-readiness-report.json"
)
DEFAULT_TRIAL_METRICS_REPORT = (
    REPO_ROOT / "docs" / "working" / "status" / "baselines" / "controlled-trial" / "trial-metrics-report.json"
)
DEFAULT_CONTROLLED_TRIAL_RUN_REPORT = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "controlled-trial"
    / "controlled-trial-run-report.json"
)
DEFAULT_DOC_INDEX = REPO_ROOT / "docs" / "INDEX.md"
DEFAULT_OUTPUT_PATH = (
    REPO_ROOT / "docs" / "working" / "status" / "baselines" / "internal-dogfood-readiness-report.json"
)
DEFAULT_SUMMARY_PATH = (
    REPO_ROOT / "docs" / "working" / "status" / "baselines" / "internal-dogfood-readiness-summary.md"
)

DECISIONS = ("READY_FOR_INTERNAL_DOGFOOD", "HOLD")
ALLOWED_EXTERNAL_HOLD_CHECKS = {"trial_loop_volume_and_modality_coverage"}
READY_DECISION = "READY_FOR_INTERNAL_DOGFOOD"
HOLD_DECISION = "HOLD"
SCOPE = "internal_dogfood_only"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate internal dogfood readiness without changing the external launch gate.",
    )
    parser.add_argument("--repo-root", default=str(REPO_ROOT), help="Repository root for checks.")
    parser.add_argument("--workflow", default="", help="CI workflow path. Defaults under --repo-root.")
    parser.add_argument(
        "--launch-gate-report",
        default="",
        help="Existing broad launch gate JSON report. Defaults under --repo-root.",
    )
    parser.add_argument(
        "--trial-metrics-report",
        default="",
        help="Controlled-trial metrics report. Defaults under --repo-root.",
    )
    parser.add_argument(
        "--controlled-trial-run-report",
        default="",
        help="Controlled-trial run report. Defaults under --repo-root.",
    )
    parser.add_argument("--doc-index", default="", help="Docs index path. Defaults under --repo-root.")
    parser.add_argument(
        "--ci-result",
        choices=("passed", "failed", "not_run", "exempted"),
        default="not_run",
        help="Observed CI baseline result supplied by the operator or calling workflow.",
    )
    parser.add_argument(
        "--ci-note",
        default="CI result was not supplied.",
        help="Short evidence note for --ci-result.",
    )
    parser.add_argument(
        "--healthz-url",
        default="",
        help="Optional live API health URL. If omitted, --healthz-report or route introspection is used.",
    )
    parser.add_argument(
        "--healthz-report",
        default="",
        help="Optional recorded health JSON with status=ready/degraded and optional http_status.",
    )
    parser.add_argument(
        "--allow-degraded-health",
        action="store_true",
        help="Allow a recorded or live status=degraded response for internal-only dogfood.",
    )
    parser.add_argument(
        "--allow-fixture-evidence",
        dest="allow_fixture_evidence",
        action="store_true",
        default=True,
        help="Allow fixture evidence for internal-only dogfood when output is clearly labelled.",
    )
    parser.add_argument(
        "--no-allow-fixture-evidence",
        dest="allow_fixture_evidence",
        action="store_false",
        help="Reject fixture evidence, useful for negative tests and stricter operator runs.",
    )
    parser.add_argument("--output", default="", help='JSON report output path. Use "-" to print only.')
    parser.add_argument("--summary-output", default="", help='Markdown summary output path. Use "-" to print only.')
    parser.add_argument("--print-json", action="store_true")
    parser.add_argument("--print-summary", action="store_true")
    parser.add_argument("--fail-on-hold", action="store_true")
    return parser.parse_args()


def _resolve_arg_path(repo_root: Path, explicit_value: str, default_path: Path) -> Path:
    raw = str(explicit_value or "").strip()
    if raw:
        path = Path(raw)
        return path if path.is_absolute() else repo_root / path
    try:
        default_relative = default_path.relative_to(REPO_ROOT)
    except ValueError:
        default_relative = default_path
    return repo_root / default_relative


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("JSON evidence root must be an object: %s" % path)
    return payload


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


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


def _status_is_pass(value: Any) -> bool:
    return str(value or "").strip().lower() in {"pass", "passed", "ok", "success", "ready"}


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


def _evaluate_ci_entrypoint(repo_root: Path, workflow_path: Path) -> dict[str, Any]:
    ci_script = repo_root / "scripts" / "ci.py"
    if not workflow_path.is_file():
        return _make_check(
            "ci_entrypoint_available",
            "fail",
            {"workflow": str(workflow_path), "exists": False},
            "workflow exists and calls scripts/ci.py",
            details="CI workflow file is missing.",
        )

    workflow_text = workflow_path.read_text(encoding="utf-8", errors="replace")
    has_ci_script = ci_script.is_file()
    calls_ci = "scripts/ci.py" in workflow_text
    calls_missing_run_ci = "scripts/run_ci.py" in workflow_text
    return _make_check(
        "ci_entrypoint_available",
        "pass" if has_ci_script and calls_ci and not calls_missing_run_ci else "fail",
        {
            "workflow": str(workflow_path),
            "scripts_ci_py_exists": has_ci_script,
            "workflow_calls_scripts_ci_py": calls_ci,
            "workflow_calls_missing_scripts_run_ci_py": calls_missing_run_ci,
        },
        {
            "scripts_ci_py_exists": True,
            "workflow_calls_scripts_ci_py": True,
            "workflow_calls_missing_scripts_run_ci_py": False,
        },
        details="Internal dogfood CI must not call a missing workflow script.",
    )


def _evaluate_ci_baseline(args: argparse.Namespace) -> dict[str, Any]:
    allowed = str(args.ci_result) in {"passed", "exempted"}
    return _make_check(
        "ci_baseline_passed",
        "pass" if allowed else "fail",
        {
            "ci_result": str(args.ci_result),
            "note": str(args.ci_note or ""),
        },
        "passed or explicitly exempted non-blocking item",
        details="The internal gate consumes the CI result; it does not lower coverage or skip the CI command.",
    )


def _evaluate_official_launch_gate(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    if not path.is_file():
        check = _make_check(
            "official_launch_gate_accounted",
            "fail",
            {"report": str(path), "exists": False},
            "readable broad launch gate report",
            details="External launch readiness must be accounted for, even when internal dogfood is allowed.",
        )
        return check, {}

    report = _read_json(path)
    decision = str(report.get("decision") or "").strip().upper()
    failed_checks = report.get("failed_checks", [])
    if not isinstance(failed_checks, list):
        failed_checks = []
    failed_ids = [str(item) for item in failed_checks]
    unexpected = [item for item in failed_ids if item not in ALLOWED_EXTERNAL_HOLD_CHECKS]
    allowed_hold = decision == HOLD_DECISION and not unexpected and bool(failed_ids)
    ready_external = decision and decision != HOLD_DECISION and not failed_ids
    status = "pass" if allowed_hold or ready_external else "fail"
    check = _make_check(
        "official_launch_gate_accounted",
        status,
        {
            "report": str(path),
            "decision": decision,
            "failed_checks": failed_ids,
            "unexpected_failed_checks": unexpected,
        },
        {
            "decision": "HOLD with only trial coverage blocker, or external READY with no blockers",
            "allowed_hold_failed_checks": sorted(ALLOWED_EXTERNAL_HOLD_CHECKS),
        },
        details=(
            "Internal dogfood may proceed only when the external HOLD is explained by missing real loop coverage; "
            "security, docs, ops, or review blockers still block."
        ),
    )
    return check, report


def _evaluate_official_not_overridden(external_decision: str) -> dict[str, Any]:
    return _make_check(
        "official_launch_gate_not_overridden",
        "pass",
        {
            "scope": SCOPE,
            "external_launch_decision": external_decision or "missing",
            "external_launch_claim": "not_ready" if external_decision == HOLD_DECISION else "unchanged",
        },
        {
            "scope": SCOPE,
            "external_launch_decision_preserved": True,
        },
        details="Internal readiness is not an external Beta, GA, or SaaS launch claim.",
    )


def _evaluate_health_from_payload(payload: dict[str, Any], *, source: str, allow_degraded: bool) -> dict[str, Any]:
    status = str(payload.get("status") or "").strip().lower()
    http_status = payload.get("http_status", payload.get("status_code"))
    http_ok = http_status in (None, "", 200) or (allow_degraded and http_status == 503)
    status_ok = status == "ready" or (allow_degraded and status == "degraded")
    return _make_check(
        "api_health_ready",
        "pass" if status_ok and http_ok else "fail",
        {"source": source, "status": status, "http_status": http_status, "payload": payload},
        {"status": "ready", "http_status": 200},
        details="API health must be ready, unless a degraded internal-only health state is explicitly allowed.",
    )


def _read_http_health(url: str, *, timeout: float = 5.0) -> tuple[int | None, dict[str, Any] | None, str]:
    request = Request(url, headers={"Accept": "application/json"})
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            payload = json.loads(body) if body.strip() else {}
            if isinstance(payload, dict):
                return int(getattr(response, "status", 0) or 0), payload, ""
            return int(getattr(response, "status", 0) or 0), None, "Health response JSON root is not an object."
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(body) if body.strip() else {}
        except json.JSONDecodeError:
            payload = None
        return int(exc.code), payload if isinstance(payload, dict) else None, ""
    except (OSError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        return None, None, str(exc)


def _evaluate_api_health(args: argparse.Namespace, repo_root: Path) -> dict[str, Any]:
    health_report_value = str(args.healthz_report or "").strip()
    if health_report_value:
        health_report_path = Path(health_report_value)
        if not health_report_path.is_absolute():
            health_report_path = repo_root / health_report_path
        if not health_report_path.is_file():
            return _make_check(
                "api_health_ready",
                "fail",
                {"healthz_report": str(health_report_path), "exists": False},
                "readable health report",
                details="Recorded API health report is missing.",
            )
        return _evaluate_health_from_payload(
            _read_json(health_report_path),
            source=str(health_report_path),
            allow_degraded=bool(args.allow_degraded_health),
        )

    healthz_url = str(args.healthz_url or "").strip()
    if healthz_url:
        http_status, payload, error = _read_http_health(healthz_url)
        if payload is None:
            return _make_check(
                "api_health_ready",
                "fail",
                {"healthz_url": healthz_url, "http_status": http_status, "error": error},
                {"status": "ready", "http_status": 200},
                details="Live API health URL was not reachable with a valid JSON object response.",
            )
        payload = {**payload, "http_status": http_status}
        return _evaluate_health_from_payload(
            payload,
            source=healthz_url,
            allow_degraded=bool(args.allow_degraded_health),
        )

    api_source = repo_root / "src" / "omni_skill_pipeline" / "api_app.py"
    if api_source.is_file():
        text = api_source.read_text(encoding="utf-8", errors="replace")
        route_present = "@app.get('/healthz')" in text or '@app.get("/healthz")' in text
        status_contract_present = "'status': 'ready'" in text and "'degraded'" in text
        if route_present and status_contract_present:
            return _make_check(
                "api_health_ready",
                "pass",
                {
                    "mode": "source_route_introspection",
                    "api_source": str(api_source),
                    "route_present": True,
                    "live_http": False,
                },
                "live /healthz ready response or source-level health route for internal-only evaluation",
                details="No live health URL was provided; internal gate verified the /healthz source contract.",
            )

    return _make_check(
        "api_health_ready",
        "fail",
        {"mode": "source_route_introspection", "api_source": str(api_source), "route_present": False},
        "live /healthz ready response",
        details="No live health URL, health report, or readable /healthz source contract was available.",
    )


def _count_fixture_samples(run_report: dict[str, Any]) -> int:
    samples = run_report.get("samples", [])
    if not isinstance(samples, list):
        return 0
    count = 0
    for sample in samples:
        if not isinstance(sample, dict):
            continue
        metrics = sample.get("loop_metrics", {})
        if isinstance(metrics, dict) and str(metrics.get("evidence_origin") or "").strip().lower() == "fixture":
            count += 1
    return count


def _evaluate_internal_sample(
    run_report_path: Path,
    *,
    allow_fixture_evidence: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not run_report_path.is_file():
        check = _make_check(
            "internal_sample_available",
            "fail",
            {"controlled_trial_run_report": str(run_report_path), "exists": False},
            "at least one controlled-trial or smoke sample",
            details="Internal dogfood needs at least one CLI/API happy path sample.",
        )
        return check, {}

    report = _read_json(run_report_path)
    sample_count = int(report.get("sample_count") or 0)
    samples = report.get("samples", [])
    complete_samples = 0
    if isinstance(samples, list):
        for item in samples:
            if not isinstance(item, dict):
                continue
            metrics = item.get("loop_metrics", {})
            if isinstance(metrics, dict) and str(metrics.get("status") or "").strip().lower() == "complete":
                complete_samples += 1
    fixture_sample_count = _count_fixture_samples(report)
    fixture_ok = allow_fixture_evidence or fixture_sample_count == 0
    status = "pass" if sample_count > 0 and complete_samples > 0 and fixture_ok else "fail"
    check = _make_check(
        "internal_sample_available",
        status,
        {
            "controlled_trial_run_report": str(run_report_path),
            "sample_count": sample_count,
            "complete_samples": complete_samples,
            "fixture_sample_count": fixture_sample_count,
            "fixture_evidence_allowed": allow_fixture_evidence,
        },
        {
            "sample_count": ">0",
            "complete_samples": ">0",
            "fixture_evidence_allowed_when_fixture_is_used": True,
        },
        details="Fixture samples can support internal dogfood only when the result is clearly internal-only.",
    )
    return check, report


def _evaluate_review_required(
    run_report: dict[str, Any],
    trial_metrics_path: Path,
) -> dict[str, Any]:
    safety: dict[str, Any] = {}
    if trial_metrics_path.is_file():
        try:
            trial_metrics = _read_json(trial_metrics_path)
            metrics = trial_metrics.get("trial_metrics", {})
            if isinstance(metrics, dict) and isinstance(metrics.get("safety"), dict):
                safety = metrics["safety"]
        except (OSError, json.JSONDecodeError, ValueError):
            safety = {}
    unreviewed_count = int(safety.get("unreviewed_published_count") or 0)
    force_review_mode = bool(run_report.get("force_review_mode")) if run_report else False
    return _make_check(
        "review_required_default",
        "pass" if unreviewed_count == 0 and force_review_mode else "fail",
        {
            "force_review_mode": force_review_mode,
            "unreviewed_published_count": unreviewed_count,
        },
        {
            "force_review_mode": True,
            "unreviewed_published_count": 0,
        },
        details="Generated artifacts must not be treated as auto-published internal outputs.",
    )


def _evaluate_internal_only_label(*, allow_fixture_evidence: bool, fixture_sample_count: int) -> dict[str, Any]:
    label_present = SCOPE == "internal_dogfood_only"
    fixture_label_ok = fixture_sample_count == 0 or allow_fixture_evidence
    return _make_check(
        "internal_only_label_present",
        "pass" if label_present and fixture_label_ok else "fail",
        {
            "scope": SCOPE,
            "internal_dogfood_only": True,
            "fixture_sample_count": fixture_sample_count,
            "fixture_evidence_allowed": allow_fixture_evidence,
        },
        {
            "scope": SCOPE,
            "internal_dogfood_only": True,
            "fixture_evidence_allowed_when_fixture_is_used": True,
        },
        details="Any fixture-backed decision must be explicitly internal-only.",
    )


def _evaluate_docs_indexed(doc_index_path: Path) -> dict[str, Any]:
    if not doc_index_path.is_file():
        return _make_check(
            "docs_indexed",
            "fail",
            {"doc_index": str(doc_index_path), "exists": False},
            "docs index references internal dogfood launch docs",
            blocking=False,
            details="Docs index is advisory for the internal gate.",
        )
    text = doc_index_path.read_text(encoding="utf-8", errors="replace")
    required = [
        "2026-06-18-internal-dogfood-launch-construction-plan.md",
        "internal-dogfood-launch/README.md",
    ]
    missing = [item for item in required if item not in text]
    return _make_check(
        "docs_indexed",
        "pass" if not missing else "fail",
        {"doc_index": str(doc_index_path), "missing": missing},
        {"missing": []},
        blocking=False,
        details="Internal dogfood docs should remain discoverable from docs/INDEX.md.",
    )


def _build_report(args: argparse.Namespace) -> dict[str, Any]:
    repo_root = Path(args.repo_root).resolve()
    workflow_path = _resolve_arg_path(repo_root, str(args.workflow or ""), DEFAULT_WORKFLOW_PATH)
    launch_gate_report_path = _resolve_arg_path(
        repo_root,
        str(args.launch_gate_report or ""),
        DEFAULT_LAUNCH_GATE_REPORT,
    )
    trial_metrics_path = _resolve_arg_path(
        repo_root,
        str(args.trial_metrics_report or ""),
        DEFAULT_TRIAL_METRICS_REPORT,
    )
    controlled_trial_run_path = _resolve_arg_path(
        repo_root,
        str(args.controlled_trial_run_report or ""),
        DEFAULT_CONTROLLED_TRIAL_RUN_REPORT,
    )
    doc_index_path = _resolve_arg_path(repo_root, str(args.doc_index or ""), DEFAULT_DOC_INDEX)

    checks: list[dict[str, Any]] = []
    checks.append(_evaluate_ci_entrypoint(repo_root, workflow_path))
    checks.append(_evaluate_ci_baseline(args))

    official_check, official_report = _evaluate_official_launch_gate(launch_gate_report_path)
    checks.append(official_check)
    external_decision = str(official_report.get("decision") or "").strip().upper() if official_report else "missing"
    checks.append(_evaluate_official_not_overridden(external_decision))

    checks.append(_evaluate_api_health(args, repo_root))

    internal_sample_check, run_report = _evaluate_internal_sample(
        controlled_trial_run_path,
        allow_fixture_evidence=bool(args.allow_fixture_evidence),
    )
    checks.append(internal_sample_check)
    fixture_sample_count = _count_fixture_samples(run_report) if run_report else 0
    checks.append(_evaluate_review_required(run_report, trial_metrics_path))
    checks.append(
        _evaluate_internal_only_label(
            allow_fixture_evidence=bool(args.allow_fixture_evidence),
            fixture_sample_count=fixture_sample_count,
        )
    )
    checks.append(_evaluate_docs_indexed(doc_index_path))

    failed_checks = [check["id"] for check in checks if check.get("blocking") and check.get("status") != "pass"]
    decision = HOLD_DECISION if failed_checks else READY_DECISION
    summary = {
        "internal_dogfood_only": True,
        "fixture_evidence_used": fixture_sample_count > 0,
        "fixture_sample_count": fixture_sample_count,
        "external_hold_allowed_blockers": sorted(ALLOWED_EXTERNAL_HOLD_CHECKS),
    }
    return {
        "schema_version": "internal_dogfood_readiness.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "decision_code": DECISIONS.index(decision),
        "scope": SCOPE,
        "internal_dogfood_only": True,
        "external_launch_decision": external_decision,
        "external_launch_claim": "not_ready" if external_decision == HOLD_DECISION else "unchanged",
        "summary": summary,
        "failed_checks": failed_checks,
        "check_count": len(checks),
        "pass_count": len([check for check in checks if check.get("status") == "pass"]),
        "fail_count": len([check for check in checks if check.get("status") != "pass"]),
        "checks": checks,
        "evidence_paths": {
            "workflow": str(workflow_path),
            "launch_gate_report": str(launch_gate_report_path),
            "trial_metrics_report": str(trial_metrics_path),
            "controlled_trial_run_report": str(controlled_trial_run_path),
            "doc_index": str(doc_index_path),
            "healthz_url": str(args.healthz_url or ""),
            "healthz_report": str(args.healthz_report or ""),
        },
    }


def _render_markdown(report: dict[str, Any]) -> str:
    failed = report.get("failed_checks", [])
    failed_text = ", ".join(str(item) for item in failed) if failed else "none"
    lines = [
        "# Internal Dogfood Readiness Summary",
        "",
        "- Decision: `%s`" % report.get("decision", HOLD_DECISION),
        "- Scope: `%s`" % report.get("scope", SCOPE),
        "- Internal-only: `%s`" % str(bool(report.get("internal_dogfood_only"))).lower(),
        "- External launch decision: `%s`" % report.get("external_launch_decision", "missing"),
        "- External launch claim: `%s`" % report.get("external_launch_claim", "not_ready"),
        "- Blocking checks: `%s`" % failed_text,
        "- Checks: `%s` pass / `%s` fail / `%s` total"
        % (report.get("pass_count", 0), report.get("fail_count", 0), report.get("check_count", 0)),
        "",
        "This result is only for internal dogfood. It is not an external Beta, GA, or SaaS launch claim.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    try:
        report = _build_report(args)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print("Internal dogfood gate failed: %s" % exc, file=sys.stderr)
        return 2

    summary = _render_markdown(report)
    output_value = str(args.output or "").strip()
    if not output_value:
        output_value = str(DEFAULT_OUTPUT_PATH)
    summary_output_value = str(args.summary_output or "").strip()
    if not summary_output_value:
        summary_output_value = str(DEFAULT_SUMMARY_PATH)

    if output_value and output_value != "-":
        output_path = Path(output_value).resolve()
        _write_text(output_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print("Internal dogfood readiness report written: %s" % output_path)
    if summary_output_value and summary_output_value != "-":
        summary_path = Path(summary_output_value).resolve()
        _write_text(summary_path, summary)
        print("Internal dogfood readiness summary written: %s" % summary_path)

    print(
        "Internal dogfood readiness decision=%s checks=%s pass=%s fail=%s"
        % (report["decision"], report["check_count"], report["pass_count"], report["fail_count"])
    )
    if report["failed_checks"]:
        print("Blocking checks: %s" % ", ".join(report["failed_checks"]))
    else:
        print("Blocking checks: none")
    if output_value == "-" or args.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    if summary_output_value == "-" or args.print_summary:
        print(summary.rstrip())
    if args.fail_on_hold and report.get("decision") == HOLD_DECISION:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
