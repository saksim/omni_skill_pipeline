from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / 'scripts' / 'pg_ga.py'


class PostgresGaValidationScriptTests(unittest.TestCase):
    def setUp(self) -> None:
        self._postgres_dsn = os.environ.pop('OMNI_TEST_POSTGRES_DSN', None)

    def tearDown(self) -> None:
        if self._postgres_dsn is not None:
            os.environ['OMNI_TEST_POSTGRES_DSN'] = self._postgres_dsn

    def test_script_dry_run_emits_default_postgres_ga_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / 'postgres-ga-plan.json'
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--python',
                    'python3',
                    '--dry-run',
                    '--output',
                    str(output_path),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn(
                'Selected stages: postgres_repository_contract, postgres_repository_integration, dual_write_contract, dual_write_integration, dual_write_benchmark',
                completed.stdout,
            )
            self.assertIn(
                'tests.test_postgres_repository.PostgresRepositoryTests',
                completed.stdout,
            )
            self.assertIn(
                'tests.test_postgres_repository_integration.PostgresRepositoryIntegrationTests',
                completed.stdout,
            )
            self.assertIn('tests.test_dual_write_repository.DualWriteRepositoryTests', completed.stdout)
            self.assertIn(
                'tests.test_dual_write_repository_integration.DualWriteRepositoryIntegrationTests',
                completed.stdout,
            )
            self.assertIn('scripts/bench_dual_write.py', completed.stdout)

            report = json.loads(output_path.read_text(encoding='utf-8'))
            self.assertEqual(report.get('stage_count'), 5)
            self.assertEqual(
                [item.get('name') for item in report.get('stages', [])],
                [
                    'postgres_repository_contract',
                    'postgres_repository_integration',
                    'dual_write_contract',
                    'dual_write_integration',
                    'dual_write_benchmark',
                ],
            )

    def test_script_respects_stage_selection_and_benchmark_options(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            benchmark_output = Path(tmp_dir) / 'postgres-ga-benchmark.json'
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--python',
                    'python3',
                    '--stages',
                    'dual_write_contract',
                    'dual_write_benchmark',
                    '--benchmark-iterations',
                    '33',
                    '--postgres-dsn',
                    'postgresql://validator',
                    '--benchmark-output',
                    str(benchmark_output),
                    '--allow-secondary-failures',
                    '--dry-run',
                    '--output',
                    '-',
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Selected stages: dual_write_contract, dual_write_benchmark', completed.stdout)
            self.assertNotIn('PostgresRepositoryIntegrationTests', completed.stdout)
            self.assertIn('DualWriteRepositoryTests', completed.stdout)
            self.assertIn('scripts/bench_dual_write.py', completed.stdout)
            self.assertIn('--iterations 33', completed.stdout)
            self.assertIn('--postgres-dsn postgresql://validator', completed.stdout)
            self.assertIn('--output %s' % str(benchmark_output.resolve()), completed.stdout)
            self.assertIn('--allow-secondary-failures', completed.stdout)

    def test_script_requires_postgres_dsn_for_runtime_stages(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                '--python',
                'python3',
                '--stages',
                'dual_write_integration',
                '--output',
                '-',
            ],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn('Postgres DSN is required', completed.stderr)


if __name__ == '__main__':
    unittest.main()
