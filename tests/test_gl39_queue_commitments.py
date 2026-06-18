from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "gl39_queue_commitments.py"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _queue_report(
    *,
    queue_status: str,
    queue_item_status: str = "pending_submission",
    cadence_status: str = "CADENCE_DUE",
    due_in_hours: float = -2.0,
) -> dict[str, Any]:
    return {
        "schema_version": "real_trial_submission_queue.v1",
        "generated_at_utc": "2026-05-29T10:00:00Z",
        "queue_status": queue_status,
        "queue_summary": {
            "total_item_count": 1,
            "pending_item_count": 1,
            "blocked_item_count": 0,
            "action_plan_status": "ACTION_PLAN_WAITING_FOR_SUBMISSIONS",
        },
        "refresh_cadence": {
            "cadence_status": cadence_status,
            "next_refresh_due_utc": "2026-05-29T08:00:00Z",
            "due_in_hours": due_in_hours,
        },
        "queue_items": [
            {
                "queue_item_id": "gl37-submission-queue-gl23-slot-001-text",
                "queue_item_status": queue_item_status,
                "backfill_action_id": "gl23-slot-001-text",
                "backfill_slot_index": 1,
                "required_modality": "text",
                "reason": "pending_template_submission_required",
                "priority_rank": 1,
                "owner": "controlled-beta-ops",
            }
        ],
    }


def _completion_report(
    *,
    completion_status: str,
    completion_progress_status: str,
    transition_state: str,
    net_new_loop_count: int,
) -> dict[str, Any]:
    return {
        "schema_version": "real_trial_submission_queue_completion.v1",
        "generated_at_utc": "2026-05-29T10:10:00Z",
        "completion_status": completion_status,
        "completion_progress_status": completion_progress_status,
        "cycle_verification_status": "CYCLE_NO_NET_NEW_MOVEMENT" if net_new_loop_count == 0 else "CYCLE_NET_NEW_VERIFIED",
        "queue_completion_counts": {
            "queue_total_item_count": 1,
            "submitted_item_count": 1 if "submitted" in transition_state else 0,
            "closed_item_count": 1 if "closed" in transition_state else 0,
            "open_item_count": 0 if "closed" in transition_state or "submitted" in transition_state else 1,
        },
        "cycle_movement_verification": {
            "throughput_net_new_loop_count": net_new_loop_count,
            "throughput_net_new_loop_ids": ["real-text-001"] if net_new_loop_count > 0 else [],
            "submitted_item_delta_from_previous_cycle": 1 if "submitted" in transition_state else 0,
            "closed_item_delta_from_previous_cycle": 1 if "closed" in transition_state else 0,
            "open_item_delta_from_previous_cycle": -1 if "closed" in transition_state or "submitted" in transition_state else 0,
        },
        "queue_transition_records": [
            {
                "queue_item_id": "gl37-submission-queue-gl23-slot-001-text",
                "transition_state": transition_state,
            }
        ],
    }


def _throughput_report(*, threshold_met: bool, action_plan_status: str) -> dict[str, Any]:
    return {
        "schema_version": "real_trial_submission_throughput.v1",
        "generated_at_utc": "2026-05-29T10:15:00Z",
        "throughput_status": "THROUGHPUT_THRESHOLD_MET" if threshold_met else "THROUGHPUT_STALLED",
        "threshold_met": threshold_met,
        "execution_focus": {
            "action_plan_status": action_plan_status,
            "action_plan_blockers": [] if threshold_met else ["throughput_not_progressing"],
        },
    }


def _escalations_report(*, escalation_status: str, include_overdue: bool) -> dict[str, Any]:
    overdue_items: list[dict[str, Any]] = []
    if include_overdue:
        overdue_items.append(
            {
                "queue_item_id": "gl37-submission-queue-gl23-slot-001-text",
                "action_id": "gl23-slot-001-text",
                "slot_index": 1,
                "required_modality": "text",
                "escalation_action": "escalate_immediately",
            }
        )
    return {
        "schema_version": "real_trial_backfill_handoff_escalations.v1",
        "generated_at_utc": "2026-05-29T10:20:00Z",
        "escalation_status": escalation_status,
        "escalation_exports": {
            "overdue_items": overdue_items,
            "sla_breached_items": [],
            "tracking_incomplete_items": [],
        },
    }


class RealTrialSubmissionQueueCommitmentsScriptTests(unittest.TestCase):
    def test_commitments_not_required_when_threshold_met_and_no_queue_items(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            queue_report = root / "queue-report.json"
            completion_report = root / "completion-report.json"
            throughput_report = root / "throughput-report.json"
            escalations_report = root / "escalations-report.json"
            commitments_report = root / "commitments-report.json"

            payload = _queue_report(queue_status="QUEUE_NOT_REQUIRED")
            payload["queue_items"] = []
            payload["queue_summary"]["total_item_count"] = 0
            payload["queue_summary"]["pending_item_count"] = 0
            _write_json(queue_report, payload)
            _write_json(
                completion_report,
                _completion_report(
                    completion_status="COMPLETION_NOT_REQUIRED",
                    completion_progress_status="COMPLETION_NOT_REQUIRED",
                    transition_state="not_required",
                    net_new_loop_count=1,
                ),
            )
            _write_json(throughput_report, _throughput_report(threshold_met=True, action_plan_status="ACTION_PLAN_NOT_REQUIRED"))
            _write_json(
                escalations_report,
                _escalations_report(
                    escalation_status="ESCALATION_NOT_REQUIRED",
                    include_overdue=False,
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-report",
                    str(queue_report),
                    "--submission-queue-completion-report",
                    str(completion_report),
                    "--handoff-escalations-report",
                    str(escalations_report),
                    "--submission-throughput-report",
                    str(throughput_report),
                    "--output",
                    str(commitments_report),
                    "--summary-output",
                    "-",
                    "--fail-on-unresolved",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            report = json.loads(commitments_report.read_text(encoding="utf-8"))
            self.assertEqual(report.get("commitment_status"), "COMMITMENTS_NOT_REQUIRED")
            self.assertEqual(report.get("cadence_run_obligation_status"), "RUN_NOT_REQUIRED")
            self.assertEqual(report.get("commitment_counts", {}).get("total_commitment_count"), 0)
            self.assertEqual(report.get("unresolved_execution_blockers"), [])

    def test_due_cycle_with_escalation_produces_unresolved_commitments(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            queue_report = root / "queue-report.json"
            completion_report = root / "completion-report.json"
            throughput_report = root / "throughput-report.json"
            escalations_report = root / "escalations-report.json"
            commitments_report = root / "commitments-report.json"

            _write_json(queue_report, _queue_report(queue_status="QUEUE_ACTIVE", queue_item_status="pending_submission"))
            _write_json(
                completion_report,
                _completion_report(
                    completion_status="COMPLETION_SUBMISSION_LINKED",
                    completion_progress_status="COMPLETION_STALLED",
                    transition_state="submitted_pending_ack",
                    net_new_loop_count=0,
                ),
            )
            _write_json(
                throughput_report,
                _throughput_report(
                    threshold_met=False,
                    action_plan_status="ACTION_PLAN_WAITING_FOR_SUBMISSIONS",
                ),
            )
            _write_json(
                escalations_report,
                _escalations_report(
                    escalation_status="ESCALATION_OVERDUE_ACTION_REQUIRED",
                    include_overdue=True,
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-report",
                    str(queue_report),
                    "--submission-queue-completion-report",
                    str(completion_report),
                    "--handoff-escalations-report",
                    str(escalations_report),
                    "--submission-throughput-report",
                    str(throughput_report),
                    "--output",
                    str(commitments_report),
                    "--summary-output",
                    "-",
                    "--fail-on-unresolved",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr + completed.stdout)
            report = json.loads(commitments_report.read_text(encoding="utf-8"))
            self.assertEqual(report.get("commitment_status"), "COMMITMENTS_ESCALATION_REQUIRED")
            self.assertEqual(
                report.get("cadence_run_obligation_status"),
                "RUN_DUE_WITH_UNRESOLVED_BLOCKERS",
            )
            counts = report.get("commitment_counts", {})
            self.assertEqual(counts.get("escalation_required_count"), 1)
            self.assertEqual(counts.get("pending_acknowledgement_count"), 0)
            blockers = report.get("unresolved_execution_blockers", [])
            self.assertIn("submission_queue_acknowledgement_escalation_required", blockers)
            self.assertIn("submission_action_plan_waiting_for_submissions", blockers)
            rows = report.get("commitment_rows", [])
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].get("commitment_status"), "escalation_required")


if __name__ == "__main__":
    unittest.main()
