from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "secrets_readiness.py"


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _production_secret_evidence(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": "secrets_management_evidence.v1",
        "status": "pass",
        "secret_manager_provider": "hashicorp_vault",
        "managed_secret_classes": [
            "provider_api_key",
            "database_password",
            "object_storage_credentials",
            "signing_key",
            "artifact_encryption_key",
        ],
        "runtime_secret_injection_status": "pass",
        "rotation_policy_status": "defined",
        "plaintext_repo_secret_scan_status": "pass",
        "no_plaintext_secrets_in_images": True,
    }
    payload.update(overrides)
    return payload


class SecretsReadinessScriptTests(unittest.TestCase):
    def test_default_repository_secret_hygiene_is_ready_without_production_manager(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report_path = root / "secrets-readiness.json"
            summary_path = root / "secrets-readiness.md"
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

            self.assertEqual(completed.returncode, 0, completed.stderr)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report.get("schema_version"), "secrets_readiness.v1")
            self.assertEqual(report.get("status"), "SECRETS_READINESS_READY")
            self.assertFalse(report.get("production_manager_required"))
            self.assertEqual(report.get("failed_checks"), [])
            self.assertIn("Status: `SECRETS_READINESS_READY`", summary_path.read_text(encoding="utf-8"))

    def test_production_manager_mode_blocks_without_external_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = Path(temp_dir) / "secrets-readiness.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--require-production-manager",
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
            self.assertEqual(report.get("status"), "SECRETS_READINESS_BLOCKED")
            self.assertIn("production_secret_manager_evidence", report.get("failed_checks", []))

    def test_production_manager_mode_passes_with_external_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            evidence_path = root / "secrets-management-evidence.json"
            report_path = root / "secrets-readiness.json"
            _write_json(evidence_path, _production_secret_evidence())

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--require-production-manager",
                    "--external-secret-evidence",
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

            self.assertEqual(completed.returncode, 0, completed.stderr)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report.get("status"), "SECRETS_READINESS_READY")
            self.assertTrue(report.get("production_manager_required"))
            production_check = next(
                check for check in report.get("checks", []) if check.get("id") == "production_secret_manager_evidence"
            )
            self.assertEqual(production_check.get("status"), "pass")

    def test_env_example_with_plaintext_secret_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            env_path = root / ".env.example"
            report_path = root / "secrets-readiness.json"
            env_path.write_text(
                "\n".join(
                    [
                        "OPENAI_API_KEY=sk-live-secret",
                        "OMNI_API_KEY=",
                        "OMNI_TENANT_ACCESS_JSON=",
                        "OMNI_TENANT_ACCESS_FILE=",
                        "OMNI_TEST_POSTGRES_DSN=",
                        "OMNI_POSTGRES_REPOSITORY_DSN=",
                        "OMNI_ARTIFACT_ENCRYPTION_KEY=",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--env-example",
                    str(env_path),
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
            self.assertEqual(report.get("status"), "SECRETS_READINESS_BLOCKED")
            self.assertIn("env_example_secret_placeholders", report.get("failed_checks", []))


if __name__ == "__main__":
    unittest.main()
