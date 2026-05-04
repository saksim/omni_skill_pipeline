from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "run_ci.py"


class CiScriptTests(unittest.TestCase):
    def test_keep_going_runs_tp_suite_after_full_suite_failure(self) -> None:
        command = (
            "import sys; print('ci-probe:' + ' '.join(sys.argv[1:])); "
            "raise SystemExit(6 if 'unittest' in sys.argv else 0)"
        )
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--python",
                '%s -c "%s"' % (sys.executable, command),
                "--no-coverage",
                "--keep-going",
            ],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 6)
        self.assertIn("ci-probe:-m unittest discover -s tests -p test_*.py", completed.stdout)
        self.assertIn("ci-probe:scripts/run_tp_tests.py --all --python", completed.stdout)
        self.assertIn("CI failures summary:", completed.stderr)
        self.assertIn("- ", completed.stderr)

    def test_default_mode_still_fails_fast(self) -> None:
        command = (
            "import sys; print('ci-probe:' + ' '.join(sys.argv[1:])); "
            "raise SystemExit(6 if 'unittest' in sys.argv else 0)"
        )
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--python",
                '%s -c "%s"' % (sys.executable, command),
                "--no-coverage",
            ],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 6)
        self.assertIn("ci-probe:-m unittest discover -s tests -p test_*.py", completed.stdout)
        self.assertNotIn("ci-probe:scripts/run_tp_tests.py --all --python", completed.stdout)


if __name__ == "__main__":
    unittest.main()
