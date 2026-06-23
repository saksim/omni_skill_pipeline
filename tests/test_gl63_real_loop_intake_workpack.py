from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "gl63_real_loop_intake_workpack.py"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _evidence_pack(*, slots: list[dict[str, Any]], missing_modalities: list[str]) -> dict[str, Any]:
    return {
        "schema_version": "real_trial_launch_evidence_pack.v1",
        "launch_decision": "HOLD" if slots else "READY_FOR_CONTROLLED_BETA",
        "evidence_paths": {},
        "evidence_classification": {
            "collection_program_status": "COLLECTION_INCOMPLETE" if slots else "COLLECTION_COMPLETE",
            "launch_gate_eligible_complete_loop_count": 0 if slots else 10,
            "launch_gate_eligible_complete_modalities": [] if slots else ["text", "audio", "image", "video"],
            "target_launch_modalities": ["text", "audio", "image", "video"],
            "missing_target_launch_modalities": missing_modalities,
            "recommended_backfill_slot_count": len(slots),
            "recommended_backfill_slots": slots,
        },
    }


def _gl62_report() -> dict[str, Any]:
    return {
        "schema_version": "real_trial_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations.v1",
        "warning_codes": ["no_net_new_launch_gate_eligible_real_loops"],
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_counts": {
            "total_item_count": 2,
            "open_item_count": 2,
            "blocked_overdue_stalled_item_count": 0,
            "due_item_count": 0,
        },
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_rows": [
            {
                "escalation_item_id": "gl62-escalation-text",
                "required_modality_gl47": "text",
                "escalation_action": "monitor_until_due",
            },
            {
                "escalation_item_id": "gl62-escalation-audio",
                "required_modality_gl47": "audio",
                "escalation_action": "monitor_until_due",
            },
        ],
    }


class RealTrialLoopIntakeWorkpackScriptTests(unittest.TestCase):
    def test_not_required_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            evidence_pack = root / "evidence-pack.json"
            report_path = root / "workpack.json"
            _write_json(evidence_pack, _evidence_pack(slots=[], missing_modalities=[]))

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--evidence-pack",
                    str(evidence_pack),
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
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("status"), "REAL_LOOP_INTAKE_NOT_REQUIRED")
            self.assertEqual(payload.get("work_items"), [])
            self.assertEqual(payload.get("warning_codes"), [])
            self.assertTrue(payload.get("launch_gate_policy_unchanged"))

    def test_action_required_generates_real_loop_manifest_work_items(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            evidence_pack = root / "evidence-pack.json"
            gl62_report = root / "gl62.json"
            report_path = root / "workpack.json"
            manifest_dir = root / "manifests"
            _write_json(
                evidence_pack,
                _evidence_pack(
                    slots=[
                        {"slot_index": 1, "required_modality": "text", "reason": "missing_target_launch_modality"},
                        {"slot_index": 2, "required_modality": "audio", "reason": "missing_target_launch_modality"},
                    ],
                    missing_modalities=["text", "audio"],
                ),
            )
            _write_json(gl62_report, _gl62_report())

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--evidence-pack",
                    str(evidence_pack),
                    "--gl62-escalation-report",
                    str(gl62_report),
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

            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("status"), "REAL_LOOP_INTAKE_ACTION_REQUIRED")
            self.assertEqual(
                payload.get("counts", {}).get("intake_item_count_by_modality"),
                {"text": 1, "audio": 1},
            )
            warning_codes = payload.get("warning_codes", [])
            self.assertIn("real_loop_intake_items_required", warning_codes)
            self.assertIn("upstream_no_net_new_launch_gate_eligible_real_loops", warning_codes)
            work_items = payload.get("work_items", [])
            self.assertEqual(len(work_items), 2)
            self.assertEqual(work_items[0].get("linked_gl62_escalation_item_id"), "gl62-escalation-text")
            self.assertIn("source_reference", work_items[0].get("required_trace_fields", []))
            self.assertIn("source_hashes", work_items[0].get("required_trace_fields", []))
            self.assertIn("agent_smoke_ref", work_items[0].get("required_trace_fields", []))
            self.assertIn("agent_smoke_result=passed", work_items[0].get("required_quality_fields", []))
            self.assertIn("redaction_status=passed", work_items[0].get("required_quality_fields", []))
            self.assertTrue(str(work_items[0].get("manifest_drop_path", "")).endswith("real-loop-001-text.json"))

    def test_fail_on_action_required_returns_non_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            evidence_pack = root / "evidence-pack.json"
            _write_json(
                evidence_pack,
                _evidence_pack(
                    slots=[
                        {"slot_index": 1, "required_modality": "image", "reason": "missing_target_launch_modality"}
                    ],
                    missing_modalities=["image"],
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--evidence-pack",
                    str(evidence_pack),
                    "--output",
                    "-",
                    "--summary-output",
                    "-",
                    "--fail-on-action-required",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 1, completed.stderr + completed.stdout)
            self.assertIn("REAL_LOOP_INTAKE_ACTION_REQUIRED", completed.stdout)


if __name__ == "__main__":
    unittest.main()
