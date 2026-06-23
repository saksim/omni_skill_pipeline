from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "observability_readiness.py"
BASELINE_TRIAL_METRICS = (
    REPO_ROOT / "docs" / "working" / "status" / "baselines" / "controlled-trial" / "trial-metrics-report.json"
)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _live_evidence(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": "observability_live_evidence.v1",
        "status": "pass",
        "job_duration_status": "pass",
        "job_success_failure_status": "pass",
        "retry_status": "pass",
        "modality_success_status": "pass",
        "human_review_scores_status": "pass",
        "release_artifact_status": "pass",
        "agent_smoke_status": "pass",
        "redaction_secret_failure_status": "pass",
        "dashboard_status": "pass",
        "operator_dashboard_ref": "docs/working/status/baselines/observability-dashboard.redacted.md",
        "created_at": "2026-06-23T00:00:00Z",
    }
    payload.update(overrides)
    return payload


class ObservabilityReadinessScriptTests(unittest.TestCase):
    def test_default_repository_static_contract_is_ready_without_live_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report_path = root / "observability-readiness.json"
            summary_path = root / "observability-readiness.md"
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
            self.assertEqual(report.get("schema_version"), "observability_readiness.v1")
            self.assertEqual(report.get("status"), "OBSERVABILITY_READINESS_READY")
            self.assertFalse(report.get("live_evidence_required"))
            self.assertEqual(report.get("failed_checks"), [])
            self.assertIn("Status: `OBSERVABILITY_READINESS_READY`", summary_path.read_text(encoding="utf-8"))

    def test_live_evidence_mode_blocks_without_external_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = Path(temp_dir) / "observability-readiness.json"
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
            self.assertEqual(report.get("status"), "OBSERVABILITY_READINESS_BLOCKED")
            self.assertIn("observability_live_evidence", report.get("failed_checks", []))

    def test_live_evidence_mode_passes_with_external_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            evidence_path = root / "observability-live-evidence.json"
            report_path = root / "observability-readiness.json"
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
            self.assertEqual(report.get("status"), "OBSERVABILITY_READINESS_READY")
            live_check = next(check for check in report.get("checks", []) if check.get("id") == "observability_live_evidence")
            self.assertEqual(live_check.get("status"), "pass")

    def test_missing_trial_metric_field_blocks_static_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report_path = root / "observability-readiness.json"
            trial_metrics_path = root / "trial-metrics-report.json"
            payload = json.loads(BASELINE_TRIAL_METRICS.read_text(encoding="utf-8"))
            payload["trial_metrics"].pop("latency_ms", None)
            _write_json(trial_metrics_path, payload)

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--trial-metrics-report",
                    str(trial_metrics_path),
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
            self.assertEqual(report.get("status"), "OBSERVABILITY_READINESS_BLOCKED")
            self.assertIn("observability_trial_metrics_contract", report.get("failed_checks", []))


if __name__ == "__main__":
    unittest.main()
