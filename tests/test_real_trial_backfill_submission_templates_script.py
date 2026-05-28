from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "run_real_trial_backfill_submission_templates.py"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _intake_actions_report(actions: list[dict[str, Any]]) -> dict[str, Any]:
    pending_count = len([item for item in actions if str(item.get("action_status", "")).lower() == "pending"])
    closed_count = len([item for item in actions if str(item.get("action_status", "")).lower() == "closed"])
    return {
        "schema_version": "real_trial_backfill_intake_actions.v1",
        "generated_at_utc": "2026-05-28T00:00:00Z",
        "intake_status": "ACTIONS_PENDING" if pending_count > 0 else "ALL_ACTIONS_CLOSED",
        "action_counts": {
            "total_actions": len(actions),
            "pending_action_count": pending_count,
            "closed_action_count": closed_count,
        },
        "actions": actions,
        "launch_gap_snapshot": {
            "program_status": "COLLECTION_INCOMPLETE",
            "missing_complete_loops_to_threshold": pending_count,
            "missing_modalities_to_threshold": 1 if pending_count > 0 else 0,
            "blockers": ["real_loop_volume_below_threshold"] if pending_count > 0 else [],
        },
    }


class RealTrialBackfillSubmissionTemplatesScriptTests(unittest.TestCase):
    def test_generates_templates_for_pending_actions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            intake_report = root / "intake-actions-report.json"
            templates_report = root / "submission-templates-report.json"
            templates_summary = root / "submission-templates-summary.md"
            manifest_template = root / "submission-manifest.template.json"

            _write_json(
                intake_report,
                _intake_actions_report(
                    [
                        {
                            "action_id": "gl23-slot-001-text",
                            "slot_index": 1,
                            "required_modality": "text",
                            "reason": "missing_target_launch_modality",
                            "action_status": "pending",
                            "owner": "ops-a",
                        },
                        {
                            "action_id": "gl23-slot-002-audio",
                            "slot_index": 2,
                            "required_modality": "audio",
                            "reason": "loop_volume_gap_after_modality_coverage",
                            "action_status": "closed",
                            "owner": "ops-a",
                        },
                    ]
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--intake-actions-report",
                    str(intake_report),
                    "--output",
                    str(templates_report),
                    "--summary-output",
                    str(templates_summary),
                    "--manifest-template-output",
                    str(manifest_template),
                    "--owner",
                    "ops-a",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            self.assertIn("status=TEMPLATES_READY", completed.stdout)

            report_payload = json.loads(templates_report.read_text(encoding="utf-8"))
            self.assertEqual(report_payload.get("template_status"), "TEMPLATES_READY")
            self.assertEqual(report_payload.get("template_counts", {}).get("generated_template_count"), 1)
            self.assertEqual(report_payload.get("template_counts", {}).get("missing_template_action_count"), 0)
            generated = report_payload.get("generated_templates", [])
            self.assertEqual(len(generated), 1)
            self.assertEqual(generated[0].get("action_id"), "gl23-slot-001-text")
            self.assertEqual(report_payload.get("manifest_template_path"), str(manifest_template.resolve()))

            manifest_payload = json.loads(manifest_template.read_text(encoding="utf-8"))
            loops = manifest_payload.get("loops", [])
            self.assertEqual(len(loops), 1)
            self.assertEqual(loops[0].get("backfill_slot_index"), 1)
            self.assertEqual(loops[0].get("backfill_action_id"), "gl23-slot-001-text")
            self.assertEqual(loops[0].get("modality"), "text")
            self.assertEqual(loops[0].get("evidence_origin"), "real")

            summary = templates_summary.read_text(encoding="utf-8")
            self.assertIn("Generated templates: `1`", summary)

    def test_reports_missing_template_when_pending_action_contract_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            intake_report = root / "intake-actions-report.json"
            templates_report = root / "submission-templates-report.json"

            _write_json(
                intake_report,
                _intake_actions_report(
                    [
                        {
                            "action_id": "",
                            "slot_index": 1,
                            "required_modality": "video",
                            "reason": "missing_target_launch_modality",
                            "action_status": "pending",
                            "owner": "ops-a",
                        }
                    ]
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--intake-actions-report",
                    str(intake_report),
                    "--output",
                    str(templates_report),
                    "--summary-output",
                    "-",
                    "--manifest-template-output",
                    "-",
                    "--fail-on-missing-template",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr + completed.stdout)
            self.assertIn("status=TEMPLATE_FIELDS_MISSING", completed.stdout)
            payload = json.loads(templates_report.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("template_status"), "TEMPLATE_FIELDS_MISSING")
            self.assertEqual(payload.get("template_counts", {}).get("generated_template_count"), 0)
            self.assertEqual(payload.get("template_counts", {}).get("missing_template_action_count"), 1)
            missing = payload.get("missing_template_actions", [])
            self.assertEqual(len(missing), 1)
            self.assertEqual(missing[0].get("missing_template_reason"), "missing_action_id")


if __name__ == "__main__":
    unittest.main()
