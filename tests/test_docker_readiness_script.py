from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "docker_readiness.py"


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _live_evidence(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": "docker_live_evidence.v1",
        "status": "pass",
        "image_build_status": "pass",
        "image_size_status": "pass",
        "cli_smoke_status": "pass",
        "container_run_status": "pass",
        "healthz_status": "pass",
        "logs_collected_status": "pass",
        "cleanup_status": "pass",
        "dry_run": False,
        "skip_build": False,
        "skip_run": False,
        "image_ref": "omni-skill-pipeline:ci-test",
        "container_smoke_report_ref": "docker-smoke/container_smoke_report.json",
        "created_at": "2026-06-23T00:00:00Z",
    }
    payload.update(overrides)
    return payload


class DockerReadinessScriptTests(unittest.TestCase):
    def test_default_repository_static_contract_is_ready_without_live_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report_path = root / "docker-readiness.json"
            summary_path = root / "docker-readiness.md"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--output",
                    str(report_path),
                    "--summary-output",
                    str(summary_path),
                    "--print-json",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report.get("schema_version"), "docker_readiness.v1")
            self.assertEqual(report.get("status"), "DOCKER_READINESS_READY")
            self.assertFalse(report.get("live_evidence_required"))
            self.assertEqual(report.get("failed_checks"), [])
            self.assertIn("Status: `DOCKER_READINESS_READY`", summary_path.read_text(encoding="utf-8"))

    def test_live_evidence_mode_blocks_without_external_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = Path(temp_dir) / "docker-readiness.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--require-live-evidence",
                    "--fail-on-blocked",
                    "--output",
                    str(report_path),
                    "--summary-output",
                    "-",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 1)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report.get("status"), "DOCKER_READINESS_BLOCKED")
            self.assertIn("docker_live_evidence", report.get("failed_checks", []))

    def test_live_evidence_mode_passes_with_external_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            evidence_path = root / "docker-live-evidence.json"
            report_path = root / "docker-readiness.json"
            _write_json(evidence_path, _live_evidence())

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--require-live-evidence",
                    "--live-evidence",
                    str(evidence_path),
                    "--output",
                    str(report_path),
                    "--summary-output",
                    "-",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report.get("status"), "DOCKER_READINESS_READY")
            live_check = next(check for check in report.get("checks", []) if check.get("id") == "docker_live_evidence")
            self.assertEqual(live_check.get("status"), "pass")

    def test_dry_run_live_evidence_blocks_strict_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            evidence_path = root / "docker-live-evidence.json"
            report_path = root / "docker-readiness.json"
            _write_json(evidence_path, _live_evidence(dry_run=True))

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--require-live-evidence",
                    "--live-evidence",
                    str(evidence_path),
                    "--output",
                    str(report_path),
                    "--summary-output",
                    "-",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report.get("status"), "DOCKER_READINESS_BLOCKED")
            live_check = next(check for check in report.get("checks", []) if check.get("id") == "docker_live_evidence")
            self.assertIn("dry_run_not_allowed", live_check.get("actual", {}).get("failure_codes", []))

    def test_missing_dockerfile_health_port_blocks_static_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            dockerfile = root / "Dockerfile"
            shutil.copyfile(REPO_ROOT / "Dockerfile", dockerfile)
            dockerfile.write_text(dockerfile.read_text(encoding="utf-8").replace("EXPOSE 8000", ""), encoding="utf-8")
            report_path = root / "docker-readiness.json"

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--dockerfile",
                    str(dockerfile),
                    "--output",
                    str(report_path),
                    "--summary-output",
                    "-",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report.get("status"), "DOCKER_READINESS_BLOCKED")
            self.assertIn("dockerfile_runtime_contract", report.get("failed_checks", []))


if __name__ == "__main__":
    unittest.main()
