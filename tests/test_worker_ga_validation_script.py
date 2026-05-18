from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / 'scripts' / 'run_worker_ga_validation.py'


class WorkerGaValidationScriptTests(unittest.TestCase):
    def test_script_dry_run_emits_default_worker_ga_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / 'worker-ga-plan.json'
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
                'Selected stages: worker_corpus, worker_retry, worker_idempotency, worker_claim_lock, worker_task_types',
                completed.stdout,
            )
            self.assertIn('tests.test_worker.WorkerCorpusIntegrationTests', completed.stdout)
            self.assertIn('tests.test_worker.WorkerRetryPolicyTests', completed.stdout)
            self.assertIn('tests.test_worker.WorkerIdempotencyTests', completed.stdout)
            self.assertIn('tests.test_worker.WorkerConcurrencyClaimTests', completed.stdout)
            self.assertIn('tests.test_worker.WorkerTaskTypeUpgradeTests', completed.stdout)

            report = json.loads(output_path.read_text(encoding='utf-8'))
            self.assertEqual(report.get('stage_count'), 5)
            self.assertEqual(
                [item.get('name') for item in report.get('stages', [])],
                [
                    'worker_corpus',
                    'worker_retry',
                    'worker_idempotency',
                    'worker_claim_lock',
                    'worker_task_types',
                ],
            )

    def test_script_respects_stage_selection(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                '--python',
                'python3',
                '--stages',
                'worker_retry',
                'worker_claim_lock',
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
        self.assertIn('Selected stages: worker_retry, worker_claim_lock', completed.stdout)
        self.assertIn('tests.test_worker.WorkerRetryPolicyTests', completed.stdout)
        self.assertIn('tests.test_worker.WorkerConcurrencyClaimTests', completed.stdout)
        self.assertNotIn('tests.test_worker.WorkerCorpusIntegrationTests', completed.stdout)
        self.assertNotIn('tests.test_worker.WorkerIdempotencyTests', completed.stdout)
        self.assertNotIn('tests.test_worker.WorkerTaskTypeUpgradeTests', completed.stdout)


if __name__ == '__main__':
    unittest.main()
