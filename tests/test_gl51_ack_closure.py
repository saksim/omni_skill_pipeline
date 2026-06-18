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
    / "gl51_ack_closure.py"
)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _collection_report(*, loop_ids: list[str]) -> dict[str, Any]:
    return {
        "schema_version": "real_trial_loop_collection.v1",
        "generated_at_utc": "2026-05-30T00:00:00Z",
        "launch_gate_alignment": {
            "program_status": "COLLECTION_INCOMPLETE",
            "launch_gate_eligible_complete_loop_count": len(loop_ids),
            "missing_complete_loops_to_threshold": max(0, 10 - len(loop_ids)),
            "missing_modalities_to_threshold": 0,
        },
        "collected_real_launch_gate_eligible_loops": [{"loop_id": item} for item in loop_ids],
    }


def _gl50_report(
    *,
    status: str,
    rows: list[dict[str, Any]],
    open_item_count: int,
    closed_item_count: int,
) -> dict[str, Any]:
    mismatch_count = sum(
        1
        for row in rows
        if str(row.get("acknowledgement_ingestion_item_status", "")).strip().lower() == "open"
        and str(row.get("acknowledgement_ingestion_state", "")).strip().lower() == "ack_loop_mismatch"
    )
    ack_missing_count = sum(
        1
        for row in rows
        if str(row.get("acknowledgement_ingestion_item_status", "")).strip().lower() == "open"
        and str(row.get("acknowledgement_ingestion_state", "")).strip().lower() == "ack_missing"
    )
    missing_handoff_count = sum(
        1
        for row in rows
        if str(row.get("acknowledgement_ingestion_item_status", "")).strip().lower() == "open"
        and str(row.get("acknowledgement_ingestion_state", "")).strip().lower() == "missing_handoff_queue_item"
    )
    return {
        "schema_version": "real_trial_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion.v1",
        "generated_at_utc": "2026-05-30T00:00:00Z",
        "owner": "controlled-beta-ops",
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_status_gl49": "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_MONITORING",
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_status": status,
        "warning_codes": [],
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_counts": {
            "total_item_count": len(rows),
            "open_item_count": open_item_count,
            "closed_item_count": closed_item_count,
            "escalation_rows_with_acknowledgement_record_count": 0,
            "escalation_rows_with_matching_ack_loop_count": 0,
            "escalation_rows_with_mismatched_ack_loop_count": mismatch_count,
            "escalation_rows_missing_acknowledgement_record_count": ack_missing_count,
            "escalation_rows_without_handoff_queue_item_count": missing_handoff_count,
            "unreferenced_acknowledgement_record_count": 0,
        },
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_rows": rows,
    }


class RealTrialSubmissionQueueFollowupResolutionEscalationActionPlanClosureCadenceEscalationAcknowledgementClosureScriptTests(
    unittest.TestCase
):
    def test_not_required_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            gl50 = root / "gl50.json"
            gl12 = root / "gl12.json"
            gl51 = root / "gl51.json"

            _write_json(
                gl50,
                _gl50_report(
                    status="ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_NOT_REQUIRED",
                    rows=[],
                    open_item_count=0,
                    closed_item_count=0,
                ),
            )
            _write_json(gl12, _collection_report(loop_ids=[]))

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-ingestion-report",
                    str(gl50),
                    "--collection-report",
                    str(gl12),
                    "--output",
                    str(gl51),
                    "--summary-output",
                    "-",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            payload = json.loads(gl51.read_text(encoding="utf-8"))
            self.assertEqual(
                payload.get(
                    "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_status"
                ),
                "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_NOT_REQUIRED",
            )
            counts = payload.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_counts",
                {},
            )
            self.assertEqual(int(counts.get("open_item_count", 0)), 0)

    def test_progressing_path_with_previous_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            gl50 = root / "gl50.json"
            gl12 = root / "gl12.json"
            previous_gl51 = root / "gl51.prev.json"
            gl51 = root / "gl51.json"

            _write_json(
                gl50,
                _gl50_report(
                    status="ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_ACTION_REQUIRED",
                    rows=[
                        {
                            "acknowledgement_ingestion_item_id": "gl50-ack-ingestion-gl46-slot-001-text",
                            "acknowledgement_ingestion_item_status": "open",
                            "acknowledgement_ingestion_state": "ack_loop_mismatch",
                            "owner": "controlled-beta-ops",
                            "action_id_gl48": "gl46-slot-001-text",
                            "required_modality_gl47": "text",
                            "handoff_queue_item_id_gl24": "gl24-queue-gl23-slot-001-text",
                            "linked_submission_loop_id_gl24": "real-text-001",
                            "acknowledged_submitted_loop_id_gl25": "real-text-999",
                            "acknowledgement_loop_matches_linked_submission": False,
                        }
                    ],
                    open_item_count=1,
                    closed_item_count=0,
                ),
            )
            _write_json(gl12, _collection_report(loop_ids=["real-text-001", "real-audio-001"]))
            _write_json(
                previous_gl51,
                {
                    "schema_version": "real_trial_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure.v1",
                    "generated_at_utc": "2026-05-29T00:00:00Z",
                    "acknowledgement_ingestion_snapshot": {
                        "open_item_count": 2,
                        "open_item_ids": [
                            "gl50-ack-ingestion-gl46-slot-001-text",
                            "gl50-ack-ingestion-gl46-slot-002-audio",
                        ],
                    },
                    "collection_snapshot": {
                        "launch_gate_eligible_complete_loop_count": 1,
                        "launch_gate_eligible_loop_ids": ["real-text-001"],
                    },
                },
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-ingestion-report",
                    str(gl50),
                    "--collection-report",
                    str(gl12),
                    "--previous-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-report",
                    str(previous_gl51),
                    "--output",
                    str(gl51),
                    "--summary-output",
                    "-",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            payload = json.loads(gl51.read_text(encoding="utf-8"))
            self.assertEqual(
                payload.get(
                    "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_status"
                ),
                "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_PROGRESSING",
            )
            counts = payload.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_counts",
                {},
            )
            self.assertEqual(int(counts.get("net_new_closed_item_count", 0)), 1)
            self.assertEqual(int(counts.get("net_new_launch_gate_eligible_loop_count", 0)), 1)
            self.assertEqual(int(counts.get("carried_open_item_count", 0)), 1)
            self.assertEqual(int(counts.get("open_item_count_delta", 0)), -1)
            self.assertEqual(
                payload.get("net_new_closed_acknowledgement_ingestion_item_ids", []),
                ["gl50-ack-ingestion-gl46-slot-002-audio"],
            )
            rows = payload.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_rows",
                [],
            )
            self.assertGreaterEqual(len(rows), 2)

    def test_stalled_fail_on_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            gl50 = root / "gl50.json"
            gl12 = root / "gl12.json"
            previous_gl51 = root / "gl51.prev.json"
            gl51 = root / "gl51.json"

            _write_json(
                gl50,
                _gl50_report(
                    status="ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_ACTION_REQUIRED",
                    rows=[
                        {
                            "acknowledgement_ingestion_item_id": "gl50-ack-ingestion-gl46-slot-001-text",
                            "acknowledgement_ingestion_item_status": "open",
                            "acknowledgement_ingestion_state": "ack_loop_mismatch",
                            "owner": "controlled-beta-ops",
                            "action_id_gl48": "gl46-slot-001-text",
                            "required_modality_gl47": "text",
                            "handoff_queue_item_id_gl24": "gl24-queue-gl23-slot-001-text",
                            "linked_submission_loop_id_gl24": "real-text-001",
                            "acknowledged_submitted_loop_id_gl25": "real-text-999",
                            "acknowledgement_loop_matches_linked_submission": False,
                        }
                    ],
                    open_item_count=1,
                    closed_item_count=0,
                ),
            )
            _write_json(gl12, _collection_report(loop_ids=["real-text-001"]))
            _write_json(
                previous_gl51,
                {
                    "schema_version": "real_trial_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure.v1",
                    "generated_at_utc": "2026-05-29T00:00:00Z",
                    "acknowledgement_ingestion_snapshot": {
                        "open_item_count": 1,
                        "open_item_ids": ["gl50-ack-ingestion-gl46-slot-001-text"],
                    },
                    "collection_snapshot": {
                        "launch_gate_eligible_complete_loop_count": 1,
                        "launch_gate_eligible_loop_ids": ["real-text-001"],
                    },
                },
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-ingestion-report",
                    str(gl50),
                    "--collection-report",
                    str(gl12),
                    "--previous-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-report",
                    str(previous_gl51),
                    "--output",
                    str(gl51),
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
            payload = json.loads(gl51.read_text(encoding="utf-8"))
            self.assertEqual(
                payload.get(
                    "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_status"
                ),
                "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_STALLED",
            )
            warnings = payload.get("warning_codes", [])
            self.assertIn("stale_open_acknowledgement_ingestion_items_present", warnings)


if __name__ == "__main__":
    unittest.main()
