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
DEFAULT_BENCHMARK_OUTPUT = (
    REPO_ROOT / 'docs' / 'working' / 'status' / 'baselines' / 'e13-postgres-soak-benchmark-report.json'
)
DEFAULT_PLAN_OUTPUT = (
    REPO_ROOT / 'docs' / 'working' / 'status' / 'baselines' / 'e13-postgres-soak-plan.json'
)
DEFAULT_STAGES = ('tp_postgres', 'review_queue', 'dual_write_benchmark')
ALL_STAGES = tuple(DEFAULT_STAGES)
REPORT_SCHEMA_VERSION = 'postgres_soak_validation.v1'
POSTGRES_REQUIRED_STAGES = {'tp_postgres', 'dual_write_benchmark'}


@dataclass(frozen=True, slots=True)
class StageSpec:
    name: str
    description: str
    command: list[str]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Run or print a PostgreSQL soak validation command pack for Linux.',
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
        help='Validation stages to include. Defaults to full Postgres soak pack.',
    )
    parser.add_argument(
        '--postgres-dsn',
        default='',
        help='Postgres DSN for integration/benchmark stages. Defaults to OMNI_TEST_POSTGRES_DSN.',
    )
    parser.add_argument(
        '--benchmark-iterations',
        type=int,
        default=120,
        help='Iterations for dual-write benchmark stage.',
    )
    parser.add_argument(
        '--benchmark-output',
        default=str(DEFAULT_BENCHMARK_OUTPUT),
        help='Benchmark report output path.',
    )
    parser.add_argument(
        '--allow-secondary-failures',
        action='store_true',
        help='Forward --allow-secondary-failures to bench_dual_write.py.',
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Print command pack only without running commands.',
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
    postgres_dsn = str(args.postgres_dsn).strip()
    benchmark_output = str(Path(args.benchmark_output).resolve())

    tp_postgres_command = [
        *python_cmd,
        'scripts/tp_tests.py',
        'TP-E8-02',
        'TP-E8-03',
        'TP-E9-03',
        '--python',
        str(args.python),
    ]
    review_queue_command = [
        *python_cmd,
        '-m',
        'unittest',
        'tests.test_review_queue_repository',
        'tests.test_review_queue_integration',
        'tests.test_api_review_queue',
    ]
    dual_write_benchmark_command = [
        *python_cmd,
        'scripts/bench_dual_write.py',
        '--iterations',
        str(int(args.benchmark_iterations)),
        '--output',
        benchmark_output,
    ]
    if postgres_dsn:
        dual_write_benchmark_command.extend(['--postgres-dsn', postgres_dsn])
    if args.allow_secondary_failures:
        dual_write_benchmark_command.append('--allow-secondary-failures')

    return {
        'tp_postgres': StageSpec(
            name='tp_postgres',
            description='Run TP-E8-02/E8-03/E9-03 mapped cases (Postgres + dual-write + lineage).',
            command=tp_postgres_command,
        ),
        'review_queue': StageSpec(
            name='review_queue',
            description='Run review queue repository/integration/API contract tests.',
            command=review_queue_command,
        ),
        'dual_write_benchmark': StageSpec(
            name='dual_write_benchmark',
            description='Run dual-write benchmark against Postgres for soak latency snapshots.',
            command=dual_write_benchmark_command,
        ),
    }


def _build_plan(stage_specs: list[StageSpec], *, postgres_dsn_provided: bool) -> dict[str, Any]:
    return {
        'schema_version': REPORT_SCHEMA_VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'execution_mode': 'pending',
        'decision': 'PENDING',
        'blocking_codes': [],
        'stage_count': len(stage_specs),
        'postgres_dsn_provided': postgres_dsn_provided,
        'stages': [
            {
                'name': stage.name,
                'description': stage.description,
                'command': stage.command,
            }
            for stage in stage_specs
        ],
        'stage_results': [],
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


def _emit_report(args: argparse.Namespace, payload: dict[str, Any]) -> None:
    output_value = str(args.output or '').strip()
    if output_value and output_value != '-':
        output_path = Path(output_value).resolve()
        _write_plan(output_path, payload)
        print('Report written: %s' % output_path)
    if args.print_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _stage_result(stage: StageSpec, *, exit_code: int, status: str) -> dict[str, Any]:
    return {
        'name': stage.name,
        'status': status,
        'exit_code': int(exit_code),
        'command': stage.command,
    }


def _validate_runtime_requirements(
    *,
    stage_specs: list[StageSpec],
    postgres_dsn: str,
    benchmark_iterations: int,
) -> int:
    if benchmark_iterations <= 0:
        print('benchmark-iterations must be > 0.', file=sys.stderr)
        return 2

    requires_postgres = any(stage.name in POSTGRES_REQUIRED_STAGES for stage in stage_specs)
    if requires_postgres and not postgres_dsn:
        print(
            'Postgres DSN is required for selected stages. Provide --postgres-dsn or set OMNI_TEST_POSTGRES_DSN.',
            file=sys.stderr,
        )
        return 2
    return 0


def _run_stages(stage_specs: list[StageSpec], *, postgres_dsn: str = '') -> tuple[int, list[dict[str, Any]]]:
    env_override = None
    if postgres_dsn:
        env_override = os.environ.copy()
        env_override['OMNI_TEST_POSTGRES_DSN'] = postgres_dsn

    results: list[dict[str, Any]] = []
    for stage in stage_specs:
        print('Running stage: %s' % stage.name)
        stage_env = env_override if stage.name in POSTGRES_REQUIRED_STAGES else None
        completed = subprocess.run(stage.command, check=False, env=stage_env)
        status = 'pass' if completed.returncode == 0 else 'fail'
        results.append(_stage_result(stage, exit_code=completed.returncode, status=status))
        if completed.returncode != 0:
            print(
                'Stage failed: %s (exit=%s)' % (stage.name, completed.returncode),
                file=sys.stderr,
            )
            return completed.returncode, results
    return 0, results


def main() -> int:
    args = _parse_args()
    if not args.stages:
        print('No stages selected. Use --stages with at least one value.', file=sys.stderr)
        return 2

    postgres_dsn = str(args.postgres_dsn or '').strip() or str(os.getenv('OMNI_TEST_POSTGRES_DSN', '')).strip()

    try:
        python_cmd = _split_python_command(args.python)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    stage_map = _build_stage_map(args, python_cmd=python_cmd)
    stage_specs = [stage_map[name] for name in args.stages]
    _print_plan(stage_specs)

    plan_payload = _build_plan(stage_specs, postgres_dsn_provided=bool(postgres_dsn))

    if args.dry_run:
        plan_payload['execution_mode'] = 'dry_run'
        plan_payload['decision'] = 'DRY_RUN'
        _emit_report(args, plan_payload)
        return 0

    validation_code = _validate_runtime_requirements(
        stage_specs=stage_specs,
        postgres_dsn=postgres_dsn,
        benchmark_iterations=int(args.benchmark_iterations),
    )
    if validation_code != 0:
        plan_payload['execution_mode'] = 'blocked'
        plan_payload['decision'] = 'FAIL'
        plan_payload['blocking_codes'] = ['runtime_requirements_failed']
        _emit_report(args, plan_payload)
        return validation_code
    execution_code, stage_results = _run_stages(stage_specs, postgres_dsn=postgres_dsn)
    plan_payload['execution_mode'] = 'executed'
    plan_payload['decision'] = 'PASS' if execution_code == 0 else 'FAIL'
    plan_payload['stage_results'] = stage_results
    plan_payload['blocking_codes'] = [] if execution_code == 0 else ['stage_failed']
    _emit_report(args, plan_payload)
    return execution_code


if __name__ == '__main__':
    raise SystemExit(main())
