from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_SCHEMA_VERSION = "postgres_readiness.v1"
DEFAULT_PG_GA_REPORT = (
    REPO_ROOT / "docs" / "working" / "status" / "baselines" / "e13-postgres-ga-validation-plan.json"
)
DEFAULT_PG_SOAK_REPORT = (
    REPO_ROOT / "docs" / "working" / "status" / "baselines" / "e13-postgres-soak-plan.json"
)
DEFAULT_BENCHMARK_REPORT = (
    REPO_ROOT / "docs" / "working" / "status" / "baselines" / "e13-postgres-soak-benchmark-report.json"
)
DEFAULT_OPERATIONS_REPORT = (
    REPO_ROOT / "docs" / "working" / "status" / "baselines" / "operations-readiness-report.json"
)
DEFAULT_SCHEMA_SQL = REPO_ROOT / "infra" / "sql" / "001_init.sql"
DEFAULT_CLI_DOC = REPO_ROOT / "docs" / "latest" / "operations" / "cli.md"
DEFAULT_OUTPUT = REPO_ROOT / "docs" / "working" / "status" / "baselines" / "postgres-readiness-report.json"
DEFAULT_SUMMARY_OUTPUT = (
    REPO_ROOT / "docs" / "working" / "status" / "baselines" / "postgres-readiness-summary.md"
)

PG_GA_SCHEMA_VERSION = "postgres_ga_validation.v1"
PG_SOAK_SCHEMA_VERSION = "postgres_soak_validation.v1"
OPERATIONS_SCHEMA_VERSION = "operations_readiness.v1"
PG_GA_REQUIRED_STAGES = (
    "postgres_repository_contract",
    "postgres_repository_integration",
    "dual_write_contract",
    "dual_write_integration",
    "dual_write_benchmark",
)
PG_SOAK_REQUIRED_STAGES = ("tp_postgres", "review_queue", "dual_write_benchmark")
SCHEMA_REQUIRED_TABLES = (
    "ingest_jobs",
    "assets",
    "evidence_units",
    "insights",
    "skills",
    "skill_versions",
    "publications",
    "review_tasks",
    "lineage_links",
    "tenant_scopes",
)
RETENTION_DOC_MARKERS = (
    "governance-report",
    "upsert-retention-policy",
    "--retention-days",
    "artifact_retention",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate the Postgres/dual-write productionization evidence contract.",
    )
    parser.add_argument("--pg-ga-report", default=str(DEFAULT_PG_GA_REPORT))
    parser.add_argument("--pg-soak-report", default=str(DEFAULT_PG_SOAK_REPORT))
    parser.add_argument("--benchmark-report", default=str(DEFAULT_BENCHMARK_REPORT))
    parser.add_argument("--operations-readiness-report", default=str(DEFAULT_OPERATIONS_REPORT))
    parser.add_argument("--schema-sql", default=str(DEFAULT_SCHEMA_SQL))
    parser.add_argument("--cli-doc", default=str(DEFAULT_CLI_DOC))
    parser.add_argument(
        "--min-benchmark-iterations",
        type=int,
        default=120,
        help="Minimum real Postgres dual-write iterations required in the benchmark report.",
    )
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help='Use "-" to skip writing JSON.')
    parser.add_argument("--summary-output", default=str(DEFAULT_SUMMARY_OUTPUT), help='Use "-" to skip writing.')
    parser.add_argument("--print-json", action="store_true")
    parser.add_argument("--fail-on-blocked", action="store_true")
    return parser.parse_args()


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("JSON root must be an object: %s" % path)
    return payload


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _int_value(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


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


def _missing_check(check_id: str, path: Path, code: str) -> dict[str, Any]:
    return _make_check(
        check_id,
        "fail",
        evidence_file=str(path),
        failure_codes=[code],
        details={"path": str(path)},
    )


def _load_required_json(path: Path, check_id: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    if not path.is_file():
        return None, _missing_check(check_id, path, "%s_missing" % check_id)
    try:
        return _read_json(path), None
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return None, _make_check(
            check_id,
            "fail",
            evidence_file=str(path),
            failure_codes=["%s_invalid_json" % check_id],
            details={"path": str(path), "error": str(exc)},
        )


def _stage_names(report: dict[str, Any], key: str) -> set[str]:
    names: set[str] = set()
    for item in _as_list(report.get(key)):
        if isinstance(item, dict):
            name = str(item.get("name", "")).strip()
            if name:
                names.add(name)
    return names


def _stage_result_statuses(report: dict[str, Any]) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for item in _as_list(report.get("stage_results")):
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        if name:
            statuses[name] = str(item.get("status", "")).strip().lower()
    return statuses


def _validate_execution_report(
    *,
    path: Path,
    check_id: str,
    expected_schema: str,
    required_stages: tuple[str, ...],
) -> dict[str, Any]:
    payload, load_check = _load_required_json(path, check_id)
    if load_check is not None:
        return load_check
    assert payload is not None

    failure_codes: list[str] = []
    schema_version = str(payload.get("schema_version", "")).strip()
    decision = str(payload.get("decision", "")).strip().upper()
    execution_mode = str(payload.get("execution_mode", "")).strip().lower()
    declared_stages = _stage_names(payload, "stages")
    result_statuses = _stage_result_statuses(payload)
    missing_stages = [stage for stage in required_stages if stage not in declared_stages]
    missing_results = [stage for stage in required_stages if stage not in result_statuses]
    failed_results = [
        stage
        for stage in required_stages
        if result_statuses.get(stage, "") not in {"pass", "passed", "ok", "success"}
    ]

    if schema_version != expected_schema:
        failure_codes.append("%s_schema_mismatch" % check_id)
    if decision != "PASS":
        failure_codes.append("%s_decision_not_pass" % check_id)
    if execution_mode != "executed":
        failure_codes.append("%s_not_executed" % check_id)
    if payload.get("postgres_dsn_provided") is not True:
        failure_codes.append("%s_postgres_dsn_missing" % check_id)
    if missing_stages:
        failure_codes.append("%s_required_stage_missing" % check_id)
    if missing_results:
        failure_codes.append("%s_stage_result_missing" % check_id)
    if failed_results:
        failure_codes.append("%s_stage_failed" % check_id)

    return _make_check(
        check_id,
        "pass" if not failure_codes else "fail",
        evidence_file=str(path),
        failure_codes=failure_codes,
        details={
            "schema_version": schema_version,
            "decision": decision,
            "execution_mode": execution_mode,
            "postgres_dsn_provided": payload.get("postgres_dsn_provided"),
            "required_stages": list(required_stages),
            "missing_stages": missing_stages,
            "missing_results": missing_results,
            "failed_results": failed_results,
        },
    )


def _validate_benchmark_report(path: Path, min_iterations: int) -> dict[str, Any]:
    payload, load_check = _load_required_json(path, "dual_write_benchmark")
    if load_check is not None:
        return load_check
    assert payload is not None

    runs = payload.get("runs")
    if not isinstance(runs, dict):
        runs = {}
    dual_write = runs.get("dual_write")
    if not isinstance(dual_write, dict):
        dual_write = {}
    summary = dual_write.get("summary")
    if not isinstance(summary, dict):
        summary = {}
    count = _int_value(summary.get("count"))

    failure_codes: list[str] = []
    if payload.get("run_postgres") is not True:
        failure_codes.append("dual_write_benchmark_postgres_not_run")
    if payload.get("postgres_configured") is not True:
        failure_codes.append("dual_write_benchmark_postgres_not_configured")
    if payload.get("postgres_schema_bootstrapped") is not True:
        failure_codes.append("dual_write_benchmark_schema_not_bootstrapped")
    if count < min_iterations:
        failure_codes.append("dual_write_benchmark_iteration_count_too_low")

    return _make_check(
        "dual_write_benchmark",
        "pass" if not failure_codes else "fail",
        evidence_file=str(path),
        failure_codes=failure_codes,
        details={
            "run_postgres": payload.get("run_postgres"),
            "postgres_configured": payload.get("postgres_configured"),
            "postgres_schema_bootstrapped": payload.get("postgres_schema_bootstrapped"),
            "dual_write_count": count,
            "min_benchmark_iterations": min_iterations,
        },
    )


def _validate_operations_report(path: Path) -> dict[str, Any]:
    payload, load_check = _load_required_json(path, "operations_readiness")
    if load_check is not None:
        return load_check
    assert payload is not None

    check_statuses: dict[str, str] = {}
    for item in _as_list(payload.get("checks")):
        if isinstance(item, dict):
            check_statuses[str(item.get("id", "")).strip()] = str(item.get("status", "")).strip().lower()

    failure_codes: list[str] = []
    if payload.get("schema_version") != OPERATIONS_SCHEMA_VERSION:
        failure_codes.append("operations_readiness_schema_mismatch")
    if str(payload.get("overall_status", "")).strip().lower() != "pass":
        failure_codes.append("operations_readiness_not_pass")
    if check_statuses.get("production_ops_runbook_contract") != "pass":
        failure_codes.append("operations_backup_restore_contract_missing")

    return _make_check(
        "operations_readiness",
        "pass" if not failure_codes else "fail",
        evidence_file=str(path),
        failure_codes=failure_codes,
        details={
            "schema_version": payload.get("schema_version"),
            "overall_status": payload.get("overall_status"),
            "production_ops_runbook_contract": check_statuses.get("production_ops_runbook_contract", "missing"),
        },
    )


def _validate_schema_sql(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return _missing_check("schema_migration_sql", path, "schema_migration_sql_missing")
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        return _make_check(
            "schema_migration_sql",
            "fail",
            evidence_file=str(path),
            failure_codes=["schema_migration_sql_unreadable"],
            details={"path": str(path), "error": str(exc)},
        )
    normalized = content.lower()
    missing_tables = [table for table in SCHEMA_REQUIRED_TABLES if "create table %s" % table not in normalized]
    failure_codes = ["schema_migration_table_missing"] if missing_tables else []
    return _make_check(
        "schema_migration_sql",
        "pass" if not failure_codes else "fail",
        evidence_file=str(path),
        failure_codes=failure_codes,
        details={"missing_tables": missing_tables, "required_tables": list(SCHEMA_REQUIRED_TABLES)},
    )


def _validate_retention_doc(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return _missing_check("data_retention_surface", path, "data_retention_surface_missing")
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return _make_check(
            "data_retention_surface",
            "fail",
            evidence_file=str(path),
            failure_codes=["data_retention_surface_unreadable"],
            details={"path": str(path), "error": str(exc)},
        )
    missing_markers = [marker for marker in RETENTION_DOC_MARKERS if marker not in content]
    failure_codes = ["data_retention_marker_missing"] if missing_markers else []
    return _make_check(
        "data_retention_surface",
        "pass" if not failure_codes else "fail",
        evidence_file=str(path),
        failure_codes=failure_codes,
        details={"missing_markers": missing_markers},
    )


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    min_iterations = max(1, int(args.min_benchmark_iterations))
    checks = [
        _validate_execution_report(
            path=Path(args.pg_ga_report).resolve(),
            check_id="postgres_ga",
            expected_schema=PG_GA_SCHEMA_VERSION,
            required_stages=PG_GA_REQUIRED_STAGES,
        ),
        _validate_execution_report(
            path=Path(args.pg_soak_report).resolve(),
            check_id="postgres_soak",
            expected_schema=PG_SOAK_SCHEMA_VERSION,
            required_stages=PG_SOAK_REQUIRED_STAGES,
        ),
        _validate_benchmark_report(Path(args.benchmark_report).resolve(), min_iterations),
        _validate_operations_report(Path(args.operations_readiness_report).resolve()),
        _validate_schema_sql(Path(args.schema_sql).resolve()),
        _validate_retention_doc(Path(args.cli_doc).resolve()),
    ]
    failed_checks = [check for check in checks if check.get("blocking") and check.get("status") != "pass"]
    blocking_codes: list[str] = []
    for check in failed_checks:
        blocking_codes.extend(str(code) for code in check.get("failure_codes", []))
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        "status": "POSTGRES_READINESS_READY" if not failed_checks else "POSTGRES_READINESS_BLOCKED",
        "blocking_codes": blocking_codes,
        "check_count": len(checks),
        "pass_count": len([check for check in checks if check.get("status") == "pass"]),
        "fail_count": len([check for check in checks if check.get("status") != "pass"]),
        "checks": checks,
    }


def _render_summary(report: dict[str, Any]) -> str:
    lines = [
        "# Postgres Readiness Summary",
        "",
        "- Status: `%s`" % report.get("status", ""),
        "- Checks: `%s`" % report.get("check_count", 0),
        "- Passed: `%s`" % report.get("pass_count", 0),
        "- Failed: `%s`" % report.get("fail_count", 0),
        "- Blocking codes: `%s`" % (", ".join(report.get("blocking_codes", [])) or "none"),
        "",
        "## Checks",
        "",
    ]
    for check in report.get("checks", []):
        lines.append("- `%s`: `%s`" % (check.get("id", ""), check.get("status", "")))
    lines.append("")
    return "\n".join(lines)


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    args = _parse_args()
    try:
        report = build_report(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print("Postgres readiness validation failed: %s" % exc, file=sys.stderr)
        return 2

    output_value = str(args.output or "").strip()
    summary_output_value = str(args.summary_output or "").strip()
    if output_value and output_value != "-":
        output_path = Path(output_value).resolve()
        _write_text(output_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print("Postgres readiness report written: %s" % output_path)
    if summary_output_value and summary_output_value != "-":
        summary_path = Path(summary_output_value).resolve()
        _write_text(summary_path, _render_summary(report))
        print("Postgres readiness summary written: %s" % summary_path)

    print(
        "Postgres readiness status=%s checks=%s pass=%s fail=%s"
        % (report["status"], report["check_count"], report["pass_count"], report["fail_count"])
    )
    if report["blocking_codes"]:
        print("Blocking codes: %s" % ", ".join(report["blocking_codes"]))
    else:
        print("Blocking codes: none")
    if args.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.fail_on_blocked and report.get("status") != "POSTGRES_READINESS_READY":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
