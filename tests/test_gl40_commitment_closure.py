from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "gl40_commitment_closure.py"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _commitments_report(
    *,
    commitment_status: str,
    cadence_status: str,
    rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    items = rows if isinstance(rows, list) else []
    return {
        "schema_version": "real_trial_submission_queue_commitments.v1",
        "generated_at_utc": "2026-05-29T10:00:00Z",
        "owner": "controlled-beta-ops",
        "commitment_status": commitment_status,
        "cadence_run_obligation_status": "RUN_ON_SCHEDULE_WITH_OPEN_COMMITMENTS",
        "unresolved_execution_blockers": [],
        "cycle_snapshot": {
            "queue_status": "QUEUE_ACTIVE" if items else "QUEUE_NOT_REQUIRED",
            "queue_cadence_status": cadence_status,
            "queue_next_refresh_due_utc": "2026-05-29T09:00:00Z",
        },
        "commitment_counts": {
            "total_commitment_count": len(items),
            "pending_submission_count": len(items),
            "pending_acknowledgement_count": 0,
            "blocked_submission_errors_count": 0,
            "escalation_required_count": 0,
            "rebuild_required_count": 0,
        },
        "commitment_rows": items,
    }


def _completion_report(*, transition_rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    rows = transition_rows if isinstance(transition_rows, list) else []
    return {
        "schema_version": "real_trial_submission_queue_completion.v1",
        "generated_at_utc": "2026-05-29T10:10:00Z",
        "queue_status": "QUEUE_ACTIVE" if rows else "QUEUE_NOT_REQUIRED",
        "completion_status": "COMPLETION_IN_PROGRESS" if rows else "COMPLETION_NOT_REQUIRED",
        "completion_progress_status": "COMPLETION_STALLED" if rows else "COMPLETION_NOT_REQUIRED",
        "cycle_verification_status": "CYCLE_NO_NET_NEW_MOVEMENT" if rows else "CYCLE_NOT_REQUIRED",
        "queue_transition_records": rows,
    }


class RealTrialSubmissionQueueCommitmentClosureScriptTests(unittest.TestCase):
    def test_closure_not_required_when_no_commitments(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            commitments = root / "commitments.json"
            completion = root / "completion.json"
            closure_report = root / "closure-report.json"

            _write_json(
                commitments,
                _commitments_report(
                    commitment_status="COMMITMENTS_NOT_REQUIRED",
                    cadence_status="CADENCE_NOT_REQUIRED",
                    rows=[],
                ),
            )
            _write_json(completion, _completion_report(transition_rows=[]))

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-commitments-report",
                    str(commitments),
                    "--submission-queue-completion-report",
                    str(completion),
                    "--output",
                    str(closure_report),
                    "--summary-output",
                    "-",
                    "--fail-on-stale-rollover",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            payload = json.loads(closure_report.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("commitment_closure_status"), "CLOSURE_NOT_REQUIRED")
            self.assertEqual(payload.get("cadence_run_closure_status"), "CLOSURE_RUN_NOT_REQUIRED")
            counts = payload.get("closure_counts", {})
            self.assertEqual(counts.get("total_commitment_count"), 0)
            self.assertEqual(counts.get("stale_rollover_count"), 0)
            self.assertEqual(payload.get("warning_codes"), [])

    def test_due_cycle_unchanged_open_commitment_triggers_stale_rollover(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            commitments = root / "commitments.json"
            completion = root / "completion.json"
            previous_closure = root / "previous-closure-report.json"
            closure_report = root / "closure-report.json"

            commitment_row = {
                "commitment_id": "gl39-gl37-submission-queue-gl23-slot-001-text",
                "owner": "controlled-beta-ops",
                "queue_item_id": "gl37-submission-queue-gl23-slot-001-text",
                "backfill_action_id": "gl23-slot-001-text",
                "required_modality": "text",
                "priority_rank": 1,
                "commitment_type": "submit_real_loop_evidence",
                "commitment_status": "pending_submission",
                "reason": "pending_template_submission_required",
                "source_transition_state": "pending_submission",
                "cycle_due_at_utc": "2026-05-29T09:00:00Z",
                "escalation_severity": "",
            }
            transition_row = {
                "queue_item_id": "gl37-submission-queue-gl23-slot-001-text",
                "queue_item_status_gl37": "pending_submission",
                "handoff_queue_status_gl24": "open",
                "transition_state": "pending_submission",
                "backfill_action_id": "gl23-slot-001-text",
                "linked_submission_loop_id": "",
                "linked_submission_review_task_id": "",
                "linked_submission_reviewed_at_utc": "",
            }

            _write_json(
                commitments,
                _commitments_report(
                    commitment_status="COMMITMENTS_ACTIVE",
                    cadence_status="CADENCE_DUE",
                    rows=[commitment_row],
                ),
            )
            _write_json(completion, _completion_report(transition_rows=[transition_row]))
            _write_json(
                previous_closure,
                {
                    "schema_version": "real_trial_submission_queue_commitment_closure.v1",
                    "generated_at_utc": "2026-05-29T08:00:00Z",
                    "closure_counts": {
                        "closed_with_acknowledgement_count": 0,
                    },
                    "commitment_closure_rows": [
                        {
                            "commitment_id": commitment_row["commitment_id"],
                            "commitment_status_gl39": "pending_submission",
                            "transition_state_gl38": "pending_submission",
                            "closure_state": "open_commitment",
                            "closure_acknowledged": False,
                        }
                    ],
                },
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-commitments-report",
                    str(commitments),
                    "--submission-queue-completion-report",
                    str(completion),
                    "--previous-commitment-closure-report",
                    str(previous_closure),
                    "--output",
                    str(closure_report),
                    "--summary-output",
                    "-",
                    "--fail-on-stale-rollover",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr + completed.stdout)
            payload = json.loads(closure_report.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("commitment_closure_status"), "CLOSURE_STALE_ROLLOVER_REQUIRED")
            self.assertEqual(
                payload.get("cadence_run_closure_status"),
                "CLOSURE_RUN_DUE_WITH_STALE_ROLLOVER",
            )
            counts = payload.get("closure_counts", {})
            self.assertEqual(counts.get("total_commitment_count"), 1)
            self.assertEqual(counts.get("active_commitment_count"), 1)
            self.assertEqual(counts.get("stale_rollover_count"), 1)
            self.assertEqual(counts.get("net_new_closed_with_acknowledgement_count"), 0)
            self.assertIn("commitment_stale_rollover_detected", payload.get("warning_codes", []))
            stale_rows = payload.get("stale_rollover_rows", [])
            self.assertEqual(len(stale_rows), 1)
            self.assertEqual(stale_rows[0].get("commitment_id"), commitment_row["commitment_id"])
            self.assertIn(
                "unchanged_open_commitment_across_cycles",
                stale_rows[0].get("stale_reason_codes", []),
            )


if __name__ == "__main__":
    unittest.main()
