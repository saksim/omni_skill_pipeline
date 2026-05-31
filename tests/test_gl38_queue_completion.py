from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "gl38_queue_completion.py"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _queue_report(
    *,
    queue_status: str,
    queue_items: list[dict[str, Any]] | None = None,
    cadence_status: str = "CADENCE_ON_SCHEDULE",
    due_in_hours: float = 6.0,
) -> dict[str, Any]:
    items = queue_items if isinstance(queue_items, list) else []
    return {
        "schema_version": "real_trial_submission_queue.v1",
        "generated_at_utc": "2026-05-29T02:00:00Z",
        "queue_status": queue_status,
        "warning_codes": [],
        "queue_summary": {
            "total_item_count": len(items),
            "pending_item_count": len(items) if queue_status != "QUEUE_BLOCKED_BY_SUBMISSION_ERRORS" else 0,
            "blocked_item_count": len(items) if queue_status == "QUEUE_BLOCKED_BY_SUBMISSION_ERRORS" else 0,
        },
        "refresh_cadence": {
            "refresh_interval_hours": 24.0,
            "cadence_status": cadence_status,
            "previous_queue_generated_at_utc": "2026-05-29T00:00:00Z",
            "next_refresh_due_utc": "2026-05-30T00:00:00Z",
            "due_in_hours": due_in_hours,
            "evaluated_at_utc": "2026-05-29T18:00:00Z",
        },
        "queue_items": items,
    }


def _throughput_report(
    *,
    throughput_status: str,
    threshold_met: bool,
    net_new_loop_ids: list[str] | None = None,
) -> dict[str, Any]:
    loop_ids = net_new_loop_ids if isinstance(net_new_loop_ids, list) else []
    return {
        "schema_version": "real_trial_submission_throughput.v1",
        "generated_at_utc": "2026-05-29T02:05:00Z",
        "throughput_status": throughput_status,
        "threshold_met": threshold_met,
        "warning_codes": [],
        "snapshot": {
            "previous_snapshot_available": True,
            "previous": {},
            "current": {},
            "delta": {
                "net_new_launch_gate_eligible_real_loop_count": len(loop_ids),
            },
            "net_new_launch_gate_eligible_real_loop_ids": loop_ids,
        },
    }


def _handoff_report(
    *,
    queue_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    rows = queue_rows if isinstance(queue_rows, list) else []
    return {
        "schema_version": "real_trial_backfill_handoff.v1",
        "generated_at_utc": "2026-05-29T02:08:00Z",
        "handoff_status": "HANDOFF_OPERATOR_ACK_PENDING",
        "queue_item_counts": {
            "total_queue_item_count": len(rows),
            "open_queue_item_count": 0,
            "submission_linked_pending_ack_count": len(rows),
            "closure_acknowledged_count": 0,
        },
        "queue_items": rows,
    }


class RealTrialSubmissionQueueCompletionScriptTests(unittest.TestCase):
    def test_completion_progressing_with_submitted_and_closed_transitions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            queue_report = root / "queue-report.json"
            throughput_report = root / "throughput-report.json"
            handoff_report = root / "handoff-report.json"
            completion_report = root / "completion-report.json"
            completion_summary = root / "completion-summary.md"

            _write_json(
                queue_report,
                _queue_report(
                    queue_status="QUEUE_ACTIVE",
                    queue_items=[
                        {
                            "queue_item_id": "gl37-submission-queue-gl23-slot-001-text",
                            "queue_item_status": "pending_submission",
                            "backfill_action_id": "gl23-slot-001-text",
                            "backfill_slot_index": 1,
                            "required_modality": "text",
                            "reason": "pending_template_submission_required",
                            "owner": "controlled-beta-ops",
                        }
                    ],
                ),
            )
            _write_json(
                throughput_report,
                _throughput_report(
                    throughput_status="THROUGHPUT_PROGRESSING",
                    threshold_met=False,
                    net_new_loop_ids=["real-text-001"],
                ),
            )
            _write_json(
                handoff_report,
                _handoff_report(
                    queue_rows=[
                        {
                            "queue_item_id": "gl24-queue-gl23-slot-001-text",
                            "action_id": "gl23-slot-001-text",
                            "slot_index": 1,
                            "required_modality": "text",
                            "queue_status": "closure_acknowledged",
                            "closure_acknowledgement": {
                                "status": "acknowledged",
                                "linked_submission": {
                                    "loop_id": "real-text-001",
                                    "review_task_id": "review-real-text-001",
                                    "reviewed_at_utc": "2026-05-29T01:30:00Z",
                                },
                            },
                        }
                    ]
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-report",
                    str(queue_report),
                    "--submission-throughput-report",
                    str(throughput_report),
                    "--handoff-report",
                    str(handoff_report),
                    "--output",
                    str(completion_report),
                    "--summary-output",
                    str(completion_summary),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            payload = json.loads(completion_report.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("completion_status"), "COMPLETION_CLOSED")
            self.assertEqual(payload.get("completion_progress_status"), "COMPLETION_PROGRESSING")
            self.assertEqual(payload.get("cycle_verification_status"), "CYCLE_NET_NEW_VERIFIED")
            counts = payload.get("queue_completion_counts", {})
            self.assertEqual(counts.get("queue_total_item_count"), 1)
            self.assertEqual(counts.get("submitted_item_count"), 1)
            self.assertEqual(counts.get("closed_item_count"), 1)
            self.assertEqual(counts.get("open_item_count"), 0)
            cycle = payload.get("cycle_movement_verification", {})
            self.assertTrue(cycle.get("net_new_movement_verified"))
            self.assertEqual(cycle.get("throughput_net_new_loop_count"), 1)
            transition_rows = payload.get("queue_transition_records", [])
            self.assertEqual(len(transition_rows), 1)
            self.assertEqual(transition_rows[0].get("transition_state"), "closed_with_acknowledgement")
            self.assertEqual(transition_rows[0].get("linked_submission_loop_id"), "real-text-001")

    def test_completion_stalled_exit_code_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            queue_report = root / "queue-report.json"
            throughput_report = root / "throughput-report.json"
            handoff_report = root / "handoff-report.json"
            completion_report = root / "completion-report.json"

            _write_json(
                queue_report,
                _queue_report(
                    queue_status="QUEUE_ACTIVE",
                    cadence_status="CADENCE_DUE",
                    due_in_hours=-1.5,
                    queue_items=[
                        {
                            "queue_item_id": "gl37-submission-queue-gl23-slot-002-audio",
                            "queue_item_status": "pending_submission",
                            "backfill_action_id": "gl23-slot-002-audio",
                            "backfill_slot_index": 2,
                            "required_modality": "audio",
                            "reason": "pending_template_submission_required",
                            "owner": "controlled-beta-ops",
                        }
                    ],
                ),
            )
            _write_json(
                throughput_report,
                _throughput_report(
                    throughput_status="THROUGHPUT_STALLED",
                    threshold_met=False,
                    net_new_loop_ids=[],
                ),
            )
            _write_json(
                handoff_report,
                _handoff_report(
                    queue_rows=[
                        {
                            "queue_item_id": "gl24-queue-gl23-slot-002-audio",
                            "action_id": "gl23-slot-002-audio",
                            "slot_index": 2,
                            "required_modality": "audio",
                            "queue_status": "open",
                            "closure_acknowledgement": {"status": "not_acknowledged"},
                        }
                    ]
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-report",
                    str(queue_report),
                    "--submission-throughput-report",
                    str(throughput_report),
                    "--handoff-report",
                    str(handoff_report),
                    "--output",
                    str(completion_report),
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
            payload = json.loads(completion_report.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("completion_status"), "COMPLETION_IN_PROGRESS")
            self.assertEqual(payload.get("completion_progress_status"), "COMPLETION_STALLED")
            self.assertEqual(payload.get("cycle_verification_status"), "CYCLE_NO_NET_NEW_MOVEMENT")
            warning_codes = payload.get("warning_codes", [])
            self.assertIn("queue_completion_progress_stalled", warning_codes)
            self.assertIn("queue_cycle_due_without_net_new_eligible_real_loops", warning_codes)

    def test_completion_not_required_when_queue_not_required_and_threshold_met(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            queue_report = root / "queue-report.json"
            throughput_report = root / "throughput-report.json"
            handoff_report = root / "handoff-report.json"
            completion_report = root / "completion-report.json"

            _write_json(
                queue_report,
                _queue_report(
                    queue_status="QUEUE_NOT_REQUIRED",
                    queue_items=[],
                    cadence_status="CADENCE_NOT_REQUIRED",
                    due_in_hours=0.0,
                ),
            )
            _write_json(
                throughput_report,
                _throughput_report(
                    throughput_status="THROUGHPUT_THRESHOLD_MET",
                    threshold_met=True,
                    net_new_loop_ids=[],
                ),
            )
            _write_json(handoff_report, _handoff_report(queue_rows=[]))

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-report",
                    str(queue_report),
                    "--submission-throughput-report",
                    str(throughput_report),
                    "--handoff-report",
                    str(handoff_report),
                    "--output",
                    str(completion_report),
                    "--summary-output",
                    "-",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            payload = json.loads(completion_report.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("completion_status"), "COMPLETION_NOT_REQUIRED")
            self.assertEqual(payload.get("completion_progress_status"), "COMPLETION_NOT_REQUIRED")
            self.assertEqual(payload.get("cycle_verification_status"), "CYCLE_NOT_REQUIRED")
            counts = payload.get("queue_completion_counts", {})
            self.assertEqual(counts.get("queue_total_item_count"), 0)
            self.assertEqual(counts.get("submitted_item_count"), 0)
            self.assertEqual(counts.get("closed_item_count"), 0)


if __name__ == "__main__":
    unittest.main()

