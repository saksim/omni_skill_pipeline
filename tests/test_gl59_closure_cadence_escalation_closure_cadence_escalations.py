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
    / "gl59_closure_cadence_escalation_closure_cadence_escalations.py"
)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _gl58_report(*, status: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    open_count = sum(
        1 for row in rows if str(row.get("cadence_item_status", "")).strip().lower() != "closed"
    )
    return {
        "schema_version": "real_trial_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence.v1",
        "generated_at_utc": "2026-05-31T00:00:00Z",
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_status_gl57": "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_PROGRESSING",
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_status": status,
        "warning_codes": [],
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_counts": {
            "total_item_count": open_count,
            "open_item_count": open_count,
            "stale_open_item_count": 0,
            "net_new_closed_item_count_gl57": 0,
            "net_new_closed_backed_by_gl54_net_new_closed_item_count": 0,
            "stall_cycle_count": 0,
            "overdue_stalled_cycles_threshold": 2,
        },
        "refresh_cadence": {
            "cadence_status": "CADENCE_BASELINE_INITIALIZED",
            "previous_generated_at_utc": "",
            "next_refresh_due_utc": "2026-06-01T00:00:00Z",
            "due_in_hours": 24.0,
            "evaluated_at_utc": "2026-05-31T00:00:00Z",
            "refresh_interval_hours": 24.0,
        },
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_rows": rows,
    }


class RealTrialSubmissionQueueFollowupResolutionEscalationActionPlanClosureCadenceEscalationAcknowledgementClosureCadenceEscalationClosureCadenceEscalationClosureCadenceEscalationsScriptTests(
    unittest.TestCase
):
    def test_not_required_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            gl58 = root / "gl58.json"
            gl59 = root / "gl59.json"
            _write_json(
                gl58,
                _gl58_report(
                    status="ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_NOT_REQUIRED",
                    rows=[],
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-report",
                    str(gl58),
                    "--output",
                    str(gl59),
                    "--summary-output",
                    "-",
                    "--now-utc",
                    "2026-05-31T01:00:00Z",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            payload = json.loads(gl59.read_text(encoding="utf-8"))
            self.assertEqual(
                payload.get(
                    "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_status"
                ),
                "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_NOT_REQUIRED",
            )
            self.assertEqual(payload.get("warning_codes"), [])
            counts = payload.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_counts",
                {},
            )
            self.assertEqual(counts.get("total_item_count"), 0)

    def test_due_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            gl58 = root / "gl58.json"
            gl59 = root / "gl59.json"
            _write_json(
                gl58,
                _gl58_report(
                    status="ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_DUE",
                    rows=[
                        {
                            "closure_item_id_gl57": "gl57-closure-cadence-escalation-closure-gl56-esc-001",
                            "closure_item_status_gl57": "open",
                            "closure_progress_state_gl57": "net_new_open",
                            "action_id_gl48": "gl46-slot-001-text",
                            "required_modality_gl47": "text",
                            "escalation_item_id_gl56": "gl56-esc-001",
                            "acknowledgement_ingestion_item_id_gl55": "gl55-ingestion-001",
                            "escalation_severity_gl56": "monitor",
                            "cadence_item_status": "refresh_due",
                            "next_refresh_due_utc_gl58": "2026-05-31T00:00:00Z",
                        }
                    ],
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-report",
                    str(gl58),
                    "--output",
                    str(gl59),
                    "--summary-output",
                    "-",
                    "--now-utc",
                    "2026-06-01T03:00:00Z",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            payload = json.loads(gl59.read_text(encoding="utf-8"))
            self.assertEqual(
                payload.get(
                    "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_status"
                ),
                "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_DUE",
            )
            warning_codes = payload.get("warning_codes", [])
            self.assertIn(
                "acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_due_escalation_required",
                warning_codes,
            )
            rows = payload.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_rows",
                [],
            )
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].get("escalation_severity"), "due_breached")

    def test_overdue_stalled_fail_on_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            gl58 = root / "gl58.json"
            gl59 = root / "gl59.json"
            _write_json(
                gl58,
                _gl58_report(
                    status="ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_OVERDUE_STALLED",
                    rows=[
                        {
                            "closure_item_id_gl57": "gl57-closure-cadence-escalation-closure-gl56-esc-001",
                            "closure_item_status_gl57": "open",
                            "closure_progress_state_gl57": "carried_open",
                            "action_id_gl48": "gl46-slot-001-text",
                            "required_modality_gl47": "text",
                            "cadence_item_status": "refresh_due",
                        }
                    ],
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-report",
                    str(gl58),
                    "--output",
                    str(gl59),
                    "--summary-output",
                    "-",
                    "--now-utc",
                    "2026-06-01T03:00:00Z",
                    "--fail-on-overdue-stalled",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr + completed.stdout)
            payload = json.loads(gl59.read_text(encoding="utf-8"))
            self.assertEqual(
                payload.get(
                    "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_status"
                ),
                "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_OVERDUE_STALLED",
            )
            counts = payload.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_counts",
                {},
            )
            self.assertEqual(counts.get("blocked_overdue_stalled_item_count"), 1)


if __name__ == "__main__":
    unittest.main()
