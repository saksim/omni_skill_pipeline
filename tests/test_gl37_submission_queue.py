from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "gl37_submission_queue.py"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _throughput_report(
    *,
    action_plan_status: str,
    recommended_actions: list[dict[str, Any]] | None = None,
    priority_modalities: list[dict[str, Any]] | None = None,
    warning_codes: list[str] | None = None,
    throughput_status: str = "THROUGHPUT_STALLED",
    threshold_met: bool = False,
    invalid_submission_count: int = 0,
    unresolved_submission_count: int = 0,
    pending_template_loop_count: int = 0,
) -> dict[str, Any]:
    actions = recommended_actions if isinstance(recommended_actions, list) else []
    modalities = priority_modalities if isinstance(priority_modalities, list) else []
    warnings = warning_codes if isinstance(warning_codes, list) else []
    blockers: list[str] = []
    if action_plan_status != "ACTION_PLAN_NOT_REQUIRED":
        blockers.append("real_loop_volume_below_threshold")
    if action_plan_status == "ACTION_PLAN_BLOCKED_BY_SUBMISSION_ERRORS":
        blockers.append("invalid_submission_rows_present")
    return {
        "schema_version": "real_trial_submission_throughput.v1",
        "generated_at_utc": "2026-05-29T00:00:00Z",
        "throughput_status": throughput_status,
        "threshold_met": threshold_met,
        "warning_codes": warnings,
        "execution_focus": {
            "action_plan_status": action_plan_status,
            "action_plan_blockers": blockers,
            "pending_submission_action_count": len(actions),
            "recommended_submission_action_count": len(actions),
            "priority_modalities": modalities,
            "recommended_submission_actions": actions,
            "submission_consumption_status": "NO_SUBMISSIONS_PROVIDED",
            "submission_consumption_template_loop_count": len(actions),
            "submission_consumption_pending_template_loop_count": pending_template_loop_count,
            "submission_consumption_invalid_submission_count": invalid_submission_count,
            "submission_consumption_unresolved_submission_count": unresolved_submission_count,
        },
        "snapshot": {
            "previous_snapshot_available": True,
            "previous": {},
            "current": {},
            "delta": {},
            "net_new_launch_gate_eligible_real_loop_ids": [],
            "retained_launch_gate_eligible_real_loop_ids": [],
            "dropped_launch_gate_eligible_real_loop_ids": [],
        },
    }


class RealTrialSubmissionQueueScriptTests(unittest.TestCase):
    def test_active_queue_initializes_cadence_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            throughput_report = root / "throughput-report.json"
            queue_report = root / "queue-report.json"
            queue_summary = root / "queue-summary.md"
            _write_json(
                throughput_report,
                _throughput_report(
                    action_plan_status="ACTION_PLAN_WAITING_FOR_SUBMISSIONS",
                    warning_codes=["no_net_new_launch_gate_eligible_real_loops"],
                    recommended_actions=[
                        {
                            "backfill_action_id": "gl23-slot-002-audio",
                            "backfill_slot_index": 2,
                            "required_modality": "audio",
                            "reason": "pending_template_submission_required",
                        },
                        {
                            "backfill_action_id": "gl23-slot-004-video",
                            "backfill_slot_index": 4,
                            "required_modality": "video",
                            "reason": "pending_template_submission_required",
                        },
                    ],
                    priority_modalities=[
                        {"modality": "audio", "pending_slot_count": 1},
                        {"modality": "video", "pending_slot_count": 1},
                    ],
                    pending_template_loop_count=2,
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--throughput-report",
                    str(throughput_report),
                    "--output",
                    str(queue_report),
                    "--summary-output",
                    str(queue_summary),
                    "--now-utc",
                    "2026-05-29T01:00:00Z",
                    "--refresh-interval-hours",
                    "24",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            payload = json.loads(queue_report.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("queue_status"), "QUEUE_ACTIVE")
            queue_summary_payload = payload.get("queue_summary", {})
            self.assertEqual(queue_summary_payload.get("total_item_count"), 2)
            self.assertEqual(queue_summary_payload.get("pending_item_count"), 2)
            self.assertEqual(queue_summary_payload.get("blocked_item_count"), 0)
            queue_items = payload.get("queue_items", [])
            self.assertEqual(queue_items[0].get("backfill_action_id"), "gl23-slot-002-audio")
            self.assertEqual(queue_items[0].get("queue_item_status"), "pending_submission")
            cadence = payload.get("refresh_cadence", {})
            self.assertEqual(cadence.get("cadence_status"), "CADENCE_BASELINE_INITIALIZED")
            self.assertEqual(cadence.get("previous_queue_generated_at_utc"), "")
            self.assertEqual(cadence.get("next_refresh_due_utc"), "2026-05-30T01:00:00Z")
            warning_codes = payload.get("warning_codes", [])
            self.assertIn("submission_queue_refresh_required_until_threshold_met", warning_codes)

    def test_blocked_queue_respects_fail_on_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            throughput_report = root / "throughput-report.json"
            queue_report = root / "queue-report.json"
            _write_json(
                throughput_report,
                _throughput_report(
                    action_plan_status="ACTION_PLAN_BLOCKED_BY_SUBMISSION_ERRORS",
                    recommended_actions=[
                        {
                            "backfill_action_id": "gl23-slot-001-text",
                            "backfill_slot_index": 1,
                            "required_modality": "text",
                            "reason": "pending_template_submission_required",
                        }
                    ],
                    priority_modalities=[{"modality": "text", "pending_slot_count": 1}],
                    invalid_submission_count=1,
                    unresolved_submission_count=1,
                    pending_template_loop_count=1,
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--throughput-report",
                    str(throughput_report),
                    "--output",
                    str(queue_report),
                    "--summary-output",
                    "-",
                    "--fail-on-blocked",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr + completed.stdout)
            payload = json.loads(queue_report.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("queue_status"), "QUEUE_BLOCKED_BY_SUBMISSION_ERRORS")
            queue_summary_payload = payload.get("queue_summary", {})
            self.assertEqual(queue_summary_payload.get("total_item_count"), 1)
            self.assertEqual(queue_summary_payload.get("pending_item_count"), 0)
            self.assertEqual(queue_summary_payload.get("blocked_item_count"), 1)
            self.assertEqual(payload.get("queue_items", [])[0].get("queue_item_status"), "blocked_by_submission_errors")

    def test_cadence_due_returns_nonzero_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            throughput_report = root / "throughput-report.json"
            previous_queue_report = root / "previous-queue-report.json"
            queue_report = root / "queue-report.json"
            _write_json(
                throughput_report,
                _throughput_report(
                    action_plan_status="ACTION_PLAN_WAITING_FOR_SUBMISSIONS",
                    recommended_actions=[
                        {
                            "backfill_action_id": "gl23-slot-010-audio",
                            "backfill_slot_index": 10,
                            "required_modality": "audio",
                            "reason": "pending_template_submission_required",
                        }
                    ],
                    priority_modalities=[{"modality": "audio", "pending_slot_count": 1}],
                    pending_template_loop_count=1,
                ),
            )
            _write_json(
                previous_queue_report,
                {
                    "schema_version": "real_trial_submission_queue.v1",
                    "generated_at_utc": "2026-05-28T00:00:00Z",
                },
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--throughput-report",
                    str(throughput_report),
                    "--previous-queue-report",
                    str(previous_queue_report),
                    "--output",
                    str(queue_report),
                    "--summary-output",
                    "-",
                    "--refresh-interval-hours",
                    "24",
                    "--now-utc",
                    "2026-05-29T06:00:00Z",
                    "--fail-on-cadence-due",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr + completed.stdout)
            payload = json.loads(queue_report.read_text(encoding="utf-8"))
            cadence = payload.get("refresh_cadence", {})
            self.assertEqual(cadence.get("cadence_status"), "CADENCE_DUE")
            self.assertEqual(cadence.get("previous_queue_generated_at_utc"), "2026-05-28T00:00:00Z")
            self.assertEqual(cadence.get("next_refresh_due_utc"), "2026-05-29T00:00:00Z")
            self.assertLessEqual(float(cadence.get("due_in_hours")), 0.0)

    def test_not_required_queue_has_no_items(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            throughput_report = root / "throughput-report.json"
            queue_report = root / "queue-report.json"
            _write_json(
                throughput_report,
                _throughput_report(
                    action_plan_status="ACTION_PLAN_NOT_REQUIRED",
                    throughput_status="THROUGHPUT_THRESHOLD_MET",
                    threshold_met=True,
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--throughput-report",
                    str(throughput_report),
                    "--output",
                    str(queue_report),
                    "--summary-output",
                    "-",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            payload = json.loads(queue_report.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("queue_status"), "QUEUE_NOT_REQUIRED")
            self.assertEqual(payload.get("queue_summary", {}).get("total_item_count"), 0)
            self.assertEqual(payload.get("queue_items"), [])
            self.assertEqual(payload.get("refresh_cadence", {}).get("cadence_status"), "CADENCE_NOT_REQUIRED")


if __name__ == "__main__":
    unittest.main()
