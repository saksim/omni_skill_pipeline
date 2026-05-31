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
    / "gl44_escalation_ack.py"
)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _escalations_report(*, rows: list[dict[str, Any]], status: str = "FOLLOWUP_RESOLUTION_ESCALATION_ACTIVE") -> dict[str, Any]:
    return {
        "schema_version": "real_trial_submission_queue_followup_resolution_escalations.v1",
        "generated_at_utc": "2026-05-30T00:00:00Z",
        "owner": "controlled-beta-ops",
        "followup_resolution_status_gl42": "FOLLOWUP_RESOLUTION_IN_PROGRESS",
        "followup_status_gl41": "FOLLOWUP_ACTIONS_OPEN",
        "followup_resolution_escalation_status": status,
        "warning_codes": [],
        "followup_resolution_escalation_counts": {
            "total_item_count": len(rows),
            "open_item_count": len(rows),
            "blocked_item_count": sum(
                1 for row in rows if str(row.get("escalation_severity", "")).strip() == "blocked"
            ),
            "pending_ack_item_count": sum(
                1 for row in rows if str(row.get("escalation_severity", "")).strip() == "pending_ack"
            ),
            "active_item_count": sum(
                1 for row in rows if str(row.get("escalation_severity", "")).strip() == "active"
            ),
        },
        "owner_followup_resolution_escalation_counts": {},
        "followup_resolution_escalation_rows": rows,
    }


def _handoff_report(*, queue_items: list[dict[str, Any]], status: str = "HANDOFF_OPERATOR_ACK_PENDING") -> dict[str, Any]:
    return {
        "schema_version": "real_trial_backfill_handoff.v1",
        "generated_at_utc": "2026-05-30T00:05:00Z",
        "handoff_status": status,
        "queue_items": queue_items,
    }


class RealTrialSubmissionQueueFollowupResolutionEscalationAcknowledgementsScriptTests(unittest.TestCase):
    def test_reports_not_required_when_no_escalation_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            escalations_report_path = root / "escalations-report.json"
            handoff_report_path = root / "handoff-report.json"
            ack_report_path = root / "ack-report.json"

            _write_json(escalations_report_path, _escalations_report(rows=[], status="FOLLOWUP_RESOLUTION_ESCALATION_NOT_REQUIRED"))
            _write_json(handoff_report_path, _handoff_report(queue_items=[], status="HANDOFF_NOT_REQUIRED"))

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-escalations-report",
                    str(escalations_report_path),
                    "--handoff-report",
                    str(handoff_report_path),
                    "--output",
                    str(ack_report_path),
                    "--summary-output",
                    "-",
                    "--fail-on-open",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)

            payload = json.loads(ack_report_path.read_text(encoding="utf-8"))
            self.assertEqual(
                payload.get("followup_resolution_escalation_acknowledgement_status"),
                "FOLLOWUP_RESOLUTION_ESCALATION_ACK_NOT_REQUIRED",
            )
            counts = payload.get("followup_resolution_escalation_acknowledgement_counts", {})
            self.assertEqual(counts.get("total_item_count"), 0)
            self.assertEqual(counts.get("open_item_count"), 0)
            self.assertEqual(counts.get("resolved_acknowledged_item_count"), 0)
            self.assertEqual(counts.get("pending_ack_item_count"), 0)
            self.assertEqual(counts.get("blocked_item_count"), 0)
            self.assertEqual(payload.get("warning_codes"), [])
            self.assertEqual(payload.get("followup_resolution_escalation_acknowledgement_rows"), [])

    def test_reports_pending_ack_when_submission_linked_pending_ack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            escalations_report_path = root / "escalations-report.json"
            handoff_report_path = root / "handoff-report.json"
            ack_report_path = root / "ack-report.json"
            ack_summary_path = root / "ack-summary.md"

            _write_json(
                escalations_report_path,
                _escalations_report(
                    rows=[
                        {
                            "escalation_item_id": "gl43-escalation-001",
                            "escalation_item_status": "open",
                            "escalation_severity": "pending_ack",
                            "escalation_reason_code": "followup_resolution_in_progress_pending_ack",
                            "escalation_action": "track_submission_linked_acknowledgement_closure",
                            "owner": "controlled-beta-ops",
                            "followup_action_id": "gl41-action-001",
                            "queue_item_id": "gl24-queue-gl23-slot-001-text",
                            "backfill_action_id": "gl23-slot-001-text",
                            "required_modality": "text",
                            "priority_rank": 1,
                        }
                    ],
                    status="FOLLOWUP_RESOLUTION_ESCALATION_PENDING_ACK_ACTION_REQUIRED",
                ),
            )
            _write_json(
                handoff_report_path,
                _handoff_report(
                    queue_items=[
                        {
                            "queue_item_id": "gl24-queue-gl23-slot-001-text",
                            "action_id": "gl23-slot-001-text",
                            "queue_status": "submission_linked_pending_ack",
                            "closure_acknowledgement": {
                                "status": "pending_operator_acknowledgement",
                                "linked_submission": {
                                    "loop_id": "real-text-001",
                                    "review_task_id": "review-real-text-001",
                                    "reviewed_at_utc": "2026-05-30T00:10:00Z",
                                },
                            },
                        }
                    ],
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-escalations-report",
                    str(escalations_report_path),
                    "--handoff-report",
                    str(handoff_report_path),
                    "--output",
                    str(ack_report_path),
                    "--summary-output",
                    str(ack_summary_path),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)

            payload = json.loads(ack_report_path.read_text(encoding="utf-8"))
            self.assertEqual(
                payload.get("followup_resolution_escalation_acknowledgement_status"),
                "FOLLOWUP_RESOLUTION_ESCALATION_ACK_PENDING_ACTION_REQUIRED",
            )
            counts = payload.get("followup_resolution_escalation_acknowledgement_counts", {})
            self.assertEqual(counts.get("total_item_count"), 1)
            self.assertEqual(counts.get("open_item_count"), 1)
            self.assertEqual(counts.get("resolved_acknowledged_item_count"), 0)
            self.assertEqual(counts.get("pending_ack_item_count"), 1)
            self.assertEqual(counts.get("blocked_item_count"), 0)
            rows = payload.get("followup_resolution_escalation_acknowledgement_rows", [])
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].get("acknowledgement_status"), "pending_ack")
            self.assertEqual(rows[0].get("acknowledgement_state"), "pending_operator_acknowledgement")
            self.assertEqual(rows[0].get("linked_submission_loop_id_gl24"), "real-text-001")
            summary = ack_summary_path.read_text(encoding="utf-8")
            self.assertIn(
                "GL-44 acknowledgement status: `FOLLOWUP_RESOLUTION_ESCALATION_ACK_PENDING_ACTION_REQUIRED`",
                summary,
            )

    def test_reports_resolved_acknowledged_when_handoff_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            escalations_report_path = root / "escalations-report.json"
            handoff_report_path = root / "handoff-report.json"
            ack_report_path = root / "ack-report.json"

            _write_json(
                escalations_report_path,
                _escalations_report(
                    rows=[
                        {
                            "escalation_item_id": "gl43-escalation-002",
                            "escalation_item_status": "open",
                            "escalation_severity": "blocked",
                            "escalation_reason_code": "followup_resolution_unresolved",
                            "escalation_action": "escalate_unresolved_followup_action",
                            "owner": "controlled-beta-ops",
                            "followup_action_id": "gl41-action-002",
                            "queue_item_id": "gl24-queue-gl23-slot-002-audio",
                            "backfill_action_id": "gl23-slot-002-audio",
                            "required_modality": "audio",
                            "priority_rank": 1,
                        }
                    ],
                    status="FOLLOWUP_RESOLUTION_ESCALATION_BLOCKED_ACTION_REQUIRED",
                ),
            )
            _write_json(
                handoff_report_path,
                _handoff_report(
                    queue_items=[
                        {
                            "queue_item_id": "gl24-queue-gl23-slot-002-audio",
                            "action_id": "gl23-slot-002-audio",
                            "queue_status": "closure_acknowledged",
                            "closure_acknowledgement": {
                                "status": "acknowledged",
                                "linked_submission": {
                                    "loop_id": "real-audio-002",
                                    "review_task_id": "review-real-audio-002",
                                    "reviewed_at_utc": "2026-05-30T00:20:00Z",
                                },
                                "operator_acknowledgement": {
                                    "acknowledged_by": "ops-reviewer-1",
                                    "acknowledged_at_utc": "2026-05-30T00:21:00Z",
                                    "submitted_loop_id": "real-audio-002",
                                },
                            },
                        }
                    ],
                    status="HANDOFF_CLOSURE_ACKNOWLEDGED",
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-escalations-report",
                    str(escalations_report_path),
                    "--handoff-report",
                    str(handoff_report_path),
                    "--output",
                    str(ack_report_path),
                    "--summary-output",
                    "-",
                    "--fail-on-open",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)

            payload = json.loads(ack_report_path.read_text(encoding="utf-8"))
            self.assertEqual(
                payload.get("followup_resolution_escalation_acknowledgement_status"),
                "FOLLOWUP_RESOLUTION_ESCALATION_ACK_COMPLETE",
            )
            counts = payload.get("followup_resolution_escalation_acknowledgement_counts", {})
            self.assertEqual(counts.get("total_item_count"), 1)
            self.assertEqual(counts.get("open_item_count"), 0)
            self.assertEqual(counts.get("resolved_acknowledged_item_count"), 1)
            self.assertEqual(counts.get("pending_ack_item_count"), 0)
            self.assertEqual(counts.get("blocked_item_count"), 0)
            rows = payload.get("followup_resolution_escalation_acknowledgement_rows", [])
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].get("acknowledgement_item_status"), "closed")
            self.assertEqual(rows[0].get("acknowledgement_status"), "resolved_acknowledged")
            self.assertEqual(rows[0].get("linked_submission_loop_id_gl24"), "real-audio-002")
            self.assertEqual(rows[0].get("operator_acknowledged_by_gl24"), "ops-reviewer-1")


if __name__ == "__main__":
    unittest.main()

