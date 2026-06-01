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
    / "gl61_closure_cadence_escalation_closure_cadence_escalation_closure_cadence.py"
)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _gl60_report(*, status: str, generated_at_utc: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    open_count = sum(
        1 for row in rows if str(row.get("closure_item_status", "")).strip().lower() == "open"
    )
    return {
        "schema_version": "real_trial_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure.v1",
        "generated_at_utc": generated_at_utc,
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_status_gl59": "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_MONITORING",
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_status_gl57": "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_PROGRESSING",
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_status": status,
        "warning_codes": [],
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_counts": {
            "total_item_count": open_count,
            "open_item_count": open_count,
            "previous_open_item_count": open_count,
            "carried_open_item_count": sum(
                1
                for row in rows
                if str(row.get("closure_progress_state", "")).strip().lower() == "carried_open"
            ),
            "stale_open_item_count": sum(
                1
                for row in rows
                if str(row.get("closure_progress_state", "")).strip().lower() == "carried_open"
            ),
            "net_new_open_item_count": sum(
                1
                for row in rows
                if str(row.get("closure_progress_state", "")).strip().lower() == "net_new_open"
            ),
            "net_new_closed_item_count": 0,
            "net_new_closed_backed_by_gl57_net_new_closed_item_count": 0,
            "net_new_closed_without_gl57_net_new_closed_item_count": 0,
            "gl57_net_new_closed_item_count": 0,
            "gl57_net_new_closed_action_item_count": 0,
        },
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_rows": rows,
    }


class RealTrialSubmissionQueueFollowupResolutionEscalationActionPlanClosureCadenceEscalationAcknowledgementClosureCadenceEscalationClosureCadenceEscalationClosureCadenceEscalationClosureCadenceScriptTests(
    unittest.TestCase
):
    def test_not_required_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            gl60 = root / "gl60.json"
            gl61 = root / "gl61.json"

            _write_json(
                gl60,
                _gl60_report(
                    status="ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_NOT_REQUIRED",
                    generated_at_utc="2026-06-01T00:00:00Z",
                    rows=[],
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalation-closure-report",
                    str(gl60),
                    "--output",
                    str(gl61),
                    "--summary-output",
                    "-",
                    "--now-utc",
                    "2026-06-01T01:00:00Z",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            payload = json.loads(gl61.read_text(encoding="utf-8"))
            self.assertEqual(
                payload.get(
                    "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_status"
                ),
                "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_NOT_REQUIRED",
            )
            cadence = payload.get("refresh_cadence", {})
            self.assertEqual(cadence.get("cadence_status"), "CADENCE_NOT_REQUIRED")
            self.assertEqual(cadence.get("next_refresh_due_utc"), "")
            self.assertEqual(payload.get("warning_codes"), [])

    def test_due_path_from_previous_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            gl60 = root / "gl60.json"
            gl61 = root / "gl61.json"

            _write_json(
                gl60,
                _gl60_report(
                    status="ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_PROGRESSING",
                    generated_at_utc="2026-06-01T00:00:00Z",
                    rows=[
                        {
                            "closure_item_id": "gl60-closure-cadence-escalation-closure-cadence-escalation-closure-gl59-esc-001",
                            "closure_item_status": "open",
                            "closure_progress_state": "net_new_open",
                            "required_modality_gl47": "text",
                            "action_id_gl48": "gl46-slot-001-text",
                            "escalation_item_id_gl59": "gl59-esc-001",
                        }
                    ],
                ),
            )

            baseline = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalation-closure-report",
                    str(gl60),
                    "--output",
                    str(gl61),
                    "--summary-output",
                    "-",
                    "--now-utc",
                    "2026-06-01T01:00:00Z",
                    "--refresh-interval-hours",
                    "24",
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
                    "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalation-closure-report",
                    str(gl60),
                    "--output",
                    str(gl61),
                    "--summary-output",
                    "-",
                    "--now-utc",
                    "2026-06-02T03:00:00Z",
                    "--refresh-interval-hours",
                    "24",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            payload = json.loads(gl61.read_text(encoding="utf-8"))
            self.assertEqual(
                payload.get(
                    "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_status"
                ),
                "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_DUE",
            )
            cadence = payload.get("refresh_cadence", {})
            self.assertEqual(cadence.get("cadence_status"), "CADENCE_DUE")
            warning_codes = payload.get("warning_codes", [])
            self.assertIn(
                "acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_due",
                warning_codes,
            )
            rows = payload.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_rows",
                [],
            )
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].get("cadence_item_status"), "refresh_due")

    def test_overdue_stalled_fail_on_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            gl60 = root / "gl60.json"
            gl61 = root / "gl61.json"

            _write_json(
                gl60,
                _gl60_report(
                    status="ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_STALLED",
                    generated_at_utc="2026-06-01T00:00:00Z",
                    rows=[
                        {
                            "closure_item_id": "gl60-closure-cadence-escalation-closure-cadence-escalation-closure-gl59-esc-001",
                            "closure_item_status": "open",
                            "closure_progress_state": "carried_open",
                            "required_modality_gl47": "text",
                            "action_id_gl48": "gl46-slot-001-text",
                            "escalation_item_id_gl59": "gl59-esc-001",
                        }
                    ],
                ),
            )

            baseline = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalation-closure-report",
                    str(gl60),
                    "--output",
                    str(gl61),
                    "--summary-output",
                    "-",
                    "--now-utc",
                    "2026-06-01T01:00:00Z",
                    "--refresh-interval-hours",
                    "24",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(baseline.returncode, 0, baseline.stderr + baseline.stdout)

            second = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalation-closure-report",
                    str(gl60),
                    "--output",
                    str(gl61),
                    "--summary-output",
                    "-",
                    "--now-utc",
                    "2026-06-02T03:30:00Z",
                    "--refresh-interval-hours",
                    "24",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(second.returncode, 0, second.stderr + second.stdout)

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalation-closure-report",
                    str(gl60),
                    "--output",
                    str(gl61),
                    "--summary-output",
                    "-",
                    "--now-utc",
                    "2026-06-03T05:00:00Z",
                    "--refresh-interval-hours",
                    "24",
                    "--overdue-stalled-cycles",
                    "2",
                    "--fail-on-overdue-stalled",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr + completed.stdout)
            payload = json.loads(gl61.read_text(encoding="utf-8"))
            self.assertEqual(
                payload.get(
                    "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_status"
                ),
                "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_OVERDUE_STALLED",
            )
            counts = payload.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_counts",
                {},
            )
            self.assertGreaterEqual(int(counts.get("stall_cycle_count", 0)), 2)
            warning_codes = payload.get("warning_codes", [])
            self.assertIn(
                "acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_overdue_stalled",
                warning_codes,
            )
            self.assertIn(
                "acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_stalled",
                warning_codes,
            )


if __name__ == "__main__":
    unittest.main()
