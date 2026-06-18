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
    / "gl49_cadence_escalations.py"
)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _cadence_report(
    *,
    status: str,
    cadence_state: str,
    due_in_hours: float,
    rows: list[dict[str, Any]],
    next_refresh_due_utc: str,
    stall_cycle_count: int = 0,
) -> dict[str, Any]:
    open_count = sum(
        1
        for row in rows
        if str(row.get("cadence_item_status", "")).strip().lower()
        not in {"closed", "closed_since_previous_cycle"}
    )
    return {
        "schema_version": "real_trial_submission_queue_followup_resolution_escalation_action_plan_closure_cadence.v1",
        "generated_at_utc": "2026-05-30T00:00:00Z",
        "followup_resolution_escalation_action_plan_closure_status_gl47": "ACTION_PLAN_CLOSURE_PROGRESSING",
        "followup_resolution_escalation_action_plan_closure_cadence_status": status,
        "warning_codes": [],
        "followup_resolution_escalation_action_plan_closure_cadence_counts": {
            "total_action_count": len(rows),
            "open_action_count": open_count,
            "stale_open_action_count": 0,
            "net_new_closed_action_count_gl47": 0,
            "net_new_launch_gate_eligible_loop_count_gl47": 0,
            "stall_cycle_count": stall_cycle_count,
            "overdue_stalled_cycles_threshold": 2,
        },
        "refresh_cadence": {
            "refresh_interval_hours": 24.0,
            "cadence_status": cadence_state,
            "previous_generated_at_utc": "2026-05-29T00:00:00Z",
            "next_refresh_due_utc": next_refresh_due_utc,
            "due_in_hours": due_in_hours,
            "evaluated_at_utc": "2026-05-30T00:00:00Z",
        },
        "followup_resolution_escalation_action_plan_closure_cadence_rows": rows,
    }


class RealTrialSubmissionQueueFollowupResolutionEscalationActionPlanClosureCadenceEscalationsScriptTests(
    unittest.TestCase
):
    def test_not_required_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            gl48 = root / "gl48.json"
            gl49 = root / "gl49.json"
            _write_json(
                gl48,
                _cadence_report(
                    status="ACTION_PLAN_CLOSURE_CADENCE_NOT_REQUIRED",
                    cadence_state="CADENCE_NOT_REQUIRED",
                    due_in_hours=0.0,
                    rows=[],
                    next_refresh_due_utc="",
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-report",
                    str(gl48),
                    "--output",
                    str(gl49),
                    "--summary-output",
                    "-",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            payload = json.loads(gl49.read_text(encoding="utf-8"))
            self.assertEqual(
                payload.get("followup_resolution_escalation_action_plan_closure_cadence_escalation_status"),
                "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_NOT_REQUIRED",
            )
            counts = payload.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_counts",
                {},
            )
            self.assertEqual(int(counts.get("open_item_count", 0)), 0)

    def test_due_path_generates_due_escalation_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            gl48 = root / "gl48.json"
            gl49 = root / "gl49.json"
            _write_json(
                gl48,
                _cadence_report(
                    status="ACTION_PLAN_CLOSURE_CADENCE_DUE",
                    cadence_state="CADENCE_DUE",
                    due_in_hours=-6.0,
                    rows=[
                        {
                            "action_id": "gl46-slot-001-text",
                            "closure_state_gl47": "open_new",
                            "cadence_item_status": "refresh_due",
                            "required_modality_gl47": "text",
                            "owner_gl47": "controlled-beta-ops",
                            "linked_submission_loop_id_gl47": "",
                        }
                    ],
                    next_refresh_due_utc="2026-05-29T18:00:00Z",
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-report",
                    str(gl48),
                    "--output",
                    str(gl49),
                    "--summary-output",
                    "-",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            payload = json.loads(gl49.read_text(encoding="utf-8"))
            self.assertEqual(
                payload.get("followup_resolution_escalation_action_plan_closure_cadence_escalation_status"),
                "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_DUE",
            )
            rows = payload.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_rows",
                [],
            )
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].get("escalation_severity"), "due")
            warning_codes = payload.get("warning_codes", [])
            self.assertIn("action_plan_closure_cadence_due_escalation_required", warning_codes)

    def test_overdue_stalled_fail_on_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            gl48 = root / "gl48.json"
            gl49 = root / "gl49.json"
            _write_json(
                gl48,
                _cadence_report(
                    status="ACTION_PLAN_CLOSURE_CADENCE_OVERDUE_STALLED",
                    cadence_state="CADENCE_OVERDUE_STALLED",
                    due_in_hours=-50.0,
                    rows=[
                        {
                            "action_id": "gl46-slot-001-text",
                            "closure_state_gl47": "open_carried",
                            "cadence_item_status": "refresh_due",
                            "required_modality_gl47": "text",
                            "owner_gl47": "controlled-beta-ops",
                            "linked_submission_loop_id_gl47": "real-text-001",
                        }
                    ],
                    next_refresh_due_utc="2026-05-28T00:00:00Z",
                    stall_cycle_count=3,
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-report",
                    str(gl48),
                    "--output",
                    str(gl49),
                    "--summary-output",
                    "-",
                    "--fail-on-overdue-stalled",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr + completed.stdout)
            payload = json.loads(gl49.read_text(encoding="utf-8"))
            self.assertEqual(
                payload.get("followup_resolution_escalation_action_plan_closure_cadence_escalation_status"),
                "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_OVERDUE_STALLED",
            )
            rows = payload.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_rows",
                [],
            )
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].get("escalation_severity"), "blocked_overdue_stalled")


if __name__ == "__main__":
    unittest.main()
