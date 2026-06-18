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
    / "gl48_action_plan_cadence.py"
)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _gl47_closure_report(
    *,
    status: str,
    generated_at_utc: str,
    rows: list[dict[str, Any]],
    warning_codes: list[str] | None = None,
    stale_open_action_count: int = 0,
    net_new_closed_action_count: int = 0,
    net_new_launch_gate_eligible_loop_count: int = 0,
) -> dict[str, Any]:
    warnings = warning_codes if isinstance(warning_codes, list) else []
    open_count = sum(
        1
        for row in rows
        if str(row.get("closure_state", "")).strip() in {"open_new", "open_carried"}
    )
    return {
        "schema_version": "real_trial_submission_queue_followup_resolution_escalation_action_plan_closure.v1",
        "generated_at_utc": generated_at_utc,
        "followup_resolution_escalation_action_plan_closure_status": status,
        "warning_codes": warnings,
        "followup_resolution_escalation_action_plan_closure_counts": {
            "total_action_count": len(rows),
            "open_action_count": open_count,
            "closed_action_count": len(rows) - open_count,
            "carried_open_action_count": sum(
                1 for row in rows if str(row.get("closure_state", "")).strip() == "open_carried"
            ),
            "net_new_closed_action_count": int(net_new_closed_action_count),
            "stale_open_action_count": int(stale_open_action_count),
            "net_new_launch_gate_eligible_loop_count": int(net_new_launch_gate_eligible_loop_count),
            "open_action_count_delta": 0,
        },
        "followup_resolution_escalation_action_plan_closure_rows": rows,
    }


def _gl12_collection_report(*, program_status: str) -> dict[str, Any]:
    return {
        "schema_version": "real_trial_loop_collection.v1",
        "generated_at_utc": "2026-05-30T00:01:00Z",
        "launch_gate_alignment": {
            "program_status": program_status,
            "launch_gate_eligible_complete_loop_count": 1,
            "launch_gate_eligible_modality_count": 1,
            "missing_complete_loops_to_threshold": 9,
            "missing_modalities_to_threshold": 3,
        },
        "collected_real_launch_gate_eligible_loops": [
            {"loop_id": "real-text-001", "modality": "text"},
        ],
    }


class RealTrialSubmissionQueueFollowupResolutionEscalationActionPlanClosureCadenceScriptTests(
    unittest.TestCase
):
    def test_not_required_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            gl47 = root / "gl47.json"
            gl12 = root / "gl12.json"
            gl48 = root / "gl48.json"
            _write_json(
                gl47,
                _gl47_closure_report(
                    status="ACTION_PLAN_CLOSURE_NOT_REQUIRED",
                    generated_at_utc="2026-05-30T00:00:00Z",
                    rows=[],
                ),
            )
            _write_json(gl12, _gl12_collection_report(program_status="COLLECTION_INCOMPLETE"))

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-escalation-action-plan-closure-report",
                    str(gl47),
                    "--collection-report",
                    str(gl12),
                    "--output",
                    str(gl48),
                    "--summary-output",
                    "-",
                    "--now-utc",
                    "2026-05-30T01:00:00Z",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            payload = json.loads(gl48.read_text(encoding="utf-8"))
            self.assertEqual(
                payload.get("followup_resolution_escalation_action_plan_closure_cadence_status"),
                "ACTION_PLAN_CLOSURE_CADENCE_NOT_REQUIRED",
            )
            cadence = payload.get("refresh_cadence", {})
            self.assertEqual(cadence.get("cadence_status"), "CADENCE_NOT_REQUIRED")
            self.assertEqual(cadence.get("next_refresh_due_utc"), "")
            self.assertEqual(payload.get("warning_codes"), [])

    def test_due_path_from_previous_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            gl47 = root / "gl47.json"
            gl12 = root / "gl12.json"
            gl48 = root / "gl48.json"

            _write_json(
                gl47,
                _gl47_closure_report(
                    status="ACTION_PLAN_CLOSURE_PROGRESSING",
                    generated_at_utc="2026-05-30T00:00:00Z",
                    rows=[
                        {
                            "action_id": "gl46-slot-001-text",
                            "closure_state": "open_new",
                            "required_modality_gl46": "text",
                            "owner_gl46": "controlled-beta-ops",
                            "linked_submission_loop_id_gl46": "",
                        }
                    ],
                    net_new_launch_gate_eligible_loop_count=1,
                ),
            )
            _write_json(gl12, _gl12_collection_report(program_status="COLLECTION_INCOMPLETE"))

            baseline = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-escalation-action-plan-closure-report",
                    str(gl47),
                    "--collection-report",
                    str(gl12),
                    "--output",
                    str(gl48),
                    "--summary-output",
                    "-",
                    "--now-utc",
                    "2026-05-30T01:00:00Z",
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
                    "--submission-queue-followup-resolution-escalation-action-plan-closure-report",
                    str(gl47),
                    "--collection-report",
                    str(gl12),
                    "--output",
                    str(gl48),
                    "--summary-output",
                    "-",
                    "--now-utc",
                    "2026-05-31T03:00:00Z",
                    "--refresh-interval-hours",
                    "24",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            payload = json.loads(gl48.read_text(encoding="utf-8"))
            self.assertEqual(
                payload.get("followup_resolution_escalation_action_plan_closure_cadence_status"),
                "ACTION_PLAN_CLOSURE_CADENCE_DUE",
            )
            cadence = payload.get("refresh_cadence", {})
            self.assertEqual(cadence.get("cadence_status"), "CADENCE_DUE")
            warning_codes = payload.get("warning_codes", [])
            self.assertIn("action_plan_closure_cadence_due", warning_codes)
            rows = payload.get("followup_resolution_escalation_action_plan_closure_cadence_rows", [])
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].get("cadence_item_status"), "refresh_due")

    def test_overdue_stalled_fail_on_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            gl47 = root / "gl47.json"
            gl12 = root / "gl12.json"
            gl48 = root / "gl48.json"

            _write_json(
                gl47,
                _gl47_closure_report(
                    status="ACTION_PLAN_CLOSURE_STALLED",
                    generated_at_utc="2026-05-30T00:00:00Z",
                    rows=[
                        {
                            "action_id": "gl46-slot-001-text",
                            "closure_state": "open_carried",
                            "required_modality_gl46": "text",
                            "owner_gl46": "controlled-beta-ops",
                            "linked_submission_loop_id_gl46": "real-text-001",
                        }
                    ],
                    stale_open_action_count=1,
                ),
            )
            _write_json(gl12, _gl12_collection_report(program_status="COLLECTION_INCOMPLETE"))

            baseline = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-escalation-action-plan-closure-report",
                    str(gl47),
                    "--collection-report",
                    str(gl12),
                    "--output",
                    str(gl48),
                    "--summary-output",
                    "-",
                    "--now-utc",
                    "2026-05-30T01:00:00Z",
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
                    "--submission-queue-followup-resolution-escalation-action-plan-closure-report",
                    str(gl47),
                    "--collection-report",
                    str(gl12),
                    "--output",
                    str(gl48),
                    "--summary-output",
                    "-",
                    "--now-utc",
                    "2026-05-31T03:30:00Z",
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
                    "--submission-queue-followup-resolution-escalation-action-plan-closure-report",
                    str(gl47),
                    "--collection-report",
                    str(gl12),
                    "--output",
                    str(gl48),
                    "--summary-output",
                    "-",
                    "--now-utc",
                    "2026-06-01T05:00:00Z",
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
            payload = json.loads(gl48.read_text(encoding="utf-8"))
            self.assertEqual(
                payload.get("followup_resolution_escalation_action_plan_closure_cadence_status"),
                "ACTION_PLAN_CLOSURE_CADENCE_OVERDUE_STALLED",
            )
            counts = payload.get("followup_resolution_escalation_action_plan_closure_cadence_counts", {})
            self.assertGreaterEqual(int(counts.get("stall_cycle_count", 0)), 2)
            warning_codes = payload.get("warning_codes", [])
            self.assertIn("action_plan_closure_cadence_overdue_stalled", warning_codes)
            self.assertIn("action_plan_closure_stalled", warning_codes)


if __name__ == "__main__":
    unittest.main()
