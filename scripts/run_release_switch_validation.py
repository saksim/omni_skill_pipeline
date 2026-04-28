from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DOC_SYNC_REPORT = (
    REPO_ROOT / 'docs' / 'current' / 'status' / 'baselines' / 'e13-doc-sync-check-report.json'
)
DEFAULT_QUALITY_REPORT = (
    REPO_ROOT / 'docs' / 'current' / 'status' / 'baselines' / 'e11-quality-regression-report.json'
)
DEFAULT_PERF_REPORT = (
    REPO_ROOT / 'docs' / 'current' / 'status' / 'baselines' / 'e11-perf-cost-baseline-report.json'
)
DEFAULT_POSTGRES_SOAK_BENCHMARK_REPORT = (
    REPO_ROOT / 'docs' / 'current' / 'status' / 'baselines' / 'e13-postgres-soak-benchmark-report.json'
)
DEFAULT_RELEASE_STANDARD_DOC = (
    REPO_ROOT / 'docs' / 'current' / 'status' / 'v2-release-switch-standard.md'
)
DEFAULT_BETA_SUITE_OUTPUT = (
    REPO_ROOT / 'docs' / 'current' / 'status' / 'baselines' / 'e13-release-gate-beta-suite-plan.json'
)
DEFAULT_GA_SUITE_OUTPUT = (
    REPO_ROOT / 'docs' / 'current' / 'status' / 'baselines' / 'e13-release-gate-ga-suite-plan.json'
)
DEFAULT_ROADMAP_SUITE_OUTPUT = (
    REPO_ROOT / 'docs' / 'current' / 'status' / 'baselines' / 'e13-release-gate-roadmap-suite-plan.json'
)
DEFAULT_RELEASE_GATE_OUTPUT = (
    REPO_ROOT / 'docs' / 'current' / 'status' / 'baselines' / 'e13-release-gate-validation-plan.json'
)
DEFAULT_PLAN_OUTPUT = (
    REPO_ROOT / 'docs' / 'current' / 'status' / 'baselines' / 'e13-release-switch-validation-plan.json'
)
DEFAULT_DECISION_OUTPUT = (
    REPO_ROOT / 'docs' / 'current' / 'status' / 'baselines' / 'e13-release-switch-decision-report.json'
)
DEFAULT_CALIBRATION_MANIFEST = (
    REPO_ROOT / 'docs' / 'current' / 'status' / 'baselines' / 'e7-calibration-manifest.json'
)
DEFAULT_CALIBRATION_REPORT_OUTPUT = (
    REPO_ROOT / 'docs' / 'current' / 'status' / 'baselines' / 'e7-calibration-report.json'
)
DEFAULT_CONTAINER_IMAGE_TAG = 'omni-skill-pipeline:beta'
DEFAULT_CONTAINER_NAME = 'omni-skill-pipeline-smoke'
DEFAULT_CONTAINER_HOST = '127.0.0.1'
DEFAULT_CONTAINER_PORT = 18000
DEFAULT_CONTAINER_TIMEOUT_SECONDS = 30.0
DEFAULT_CONTAINER_INTERVAL_SECONDS = 1.0
DEFAULT_MAX_EVIDENCE_FUTURE_SKEW_HOURS = 0.25
DEFAULT_MAX_EVIDENCE_COHORT_SKEW_HOURS = 12.0
DEFAULT_RELEASE_GATE_COVERAGE_FLOOR = 50.0
FORBIDDEN_PYTHON_OPTIMIZATION_FLAGS = ('-O', '-OO')
FORBIDDEN_PYTHON_OPTIMIZE_ENV_KEYS = ('PYTHONOPTIMIZE',)
FORBIDDEN_PYTHON_PATH_ENV_KEYS = ('PYTHONPATH',)
FORBIDDEN_PYTHON_HOME_ENV_KEYS = ('PYTHONHOME',)
FORBIDDEN_PYTHON_USER_BASE_ENV_KEYS = ('PYTHONUSERBASE',)
FORBIDDEN_PYTHON_BREAKPOINT_ENV_KEYS = ('PYTHONBREAKPOINT',)
FORBIDDEN_PYTHON_STARTUP_ENV_KEYS = ('PYTHONSTARTUP',)
FORBIDDEN_PYTHON_INSPECT_ENV_KEYS = ('PYTHONINSPECT',)
FORBIDDEN_PYTHON_WARNINGS_ENV_KEYS = ('PYTHONWARNINGS',)
DEFAULT_STAGES = ('release_gate', 'release_contract', 'doc_sync')
ALL_STAGES = tuple(DEFAULT_STAGES)
RELEASE_GATE_MARKERS = (
    'graph_is_source_of_truth',
    'review_queue_operational',
    'publication_view_count>=2',
    'postgres_repository_stable',
    'regression_beats_v1',
)


@dataclass(frozen=True, slots=True)
class StageSpec:
    name: str
    description: str
    command: list[str]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Run release-switch validation command pack and evaluate GO/HOLD evidence gates.',
    )
    parser.add_argument(
        '--python',
        default='python3',
        help='Python command for Linux execution, e.g. "python3" or "python3.11".',
    )
    parser.add_argument(
        '--stages',
        nargs='*',
        choices=ALL_STAGES,
        default=list(DEFAULT_STAGES),
        help='Validation stages to include. Defaults to release-gate + TP contract + doc-sync.',
    )
    parser.add_argument(
        '--coverage-fail-under',
        type=float,
        default=50.0,
        help='Coverage fail-under forwarded into release_gate stage.',
    )
    parser.add_argument(
        '--no-coverage',
        action='store_true',
        help='Forward --no-coverage into release_gate stage.',
    )
    parser.add_argument(
        '--allow-regression',
        action='store_true',
        help='Forward --allow-regression into release_gate stage.',
    )
    parser.add_argument(
        '--container-image-tag',
        default=DEFAULT_CONTAINER_IMAGE_TAG,
        help='Container smoke image tag forwarded into release_gate stage.',
    )
    parser.add_argument(
        '--container-name',
        default=DEFAULT_CONTAINER_NAME,
        help='Container smoke name forwarded into release_gate stage.',
    )
    parser.add_argument(
        '--container-host',
        default=DEFAULT_CONTAINER_HOST,
        help='Container smoke host forwarded into release_gate stage.',
    )
    parser.add_argument(
        '--container-port',
        type=int,
        default=DEFAULT_CONTAINER_PORT,
        help='Container smoke host port forwarded into release_gate stage.',
    )
    parser.add_argument(
        '--container-timeout-seconds',
        type=float,
        default=DEFAULT_CONTAINER_TIMEOUT_SECONDS,
        help='Container smoke timeout forwarded into release_gate stage.',
    )
    parser.add_argument(
        '--container-interval-seconds',
        type=float,
        default=DEFAULT_CONTAINER_INTERVAL_SECONDS,
        help='Container smoke polling interval forwarded into release_gate stage.',
    )
    parser.add_argument(
        '--container-skip-build',
        action='store_true',
        help='Forward --container-skip-build into release_gate stage.',
    )
    parser.add_argument(
        '--container-skip-run',
        action='store_true',
        help='Forward --container-skip-run into release_gate stage.',
    )
    parser.add_argument(
        '--postgres-dsn',
        default=os.getenv('OMNI_TEST_POSTGRES_DSN', ''),
        help='Postgres DSN forwarded into release_gate stage.',
    )
    parser.add_argument(
        '--postgres-soak-iterations',
        type=int,
        default=120,
        help='Postgres soak iterations forwarded into release_gate stage.',
    )
    parser.add_argument(
        '--postgres-ga-iterations',
        type=int,
        default=120,
        help='Postgres GA iterations forwarded into release_gate stage.',
    )
    parser.add_argument(
        '--allow-secondary-failures',
        action='store_true',
        help='Forward --allow-secondary-failures into release_gate stage.',
    )
    parser.add_argument(
        '--calibration-manifest',
        default=str(DEFAULT_CALIBRATION_MANIFEST),
        help='Calibration manifest forwarded into release_gate stage.',
    )
    parser.add_argument(
        '--calibration-report-output',
        default=str(DEFAULT_CALIBRATION_REPORT_OUTPUT),
        help='Calibration report output forwarded into release_gate stage.',
    )
    parser.add_argument(
        '--calibration-margin',
        type=float,
        default=0.03,
        help='Calibration margin forwarded into release_gate stage.',
    )
    parser.add_argument(
        '--calibration-fail-on-mismatch',
        action='store_true',
        help='Forward --calibration-fail-on-mismatch into release_gate stage.',
    )
    parser.add_argument(
        '--beta-suite-output',
        default=str(DEFAULT_BETA_SUITE_OUTPUT),
        help='Nested release-gate beta suite output path used for decision evaluation.',
    )
    parser.add_argument(
        '--ga-suite-output',
        default=str(DEFAULT_GA_SUITE_OUTPUT),
        help='Nested release-gate GA suite output path used for decision evaluation.',
    )
    parser.add_argument(
        '--roadmap-suite-output',
        default=str(DEFAULT_ROADMAP_SUITE_OUTPUT),
        help='Nested release-gate roadmap suite output path used for decision evaluation.',
    )
    parser.add_argument(
        '--release-gate-output',
        default=str(DEFAULT_RELEASE_GATE_OUTPUT),
        help='Release-gate top-level plan output path used for decision evaluation.',
    )
    parser.add_argument(
        '--doc-sync-report',
        default=str(DEFAULT_DOC_SYNC_REPORT),
        help='Doc-sync report path used by doc_sync stage and decision evaluation.',
    )
    parser.add_argument(
        '--quality-report',
        default=str(DEFAULT_QUALITY_REPORT),
        help='Quality regression report path used for decision evaluation.',
    )
    parser.add_argument(
        '--perf-report',
        default=str(DEFAULT_PERF_REPORT),
        help='Perf-cost baseline report path used for decision evaluation.',
    )
    parser.add_argument(
        '--postgres-soak-benchmark-report',
        default=str(DEFAULT_POSTGRES_SOAK_BENCHMARK_REPORT),
        help='Postgres soak benchmark report path used for decision evaluation.',
    )
    parser.add_argument(
        '--release-standard-doc',
        default=str(DEFAULT_RELEASE_STANDARD_DOC),
        help='Release switch standard document path used for gate-marker checks.',
    )
    parser.add_argument(
        '--decision-only',
        action='store_true',
        help='Skip command stages and evaluate decision from existing evidence files only.',
    )
    parser.add_argument(
        '--allow-hold',
        action='store_true',
        help='Return exit code 0 even when decision is HOLD.',
    )
    parser.add_argument(
        '--max-evidence-age-hours',
        type=float,
        default=24.0,
        help='Maximum allowed age in hours for evidence files used by decision gates. Set <=0 to disable freshness check.',
    )
    parser.add_argument(
        '--max-evidence-future-skew-hours',
        type=float,
        default=DEFAULT_MAX_EVIDENCE_FUTURE_SKEW_HOURS,
        help='Maximum allowed future timestamp skew in hours for evidence files. Set <=0 to disable future-skew gate.',
    )
    parser.add_argument(
        '--max-evidence-cohort-skew-hours',
        type=float,
        default=DEFAULT_MAX_EVIDENCE_COHORT_SKEW_HOURS,
        help='Maximum allowed timestamp spread across decision evidence files in hours. Set <=0 to disable cohort-skew gate.',
    )
    parser.add_argument(
        '--skip-release-gate-output-binding-check',
        action='store_true',
        help='Disable release-gate stage output path binding gate in decision evaluation.',
    )
    parser.add_argument(
        '--skip-release-gate-stage-contract-check',
        action='store_true',
        help='Disable release-gate stage contract gate (script path + --stages set) in decision evaluation.',
    )
    parser.add_argument(
        '--skip-release-gate-script-position-check',
        action='store_true',
        help='Disable release-gate script-position gate (enforce linux-suite script as executed script token) in decision evaluation.',
    )
    parser.add_argument(
        '--skip-release-gate-script-anchor-check',
        action='store_true',
        help='Disable release-gate script-anchor gate (enforce linux-suite script resolves to repository canonical path) in decision evaluation.',
    )
    parser.add_argument(
        '--skip-release-gate-python-binding-check',
        action='store_true',
        help='Disable release-gate python-binding gate (--python consistency checks) in decision evaluation.',
    )
    parser.add_argument(
        '--skip-release-gate-python-optimization-check',
        action='store_true',
        help='Disable release-gate python-optimization gate (-O/-OO assert-bypass checks) in decision evaluation.',
    )
    parser.add_argument(
        '--skip-release-gate-python-option-optimization-check',
        action='store_true',
        help='Disable release-gate python-option optimization gate (--python relay -O/-OO checks) in decision evaluation.',
    )
    parser.add_argument(
        '--skip-release-gate-python-optimize-env-check',
        action='store_true',
        help='Disable release-gate python-optimize-env gate (PYTHONOPTIMIZE env-assignment checks) in decision evaluation.',
    )
    parser.add_argument(
        '--skip-release-gate-python-path-env-check',
        action='store_true',
        help='Disable release-gate python-path-env gate (PYTHONPATH env-assignment checks) in decision evaluation.',
    )
    parser.add_argument(
        '--skip-release-gate-python-home-env-check',
        action='store_true',
        help='Disable release-gate python-home-env gate (PYTHONHOME env-assignment checks) in decision evaluation.',
    )
    parser.add_argument(
        '--skip-release-gate-python-user-base-env-check',
        action='store_true',
        help='Disable release-gate python-user-base-env gate (PYTHONUSERBASE env-assignment checks) in decision evaluation.',
    )
    parser.add_argument(
        '--skip-release-gate-python-breakpoint-env-check',
        action='store_true',
        help='Disable release-gate python-breakpoint-env gate (PYTHONBREAKPOINT env-assignment checks) in decision evaluation.',
    )
    parser.add_argument(
        '--skip-release-gate-python-startup-env-check',
        action='store_true',
        help='Disable release-gate python-startup-env gate (PYTHONSTARTUP env-assignment checks) in decision evaluation.',
    )
    parser.add_argument(
        '--skip-release-gate-python-inspect-env-check',
        action='store_true',
        help='Disable release-gate python-inspect-env gate (PYTHONINSPECT env-assignment checks) in decision evaluation.',
    )
    parser.add_argument(
        '--skip-release-gate-python-warnings-env-check',
        action='store_true',
        help='Disable release-gate python-warnings-env gate (PYTHONWARNINGS env-assignment checks) in decision evaluation.',
    )
    parser.add_argument(
        '--skip-release-gate-python-option-inline-exec-check',
        action='store_true',
        help='Disable release-gate python-option inline-exec gate (--python relay -c/-m/- checks) in decision evaluation.',
    )
    parser.add_argument(
        '--skip-release-gate-coverage-floor-check',
        action='store_true',
        help='Disable release-gate coverage-floor gate (--coverage-fail-under binding + minimum floor) in decision evaluation.',
    )
    parser.add_argument(
        '--skip-release-gate-inline-exec-check',
        action='store_true',
        help='Disable release-gate inline-exec gate (-c/-m/- dispatch bypass checks) in decision evaluation.',
    )
    parser.add_argument(
        '--skip-release-gate-option-override-check',
        action='store_true',
        help='Disable release-gate option override gate (--stages/--output ambiguity checks) in decision evaluation.',
    )
    parser.add_argument(
        '--skip-release-gate-dry-run-check',
        action='store_true',
        help='Disable release-gate dry-run gate (--dry-run bypass checks) in decision evaluation.',
    )
    parser.add_argument(
        '--skip-release-gate-relaxed-flags-check',
        action='store_true',
        help='Disable release-gate relaxed-flags gate (--allow-regression/--no-coverage/etc.) in decision evaluation.',
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Print command pack without executing stages.',
    )
    parser.add_argument(
        '--output',
        default=str(DEFAULT_PLAN_OUTPUT),
        help='Write command plan JSON to this path. Use "-" to skip file writing.',
    )
    parser.add_argument(
        '--decision-output',
        default=str(DEFAULT_DECISION_OUTPUT),
        help='Write decision report JSON to this path. Use "-" to skip file writing.',
    )
    parser.add_argument(
        '--print-json',
        action='store_true',
        help='Print decision report JSON to stdout.',
    )
    return parser.parse_args()


def _split_python_command(raw: str) -> list[str]:
    parts = shlex.split(raw, posix=os.name != 'nt')
    if not parts:
        raise ValueError('Empty --python command.')
    return parts


def _build_stage_map(args: argparse.Namespace, *, python_cmd: list[str]) -> dict[str, StageSpec]:
    release_gate_command = [
        *python_cmd,
        'scripts/run_release_gate_validation.py',
        '--python',
        str(args.python),
        '--coverage-fail-under',
        str(float(args.coverage_fail_under)),
        '--container-image-tag',
        str(args.container_image_tag),
        '--container-name',
        str(args.container_name),
        '--container-host',
        str(args.container_host),
        '--container-port',
        str(int(args.container_port)),
        '--container-timeout-seconds',
        str(float(args.container_timeout_seconds)),
        '--container-interval-seconds',
        str(float(args.container_interval_seconds)),
        '--postgres-soak-iterations',
        str(int(args.postgres_soak_iterations)),
        '--postgres-ga-iterations',
        str(int(args.postgres_ga_iterations)),
        '--calibration-manifest',
        str(Path(args.calibration_manifest).resolve()),
        '--calibration-report-output',
        str(Path(args.calibration_report_output).resolve()),
        '--calibration-margin',
        str(float(args.calibration_margin)),
        '--beta-suite-output',
        str(Path(args.beta_suite_output).resolve()),
        '--ga-suite-output',
        str(Path(args.ga_suite_output).resolve()),
        '--roadmap-suite-output',
        str(Path(args.roadmap_suite_output).resolve()),
        '--output',
        str(Path(args.release_gate_output).resolve())
        if str(args.release_gate_output).strip() != '-'
        else '-',
    ]
    postgres_dsn = str(args.postgres_dsn or '').strip()
    if postgres_dsn:
        release_gate_command.extend(['--postgres-dsn', postgres_dsn])
    if args.no_coverage:
        release_gate_command.append('--no-coverage')
    if args.allow_regression:
        release_gate_command.append('--allow-regression')
    if args.container_skip_build:
        release_gate_command.append('--container-skip-build')
    if args.container_skip_run:
        release_gate_command.append('--container-skip-run')
    if args.allow_secondary_failures:
        release_gate_command.append('--allow-secondary-failures')
    if args.calibration_fail_on_mismatch:
        release_gate_command.append('--calibration-fail-on-mismatch')

    release_contract_command = [
        *python_cmd,
        'scripts/run_tp_tests.py',
        'TP-E9-03',
        'TP-E11-03',
        'TP-E13-03',
        '--python',
        str(args.python),
    ]
    doc_sync_command = [
        *python_cmd,
        'scripts/run_doc_sync_check.py',
        '--output',
        str(Path(args.doc_sync_report).resolve()),
    ]

    return {
        'release_gate': StageSpec(
            name='release_gate',
            description='Run release gate stage packs (beta + ga + roadmap).',
            command=release_gate_command,
        ),
        'release_contract': StageSpec(
            name='release_contract',
            description='Run TP release-switch contract checks (TP-E9-03/E11-03/E13-03).',
            command=release_contract_command,
        ),
        'doc_sync': StageSpec(
            name='doc_sync',
            description='Run docs contract checks for release-switch evidence surfaces.',
            command=doc_sync_command,
        ),
    }


def _build_plan(stage_specs: list[StageSpec]) -> dict[str, Any]:
    return {
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'stage_count': len(stage_specs),
        'stages': [
            {
                'name': stage.name,
                'description': stage.description,
                'command': stage.command,
            }
            for stage in stage_specs
        ],
    }


def _print_plan(stage_specs: list[StageSpec]) -> None:
    print('Selected stages: %s' % ', '.join(stage.name for stage in stage_specs))
    for stage in stage_specs:
        print('Stage: %s' % stage.name)
        print('Description: %s' % stage.description)
        print('Command: %s' % ' '.join(stage.command))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def _run_stages(stage_specs: list[StageSpec]) -> int:
    for stage in stage_specs:
        print('Running stage: %s' % stage.name)
        completed = subprocess.run(stage.command, check=False)
        if completed.returncode != 0:
            print(
                'Stage failed: %s (exit=%s)' % (stage.name, completed.returncode),
                file=sys.stderr,
            )
            return completed.returncode
    return 0


def _load_json_file(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not path.is_file():
        return None, 'missing'
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return None, 'invalid_json'
    if not isinstance(payload, dict):
        return None, 'invalid_root_type'
    return payload, None


def _read_text_file(path: Path) -> tuple[str | None, str | None]:
    if not path.is_file():
        return None, 'missing'
    try:
        return path.read_text(encoding='utf-8'), None
    except OSError:
        return None, 'read_error'


def _extract_doc_sync_release_check_status(doc_sync_report: dict[str, Any]) -> str:
    checks = doc_sync_report.get('checks')
    if not isinstance(checks, list):
        return 'unknown'
    for item in checks:
        if not isinstance(item, dict):
            continue
        if str(item.get('name')) != 'release_switch_standard_completeness':
            continue
        status = str(item.get('status', '')).strip().lower()
        if status == 'pass':
            return 'pass'
        if status == 'fail':
            return 'fail'
    return 'unknown'


def _plan_has_stage(plan_report: dict[str, Any], stage_name: str) -> bool:
    stages = plan_report.get('stages')
    if not isinstance(stages, list):
        return False
    for item in stages:
        if not isinstance(item, dict):
            continue
        if str(item.get('name', '')).strip() == stage_name:
            return True
    return False


def _plan_stage_has_command(plan_report: dict[str, Any], stage_name: str) -> bool:
    stages = plan_report.get('stages')
    if not isinstance(stages, list):
        return False
    for item in stages:
        if not isinstance(item, dict):
            continue
        if str(item.get('name', '')).strip() != stage_name:
            continue
        command = item.get('command')
        if not isinstance(command, list) or not command:
            return False
        for token in command:
            if not isinstance(token, str) or not token.strip():
                return False
        return True
    return False


def _plan_stage_count_matches(plan_report: dict[str, Any], expected_count: int) -> bool:
    value = plan_report.get('stage_count')
    try:
        return int(value) == int(expected_count)
    except (TypeError, ValueError):
        return False


def _plan_stage_pack_complete(plan_report: dict[str, Any], required_stages: tuple[str, ...]) -> bool:
    return _plan_stage_count_matches(plan_report, len(required_stages)) and all(
        _plan_has_stage(plan_report, stage_name) for stage_name in required_stages
    )


def _plan_stage_pack_executable(plan_report: dict[str, Any], required_stages: tuple[str, ...]) -> bool:
    return all(
        _plan_stage_has_command(plan_report, stage_name) for stage_name in required_stages
    )


def _normalize_cli_path(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    if not normalized or normalized == '-':
        return normalized
    return str(Path(normalized).resolve())


def _plan_stage_option_value(
    plan_report: dict[str, Any],
    stage_name: str,
    option_name: str,
) -> str | None:
    stages = plan_report.get('stages')
    if not isinstance(stages, list):
        return None
    for item in stages:
        if not isinstance(item, dict):
            continue
        if str(item.get('name', '')).strip() != stage_name:
            continue
        command = item.get('command')
        if not isinstance(command, list) or not command:
            return None
        for index, token in enumerate(command):
            if not isinstance(token, str):
                continue
            if token.strip() != option_name:
                continue
            if index + 1 >= len(command):
                return None
            raw_value = command[index + 1]
            if not isinstance(raw_value, str):
                return None
            return raw_value
        return None
    return None


def _plan_stage_command(plan_report: dict[str, Any], stage_name: str) -> list[str] | None:
    stages = plan_report.get('stages')
    if not isinstance(stages, list):
        return None
    for item in stages:
        if not isinstance(item, dict):
            continue
        if str(item.get('name', '')).strip() != stage_name:
            continue
        command = item.get('command')
        if not isinstance(command, list) or not command:
            return None
        if not all(isinstance(token, str) and token.strip() for token in command):
            return None
        return [str(token) for token in command]
    return None


def _command_contains_script_token(command: list[str], script_relpath: str) -> bool:
    expected = script_relpath.replace('\\', '/').lower()
    for token in command:
        normalized = str(token).strip().replace('\\', '/').lower()
        if normalized == expected or normalized.endswith('/' + expected):
            return True
    return False


def _command_script_token_index(command: list[str], script_relpath: str) -> int | None:
    expected = script_relpath.replace('\\', '/').lower()
    for index, token in enumerate(command):
        normalized = str(token).strip().replace('\\', '/').lower()
        if normalized == expected or normalized.endswith('/' + expected):
            return index
    return None


def _command_first_script_like_index(command: list[str]) -> int | None:
    for index, token in enumerate(command):
        stripped = str(token).strip()
        if not stripped or stripped.startswith('--'):
            continue
        normalized = stripped.replace('\\', '/').lower()
        if normalized.endswith('.py'):
            return index
    return None


def _resolve_command_script_token_path(token: str) -> Path | None:
    raw = str(token).strip()
    if not raw:
        return None
    candidate = Path(raw)
    try:
        if candidate.is_absolute():
            return candidate.resolve()
        return (REPO_ROOT / candidate).resolve()
    except (OSError, RuntimeError):
        return None


def _command_option_values(command: list[str], option_name: str) -> list[str] | None:
    for index, token in enumerate(command):
        if str(token).strip() != option_name:
            continue
        values: list[str] = []
        cursor = index + 1
        while cursor < len(command):
            value = command[cursor]
            if not isinstance(value, str):
                break
            stripped = value.strip()
            if not stripped:
                break
            if stripped.startswith('--'):
                break
            values.append(stripped)
            cursor += 1
        return values
    return None


def _command_option_occurrence_count(command: list[str], option_name: str) -> int:
    return sum(1 for token in command if str(token).strip() == option_name)


def _command_forbidden_inline_exec_flag(token: str) -> str | None:
    stripped = str(token).strip()
    if stripped in ('-c', '-m', '-'):
        return stripped
    if stripped.startswith('-c') and len(stripped) > 2:
        return '-c'
    if stripped.startswith('-m') and len(stripped) > 2:
        return '-m'
    return None


def _command_forbidden_python_optimization_flag(token: str) -> str | None:
    stripped = str(token).strip()
    if stripped in FORBIDDEN_PYTHON_OPTIMIZATION_FLAGS:
        return stripped
    if stripped.startswith('-O') and not stripped.startswith('--') and len(stripped) > 2:
        return '-O*'
    return None


def _command_forbidden_python_optimize_env_assignment(token: str) -> str | None:
    stripped = str(token).strip()
    if not stripped or stripped.startswith('--') or '=' not in stripped:
        return None
    env_key, _, env_value = stripped.partition('=')
    normalized_key = env_key.strip().upper()
    if normalized_key not in FORBIDDEN_PYTHON_OPTIMIZE_ENV_KEYS:
        return None
    return '%s=%s' % (env_key.strip(), env_value)


def _command_forbidden_python_path_env_assignment(token: str) -> str | None:
    stripped = str(token).strip()
    if not stripped or stripped.startswith('--') or '=' not in stripped:
        return None
    env_key, _, env_value = stripped.partition('=')
    normalized_key = env_key.strip().upper()
    if normalized_key not in FORBIDDEN_PYTHON_PATH_ENV_KEYS:
        return None
    return '%s=%s' % (env_key.strip(), env_value)


def _command_forbidden_python_home_env_assignment(token: str) -> str | None:
    stripped = str(token).strip()
    if not stripped or stripped.startswith('--') or '=' not in stripped:
        return None
    env_key, _, env_value = stripped.partition('=')
    normalized_key = env_key.strip().upper()
    if normalized_key not in FORBIDDEN_PYTHON_HOME_ENV_KEYS:
        return None
    return '%s=%s' % (env_key.strip(), env_value)


def _command_forbidden_python_user_base_env_assignment(token: str) -> str | None:
    stripped = str(token).strip()
    if not stripped or stripped.startswith('--') or '=' not in stripped:
        return None
    env_key, _, env_value = stripped.partition('=')
    normalized_key = env_key.strip().upper()
    if normalized_key not in FORBIDDEN_PYTHON_USER_BASE_ENV_KEYS:
        return None
    return '%s=%s' % (env_key.strip(), env_value)


def _command_forbidden_python_breakpoint_env_assignment(token: str) -> str | None:
    stripped = str(token).strip()
    if not stripped or stripped.startswith('--') or '=' not in stripped:
        return None
    env_key, _, env_value = stripped.partition('=')
    normalized_key = env_key.strip().upper()
    if normalized_key not in FORBIDDEN_PYTHON_BREAKPOINT_ENV_KEYS:
        return None
    return '%s=%s' % (env_key.strip(), env_value)


def _command_forbidden_python_startup_env_assignment(token: str) -> str | None:
    stripped = str(token).strip()
    if not stripped or stripped.startswith('--') or '=' not in stripped:
        return None
    env_key, _, env_value = stripped.partition('=')
    normalized_key = env_key.strip().upper()
    if normalized_key not in FORBIDDEN_PYTHON_STARTUP_ENV_KEYS:
        return None
    return '%s=%s' % (env_key.strip(), env_value)


def _command_forbidden_python_inspect_env_assignment(token: str) -> str | None:
    stripped = str(token).strip()
    if not stripped or stripped.startswith('--') or '=' not in stripped:
        return None
    env_key, _, env_value = stripped.partition('=')
    normalized_key = env_key.strip().upper()
    if normalized_key not in FORBIDDEN_PYTHON_INSPECT_ENV_KEYS:
        return None
    return '%s=%s' % (env_key.strip(), env_value)


def _command_forbidden_python_warnings_env_assignment(token: str) -> str | None:
    stripped = str(token).strip()
    if not stripped or stripped.startswith('--') or '=' not in stripped:
        return None
    env_key, _, env_value = stripped.partition('=')
    normalized_key = env_key.strip().upper()
    if normalized_key not in FORBIDDEN_PYTHON_WARNINGS_ENV_KEYS:
        return None
    return '%s=%s' % (env_key.strip(), env_value)


def _release_gate_stage_output_mismatches(
    release_gate_plan: dict[str, Any],
    expected_stage_outputs: dict[str, Path],
) -> list[dict[str, Any]]:
    mismatches: list[dict[str, Any]] = []
    for stage_name, expected_path in expected_stage_outputs.items():
        actual_output = _plan_stage_option_value(release_gate_plan, stage_name, '--output')
        normalized_actual = _normalize_cli_path(actual_output)
        normalized_expected = str(expected_path.resolve())
        if normalized_actual == normalized_expected:
            continue
        mismatches.append(
            {
                'stage': stage_name,
                'option': '--output',
                'expected': normalized_expected,
                'actual': normalized_actual,
            }
        )
    return mismatches


def _release_gate_option_override_mismatches(
    release_gate_plan: dict[str, Any],
) -> list[dict[str, Any]]:
    stage_names = ('beta_gate', 'ga_gate', 'roadmap_gate')
    mismatches: list[dict[str, Any]] = []
    for stage_name in stage_names:
        command = _plan_stage_command(release_gate_plan, stage_name)
        if command is None:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'command',
                    'expected': 'non-empty command',
                    'actual': None,
                }
            )
            continue
        for option_name in ('--stages', '--output'):
            occurrence_count = _command_option_occurrence_count(command, option_name)
            if occurrence_count == 1:
                continue
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': '%s-occurrence' % option_name,
                    'expected': 1,
                    'actual': occurrence_count,
                }
            )
    return mismatches


def _release_gate_relaxed_flag_mismatches(
    release_gate_plan: dict[str, Any],
) -> list[dict[str, Any]]:
    forbidden_flags: dict[str, tuple[str, ...]] = {
        'beta_gate': (
            '--allow-regression',
            '--no-coverage',
            '--container-skip-build',
            '--container-skip-run',
        ),
        'ga_gate': (
            '--allow-secondary-failures',
        ),
        'roadmap_gate': (),
    }
    mismatches: list[dict[str, Any]] = []
    for stage_name, stage_flags in forbidden_flags.items():
        if not stage_flags:
            continue
        command = _plan_stage_command(release_gate_plan, stage_name)
        if command is None:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'command',
                    'expected': 'non-empty command',
                    'actual': None,
                }
            )
            continue
        for option_name in stage_flags:
            occurrence_count = _command_option_occurrence_count(command, option_name)
            if occurrence_count == 0:
                continue
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'forbidden-flag',
                    'option': option_name,
                    'expected': 0,
                    'actual': occurrence_count,
                }
            )
    return mismatches


def _release_gate_dry_run_mismatches(
    release_gate_plan: dict[str, Any],
) -> list[dict[str, Any]]:
    stage_names = ('beta_gate', 'ga_gate', 'roadmap_gate')
    mismatches: list[dict[str, Any]] = []
    for stage_name in stage_names:
        command = _plan_stage_command(release_gate_plan, stage_name)
        if command is None:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'command',
                    'expected': 'non-empty command',
                    'actual': None,
                }
            )
            continue
        occurrence_count = _command_option_occurrence_count(command, '--dry-run')
        if occurrence_count == 0:
            continue
        mismatches.append(
            {
                'stage': stage_name,
                'check': 'forbidden-flag',
                'option': '--dry-run',
                'expected': 0,
                'actual': occurrence_count,
            }
        )
    return mismatches


def _release_gate_stage_contract_mismatches(
    release_gate_plan: dict[str, Any],
) -> list[dict[str, Any]]:
    expected: dict[str, tuple[str, ...]] = {
        'beta_gate': ('ci', 'container_smoke', 'doc_sync', 'quality_regression', 'perf_cost_baseline'),
        'ga_gate': (
            'postgres_soak',
            'postgres_ga',
            'worker_ga',
            'review_queue_ga',
            'provider_ga',
            'calibration_ga',
        ),
        'roadmap_gate': ('roadmap_extension',),
    }
    mismatches: list[dict[str, Any]] = []
    for stage_name, expected_stages in expected.items():
        command = _plan_stage_command(release_gate_plan, stage_name)
        if command is None:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'command',
                    'expected': 'non-empty command',
                    'actual': None,
                }
            )
            continue
        if not _command_contains_script_token(command, 'scripts/run_linux_validation_suite.py'):
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'script',
                    'expected': 'scripts/run_linux_validation_suite.py',
                    'actual': command,
                }
            )
        actual_stages = _command_option_values(command, '--stages')
        if tuple(actual_stages or ()) != expected_stages:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': '--stages',
                    'expected': list(expected_stages),
                    'actual': actual_stages,
                }
            )
    return mismatches


def _release_gate_script_position_mismatches(
    release_gate_plan: dict[str, Any],
) -> list[dict[str, Any]]:
    expected_script = 'scripts/run_linux_validation_suite.py'
    stage_names = ('beta_gate', 'ga_gate', 'roadmap_gate')
    mismatches: list[dict[str, Any]] = []
    for stage_name in stage_names:
        command = _plan_stage_command(release_gate_plan, stage_name)
        if command is None:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'command',
                    'expected': 'non-empty command',
                    'actual': None,
                }
            )
            continue
        expected_index = _command_script_token_index(command, expected_script)
        if expected_index is None:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'expected-script-token',
                    'expected': expected_script,
                    'actual': command,
                }
            )
            continue
        first_script_index = _command_first_script_like_index(command)
        if first_script_index is None:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'first-script-token',
                    'expected': expected_script,
                    'actual': None,
                }
            )
            continue
        if first_script_index != expected_index:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'script-position',
                    'expected': expected_script,
                    'actual': command[first_script_index],
                    'expected_index': expected_index,
                    'actual_index': first_script_index,
                }
            )
        first_option_index: int | None = None
        for index, token in enumerate(command):
            if str(token).strip().startswith('--'):
                first_option_index = index
                break
        if first_option_index is not None and expected_index > first_option_index:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'script-before-options',
                    'expected': '< option_index %s' % first_option_index,
                    'actual': expected_index,
                }
            )
    return mismatches


def _release_gate_inline_exec_mismatches(
    release_gate_plan: dict[str, Any],
) -> list[dict[str, Any]]:
    expected_script = 'scripts/run_linux_validation_suite.py'
    stage_names = ('beta_gate', 'ga_gate', 'roadmap_gate')
    mismatches: list[dict[str, Any]] = []
    for stage_name in stage_names:
        command = _plan_stage_command(release_gate_plan, stage_name)
        if command is None:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'command',
                    'expected': 'non-empty command',
                    'actual': None,
                }
            )
            continue
        expected_index = _command_script_token_index(command, expected_script)
        if expected_index is None:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'expected-script-token',
                    'expected': expected_script,
                    'actual': command,
                }
            )
            continue
        for index, token in enumerate(command[:expected_index]):
            forbidden_flag = _command_forbidden_inline_exec_flag(str(token))
            if forbidden_flag is None:
                continue
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'forbidden-inline-exec-flag',
                    'option': forbidden_flag,
                    'actual': str(token),
                    'index': index,
                }
            )
    return mismatches


def _release_gate_script_anchor_mismatches(
    release_gate_plan: dict[str, Any],
) -> list[dict[str, Any]]:
    expected_script = 'scripts/run_linux_validation_suite.py'
    expected_script_path = (REPO_ROOT / expected_script).resolve()
    expected_normalized_path = str(expected_script_path).replace('\\', '/').casefold()
    stage_names = ('beta_gate', 'ga_gate', 'roadmap_gate')
    mismatches: list[dict[str, Any]] = []
    for stage_name in stage_names:
        command = _plan_stage_command(release_gate_plan, stage_name)
        if command is None:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'command',
                    'expected': 'non-empty command',
                    'actual': None,
                }
            )
            continue
        first_script_index = _command_first_script_like_index(command)
        if first_script_index is None:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'first-script-token',
                    'expected': expected_script,
                    'actual': None,
                }
            )
            continue
        actual_token = str(command[first_script_index])
        actual_script_path = _resolve_command_script_token_path(actual_token)
        if actual_script_path is None:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'script-anchor',
                    'expected': str(expected_script_path),
                    'actual': None,
                    'actual_token': actual_token,
                    'actual_index': first_script_index,
                }
            )
            continue
        actual_normalized_path = str(actual_script_path).replace('\\', '/').casefold()
        if actual_normalized_path == expected_normalized_path:
            continue
        mismatches.append(
            {
                'stage': stage_name,
                'check': 'script-anchor',
                'expected': str(expected_script_path),
                'actual': str(actual_script_path),
                'actual_token': actual_token,
                'actual_index': first_script_index,
            }
        )
    return mismatches


def _release_gate_python_binding_mismatches(
    release_gate_plan: dict[str, Any],
    *,
    expected_python: str,
) -> list[dict[str, Any]]:
    expected_script = 'scripts/run_linux_validation_suite.py'
    expected_python_value = str(expected_python).strip()
    stage_names = ('beta_gate', 'ga_gate', 'roadmap_gate')
    mismatches: list[dict[str, Any]] = []
    for stage_name in stage_names:
        command = _plan_stage_command(release_gate_plan, stage_name)
        if command is None:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'command',
                    'expected': 'non-empty command',
                    'actual': None,
                }
            )
            continue
        script_index = _command_script_token_index(command, expected_script)
        if script_index is None:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'expected-script-token',
                    'expected': expected_script,
                    'actual': command,
                }
            )
            continue
        python_option_occurrence_count = _command_option_occurrence_count(command, '--python')
        if python_option_occurrence_count != 1:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': '--python-occurrence',
                    'expected': 1,
                    'actual': python_option_occurrence_count,
                }
            )
            continue
        python_values = _command_option_values(command, '--python') or []
        if len(python_values) != 1:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': '--python-value-shape',
                    'expected': 'single value',
                    'actual': python_values,
                }
            )
            continue
        actual_python_value = str(python_values[0]).strip()
        if actual_python_value != expected_python_value:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': '--python-value',
                    'expected': expected_python_value,
                    'actual': actual_python_value,
                }
            )
        launcher_tokens = [
            str(token).strip()
            for token in command[:script_index]
            if str(token).strip()
        ]
        launcher_value = ' '.join(launcher_tokens)
        if launcher_value != expected_python_value:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'python-launcher-binding',
                    'expected': expected_python_value,
                    'actual': launcher_value or None,
                }
            )
    return mismatches


def _release_gate_coverage_floor_mismatches(
    release_gate_plan: dict[str, Any],
    *,
    expected_coverage_fail_under: float,
    minimum_coverage_fail_under: float,
) -> list[dict[str, Any]]:
    stage_name = 'beta_gate'
    option_name = '--coverage-fail-under'
    expected_value = float(expected_coverage_fail_under)
    minimum_value = float(minimum_coverage_fail_under)
    mismatches: list[dict[str, Any]] = []
    command = _plan_stage_command(release_gate_plan, stage_name)
    if command is None:
        return [
            {
                'stage': stage_name,
                'check': 'command',
                'expected': 'non-empty command',
                'actual': None,
            }
        ]
    option_occurrence_count = _command_option_occurrence_count(command, option_name)
    if option_occurrence_count != 1:
        return [
            {
                'stage': stage_name,
                'check': '%s-occurrence' % option_name,
                'expected': 1,
                'actual': option_occurrence_count,
            }
        ]
    option_values = _command_option_values(command, option_name) or []
    if len(option_values) != 1:
        return [
            {
                'stage': stage_name,
                'check': '%s-value-shape' % option_name,
                'expected': 'single value',
                'actual': option_values,
            }
        ]
    raw_value = str(option_values[0]).strip()
    try:
        actual_value = float(raw_value)
    except ValueError:
        return [
            {
                'stage': stage_name,
                'check': '%s-value-parse' % option_name,
                'expected': 'float',
                'actual': raw_value or None,
            }
        ]
    if abs(actual_value - expected_value) > 1e-9:
        mismatches.append(
            {
                'stage': stage_name,
                'check': '%s-binding' % option_name,
                'expected': expected_value,
                'actual': actual_value,
            }
        )
    if actual_value < minimum_value:
        mismatches.append(
            {
                'stage': stage_name,
                'check': '%s-floor' % option_name,
                'expected': '>= %.3f' % minimum_value,
                'actual': actual_value,
            }
        )
    return mismatches


def _release_gate_python_optimization_mismatches(
    release_gate_plan: dict[str, Any],
) -> list[dict[str, Any]]:
    expected_script = 'scripts/run_linux_validation_suite.py'
    stage_names = ('beta_gate', 'ga_gate', 'roadmap_gate')
    mismatches: list[dict[str, Any]] = []
    for stage_name in stage_names:
        command = _plan_stage_command(release_gate_plan, stage_name)
        if command is None:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'command',
                    'expected': 'non-empty command',
                    'actual': None,
                }
            )
            continue
        script_index = _command_script_token_index(command, expected_script)
        if script_index is None:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'expected-script-token',
                    'expected': expected_script,
                    'actual': command,
                }
            )
            continue
        for index, token in enumerate(command[:script_index]):
            forbidden_flag = _command_forbidden_python_optimization_flag(str(token))
            if forbidden_flag is None:
                continue
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'forbidden-python-optimization-flag',
                    'option': forbidden_flag,
                    'actual': str(token),
                    'index': index,
                }
            )
    return mismatches


def _release_gate_python_option_optimization_mismatches(
    release_gate_plan: dict[str, Any],
) -> list[dict[str, Any]]:
    expected_script = 'scripts/run_linux_validation_suite.py'
    stage_names = ('beta_gate', 'ga_gate', 'roadmap_gate')
    mismatches: list[dict[str, Any]] = []
    for stage_name in stage_names:
        command = _plan_stage_command(release_gate_plan, stage_name)
        if command is None:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'command',
                    'expected': 'non-empty command',
                    'actual': None,
                }
            )
            continue
        script_index = _command_script_token_index(command, expected_script)
        if script_index is None:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'expected-script-token',
                    'expected': expected_script,
                    'actual': command,
                }
            )
            continue
        python_option_occurrence_count = _command_option_occurrence_count(command, '--python')
        if python_option_occurrence_count != 1:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': '--python-occurrence',
                    'expected': 1,
                    'actual': python_option_occurrence_count,
                }
            )
            continue
        python_values = _command_option_values(command, '--python') or []
        if len(python_values) != 1:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': '--python-value-shape',
                    'expected': 'single value',
                    'actual': python_values,
                }
            )
            continue
        raw_python_value = str(python_values[0]).strip()
        try:
            python_parts = _split_python_command(raw_python_value)
        except ValueError:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': '--python-value-parse',
                    'expected': 'non-empty python command',
                    'actual': raw_python_value or None,
                }
            )
            continue
        if len(python_parts) <= 1:
            continue
        for index, token in enumerate(python_parts[1:], start=1):
            forbidden_flag = _command_forbidden_python_optimization_flag(str(token))
            if forbidden_flag is None:
                continue
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'forbidden-python-option-optimization-flag',
                    'option': forbidden_flag,
                    'actual': str(token),
                    'python_option_value': raw_python_value,
                    'python_option_index': index,
                }
            )
    return mismatches


def _release_gate_python_optimize_env_mismatches(
    release_gate_plan: dict[str, Any],
) -> list[dict[str, Any]]:
    expected_script = 'scripts/run_linux_validation_suite.py'
    stage_names = ('beta_gate', 'ga_gate', 'roadmap_gate')
    mismatches: list[dict[str, Any]] = []
    for stage_name in stage_names:
        command = _plan_stage_command(release_gate_plan, stage_name)
        if command is None:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'command',
                    'expected': 'non-empty command',
                    'actual': None,
                }
            )
            continue
        script_index = _command_script_token_index(command, expected_script)
        if script_index is None:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'expected-script-token',
                    'expected': expected_script,
                    'actual': command,
                }
            )
            continue
        for index, token in enumerate(command[:script_index]):
            forbidden_assignment = _command_forbidden_python_optimize_env_assignment(str(token))
            if forbidden_assignment is None:
                continue
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'forbidden-python-optimize-env-assignment',
                    'scope': 'launcher',
                    'actual': forbidden_assignment,
                    'index': index,
                }
            )
        python_option_occurrence_count = _command_option_occurrence_count(command, '--python')
        if python_option_occurrence_count != 1:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': '--python-occurrence',
                    'expected': 1,
                    'actual': python_option_occurrence_count,
                }
            )
            continue
        python_values = _command_option_values(command, '--python') or []
        if len(python_values) != 1:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': '--python-value-shape',
                    'expected': 'single value',
                    'actual': python_values,
                }
            )
            continue
        raw_python_value = str(python_values[0]).strip()
        try:
            python_parts = _split_python_command(raw_python_value)
        except ValueError:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': '--python-value-parse',
                    'expected': 'non-empty python command',
                    'actual': raw_python_value or None,
                }
            )
            continue
        for index, token in enumerate(python_parts):
            forbidden_assignment = _command_forbidden_python_optimize_env_assignment(str(token))
            if forbidden_assignment is None:
                continue
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'forbidden-python-optimize-env-assignment',
                    'scope': '--python-value',
                    'actual': forbidden_assignment,
                    'python_option_value': raw_python_value,
                    'python_option_index': index,
                }
            )
    return mismatches


def _release_gate_python_option_inline_exec_mismatches(
    release_gate_plan: dict[str, Any],
) -> list[dict[str, Any]]:
    expected_script = 'scripts/run_linux_validation_suite.py'
    stage_names = ('beta_gate', 'ga_gate', 'roadmap_gate')
    mismatches: list[dict[str, Any]] = []
    for stage_name in stage_names:
        command = _plan_stage_command(release_gate_plan, stage_name)
        if command is None:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'command',
                    'expected': 'non-empty command',
                    'actual': None,
                }
            )
            continue
        script_index = _command_script_token_index(command, expected_script)
        if script_index is None:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'expected-script-token',
                    'expected': expected_script,
                    'actual': command,
                }
            )
            continue
        python_option_occurrence_count = _command_option_occurrence_count(command, '--python')
        if python_option_occurrence_count != 1:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': '--python-occurrence',
                    'expected': 1,
                    'actual': python_option_occurrence_count,
                }
            )
            continue
        python_values = _command_option_values(command, '--python') or []
        if len(python_values) != 1:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': '--python-value-shape',
                    'expected': 'single value',
                    'actual': python_values,
                }
            )
            continue
        raw_python_value = str(python_values[0]).strip()
        try:
            python_parts = _split_python_command(raw_python_value)
        except ValueError:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': '--python-value-parse',
                    'expected': 'non-empty python command',
                    'actual': raw_python_value or None,
                }
            )
            continue
        if len(python_parts) <= 1:
            continue
        for index, token in enumerate(python_parts[1:], start=1):
            forbidden_flag = _command_forbidden_inline_exec_flag(str(token))
            if forbidden_flag is None:
                continue
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'forbidden-python-option-inline-exec-flag',
                    'option': forbidden_flag,
                    'actual': str(token),
                    'python_option_value': raw_python_value,
                    'python_option_index': index,
                }
            )
    return mismatches


def _release_gate_python_path_env_mismatches(
    release_gate_plan: dict[str, Any],
) -> list[dict[str, Any]]:
    expected_script = 'scripts/run_linux_validation_suite.py'
    stage_names = ('beta_gate', 'ga_gate', 'roadmap_gate')
    mismatches: list[dict[str, Any]] = []
    for stage_name in stage_names:
        command = _plan_stage_command(release_gate_plan, stage_name)
        if command is None:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'command',
                    'expected': 'non-empty command',
                    'actual': None,
                }
            )
            continue
        script_index = _command_script_token_index(command, expected_script)
        if script_index is None:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'expected-script-token',
                    'expected': expected_script,
                    'actual': command,
                }
            )
            continue
        for index, token in enumerate(command[:script_index]):
            forbidden_assignment = _command_forbidden_python_path_env_assignment(str(token))
            if forbidden_assignment is None:
                continue
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'forbidden-python-path-env-assignment',
                    'scope': 'launcher',
                    'actual': forbidden_assignment,
                    'index': index,
                }
            )
        python_option_occurrence_count = _command_option_occurrence_count(command, '--python')
        if python_option_occurrence_count != 1:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': '--python-occurrence',
                    'expected': 1,
                    'actual': python_option_occurrence_count,
                }
            )
            continue
        python_values = _command_option_values(command, '--python') or []
        if len(python_values) != 1:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': '--python-value-shape',
                    'expected': 'single value',
                    'actual': python_values,
                }
            )
            continue
        raw_python_value = str(python_values[0]).strip()
        try:
            python_parts = _split_python_command(raw_python_value)
        except ValueError:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': '--python-value-parse',
                    'expected': 'non-empty python command',
                    'actual': raw_python_value or None,
                }
            )
            continue
        for index, token in enumerate(python_parts):
            forbidden_assignment = _command_forbidden_python_path_env_assignment(str(token))
            if forbidden_assignment is None:
                continue
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'forbidden-python-path-env-assignment',
                    'scope': '--python-value',
                    'actual': forbidden_assignment,
                    'python_option_value': raw_python_value,
                    'python_option_index': index,
                }
            )
    return mismatches


def _release_gate_python_home_env_mismatches(
    release_gate_plan: dict[str, Any],
) -> list[dict[str, Any]]:
    expected_script = 'scripts/run_linux_validation_suite.py'
    stage_names = ('beta_gate', 'ga_gate', 'roadmap_gate')
    mismatches: list[dict[str, Any]] = []
    for stage_name in stage_names:
        command = _plan_stage_command(release_gate_plan, stage_name)
        if command is None:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'command',
                    'expected': 'non-empty command',
                    'actual': None,
                }
            )
            continue
        script_index = _command_script_token_index(command, expected_script)
        if script_index is None:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'expected-script-token',
                    'expected': expected_script,
                    'actual': command,
                }
            )
            continue
        for index, token in enumerate(command[:script_index]):
            forbidden_assignment = _command_forbidden_python_home_env_assignment(str(token))
            if forbidden_assignment is None:
                continue
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'forbidden-python-home-env-assignment',
                    'scope': 'launcher',
                    'actual': forbidden_assignment,
                    'index': index,
                }
            )
        python_option_occurrence_count = _command_option_occurrence_count(command, '--python')
        if python_option_occurrence_count != 1:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': '--python-occurrence',
                    'expected': 1,
                    'actual': python_option_occurrence_count,
                }
            )
            continue
        python_values = _command_option_values(command, '--python') or []
        if len(python_values) != 1:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': '--python-value-shape',
                    'expected': 'single value',
                    'actual': python_values,
                }
            )
            continue
        raw_python_value = str(python_values[0]).strip()
        try:
            python_parts = _split_python_command(raw_python_value)
        except ValueError:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': '--python-value-parse',
                    'expected': 'non-empty python command',
                    'actual': raw_python_value or None,
                }
            )
            continue
        for index, token in enumerate(python_parts):
            forbidden_assignment = _command_forbidden_python_home_env_assignment(str(token))
            if forbidden_assignment is None:
                continue
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'forbidden-python-home-env-assignment',
                    'scope': '--python-value',
                    'actual': forbidden_assignment,
                    'python_option_value': raw_python_value,
                    'python_option_index': index,
                }
            )
    return mismatches


def _release_gate_python_user_base_env_mismatches(
    release_gate_plan: dict[str, Any],
) -> list[dict[str, Any]]:
    expected_script = 'scripts/run_linux_validation_suite.py'
    stage_names = ('beta_gate', 'ga_gate', 'roadmap_gate')
    mismatches: list[dict[str, Any]] = []
    for stage_name in stage_names:
        command = _plan_stage_command(release_gate_plan, stage_name)
        if command is None:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'command',
                    'expected': 'non-empty command',
                    'actual': None,
                }
            )
            continue
        script_index = _command_script_token_index(command, expected_script)
        if script_index is None:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'expected-script-token',
                    'expected': expected_script,
                    'actual': command,
                }
            )
            continue
        for index, token in enumerate(command[:script_index]):
            forbidden_assignment = _command_forbidden_python_user_base_env_assignment(str(token))
            if forbidden_assignment is None:
                continue
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'forbidden-python-user-base-env-assignment',
                    'scope': 'launcher',
                    'actual': forbidden_assignment,
                    'index': index,
                }
            )
        python_option_occurrence_count = _command_option_occurrence_count(command, '--python')
        if python_option_occurrence_count != 1:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': '--python-occurrence',
                    'expected': 1,
                    'actual': python_option_occurrence_count,
                }
            )
            continue
        python_values = _command_option_values(command, '--python') or []
        if len(python_values) != 1:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': '--python-value-shape',
                    'expected': 'single value',
                    'actual': python_values,
                }
            )
            continue
        raw_python_value = str(python_values[0]).strip()
        try:
            python_parts = _split_python_command(raw_python_value)
        except ValueError:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': '--python-value-parse',
                    'expected': 'non-empty python command',
                    'actual': raw_python_value or None,
                }
            )
            continue
        for index, token in enumerate(python_parts):
            forbidden_assignment = _command_forbidden_python_user_base_env_assignment(str(token))
            if forbidden_assignment is None:
                continue
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'forbidden-python-user-base-env-assignment',
                    'scope': '--python-value',
                    'actual': forbidden_assignment,
                    'python_option_value': raw_python_value,
                    'python_option_index': index,
                }
            )
    return mismatches


def _release_gate_python_breakpoint_env_mismatches(
    release_gate_plan: dict[str, Any],
) -> list[dict[str, Any]]:
    expected_script = 'scripts/run_linux_validation_suite.py'
    stage_names = ('beta_gate', 'ga_gate', 'roadmap_gate')
    mismatches: list[dict[str, Any]] = []
    for stage_name in stage_names:
        command = _plan_stage_command(release_gate_plan, stage_name)
        if command is None:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'command',
                    'expected': 'non-empty command',
                    'actual': None,
                }
            )
            continue
        script_index = _command_script_token_index(command, expected_script)
        if script_index is None:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'expected-script-token',
                    'expected': expected_script,
                    'actual': command,
                }
            )
            continue
        for index, token in enumerate(command[:script_index]):
            forbidden_assignment = _command_forbidden_python_breakpoint_env_assignment(str(token))
            if forbidden_assignment is None:
                continue
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'forbidden-python-breakpoint-env-assignment',
                    'scope': 'launcher',
                    'actual': forbidden_assignment,
                    'index': index,
                }
            )
        python_option_occurrence_count = _command_option_occurrence_count(command, '--python')
        if python_option_occurrence_count != 1:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': '--python-occurrence',
                    'expected': 1,
                    'actual': python_option_occurrence_count,
                }
            )
            continue
        python_values = _command_option_values(command, '--python') or []
        if len(python_values) != 1:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': '--python-value-shape',
                    'expected': 'single value',
                    'actual': python_values,
                }
            )
            continue
        raw_python_value = str(python_values[0]).strip()
        try:
            python_parts = _split_python_command(raw_python_value)
        except ValueError:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': '--python-value-parse',
                    'expected': 'non-empty python command',
                    'actual': raw_python_value or None,
                }
            )
            continue
        for index, token in enumerate(python_parts):
            forbidden_assignment = _command_forbidden_python_breakpoint_env_assignment(str(token))
            if forbidden_assignment is None:
                continue
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'forbidden-python-breakpoint-env-assignment',
                    'scope': '--python-value',
                    'actual': forbidden_assignment,
                    'python_option_value': raw_python_value,
                    'python_option_index': index,
                }
            )
    return mismatches


def _release_gate_python_startup_env_mismatches(
    release_gate_plan: dict[str, Any],
) -> list[dict[str, Any]]:
    expected_script = 'scripts/run_linux_validation_suite.py'
    stage_names = ('beta_gate', 'ga_gate', 'roadmap_gate')
    mismatches: list[dict[str, Any]] = []
    for stage_name in stage_names:
        command = _plan_stage_command(release_gate_plan, stage_name)
        if command is None:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'command',
                    'expected': 'non-empty command',
                    'actual': None,
                }
            )
            continue
        script_index = _command_script_token_index(command, expected_script)
        if script_index is None:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'expected-script-token',
                    'expected': expected_script,
                    'actual': command,
                }
            )
            continue
        for index, token in enumerate(command[:script_index]):
            forbidden_assignment = _command_forbidden_python_startup_env_assignment(str(token))
            if forbidden_assignment is None:
                continue
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'forbidden-python-startup-env-assignment',
                    'scope': 'launcher',
                    'actual': forbidden_assignment,
                    'index': index,
                }
            )
        python_option_occurrence_count = _command_option_occurrence_count(command, '--python')
        if python_option_occurrence_count != 1:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': '--python-occurrence',
                    'expected': 1,
                    'actual': python_option_occurrence_count,
                }
            )
            continue
        python_values = _command_option_values(command, '--python') or []
        if len(python_values) != 1:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': '--python-value-shape',
                    'expected': 'single value',
                    'actual': python_values,
                }
            )
            continue
        raw_python_value = str(python_values[0]).strip()
        try:
            python_parts = _split_python_command(raw_python_value)
        except ValueError:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': '--python-value-parse',
                    'expected': 'non-empty python command',
                    'actual': raw_python_value or None,
                }
            )
            continue
        for index, token in enumerate(python_parts):
            forbidden_assignment = _command_forbidden_python_startup_env_assignment(str(token))
            if forbidden_assignment is None:
                continue
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'forbidden-python-startup-env-assignment',
                    'scope': '--python-value',
                    'actual': forbidden_assignment,
                    'python_option_value': raw_python_value,
                    'python_option_index': index,
                }
            )
    return mismatches


def _release_gate_python_inspect_env_mismatches(
    release_gate_plan: dict[str, Any],
) -> list[dict[str, Any]]:
    expected_script = 'scripts/run_linux_validation_suite.py'
    stage_names = ('beta_gate', 'ga_gate', 'roadmap_gate')
    mismatches: list[dict[str, Any]] = []
    for stage_name in stage_names:
        command = _plan_stage_command(release_gate_plan, stage_name)
        if command is None:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'command',
                    'expected': 'non-empty command',
                    'actual': None,
                }
            )
            continue
        script_index = _command_script_token_index(command, expected_script)
        if script_index is None:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'expected-script-token',
                    'expected': expected_script,
                    'actual': command,
                }
            )
            continue
        for index, token in enumerate(command[:script_index]):
            forbidden_assignment = _command_forbidden_python_inspect_env_assignment(str(token))
            if forbidden_assignment is None:
                continue
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'forbidden-python-inspect-env-assignment',
                    'scope': 'launcher',
                    'actual': forbidden_assignment,
                    'index': index,
                }
            )
        python_option_occurrence_count = _command_option_occurrence_count(command, '--python')
        if python_option_occurrence_count != 1:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': '--python-occurrence',
                    'expected': 1,
                    'actual': python_option_occurrence_count,
                }
            )
            continue
        python_values = _command_option_values(command, '--python') or []
        if len(python_values) != 1:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': '--python-value-shape',
                    'expected': 'single value',
                    'actual': python_values,
                }
            )
            continue
        raw_python_value = str(python_values[0]).strip()
        try:
            python_parts = _split_python_command(raw_python_value)
        except ValueError:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': '--python-value-parse',
                    'expected': 'non-empty python command',
                    'actual': raw_python_value or None,
                }
            )
            continue
        for index, token in enumerate(python_parts):
            forbidden_assignment = _command_forbidden_python_inspect_env_assignment(str(token))
            if forbidden_assignment is None:
                continue
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'forbidden-python-inspect-env-assignment',
                    'scope': '--python-value',
                    'actual': forbidden_assignment,
                    'python_option_value': raw_python_value,
                    'python_option_index': index,
                }
            )
    return mismatches


def _release_gate_python_warnings_env_mismatches(
    release_gate_plan: dict[str, Any],
) -> list[dict[str, Any]]:
    expected_script = 'scripts/run_linux_validation_suite.py'
    stage_names = ('beta_gate', 'ga_gate', 'roadmap_gate')
    mismatches: list[dict[str, Any]] = []
    for stage_name in stage_names:
        command = _plan_stage_command(release_gate_plan, stage_name)
        if command is None:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'command',
                    'expected': 'non-empty command',
                    'actual': None,
                }
            )
            continue
        script_index = _command_script_token_index(command, expected_script)
        if script_index is None:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'expected-script-token',
                    'expected': expected_script,
                    'actual': command,
                }
            )
            continue
        for index, token in enumerate(command[:script_index]):
            forbidden_assignment = _command_forbidden_python_warnings_env_assignment(str(token))
            if forbidden_assignment is None:
                continue
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'forbidden-python-warnings-env-assignment',
                    'scope': 'launcher',
                    'actual': forbidden_assignment,
                    'index': index,
                }
            )
        python_option_occurrence_count = _command_option_occurrence_count(command, '--python')
        if python_option_occurrence_count != 1:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': '--python-occurrence',
                    'expected': 1,
                    'actual': python_option_occurrence_count,
                }
            )
            continue
        python_values = _command_option_values(command, '--python') or []
        if len(python_values) != 1:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': '--python-value-shape',
                    'expected': 'single value',
                    'actual': python_values,
                }
            )
            continue
        raw_python_value = str(python_values[0]).strip()
        try:
            python_parts = _split_python_command(raw_python_value)
        except ValueError:
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': '--python-value-parse',
                    'expected': 'non-empty python command',
                    'actual': raw_python_value or None,
                }
            )
            continue
        for index, token in enumerate(python_parts):
            forbidden_assignment = _command_forbidden_python_warnings_env_assignment(str(token))
            if forbidden_assignment is None:
                continue
            mismatches.append(
                {
                    'stage': stage_name,
                    'check': 'forbidden-python-warnings-env-assignment',
                    'scope': '--python-value',
                    'actual': forbidden_assignment,
                    'python_option_value': raw_python_value,
                    'python_option_index': index,
                }
            )
    return mismatches


def _resolve_file_age_delta_hours(path: Path) -> float | None:
    try:
        modified_at = float(path.stat().st_mtime)
    except (OSError, ValueError):
        return None
    now_ts = datetime.now(timezone.utc).timestamp()
    age_seconds = now_ts - modified_at
    return age_seconds / 3600.0


def _evaluate_decision(args: argparse.Namespace) -> dict[str, Any]:
    doc_sync_path = Path(args.doc_sync_report).resolve()
    quality_path = Path(args.quality_report).resolve()
    perf_path = Path(args.perf_report).resolve()
    postgres_soak_benchmark_path = Path(args.postgres_soak_benchmark_report).resolve()
    beta_suite_path = Path(args.beta_suite_output).resolve()
    ga_suite_path = Path(args.ga_suite_output).resolve()
    roadmap_suite_path = Path(args.roadmap_suite_output).resolve()
    release_gate_path = Path(args.release_gate_output).resolve()
    release_standard_path = Path(args.release_standard_doc).resolve()
    max_evidence_age_hours = float(args.max_evidence_age_hours)
    max_evidence_future_skew_hours = float(args.max_evidence_future_skew_hours)
    max_evidence_cohort_skew_hours = float(args.max_evidence_cohort_skew_hours)
    release_gate_binding_check_enabled = not bool(args.skip_release_gate_output_binding_check)
    release_gate_stage_contract_check_enabled = not bool(args.skip_release_gate_stage_contract_check)
    release_gate_script_position_check_enabled = not bool(
        args.skip_release_gate_script_position_check
    )
    release_gate_script_anchor_check_enabled = not bool(
        args.skip_release_gate_script_anchor_check
    )
    release_gate_python_binding_check_enabled = not bool(
        args.skip_release_gate_python_binding_check
    )
    release_gate_python_optimization_check_enabled = not bool(
        args.skip_release_gate_python_optimization_check
    )
    release_gate_python_option_optimization_check_enabled = not bool(
        args.skip_release_gate_python_option_optimization_check
    )
    release_gate_python_optimize_env_check_enabled = not bool(
        args.skip_release_gate_python_optimize_env_check
    )
    release_gate_python_path_env_check_enabled = not bool(
        args.skip_release_gate_python_path_env_check
    )
    release_gate_python_home_env_check_enabled = not bool(
        args.skip_release_gate_python_home_env_check
    )
    release_gate_python_user_base_env_check_enabled = not bool(
        args.skip_release_gate_python_user_base_env_check
    )
    release_gate_python_breakpoint_env_check_enabled = not bool(
        args.skip_release_gate_python_breakpoint_env_check
    )
    release_gate_python_startup_env_check_enabled = not bool(
        args.skip_release_gate_python_startup_env_check
    )
    release_gate_python_inspect_env_check_enabled = not bool(
        args.skip_release_gate_python_inspect_env_check
    )
    release_gate_python_warnings_env_check_enabled = not bool(
        args.skip_release_gate_python_warnings_env_check
    )
    release_gate_python_option_inline_exec_check_enabled = not bool(
        args.skip_release_gate_python_option_inline_exec_check
    )
    release_gate_coverage_floor_check_enabled = not bool(
        args.skip_release_gate_coverage_floor_check
    )
    release_gate_inline_exec_check_enabled = not bool(
        args.skip_release_gate_inline_exec_check
    )
    release_gate_option_override_check_enabled = not bool(
        args.skip_release_gate_option_override_check
    )
    release_gate_dry_run_check_enabled = not bool(
        args.skip_release_gate_dry_run_check
    )
    release_gate_relaxed_flags_check_enabled = not bool(
        args.skip_release_gate_relaxed_flags_check
    )
    freshness_check_enabled = max_evidence_age_hours > 0
    future_skew_check_enabled = max_evidence_future_skew_hours > 0
    cohort_skew_check_enabled = max_evidence_cohort_skew_hours > 0

    doc_sync_report, doc_sync_error = _load_json_file(doc_sync_path)
    quality_report, quality_error = _load_json_file(quality_path)
    perf_report, perf_error = _load_json_file(perf_path)
    postgres_soak_report, postgres_soak_error = _load_json_file(postgres_soak_benchmark_path)
    beta_suite_report, beta_suite_error = _load_json_file(beta_suite_path)
    ga_suite_report, ga_suite_error = _load_json_file(ga_suite_path)
    roadmap_suite_report, roadmap_suite_error = _load_json_file(roadmap_suite_path)
    release_gate_report, release_gate_error = _load_json_file(release_gate_path)
    release_standard_text, release_standard_error = _read_text_file(release_standard_path)

    doc_sync_pass = bool(
        doc_sync_report is not None
        and str(doc_sync_report.get('status', '')).lower() == 'pass'
        and int(doc_sync_report.get('failed_count', 1)) == 0
    )
    release_contract_check = (
        _extract_doc_sync_release_check_status(doc_sync_report) if doc_sync_report is not None else 'unknown'
    )
    standard_markers: dict[str, bool] = {}
    if release_standard_text is not None:
        standard_markers = {
            marker: marker in release_standard_text
            for marker in RELEASE_GATE_MARKERS
        }

    quality_regressed_count = None
    if quality_report is not None:
        try:
            quality_regressed_count = int(quality_report.get('regressed_count', 0))
        except (TypeError, ValueError):
            quality_regressed_count = None

    perf_regressed_count = None
    if perf_report is not None:
        try:
            perf_regressed_count = int(perf_report.get('regressed_count', 0))
        except (TypeError, ValueError):
            perf_regressed_count = None

    postgres_run_enabled = bool(
        postgres_soak_report is not None and postgres_soak_report.get('run_postgres') is True
    )
    dual_write_count = 0
    if postgres_soak_report is not None:
        runs = postgres_soak_report.get('runs')
        if isinstance(runs, dict):
            dual_write = runs.get('dual_write')
            if isinstance(dual_write, dict):
                summary = dual_write.get('summary')
                if isinstance(summary, dict):
                    try:
                        dual_write_count = int(summary.get('count', 0))
                    except (TypeError, ValueError):
                        dual_write_count = 0

    beta_required_stages = ('ci', 'container_smoke', 'doc_sync', 'quality_regression', 'perf_cost_baseline')
    ga_required_stages = (
        'postgres_soak',
        'postgres_ga',
        'worker_ga',
        'review_queue_ga',
        'provider_ga',
        'calibration_ga',
    )
    roadmap_required_stages = ('roadmap_extension',)
    release_gate_required_stages = ('beta_gate', 'ga_gate', 'roadmap_gate')

    beta_suite_stage_pack_complete = bool(
        beta_suite_report is not None and _plan_stage_pack_complete(beta_suite_report, beta_required_stages)
    )
    beta_suite_stage_pack_executable = bool(
        beta_suite_report is not None and _plan_stage_pack_executable(beta_suite_report, beta_required_stages)
    )
    ga_suite_stage_pack_complete = bool(
        ga_suite_report is not None and _plan_stage_pack_complete(ga_suite_report, ga_required_stages)
    )
    ga_suite_stage_pack_executable = bool(
        ga_suite_report is not None and _plan_stage_pack_executable(ga_suite_report, ga_required_stages)
    )
    roadmap_suite_stage_pack_complete = bool(
        roadmap_suite_report is not None
        and _plan_stage_pack_complete(roadmap_suite_report, roadmap_required_stages)
    )
    roadmap_suite_stage_pack_executable = bool(
        roadmap_suite_report is not None
        and _plan_stage_pack_executable(roadmap_suite_report, roadmap_required_stages)
    )
    release_gate_stage_pack_complete = bool(
        release_gate_report is not None
        and _plan_stage_pack_complete(release_gate_report, release_gate_required_stages)
    )
    release_gate_stage_pack_executable = bool(
        release_gate_report is not None
        and _plan_stage_pack_executable(release_gate_report, release_gate_required_stages)
    )
    release_gate_binding_mismatches: list[dict[str, Any]] = []
    if release_gate_binding_check_enabled and release_gate_report is not None:
        release_gate_binding_mismatches = _release_gate_stage_output_mismatches(
            release_gate_report,
            {
                'beta_gate': beta_suite_path,
                'ga_gate': ga_suite_path,
                'roadmap_gate': roadmap_suite_path,
            },
        )
    release_gate_output_binding_pass = (
        (not release_gate_binding_check_enabled) or (not release_gate_binding_mismatches)
    )
    release_gate_stage_contract_mismatches: list[dict[str, Any]] = []
    if release_gate_stage_contract_check_enabled and release_gate_report is not None:
        release_gate_stage_contract_mismatches = _release_gate_stage_contract_mismatches(
            release_gate_report
        )
    release_gate_stage_contract_pass = (
        (not release_gate_stage_contract_check_enabled) or (not release_gate_stage_contract_mismatches)
    )
    release_gate_script_position_mismatches: list[dict[str, Any]] = []
    if release_gate_script_position_check_enabled and release_gate_report is not None:
        release_gate_script_position_mismatches = _release_gate_script_position_mismatches(
            release_gate_report
        )
    release_gate_script_position_pass = (
        (not release_gate_script_position_check_enabled)
        or (not release_gate_script_position_mismatches)
    )
    release_gate_script_anchor_mismatches: list[dict[str, Any]] = []
    if release_gate_script_anchor_check_enabled and release_gate_report is not None:
        release_gate_script_anchor_mismatches = _release_gate_script_anchor_mismatches(
            release_gate_report
        )
    release_gate_script_anchor_pass = (
        (not release_gate_script_anchor_check_enabled)
        or (not release_gate_script_anchor_mismatches)
    )
    release_gate_python_binding_mismatches: list[dict[str, Any]] = []
    if release_gate_python_binding_check_enabled and release_gate_report is not None:
        release_gate_python_binding_mismatches = _release_gate_python_binding_mismatches(
            release_gate_report,
            expected_python=str(args.python),
        )
    release_gate_python_binding_pass = (
        (not release_gate_python_binding_check_enabled)
        or (not release_gate_python_binding_mismatches)
    )
    release_gate_python_optimization_mismatches: list[dict[str, Any]] = []
    if release_gate_python_optimization_check_enabled and release_gate_report is not None:
        release_gate_python_optimization_mismatches = _release_gate_python_optimization_mismatches(
            release_gate_report
        )
    release_gate_python_optimization_pass = (
        (not release_gate_python_optimization_check_enabled)
        or (not release_gate_python_optimization_mismatches)
    )
    release_gate_python_option_optimization_mismatches: list[dict[str, Any]] = []
    if release_gate_python_option_optimization_check_enabled and release_gate_report is not None:
        release_gate_python_option_optimization_mismatches = (
            _release_gate_python_option_optimization_mismatches(
                release_gate_report
            )
        )
    release_gate_python_option_optimization_pass = (
        (not release_gate_python_option_optimization_check_enabled)
        or (not release_gate_python_option_optimization_mismatches)
    )
    release_gate_python_optimize_env_mismatches: list[dict[str, Any]] = []
    if release_gate_python_optimize_env_check_enabled and release_gate_report is not None:
        release_gate_python_optimize_env_mismatches = (
            _release_gate_python_optimize_env_mismatches(
                release_gate_report
            )
        )
    release_gate_python_optimize_env_pass = (
        (not release_gate_python_optimize_env_check_enabled)
        or (not release_gate_python_optimize_env_mismatches)
    )
    release_gate_python_path_env_mismatches: list[dict[str, Any]] = []
    if release_gate_python_path_env_check_enabled and release_gate_report is not None:
        release_gate_python_path_env_mismatches = _release_gate_python_path_env_mismatches(
            release_gate_report
        )
    release_gate_python_path_env_pass = (
        (not release_gate_python_path_env_check_enabled)
        or (not release_gate_python_path_env_mismatches)
    )
    release_gate_python_home_env_mismatches: list[dict[str, Any]] = []
    if release_gate_python_home_env_check_enabled and release_gate_report is not None:
        release_gate_python_home_env_mismatches = _release_gate_python_home_env_mismatches(
            release_gate_report
        )
    release_gate_python_home_env_pass = (
        (not release_gate_python_home_env_check_enabled)
        or (not release_gate_python_home_env_mismatches)
    )
    release_gate_python_user_base_env_mismatches: list[dict[str, Any]] = []
    if release_gate_python_user_base_env_check_enabled and release_gate_report is not None:
        release_gate_python_user_base_env_mismatches = (
            _release_gate_python_user_base_env_mismatches(release_gate_report)
        )
    release_gate_python_user_base_env_pass = (
        (not release_gate_python_user_base_env_check_enabled)
        or (not release_gate_python_user_base_env_mismatches)
    )
    release_gate_python_breakpoint_env_mismatches: list[dict[str, Any]] = []
    if release_gate_python_breakpoint_env_check_enabled and release_gate_report is not None:
        release_gate_python_breakpoint_env_mismatches = (
            _release_gate_python_breakpoint_env_mismatches(release_gate_report)
        )
    release_gate_python_breakpoint_env_pass = (
        (not release_gate_python_breakpoint_env_check_enabled)
        or (not release_gate_python_breakpoint_env_mismatches)
    )
    release_gate_python_startup_env_mismatches: list[dict[str, Any]] = []
    if release_gate_python_startup_env_check_enabled and release_gate_report is not None:
        release_gate_python_startup_env_mismatches = (
            _release_gate_python_startup_env_mismatches(release_gate_report)
        )
    release_gate_python_startup_env_pass = (
        (not release_gate_python_startup_env_check_enabled)
        or (not release_gate_python_startup_env_mismatches)
    )
    release_gate_python_inspect_env_mismatches: list[dict[str, Any]] = []
    if release_gate_python_inspect_env_check_enabled and release_gate_report is not None:
        release_gate_python_inspect_env_mismatches = (
            _release_gate_python_inspect_env_mismatches(release_gate_report)
        )
    release_gate_python_inspect_env_pass = (
        (not release_gate_python_inspect_env_check_enabled)
        or (not release_gate_python_inspect_env_mismatches)
    )
    release_gate_python_warnings_env_mismatches: list[dict[str, Any]] = []
    if release_gate_python_warnings_env_check_enabled and release_gate_report is not None:
        release_gate_python_warnings_env_mismatches = (
            _release_gate_python_warnings_env_mismatches(release_gate_report)
        )
    release_gate_python_warnings_env_pass = (
        (not release_gate_python_warnings_env_check_enabled)
        or (not release_gate_python_warnings_env_mismatches)
    )
    release_gate_python_option_inline_exec_mismatches: list[dict[str, Any]] = []
    if (
        release_gate_python_option_inline_exec_check_enabled
        and release_gate_report is not None
    ):
        release_gate_python_option_inline_exec_mismatches = (
            _release_gate_python_option_inline_exec_mismatches(release_gate_report)
        )
    release_gate_python_option_inline_exec_pass = (
        (not release_gate_python_option_inline_exec_check_enabled)
        or (not release_gate_python_option_inline_exec_mismatches)
    )
    release_gate_coverage_floor_mismatches: list[dict[str, Any]] = []
    if release_gate_coverage_floor_check_enabled and release_gate_report is not None:
        release_gate_coverage_floor_mismatches = _release_gate_coverage_floor_mismatches(
            release_gate_report,
            expected_coverage_fail_under=float(args.coverage_fail_under),
            minimum_coverage_fail_under=DEFAULT_RELEASE_GATE_COVERAGE_FLOOR,
        )
    release_gate_coverage_floor_pass = (
        (not release_gate_coverage_floor_check_enabled)
        or (not release_gate_coverage_floor_mismatches)
    )
    release_gate_inline_exec_mismatches: list[dict[str, Any]] = []
    if release_gate_inline_exec_check_enabled and release_gate_report is not None:
        release_gate_inline_exec_mismatches = _release_gate_inline_exec_mismatches(
            release_gate_report
        )
    release_gate_inline_exec_pass = (
        (not release_gate_inline_exec_check_enabled)
        or (not release_gate_inline_exec_mismatches)
    )
    release_gate_option_override_mismatches: list[dict[str, Any]] = []
    if release_gate_option_override_check_enabled and release_gate_report is not None:
        release_gate_option_override_mismatches = _release_gate_option_override_mismatches(
            release_gate_report
        )
    release_gate_option_override_pass = (
        (not release_gate_option_override_check_enabled) or (not release_gate_option_override_mismatches)
    )
    release_gate_dry_run_mismatches: list[dict[str, Any]] = []
    if release_gate_dry_run_check_enabled and release_gate_report is not None:
        release_gate_dry_run_mismatches = _release_gate_dry_run_mismatches(
            release_gate_report
        )
    release_gate_dry_run_pass = (
        (not release_gate_dry_run_check_enabled) or (not release_gate_dry_run_mismatches)
    )
    release_gate_relaxed_flag_mismatches: list[dict[str, Any]] = []
    if release_gate_relaxed_flags_check_enabled and release_gate_report is not None:
        release_gate_relaxed_flag_mismatches = _release_gate_relaxed_flag_mismatches(
            release_gate_report
        )
    release_gate_relaxed_flags_pass = (
        (not release_gate_relaxed_flags_check_enabled) or (not release_gate_relaxed_flag_mismatches)
    )
    beta_suite_evidence_pack_complete = beta_suite_stage_pack_complete and beta_suite_stage_pack_executable
    ga_suite_evidence_pack_complete = ga_suite_stage_pack_complete and ga_suite_stage_pack_executable
    roadmap_suite_evidence_pack_complete = roadmap_suite_stage_pack_complete and roadmap_suite_stage_pack_executable
    release_gate_evidence_pack_complete = (
        release_gate_stage_pack_complete
        and release_gate_stage_pack_executable
        and release_gate_output_binding_pass
        and release_gate_stage_contract_pass
        and release_gate_script_position_pass
        and release_gate_script_anchor_pass
        and release_gate_python_binding_pass
        and release_gate_python_optimization_pass
        and release_gate_python_option_optimization_pass
        and release_gate_python_optimize_env_pass
        and release_gate_python_path_env_pass
        and release_gate_python_home_env_pass
        and release_gate_python_user_base_env_pass
        and release_gate_python_breakpoint_env_pass
        and release_gate_python_startup_env_pass
        and release_gate_python_inspect_env_pass
        and release_gate_python_option_inline_exec_pass
        and release_gate_coverage_floor_pass
        and release_gate_inline_exec_pass
        and release_gate_option_override_pass
        and release_gate_dry_run_pass
        and release_gate_relaxed_flags_pass
    )
    review_queue_stage_present = bool(
        ga_suite_report is not None
        and _plan_has_stage(ga_suite_report, 'review_queue_ga')
        and _plan_stage_has_command(ga_suite_report, 'review_queue_ga')
    )
    freshness_target_paths = (
        doc_sync_path,
        quality_path,
        perf_path,
        postgres_soak_benchmark_path,
        beta_suite_path,
        ga_suite_path,
        roadmap_suite_path,
        release_gate_path,
    )
    evidence_age_hours: dict[str, float] = {}
    evidence_age_hours_raw: dict[str, float] = {}
    stale_evidence_files: list[str] = []
    future_evidence_files: list[str] = []
    for target_path in freshness_target_paths:
        age_hours = _resolve_file_age_delta_hours(target_path)
        if age_hours is None:
            continue
        normalized_age_hours = round(age_hours, 3)
        evidence_age_hours_raw[str(target_path)] = age_hours
        evidence_age_hours[str(target_path)] = normalized_age_hours
        if freshness_check_enabled and age_hours > max_evidence_age_hours:
            stale_evidence_files.append(str(target_path))
        if future_skew_check_enabled and age_hours < (0.0 - max_evidence_future_skew_hours):
            future_evidence_files.append(str(target_path))
    stale_evidence_files = sorted(set(stale_evidence_files))
    future_evidence_files = sorted(set(future_evidence_files))
    stale_evidence_file_set = set(stale_evidence_files)
    future_evidence_file_set = set(future_evidence_files)
    evidence_freshness_gate_pass = (
        ((not freshness_check_enabled) or (not stale_evidence_files))
        and ((not future_skew_check_enabled) or (not future_evidence_files))
    )
    oldest_evidence_file = ''
    newest_evidence_file = ''
    evidence_cohort_age_spread_hours: float | None = None
    cohort_skew_violation_files: list[str] = []
    if evidence_age_hours_raw:
        oldest_evidence_file = max(evidence_age_hours_raw, key=evidence_age_hours_raw.__getitem__)
        newest_evidence_file = min(evidence_age_hours_raw, key=evidence_age_hours_raw.__getitem__)
    if len(evidence_age_hours_raw) >= 2:
        oldest_age_hours = evidence_age_hours_raw[oldest_evidence_file]
        newest_age_hours = evidence_age_hours_raw[newest_evidence_file]
        evidence_cohort_age_spread_hours = round(oldest_age_hours - newest_age_hours, 3)
        if cohort_skew_check_enabled and (oldest_age_hours - newest_age_hours) > max_evidence_cohort_skew_hours:
            cohort_skew_violation_files = sorted({oldest_evidence_file, newest_evidence_file})
    cohort_skew_gate_pass = (
        (not cohort_skew_check_enabled)
        or len(evidence_age_hours_raw) <= 1
        or (
            evidence_cohort_age_spread_hours is not None
            and evidence_cohort_age_spread_hours <= max_evidence_cohort_skew_hours
        )
    )

    gate_graph_source = (
        doc_sync_pass
        and release_contract_check == 'pass'
        and release_gate_evidence_pack_complete
        and beta_suite_evidence_pack_complete
        and standard_markers.get('graph_is_source_of_truth', False)
    )
    gate_review_queue = (
        review_queue_stage_present
        and release_gate_evidence_pack_complete
        and ga_suite_evidence_pack_complete
        and standard_markers.get('review_queue_operational', False)
    )
    gate_publication_views = (
        doc_sync_pass
        and release_contract_check == 'pass'
        and release_gate_evidence_pack_complete
        and roadmap_suite_evidence_pack_complete
        and standard_markers.get('publication_view_count>=2', False)
    )
    gate_postgres = (
        postgres_run_enabled
        and dual_write_count > 0
        and release_gate_evidence_pack_complete
        and ga_suite_evidence_pack_complete
        and standard_markers.get('postgres_repository_stable', False)
    )
    gate_regression = (
        quality_regressed_count == 0
        and perf_regressed_count == 0
        and release_gate_evidence_pack_complete
        and beta_suite_evidence_pack_complete
        and standard_markers.get('regression_beats_v1', False)
    )

    gates = [
        {
            'name': 'evidence_freshness',
            'status': 'pass' if evidence_freshness_gate_pass else 'hold',
            'reason': (
                'all decision evidence files are within freshness threshold (hours <= %.3f) and future-skew threshold (hours <= %.3f)'
                % (max_evidence_age_hours, max_evidence_future_skew_hours)
                if evidence_freshness_gate_pass and freshness_check_enabled and future_skew_check_enabled
                else (
                    'all decision evidence files are within freshness threshold (hours <= %.3f); future-skew gate disabled (--max-evidence-future-skew-hours <= 0)'
                    % max_evidence_age_hours
                    if evidence_freshness_gate_pass and freshness_check_enabled and not future_skew_check_enabled
                    else (
                        'freshness check disabled (--max-evidence-age-hours <= 0) and future-skew gate disabled (--max-evidence-future-skew-hours <= 0)'
                        if evidence_freshness_gate_pass
                        and not freshness_check_enabled
                        and not future_skew_check_enabled
                        else (
                            'freshness check disabled (--max-evidence-age-hours <= 0); future-skew threshold enforced (hours <= %.3f)'
                            % max_evidence_future_skew_hours
                            if evidence_freshness_gate_pass and not freshness_check_enabled and future_skew_check_enabled
                            else 'decision evidence violates freshness/future-skew thresholds'
                        )
                    )
                )
            ),
            'evidence': (
                sorted(set(stale_evidence_files + future_evidence_files))
                if (stale_evidence_files or future_evidence_files)
                else (
                    [str(path) for path in freshness_target_paths]
                )
            ),
        },
        {
            'name': 'evidence_cohort_skew',
            'status': 'pass' if cohort_skew_gate_pass else 'hold',
            'reason': (
                'decision evidence timestamps stay within cohort skew threshold (hours <= %.3f)'
                % max_evidence_cohort_skew_hours
                if cohort_skew_gate_pass and cohort_skew_check_enabled and len(evidence_age_hours_raw) >= 2
                else (
                    'cohort skew check disabled (--max-evidence-cohort-skew-hours <= 0)'
                    if cohort_skew_gate_pass and not cohort_skew_check_enabled
                    else (
                        'cohort skew check skipped (fewer than two evidence files with readable timestamps)'
                        if cohort_skew_gate_pass
                        else 'decision evidence timestamps exceed cohort skew threshold (hours > %.3f)'
                        % max_evidence_cohort_skew_hours
                    )
                )
            ),
            'evidence': (
                cohort_skew_violation_files
                if cohort_skew_violation_files
                else (
                    [str(path) for path in freshness_target_paths]
                )
            ),
        },
        {
            'name': 'release_gate_evidence_binding',
            'status': 'pass' if release_gate_output_binding_pass else 'hold',
            'reason': (
                'release-gate beta/ga/roadmap stage outputs are bound to the provided nested evidence paths'
                if release_gate_output_binding_pass and release_gate_binding_check_enabled
                else (
                    'release-gate output binding gate disabled (--skip-release-gate-output-binding-check)'
                    if release_gate_output_binding_pass
                    else 'release-gate stage output paths do not match provided nested evidence paths'
                )
            ),
            'evidence': (
                [
                    str(release_gate_path),
                    str(beta_suite_path),
                    str(ga_suite_path),
                    str(roadmap_suite_path),
                ]
                if not release_gate_binding_mismatches
                else release_gate_binding_mismatches
            ),
        },
        {
            'name': 'release_gate_stage_contract',
            'status': 'pass' if release_gate_stage_contract_pass else 'hold',
            'reason': (
                'release-gate stage commands target scripts/run_linux_validation_suite.py and expected --stages packs'
                if release_gate_stage_contract_pass and release_gate_stage_contract_check_enabled
                else (
                    'release-gate stage contract gate disabled (--skip-release-gate-stage-contract-check)'
                    if release_gate_stage_contract_pass
                    else 'release-gate stage command contract does not match expected linux suite stage packs'
                )
            ),
            'evidence': (
                [str(release_gate_path)]
                if not release_gate_stage_contract_mismatches
                else release_gate_stage_contract_mismatches
            ),
        },
        {
            'name': 'release_gate_script_position',
            'status': 'pass' if release_gate_script_position_pass else 'hold',
            'reason': (
                'release-gate stage commands execute scripts/run_linux_validation_suite.py as the first script token'
                if release_gate_script_position_pass and release_gate_script_position_check_enabled
                else (
                    'release-gate script-position gate disabled (--skip-release-gate-script-position-check)'
                    if release_gate_script_position_pass
                    else 'release-gate stage commands do not execute scripts/run_linux_validation_suite.py as the first script token'
                )
            ),
            'evidence': (
                [str(release_gate_path)]
                if not release_gate_script_position_mismatches
                else release_gate_script_position_mismatches
            ),
        },
        {
            'name': 'release_gate_script_anchor',
            'status': 'pass' if release_gate_script_anchor_pass else 'hold',
            'reason': (
                'release-gate stage commands resolve scripts/run_linux_validation_suite.py to repository canonical path'
                if release_gate_script_anchor_pass and release_gate_script_anchor_check_enabled
                else (
                    'release-gate script-anchor gate disabled (--skip-release-gate-script-anchor-check)'
                    if release_gate_script_anchor_pass
                    else 'release-gate stage commands resolve linux-suite script token to non-canonical path'
                )
            ),
            'evidence': (
                [str(release_gate_path)]
                if not release_gate_script_anchor_mismatches
                else release_gate_script_anchor_mismatches
            ),
        },
        {
            'name': 'release_gate_python_binding',
            'status': 'pass' if release_gate_python_binding_pass else 'hold',
            'reason': (
                'release-gate stage commands keep --python and launcher prefix bound to release-switch --python input'
                if release_gate_python_binding_pass and release_gate_python_binding_check_enabled
                else (
                    'release-gate python-binding gate disabled (--skip-release-gate-python-binding-check)'
                    if release_gate_python_binding_pass
                    else 'release-gate stage commands contain --python/launcher binding drift'
                )
            ),
            'evidence': (
                [str(release_gate_path)]
                if not release_gate_python_binding_mismatches
                else release_gate_python_binding_mismatches
            ),
        },
        {
            'name': 'release_gate_coverage_floor',
            'status': 'pass' if release_gate_coverage_floor_pass else 'hold',
            'reason': (
                'release-gate beta stage keeps --coverage-fail-under bound to release-switch input and >= %.1f'
                % DEFAULT_RELEASE_GATE_COVERAGE_FLOOR
                if release_gate_coverage_floor_pass and release_gate_coverage_floor_check_enabled
                else (
                    'release-gate coverage-floor gate disabled (--skip-release-gate-coverage-floor-check)'
                    if release_gate_coverage_floor_pass
                    else 'release-gate beta stage --coverage-fail-under is missing, drifted, or below floor'
                )
            ),
            'evidence': (
                [str(release_gate_path)]
                if not release_gate_coverage_floor_mismatches
                else release_gate_coverage_floor_mismatches
            ),
        },
        {
            'name': 'release_gate_python_optimization',
            'status': 'pass' if release_gate_python_optimization_pass else 'hold',
            'reason': (
                'release-gate stage launchers do not include python optimization flags (-O/-OO) that can bypass assertions'
                if release_gate_python_optimization_pass
                and release_gate_python_optimization_check_enabled
                else (
                    'release-gate python-optimization gate disabled (--skip-release-gate-python-optimization-check)'
                    if release_gate_python_optimization_pass
                    else 'release-gate stage launchers include forbidden python optimization flags (-O/-OO)'
                )
            ),
            'evidence': (
                [str(release_gate_path)]
                if not release_gate_python_optimization_mismatches
                else release_gate_python_optimization_mismatches
            ),
        },
        {
            'name': 'release_gate_python_option_optimization',
            'status': 'pass' if release_gate_python_option_optimization_pass else 'hold',
            'reason': (
                'release-gate stage --python values do not include python optimization flags (-O/-OO) that can bypass downstream assertions'
                if release_gate_python_option_optimization_pass
                and release_gate_python_option_optimization_check_enabled
                else (
                    'release-gate python-option-optimization gate disabled (--skip-release-gate-python-option-optimization-check)'
                    if release_gate_python_option_optimization_pass
                    else 'release-gate stage --python values include forbidden python optimization flags (-O/-OO)'
                )
            ),
            'evidence': (
                [str(release_gate_path)]
                if not release_gate_python_option_optimization_mismatches
                else release_gate_python_option_optimization_mismatches
            ),
        },
        {
            'name': 'release_gate_python_optimize_env',
            'status': 'pass' if release_gate_python_optimize_env_pass else 'hold',
            'reason': (
                'release-gate stage launchers and --python relay values do not assign PYTHONOPTIMIZE env flags that can bypass assertions'
                if release_gate_python_optimize_env_pass
                and release_gate_python_optimize_env_check_enabled
                else (
                    'release-gate python-optimize-env gate disabled (--skip-release-gate-python-optimize-env-check)'
                    if release_gate_python_optimize_env_pass
                    else 'release-gate stage launchers or --python relay values include forbidden PYTHONOPTIMIZE env assignments'
                )
            ),
            'evidence': (
                [str(release_gate_path)]
                if not release_gate_python_optimize_env_mismatches
                else release_gate_python_optimize_env_mismatches
            ),
        },
        {
            'name': 'release_gate_python_path_env',
            'status': 'pass' if release_gate_python_path_env_pass else 'hold',
            'reason': (
                'release-gate stage launchers and --python relay values do not assign PYTHONPATH env values that can redirect module resolution'
                if release_gate_python_path_env_pass
                and release_gate_python_path_env_check_enabled
                else (
                    'release-gate python-path-env gate disabled (--skip-release-gate-python-path-env-check)'
                    if release_gate_python_path_env_pass
                    else 'release-gate stage launchers or --python relay values include forbidden PYTHONPATH env assignments'
                )
            ),
            'evidence': (
                [str(release_gate_path)]
                if not release_gate_python_path_env_mismatches
                else release_gate_python_path_env_mismatches
            ),
        },
        {
            'name': 'release_gate_python_home_env',
            'status': 'pass' if release_gate_python_home_env_pass else 'hold',
            'reason': (
                'release-gate stage launchers and --python relay values do not assign PYTHONHOME env values that can redirect runtime home resolution'
                if release_gate_python_home_env_pass
                and release_gate_python_home_env_check_enabled
                else (
                    'release-gate python-home-env gate disabled (--skip-release-gate-python-home-env-check)'
                    if release_gate_python_home_env_pass
                    else 'release-gate stage launchers or --python relay values include forbidden PYTHONHOME env assignments'
                )
            ),
            'evidence': (
                [str(release_gate_path)]
                if not release_gate_python_home_env_mismatches
                else release_gate_python_home_env_mismatches
            ),
        },
        {
            'name': 'release_gate_python_user_base_env',
            'status': 'pass' if release_gate_python_user_base_env_pass else 'hold',
            'reason': (
                'release-gate stage launchers and --python relay values do not assign PYTHONUSERBASE env values that can redirect user-site package resolution'
                if release_gate_python_user_base_env_pass
                and release_gate_python_user_base_env_check_enabled
                else (
                    'release-gate python-user-base-env gate disabled (--skip-release-gate-python-user-base-env-check)'
                    if release_gate_python_user_base_env_pass
                    else 'release-gate stage launchers or --python relay values include forbidden PYTHONUSERBASE env assignments'
                )
            ),
            'evidence': (
                [str(release_gate_path)]
                if not release_gate_python_user_base_env_mismatches
                else release_gate_python_user_base_env_mismatches
            ),
        },
        {
            'name': 'release_gate_python_breakpoint_env',
            'status': 'pass' if release_gate_python_breakpoint_env_pass else 'hold',
            'reason': (
                'release-gate stage launchers and --python relay values do not assign PYTHONBREAKPOINT env values that can hook breakpoint dispatch'
                if release_gate_python_breakpoint_env_pass
                and release_gate_python_breakpoint_env_check_enabled
                else (
                    'release-gate python-breakpoint-env gate disabled (--skip-release-gate-python-breakpoint-env-check)'
                    if release_gate_python_breakpoint_env_pass
                    else 'release-gate stage launchers or --python relay values include forbidden PYTHONBREAKPOINT env assignments'
                )
            ),
            'evidence': (
                [str(release_gate_path)]
                if not release_gate_python_breakpoint_env_mismatches
                else release_gate_python_breakpoint_env_mismatches
            ),
        },
        {
            'name': 'release_gate_python_startup_env',
            'status': 'pass' if release_gate_python_startup_env_pass else 'hold',
            'reason': (
                'release-gate stage launchers and --python relay values do not assign PYTHONSTARTUP env values that can inject startup hooks'
                if release_gate_python_startup_env_pass
                and release_gate_python_startup_env_check_enabled
                else (
                    'release-gate python-startup-env gate disabled (--skip-release-gate-python-startup-env-check)'
                    if release_gate_python_startup_env_pass
                    else 'release-gate stage launchers or --python relay values include forbidden PYTHONSTARTUP env assignments'
                )
            ),
            'evidence': (
                [str(release_gate_path)]
                if not release_gate_python_startup_env_mismatches
                else release_gate_python_startup_env_mismatches
            ),
        },
        {
            'name': 'release_gate_python_inspect_env',
            'status': 'pass' if release_gate_python_inspect_env_pass else 'hold',
            'reason': (
                'release-gate stage launchers and --python relay values do not assign PYTHONINSPECT env values that can trigger interactive-dispatch drift'
                if release_gate_python_inspect_env_pass
                and release_gate_python_inspect_env_check_enabled
                else (
                    'release-gate python-inspect-env gate disabled (--skip-release-gate-python-inspect-env-check)'
                    if release_gate_python_inspect_env_pass
                    else 'release-gate stage launchers or --python relay values include forbidden PYTHONINSPECT env assignments'
                )
            ),
            'evidence': (
                [str(release_gate_path)]
                if not release_gate_python_inspect_env_mismatches
                else release_gate_python_inspect_env_mismatches
            ),
        },
        {
            'name': 'release_gate_python_warnings_env',
            'status': 'pass' if release_gate_python_warnings_env_pass else 'hold',
            'reason': (
                'release-gate stage launchers and --python relay values do not assign PYTHONWARNINGS env values that can suppress release-critical warning contracts'
                if release_gate_python_warnings_env_pass
                and release_gate_python_warnings_env_check_enabled
                else (
                    'release-gate python-warnings-env gate disabled (--skip-release-gate-python-warnings-env-check)'
                    if release_gate_python_warnings_env_pass
                    else 'release-gate stage launchers or --python relay values include forbidden PYTHONWARNINGS env assignments'
                )
            ),
            'evidence': (
                [str(release_gate_path)]
                if not release_gate_python_warnings_env_mismatches
                else release_gate_python_warnings_env_mismatches
            ),
        },
        {
            'name': 'release_gate_python_option_inline_exec',
            'status': 'pass' if release_gate_python_option_inline_exec_pass else 'hold',
            'reason': (
                'release-gate stage --python values do not include inline-dispatch flags (-c/-m/-) that can bypass downstream script execution'
                if release_gate_python_option_inline_exec_pass
                and release_gate_python_option_inline_exec_check_enabled
                else (
                    'release-gate python-option-inline-exec gate disabled (--skip-release-gate-python-option-inline-exec-check)'
                    if release_gate_python_option_inline_exec_pass
                    else 'release-gate stage --python values include forbidden inline-dispatch flags (-c/-m/-)'
                )
            ),
            'evidence': (
                [str(release_gate_path)]
                if not release_gate_python_option_inline_exec_mismatches
                else release_gate_python_option_inline_exec_mismatches
            ),
        },
        {
            'name': 'release_gate_inline_exec',
            'status': 'pass' if release_gate_inline_exec_pass else 'hold',
            'reason': (
                'release-gate stage commands do not use inline-dispatch flags (-c/-m/-) before linux-suite script token'
                if release_gate_inline_exec_pass and release_gate_inline_exec_check_enabled
                else (
                    'release-gate inline-exec gate disabled (--skip-release-gate-inline-exec-check)'
                    if release_gate_inline_exec_pass
                    else 'release-gate stage commands include forbidden inline-dispatch flags before linux-suite script token'
                )
            ),
            'evidence': (
                [str(release_gate_path)]
                if not release_gate_inline_exec_mismatches
                else release_gate_inline_exec_mismatches
            ),
        },
        {
            'name': 'release_gate_option_override',
            'status': 'pass' if release_gate_option_override_pass else 'hold',
            'reason': (
                'release-gate stage commands contain single --stages and --output options (no override ambiguity)'
                if release_gate_option_override_pass and release_gate_option_override_check_enabled
                else (
                    'release-gate option-override gate disabled (--skip-release-gate-option-override-check)'
                    if release_gate_option_override_pass
                    else 'release-gate stage commands contain ambiguous repeated --stages/--output options'
                )
            ),
            'evidence': (
                [str(release_gate_path)]
                if not release_gate_option_override_mismatches
                else release_gate_option_override_mismatches
            ),
        },
        {
            'name': 'release_gate_dry_run',
            'status': 'pass' if release_gate_dry_run_pass else 'hold',
            'reason': (
                'release-gate stage commands do not include --dry-run bypass flag'
                if release_gate_dry_run_pass and release_gate_dry_run_check_enabled
                else (
                    'release-gate dry-run gate disabled (--skip-release-gate-dry-run-check)'
                    if release_gate_dry_run_pass
                    else 'release-gate stage commands include forbidden --dry-run bypass flag'
                )
            ),
            'evidence': (
                [str(release_gate_path)]
                if not release_gate_dry_run_mismatches
                else release_gate_dry_run_mismatches
            ),
        },
        {
            'name': 'release_gate_relaxed_flags',
            'status': 'pass' if release_gate_relaxed_flags_pass else 'hold',
            'reason': (
                'release-gate stage commands do not include relaxed gate-bypass flags'
                if release_gate_relaxed_flags_pass and release_gate_relaxed_flags_check_enabled
                else (
                    'release-gate relaxed-flags gate disabled (--skip-release-gate-relaxed-flags-check)'
                    if release_gate_relaxed_flags_pass
                    else 'release-gate stage commands include forbidden relaxed flags'
                )
            ),
            'evidence': (
                [str(release_gate_path)]
                if not release_gate_relaxed_flag_mismatches
                else release_gate_relaxed_flag_mismatches
            ),
        },
        {
            'name': 'graph_is_source_of_truth',
            'status': 'pass' if gate_graph_source else 'hold',
            'reason': (
                'doc_sync/release-contract pass + release gate evidence pack complete and executable'
                if gate_graph_source
                else 'missing/failing release-switch contract or incomplete/non-executable release-gate evidence pack'
            ),
            'evidence': [str(doc_sync_path), str(beta_suite_path), str(release_gate_path), str(release_standard_path)],
        },
        {
            'name': 'review_queue_operational',
            'status': 'pass' if gate_review_queue else 'hold',
            'reason': (
                'release gate and ga suite include executable review_queue hardening stages'
                if gate_review_queue
                else 'ga suite/release-gate evidence missing review_queue executable stage contract or marker'
            ),
            'evidence': [str(ga_suite_path), str(release_gate_path), str(release_standard_path)],
        },
        {
            'name': 'publication_view_count>=2',
            'status': 'pass' if gate_publication_views else 'hold',
            'reason': (
                'release-switch docs contract + roadmap evidence pack complete and executable'
                if gate_publication_views
                else 'release-switch contract/doc check or roadmap evidence pack incomplete/non-executable'
            ),
            'evidence': [str(doc_sync_path), str(roadmap_suite_path), str(release_gate_path), str(release_standard_path)],
        },
        {
            'name': 'postgres_repository_stable',
            'status': 'pass' if gate_postgres else 'hold',
            'reason': (
                'postgres soak benchmark recorded dual_write run with complete and executable ga gate evidence pack'
                if gate_postgres
                else 'postgres soak evidence missing/incomplete, ga gate non-executable, or dual_write did not execute'
            ),
            'evidence': [str(postgres_soak_benchmark_path), str(ga_suite_path), str(release_gate_path), str(release_standard_path)],
        },
        {
            'name': 'regression_beats_v1',
            'status': 'pass' if gate_regression else 'hold',
            'reason': (
                'quality/perf regression counts are zero and beta gate evidence pack complete and executable'
                if gate_regression
                else 'quality/perf report missing/regressed or beta gate evidence pack incomplete/non-executable'
            ),
            'evidence': [str(quality_path), str(perf_path), str(beta_suite_path), str(release_gate_path), str(release_standard_path)],
        },
    ]
    hold_count = sum(1 for item in gates if item['status'] != 'pass')
    pass_count = len(gates) - hold_count

    cohort_skew_violation_file_set = set(cohort_skew_violation_files)
    evidence_files = []
    for path, status in (
        (doc_sync_path, doc_sync_error or 'ok'),
        (quality_path, quality_error or 'ok'),
        (perf_path, perf_error or 'ok'),
        (postgres_soak_benchmark_path, postgres_soak_error or 'ok'),
        (beta_suite_path, beta_suite_error or 'ok'),
        (ga_suite_path, ga_suite_error or 'ok'),
        (roadmap_suite_path, roadmap_suite_error or 'ok'),
        (release_gate_path, release_gate_error or 'ok'),
        (release_standard_path, release_standard_error or 'ok'),
    ):
        payload: dict[str, Any] = {'path': str(path), 'status': status}
        age_hours = evidence_age_hours.get(str(path))
        if age_hours is not None:
            payload['age_hours'] = age_hours
        if status == 'ok' and str(path) in future_evidence_file_set:
            payload['freshness'] = 'future_skewed'
        elif freshness_check_enabled and status == 'ok' and str(path) in stale_evidence_file_set:
            payload['freshness'] = 'stale'
        elif cohort_skew_check_enabled and status == 'ok' and str(path) in cohort_skew_violation_file_set:
            payload['freshness'] = 'cohort_skewed'
        elif (
            freshness_check_enabled
            or future_skew_check_enabled
            or cohort_skew_check_enabled
        ) and status == 'ok' and str(path) in evidence_age_hours:
            payload['freshness'] = 'fresh'
        evidence_files.append(payload)
    missing_or_invalid = [item for item in evidence_files if item['status'] != 'ok']

    decision = 'GO' if hold_count == 0 else 'HOLD'
    return {
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'decision': decision,
        'gate_count': len(gates),
        'pass_count': pass_count,
        'hold_count': hold_count,
        'gates': gates,
        'evidence_files': evidence_files,
        'missing_or_invalid_evidence': missing_or_invalid,
        'evidence_summary': {
            'doc_sync_status': (doc_sync_report or {}).get('status') if doc_sync_report else 'missing',
            'doc_sync_release_switch_check': release_contract_check,
            'quality_regressed_count': quality_regressed_count,
            'perf_regressed_count': perf_regressed_count,
            'postgres_run_postgres': postgres_run_enabled,
            'postgres_dual_write_count': dual_write_count,
            'freshness_check_enabled': freshness_check_enabled,
            'max_evidence_age_hours': max_evidence_age_hours,
            'future_skew_check_enabled': future_skew_check_enabled,
            'max_evidence_future_skew_hours': max_evidence_future_skew_hours,
            'cohort_skew_check_enabled': cohort_skew_check_enabled,
            'max_evidence_cohort_skew_hours': max_evidence_cohort_skew_hours,
            'evidence_freshness_gate_pass': evidence_freshness_gate_pass,
            'evidence_cohort_skew_gate_pass': cohort_skew_gate_pass,
            'release_gate_binding_check_enabled': release_gate_binding_check_enabled,
            'release_gate_output_binding_pass': release_gate_output_binding_pass,
            'release_gate_binding_mismatch_count': len(release_gate_binding_mismatches),
            'release_gate_binding_mismatches': release_gate_binding_mismatches,
            'release_gate_stage_contract_check_enabled': release_gate_stage_contract_check_enabled,
            'release_gate_stage_contract_pass': release_gate_stage_contract_pass,
            'release_gate_stage_contract_mismatch_count': len(release_gate_stage_contract_mismatches),
            'release_gate_stage_contract_mismatches': release_gate_stage_contract_mismatches,
            'release_gate_script_position_check_enabled': release_gate_script_position_check_enabled,
            'release_gate_script_position_pass': release_gate_script_position_pass,
            'release_gate_script_position_mismatch_count': len(
                release_gate_script_position_mismatches
            ),
            'release_gate_script_position_mismatches': release_gate_script_position_mismatches,
            'release_gate_script_anchor_check_enabled': release_gate_script_anchor_check_enabled,
            'release_gate_script_anchor_pass': release_gate_script_anchor_pass,
            'release_gate_script_anchor_mismatch_count': len(
                release_gate_script_anchor_mismatches
            ),
            'release_gate_script_anchor_mismatches': release_gate_script_anchor_mismatches,
            'release_gate_python_binding_check_enabled': release_gate_python_binding_check_enabled,
            'release_gate_python_binding_pass': release_gate_python_binding_pass,
            'release_gate_python_binding_mismatch_count': len(
                release_gate_python_binding_mismatches
            ),
            'release_gate_python_binding_mismatches': release_gate_python_binding_mismatches,
            'release_gate_python_optimization_check_enabled': release_gate_python_optimization_check_enabled,
            'release_gate_python_optimization_pass': release_gate_python_optimization_pass,
            'release_gate_python_optimization_mismatch_count': len(
                release_gate_python_optimization_mismatches
            ),
            'release_gate_python_optimization_mismatches': release_gate_python_optimization_mismatches,
            'release_gate_python_option_optimization_check_enabled': release_gate_python_option_optimization_check_enabled,
            'release_gate_python_option_optimization_pass': release_gate_python_option_optimization_pass,
            'release_gate_python_option_optimization_mismatch_count': len(
                release_gate_python_option_optimization_mismatches
            ),
            'release_gate_python_option_optimization_mismatches': release_gate_python_option_optimization_mismatches,
            'release_gate_python_optimize_env_check_enabled': release_gate_python_optimize_env_check_enabled,
            'release_gate_python_optimize_env_pass': release_gate_python_optimize_env_pass,
            'release_gate_python_optimize_env_mismatch_count': len(
                release_gate_python_optimize_env_mismatches
            ),
            'release_gate_python_optimize_env_mismatches': release_gate_python_optimize_env_mismatches,
            'release_gate_python_path_env_check_enabled': release_gate_python_path_env_check_enabled,
            'release_gate_python_path_env_pass': release_gate_python_path_env_pass,
            'release_gate_python_path_env_mismatch_count': len(
                release_gate_python_path_env_mismatches
            ),
            'release_gate_python_path_env_mismatches': release_gate_python_path_env_mismatches,
            'release_gate_python_home_env_check_enabled': release_gate_python_home_env_check_enabled,
            'release_gate_python_home_env_pass': release_gate_python_home_env_pass,
            'release_gate_python_home_env_mismatch_count': len(
                release_gate_python_home_env_mismatches
            ),
            'release_gate_python_home_env_mismatches': release_gate_python_home_env_mismatches,
            'release_gate_python_user_base_env_check_enabled': release_gate_python_user_base_env_check_enabled,
            'release_gate_python_user_base_env_pass': release_gate_python_user_base_env_pass,
            'release_gate_python_user_base_env_mismatch_count': len(
                release_gate_python_user_base_env_mismatches
            ),
            'release_gate_python_user_base_env_mismatches': release_gate_python_user_base_env_mismatches,
            'release_gate_python_breakpoint_env_check_enabled': release_gate_python_breakpoint_env_check_enabled,
            'release_gate_python_breakpoint_env_pass': release_gate_python_breakpoint_env_pass,
            'release_gate_python_breakpoint_env_mismatch_count': len(
                release_gate_python_breakpoint_env_mismatches
            ),
            'release_gate_python_breakpoint_env_mismatches': release_gate_python_breakpoint_env_mismatches,
            'release_gate_python_startup_env_check_enabled': release_gate_python_startup_env_check_enabled,
            'release_gate_python_startup_env_pass': release_gate_python_startup_env_pass,
            'release_gate_python_startup_env_mismatch_count': len(
                release_gate_python_startup_env_mismatches
            ),
            'release_gate_python_startup_env_mismatches': release_gate_python_startup_env_mismatches,
            'release_gate_python_inspect_env_check_enabled': release_gate_python_inspect_env_check_enabled,
            'release_gate_python_inspect_env_pass': release_gate_python_inspect_env_pass,
            'release_gate_python_inspect_env_mismatch_count': len(
                release_gate_python_inspect_env_mismatches
            ),
            'release_gate_python_inspect_env_mismatches': release_gate_python_inspect_env_mismatches,
            'release_gate_python_warnings_env_check_enabled': release_gate_python_warnings_env_check_enabled,
            'release_gate_python_warnings_env_pass': release_gate_python_warnings_env_pass,
            'release_gate_python_warnings_env_mismatch_count': len(
                release_gate_python_warnings_env_mismatches
            ),
            'release_gate_python_warnings_env_mismatches': release_gate_python_warnings_env_mismatches,
            'release_gate_python_option_inline_exec_check_enabled': release_gate_python_option_inline_exec_check_enabled,
            'release_gate_python_option_inline_exec_pass': release_gate_python_option_inline_exec_pass,
            'release_gate_python_option_inline_exec_mismatch_count': len(
                release_gate_python_option_inline_exec_mismatches
            ),
            'release_gate_python_option_inline_exec_mismatches': release_gate_python_option_inline_exec_mismatches,
            'release_gate_coverage_floor_check_enabled': release_gate_coverage_floor_check_enabled,
            'release_gate_coverage_floor_pass': release_gate_coverage_floor_pass,
            'release_gate_coverage_floor_mismatch_count': len(
                release_gate_coverage_floor_mismatches
            ),
            'release_gate_coverage_floor_mismatches': release_gate_coverage_floor_mismatches,
            'release_gate_inline_exec_check_enabled': release_gate_inline_exec_check_enabled,
            'release_gate_inline_exec_pass': release_gate_inline_exec_pass,
            'release_gate_inline_exec_mismatch_count': len(
                release_gate_inline_exec_mismatches
            ),
            'release_gate_inline_exec_mismatches': release_gate_inline_exec_mismatches,
            'release_gate_option_override_check_enabled': release_gate_option_override_check_enabled,
            'release_gate_option_override_pass': release_gate_option_override_pass,
            'release_gate_option_override_mismatch_count': len(
                release_gate_option_override_mismatches
            ),
            'release_gate_option_override_mismatches': release_gate_option_override_mismatches,
            'release_gate_dry_run_check_enabled': release_gate_dry_run_check_enabled,
            'release_gate_dry_run_pass': release_gate_dry_run_pass,
            'release_gate_dry_run_mismatch_count': len(
                release_gate_dry_run_mismatches
            ),
            'release_gate_dry_run_mismatches': release_gate_dry_run_mismatches,
            'release_gate_relaxed_flags_check_enabled': release_gate_relaxed_flags_check_enabled,
            'release_gate_relaxed_flags_pass': release_gate_relaxed_flags_pass,
            'release_gate_relaxed_flags_mismatch_count': len(
                release_gate_relaxed_flag_mismatches
            ),
            'release_gate_relaxed_flags_mismatches': release_gate_relaxed_flag_mismatches,
            'evidence_cohort_age_spread_hours': evidence_cohort_age_spread_hours,
            'oldest_evidence_file': oldest_evidence_file or None,
            'newest_evidence_file': newest_evidence_file or None,
            'cohort_skew_violation_count': len(cohort_skew_violation_files),
            'cohort_skew_violation_files': cohort_skew_violation_files,
            'stale_evidence_count': len(stale_evidence_files),
            'stale_evidence_files': stale_evidence_files,
            'future_evidence_count': len(future_evidence_files),
            'future_evidence_files': future_evidence_files,
            'beta_suite_stage_pack_complete': beta_suite_stage_pack_complete,
            'beta_suite_stage_pack_executable': beta_suite_stage_pack_executable,
            'beta_suite_evidence_pack_complete': beta_suite_evidence_pack_complete,
            'ga_suite_stage_pack_complete': ga_suite_stage_pack_complete,
            'ga_suite_stage_pack_executable': ga_suite_stage_pack_executable,
            'ga_suite_evidence_pack_complete': ga_suite_evidence_pack_complete,
            'roadmap_suite_stage_pack_complete': roadmap_suite_stage_pack_complete,
            'roadmap_suite_stage_pack_executable': roadmap_suite_stage_pack_executable,
            'roadmap_suite_evidence_pack_complete': roadmap_suite_evidence_pack_complete,
            'release_gate_stage_pack_complete': release_gate_stage_pack_complete,
            'release_gate_stage_pack_executable': release_gate_stage_pack_executable,
            'release_gate_evidence_pack_complete': release_gate_evidence_pack_complete,
            'ga_suite_has_review_queue_ga': review_queue_stage_present,
            'release_standard_markers': standard_markers,
        },
    }


def _print_decision_summary(decision_report: dict[str, Any]) -> None:
    print(
        'Release switch decision=%s gates(pass=%s hold=%s)'
        % (
            decision_report.get('decision'),
            decision_report.get('pass_count'),
            decision_report.get('hold_count'),
        )
    )
    for gate in decision_report.get('gates', []):
        print(
            '- %s: %s (%s)'
            % (
                gate.get('name'),
                gate.get('status'),
                gate.get('reason'),
            )
        )


def main() -> int:
    args = _parse_args()

    stage_specs: list[StageSpec] = []
    if not args.decision_only:
        if not args.stages:
            print('No stages selected. Use --stages with at least one value.', file=sys.stderr)
            return 2
        try:
            python_cmd = _split_python_command(args.python)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2

        stage_map = _build_stage_map(args, python_cmd=python_cmd)
        stage_specs = [stage_map[name] for name in args.stages]
        _print_plan(stage_specs)

        plan_payload = _build_plan(stage_specs)
        output_value = str(args.output or '').strip()
        if output_value and output_value != '-':
            output_path = Path(output_value).resolve()
            _write_json(output_path, plan_payload)
            print('Plan written: %s' % output_path)

        if args.dry_run:
            print('Dry-run enabled: command stages are not executed.')
        else:
            run_code = _run_stages(stage_specs)
            if run_code != 0:
                return run_code

    decision_report = _evaluate_decision(args)
    _print_decision_summary(decision_report)

    decision_output_value = str(args.decision_output or '').strip()
    if decision_output_value and decision_output_value != '-':
        decision_output_path = Path(decision_output_value).resolve()
        _write_json(decision_output_path, decision_report)
        print('Decision report written: %s' % decision_output_path)

    if args.print_json:
        print(json.dumps(decision_report, ensure_ascii=False, indent=2))

    if args.dry_run:
        return 0
    if decision_report.get('decision') == 'HOLD' and not args.allow_hold:
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
