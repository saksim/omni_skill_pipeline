from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / 'scripts' / 'postgres_readiness.py'


PG_GA_STAGES = [
    'postgres_repository_contract',
    'postgres_repository_integration',
    'dual_write_contract',
    'dual_write_integration',
    'dual_write_benchmark',
]
PG_SOAK_STAGES = ['tp_postgres', 'review_queue', 'dual_write_benchmark']


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def _execution_report(schema_version: str, stages: list[str], *, decision: str = 'PASS') -> dict:
    execution_mode = 'executed' if decision == 'PASS' else 'dry_run'
    return {
        'schema_version': schema_version,
        'generated_at_utc': '2026-06-23T00:00:00+00:00',
        'execution_mode': execution_mode,
        'decision': decision,
        'blocking_codes': [],
        'stage_count': len(stages),
        'postgres_dsn_provided': True,
        'stages': [
            {
                'name': stage,
                'description': 'test stage',
                'command': ['python', '-m', 'unittest', stage],
            }
            for stage in stages
        ],
        'stage_results': [
            {
                'name': stage,
                'status': 'pass',
                'exit_code': 0,
                'command': ['python', '-m', 'unittest', stage],
            }
            for stage in stages
        ],
    }


def _benchmark_report(iterations: int = 120, *, run_postgres: bool = True) -> dict:
    return {
        'generated_at': '2026-06-23T00:00:00Z',
        'iterations': iterations,
        'run_postgres': run_postgres,
        'postgres_configured': run_postgres,
        'postgres_schema_bootstrapped': run_postgres,
        'runs': {
            'file_only': {'summary': {'count': iterations}},
            'dual_write': {'summary': {'count': iterations}},
        },
    }


def _operations_report() -> dict:
    return {
        'schema_version': 'operations_readiness.v1',
        'generated_at_utc': '2026-06-23T00:00:00Z',
        'overall_status': 'pass',
        'checks': [
            {'id': 'production_ops_runbook_contract', 'status': 'pass'},
        ],
    }


class PostgresReadinessScriptTests(unittest.TestCase):
    def _write_ready_evidence(self, tmp_dir: Path) -> dict[str, Path]:
        paths = {
            'ga': tmp_dir / 'pg-ga.json',
            'soak': tmp_dir / 'pg-soak.json',
            'benchmark': tmp_dir / 'benchmark.json',
            'ops': tmp_dir / 'ops.json',
            'output': tmp_dir / 'postgres-readiness.json',
            'summary': tmp_dir / 'postgres-readiness.md',
        }
        _write_json(paths['ga'], _execution_report('postgres_ga_validation.v1', PG_GA_STAGES))
        _write_json(paths['soak'], _execution_report('postgres_soak_validation.v1', PG_SOAK_STAGES))
        _write_json(paths['benchmark'], _benchmark_report())
        _write_json(paths['ops'], _operations_report())
        return paths

    def test_script_passes_complete_postgres_readiness_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = self._write_ready_evidence(Path(tmp))
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--pg-ga-report',
                    str(paths['ga']),
                    '--pg-soak-report',
                    str(paths['soak']),
                    '--benchmark-report',
                    str(paths['benchmark']),
                    '--operations-readiness-report',
                    str(paths['ops']),
                    '--min-benchmark-iterations',
                    '120',
                    '--output',
                    str(paths['output']),
                    '--summary-output',
                    str(paths['summary']),
                    '--fail-on-blocked',
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            report = json.loads(paths['output'].read_text(encoding='utf-8'))
            self.assertEqual(report.get('schema_version'), 'postgres_readiness.v1')
            self.assertEqual(report.get('status'), 'POSTGRES_READINESS_READY')
            self.assertEqual(report.get('fail_count'), 0)
            self.assertIn('Status: `POSTGRES_READINESS_READY`', paths['summary'].read_text(encoding='utf-8'))

    def test_script_blocks_dry_run_pg_ga_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = self._write_ready_evidence(Path(tmp))
            _write_json(paths['ga'], _execution_report('postgres_ga_validation.v1', PG_GA_STAGES, decision='DRY_RUN'))
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--pg-ga-report',
                    str(paths['ga']),
                    '--pg-soak-report',
                    str(paths['soak']),
                    '--benchmark-report',
                    str(paths['benchmark']),
                    '--operations-readiness-report',
                    str(paths['ops']),
                    '--output',
                    str(paths['output']),
                    '--summary-output',
                    '-',
                    '--fail-on-blocked',
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1)
            report = json.loads(paths['output'].read_text(encoding='utf-8'))
            self.assertEqual(report.get('status'), 'POSTGRES_READINESS_BLOCKED')
            self.assertIn('postgres_ga_not_executed', report.get('blocking_codes', []))
            self.assertIn('postgres_ga_decision_not_pass', report.get('blocking_codes', []))

    def test_script_blocks_benchmark_without_real_postgres_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = self._write_ready_evidence(Path(tmp))
            _write_json(paths['benchmark'], _benchmark_report(iterations=3, run_postgres=False))
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--pg-ga-report',
                    str(paths['ga']),
                    '--pg-soak-report',
                    str(paths['soak']),
                    '--benchmark-report',
                    str(paths['benchmark']),
                    '--operations-readiness-report',
                    str(paths['ops']),
                    '--min-benchmark-iterations',
                    '120',
                    '--output',
                    str(paths['output']),
                    '--summary-output',
                    '-',
                    '--fail-on-blocked',
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1)
            report = json.loads(paths['output'].read_text(encoding='utf-8'))
            self.assertIn('dual_write_benchmark_postgres_not_run', report.get('blocking_codes', []))
            self.assertIn('dual_write_benchmark_iteration_count_too_low', report.get('blocking_codes', []))


if __name__ == '__main__':
    unittest.main()
