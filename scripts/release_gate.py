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
DEFAULT_CALIBRATION_MANIFEST = (
    REPO_ROOT / 'docs' / 'working' / 'status' / 'baselines' / 'e7-calibration-manifest.json'
)
DEFAULT_CALIBRATION_REPORT_OUTPUT = (
    REPO_ROOT / 'docs' / 'working' / 'status' / 'baselines' / 'e7-calibration-report.json'
)
DEFAULT_BETA_SUITE_OUTPUT = (
    REPO_ROOT / 'docs' / 'working' / 'status' / 'baselines' / 'e13-release-gate-beta-suite-plan.json'
)
DEFAULT_GA_SUITE_OUTPUT = (
    REPO_ROOT / 'docs' / 'working' / 'status' / 'baselines' / 'e13-release-gate-ga-suite-plan.json'
)
DEFAULT_ROADMAP_SUITE_OUTPUT = (
    REPO_ROOT / 'docs' / 'working' / 'status' / 'baselines' / 'e13-release-gate-roadmap-suite-plan.json'
)
DEFAULT_PLAN_OUTPUT = (
    REPO_ROOT / 'docs' / 'working' / 'status' / 'baselines' / 'e13-release-gate-validation-plan.json'
)
DEFAULT_CONTAINER_IMAGE_TAG = 'omni-skill-pipeline:beta'
DEFAULT_CONTAINER_NAME = 'omni-skill-pipeline-smoke'
DEFAULT_CONTAINER_HOST = '127.0.0.1'
DEFAULT_CONTAINER_PORT = 18000
DEFAULT_CONTAINER_TIMEOUT_SECONDS = 30.0
DEFAULT_CONTAINER_INTERVAL_SECONDS = 1.0
DEFAULT_STAGES = (
    'beta_gate',
    'ga_gate',
    'roadmap_gate',
)
ALL_STAGES = tuple(DEFAULT_STAGES)


@dataclass(frozen=True, slots=True)
class StageSpec:
    name: str
    description: str
    command: list[str]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Run or print release-gate command packs for Linux validation.',
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
        help='Validation stages to include. Defaults to beta+ga+roadmap release gate packs.',
    )
    parser.add_argument(
        '--coverage-fail-under',
        type=float,
        default=50.0,
        help='Coverage fail-under forwarded into beta gate.',
    )
    parser.add_argument(
        '--no-coverage',
        action='store_true',
        help='Forward --no-coverage into beta gate.',
    )
    parser.add_argument(
        '--allow-regression',
        action='store_true',
        help='Forward --allow-regression into beta gate baseline checks.',
    )
    parser.add_argument(
        '--container-image-tag',
        default=DEFAULT_CONTAINER_IMAGE_TAG,
        help='Container smoke image tag for beta gate.',
    )
    parser.add_argument(
        '--container-name',
        default=DEFAULT_CONTAINER_NAME,
        help='Container smoke container name for beta gate.',
    )
    parser.add_argument(
        '--container-host',
        default=DEFAULT_CONTAINER_HOST,
        help='Container smoke host for beta gate.',
    )
    parser.add_argument(
        '--container-port',
        type=int,
        default=DEFAULT_CONTAINER_PORT,
        help='Container smoke host port for beta gate.',
    )
    parser.add_argument(
        '--container-timeout-seconds',
        type=float,
        default=DEFAULT_CONTAINER_TIMEOUT_SECONDS,
        help='Container smoke timeout for beta gate.',
    )
    parser.add_argument(
        '--container-interval-seconds',
        type=float,
        default=DEFAULT_CONTAINER_INTERVAL_SECONDS,
        help='Container smoke polling interval for beta gate.',
    )
    parser.add_argument(
        '--container-skip-build',
        action='store_true',
        help='Forward --container-skip-build into beta gate.',
    )
    parser.add_argument(
        '--container-skip-run',
        action='store_true',
        help='Forward --container-skip-run into beta gate.',
    )
    parser.add_argument(
        '--postgres-dsn',
        default='',
        help='Postgres DSN forwarded into ga gate.',
    )
    parser.add_argument(
        '--postgres-soak-iterations',
        type=int,
        default=120,
        help='Postgres soak benchmark iterations forwarded into ga gate.',
    )
    parser.add_argument(
        '--postgres-ga-iterations',
        type=int,
        default=120,
        help='Postgres GA benchmark iterations forwarded into ga gate.',
    )
    parser.add_argument(
        '--allow-secondary-failures',
        action='store_true',
        help='Forward --allow-secondary-failures into ga gate.',
    )
    parser.add_argument(
        '--calibration-manifest',
        default=str(DEFAULT_CALIBRATION_MANIFEST),
        help='Calibration manifest path forwarded into ga gate.',
    )
    parser.add_argument(
        '--calibration-report-output',
        default=str(DEFAULT_CALIBRATION_REPORT_OUTPUT),
        help='Calibration report output path forwarded into ga gate.',
    )
    parser.add_argument(
        '--calibration-margin',
        type=float,
        default=0.03,
        help='Calibration margin forwarded into ga gate.',
    )
    parser.add_argument(
        '--calibration-fail-on-mismatch',
        action='store_true',
        help='Forward --calibration-fail-on-mismatch into ga gate.',
    )
    parser.add_argument(
        '--beta-suite-output',
        default=str(DEFAULT_BETA_SUITE_OUTPUT),
        help='Nested Linux suite plan output for beta gate.',
    )
    parser.add_argument(
        '--ga-suite-output',
        default=str(DEFAULT_GA_SUITE_OUTPUT),
        help='Nested Linux suite plan output for ga gate.',
    )
    parser.add_argument(
        '--roadmap-suite-output',
        default=str(DEFAULT_ROADMAP_SUITE_OUTPUT),
        help='Nested Linux suite plan output for roadmap gate.',
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Print command pack only without running commands.',
    )
    parser.add_argument(
        '--keep-going',
        action='store_true',
        help='Continue after failed release-gate stages and summarize all failures.',
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
    beta_command = [
        *python_cmd,
        'scripts/linux_validate.py',
        '--python',
        str(args.python),
        '--stages',
        'ci',
        'container_smoke',
        'doc_sync',
        'quality_regression',
        'perf_cost_baseline',
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
        '--output',
        str(Path(args.beta_suite_output).resolve()),
    ]
    if args.no_coverage:
        beta_command.append('--no-coverage')
    if args.allow_regression:
        beta_command.append('--allow-regression')
    if args.keep_going:
        beta_command.append('--keep-going')
    if args.container_skip_build:
        beta_command.append('--container-skip-build')
    if args.container_skip_run:
        beta_command.append('--container-skip-run')

    ga_command = [
        *python_cmd,
        'scripts/linux_validate.py',
        '--python',
        str(args.python),
        '--stages',
        'postgres_soak',
        'postgres_ga',
        'worker_ga',
        'review_queue_ga',
        'provider_ga',
        'calibration_ga',
        '--require-postgres',
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
        '--output',
        str(Path(args.ga_suite_output).resolve()),
    ]
    explicit_postgres_dsn = str(args.postgres_dsn or '').strip()
    if explicit_postgres_dsn:
        postgres_dsn = explicit_postgres_dsn
        ga_command.extend(['--postgres-dsn', postgres_dsn])
    else:
        postgres_dsn = str(os.getenv('OMNI_TEST_POSTGRES_DSN', '')).strip()
    if args.allow_secondary_failures:
        ga_command.append('--allow-secondary-failures')
    if args.calibration_fail_on_mismatch:
        ga_command.append('--calibration-fail-on-mismatch')
    if args.keep_going:
        ga_command.append('--keep-going')

    roadmap_command = [
        *python_cmd,
        'scripts/linux_validate.py',
        '--python',
        str(args.python),
        '--stages',
        'roadmap_extension',
        '--output',
        str(Path(args.roadmap_suite_output).resolve()),
    ]

    return {
        'beta_gate': StageSpec(
            name='beta_gate',
            description='Run beta release gate pack (ci + container smoke + doc sync + quality/perf baselines).',
            command=beta_command,
        ),
        'ga_gate': StageSpec(
            name='ga_gate',
            description='Run GA release gate pack (postgres soak/ga + worker/provider/review/calibration hardening).',
            command=ga_command,
        ),
        'roadmap_gate': StageSpec(
            name='roadmap_gate',
            description='Run roadmap extension gate pack (LC-R-34~37 validation surface).',
            command=roadmap_command,
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
            include_postgres_dsn=stage.name == 'ga_gate',
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
    stage_specs = [stage_map[name] for name in args.stages]
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
