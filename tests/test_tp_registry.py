from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class TPRegistryScriptTests(unittest.TestCase):
    def test_list_command_exposes_known_work_orders(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/run_tp_tests.py", "--list"],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("TP-E4-01", completed.stdout)
        self.assertIn("TP-E6-02", completed.stdout)
        self.assertIn("TP-E13-01", completed.stdout)
        self.assertIn("TP-E13-02", completed.stdout)
        self.assertIn("TP-E13-03", completed.stdout)
        self.assertIn("TP-E13-04", completed.stdout)
        self.assertIn("TP-E13-05", completed.stdout)

    def test_all_dry_run_builds_unittest_command(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/run_tp_tests.py", "--all", "--dry-run", "--python", sys.executable],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Selected TP IDs:", completed.stdout)
        self.assertIn("Command:", completed.stdout)
        self.assertIn("-m unittest", completed.stdout)


if __name__ == "__main__":
    unittest.main()
