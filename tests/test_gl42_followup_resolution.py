from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "gl42_followup_resolution.py"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _followup_report(*, rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "real_trial_submission_queue_followup.v1",
        "generated_at_utc": "2026-05-29T12:00:00Z",
        "owner": "controlled-beta-ops",
        "commitment_closure_status_gl40": "CLOSURE_STALE_ROLLOVER_REQUIRED",
        "cadence_run_closure_status_gl40": "CLOSURE_RUN_ACTIVE",
        "followup_status": "FOLLOWUP_ACTIONS_OPEN",
        "warning_codes": ["open_followup_actions_present"],
        "followup_counts": {
            "total_action_count": len(rows),
            "open_action_count": sum(
                1 for row in rows if str(row.get("followup_action_status", "")).strip() == "open"
            ),
            "closed_action_count": sum(
                1 for row in rows if str(row.get("followup_action_status", "")).strip() != "open"
            ),
            "stale_rollover_action_count": sum(
                1
                for row in rows
                if str(row.get("followup_action_type", "")).strip() == "resolve_stale_rollover"
            ),
            "acknowledgement_completion_action_count": sum(
                1
                for row in rows
                if str(row.get("followup_action_type", "")).strip() == "complete_acknowledgement_closure"
            ),
            "acknowledgement_closed_action_count": 0,
            "blocked_action_count": 0,
        },
        "owner_followup_counts": {},
        "followup_action_rows": rows,
    }


def _handoff_report(*, queue_items: list[dict[str, Any]], handoff_status: str = "HANDOFF_ACTIONS_PENDING") -> dict[str, Any]:
    return {
        "schema_version": "real_trial_backfill_handoff.v1",
        "generated_at_utc": "2026-05-29T12:05:00Z",
        "handoff_status": handoff_status,
        "owner": "controlled-beta-ops",
        "queue_item_counts": {
            "total_queue_item_count": len(queue_items),
            "open_queue_item_count": sum(
                1 for row in queue_items if str(row.get("queue_status", "")).strip() == "open"
            ),
            "submission_linked_pending_ack_count": sum(
                1
                for row in queue_items
                if str(row.get("queue_status", "")).strip() == "submission_linked_pending_ack"
            ),
            "closure_acknowledged_count": sum(
                1 for row in queue_items if str(row.get("queue_status", "")).strip() == "closure_acknowledged"
            ),
        },
        "queue_items": queue_items,
    }


def _consumption_report(
    *,
    status: str,
    linkage_rows: list[dict[str, Any]],
    invalid_submission_count: int = 0,
    unresolved_submission_count: int = 0,
) -> dict[str, Any]:
    return {
        "schema_version": "real_trial_backfill_submission_consumption.v1",
        "generated_at_utc": "2026-05-29T12:10:00Z",
        "owner": "controlled-beta-ops",
        "consumption_status": status,
        "counts": {
            "template_loop_count": max(len(linkage_rows), 1),
            "submitted_row_count": len(linkage_rows),
            "consumed_loop_count": len(linkage_rows),
            "pending_template_loop_count": max(1 - len(linkage_rows), 0),
            "invalid_submission_count": invalid_submission_count,
            "unresolved_submission_count": unresolved_submission_count,
        },
        "consumption_linkage_records": linkage_rows,
        "pending_template_rows": [],
        "invalid_submissions": [],
        "unresolved_submissions": [],
    }


class RealTrialSubmissionQueueFollowupResolutionScriptTests(unittest.TestCase):
    def test_resolution_in_progress_with_submission_and_ack_progress(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            followup_report_path = root / "followup-report.json"
            handoff_report_path = root / "handoff-report.json"
            consumption_report_path = root / "consumption-report.json"
            resolution_report_path = root / "resolution-report.json"

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
                            "cycle_due_at_utc": "2026-05-30T00:00:00Z",
                        }
                    ]
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
                                "linked_submission": {
                                    "loop_id": "real-text-001",
                                }
                            },
                        }
                    ]
                ),
            )
            _write_json(
                consumption_report_path,
                _consumption_report(
                    status="CONSUMED_MANIFEST_READY",
                    linkage_rows=[
                        {
                            "backfill_action_id": "gl23-slot-001-text",
                            "backfill_slot_index": 1,
                            "loop_id": "real-text-001",
                        }
                    ],
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-report",
                    str(followup_report_path),
                    "--handoff-report",
                    str(handoff_report_path),
                    "--backfill-submission-consumption-report",
                    str(consumption_report_path),
                    "--output",
                    str(resolution_report_path),
                    "--summary-output",
                    "-",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            payload = json.loads(resolution_report_path.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("followup_resolution_status"), "FOLLOWUP_RESOLUTION_IN_PROGRESS")
            counts = payload.get("followup_resolution_counts", {})
            self.assertEqual(counts.get("total_action_count"), 1)
            self.assertEqual(counts.get("open_action_count_gl41"), 1)
            self.assertEqual(counts.get("resolved_action_count"), 0)
            self.assertEqual(counts.get("in_progress_action_count"), 1)
            self.assertEqual(counts.get("unresolved_action_count"), 0)
            rows = payload.get("followup_resolution_rows", [])
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].get("resolution_status"), "in_progress")
            self.assertEqual(
                rows[0].get("resolution_state"),
                "in_progress_submission_linked_pending_ack",
            )
            self.assertEqual(rows[0].get("submission_consumed_loop_id_gl33"), "real-text-001")
            self.assertEqual(rows[0].get("handoff_queue_status_gl24"), "submission_linked_pending_ack")
            self.assertEqual(payload.get("warning_codes"), [])

    def test_resolution_unresolved_blocks_fail_on_unresolved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            followup_report_path = root / "followup-report.json"
            handoff_report_path = root / "handoff-report.json"
            consumption_report_path = root / "consumption-report.json"
            resolution_report_path = root / "resolution-report.json"

            _write_json(
                followup_report_path,
                _followup_report(
                    rows=[
                        {
                            "followup_action_id": "gl41-action-002",
                            "followup_action_status": "open",
                            "followup_action_type": "resolve_stale_rollover",
                            "followup_reason_code": "stale_rollover_requires_followup",
                            "owner": "controlled-beta-ops",
                            "queue_item_id": "gl24-queue-gl23-slot-002-audio",
                            "backfill_action_id": "gl23-slot-002-audio",
                            "required_modality": "audio",
                            "priority_rank": 1,
                            "cycle_due_at_utc": "2026-05-30T00:00:00Z",
                        }
                    ]
                ),
            )
            _write_json(handoff_report_path, _handoff_report(queue_items=[], handoff_status="HANDOFF_ACTIONS_PENDING"))
            _write_json(
                consumption_report_path,
                _consumption_report(
                    status="NO_SUBMISSIONS_PROVIDED",
                    linkage_rows=[],
                    invalid_submission_count=0,
                    unresolved_submission_count=0,
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-report",
                    str(followup_report_path),
                    "--handoff-report",
                    str(handoff_report_path),
                    "--backfill-submission-consumption-report",
                    str(consumption_report_path),
                    "--output",
                    str(resolution_report_path),
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
            payload = json.loads(resolution_report_path.read_text(encoding="utf-8"))
            self.assertEqual(
                payload.get("followup_resolution_status"),
                "FOLLOWUP_RESOLUTION_PENDING_SUBMISSIONS",
            )
            counts = payload.get("followup_resolution_counts", {})
            self.assertEqual(counts.get("total_action_count"), 1)
            self.assertEqual(counts.get("unresolved_action_count"), 1)
            self.assertEqual(counts.get("in_progress_action_count"), 0)
            warning_codes = payload.get("warning_codes", [])
            self.assertIn("open_followup_actions_unresolved", warning_codes)
            self.assertIn("submission_consumption_not_ready", warning_codes)
            rows = payload.get("followup_resolution_rows", [])
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].get("resolution_status"), "unresolved")
            self.assertEqual(rows[0].get("resolution_state"), "unresolved_no_submission_progress")


if __name__ == "__main__":
    unittest.main()
