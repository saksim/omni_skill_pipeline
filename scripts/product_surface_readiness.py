from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_SCHEMA_VERSION = "product_surface_readiness.v1"
LIVE_EVIDENCE_SCHEMA_VERSION = "product_surface_live_evidence.v1"

DEFAULT_API_SOURCE = REPO_ROOT / "src" / "omni_skill_pipeline" / "api_app.py"
DEFAULT_CONSOLE_SOURCE = REPO_ROOT / "src" / "omni_skill_pipeline" / "platform_console.py"
DEFAULT_API_DOC = REPO_ROOT / "docs" / "latest" / "operations" / "api.md"
DEFAULT_BETA_RUNBOOK = (
    REPO_ROOT / "docs" / "latest" / "operations" / "runbooks" / "controlled-external-beta-onboarding.md"
)
DEFAULT_LAUNCH_RUNBOOK = REPO_ROOT / "docs" / "latest" / "operations" / "runbooks" / "launch-beta.md"
DEFAULT_LIVE_EVIDENCE = (
    REPO_ROOT / "docs" / "working" / "status" / "baselines" / "product-surface-live-evidence.json"
)
DEFAULT_OUTPUT = (
    REPO_ROOT / "docs" / "working" / "status" / "baselines" / "product-surface-readiness-report.json"
)
DEFAULT_SUMMARY_OUTPUT = (
    REPO_ROOT / "docs" / "working" / "status" / "baselines" / "product-surface-readiness-summary.md"
)

REQUIRED_API_ROUTES = (
    "GET /healthz",
    "GET /v1/templates/skill",
    "POST /v1/distill/text",
    "POST /v1/distill/audio",
    "POST /v1/distill/image",
    "POST /v1/distill/tabular",
    "POST /v1/distill/video",
    "POST /v1/distill/corpus",
    "GET /v1/review/queue",
    "POST /v1/review/queue/claim",
    "POST /v1/review/queue/{review_task_id}/close",
    "POST /v1/review/queue/{review_task_id}/decision",
    "POST /v1/governance/report",
    "POST /v1/governance/retention-policy",
    "POST /v1/governance/deletion",
    "POST /v1/console/views",
)
REQUIRED_CONSOLE_VIEW_GROUPS = (
    "trial_runs",
    "review_queue",
    "skill_registry",
    "metrics",
    "security_failures",
    "cost",
)
REQUIRED_PRODUCT_FLOW_MARKERS = (
    "source intake",
    "job run",
    "generated skill preview",
    "human review",
    "export/validate",
    "evidence/manifest",
    "launch gate dashboard",
    "/v1/console/views",
)
REQUIRED_LIVE_STATUS_FIELDS = (
    "source_intake_status",
    "job_run_status",
    "skill_preview_status",
    "human_review_status",
    "export_validate_status",
    "evidence_manifest_status",
    "dashboard_status",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate the P2 beta product-entry surface without building a GUI or faking live evidence.",
    )
    parser.add_argument("--api-source", default=str(DEFAULT_API_SOURCE))
    parser.add_argument("--console-source", default=str(DEFAULT_CONSOLE_SOURCE))
    parser.add_argument("--api-doc", default=str(DEFAULT_API_DOC))
    parser.add_argument("--beta-runbook", default=str(DEFAULT_BETA_RUNBOOK))
    parser.add_argument("--launch-runbook", default=str(DEFAULT_LAUNCH_RUNBOOK))
    parser.add_argument("--live-evidence", default=str(DEFAULT_LIVE_EVIDENCE))
    parser.add_argument(
        "--require-live-evidence",
        action="store_true",
        help="Require an external operator transcript/evidence pack for the full beta product flow.",
    )
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help='JSON report output. Use "-" to skip writing.')
    parser.add_argument("--summary-output", default=str(DEFAULT_SUMMARY_OUTPUT), help='Markdown output. Use "-" to skip.')
    parser.add_argument("--print-json", action="store_true")
    parser.add_argument("--print-summary", action="store_true")
    parser.add_argument("--fail-on-blocked", action="store_true")
    return parser.parse_args()


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("JSON root must be an object: %s" % path)
    return payload


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


def _extract_routes(api_source_text: str) -> set[str]:
    routes: set[str] = set()
    pattern = re.compile(r"@app\.(get|post|put|delete|patch)\(\s*['\"]([^'\"]+)['\"]", re.IGNORECASE)
    for match in pattern.finditer(api_source_text):
        routes.add("%s %s" % (match.group(1).upper(), match.group(2)))
    return routes


def _check_api_routes(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return _check("product_surface_api_routes", "fail", "missing", str(path))
    routes = _extract_routes(_read_text(path))
    missing = [route for route in REQUIRED_API_ROUTES if route not in routes]
    return _check(
        "product_surface_api_routes",
        "pass" if not missing else "fail",
        {"missing": missing, "route_count": len(routes)},
        {"missing": []},
        details=(
            "The P2 beta entry requires API source intake, review operations, governance, "
            "and a console snapshot route."
        ),
    )


def _check_console_groups(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return _check("product_surface_console_views", "fail", "missing", str(path))
    text = _read_text(path)
    missing = [group for group in REQUIRED_CONSOLE_VIEW_GROUPS if group not in text]
    return _check(
        "product_surface_console_views",
        "pass" if not missing else "fail",
        {"missing": missing},
        {"missing": []},
        details="The platform console surface must expose operator, reviewer, evidence, metrics, security, and cost views.",
    )


def _read_existing_docs(paths: tuple[Path, ...]) -> tuple[str, list[str]]:
    chunks: list[str] = []
    missing: list[str] = []
    for path in paths:
        if path.is_file():
            chunks.append(_read_text(path))
        else:
            missing.append(str(path))
    return "\n".join(chunks), missing


def _check_product_flow_docs(paths: tuple[Path, ...]) -> dict[str, Any]:
    text, missing_docs = _read_existing_docs(paths)
    lowered = text.lower()
    missing_markers = [marker for marker in REQUIRED_PRODUCT_FLOW_MARKERS if marker.lower() not in lowered]
    return _check(
        "product_surface_workflow_docs",
        "pass" if not missing_docs and not missing_markers else "fail",
        {"missing_docs": missing_docs, "missing_markers": missing_markers},
        {"missing_docs": [], "missing_markers": []},
        details=(
            "Beta operators must be able to trace source intake, job execution, preview, review, "
            "export/validate, evidence/manifest, and launch dashboard steps from docs."
        ),
    )


def _status_pass(value: Any) -> bool:
    return str(value or "").strip().lower() in {"pass", "passed", "ok", "ready", "true"}


def _check_live_evidence(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return _check(
            "product_surface_live_evidence",
            "fail",
            "missing",
            str(path),
            details="Strict beta product-surface readiness requires external live operator evidence.",
        )
    try:
        payload = _read_json(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return _check("product_surface_live_evidence", "fail", str(exc), "valid JSON object")

    failure_codes: list[str] = []
    if payload.get("schema_version") != LIVE_EVIDENCE_SCHEMA_VERSION:
        failure_codes.append("schema_version_mismatch")
    if not _status_pass(payload.get("status")):
        failure_codes.append("status_not_pass")
    for field in REQUIRED_LIVE_STATUS_FIELDS:
        if not _status_pass(payload.get(field)):
            failure_codes.append("%s_not_pass" % field)
    if not str(payload.get("operator_transcript_ref", "")).strip():
        failure_codes.append("operator_transcript_ref_missing")
    if not str(payload.get("created_at", "")).strip():
        failure_codes.append("created_at_missing")

    return _check(
        "product_surface_live_evidence",
        "pass" if not failure_codes else "fail",
        {"failure_codes": failure_codes},
        {"schema_version": LIVE_EVIDENCE_SCHEMA_VERSION, "all_status_fields": "pass"},
        details="Live evidence must cover one operator-run beta flow from intake through console dashboard review.",
    )


def _build_report(args: argparse.Namespace) -> dict[str, Any]:
    api_source = Path(args.api_source).resolve()
    console_source = Path(args.console_source).resolve()
    api_doc = Path(args.api_doc).resolve()
    beta_runbook = Path(args.beta_runbook).resolve()
    launch_runbook = Path(args.launch_runbook).resolve()
    live_evidence = Path(args.live_evidence).resolve()

    checks = [
        _check_api_routes(api_source),
        _check_console_groups(console_source),
        _check_product_flow_docs((api_doc, beta_runbook, launch_runbook)),
    ]
    if bool(args.require_live_evidence):
        checks.append(_check_live_evidence(live_evidence))

    failed_checks = [check["id"] for check in checks if check.get("status") != "pass"]
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        "status": "PRODUCT_SURFACE_READINESS_READY" if not failed_checks else "PRODUCT_SURFACE_READINESS_BLOCKED",
        "live_evidence_required": bool(args.require_live_evidence),
        "required_api_routes": list(REQUIRED_API_ROUTES),
        "required_console_view_groups": list(REQUIRED_CONSOLE_VIEW_GROUPS),
        "required_product_flow_markers": list(REQUIRED_PRODUCT_FLOW_MARKERS),
        "check_count": len(checks),
        "pass_count": len([check for check in checks if check.get("status") == "pass"]),
        "fail_count": len([check for check in checks if check.get("status") != "pass"]),
        "failed_checks": failed_checks,
        "checks": checks,
        "evidence_paths": {
            "api_source": str(api_source),
            "console_source": str(console_source),
            "api_doc": str(api_doc),
            "beta_runbook": str(beta_runbook),
            "launch_runbook": str(launch_runbook),
            "live_evidence": str(live_evidence),
        },
    }


def _render_summary(report: dict[str, Any]) -> str:
    lines = [
        "# Product Surface Readiness Summary",
        "",
        "- Status: `%s`" % report.get("status", "PRODUCT_SURFACE_READINESS_BLOCKED"),
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
        print("Product surface readiness failed: %s" % exc, file=sys.stderr)
        return 2

    summary = _render_summary(report)
    output_value = str(args.output or "").strip()
    summary_output_value = str(args.summary_output or "").strip()
    if output_value and output_value != "-":
        _write_text(Path(output_value), json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print("Product surface readiness report written: %s" % output_value)
    if summary_output_value and summary_output_value != "-":
        _write_text(Path(summary_output_value), summary)
        print("Product surface readiness summary written: %s" % summary_output_value)
    if args.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.print_summary:
        print(summary)
    print(
        "Product surface readiness status=%s checks=%s pass=%s fail=%s"
        % (
            report.get("status"),
            report.get("check_count"),
            report.get("pass_count"),
            report.get("fail_count"),
        )
    )
    if args.fail_on_blocked and report.get("status") != "PRODUCT_SURFACE_READINESS_READY":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
