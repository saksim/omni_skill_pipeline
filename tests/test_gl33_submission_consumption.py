from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "gl33_submission_consumption.py"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _template_manifest(loop_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "manifest_id": "gl31-real-backfill-submission-template",
        "manifest_version": "1.0",
        "generated_at_utc": "2026-05-28T00:00:00Z",
        "owner": "controlled-beta-ops",
        "loops": loop_rows,
    }


def _template_loop(action_id: str, slot_index: int, modality: str) -> dict[str, Any]:
    return {
        "loop_id": "real-%s-slot-%03d-template" % (modality, slot_index),
        "status": "complete",
        "modality": modality,
        "evidence_origin": "real",
        "launch_gate_eligible": True,
        "source_system": "TEMPLATE_REQUIRED_REPLACE_WITH_REAL_SOURCE_SYSTEM",
        "source_reference": "TEMPLATE_REQUIRED_REPLACE_WITH_REAL_SOURCE_REFERENCE",
        "collected_at_utc": "TEMPLATE_REQUIRED_REPLACE_WITH_UTC_TIMESTAMP",
        "review_task_id": "TEMPLATE_REQUIRED_REPLACE_WITH_REVIEW_TASK_ID",
        "reviewed_by": "TEMPLATE_REQUIRED_REPLACE_WITH_REVIEWER",
        "reviewed_at_utc": "TEMPLATE_REQUIRED_REPLACE_WITH_UTC_TIMESTAMP",
        "review_outcome": "approved",
        "revisions_before_approval": 0,
        "reviewer_edit_distance_pct": 0.0,
        "agent_smoke_result": "not_run",
        "published_without_review": False,
        "critical_secret_or_pii_leak": False,
        "high_severity_incident": False,
        "latency_ms": 0.0,
        "provider_failure_count": 0,
        "provider_call_count": 0,
        "retry_count": 0,
        "artifact_count": 0,
        "estimated_cost_usd": 0.0,
        "backfill_slot_index": slot_index,
        "backfill_action_id": action_id,
    }


def _real_inputs(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "real_trial_backfill_submission_real_inputs.v1",
        "generated_at_utc": "2026-05-28T00:00:00Z",
        "owner": "controlled-beta-ops",
        "submissions": rows,
    }


def _real_submission(
    action_id: str,
    slot_index: int,
    modality: str,
    loop_id: str,
) -> dict[str, Any]:
    return {
        "backfill_action_id": action_id,
        "backfill_slot_index": slot_index,
        "modality": modality,
        "loop_id": loop_id,
        "source_system": "pilot-ops",
        "source_reference": "ticket://%s" % loop_id,
        "collected_at_utc": "2026-05-28T00:00:00Z",
        "review_task_id": "review-%s" % loop_id,
        "reviewed_by": "reviewer-a",
        "reviewed_at_utc": "2026-05-28T00:05:00Z",
        "review_outcome": "approved",
        "revisions_before_approval": 1,
        "reviewer_edit_distance_pct": 5.0,
        "agent_smoke_result": "passed",
        "published_without_review": False,
        "critical_secret_or_pii_leak": False,
        "high_severity_incident": False,
        "latency_ms": 150.0,
        "provider_failure_count": 0,
        "provider_call_count": 2,
        "retry_count": 0,
        "artifact_count": 6,
        "estimated_cost_usd": 0.2,
    }


class RealTrialBackfillSubmissionConsumptionScriptTests(unittest.TestCase):
    def test_consumes_template_rows_into_ingestion_ready_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            template_manifest = root / "template-manifest.json"
            real_inputs = root / "real-inputs.json"
            report_path = root / "consumption-report.json"
            summary_path = root / "consumption-summary.md"
            consumed_manifest_path = root / "consumed-manifest.json"

            _write_json(
                template_manifest,
                _template_manifest(
                    [
                        _template_loop("gl23-slot-001-text", 1, "text"),
                        _template_loop("gl23-slot-002-audio", 2, "audio"),
                    ]
                ),
            )
            _write_json(
                real_inputs,
                _real_inputs(
                    [
                        _real_submission(
                            "gl23-slot-001-text",
                            1,
                            "text",
                            "real-text-001",
                        ),
                        _real_submission(
                            "gl23-slot-002-audio",
                            2,
                            "audio",
                            "real-audio-001",
                        ),
                    ]
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-manifest-template",
                    str(template_manifest),
                    "--real-submissions-input",
                    str(real_inputs),
                    "--output",
                    str(report_path),
                    "--summary-output",
                    str(summary_path),
                    "--consumed-manifest-output",
                    str(consumed_manifest_path),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            self.assertIn("status=CONSUMED_MANIFEST_READY", completed.stdout)

            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report.get("consumption_status"), "CONSUMED_MANIFEST_READY")
            counts = report.get("counts", {})
            self.assertEqual(counts.get("template_loop_count"), 2)
            self.assertEqual(counts.get("submitted_row_count"), 2)
            self.assertEqual(counts.get("consumed_loop_count"), 2)
            self.assertEqual(counts.get("pending_template_loop_count"), 0)
            self.assertEqual(counts.get("invalid_submission_count"), 0)
            self.assertEqual(counts.get("unresolved_submission_count"), 0)

            consumed_manifest = json.loads(consumed_manifest_path.read_text(encoding="utf-8"))
            loops = consumed_manifest.get("loops", [])
            self.assertEqual(len(loops), 2)
            self.assertEqual(loops[0].get("source_system"), "pilot-ops")
            self.assertEqual(loops[0].get("evidence_origin"), "real")
            self.assertEqual(loops[0].get("launch_gate_eligible"), True)
            self.assertFalse("TEMPLATE_REQUIRED_" in json.dumps(loops[0], ensure_ascii=False))

    def test_reports_incomplete_when_submission_rows_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            template_manifest = root / "template-manifest.json"
            real_inputs = root / "real-inputs.json"
            report_path = root / "consumption-report.json"

            _write_json(
                template_manifest,
                _template_manifest([_template_loop("gl23-slot-001-text", 1, "text")]),
            )
            _write_json(real_inputs, _real_inputs([]))

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-manifest-template",
                    str(template_manifest),
                    "--real-submissions-input",
                    str(real_inputs),
                    "--output",
                    str(report_path),
                    "--summary-output",
                    "-",
                    "--consumed-manifest-output",
                    "-",
                    "--fail-on-incomplete",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr + completed.stdout)
            self.assertIn("status=NO_SUBMISSIONS_PROVIDED", completed.stdout)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report.get("consumption_status"), "NO_SUBMISSIONS_PROVIDED")
            counts = report.get("counts", {})
            self.assertEqual(counts.get("template_loop_count"), 1)
            self.assertEqual(counts.get("submitted_row_count"), 0)
            self.assertEqual(counts.get("pending_template_loop_count"), 1)


if __name__ == "__main__":
    unittest.main()
