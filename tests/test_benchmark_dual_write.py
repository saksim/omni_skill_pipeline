from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / 'scripts' / 'benchmark_dual_write.py'


class BenchmarkDualWriteScriptTests(unittest.TestCase):
    def test_script_smoke_runs_file_only_and_writes_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / 'benchmark-report.json'
            draft_dir = Path(tmp_dir) / 'drafts'
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--iterations',
                    '3',
                    '--skip-postgres',
                    '--output',
                    str(output_path),
                    '--draft-dir',
                    str(draft_dir),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Benchmark mode=file_only', completed.stdout)
            self.assertIn('Benchmark report written:', completed.stdout)
            payload = json.loads(output_path.read_text(encoding='utf-8'))
            self.assertEqual(payload.get('iterations'), 3)
            self.assertIn('file_only', payload.get('runs', {}))
            self.assertNotIn('dual_write', payload.get('runs', {}))
            self.assertEqual(payload['runs']['file_only']['summary']['count'], 3)

    def test_script_rejects_non_positive_iterations(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                '--iterations',
                '0',
                '--skip-postgres',
                '--output',
                '-',
            ],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn('iterations must be > 0', completed.stderr)


if __name__ == '__main__':
    unittest.main()
