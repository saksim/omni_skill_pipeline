from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class ContainerSmokeScriptTests(unittest.TestCase):
    def test_dry_run_outputs_expected_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "container-smoke-report.json"
            summary_path = Path(tmp_dir) / "container-smoke-summary.md"

            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/container_smoke.py",
                    "--dry-run",
                    "--image-tag",
                    "omni:test",
                    "--container-name",
                    "omni-smoke",
                    "--port",
                    "18080",
                    "--output",
                    str(report_path),
                    "--summary-output",
                    str(summary_path),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("Plan: docker build -t omni:test .", completed.stdout)
            self.assertIn("Plan: docker run -d --name omni-smoke -p 18080:8000 omni:test", completed.stdout)
            self.assertIn("Plan: poll http://127.0.0.1:18080/healthz", completed.stdout)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report.get("schema_version"), "container_smoke.v1")
            self.assertEqual(report.get("decision"), "DRY_RUN")
            self.assertEqual(report.get("config", {}).get("health_url"), "http://127.0.0.1:18080/healthz")
            self.assertIn("Decision: `DRY_RUN`", summary_path.read_text(encoding="utf-8"))

    def test_skip_build_and_run_returns_usage_error(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/container_smoke.py",
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

    def test_missing_docker_cli_returns_clear_error(self) -> None:
        env = os.environ.copy()
        env["PATH"] = ""
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "container-smoke-report.json"

            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/container_smoke.py",
                    "--image-tag",
                    "omni:test",
                    "--container-name",
                    "omni-smoke",
                    "--port",
                    "18080",
                    "--output",
                    str(report_path),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
                env=env,
            )

            self.assertEqual(completed.returncode, 127)
            self.assertIn("Docker CLI not found in PATH", completed.stderr)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report.get("decision"), "FAIL")
            self.assertEqual(report.get("failure_stage"), "docker_cli")
            self.assertEqual(report.get("failure_category"), "docker_cli_missing")


if __name__ == "__main__":
    unittest.main()
