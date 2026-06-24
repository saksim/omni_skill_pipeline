from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_SCHEMA_VERSION = "docker_readiness.v1"
LIVE_EVIDENCE_SCHEMA_VERSION = "docker_live_evidence.v1"

DEFAULT_DOCKERFILE = REPO_ROOT / "Dockerfile"
DEFAULT_DOCKERIGNORE = REPO_ROOT / ".dockerignore"
DEFAULT_CONTAINER_SMOKE_SOURCE = REPO_ROOT / "scripts" / "container_smoke.py"
DEFAULT_CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"
DEFAULT_TESTING_DOC = REPO_ROOT / "docs" / "latest" / "operations" / "testing.md"
DEFAULT_DOCKER_RUNBOOK = REPO_ROOT / "docs" / "latest" / "operations" / "runbooks" / "docker-zero-to-release.md"
DEFAULT_PRODUCTION_OPS_RUNBOOK = (
    REPO_ROOT / "docs" / "latest" / "operations" / "runbooks" / "production-operations-baseline.md"
)
DEFAULT_LIVE_EVIDENCE = REPO_ROOT / "docs" / "working" / "status" / "baselines" / "docker-live-evidence.json"
DEFAULT_OUTPUT = REPO_ROOT / "docs" / "working" / "status" / "baselines" / "docker-readiness-report.json"
DEFAULT_SUMMARY_OUTPUT = REPO_ROOT / "docs" / "working" / "status" / "baselines" / "docker-readiness-summary.md"

REQUIRED_DOCKERFILE_MARKERS = (
    "FROM python:3.11-slim",
    "OMNI_REPO_ROOT=/app",
    "WORKDIR /app",
    "COPY pyproject.toml README.md requirements-dev.txt ./",
    "COPY src ./src",
    "COPY apps ./apps",
    "python -m pip install .[api]",
    "mkdir -p /app/skills/drafts /app/skills/published",
    "EXPOSE 8000",
    "uvicorn",
    "--host",
    "0.0.0.0",
    "--port",
    "8000",
)
REQUIRED_DOCKERIGNORE_MARKERS = (
    ".git",
    ".venv",
    "__pycache__/",
    "*.pyc",
    ".pytest_cache/",
    "coverage.xml",
    "skills/drafts/",
    "skills/published/",
    "!docs/latest/contracts/**",
)
REQUIRED_CONTAINER_SMOKE_MARKERS = (
    'REPORT_SCHEMA_VERSION = "container_smoke.v1"',
    "_build_command",
    "_image_size_command",
    "_cli_smoke_command",
    "_run_command",
    "_poll_healthz",
    "_logs_command",
    "_cleanup_command",
    "docker_cli_missing",
    "docker_daemon_unavailable",
    "image_build",
    "image_size",
    "cli_smoke",
    "container_run",
    "healthz",
    "container_logs",
    "cleanup",
    "dry_run",
    "skip_build",
    "skip_run",
)
REQUIRED_CI_MARKERS = (
    "docker-smoke",
    "python scripts/container_smoke.py",
    "container_smoke_report.json",
    "container_smoke_summary.md",
    "docker-smoke-evidence",
)
REQUIRED_DOC_MARKERS = (
    "python scripts/container_smoke.py",
    "docker build",
    "docker run --rm",
    "docker run -d",
    "curl -fsS http://127.0.0.1:8000/healthz",
    "docker logs",
    "docker rm -f",
    "python scripts/docker_readiness.py",
    "--dry-run",
    "--skip-build",
    "--skip-run",
)
REQUIRED_LIVE_STATUS_FIELDS = (
    "image_build_status",
    "image_size_status",
    "cli_smoke_status",
    "container_run_status",
    "healthz_status",
    "logs_collected_status",
    "cleanup_status",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate Docker readiness without treating dry-run plans as live container smoke evidence.",
    )
    parser.add_argument("--dockerfile", default=str(DEFAULT_DOCKERFILE))
    parser.add_argument("--dockerignore", default=str(DEFAULT_DOCKERIGNORE))
    parser.add_argument("--container-smoke-source", default=str(DEFAULT_CONTAINER_SMOKE_SOURCE))
    parser.add_argument("--ci-workflow", default=str(DEFAULT_CI_WORKFLOW))
    parser.add_argument("--testing-doc", default=str(DEFAULT_TESTING_DOC))
    parser.add_argument("--docker-runbook", default=str(DEFAULT_DOCKER_RUNBOOK))
    parser.add_argument("--production-ops-runbook", default=str(DEFAULT_PRODUCTION_OPS_RUNBOOK))
    parser.add_argument("--live-evidence", default=str(DEFAULT_LIVE_EVIDENCE))
    parser.add_argument(
        "--require-live-evidence",
        action="store_true",
        help="Require external non-dry-run Docker smoke evidence for strict production readiness.",
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


def _status_pass(value: Any) -> bool:
    return str(value or "").strip().lower() in {"pass", "passed", "ready", "ok", "true"}


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() not in {"", "0", "false", "no", "none", "null"}
    return value is not None


def _check_text_markers(
    *,
    check_id: str,
    path: Path,
    markers: tuple[str, ...],
    details: str,
) -> dict[str, Any]:
    if not path.is_file():
        return _check(check_id, "fail", "missing", str(path), details=details)
    text = _read_text(path)
    missing = [marker for marker in markers if marker not in text]
    return _check(
        check_id,
        "pass" if not missing else "fail",
        {"missing_markers": missing},
        {"missing_markers": []},
        details=details,
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


def _check_docs_contract(paths: tuple[Path, ...]) -> dict[str, Any]:
    text, missing_docs = _read_existing_text(paths)
    missing_markers = [marker for marker in REQUIRED_DOC_MARKERS if marker not in text]
    return _check(
        "docker_docs_contract",
        "pass" if not missing_docs and not missing_markers else "fail",
        {"missing_docs": missing_docs, "missing_markers": missing_markers},
        {"missing_docs": [], "missing_markers": []},
        details=(
            "Docker operations docs must explain build/run/health/log/cleanup evidence and the readiness gate."
        ),
    )


def _check_live_evidence(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return _check(
            "docker_live_evidence",
            "fail",
            "missing",
            str(path),
            details="Strict Docker readiness requires external non-dry-run container smoke evidence.",
        )
    try:
        payload = _read_json(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return _check("docker_live_evidence", "fail", str(exc), "valid JSON object")

    failure_codes: list[str] = []
    if payload.get("schema_version") != LIVE_EVIDENCE_SCHEMA_VERSION:
        failure_codes.append("schema_version_mismatch")
    if not _status_pass(payload.get("status")):
        failure_codes.append("status_not_pass")
    for field in REQUIRED_LIVE_STATUS_FIELDS:
        if not _status_pass(payload.get(field)):
            failure_codes.append("%s_not_pass" % field)
    for field in ("dry_run", "skip_build", "skip_run"):
        if _truthy(payload.get(field)):
            failure_codes.append("%s_not_allowed" % field)
    if not str(payload.get("image_ref") or payload.get("image_tag") or "").strip():
        failure_codes.append("image_ref_missing")
    if not str(payload.get("container_smoke_report_ref") or payload.get("evidence_bundle_ref") or "").strip():
        failure_codes.append("container_smoke_report_or_evidence_bundle_ref_missing")
    if not str(payload.get("created_at", "")).strip():
        failure_codes.append("created_at_missing")

    return _check(
        "docker_live_evidence",
        "pass" if not failure_codes else "fail",
        {"failure_codes": failure_codes},
        {
            "schema_version": LIVE_EVIDENCE_SCHEMA_VERSION,
            "all_status_fields": "pass",
            "dry_run": False,
            "skip_build": False,
            "skip_run": False,
        },
        details=(
            "Live Docker evidence must cover image build, image size, CLI smoke, container run, "
            "healthz, logs, and cleanup without dry-run or skipped stages."
        ),
    )


def _build_report(args: argparse.Namespace) -> dict[str, Any]:
    dockerfile = Path(args.dockerfile).resolve()
    dockerignore = Path(args.dockerignore).resolve()
    container_smoke_source = Path(args.container_smoke_source).resolve()
    ci_workflow = Path(args.ci_workflow).resolve()
    testing_doc = Path(args.testing_doc).resolve()
    docker_runbook = Path(args.docker_runbook).resolve()
    production_ops_runbook = Path(args.production_ops_runbook).resolve()
    live_evidence = Path(args.live_evidence).resolve()

    checks = [
        _check_text_markers(
            check_id="dockerfile_runtime_contract",
            path=dockerfile,
            markers=REQUIRED_DOCKERFILE_MARKERS,
            details="Runtime Dockerfile must build the API image with Python 3.11 and expose /healthz on port 8000.",
        ),
        _check_text_markers(
            check_id="dockerignore_hygiene_contract",
            path=dockerignore,
            markers=REQUIRED_DOCKERIGNORE_MARKERS,
            details="Docker build context must exclude VCS, caches, coverage, generated skills, and transient files.",
        ),
        _check_text_markers(
            check_id="container_smoke_contract",
            path=container_smoke_source,
            markers=REQUIRED_CONTAINER_SMOKE_MARKERS,
            details="container_smoke.py must record build/run/health/log/cleanup stages and expose dry-run/skip flags.",
        ),
        _check_text_markers(
            check_id="docker_ci_contract",
            path=ci_workflow,
            markers=REQUIRED_CI_MARKERS,
            details="CI must run a real Docker smoke job and upload structured container smoke evidence.",
        ),
        _check_docs_contract((testing_doc, docker_runbook, production_ops_runbook)),
    ]
    if bool(args.require_live_evidence):
        checks.append(_check_live_evidence(live_evidence))

    failed_checks = [check["id"] for check in checks if check.get("status") != "pass"]
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        "status": "DOCKER_READINESS_READY" if not failed_checks else "DOCKER_READINESS_BLOCKED",
        "live_evidence_required": bool(args.require_live_evidence),
        "required_live_status_fields": list(REQUIRED_LIVE_STATUS_FIELDS),
        "check_count": len(checks),
        "pass_count": len([check for check in checks if check.get("status") == "pass"]),
        "fail_count": len([check for check in checks if check.get("status") != "pass"]),
        "failed_checks": failed_checks,
        "checks": checks,
        "evidence_paths": {
            "dockerfile": str(dockerfile),
            "dockerignore": str(dockerignore),
            "container_smoke_source": str(container_smoke_source),
            "ci_workflow": str(ci_workflow),
            "testing_doc": str(testing_doc),
            "docker_runbook": str(docker_runbook),
            "production_ops_runbook": str(production_ops_runbook),
            "live_evidence": str(live_evidence),
        },
    }


def _render_summary(report: dict[str, Any]) -> str:
    lines = [
        "# Docker Readiness Summary",
        "",
        "- Status: `%s`" % report.get("status", "DOCKER_READINESS_BLOCKED"),
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
        print("Docker readiness failed: %s" % exc, file=sys.stderr)
        return 2

    summary = _render_summary(report)
    output_value = str(args.output or "").strip()
    summary_output_value = str(args.summary_output or "").strip()
    if output_value and output_value != "-":
        _write_text(Path(output_value), json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print("Docker readiness report written: %s" % output_value)
    if summary_output_value and summary_output_value != "-":
        _write_text(Path(summary_output_value), summary)
        print("Docker readiness summary written: %s" % summary_output_value)
    if args.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.print_summary:
        print(summary)
    print(
        "Docker readiness status=%s checks=%s pass=%s fail=%s"
        % (
            report.get("status"),
            report.get("check_count"),
            report.get("pass_count"),
            report.get("fail_count"),
        )
    )
    if args.fail_on_blocked and report.get("status") != "DOCKER_READINESS_READY":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
