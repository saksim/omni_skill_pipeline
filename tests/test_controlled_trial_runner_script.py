from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "run_controlled_trial.py"


def _text_manifest_payload() -> dict[str, object]:
    return {
        "manifest_id": "cbt11-script-test",
        "manifest_version": "1.0",
        "created_on": "2026-05-20",
        "samples": [
            {
                "sample_id": "text-loop-001",
                "modality": "text",
                "scenario": "controlled trial text script smoke",
                "source_owner": "test-owner",
                "sensitivity": "internal",
                "asset_list": [
                    {
                        "asset_id": "text-asset-001",
                        "asset_type": "markdown",
                        "uri": "examples/trial/text/slow-query-notes.md",
                    }
                ],
                "review_owner": "reviewer-a",
                "target_package_format": "portable",
                "expected_output_type": "diagnostic_skill",
            }
        ],
    }


def _mixed_manifest_payload() -> dict[str, object]:
    return {
        "manifest_id": "cbt11-script-test-mixed",
        "manifest_version": "1.0",
        "created_on": "2026-05-20",
        "samples": [
            {
                "sample_id": "mixed-loop-001",
                "modality": "mixed_corpus",
                "scenario": "controlled trial mixed script smoke",
                "source_owner": "test-owner",
                "sensitivity": "internal",
                "asset_list": [
                    {
                        "asset_id": "mixed-asset-001",
                        "asset_type": "document",
                        "uri": "examples/trial/mixed/incident-postmortem.md",
                    },
                    {
                        "asset_id": "mixed-asset-002",
                        "asset_type": "screenshot",
                        "uri": "examples/trial/mixed/incident-dashboard.png",
                    },
                    {
                        "asset_id": "mixed-asset-003",
                        "asset_type": "transcript",
                        "uri": "examples/trial/mixed/incident-review-transcript.md",
                    },
                ],
                "review_owner": "reviewer-b",
                "target_package_format": "portable",
                "expected_output_type": "runbook_skill",
            }
        ],
    }


class ControlledTrialRunnerScriptTests(unittest.TestCase):
    def test_dry_run_writes_execution_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            manifest_path = tmp_path / "trial-manifest.json"
            output_dir = tmp_path / "out"
            manifest_path.write_text(json.dumps(_text_manifest_payload(), ensure_ascii=False, indent=2), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--manifest",
                    str(manifest_path),
                    "--output-dir",
                    str(output_dir),
                    "--dry-run",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("dry-run plan written", completed.stdout.lower())

            plan_path = output_dir / "controlled-trial-execution-plan.json"
            self.assertTrue(plan_path.is_file())
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            self.assertEqual(plan.get("sample_count"), 1)
            first = (plan.get("samples") or [None])[0]
            self.assertIsInstance(first, dict)
            self.assertEqual(first.get("sample_id"), "text-loop-001")
            self.assertEqual(first.get("modality"), "text")

    def test_fixture_smoke_runs_end_to_end_and_emits_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            manifest_path = tmp_path / "trial-manifest-mixed.json"
            output_dir = tmp_path / "out"
            manifest_path.write_text(
                json.dumps(_mixed_manifest_payload(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--manifest",
                    str(manifest_path),
                    "--output-dir",
                    str(output_dir),
                    "--use-fixture-stubs",
                    "--target",
                    "portable",
                    "--simulated-agent-smoke-result",
                    "passed",
                    "--release-decision",
                    "GO",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("controlled trial loop complete", completed.stdout.lower())

            run_report_path = output_dir / "controlled-trial-run-report.json"
            metrics_report_path = output_dir / "trial-metrics-report.json"
            metrics_summary_path = output_dir / "trial-metrics-summary.md"
            self.assertTrue(run_report_path.is_file())
            self.assertTrue(metrics_report_path.is_file())
            self.assertTrue(metrics_summary_path.is_file())

            run_report = json.loads(run_report_path.read_text(encoding="utf-8"))
            self.assertEqual(run_report.get("sample_count"), 1)
            self.assertEqual(run_report.get("metrics_status"), "fail")
            self.assertTrue(run_report.get("ga_discussion_blocked"))

            samples = run_report.get("samples", [])
            self.assertEqual(len(samples), 1)
            sample = samples[0]
            self.assertEqual(sample.get("sample_id"), "mixed-loop-001")
            exports = sample.get("export_results", [])
            self.assertTrue(exports)
            validator_reports = sample.get("validator_reports", [])
            self.assertTrue(validator_reports)
            self.assertEqual(validator_reports[0].get("status"), "pass")
            trial_security_report = sample.get("trial_security_gate_report", {})
            self.assertEqual(trial_security_report.get("status"), "pass")
            self.assertEqual(trial_security_report.get("failure_code_count"), 0)

            metrics_report = json.loads(metrics_report_path.read_text(encoding="utf-8"))
            self.assertEqual(metrics_report.get("overall_status"), "fail")
            self.assertTrue(metrics_report.get("ga_discussion_blocked"))
            failed_ids = {
                str(item.get("id", ""))
                for item in metrics_report.get("success_criteria", {}).get("failed_conditions", [])
            }
            self.assertIn("loop_volume_and_modality_coverage", failed_ids)
            self.assertIn("release_run_go", {str(item.get("id", "")) for item in metrics_report.get("success_criteria", {}).get("conditions", []) if item.get("status") == "pass"})

            summary_text = metrics_summary_path.read_text(encoding="utf-8")
            self.assertIn("Overall status: `fail`", summary_text)
            self.assertIn("loop_volume_and_modality_coverage", summary_text)


if __name__ == "__main__":
    unittest.main()
