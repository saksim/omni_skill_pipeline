from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path
from statistics import mean
from uuid import uuid4

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.models import (
    Asset,
    ContentType,
    DistillBundle,
    EvidenceUnit,
    Insight,
    InsightType,
    Modality,
    SkillDocument,
    SkillStep,
    utc_now_iso,
)
from omni_skill_pipeline.persistence import DualWriteArtifactRepository, PostgresRepository
from omni_skill_pipeline.repository import FileArtifactRepository

DEFAULT_OUTPUT_PATH = REPO_ROOT / 'docs' / 'current' / 'status' / 'baselines' / 'e8-dual-write-benchmark-report.json'
DEFAULT_DRAFT_DIR = REPO_ROOT / 'tests' / '.tmp_runtime' / 'dual_write_benchmark'
SCHEMA_SQL_PATH = REPO_ROOT / 'infra' / 'sql' / '001_init.sql'


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Measure file repository latency and optional file+postgres dual-write latency.',
    )
    parser.add_argument(
        '--iterations',
        type=int,
        default=20,
        help='Iterations per benchmark mode (default: %(default)s).',
    )
    parser.add_argument(
        '--output',
        default=str(DEFAULT_OUTPUT_PATH),
        help='JSON output path. Use "-" to skip writing report file.',
    )
    parser.add_argument(
        '--draft-dir',
        default=str(DEFAULT_DRAFT_DIR),
        help='Directory used for benchmark artifact outputs.',
    )
    parser.add_argument(
        '--postgres-dsn',
        default=os.getenv('OMNI_TEST_POSTGRES_DSN', ''),
        help='Postgres DSN used for dual-write benchmark. Defaults to OMNI_TEST_POSTGRES_DSN.',
    )
    parser.add_argument(
        '--skip-postgres',
        action='store_true',
        help='Run file-only benchmark and skip dual-write benchmark.',
    )
    parser.add_argument(
        '--allow-secondary-failures',
        action='store_true',
        help='Keep file artifacts even if secondary postgres write fails during benchmark.',
    )
    parser.add_argument(
        '--print-json',
        action='store_true',
        help='Print full benchmark report JSON to stdout.',
    )
    parser.add_argument(
        '--cleanup',
        action='store_true',
        help='Delete benchmark draft directory after run.',
    )
    return parser.parse_args(argv)


def _percentile(values: list[float], ratio: float) -> float:
    if not values:
        return 0.0
    normalized = min(1.0, max(0.0, float(ratio)))
    ordered = sorted(values)
    index = int(round((len(ordered) - 1) * normalized))
    return float(ordered[index])


def _summarize_latency(latencies_ms: list[float]) -> dict[str, float | int]:
    return {
        'count': len(latencies_ms),
        'total_ms': round(sum(latencies_ms), 3),
        'avg_ms': round(mean(latencies_ms), 3) if latencies_ms else 0.0,
        'p50_ms': round(_percentile(latencies_ms, 0.5), 3),
        'p95_ms': round(_percentile(latencies_ms, 0.95), 3),
        'min_ms': round(min(latencies_ms), 3) if latencies_ms else 0.0,
        'max_ms': round(max(latencies_ms), 3) if latencies_ms else 0.0,
    }


def _build_bundle(index: int, mode: str) -> DistillBundle:
    asset = Asset(modality=Modality.TEXT, source_uri='memory://dual-write-benchmark/%s/%s' % (mode, index))
    evidence = EvidenceUnit(
        asset_id=asset.asset_id,
        span_ref='text:line:1',
        content_type=ContentType.TEXT,
        content='Benchmark sample %s for mode %s.' % (index, mode),
    )
    insight = Insight(
        insight_type=InsightType.PROCEDURE,
        summary='Persist benchmark sample %s (%s).' % (index, mode),
        evidence_refs=[evidence.evidence_id],
    )
    skill = SkillDocument(
        name='Benchmark %s skill %s' % (mode, index),
        goal='Measure repository latency for %s mode.' % mode,
        source_modality=Modality.TEXT,
        steps=[SkillStep(step=1, action='Persist benchmark sample %s.' % index, why='latency measurement')],
        evidence_refs=[evidence.evidence_id],
    )
    return DistillBundle(
        asset=asset,
        evidence_units=[evidence],
        insights=[insight],
        skill=skill,
        skill_markdown='# Benchmark Skill\n\n- Persist benchmark sample.\n',
    )


def _run_mode(*, mode: str, repository, iterations: int) -> dict[str, object]:
    latencies_ms: list[float] = []
    first_artifacts: dict[str, str] = {}
    for index in range(iterations):
        bundle = _build_bundle(index=index, mode=mode)
        start = time.perf_counter()
        artifacts = repository.save_bundle(bundle)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        latencies_ms.append(elapsed_ms)
        if index == 0:
            first_artifacts = dict(artifacts)
    summary = _summarize_latency(latencies_ms)
    print(
        'Benchmark mode=%s iterations=%s avg_ms=%.3f p95_ms=%.3f'
        % (mode, summary['count'], summary['avg_ms'], summary['p95_ms'])
    )
    return {
        'mode': mode,
        'summary': summary,
        'first_artifacts': first_artifacts,
    }


def _write_report(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def _quote_identifier(identifier: str) -> str:
    if not identifier or not all(character.isalnum() or character == '_' for character in identifier):
        raise ValueError('Unsafe Postgres identifier: %s' % identifier)
    return '"%s"' % identifier


def _run_ddl(cursor, sql_text: str) -> None:
    for statement in sql_text.split(';'):
        normalized = statement.strip()
        if normalized:
            cursor.execute(normalized)


def _load_psycopg():
    try:
        import psycopg  # type: ignore
    except ImportError as exc:  # pragma: no cover - integration environment dependent
        raise RuntimeError('psycopg is required for Postgres dual-write benchmark.') from exc
    return psycopg


def _initialize_postgres_schema(psycopg_module, dsn: str, schema: str) -> None:
    if not SCHEMA_SQL_PATH.exists():
        raise FileNotFoundError('Postgres schema SQL not found: %s' % SCHEMA_SQL_PATH)

    schema_sql = SCHEMA_SQL_PATH.read_text(encoding='utf-8')
    quoted_schema = _quote_identifier(schema)
    with psycopg_module.connect(dsn, autocommit=True) as connection:
        with connection.cursor() as cursor:
            cursor.execute('CREATE SCHEMA %s' % quoted_schema)
            cursor.execute('SET search_path TO %s' % quoted_schema)
            _run_ddl(cursor, schema_sql)


def _drop_postgres_schema(psycopg_module, dsn: str, schema: str) -> None:
    quoted_schema = _quote_identifier(schema)
    with psycopg_module.connect(dsn, autocommit=True) as connection:
        with connection.cursor() as cursor:
            cursor.execute('DROP SCHEMA IF EXISTS %s CASCADE' % quoted_schema)


def _connect_with_schema(psycopg_module, schema: str):
    quoted_schema = _quote_identifier(schema)

    def connect(dsn: str):
        connection = psycopg_module.connect(dsn)
        with connection.cursor() as cursor:
            cursor.execute('SET search_path TO %s' % quoted_schema)
        return connection

    return connect


def main_with_args(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.iterations <= 0:
        print('iterations must be > 0', file=sys.stderr)
        return 2

    draft_dir = Path(args.draft_dir).resolve()
    output_path = None if str(args.output).strip() == '-' else Path(args.output).resolve()
    postgres_dsn = str(args.postgres_dsn).strip()
    run_postgres = (not args.skip_postgres) and bool(postgres_dsn)

    if draft_dir.exists():
        shutil.rmtree(draft_dir, ignore_errors=True)
    draft_dir.mkdir(parents=True, exist_ok=True)

    report: dict[str, object] = {
        'generated_at': utc_now_iso(),
        'iterations': int(args.iterations),
        'run_postgres': run_postgres,
        'postgres_configured': bool(postgres_dsn),
        'postgres_schema_bootstrapped': False,
        'runs': {},
    }

    psycopg_module = None
    postgres_schema = ''
    try:
        if run_postgres:
            psycopg_module = _load_psycopg()
            postgres_schema = 'omni_dual_write_benchmark_%s' % uuid4().hex[:12]
            _initialize_postgres_schema(psycopg_module, postgres_dsn, postgres_schema)
            report['postgres_schema_bootstrapped'] = True

        file_repository = FileArtifactRepository(draft_dir / 'file_only')
        file_result = _run_mode(mode='file_only', repository=file_repository, iterations=args.iterations)
        report['runs']['file_only'] = file_result

        if run_postgres:
            dual_repository = DualWriteArtifactRepository(
                primary=FileArtifactRepository(draft_dir / 'dual_write'),
                secondary=PostgresRepository(
                    postgres_dsn,
                    connect=_connect_with_schema(psycopg_module, postgres_schema),
                ),
                continue_on_secondary_error=bool(args.allow_secondary_failures),
            )
            dual_result = _run_mode(mode='dual_write', repository=dual_repository, iterations=args.iterations)
            report['runs']['dual_write'] = dual_result
        elif not args.skip_postgres:
            print('Postgres DSN is empty; dual_write mode skipped.')

        if output_path is not None:
            _write_report(output_path, report)
            print('Benchmark report written: %s' % output_path)

        if args.print_json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
    finally:
        if run_postgres and psycopg_module is not None and postgres_schema:
            _drop_postgres_schema(psycopg_module, postgres_dsn, postgres_schema)
        if args.cleanup:
            shutil.rmtree(draft_dir, ignore_errors=True)
            print('Benchmark draft directory removed: %s' % draft_dir)

    return 0


def main() -> int:
    return main_with_args()


if __name__ == '__main__':
    raise SystemExit(main())
