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
DEFAULT_PLAN_OUTPUT = (
    REPO_ROOT / 'docs' / 'working' / 'status' / 'baselines' / 'e13-postgres-ga-validation-plan.json'
)
DEFAULT_BENCHMARK_OUTPUT = (
    REPO_ROOT / 'docs' / 'working' / 'status' / 'baselines' / 'e13-postgres-ga-benchmark-report.json'
)
DEFAULT_STAGES = (
    'postgres_repository_contract',
    'postgres_repository_integration',
    'dual_write_contract',
    'dual_write_integration',
    'dual_write_benchmark',
)
ALL_STAGES = tuple(DEFAULT_STAGES)
POSTGRES_REQUIRED_STAGES = {
    'postgres_repository_integration',
    'dual_write_integration',
    'dual_write_benchmark',
}


@dataclass(frozen=True, slots=True)
class StageSpec:
    name: str
    description: str
    command: list[str]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Run or print a PostgreSQL GA-hardening validation command pack for Linux.',
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
        help='Validation stages to include. Defaults to full Postgres GA command pack.',
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
        'postgres_repository_contract': StageSpec(
            name='postgres_repository_contract',
            description='Validate Postgres repository persistence and rollback guards.',
            command=[
                *python_cmd,
                '-m',
                'unittest',
                'tests.test_postgres_repository.PostgresRepositoryTests',
            ],
        ),
        'postgres_repository_integration': StageSpec(
            name='postgres_repository_integration',
            description='Validate Postgres repository integration writes/reads on real PostgreSQL.',
            command=[
                *python_cmd,
                '-m',
                'unittest',
                'tests.test_postgres_repository_integration.PostgresRepositoryIntegrationTests',
            ],
        ),
        'dual_write_contract': StageSpec(
            name='dual_write_contract',
            description='Validate dual-write repository behavior and secondary-failure isolation.',
            command=[
                *python_cmd,
                '-m',
                'unittest',
                'tests.test_dual_write_repository.DualWriteRepositoryTests',
            ],
        ),
        'dual_write_integration': StageSpec(
            name='dual_write_integration',
            description='Validate file+postgres dual-write integration contract.',
            command=[
                *python_cmd,
                '-m',
                'unittest',
                'tests.test_dual_write_repository_integration.DualWriteRepositoryIntegrationTests',
            ],
        ),
        'dual_write_benchmark': StageSpec(
            name='dual_write_benchmark',
            description='Run dual-write benchmark against Postgres for GA latency snapshots.',
            command=dual_write_benchmark_command,
        ),
    }


def _build_plan(stage_specs: list[StageSpec], *, postgres_dsn_provided: bool) -> dict[str, Any]:
    return {
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
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


def _run_stages(stage_specs: list[StageSpec], *, postgres_dsn: str) -> int:
    env_override = None
    if postgres_dsn:
        env_override = os.environ.copy()
        env_override['OMNI_TEST_POSTGRES_DSN'] = postgres_dsn

    for stage in stage_specs:
        print('Running stage: %s' % stage.name)
        stage_env = env_override if stage.name in POSTGRES_REQUIRED_STAGES else None
        completed = subprocess.run(stage.command, check=False, env=stage_env)
        if completed.returncode != 0:
            print(
                'Stage failed: %s (exit=%s)' % (stage.name, completed.returncode),
                file=sys.stderr,
            )
            return completed.returncode
    return 0


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
    output_value = str(args.output or '').strip()
    if output_value and output_value != '-':
        output_path = Path(output_value).resolve()
        _write_plan(output_path, plan_payload)
        print('Plan written: %s' % output_path)

    if args.print_json:
        print(json.dumps(plan_payload, ensure_ascii=False, indent=2))

    if args.dry_run:
        return 0

    validation_code = _validate_runtime_requirements(
        stage_specs=stage_specs,
        postgres_dsn=postgres_dsn,
        benchmark_iterations=int(args.benchmark_iterations),
    )
    if validation_code != 0:
        return validation_code
    return _run_stages(stage_specs, postgres_dsn=postgres_dsn)


if __name__ == '__main__':
    raise SystemExit(main())
