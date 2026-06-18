from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = (
    REPO_ROOT
    / "scripts"
    / "gl47_action_plan_closure.py"
)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _gl46_action_plan_report(
    *,
    status: str,
    warning_codes: list[str],
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    open_count = sum(1 for row in rows if str(row.get("action_status", "")).strip().lower() == "open")
    return {
        "schema_version": "real_trial_submission_queue_followup_resolution_escalation_action_plan.v1",
        "generated_at_utc": "2026-05-30T00:00:00Z",
        "followup_resolution_escalation_action_plan_status": status,
        "warning_codes": warning_codes,
        "followup_resolution_escalation_action_plan_counts": {
            "total_action_count": len(rows),
            "open_action_count": open_count,
            "closed_action_count": len(rows) - open_count,
            "unresolved_ack_mapping_action_count": sum(
                1
                for row in rows
                if str(row.get("action_type", "")).strip() == "resolve_acknowledged_loop_mapping_gap"
            ),
            "recommended_backfill_slot_action_count": sum(
                1
                for row in rows
                if str(row.get("action_type", "")).strip() == "collect_launch_gate_eligible_real_loop"
            ),
        },
        "followup_resolution_escalation_action_plan_rows": rows,
    }


def _gl12_collection_report(
    *,
    loops: list[dict[str, Any]],
    missing_complete_loops_to_threshold: int,
    missing_modalities_to_threshold: int,
) -> dict[str, Any]:
    return {
        "schema_version": "real_trial_loop_collection.v1",
        "generated_at_utc": "2026-05-30T00:01:00Z",
        "launch_gate_alignment": {
            "program_status": "COLLECTION_INCOMPLETE",
            "launch_gate_eligible_complete_loop_count": len(loops),
            "missing_complete_loops_to_threshold": missing_complete_loops_to_threshold,
            "missing_modalities_to_threshold": missing_modalities_to_threshold,
        },
        "collected_real_launch_gate_eligible_loops": loops,
    }


class RealTrialSubmissionQueueFollowupResolutionEscalationActionPlanClosureScriptTests(unittest.TestCase):
    def test_baseline_initialized_with_open_actions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            gl46 = root / "gl46.json"
            gl12 = root / "gl12.json"
            output = root / "gl47.json"

            _write_json(
                gl46,
                _gl46_action_plan_report(
                    status="ACTION_PLAN_OPEN",
                    warning_codes=["loop_volume_gap_persists"],
                    rows=[
                        {
                            "action_id": "gl46-slot-001-text",
                            "action_status": "open",
                            "action_type": "collect_launch_gate_eligible_real_loop",
                            "required_modality": "text",
                            "reason": "missing_target_launch_modality",
                            "owner": "controlled-beta-ops",
                            "backfill_slot_index": 1,
                            "linked_submission_loop_id": "",
                            "source": "gl12.recommended_backfill_slots",
                        }
                    ],
                ),
            )
            _write_json(
                gl12,
                _gl12_collection_report(
                    loops=[{"loop_id": "real-text-000", "modality": "text"}],
                    missing_complete_loops_to_threshold=9,
                    missing_modalities_to_threshold=3,
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-escalation-action-plan-report",
                    str(gl46),
                    "--collection-report",
                    str(gl12),
                    "--output",
                    str(output),
                    "--summary-output",
                    "-",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(
                payload.get("followup_resolution_escalation_action_plan_closure_status"),
                "ACTION_PLAN_CLOSURE_BASELINE_INITIALIZED",
            )
            counts = payload.get("followup_resolution_escalation_action_plan_closure_counts", {})
            self.assertEqual(counts.get("open_action_count"), 1)
            self.assertEqual(counts.get("net_new_closed_action_count"), 0)
            self.assertEqual(counts.get("net_new_launch_gate_eligible_loop_count"), 1)
            self.assertEqual(counts.get("stale_open_action_count"), 0)

    def test_progressing_when_actions_close_and_loop_growth(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            gl46 = root / "gl46.json"
            gl12 = root / "gl12.json"
            output = root / "gl47.json"

            _write_json(
                gl46,
                _gl46_action_plan_report(
                    status="ACTION_PLAN_OPEN",
                    warning_codes=[],
                    rows=[
                        {
                            "action_id": "gl46-slot-001-text",
                            "action_status": "open",
                            "action_type": "collect_launch_gate_eligible_real_loop",
                            "required_modality": "text",
                            "reason": "missing_target_launch_modality",
                            "owner": "controlled-beta-ops",
                            "backfill_slot_index": 1,
                            "linked_submission_loop_id": "",
                            "source": "gl12.recommended_backfill_slots",
                        },
                        {
                            "action_id": "gl46-slot-002-audio",
                            "action_status": "open",
                            "action_type": "collect_launch_gate_eligible_real_loop",
                            "required_modality": "audio",
                            "reason": "missing_target_launch_modality",
                            "owner": "controlled-beta-ops",
                            "backfill_slot_index": 2,
                            "linked_submission_loop_id": "",
                            "source": "gl12.recommended_backfill_slots",
                        },
                    ],
                ),
            )
            _write_json(
                gl12,
                _gl12_collection_report(
                    loops=[{"loop_id": "real-text-000", "modality": "text"}],
                    missing_complete_loops_to_threshold=9,
                    missing_modalities_to_threshold=3,
                ),
            )
            baseline = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-escalation-action-plan-report",
                    str(gl46),
                    "--collection-report",
                    str(gl12),
                    "--output",
                    str(output),
                    "--summary-output",
                    "-",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(baseline.returncode, 0, baseline.stderr + baseline.stdout)

            _write_json(
                gl46,
                _gl46_action_plan_report(
                    status="ACTION_PLAN_OPEN",
                    warning_codes=[],
                    rows=[
                        {
                            "action_id": "gl46-slot-002-audio",
                            "action_status": "open",
                            "action_type": "collect_launch_gate_eligible_real_loop",
                            "required_modality": "audio",
                            "reason": "missing_target_launch_modality",
                            "owner": "controlled-beta-ops",
                            "backfill_slot_index": 2,
                            "linked_submission_loop_id": "",
                            "source": "gl12.recommended_backfill_slots",
                        }
                    ],
                ),
            )
            _write_json(
                gl12,
                _gl12_collection_report(
                    loops=[
                        {"loop_id": "real-text-000", "modality": "text"},
                        {"loop_id": "real-audio-001", "modality": "audio"},
                    ],
                    missing_complete_loops_to_threshold=8,
                    missing_modalities_to_threshold=2,
                ),
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-escalation-action-plan-report",
                    str(gl46),
                    "--collection-report",
                    str(gl12),
                    "--output",
                    str(output),
                    "--summary-output",
                    "-",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(
                payload.get("followup_resolution_escalation_action_plan_closure_status"),
                "ACTION_PLAN_CLOSURE_PROGRESSING",
            )
            counts = payload.get("followup_resolution_escalation_action_plan_closure_counts", {})
            self.assertEqual(counts.get("open_action_count"), 1)
            self.assertEqual(counts.get("carried_open_action_count"), 1)
            self.assertEqual(counts.get("net_new_closed_action_count"), 1)
            self.assertEqual(counts.get("net_new_launch_gate_eligible_loop_count"), 1)
            self.assertEqual(counts.get("stale_open_action_count"), 1)
            self.assertEqual(payload.get("net_new_closed_action_ids"), ["gl46-slot-001-text"])
            closure_rows = payload.get("followup_resolution_escalation_action_plan_closure_rows", [])
            self.assertEqual(len(closure_rows), 2)
            self.assertEqual(closure_rows[0].get("action_id"), "gl46-slot-002-audio")
            self.assertEqual(closure_rows[0].get("closure_state"), "open_carried")
            self.assertEqual(closure_rows[1].get("action_id"), "gl46-slot-001-text")
            self.assertEqual(closure_rows[1].get("closure_state"), "closed_since_previous_cycle")

    def test_stalled_fail_on_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            gl46 = root / "gl46.json"
            gl12 = root / "gl12.json"
            output = root / "gl47.json"

            _write_json(
                gl46,
                _gl46_action_plan_report(
                    status="ACTION_PLAN_OPEN",
                    warning_codes=[],
                    rows=[
                        {
                            "action_id": "gl46-slot-001-text",
                            "action_status": "open",
                            "action_type": "collect_launch_gate_eligible_real_loop",
                            "required_modality": "text",
                            "reason": "missing_target_launch_modality",
                            "owner": "controlled-beta-ops",
                            "backfill_slot_index": 1,
                            "linked_submission_loop_id": "",
                            "source": "gl12.recommended_backfill_slots",
                        }
                    ],
                ),
            )
            _write_json(
                gl12,
                _gl12_collection_report(
                    loops=[],
                    missing_complete_loops_to_threshold=10,
                    missing_modalities_to_threshold=4,
                ),
            )
            baseline = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-escalation-action-plan-report",
                    str(gl46),
                    "--collection-report",
                    str(gl12),
                    "--output",
                    str(output),
                    "--summary-output",
                    "-",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(baseline.returncode, 0, baseline.stderr + baseline.stdout)

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-escalation-action-plan-report",
                    str(gl46),
                    "--collection-report",
                    str(gl12),
                    "--output",
                    str(output),
                    "--summary-output",
                    "-",
                    "--fail-on-stalled",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr + completed.stdout)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(
                payload.get("followup_resolution_escalation_action_plan_closure_status"),
                "ACTION_PLAN_CLOSURE_STALLED",
            )
            warning_codes = payload.get("warning_codes", [])
            self.assertIn("no_net_new_closed_action_plan_items", warning_codes)
            self.assertIn("no_net_new_launch_gate_eligible_real_loops", warning_codes)
            self.assertIn("stale_open_action_plan_items_present", warning_codes)


if __name__ == "__main__":
    unittest.main()
