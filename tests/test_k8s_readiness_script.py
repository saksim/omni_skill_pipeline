from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "k8s_readiness.py"


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _cluster_evidence(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": "k8s_cluster_evidence.v1",
        "status": "pass",
        "namespace": "omni-skill-pipeline",
        "server_dry_run_status": "pass",
        "rollout_status": "pass",
        "health_probe_status": "pass",
        "log_inspection_status": "pass",
        "secret_reference_status": "pass",
    }
    payload.update(overrides)
    return payload


class K8sReadinessScriptTests(unittest.TestCase):
    def test_default_repository_k8s_static_contract_is_ready_without_cluster_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report_path = root / "k8s-readiness.json"
            summary_path = root / "k8s-readiness.md"
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
            self.assertEqual(report.get("schema_version"), "k8s_readiness.v1")
            self.assertEqual(report.get("status"), "K8S_READINESS_READY")
            self.assertFalse(report.get("cluster_evidence_required"))
            self.assertEqual(report.get("failed_checks"), [])
            self.assertIn("Status: `K8S_READINESS_READY`", summary_path.read_text(encoding="utf-8"))

    def test_cluster_evidence_mode_blocks_without_external_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = Path(temp_dir) / "k8s-readiness.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--require-cluster-evidence",
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
            self.assertEqual(report.get("status"), "K8S_READINESS_BLOCKED")
            self.assertIn("k8s_cluster_evidence", report.get("failed_checks", []))

    def test_cluster_evidence_mode_passes_with_external_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            evidence_path = root / "k8s-cluster-evidence.json"
            report_path = root / "k8s-readiness.json"
            _write_json(evidence_path, _cluster_evidence())

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--require-cluster-evidence",
                    "--cluster-evidence",
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
            self.assertEqual(report.get("status"), "K8S_READINESS_READY")
            self.assertTrue(report.get("cluster_evidence_required"))
            cluster_check = next(check for check in report.get("checks", []) if check.get("id") == "k8s_cluster_evidence")
            self.assertEqual(cluster_check.get("status"), "pass")

    def test_missing_readiness_probe_blocks_static_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_dir = root / "k8s"
            shutil.copytree(REPO_ROOT / "k8s", manifest_dir)
            deployment_path = manifest_dir / "deployment.yaml"
            deployment_text = deployment_path.read_text(encoding="utf-8")
            deployment_path.write_text(deployment_text.replace("readinessProbe:", "readinessProbeDisabled:"), encoding="utf-8")
            report_path = root / "k8s-readiness.json"

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--manifest-dir",
                    str(manifest_dir),
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
            self.assertEqual(report.get("status"), "K8S_READINESS_BLOCKED")
            self.assertIn("k8s_deployment_contract", report.get("failed_checks", []))


if __name__ == "__main__":
    unittest.main()
