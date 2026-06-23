from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "product_surface_readiness.py"


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _live_evidence(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": "product_surface_live_evidence.v1",
        "status": "pass",
        "source_intake_status": "pass",
        "job_run_status": "pass",
        "skill_preview_status": "pass",
        "human_review_status": "pass",
        "export_validate_status": "pass",
        "evidence_manifest_status": "pass",
        "dashboard_status": "pass",
        "operator_transcript_ref": "docs/working/status/baselines/product-surface-transcript.redacted.md",
        "created_at": "2026-06-23T00:00:00Z",
    }
    payload.update(overrides)
    return payload


class ProductSurfaceReadinessScriptTests(unittest.TestCase):
    def test_default_repository_static_contract_is_ready_without_live_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report_path = root / "product-surface-readiness.json"
            summary_path = root / "product-surface-readiness.md"
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
            self.assertEqual(report.get("schema_version"), "product_surface_readiness.v1")
            self.assertEqual(report.get("status"), "PRODUCT_SURFACE_READINESS_READY")
            self.assertFalse(report.get("live_evidence_required"))
            self.assertEqual(report.get("failed_checks"), [])
            self.assertIn("Status: `PRODUCT_SURFACE_READINESS_READY`", summary_path.read_text(encoding="utf-8"))

    def test_live_evidence_mode_blocks_without_external_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = Path(temp_dir) / "product-surface-readiness.json"
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
            self.assertEqual(report.get("status"), "PRODUCT_SURFACE_READINESS_BLOCKED")
            self.assertIn("product_surface_live_evidence", report.get("failed_checks", []))

    def test_live_evidence_mode_passes_with_external_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            evidence_path = root / "product-surface-live-evidence.json"
            report_path = root / "product-surface-readiness.json"
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
            self.assertEqual(report.get("status"), "PRODUCT_SURFACE_READINESS_READY")
            live_check = next(check for check in report.get("checks", []) if check.get("id") == "product_surface_live_evidence")
            self.assertEqual(live_check.get("status"), "pass")

    def test_missing_console_route_blocks_static_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            api_source = root / "api_app.py"
            shutil.copyfile(REPO_ROOT / "src" / "omni_skill_pipeline" / "api_app.py", api_source)
            api_source.write_text(
                api_source.read_text(encoding="utf-8").replace("@app.post('/v1/console/views')", ""),
                encoding="utf-8",
            )
            report_path = root / "product-surface-readiness.json"

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--api-source",
                    str(api_source),
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
            self.assertEqual(report.get("status"), "PRODUCT_SURFACE_READINESS_BLOCKED")
            self.assertIn("product_surface_api_routes", report.get("failed_checks", []))


if __name__ == "__main__":
    unittest.main()
