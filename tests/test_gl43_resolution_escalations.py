from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "gl43_resolution_escalations.py"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _followup_report(*, rows: list[dict[str, Any]], followup_status: str = "FOLLOWUP_ACTIONS_OPEN") -> dict[str, Any]:
    return {
        "schema_version": "real_trial_submission_queue_followup.v1",
        "generated_at_utc": "2026-05-30T00:00:00Z",
        "owner": "controlled-beta-ops",
        "commitment_closure_status_gl40": "CLOSURE_ESCALATION_REQUIRED",
        "cadence_run_closure_status_gl40": "CLOSURE_RUN_ACTIVE",
        "followup_status": followup_status,
        "warning_codes": [],
        "followup_counts": {
            "total_action_count": len(rows),
            "open_action_count": sum(
                1 for row in rows if str(row.get("followup_action_status", "")).strip() == "open"
            ),
            "closed_action_count": sum(
                1 for row in rows if str(row.get("followup_action_status", "")).strip() == "closed"
            ),
            "stale_rollover_action_count": 0,
            "acknowledgement_completion_action_count": 0,
            "acknowledgement_closed_action_count": 0,
            "blocked_action_count": 0,
        },
        "owner_followup_counts": {},
        "followup_action_rows": rows,
    }


def _resolution_report(*, status: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "real_trial_submission_queue_followup_resolution.v1",
        "generated_at_utc": "2026-05-30T00:05:00Z",
        "owner": "controlled-beta-ops",
        "followup_status_gl41": "FOLLOWUP_ACTIONS_OPEN",
        "commitment_closure_status_gl40": "CLOSURE_ESCALATION_REQUIRED",
        "cadence_run_closure_status_gl40": "CLOSURE_RUN_ACTIVE",
        "handoff_status_gl24": "HANDOFF_ACTIONS_PENDING",
        "submission_consumption_status_gl33": "NO_SUBMISSIONS_PROVIDED",
        "followup_resolution_status": status,
        "warning_codes": [],
        "followup_resolution_counts": {
            "total_action_count": len(rows),
            "open_action_count_gl41": sum(
                1 for row in rows if str(row.get("followup_action_status_gl41", "")).strip() == "open"
            ),
            "closed_action_count_gl41": sum(
                1 for row in rows if str(row.get("followup_action_status_gl41", "")).strip() != "open"
            ),
            "resolved_action_count": sum(
                1 for row in rows if str(row.get("resolution_status", "")).strip() == "resolved"
            ),
            "in_progress_action_count": sum(
                1 for row in rows if str(row.get("resolution_status", "")).strip() == "in_progress"
            ),
            "unresolved_action_count": sum(
                1 for row in rows if str(row.get("resolution_status", "")).strip() == "unresolved"
            ),
            "submission_linked_action_count": sum(
                1
                for row in rows
                if str(row.get("handoff_queue_status_gl24", "")).strip()
                in {"submission_linked_pending_ack", "closure_acknowledged"}
            ),
            "closure_acknowledged_action_count": sum(
                1 for row in rows if str(row.get("handoff_queue_status_gl24", "")).strip() == "closure_acknowledged"
            ),
            "consumed_submission_action_count": sum(
                1 for row in rows if str(row.get("submission_consumed_loop_id_gl33", "")).strip()
            ),
            "submission_consumption_invalid_submission_count": 0,
            "submission_consumption_unresolved_submission_count": 0,
        },
        "owner_followup_resolution_counts": {},
        "followup_resolution_rows": rows,
    }


class RealTrialSubmissionQueueFollowupResolutionEscalationsScriptTests(unittest.TestCase):
    def test_generates_blocked_escalation_for_unresolved_row(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            followup_report_path = root / "followup-report.json"
            resolution_report_path = root / "resolution-report.json"
            escalation_report_path = root / "escalation-report.json"

            _write_json(
                followup_report_path,
                _followup_report(
                    rows=[
                        {
                            "followup_action_id": "gl41-action-001",
                            "followup_action_status": "open",
                            "followup_action_type": "resolve_stale_rollover",
                            "followup_reason_code": "stale_rollover_requires_followup",
                            "owner": "controlled-beta-ops",
                            "queue_item_id": "gl24-queue-gl23-slot-001-text",
                            "backfill_action_id": "gl23-slot-001-text",
                            "required_modality": "text",
                            "priority_rank": 1,
                            "source_stale_rollover": True,
                            "source_closure_state_gl40": "stale_rollover",
                            "source_commitment_status_gl39": "escalation_required",
                            "source_transition_state_gl38": "blocked",
                            "source_stale_reason_codes": ["missing_submission_linkage"],
                            "cycle_due_at_utc": "2026-05-30T00:00:00Z",
                        }
                    ]
                ),
            )
            _write_json(
                resolution_report_path,
                _resolution_report(
                    status="FOLLOWUP_RESOLUTION_PENDING_SUBMISSIONS",
                    rows=[
                        {
                            "followup_action_id": "gl41-action-001",
                            "owner": "controlled-beta-ops",
                            "followup_action_type": "resolve_stale_rollover",
                            "followup_action_status_gl41": "open",
                            "followup_reason_code": "stale_rollover_requires_followup",
                            "queue_item_id": "gl24-queue-gl23-slot-001-text",
                            "backfill_action_id": "gl23-slot-001-text",
                            "required_modality": "text",
                            "priority_rank": 1,
                            "resolution_status": "unresolved",
                            "resolution_state": "unresolved_no_submission_progress",
                            "handoff_queue_status_gl24": "",
                            "submission_consumed_loop_id_gl33": "",
                            "handoff_linked_loop_id_gl24": "",
                            "cycle_due_at_utc": "2026-05-30T00:00:00Z",
                        }
                    ],
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-report",
                    str(resolution_report_path),
                    "--submission-queue-followup-report",
                    str(followup_report_path),
                    "--output",
                    str(escalation_report_path),
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

            payload = json.loads(escalation_report_path.read_text(encoding="utf-8"))
            self.assertEqual(
                payload.get("followup_resolution_escalation_status"),
                "FOLLOWUP_RESOLUTION_ESCALATION_BLOCKED_ACTION_REQUIRED",
            )
            counts = payload.get("followup_resolution_escalation_counts", {})
            self.assertEqual(counts.get("total_item_count"), 1)
            self.assertEqual(counts.get("open_item_count"), 1)
            self.assertEqual(counts.get("blocked_item_count"), 1)
            self.assertEqual(counts.get("pending_ack_item_count"), 0)
            self.assertEqual(counts.get("active_item_count"), 0)
            warning_codes = payload.get("warning_codes", [])
            self.assertIn("followup_resolution_unresolved_escalations_required", warning_codes)
            self.assertIn("open_followup_resolution_escalation_items_present", warning_codes)
            rows = payload.get("followup_resolution_escalation_rows", [])
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].get("escalation_severity"), "blocked")
            self.assertEqual(rows[0].get("escalation_reason_code"), "followup_resolution_unresolved")
            self.assertEqual(rows[0].get("resolution_status_gl42"), "unresolved")
            self.assertEqual(rows[0].get("source_stale_rollover_gl41"), True)
            self.assertEqual(rows[0].get("source_stale_reason_codes_gl40"), ["missing_submission_linkage"])

    def test_generates_pending_ack_escalation_for_in_progress_row(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            followup_report_path = root / "followup-report.json"
            resolution_report_path = root / "resolution-report.json"
            escalation_report_path = root / "escalation-report.json"
            escalation_summary_path = root / "escalation-summary.md"

            _write_json(
                followup_report_path,
                _followup_report(
                    rows=[
                        {
                            "followup_action_id": "gl41-action-002",
                            "followup_action_status": "open",
                            "followup_action_type": "resolve_escalation_required_closure",
                            "followup_reason_code": "escalation_required_followup_actions_required",
                            "owner": "controlled-beta-ops",
                            "queue_item_id": "gl24-queue-gl23-slot-002-audio",
                            "backfill_action_id": "gl23-slot-002-audio",
                            "required_modality": "audio",
                            "priority_rank": 2,
                            "source_stale_rollover": False,
                            "source_closure_state_gl40": "escalation_required",
                            "source_commitment_status_gl39": "escalation_required",
                            "source_transition_state_gl38": "submission_linked_pending_ack",
                            "source_stale_reason_codes": [],
                            "cycle_due_at_utc": "2026-05-30T02:00:00Z",
                        }
                    ]
                ),
            )
            _write_json(
                resolution_report_path,
                _resolution_report(
                    status="FOLLOWUP_RESOLUTION_IN_PROGRESS",
                    rows=[
                        {
                            "followup_action_id": "gl41-action-002",
                            "owner": "controlled-beta-ops",
                            "followup_action_type": "resolve_escalation_required_closure",
                            "followup_action_status_gl41": "open",
                            "followup_reason_code": "escalation_required_followup_actions_required",
                            "queue_item_id": "gl24-queue-gl23-slot-002-audio",
                            "backfill_action_id": "gl23-slot-002-audio",
                            "required_modality": "audio",
                            "priority_rank": 2,
                            "resolution_status": "in_progress",
                            "resolution_state": "in_progress_submission_linked_pending_ack",
                            "handoff_queue_status_gl24": "submission_linked_pending_ack",
                            "submission_consumed_loop_id_gl33": "real-audio-002",
                            "handoff_linked_loop_id_gl24": "real-audio-002",
                            "cycle_due_at_utc": "2026-05-30T02:00:00Z",
                        }
                    ],
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-report",
                    str(resolution_report_path),
                    "--submission-queue-followup-report",
                    str(followup_report_path),
                    "--output",
                    str(escalation_report_path),
                    "--summary-output",
                    str(escalation_summary_path),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)

            payload = json.loads(escalation_report_path.read_text(encoding="utf-8"))
            self.assertEqual(
                payload.get("followup_resolution_escalation_status"),
                "FOLLOWUP_RESOLUTION_ESCALATION_PENDING_ACK_ACTION_REQUIRED",
            )
            counts = payload.get("followup_resolution_escalation_counts", {})
            self.assertEqual(counts.get("total_item_count"), 1)
            self.assertEqual(counts.get("blocked_item_count"), 0)
            self.assertEqual(counts.get("pending_ack_item_count"), 1)
            self.assertEqual(counts.get("active_item_count"), 0)
            rows = payload.get("followup_resolution_escalation_rows", [])
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].get("escalation_severity"), "pending_ack")
            self.assertEqual(
                rows[0].get("escalation_reason_code"),
                "followup_resolution_in_progress_pending_ack",
            )
            self.assertEqual(
                rows[0].get("escalation_action"),
                "track_submission_linked_acknowledgement_closure",
            )
            self.assertEqual(rows[0].get("submission_consumed_loop_id_gl33"), "real-audio-002")
            summary = escalation_summary_path.read_text(encoding="utf-8")
            self.assertIn("GL-43 escalation status: `FOLLOWUP_RESOLUTION_ESCALATION_PENDING_ACK_ACTION_REQUIRED`", summary)

    def test_reports_not_required_when_resolution_has_no_open_work(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            followup_report_path = root / "followup-report.json"
            resolution_report_path = root / "resolution-report.json"
            escalation_report_path = root / "escalation-report.json"

            _write_json(followup_report_path, _followup_report(rows=[], followup_status="FOLLOWUP_NOT_REQUIRED"))
            _write_json(
                resolution_report_path,
                _resolution_report(
                    status="FOLLOWUP_RESOLUTION_NOT_REQUIRED",
                    rows=[],
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-report",
                    str(resolution_report_path),
                    "--submission-queue-followup-report",
                    str(followup_report_path),
                    "--output",
                    str(escalation_report_path),
                    "--summary-output",
                    "-",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)

            payload = json.loads(escalation_report_path.read_text(encoding="utf-8"))
            self.assertEqual(
                payload.get("followup_resolution_escalation_status"),
                "FOLLOWUP_RESOLUTION_ESCALATION_NOT_REQUIRED",
            )
            counts = payload.get("followup_resolution_escalation_counts", {})
            self.assertEqual(counts.get("total_item_count"), 0)
            self.assertEqual(counts.get("open_item_count"), 0)
            self.assertEqual(payload.get("warning_codes"), [])
            self.assertEqual(payload.get("followup_resolution_escalation_rows"), [])


if __name__ == "__main__":
    unittest.main()

