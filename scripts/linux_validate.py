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
DEFAULT_DOC_SYNC_OUTPUT = (
    REPO_ROOT / 'docs' / 'current' / 'status' / 'baselines' / 'e13-doc-sync-check-report.json'
)
DEFAULT_QUALITY_MANIFEST = (
    REPO_ROOT / 'docs' / 'current' / 'status' / 'baselines' / 'e11-quality-regression-manifest.json'
)
DEFAULT_QUALITY_OUTPUT = (
    REPO_ROOT / 'docs' / 'current' / 'status' / 'baselines' / 'e11-quality-regression-report.json'
)
DEFAULT_PERF_MANIFEST = (
    REPO_ROOT / 'docs' / 'current' / 'status' / 'baselines' / 'e11-perf-cost-baseline-manifest.json'
)
DEFAULT_PERF_OUTPUT = (
    REPO_ROOT / 'docs' / 'current' / 'status' / 'baselines' / 'e11-perf-cost-baseline-report.json'
)
DEFAULT_CONTAINER_IMAGE_TAG = 'omni-skill-pipeline:beta'
DEFAULT_CONTAINER_NAME = 'omni-skill-pipeline-smoke'
DEFAULT_CONTAINER_HOST = '127.0.0.1'
DEFAULT_CONTAINER_PORT = 18000
DEFAULT_CONTAINER_TIMEOUT_SECONDS = 30.0
DEFAULT_CONTAINER_INTERVAL_SECONDS = 1.0
DEFAULT_POSTGRES_SOAK_OUTPUT = (
    REPO_ROOT / 'docs' / 'current' / 'status' / 'baselines' / 'e13-postgres-soak-plan.json'
)
DEFAULT_POSTGRES_SOAK_BENCHMARK_OUTPUT = (
    REPO_ROOT / 'docs' / 'current' / 'status' / 'baselines' / 'e13-postgres-soak-benchmark-report.json'
)
DEFAULT_POSTGRES_GA_OUTPUT = (
    REPO_ROOT / 'docs' / 'current' / 'status' / 'baselines' / 'e13-postgres-ga-validation-plan.json'
)
DEFAULT_POSTGRES_GA_BENCHMARK_OUTPUT = (
    REPO_ROOT / 'docs' / 'current' / 'status' / 'baselines' / 'e13-postgres-ga-benchmark-report.json'
)
DEFAULT_WORKER_GA_OUTPUT = (
    REPO_ROOT / 'docs' / 'current' / 'status' / 'baselines' / 'e13-worker-ga-validation-plan.json'
)
DEFAULT_REVIEW_QUEUE_GA_OUTPUT = (
    REPO_ROOT / 'docs' / 'current' / 'status' / 'baselines' / 'e13-review-queue-ga-validation-plan.json'
)
DEFAULT_PROVIDER_GA_OUTPUT = (
    REPO_ROOT / 'docs' / 'current' / 'status' / 'baselines' / 'e13-provider-ga-validation-plan.json'
)
DEFAULT_CALIBRATION_MANIFEST = (
    REPO_ROOT / 'docs' / 'current' / 'status' / 'baselines' / 'e7-calibration-manifest.json'
)
DEFAULT_CALIBRATION_REPORT_OUTPUT = (
    REPO_ROOT / 'docs' / 'current' / 'status' / 'baselines' / 'e7-calibration-report.json'
)
DEFAULT_CALIBRATION_GA_OUTPUT = (
    REPO_ROOT / 'docs' / 'current' / 'status' / 'baselines' / 'e13-calibration-ga-validation-plan.json'
)
DEFAULT_ROADMAP_EXTENSION_OUTPUT = (
    REPO_ROOT / 'docs' / 'current' / 'status' / 'baselines' / 'e13-roadmap-extension-validation-plan.json'
)
DEFAULT_PLAN_OUTPUT = (
    REPO_ROOT / 'docs' / 'current' / 'status' / 'baselines' / 'e13-linux-validation-suite-plan.json'
)
DEFAULT_STAGES = (
    'ci',
    'container_smoke',
    'doc_sync',
    'quality_regression',
    'perf_cost_baseline',
    'postgres_soak',
    'postgres_ga',
    'worker_ga',
    'review_queue_ga',
    'provider_ga',
    'calibration_ga',
    'roadmap_extension',
)
ALL_STAGES = tuple(sorted(DEFAULT_STAGES))
POSTGRES_STAGES = {'postgres_soak', 'postgres_ga'}


@dataclass(frozen=True, slots=True)
class StageSpec:
    name: str
    description: str
    command: list[str]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Run or print a Linux validation command pack for the distillation project.',
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
        help='Validation stages to include. Defaults to full command pack.',
    )
    parser.add_argument(
        '--coverage-fail-under',
        type=float,
        default=50.0,
        help='Coverage fail-under passed to scripts/ci.py.',
    )
    parser.add_argument(
        '--no-coverage',
        action='store_true',
        help='Forward --no-coverage to scripts/ci.py.',
    )
    parser.add_argument(
        '--doc-sync-output',
        default=str(DEFAULT_DOC_SYNC_OUTPUT),
        help='Doc sync report output path.',
    )
    parser.add_argument(
        '--quality-manifest',
        default=str(DEFAULT_QUALITY_MANIFEST),
        help='Quality regression manifest path.',
    )
    parser.add_argument(
        '--quality-output',
        default=str(DEFAULT_QUALITY_OUTPUT),
        help='Quality regression report output path.',
    )
    parser.add_argument(
        '--perf-manifest',
        default=str(DEFAULT_PERF_MANIFEST),
        help='Perf/cost regression manifest path.',
    )
    parser.add_argument(
        '--perf-output',
        default=str(DEFAULT_PERF_OUTPUT),
        help='Perf/cost regression report output path.',
    )
    parser.add_argument(
        '--allow-regression',
        action='store_true',
        help='Do not pass --fail-on-regression to baseline scripts.',
    )
    parser.add_argument(
        '--container-image-tag',
        default=DEFAULT_CONTAINER_IMAGE_TAG,
        help='Container smoke stage image tag.',
    )
    parser.add_argument(
        '--container-name',
        default=DEFAULT_CONTAINER_NAME,
        help='Container smoke stage container name.',
    )
    parser.add_argument(
        '--container-host',
        default=DEFAULT_CONTAINER_HOST,
        help='Container smoke stage health-check host.',
    )
    parser.add_argument(
        '--container-port',
        type=int,
        default=DEFAULT_CONTAINER_PORT,
        help='Container smoke stage host port mapped to container 8000.',
    )
    parser.add_argument(
        '--container-timeout-seconds',
        type=float,
        default=DEFAULT_CONTAINER_TIMEOUT_SECONDS,
        help='Container smoke stage health polling timeout.',
    )
    parser.add_argument(
        '--container-interval-seconds',
        type=float,
        default=DEFAULT_CONTAINER_INTERVAL_SECONDS,
        help='Container smoke stage health polling interval.',
    )
    parser.add_argument(
        '--container-skip-build',
        action='store_true',
        help='Forward --skip-build to scripts/container_smoke.py.',
    )
    parser.add_argument(
        '--container-skip-run',
        action='store_true',
        help='Forward --skip-run to scripts/container_smoke.py.',
    )
    parser.add_argument(
        '--postgres-dsn',
        default='',
        help='Postgres DSN forwarded to postgres soak stage.',
    )
    parser.add_argument(
        '--postgres-soak-iterations',
        type=int,
        default=120,
        help='Iterations passed to scripts/pg_soak.py benchmark stage.',
    )
    parser.add_argument(
        '--postgres-soak-output',
        default=str(DEFAULT_POSTGRES_SOAK_OUTPUT),
        help='Postgres soak plan output path.',
    )
    parser.add_argument(
        '--postgres-soak-benchmark-output',
        default=str(DEFAULT_POSTGRES_SOAK_BENCHMARK_OUTPUT),
        help='Postgres soak benchmark output path.',
    )
    parser.add_argument(
        '--postgres-ga-iterations',
        type=int,
        default=120,
        help='Iterations passed to scripts/pg_ga.py benchmark stage.',
    )
    parser.add_argument(
        '--postgres-ga-output',
        default=str(DEFAULT_POSTGRES_GA_OUTPUT),
        help='Postgres GA validation stage plan output path.',
    )
    parser.add_argument(
        '--postgres-ga-benchmark-output',
        default=str(DEFAULT_POSTGRES_GA_BENCHMARK_OUTPUT),
        help='Postgres GA benchmark output path.',
    )
    parser.add_argument(
        '--allow-secondary-failures',
        action='store_true',
        help='Forward --allow-secondary-failures to postgres soak benchmark stage.',
    )
    parser.add_argument(
        '--require-postgres',
        action='store_true',
        help='Fail when Postgres stages are selected without --postgres-dsn/OMNI_TEST_POSTGRES_DSN.',
    )
    parser.add_argument(
        '--worker-ga-output',
        default=str(DEFAULT_WORKER_GA_OUTPUT),
        help='Worker GA validation stage plan output path.',
    )
    parser.add_argument(
        '--review-queue-ga-output',
        default=str(DEFAULT_REVIEW_QUEUE_GA_OUTPUT),
        help='Review-queue GA validation stage plan output path.',
    )
    parser.add_argument(
        '--provider-ga-output',
        default=str(DEFAULT_PROVIDER_GA_OUTPUT),
        help='Provider GA validation stage plan output path.',
    )
    parser.add_argument(
        '--calibration-manifest',
        default=str(DEFAULT_CALIBRATION_MANIFEST),
        help='Calibration manifest path forwarded to calibration GA stage.',
    )
    parser.add_argument(
        '--calibration-report-output',
        default=str(DEFAULT_CALIBRATION_REPORT_OUTPUT),
        help='Calibration report output path forwarded to calibration GA stage.',
    )
    parser.add_argument(
        '--calibration-margin',
        type=float,
        default=0.03,
        help='Margin forwarded to calibration GA stage.',
    )
    parser.add_argument(
        '--calibration-fail-on-mismatch',
        action='store_true',
        help='Forward --fail-on-mismatch to calibration GA stage.',
    )
    parser.add_argument(
        '--calibration-ga-output',
        default=str(DEFAULT_CALIBRATION_GA_OUTPUT),
        help='Calibration GA validation stage plan output path.',
    )
    parser.add_argument(
        '--roadmap-extension-output',
        default=str(DEFAULT_ROADMAP_EXTENSION_OUTPUT),
        help='Roadmap extension validation stage plan output path.',
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Print command pack only without running commands.',
    )
    parser.add_argument(
        '--keep-going',
        action='store_true',
        help='Continue after failed stages and summarize all failures.',
    )
    parser.add_argument(
        '--output',
        default=str(DEFAULT_PLAN_OUTPUT),
        help='Write JSON plan/report to this path. Use "-" to skip file writing.',
    )
    parser.add_argument(
        '--print-json',
        action='store_true',
        help='Print JSON plan/report to stdout.',
    )
    return parser.parse_args()


def _split_python_command(raw: str) -> list[str]:
    parts = shlex.split(raw, posix=os.name != 'nt')
    if not parts:
        raise ValueError('Empty --python command.')
    return parts


def _build_stage_map(args: argparse.Namespace, *, python_cmd: list[str]) -> dict[str, StageSpec]:
    ci_command = [
        *python_cmd,
        'scripts/ci.py',
        '--python',
        str(args.python),
        '--coverage-fail-under',
        str(args.coverage_fail_under),
    ]
    if args.no_coverage:
        ci_command.append('--no-coverage')
    if args.keep_going:
        ci_command.append('--keep-going')
    ci_command.append('--isolate-test-files')

    doc_sync_command = [
        *python_cmd,
        'scripts/doc_sync.py',
        '--output',
        str(Path(args.doc_sync_output).resolve()),
    ]

    quality_command = [
        *python_cmd,
        'scripts/quality_regression.py',
        '--manifest',
        str(Path(args.quality_manifest).resolve()),
        '--output',
        str(Path(args.quality_output).resolve()),
    ]
    perf_command = [
        *python_cmd,
        'scripts/perf_baseline.py',
        '--manifest',
        str(Path(args.perf_manifest).resolve()),
        '--output',
        str(Path(args.perf_output).resolve()),
    ]
    if not args.allow_regression:
        quality_command.append('--fail-on-regression')
        perf_command.append('--fail-on-regression')

    container_smoke_command = [
        *python_cmd,
        'scripts/container_smoke.py',
        '--image-tag',
        str(args.container_image_tag),
        '--container-name',
        str(args.container_name),
        '--host',
        str(args.container_host),
        '--port',
        str(int(args.container_port)),
        '--timeout-seconds',
        str(float(args.container_timeout_seconds)),
        '--interval-seconds',
        str(float(args.container_interval_seconds)),
    ]
    if args.container_skip_build:
        container_smoke_command.append('--skip-build')
    if args.container_skip_run:
        container_smoke_command.append('--skip-run')

    postgres_soak_command = [
        *python_cmd,
        'scripts/pg_soak.py',
        '--python',
        str(args.python),
        '--benchmark-iterations',
        str(int(args.postgres_soak_iterations)),
        '--benchmark-output',
        str(Path(args.postgres_soak_benchmark_output).resolve()),
        '--output',
        str(Path(args.postgres_soak_output).resolve()),
    ]
    explicit_postgres_dsn = str(args.postgres_dsn or '').strip()
    if explicit_postgres_dsn:
        postgres_dsn = explicit_postgres_dsn
        postgres_soak_command.extend(['--postgres-dsn', postgres_dsn])
    else:
        postgres_dsn = str(os.getenv('OMNI_TEST_POSTGRES_DSN', '')).strip()
    if args.allow_secondary_failures:
        postgres_soak_command.append('--allow-secondary-failures')

    postgres_ga_command = [
        *python_cmd,
        'scripts/pg_ga.py',
        '--python',
        str(args.python),
        '--benchmark-iterations',
        str(int(args.postgres_ga_iterations)),
        '--benchmark-output',
        str(Path(args.postgres_ga_benchmark_output).resolve()),
        '--output',
        str(Path(args.postgres_ga_output).resolve()),
    ]
    if explicit_postgres_dsn:
        postgres_ga_command.extend(['--postgres-dsn', postgres_dsn])
    if args.allow_secondary_failures:
        postgres_ga_command.append('--allow-secondary-failures')

    worker_ga_command = [
        *python_cmd,
        'scripts/worker_ga.py',
        '--python',
        str(args.python),
        '--output',
        str(Path(args.worker_ga_output).resolve()),
    ]
    review_queue_ga_command = [
        *python_cmd,
        'scripts/ga_review_queue.py',
        '--python',
        str(args.python),
        '--output',
        str(Path(args.review_queue_ga_output).resolve()),
    ]
    provider_ga_command = [
        *python_cmd,
        'scripts/provider_ga.py',
        '--python',
        str(args.python),
        '--output',
        str(Path(args.provider_ga_output).resolve()),
    ]
    calibration_ga_command = [
        *python_cmd,
        'scripts/ga_calibration.py',
        '--python',
        str(args.python),
        '--manifest',
        str(Path(args.calibration_manifest).resolve()),
        '--calibration-report-output',
        str(Path(args.calibration_report_output).resolve()),
        '--margin',
        str(float(args.calibration_margin)),
        '--output',
        str(Path(args.calibration_ga_output).resolve()),
    ]
    if args.calibration_fail_on_mismatch:
        calibration_ga_command.append('--fail-on-mismatch')

    roadmap_extension_command = [
        *python_cmd,
        'scripts/roadmap_ext.py',
        '--python',
        str(args.python),
        '--output',
        str(Path(args.roadmap_extension_output).resolve()),
    ]

    return {
        'ci': StageSpec(
            name='ci',
            description='Run full unittest + TP suite with coverage gate.',
            command=ci_command,
        ),
        'container_smoke': StageSpec(
            name='container_smoke',
            description='Build/start API container and poll /healthz smoke gate.',
            command=container_smoke_command,
        ),
        'doc_sync': StageSpec(
            name='doc_sync',
            description='Validate README/API/CLI/worker/testing docs contract.',
            command=doc_sync_command,
        ),
        'quality_regression': StageSpec(
            name='quality_regression',
            description='Compare quality baseline (traceability + reviewer edit distance).',
            command=quality_command,
        ),
        'perf_cost_baseline': StageSpec(
            name='perf_cost_baseline',
            description='Compare perf/cost baseline (latency + tokens + provider calls).',
            command=perf_command,
        ),
        'postgres_soak': StageSpec(
            name='postgres_soak',
            description='Run Postgres soak pack (TP pg cases + review queue + dual-write benchmark).',
            command=postgres_soak_command,
        ),
        'postgres_ga': StageSpec(
            name='postgres_ga',
            description='Run Postgres GA-hardening pack (repository + dual-write contracts and benchmark).',
            command=postgres_ga_command,
        ),
        'worker_ga': StageSpec(
            name='worker_ga',
            description='Run worker GA-hardening command pack (corpus + retry + idempotency + claim-lock).',
            command=worker_ga_command,
        ),
        'review_queue_ga': StageSpec(
            name='review_queue_ga',
            description='Run review-queue GA-hardening command pack (queue transitions + feedback consumer).',
            command=review_queue_ga_command,
        ),
        'provider_ga': StageSpec(
            name='provider_ga',
            description='Run provider GA-hardening command pack (retry + circuit-breaker + audit footprint).',
            command=provider_ga_command,
        ),
        'calibration_ga': StageSpec(
            name='calibration_ga',
            description='Run calibration GA-hardening command pack (threshold contract + tuning report).',
            command=calibration_ga_command,
        ),
        'roadmap_extension': StageSpec(
            name='roadmap_extension',
            description='Run roadmap-extension command pack (retrieval + lifecycle + publication + review-queue surface).',
            command=roadmap_extension_command,
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


def _filter_stage_specs(args: argparse.Namespace, stage_specs: list[StageSpec]) -> list[StageSpec]:
    postgres_dsn = str(args.postgres_dsn or '').strip() or str(os.getenv('OMNI_TEST_POSTGRES_DSN', '')).strip()
    if postgres_dsn or args.require_postgres:
        return stage_specs
    filtered = [stage for stage in stage_specs if stage.name not in POSTGRES_STAGES]
    skipped = [stage.name for stage in stage_specs if stage.name in POSTGRES_STAGES]
    if skipped:
        print(
            'Skipping Postgres stages without DSN: %s. Pass --postgres-dsn or --require-postgres to enforce them.'
            % ', '.join(skipped)
        )
    return filtered


def _print_plan(stage_specs: list[StageSpec]) -> None:
    print('Selected stages: %s' % ', '.join(stage.name for stage in stage_specs))
    for stage in stage_specs:
        print('Stage: %s' % stage.name)
        print('Description: %s' % stage.description)
        print('Command: %s' % ' '.join(stage.command))


def _write_plan(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def _stage_environment(*, include_postgres_dsn: bool, postgres_dsn: str) -> dict[str, str]:
    env = os.environ.copy()
    env.pop('OMNI_TEST_POSTGRES_DSN', None)
    if include_postgres_dsn and postgres_dsn:
        env['OMNI_TEST_POSTGRES_DSN'] = postgres_dsn
    return env


def _run_stages(stage_specs: list[StageSpec], *, keep_going: bool = False, postgres_dsn: str = '') -> int:
    failures: list[tuple[str, int]] = []
    for stage in stage_specs:
        print('Running stage: %s' % stage.name)
        stage_env = _stage_environment(
            include_postgres_dsn=stage.name in POSTGRES_STAGES,
            postgres_dsn=postgres_dsn,
        )
        completed = subprocess.run(stage.command, check=False, env=stage_env)
        if completed.returncode != 0:
            failures.append((stage.name, completed.returncode))
            print(
                'Stage failed: %s (exit=%s)' % (stage.name, completed.returncode),
                file=sys.stderr,
            )
            if not keep_going:
                return completed.returncode
    if failures:
        print('Stage failures summary:', file=sys.stderr)
        for stage_name, exit_code in failures:
            print('- %s (exit=%s)' % (stage_name, exit_code), file=sys.stderr)
        return failures[0][1]
    return 0


def main() -> int:
    args = _parse_args()
    if not args.stages:
        print('No stages selected. Use --stages with at least one value.', file=sys.stderr)
        return 2

    try:
        python_cmd = _split_python_command(args.python)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    stage_map = _build_stage_map(args, python_cmd=python_cmd)
    stage_specs = _filter_stage_specs(args, [stage_map[name] for name in args.stages])
    if not stage_specs:
        print('No runnable stages selected after environment filtering.', file=sys.stderr)
        return 2
    _print_plan(stage_specs)

    plan_payload = _build_plan(stage_specs)
    output_value = str(args.output or '').strip()
    if output_value and output_value != '-':
        output_path = Path(output_value).resolve()
        _write_plan(output_path, plan_payload)
        print('Plan written: %s' % output_path)

    if args.print_json:
        print(json.dumps(plan_payload, ensure_ascii=False, indent=2))

    if args.dry_run:
        return 0
    return _run_stages(
        stage_specs,
        keep_going=bool(args.keep_going),
        postgres_dsn=str(args.postgres_dsn or '').strip() or str(os.getenv('OMNI_TEST_POSTGRES_DSN', '')).strip(),
    )


if __name__ == '__main__':
    raise SystemExit(main())
