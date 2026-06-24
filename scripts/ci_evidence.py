from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVIDENCE_DIR = REPO_ROOT / "docs" / "working" / "status" / "baselines" / "ci-matrix"
REPORT_SCHEMA_VERSION = "ci_evidence.v1"
CI_SUMMARY_SCHEMA_VERSION = "ci_summary.v1"
PASS_STATUSES = {"pass", "passed", "ok", "success", "succeeded"}
RELEASE_ARTIFACTS_SCHEMA_VERSION = "omni.release_artifacts.v1"
RELEASE_CONSUMER_SCHEMA_VERSION = "release_consumer_smoke.v1"
LAUNCH_GATE_SCHEMA_VERSION = "broad_launch_readiness.v1"
LAUNCH_GATE_DECISIONS = {
    "HOLD",
    "READY_FOR_CONTROLLED_BETA",
    "READY_FOR_GA_REVIEW",
    "READY_FOR_PLATFORM_BETA",
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate the archived CI evidence pack required by the Python matrix release gate.",
    )
    parser.add_argument(
        "--evidence-dir",
        default=str(DEFAULT_EVIDENCE_DIR),
        help="Directory containing CI evidence files.",
    )
    parser.add_argument(
        "--required-python-versions",
        default="3.11,3.12",
        help="Comma or whitespace separated Python minor versions expected in CI summaries.",
    )
    parser.add_argument(
        "--output",
        default="",
        help='JSON report output path. Defaults to <evidence-dir>/ci_evidence_report.json. Use "-" to skip.',
    )
    parser.add_argument(
        "--summary-output",
        default="",
        help='Markdown summary output path. Defaults to <evidence-dir>/ci_evidence_summary.md. Use "-" to skip.',
    )
    parser.add_argument("--print-json", action="store_true")
    parser.add_argument("--fail-on-blocked", action="store_true")
    return parser.parse_args()


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_versions(value: str) -> list[str]:
    versions = [item.strip() for item in value.replace(",", " ").split() if item.strip()]
    if not versions:
        raise ValueError("At least one required Python version is needed.")
    return versions


def _summary_filename(version: str) -> str:
    return "ci_summary_python_%s.json" % version.replace(".", "_")


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("JSON root must be an object.")
    return payload


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _status_is_pass(value: Any) -> bool:
    return str(value or "").strip().lower() in PASS_STATUSES


def _int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _make_check(
    check_id: str,
    status: str,
    *,
    evidence_file: str,
    failure_codes: list[str] | None = None,
    details: dict[str, Any] | None = None,
    blocking: bool = True,
) -> dict[str, Any]:
    return {
        "id": check_id,
        "status": status,
        "blocking": blocking,
        "evidence_file": evidence_file,
        "failure_codes": failure_codes or [],
        "details": details or {},
    }


def _fail(
    check_id: str,
    evidence_file: str,
    code: str,
    *,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _make_check(
        check_id,
        "fail",
        evidence_file=evidence_file,
        failure_codes=[code],
        details=details,
    )


def _load_required_json(
    path: Path,
    check_id: str,
    missing_code: str,
    invalid_code: str,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    if not path.is_file():
        return None, _fail(check_id, path.name, missing_code, details={"path": str(path)})
    try:
        return _read_json(path), None
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return None, _fail(check_id, path.name, invalid_code, details={"path": str(path), "error": str(exc)})


def _command_strings(commands: list[Any]) -> list[str]:
    strings: list[str] = []
    for item in commands:
        if isinstance(item, str):
            strings.append(item)
        elif isinstance(item, dict):
            command = item.get("command_string", item.get("command", ""))
            if isinstance(command, list):
                strings.append(" ".join(str(part) for part in command))
            else:
                strings.append(str(command))
    return strings


def _validate_ci_summary(evidence_dir: Path, version: str) -> dict[str, Any]:
    filename = _summary_filename(version)
    path = evidence_dir / filename
    payload, load_check = _load_required_json(
        path,
        "ci_summary_python_%s" % version.replace(".", "_"),
        "ci_summary_missing:%s" % version,
        "ci_summary_invalid_json:%s" % version,
    )
    if load_check is not None:
        return load_check
    assert payload is not None

    failure_codes: list[str] = []
    schema_version = str(payload.get("schema_version", "")).strip()
    if schema_version != CI_SUMMARY_SCHEMA_VERSION:
        failure_codes.append("ci_summary_schema_mismatch:%s" % version)

    declared_python = str(payload.get("declared_python_version", "")).strip()
    actual_python = str(payload.get("python_version", "")).strip()
    if not declared_python.startswith(version) and not actual_python.startswith(version):
        failure_codes.append("ci_summary_python_version_mismatch:%s" % version)

    if not _status_is_pass(payload.get("status")):
        failure_codes.append("ci_summary_status_failed:%s" % version)

    exit_code = _int_or_none(payload.get("exit_code"))
    if exit_code != 0:
        failure_codes.append("ci_summary_exit_nonzero:%s" % version)

    if not str(payload.get("generated_at_utc", "")).strip():
        failure_codes.append("ci_summary_timestamp_missing:%s" % version)

    command_strings = _command_strings(_as_list(payload.get("commands")))
    if not command_strings:
        failure_codes.append("ci_summary_commands_missing:%s" % version)
    elif not any("scripts/ci.py" in command for command in command_strings):
        failure_codes.append("ci_summary_ci_command_missing:%s" % version)

    coverage_xml = str(payload.get("coverage_xml", "")).strip()
    if coverage_xml and not (evidence_dir / coverage_xml).is_file():
        failure_codes.append("ci_summary_coverage_missing:%s" % version)

    return _make_check(
        "ci_summary_python_%s" % version.replace(".", "_"),
        "pass" if not failure_codes else "fail",
        evidence_file=filename,
        failure_codes=failure_codes,
        details={
            "schema_version": schema_version,
            "declared_python_version": declared_python,
            "python_version": actual_python,
            "status": payload.get("status"),
            "exit_code": exit_code,
            "command_count": len(command_strings),
            "coverage_xml": coverage_xml,
        },
    )


def _validate_coverage_xml(evidence_dir: Path) -> dict[str, Any]:
    path = evidence_dir / "coverage.xml"
    if not path.is_file():
        return _fail("coverage_xml", path.name, "coverage_xml_missing", details={"path": str(path)})
    try:
        tree = ET.parse(path)
        root_tag = tree.getroot().tag
    except (OSError, ET.ParseError) as exc:
        return _fail("coverage_xml", path.name, "coverage_xml_invalid", details={"path": str(path), "error": str(exc)})
    if not str(root_tag).endswith("coverage"):
        return _fail("coverage_xml", path.name, "coverage_xml_root_mismatch", details={"root_tag": root_tag})
    return _make_check(
        "coverage_xml",
        "pass",
        evidence_file=path.name,
        details={"bytes": path.stat().st_size, "root_tag": root_tag},
    )


def _validate_doc_sync(evidence_dir: Path) -> dict[str, Any]:
    path = evidence_dir / "doc_sync.json"
    payload, load_check = _load_required_json(path, "doc_sync", "doc_sync_missing", "doc_sync_invalid_json")
    if load_check is not None:
        return load_check
    assert payload is not None

    failed_count = _int_or_none(payload.get("failed_count"))
    status = payload.get("status")
    failure_codes: list[str] = []
    if not _status_is_pass(status):
        failure_codes.append("doc_sync_status_failed")
    if failed_count != 0:
        failure_codes.append("doc_sync_failed_count_nonzero")
    return _make_check(
        "doc_sync",
        "pass" if not failure_codes else "fail",
        evidence_file=path.name,
        failure_codes=failure_codes,
        details={"status": status, "failed_count": failed_count},
    )


def _validate_release_artifacts(evidence_dir: Path) -> dict[str, Any]:
    path = evidence_dir / "release_artifacts.json"
    payload, load_check = _load_required_json(
        path,
        "release_artifacts",
        "release_artifacts_missing",
        "release_artifacts_invalid_json",
    )
    if load_check is not None:
        return load_check
    assert payload is not None

    artifacts = _as_list(payload.get("artifacts"))
    roles = {str(item.get("role", "")).strip() for item in artifacts if isinstance(item, dict)}
    source_archive = payload.get("source_archive", {})
    if not isinstance(source_archive, dict):
        source_archive = {}

    failure_codes: list[str] = []
    if payload.get("schema_version") != RELEASE_ARTIFACTS_SCHEMA_VERSION:
        failure_codes.append("release_artifacts_schema_mismatch")
    if not str(payload.get("release_id", "")).strip():
        failure_codes.append("release_artifacts_release_id_missing")
    for required_role in ("source_archive", "python_wheel"):
        if required_role not in roles:
            failure_codes.append("release_artifacts_role_missing:%s" % required_role)
    archive_mode = str(source_archive.get("source_archive_mode", "")).strip()
    if archive_mode not in {"git_archive", "source_tree_fallback"}:
        failure_codes.append("release_artifacts_source_archive_mode_missing")
    if not str(source_archive.get("source_archive_sha256", "")).strip():
        failure_codes.append("release_artifacts_source_archive_digest_missing")

    return _make_check(
        "release_artifacts",
        "pass" if not failure_codes else "fail",
        evidence_file=path.name,
        failure_codes=failure_codes,
        details={
            "schema_version": payload.get("schema_version"),
            "release_id": payload.get("release_id"),
            "roles": sorted(roles),
            "source_archive_mode": archive_mode,
        },
    )


def _validate_release_consumer_smoke(evidence_dir: Path) -> dict[str, Any]:
    path = evidence_dir / "release_consumer_smoke.json"
    payload, load_check = _load_required_json(
        path,
        "release_consumer_smoke",
        "release_consumer_smoke_missing",
        "release_consumer_smoke_invalid_json",
    )
    if load_check is not None:
        return load_check
    assert payload is not None

    failure_codes: list[str] = []
    if payload.get("schema_version") != RELEASE_CONSUMER_SCHEMA_VERSION:
        failure_codes.append("release_consumer_smoke_schema_mismatch")
    if str(payload.get("decision", "")).strip().upper() != "PASS":
        failure_codes.append("release_consumer_smoke_decision_not_pass")
    stages = _as_list(payload.get("stages"))
    if not stages:
        failure_codes.append("release_consumer_smoke_stages_missing")
    return _make_check(
        "release_consumer_smoke",
        "pass" if not failure_codes else "fail",
        evidence_file=path.name,
        failure_codes=failure_codes,
        details={
            "schema_version": payload.get("schema_version"),
            "decision": payload.get("decision"),
            "stage_count": len(stages),
        },
    )


def _validate_launch_gate(evidence_dir: Path) -> dict[str, Any]:
    path = evidence_dir / "launch_gate.json"
    payload, load_check = _load_required_json(path, "launch_gate", "launch_gate_missing", "launch_gate_invalid_json")
    if load_check is not None:
        return load_check
    assert payload is not None

    decision = str(payload.get("decision", "")).strip().upper()
    checks = _as_list(payload.get("checks"))
    failed_checks = payload.get("failed_checks", [])

    failure_codes: list[str] = []
    if payload.get("schema_version") != LAUNCH_GATE_SCHEMA_VERSION:
        failure_codes.append("launch_gate_schema_mismatch")
    if decision not in LAUNCH_GATE_DECISIONS:
        failure_codes.append("launch_gate_decision_unknown")
    if not checks:
        failure_codes.append("launch_gate_checks_missing")
    if not isinstance(failed_checks, list):
        failure_codes.append("launch_gate_failed_checks_not_list")

    return _make_check(
        "launch_gate",
        "pass" if not failure_codes else "fail",
        evidence_file=path.name,
        failure_codes=failure_codes,
        details={
            "schema_version": payload.get("schema_version"),
            "decision": decision,
            "check_count": len(checks),
            "failed_check_count": len(failed_checks) if isinstance(failed_checks, list) else None,
            "hold_is_allowed": True,
        },
    )


def build_report(evidence_dir: Path, required_python_versions: list[str]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    checks.extend(_validate_ci_summary(evidence_dir, version) for version in required_python_versions)
    checks.append(_validate_coverage_xml(evidence_dir))
    checks.append(_validate_doc_sync(evidence_dir))
    checks.append(_validate_release_artifacts(evidence_dir))
    checks.append(_validate_release_consumer_smoke(evidence_dir))
    checks.append(_validate_launch_gate(evidence_dir))

    failed_checks = [check for check in checks if check.get("blocking") and check.get("status") != "pass"]
    blocking_codes: list[str] = []
    for check in failed_checks:
        blocking_codes.extend(str(code) for code in check.get("failure_codes", []))

    required_files = [_summary_filename(version) for version in required_python_versions] + [
        "coverage.xml",
        "doc_sync.json",
        "release_artifacts.json",
        "release_consumer_smoke.json",
        "launch_gate.json",
    ]
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        "status": "CI_EVIDENCE_READY" if not failed_checks else "CI_EVIDENCE_BLOCKED",
        "evidence_dir": str(evidence_dir),
        "required_python_versions": required_python_versions,
        "required_files": required_files,
        "missing_files": [name for name in required_files if not (evidence_dir / name).is_file()],
        "blocking_codes": blocking_codes,
        "check_count": len(checks),
        "pass_count": len([check for check in checks if check.get("status") == "pass"]),
        "fail_count": len([check for check in checks if check.get("status") != "pass"]),
        "checks": checks,
    }


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _render_summary(report: dict[str, Any]) -> str:
    lines = [
        "# CI Evidence Summary",
        "",
        "- Status: `%s`" % report.get("status", ""),
        "- Evidence dir: `%s`" % report.get("evidence_dir", ""),
        "- Required Python: `%s`" % ", ".join(str(item) for item in report.get("required_python_versions", [])),
        "- Blocking codes: `%s`" % (", ".join(report.get("blocking_codes", [])) or "none"),
        "",
        "## Checks",
        "",
    ]
    for check in report.get("checks", []):
        lines.append("- `%s`: `%s`" % (check.get("id", ""), check.get("status", "")))
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    try:
        evidence_dir = Path(str(args.evidence_dir)).expanduser().resolve()
        required_versions = _parse_versions(str(args.required_python_versions))
        report = build_report(evidence_dir, required_versions)
        output_value = str(args.output or "").strip()
        summary_output_value = str(args.summary_output or "").strip()
        output_path = evidence_dir / "ci_evidence_report.json" if not output_value else Path(output_value).resolve()
        summary_path = (
            evidence_dir / "ci_evidence_summary.md"
            if not summary_output_value
            else Path(summary_output_value).resolve()
        )
        if output_value != "-":
            _write_text(output_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
            print("CI evidence report written: %s" % output_path)
        if summary_output_value != "-":
            _write_text(summary_path, _render_summary(report))
            print("CI evidence summary written: %s" % summary_path)
    except (OSError, ValueError) as exc:
        print("CI evidence validation failed: %s" % exc, file=sys.stderr)
        return 2

    print(
        "CI evidence status=%s checks=%s pass=%s fail=%s"
        % (report["status"], report["check_count"], report["pass_count"], report["fail_count"])
    )
    if report["blocking_codes"]:
        print("Blocking codes: %s" % ", ".join(report["blocking_codes"]))
    else:
        print("Blocking codes: none")
    if args.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.fail_on_blocked and report.get("status") != "CI_EVIDENCE_READY":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
