from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / 'scripts' / 'pg_soak.py'


class PostgresSoakValidationScriptTests(unittest.TestCase):
    def setUp(self) -> None:
        self._postgres_dsn = os.environ.pop('OMNI_TEST_POSTGRES_DSN', None)

    def tearDown(self) -> None:
        if self._postgres_dsn is not None:
            os.environ['OMNI_TEST_POSTGRES_DSN'] = self._postgres_dsn

    def test_script_dry_run_emits_default_postgres_soak_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / 'postgres-soak-plan.json'
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
                'Selected stages: tp_postgres, review_queue, dual_write_benchmark',
                completed.stdout,
            )
            self.assertIn('scripts/tp_tests.py TP-E8-02 TP-E8-03 TP-E9-03', completed.stdout)
            self.assertIn('tests.test_review_queue_repository', completed.stdout)
            self.assertIn('scripts/bench_dual_write.py', completed.stdout)

            report = json.loads(output_path.read_text(encoding='utf-8'))
            self.assertEqual(report.get('stage_count'), 3)
            self.assertEqual(
                [item.get('name') for item in report.get('stages', [])],
                ['tp_postgres', 'review_queue', 'dual_write_benchmark'],
            )

    def test_script_respects_stage_selection_and_benchmark_options(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                '--python',
                'python3',
                '--stages',
                'review_queue',
                'dual_write_benchmark',
                '--benchmark-iterations',
                '42',
                '--postgres-dsn',
                'postgresql://example',
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
        self.assertIn('Selected stages: review_queue, dual_write_benchmark', completed.stdout)
        self.assertNotIn('scripts/tp_tests.py TP-E8-02 TP-E8-03 TP-E9-03', completed.stdout)
        self.assertIn('scripts/bench_dual_write.py', completed.stdout)

        benchmark_lines = [
            line
            for line in completed.stdout.splitlines()
            if 'scripts/bench_dual_write.py' in line
        ]
        self.assertTrue(benchmark_lines)
        for line in benchmark_lines:
            self.assertIn('--iterations 42', line)
            self.assertIn('--postgres-dsn postgresql://example', line)
            self.assertIn('--allow-secondary-failures', line)

    def test_script_requires_postgres_dsn_for_runtime_stages(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                '--python',
                'python3',
                '--stages',
                'dual_write_benchmark',
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
