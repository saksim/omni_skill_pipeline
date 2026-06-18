from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "gl57_closure_cadence_escalation_closure.py"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _gl56_report(*, status: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    open_count = sum(
        1 for row in rows if str(row.get("escalation_item_status", "")).strip().lower() == "open"
    )
    return {
        "schema_version": "real_trial_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations.v1",
        "generated_at_utc": "2026-05-31T00:00:00Z",
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_status_gl55": "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ON_SCHEDULE",
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_status": status,
        "warning_codes": [],
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_counts": {
            "total_item_count": open_count,
            "open_item_count": open_count,
            "blocked_overdue_stalled_item_count": 0,
            "due_item_count": 0,
            "monitor_item_count": open_count,
            "cadence_stall_cycle_count_gl55": 0,
            "cadence_overdue_stalled_cycles_threshold_gl55": 2,
            "escalate_after_due_hours": 24.0,
        },
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_rows": rows,
    }


def _gl54_report(*, rows: list[dict[str, Any]], previous_report_path: str = "") -> dict[str, Any]:
    open_count = sum(
        1 for row in rows if str(row.get("closure_item_status", "")).strip().lower() == "open"
    )
    return {
        "schema_version": "real_trial_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure.v1",
        "generated_at_utc": "2026-05-31T00:00:00Z",
        "input_paths": {
            "previous_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_report": previous_report_path
        },
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_status": (
            "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_PROGRESSING"
        ),
        "warning_codes": [],
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_counts": {
            "total_item_count": open_count,
            "open_item_count": open_count,
        },
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_rows": rows,
    }


class RealTrialSubmissionQueueFollowupResolutionEscalationActionPlanClosureCadenceEscalationAcknowledgementClosureCadenceEscalationClosureCadenceEscalationClosureScriptTests(
    unittest.TestCase
):
    def test_not_required_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            gl56 = root / "gl56.json"
            gl54 = root / "gl54.json"
            gl57 = root / "gl57.json"
            _write_json(
                gl56,
                _gl56_report(
                    status=(
                        "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_NOT_REQUIRED"
                    ),
                    rows=[],
                ),
            )
            _write_json(gl54, _gl54_report(rows=[]))

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalations-report",
                    str(gl56),
                    "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-report",
                    str(gl54),
                    "--output",
                    str(gl57),
                    "--summary-output",
                    "-",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            payload = json.loads(gl57.read_text(encoding="utf-8"))
            self.assertEqual(
                payload.get(
                    "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_status"
                ),
                "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_NOT_REQUIRED",
            )
            counts = payload.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_counts",
                {},
            )
            self.assertEqual(int(counts.get("open_item_count", 0)), 0)

    def test_progressing_path_reports_gl54_backed_net_new_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            gl56 = root / "gl56.json"
            gl54 = root / "gl54.json"
            previous_gl54 = root / "previous-gl54.json"
            previous_gl57 = root / "previous-gl57.json"
            gl57 = root / "gl57.json"

            _write_json(
                gl56,
                _gl56_report(
                    status=(
                        "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_MONITORING"
                    ),
                    rows=[
                        {
                            "escalation_item_id": "gl56-esc-002",
                            "escalation_item_status": "open",
                            "escalation_severity": "monitor",
                            "action_id_gl48": "gl46-slot-002-audio",
                            "required_modality_gl47": "audio",
                            "acknowledgement_ingestion_item_id_gl55": "gl50-ack-002",
                            "owner": "controlled-beta-ops",
                        }
                    ],
                ),
            )
            _write_json(
                previous_gl54,
                {
                    "schema_version": "real_trial_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure.v1",
                    "generated_at_utc": "2026-05-30T00:00:00Z",
                    "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_rows": [
                        {
                            "closure_item_status": "open",
                            "escalation_item_id_gl53": "gl53-esc-001",
                            "action_id_gl48": "gl46-slot-001-text",
                        },
                        {
                            "closure_item_status": "open",
                            "escalation_item_id_gl53": "gl53-esc-002",
                            "action_id_gl48": "gl46-slot-002-audio",
                        },
                    ],
                },
            )
            _write_json(
                gl54,
                _gl54_report(
                    rows=[
                        {
                            "closure_item_status": "open",
                            "escalation_item_id_gl53": "gl53-esc-002",
                            "action_id_gl48": "gl46-slot-002-audio",
                        }
                    ],
                    previous_report_path=str(previous_gl54),
                ),
            )
            _write_json(
                previous_gl57,
                {
                    "schema_version": "real_trial_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure.v1",
                    "generated_at_utc": "2026-05-30T00:00:00Z",
                    "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_rows": [
                        {
                            "closure_item_status": "open",
                            "escalation_item_id_gl56": "gl56-esc-001",
                            "action_id_gl48": "gl46-slot-001-text",
                        },
                        {
                            "closure_item_status": "open",
                            "escalation_item_id_gl56": "gl56-esc-002",
                            "action_id_gl48": "gl46-slot-002-audio",
                        },
                    ],
                },
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalations-report",
                    str(gl56),
                    "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-report",
                    str(gl54),
                    "--previous-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-report",
                    str(previous_gl57),
                    "--output",
                    str(gl57),
                    "--summary-output",
                    "-",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            payload = json.loads(gl57.read_text(encoding="utf-8"))
            self.assertEqual(
                payload.get(
                    "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_status"
                ),
                "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_PROGRESSING",
            )
            counts = payload.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_counts",
                {},
            )
            self.assertEqual(int(counts.get("open_item_count", 0)), 1)
            self.assertEqual(int(counts.get("previous_open_item_count", 0)), 2)
            self.assertEqual(int(counts.get("carried_open_item_count", 0)), 1)
            self.assertEqual(int(counts.get("net_new_closed_item_count", 0)), 1)
            self.assertEqual(
                int(counts.get("net_new_closed_backed_by_gl54_net_new_closed_item_count", 0)),
                1,
            )
            self.assertEqual(
                payload.get(
                    "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_item_ids"
                ),
                ["gl56-esc-001"],
            )

    def test_stalled_path_fails_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            gl56 = root / "gl56.json"
            gl54 = root / "gl54.json"
            previous_gl57 = root / "previous-gl57.json"
            gl57 = root / "gl57.json"

            row = {
                "escalation_item_id": "gl56-esc-002",
                "escalation_item_status": "open",
                "escalation_severity": "monitor",
                "action_id_gl48": "gl46-slot-002-audio",
                "required_modality_gl47": "audio",
                "acknowledgement_ingestion_item_id_gl55": "gl50-ack-002",
                "owner": "controlled-beta-ops",
            }
            _write_json(
                gl56,
                _gl56_report(
                    status=(
                        "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_MONITORING"
                    ),
                    rows=[row],
                ),
            )
            _write_json(gl54, _gl54_report(rows=[]))
            _write_json(
                previous_gl57,
                {
                    "schema_version": "real_trial_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure.v1",
                    "generated_at_utc": "2026-05-30T00:00:00Z",
                    "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_rows": [
                        {
                            "closure_item_status": "open",
                            "escalation_item_id_gl56": "gl56-esc-002",
                            "action_id_gl48": "gl46-slot-002-audio",
                        }
                    ],
                },
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalations-report",
                    str(gl56),
                    "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-report",
                    str(gl54),
                    "--previous-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-report",
                    str(previous_gl57),
                    "--output",
                    str(gl57),
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
            payload = json.loads(gl57.read_text(encoding="utf-8"))
            self.assertEqual(
                payload.get(
                    "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_status"
                ),
                "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_STALLED",
            )
            warning_codes = payload.get("warning_codes", [])
            self.assertIn(
                "acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_stalled",
                warning_codes,
            )


if __name__ == "__main__":
    unittest.main()

