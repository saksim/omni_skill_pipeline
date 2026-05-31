from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "ci.py"


class CiScriptTests(unittest.TestCase):
    def test_isolate_test_files_runs_each_matching_file(self) -> None:
        command = (
            "import sys; print('ci-probe:' + ' '.join(sys.argv[1:])); "
            "raise SystemExit(6 if any(arg.endswith('test_ci_script.py') for arg in sys.argv) else 0)"
        )
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--python",
                '%s -c "%s"' % (sys.executable, command),
                "--no-coverage",
                "--keep-going",
                "--isolate-test-files",
                "--test-pattern",
                "test_ci_script.py",
                "--skip-tp-suite",
            ],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 6)
        self.assertIn("CI unittest mode: isolated files (1 files)", completed.stdout)
        self.assertIn("ci-probe:-m unittest tests", completed.stdout)
        self.assertIn("test_ci_script.py", completed.stdout)
        self.assertIn("CI failures summary:", completed.stderr)

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
        self.assertIn("ci-probe:-m unittest", completed.stdout)
        self.assertIn("ci-probe:scripts/tp_tests.py --all --python", completed.stdout)
        self.assertIn("CI failures summary:", completed.stderr)
        self.assertIn("- ", completed.stderr)

    def test_coverage_post_processing_is_skipped_without_data(self) -> None:
        command = "import sys; print('ci-probe:' + ' '.join(sys.argv[1:])); raise SystemExit(0)"
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--python",
                '%s -c "%s"' % (sys.executable, command),
                "--keep-going",
                "--isolate-test-files",
                "--test-pattern",
                "test_ci_script.py",
                "--skip-tp-suite",
            ],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertIn(
            completed.returncode,
            (0, 1),
            completed.stdout + "\n" + completed.stderr,
        )
        if completed.returncode == 1:
            self.assertIn("Coverage post-processing skipped: no coverage data files found.", completed.stderr)
            self.assertNotIn("coverage combine", completed.stdout)
            self.assertNotIn("coverage report", completed.stdout)
        else:
            self.assertNotIn("Coverage post-processing skipped: no coverage data files found.", completed.stderr)
            self.assertIn("coverage combine", completed.stdout)
            self.assertIn("coverage report", completed.stdout)

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
        self.assertIn("ci-probe:-m unittest", completed.stdout)
        self.assertNotIn("ci-probe:scripts/tp_tests.py --all --python", completed.stdout)


if __name__ == "__main__":
    unittest.main()
