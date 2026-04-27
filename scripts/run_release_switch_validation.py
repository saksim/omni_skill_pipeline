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
    beta_suite_evidence_pack_complete = beta_suite_stage_pack_complete and beta_suite_stage_pack_executable
    ga_suite_evidence_pack_complete = ga_suite_stage_pack_complete and ga_suite_stage_pack_executable
    roadmap_suite_evidence_pack_complete = roadmap_suite_stage_pack_complete and roadmap_suite_stage_pack_executable
    release_gate_evidence_pack_complete = (
        release_gate_stage_pack_complete
        and release_gate_stage_pack_executable
        and release_gate_output_binding_pass
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
