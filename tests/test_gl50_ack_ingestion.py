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
    / "gl50_ack_ingestion.py"
)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _gl49_report(*, rows: list[dict[str, Any]], status: str = "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_MONITORING") -> dict[str, Any]:
    return {
        "schema_version": "real_trial_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations.v1",
        "generated_at_utc": "2026-05-30T00:00:00Z",
        "owner": "controlled-beta-ops",
        "followup_resolution_escalation_action_plan_closure_cadence_status_gl48": "ACTION_PLAN_CLOSURE_CADENCE_ON_SCHEDULE",
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_status": status,
        "warning_codes": [],
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_counts": {
            "total_item_count": len(rows),
            "open_item_count": len(rows),
            "blocked_overdue_stalled_item_count": 0,
            "due_item_count": 0,
            "monitor_item_count": len(rows),
            "cadence_stall_cycle_count_gl48": 0,
            "cadence_overdue_stalled_cycles_threshold_gl48": 2,
            "escalate_after_due_hours": 24.0,
        },
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_rows": rows,
    }


def _gl24_handoff(*, queue_items: list[dict[str, Any]], ack_input_path: str = "") -> dict[str, Any]:
    return {
        "schema_version": "real_trial_backfill_handoff.v1",
        "generated_at_utc": "2026-05-30T00:00:00Z",
        "input_paths": {
            "intake_actions_report": "unused",
            "collection_report": "unused",
            "acknowledgements_report": ack_input_path,
        },
        "handoff_status": "HANDOFF_OPERATOR_ACK_PENDING" if queue_items else "HANDOFF_NOT_REQUIRED",
        "queue_items": queue_items,
    }


def _handoff_queue_item(
    *,
    slot: int,
    modality: str,
    linked_loop_id: str,
    queue_status: str = "submission_linked_pending_ack",
) -> dict[str, Any]:
    action_id = "gl23-slot-%03d-%s" % (slot, modality)
    return {
        "queue_item_id": "gl24-queue-%s" % action_id,
        "action_id": action_id,
        "slot_index": slot,
        "required_modality": modality,
        "queue_status": queue_status,
        "closure_acknowledgement": {
            "status": "pending_operator_acknowledgement",
            "linked_submission": {
                "loop_id": linked_loop_id,
                "review_task_id": "review-%s" % linked_loop_id,
                "reviewed_at_utc": "2026-05-30T00:05:00Z",
            },
        },
    }


class RealTrialSubmissionQueueFollowupResolutionEscalationActionPlanClosureCadenceEscalationAckIngestionScriptTests(
    unittest.TestCase
):
    def test_not_required_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            gl49_path = root / "gl49.json"
            gl24_path = root / "gl24.json"
            out_path = root / "gl50.json"

            _write_json(gl49_path, _gl49_report(rows=[], status="ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_NOT_REQUIRED"))
            _write_json(gl24_path, _gl24_handoff(queue_items=[]))

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalations-report",
                    str(gl49_path),
                    "--handoff-report",
                    str(gl24_path),
                    "--output",
                    str(out_path),
                    "--summary-output",
                    "-",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            payload = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertEqual(
                payload.get(
                    "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_status"
                ),
                "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_NOT_REQUIRED",
            )
            counts = payload.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_counts",
                {},
            )
            self.assertEqual(int(counts.get("total_item_count", 0)), 0)

    def test_input_missing_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            gl49_path = root / "gl49.json"
            gl24_path = root / "gl24.json"
            out_path = root / "gl50.json"

            _write_json(
                gl49_path,
                _gl49_report(
                    rows=[
                        {
                            "escalation_item_id": "gl49-cadence-escalation-gl46-slot-001-text",
                            "action_id_gl48": "gl46-slot-001-text",
                            "required_modality_gl47": "text",
                            "owner": "controlled-beta-ops",
                            "linked_submission_loop_id_gl47": "",
                        }
                    ]
                ),
            )
            _write_json(
                gl24_path,
                _gl24_handoff(
                    queue_items=[_handoff_queue_item(slot=1, modality="text", linked_loop_id="real-text-001")],
                    ack_input_path="",
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalations-report",
                    str(gl49_path),
                    "--handoff-report",
                    str(gl24_path),
                    "--output",
                    str(out_path),
                    "--summary-output",
                    "-",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            payload = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertEqual(
                payload.get(
                    "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_status"
                ),
                "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_INPUT_MISSING",
            )
            counts = payload.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_counts",
                {},
            )
            self.assertEqual(int(counts.get("open_item_count", 0)), 1)
            rows = payload.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_rows",
                [],
            )
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].get("acknowledgement_ingestion_state"), "ack_input_missing")
            warnings = payload.get("warning_codes", [])
            self.assertIn("acknowledgement_input_missing", warnings)

    def test_loop_mismatch_path_and_fail_on_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            gl49_path = root / "gl49.json"
            gl24_path = root / "gl24.json"
            ack_path = root / "ack.json"
            out_path = root / "gl50.json"

            _write_json(
                gl49_path,
                _gl49_report(
                    rows=[
                        {
                            "escalation_item_id": "gl49-cadence-escalation-gl46-slot-001-text",
                            "action_id_gl48": "gl46-slot-001-text",
                            "required_modality_gl47": "text",
                            "owner": "controlled-beta-ops",
                            "linked_submission_loop_id_gl47": "",
                        }
                    ]
                ),
            )
            _write_json(
                gl24_path,
                _gl24_handoff(
                    queue_items=[_handoff_queue_item(slot=1, modality="text", linked_loop_id="real-text-001")],
                    ack_input_path=str(ack_path),
                ),
            )
            _write_json(
                ack_path,
                {
                    "schema_version": "real_trial_backfill_handoff_acknowledgements.v1",
                    "generated_at_utc": "2026-05-30T00:06:00Z",
                    "acknowledgements": [
                        {
                            "acknowledgement_id": "ack-001",
                            "queue_item_id": "gl24-queue-gl23-slot-001-text",
                            "action_id": "gl23-slot-001-text",
                            "submitted_loop_id": "real-text-999",
                            "submitted_modality": "text",
                            "acknowledged_by": "ops-reviewer-1",
                            "acknowledged_at_utc": "2026-05-30T00:07:00Z",
                            "notes": "mismatch on purpose",
                        }
                    ],
                },
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalations-report",
                    str(gl49_path),
                    "--handoff-report",
                    str(gl24_path),
                    "--acknowledgements-report",
                    str(ack_path),
                    "--output",
                    str(out_path),
                    "--summary-output",
                    "-",
                    "--fail-on-gap",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr + completed.stdout)
            payload = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertEqual(
                payload.get(
                    "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_status"
                ),
                "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_ACTION_REQUIRED",
            )
            counts = payload.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_counts",
                {},
            )
            self.assertEqual(int(counts.get("escalation_rows_with_mismatched_ack_loop_count", 0)), 1)
            rows = payload.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_rows",
                [],
            )
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].get("acknowledgement_ingestion_state"), "ack_loop_mismatch")
            warnings = payload.get("warning_codes", [])
            self.assertIn("escalation_rows_acknowledgement_loop_mismatch", warnings)


if __name__ == "__main__":
    unittest.main()
