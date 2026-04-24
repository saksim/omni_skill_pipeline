from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class ContainerSmokeScriptTests(unittest.TestCase):
    def test_dry_run_outputs_expected_plan(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/run_container_smoke.py",
                "--dry-run",
                "--image-tag",
                "omni:test",
                "--container-name",
                "omni-smoke",
                "--port",
                "18080",
            ],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Plan: docker build -t omni:test .", completed.stdout)
        self.assertIn("Plan: docker run --rm -d --name omni-smoke -p 18080:8000 omni:test", completed.stdout)
        self.assertIn("Plan: poll http://127.0.0.1:18080/healthz", completed.stdout)

    def test_skip_build_and_run_returns_usage_error(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/run_container_smoke.py",
                "--skip-build",
                "--skip-run",
            ],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("No smoke actions selected.", completed.stderr)


if __name__ == "__main__":
    unittest.main()
