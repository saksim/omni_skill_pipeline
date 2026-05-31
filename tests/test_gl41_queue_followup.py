from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "gl41_queue_followup.py"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _closure_report(
    *,
    closure_status: str,
    cadence_run_status: str,
    closure_rows: list[dict[str, Any]] | None = None,
    acknowledgement_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    rows = closure_rows if isinstance(closure_rows, list) else []
    acknowledgements = acknowledgement_rows if isinstance(acknowledgement_rows, list) else []
    stale_count = sum(1 for row in rows if bool(row.get("stale_rollover", False)))
    return {
        "schema_version": "real_trial_submission_queue_commitment_closure.v1",
        "generated_at_utc": "2026-05-29T10:00:00Z",
        "owner": "controlled-beta-ops",
        "commitment_closure_status": closure_status,
        "cadence_run_closure_status": cadence_run_status,
        "warning_codes": [],
        "closure_counts": {
            "total_commitment_count": len(rows),
            "closed_with_acknowledgement_count": len(acknowledgements),
            "active_commitment_count": len(rows),
            "stale_rollover_count": stale_count,
            "net_new_closed_with_acknowledgement_count": len(acknowledgements),
        },
        "commitment_closure_rows": rows,
        "closure_acknowledgement_rows": acknowledgements,
        "stale_rollover_rows": [row for row in rows if bool(row.get("stale_rollover", False))],
    }


class RealTrialSubmissionQueueFollowupScriptTests(unittest.TestCase):
    def test_followup_not_required_when_closure_not_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            closure_report_path = root / "commitment-closure-report.json"
            followup_report_path = root / "followup-report.json"

            _write_json(
                closure_report_path,
                _closure_report(
                    closure_status="CLOSURE_NOT_REQUIRED",
                    cadence_run_status="CLOSURE_RUN_NOT_REQUIRED",
                    closure_rows=[],
                    acknowledgement_rows=[],
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-commitment-closure-report",
                    str(closure_report_path),
                    "--output",
                    str(followup_report_path),
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
            payload = json.loads(followup_report_path.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("followup_status"), "FOLLOWUP_NOT_REQUIRED")
            counts = payload.get("followup_counts", {})
            self.assertEqual(counts.get("total_action_count"), 0)
            self.assertEqual(counts.get("open_action_count"), 0)
            self.assertEqual(counts.get("closed_action_count"), 0)
            self.assertEqual(payload.get("warning_codes"), [])

    def test_followup_stale_and_acknowledgement_actions_are_emitted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            closure_report_path = root / "commitment-closure-report.json"
            followup_report_path = root / "followup-report.json"

            closure_rows = [
                {
                    "commitment_id": "gl39-commitment-stale",
                    "queue_item_id": "gl37-submission-queue-gl23-slot-001-text",
                    "backfill_action_id": "gl23-slot-001-text",
                    "required_modality": "text",
                    "owner": "controlled-beta-ops",
                    "priority_rank": 1,
                    "commitment_status_gl39": "pending_submission",
                    "transition_state_gl38": "pending_submission",
                    "closure_state": "open_commitment",
                    "stale_rollover": True,
                    "stale_reason_codes": ["unchanged_open_commitment_across_cycles"],
                    "cycle_due_at_utc": "2026-05-29T09:00:00Z",
                    "reason": "pending_template_submission_required",
                },
                {
                    "commitment_id": "gl39-commitment-pending-ack",
                    "queue_item_id": "gl37-submission-queue-gl23-slot-002-image",
                    "backfill_action_id": "gl23-slot-002-image",
                    "required_modality": "image",
                    "owner": "controlled-beta-ops",
                    "priority_rank": 2,
                    "commitment_status_gl39": "pending_acknowledgement",
                    "transition_state_gl38": "submitted_pending_ack",
                    "closure_state": "pending_acknowledgement",
                    "stale_rollover": False,
                    "stale_reason_codes": [],
                    "cycle_due_at_utc": "2026-05-29T09:00:00Z",
                    "reason": "submission_linked_pending_ack",
                },
            ]
            acknowledgement_rows = [
                {
                    "commitment_id": "gl39-commitment-closed",
                    "queue_item_id": "gl37-submission-queue-gl23-slot-003-audio",
                    "backfill_action_id": "gl23-slot-003-audio",
                    "required_modality": "audio",
                    "owner": "controlled-beta-ops",
                    "closure_state": "closed_with_acknowledgement",
                    "linked_submission_loop_id": "real-audio-101",
                    "linked_submission_review_task_id": "review-real-audio-101",
                    "linked_submission_reviewed_at_utc": "2026-05-29T10:10:00Z",
                }
            ]
            _write_json(
                closure_report_path,
                _closure_report(
                    closure_status="CLOSURE_STALE_ROLLOVER_REQUIRED",
                    cadence_run_status="CLOSURE_RUN_DUE_WITH_STALE_ROLLOVER",
                    closure_rows=closure_rows,
                    acknowledgement_rows=acknowledgement_rows,
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-commitment-closure-report",
                    str(closure_report_path),
                    "--output",
                    str(followup_report_path),
                    "--summary-output",
                    "-",
                    "--fail-on-open",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr + completed.stdout)
            payload = json.loads(followup_report_path.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("followup_status"), "FOLLOWUP_STALE_ROLLOVER_ACTION_REQUIRED")
            counts = payload.get("followup_counts", {})
            self.assertEqual(counts.get("total_action_count"), 3)
            self.assertEqual(counts.get("open_action_count"), 2)
            self.assertEqual(counts.get("closed_action_count"), 1)
            self.assertEqual(counts.get("stale_rollover_action_count"), 1)
            self.assertEqual(counts.get("acknowledgement_completion_action_count"), 1)
            self.assertEqual(counts.get("acknowledgement_closed_action_count"), 1)
            warning_codes = payload.get("warning_codes", [])
            self.assertIn("stale_rollover_followup_actions_required", warning_codes)
            self.assertIn("pending_acknowledgement_followup_actions_required", warning_codes)
            self.assertIn("open_followup_actions_present", warning_codes)
            actions = payload.get("followup_action_rows", [])
            self.assertEqual(len(actions), 3)
            open_action_types = {
                str(row.get("followup_action_type", ""))
                for row in actions
                if str(row.get("followup_action_status", "")) == "open"
            }
            self.assertEqual(
                open_action_types,
                {"resolve_stale_rollover", "complete_acknowledgement_closure"},
            )
            closed_action_types = {
                str(row.get("followup_action_type", ""))
                for row in actions
                if str(row.get("followup_action_status", "")) == "closed"
            }
            self.assertEqual(closed_action_types, {"acknowledgement_closure_recorded"})


if __name__ == "__main__":
    unittest.main()

