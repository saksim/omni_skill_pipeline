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
        help='Nested release-gate beta suite output path.',
    )
    parser.add_argument(
        '--ga-suite-output',
        default=str(DEFAULT_GA_SUITE_OUTPUT),
        help='Nested release-gate GA suite output path.',
    )
    parser.add_argument(
        '--roadmap-suite-output',
        default=str(DEFAULT_ROADMAP_SUITE_OUTPUT),
        help='Nested release-gate roadmap suite output path.',
    )
    parser.add_argument(
        '--release-gate-output',
        default=str(DEFAULT_RELEASE_GATE_OUTPUT),
        help='Release-gate top-level plan output path.',
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


def _ga_suite_has_stage(ga_suite_report: dict[str, Any], stage_name: str) -> bool:
    stages = ga_suite_report.get('stages')
    if not isinstance(stages, list):
        return False
    for item in stages:
        if not isinstance(item, dict):
            continue
        if str(item.get('name', '')).strip() == stage_name:
            return True
    return False


def _evaluate_decision(args: argparse.Namespace) -> dict[str, Any]:
    doc_sync_path = Path(args.doc_sync_report).resolve()
    quality_path = Path(args.quality_report).resolve()
    perf_path = Path(args.perf_report).resolve()
    postgres_soak_benchmark_path = Path(args.postgres_soak_benchmark_report).resolve()
    ga_suite_path = Path(args.ga_suite_output).resolve()
    release_standard_path = Path(args.release_standard_doc).resolve()

    doc_sync_report, doc_sync_error = _load_json_file(doc_sync_path)
    quality_report, quality_error = _load_json_file(quality_path)
    perf_report, perf_error = _load_json_file(perf_path)
    postgres_soak_report, postgres_soak_error = _load_json_file(postgres_soak_benchmark_path)
    ga_suite_report, ga_suite_error = _load_json_file(ga_suite_path)
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

    review_queue_stage_present = bool(
        ga_suite_report is not None and _ga_suite_has_stage(ga_suite_report, 'review_queue_ga')
    )

    gate_graph_source = (
        doc_sync_pass
        and release_contract_check == 'pass'
        and standard_markers.get('graph_is_source_of_truth', False)
    )
    gate_review_queue = (
        review_queue_stage_present
        and standard_markers.get('review_queue_operational', False)
    )
    gate_publication_views = (
        doc_sync_pass
        and release_contract_check == 'pass'
        and standard_markers.get('publication_view_count>=2', False)
    )
    gate_postgres = (
        postgres_run_enabled
        and dual_write_count > 0
        and standard_markers.get('postgres_repository_stable', False)
    )
    gate_regression = (
        quality_regressed_count == 0
        and perf_regressed_count == 0
        and standard_markers.get('regression_beats_v1', False)
    )

    gates = [
        {
            'name': 'graph_is_source_of_truth',
            'status': 'pass' if gate_graph_source else 'hold',
            'reason': (
                'doc_sync pass + release switch contract pass'
                if gate_graph_source
                else 'missing or failing release-switch doc/evidence contract'
            ),
            'evidence': [str(doc_sync_path), str(release_standard_path)],
        },
        {
            'name': 'review_queue_operational',
            'status': 'pass' if gate_review_queue else 'hold',
            'reason': (
                'ga suite includes review_queue_ga stage'
                if gate_review_queue
                else 'ga suite plan missing review_queue_ga stage or marker'
            ),
            'evidence': [str(ga_suite_path), str(release_standard_path)],
        },
        {
            'name': 'publication_view_count>=2',
            'status': 'pass' if gate_publication_views else 'hold',
            'reason': (
                'release-switch contract checks passed'
                if gate_publication_views
                else 'release-switch contract/doc check not passed'
            ),
            'evidence': [str(doc_sync_path), str(release_standard_path)],
        },
        {
            'name': 'postgres_repository_stable',
            'status': 'pass' if gate_postgres else 'hold',
            'reason': (
                'postgres soak benchmark recorded dual_write run'
                if gate_postgres
                else 'postgres soak benchmark missing or did not execute dual_write'
            ),
            'evidence': [str(postgres_soak_benchmark_path), str(release_standard_path)],
        },
        {
            'name': 'regression_beats_v1',
            'status': 'pass' if gate_regression else 'hold',
            'reason': (
                'quality/perf regression counts are zero'
                if gate_regression
                else 'quality/perf regression report missing or regressed'
            ),
            'evidence': [str(quality_path), str(perf_path), str(release_standard_path)],
        },
    ]
    hold_count = sum(1 for item in gates if item['status'] != 'pass')
    pass_count = len(gates) - hold_count

    evidence_files = [
        {'path': str(doc_sync_path), 'status': doc_sync_error or 'ok'},
        {'path': str(quality_path), 'status': quality_error or 'ok'},
        {'path': str(perf_path), 'status': perf_error or 'ok'},
        {'path': str(postgres_soak_benchmark_path), 'status': postgres_soak_error or 'ok'},
        {'path': str(ga_suite_path), 'status': ga_suite_error or 'ok'},
        {'path': str(release_standard_path), 'status': release_standard_error or 'ok'},
    ]
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
