from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_SCHEMA_VERSION = "secrets_readiness.v1"
EXTERNAL_EVIDENCE_SCHEMA_VERSION = "secrets_management_evidence.v1"
DEFAULT_ENV_EXAMPLE = REPO_ROOT / ".env.example"
DEFAULT_ENV_DOC = REPO_ROOT / "docs" / "latest" / "operations" / "env.md"
DEFAULT_ARTIFACT_ENCRYPTION_RUNBOOK = (
    REPO_ROOT / "docs" / "latest" / "operations" / "runbooks" / "artifact-encryption.md"
)
DEFAULT_PRODUCTION_OPS_RUNBOOK = (
    REPO_ROOT / "docs" / "latest" / "operations" / "runbooks" / "production-operations-baseline.md"
)
DEFAULT_EXTERNAL_EVIDENCE = (
    REPO_ROOT / "docs" / "working" / "status" / "baselines" / "secrets-management-evidence.json"
)
DEFAULT_OUTPUT = REPO_ROOT / "docs" / "working" / "status" / "baselines" / "secrets-readiness-report.json"
DEFAULT_SUMMARY_OUTPUT = (
    REPO_ROOT / "docs" / "working" / "status" / "baselines" / "secrets-readiness-summary.md"
)

SENSITIVE_ENV_VARS = (
    "OPENAI_API_KEY",
    "OMNI_API_KEY",
    "OMNI_TENANT_ACCESS_JSON",
    "OMNI_TENANT_ACCESS_FILE",
    "OMNI_TEST_POSTGRES_DSN",
    "OMNI_POSTGRES_REPOSITORY_DSN",
    "OMNI_ARTIFACT_ENCRYPTION_KEY",
)
PRODUCTION_SECRET_CLASSES = (
    "provider_api_key",
    "database_password",
    "object_storage_credentials",
    "signing_key",
    "artifact_encryption_key",
)
PRODUCTION_SECRET_PROVIDERS = {
    "vault",
    "hashicorp_vault",
    "kms",
    "secret_manager",
    "aws_secrets_manager",
    "gcp_secret_manager",
    "azure_key_vault",
}
DOC_REQUIRED_MARKERS = (
    "OPENAI_API_KEY",
    "OMNI_API_KEY",
    "OMNI_ARTIFACT_ENCRYPTION_KEY",
    "secret store",
    "CI secret",
    "不要提交",
)
PRODUCTION_OPS_REQUIRED_MARKERS = (
    "Required secrets are managed outside image layers",
    "OPENAI_API_KEY",
    "OMNI_API_KEY",
)
HIGH_RISK_ASSIGNMENT_RE = re.compile(
    r"(?i)\b([A-Z0-9_]*(?:API_KEY|SECRET|TOKEN|PASSWORD|DSN|ENCRYPTION_KEY)[A-Z0-9_]*)\b\s*[:=]\s*([^\r\n#]+)"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate repository and production secret-management readiness evidence.",
    )
    parser.add_argument("--env-example", default=str(DEFAULT_ENV_EXAMPLE))
    parser.add_argument("--env-doc", default=str(DEFAULT_ENV_DOC))
    parser.add_argument("--artifact-encryption-runbook", default=str(DEFAULT_ARTIFACT_ENCRYPTION_RUNBOOK))
    parser.add_argument("--production-ops-runbook", default=str(DEFAULT_PRODUCTION_OPS_RUNBOOK))
    parser.add_argument("--external-secret-evidence", default=str(DEFAULT_EXTERNAL_EVIDENCE))
    parser.add_argument(
        "--require-production-manager",
        action="store_true",
        help="Require external Vault/KMS/Secret Manager evidence for production readiness.",
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


def _placeholder(value: str) -> bool:
    text = value.strip().strip("'\"")
    lowered = text.lower()
    if not text:
        return True
    if text.startswith("<") and text.endswith(">"):
        return True
    if text.startswith("${") or text.startswith("$("):
        return True
    if "${{ secrets." in lowered or "${{ env." in lowered:
        return True
    return lowered in {
        "changeme",
        "change-me",
        "replace_me",
        "replace-me",
        "example",
        "example-value",
        "dummy",
        "test",
        "placeholder",
    }


def _parse_env_assignments(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key or not re.fullmatch(r"[A-Z0-9_]+", key):
            continue
        values[key] = value.strip()
    return values


def _check_env_example(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return _check("env_example_secret_placeholders", "fail", "missing", str(path))
    values = _parse_env_assignments(_read_text(path))
    missing = [key for key in SENSITIVE_ENV_VARS if key not in values]
    non_placeholder = [
        {"name": key, "value_preview": values[key][:8] + ("..." if len(values[key]) > 8 else "")}
        for key in SENSITIVE_ENV_VARS
        if key in values and not _placeholder(values[key])
    ]
    return _check(
        "env_example_secret_placeholders",
        "pass" if not missing and not non_placeholder else "fail",
        {"missing": missing, "non_placeholder": non_placeholder},
        {"missing": [], "non_placeholder": []},
        details=".env.example must document sensitive variables without committing real values.",
    )


def _check_doc_markers(path: Path, *, check_id: str, markers: tuple[str, ...]) -> dict[str, Any]:
    if not path.is_file():
        return _check(check_id, "fail", "missing", str(path))
    content = _read_text(path)
    missing = [marker for marker in markers if marker not in content]
    return _check(
        check_id,
        "pass" if not missing else "fail",
        {"missing_markers": missing, "path": str(path)},
        {"missing_markers": []},
        details="Secret-management documentation must describe external storage and no-commit handling.",
    )


def _scan_candidate_files(repo_root: Path) -> list[Path]:
    candidates: list[Path] = []
    for relative in (".env.example", "Dockerfile"):
        path = repo_root / relative
        if path.is_file():
            candidates.append(path)
    github_dir = repo_root / ".github" / "workflows"
    if github_dir.is_dir():
        candidates.extend(sorted(github_dir.glob("*.yml")))
        candidates.extend(sorted(github_dir.glob("*.yaml")))
    for pattern in ("docker-compose*.yml", "docker-compose*.yaml", "compose*.yml", "compose*.yaml"):
        candidates.extend(sorted(repo_root.glob(pattern)))
    k8s_dir = repo_root / "k8s"
    if k8s_dir.is_dir():
        candidates.extend(sorted(k8s_dir.rglob("*.yml")))
        candidates.extend(sorted(k8s_dir.rglob("*.yaml")))
    seen: set[Path] = set()
    ordered: list[Path] = []
    for path in candidates:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        ordered.append(path)
    return ordered


def _check_high_risk_config_scan(repo_root: Path) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    scanned: list[str] = []
    for path in _scan_candidate_files(repo_root):
        scanned.append(str(path.relative_to(repo_root)))
        try:
            content = _read_text(path)
        except OSError as exc:
            findings.append({"path": str(path), "line": 0, "name": "read_error", "reason": str(exc)})
            continue
        for line_no, line in enumerate(content.splitlines(), start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            match = HIGH_RISK_ASSIGNMENT_RE.search(stripped)
            if not match:
                continue
            name = match.group(1).strip()
            if name.endswith("_KEY_ID"):
                continue
            value = match.group(2).strip().strip("'\"")
            if _placeholder(value):
                continue
            findings.append(
                {
                    "path": str(path.relative_to(repo_root)),
                    "line": line_no,
                    "name": name,
                    "value_preview": value[:8] + ("..." if len(value) > 8 else ""),
                }
            )
    return _check(
        "high_risk_config_plaintext_secret_scan",
        "pass" if not findings else "fail",
        {"scanned": scanned, "findings": findings},
        {"findings": []},
        details="High-risk config surfaces must use blanks, placeholders, or platform secret references.",
    )


def _status_pass(value: Any) -> bool:
    return str(value or "").strip().lower() in {"pass", "passed", "ok", "ready", "defined", "true"}


def _validate_external_secret_evidence(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return _check(
            "production_secret_manager_evidence",
            "fail",
            "missing",
            str(path),
            details="Production readiness requires explicit external secret-manager evidence.",
        )
    try:
        payload = _read_json(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return _check("production_secret_manager_evidence", "fail", str(exc), "valid JSON object")

    failure_codes: list[str] = []
    provider = str(payload.get("secret_manager_provider", "")).strip().lower()
    managed_classes = payload.get("managed_secret_classes", [])
    if not isinstance(managed_classes, list):
        managed_classes = []
    managed_class_set = {str(item).strip().lower() for item in managed_classes}
    missing_classes = sorted(set(PRODUCTION_SECRET_CLASSES) - managed_class_set)

    if payload.get("schema_version") != EXTERNAL_EVIDENCE_SCHEMA_VERSION:
        failure_codes.append("schema_version_mismatch")
    if not _status_pass(payload.get("status")):
        failure_codes.append("status_not_pass")
    if provider not in PRODUCTION_SECRET_PROVIDERS:
        failure_codes.append("unsupported_secret_manager_provider")
    if missing_classes:
        failure_codes.append("managed_secret_classes_incomplete")
    for key in (
        "runtime_secret_injection_status",
        "rotation_policy_status",
        "plaintext_repo_secret_scan_status",
        "no_plaintext_secrets_in_images",
    ):
        if not _status_pass(payload.get(key)):
            failure_codes.append("%s_not_pass" % key)

    return _check(
        "production_secret_manager_evidence",
        "pass" if not failure_codes else "fail",
        {
            "provider": provider,
            "managed_secret_classes": sorted(managed_class_set),
            "missing_secret_classes": missing_classes,
            "failure_codes": failure_codes,
        },
        {
            "schema_version": EXTERNAL_EVIDENCE_SCHEMA_VERSION,
            "provider_in": sorted(PRODUCTION_SECRET_PROVIDERS),
            "managed_secret_classes": list(PRODUCTION_SECRET_CLASSES),
            "all_status_fields": "pass",
        },
        details="Vault/KMS/Secret Manager evidence is required before claiming production secret management.",
    )


def _build_report(args: argparse.Namespace) -> dict[str, Any]:
    env_example_path = Path(args.env_example).resolve()
    env_doc_path = Path(args.env_doc).resolve()
    artifact_encryption_runbook_path = Path(args.artifact_encryption_runbook).resolve()
    production_ops_runbook_path = Path(args.production_ops_runbook).resolve()
    external_evidence_path = Path(args.external_secret_evidence).resolve()

    checks = [
        _check_env_example(env_example_path),
        _check_doc_markers(env_doc_path, check_id="env_doc_secret_handling", markers=DOC_REQUIRED_MARKERS),
        _check_doc_markers(
            artifact_encryption_runbook_path,
            check_id="artifact_encryption_secret_handling",
            markers=("secret store", "CI secret", "Vault/KMS", "key rotation", "不要提交"),
        ),
        _check_doc_markers(
            production_ops_runbook_path,
            check_id="production_ops_secret_externalization",
            markers=PRODUCTION_OPS_REQUIRED_MARKERS,
        ),
        _check_high_risk_config_scan(REPO_ROOT),
    ]
    if bool(args.require_production_manager):
        checks.append(_validate_external_secret_evidence(external_evidence_path))

    failed_checks = [check["id"] for check in checks if check.get("status") != "pass"]
    status = "SECRETS_READINESS_READY" if not failed_checks else "SECRETS_READINESS_BLOCKED"
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        "status": status,
        "production_manager_required": bool(args.require_production_manager),
        "check_count": len(checks),
        "pass_count": len([check for check in checks if check.get("status") == "pass"]),
        "fail_count": len([check for check in checks if check.get("status") != "pass"]),
        "failed_checks": failed_checks,
        "checks": checks,
        "evidence_paths": {
            "env_example": str(env_example_path),
            "env_doc": str(env_doc_path),
            "artifact_encryption_runbook": str(artifact_encryption_runbook_path),
            "production_ops_runbook": str(production_ops_runbook_path),
            "external_secret_evidence": str(external_evidence_path),
        },
    }


def _render_summary(report: dict[str, Any]) -> str:
    lines = [
        "# Secrets Readiness Summary",
        "",
        "- Status: `%s`" % report.get("status", "SECRETS_READINESS_BLOCKED"),
        "- Production manager required: `%s`" % report.get("production_manager_required", False),
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
        print("Secrets readiness failed: %s" % exc, file=sys.stderr)
        return 2

    summary = _render_summary(report)
    output_value = str(args.output or "").strip()
    summary_output_value = str(args.summary_output or "").strip()
    if output_value and output_value != "-":
        _write_text(Path(output_value).resolve(), json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    if summary_output_value and summary_output_value != "-":
        _write_text(Path(summary_output_value).resolve(), summary)

    print(
        "Secrets readiness status=%s checks=%s pass=%s fail=%s"
        % (
            report.get("status", "SECRETS_READINESS_BLOCKED"),
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
    if bool(args.fail_on_blocked) and report.get("status") != "SECRETS_READINESS_READY":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
