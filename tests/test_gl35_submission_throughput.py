from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "gl35_submission_throughput.py"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _collection_report(*, loop_ids: list[str], modality_counts: dict[str, int]) -> dict[str, Any]:
    return {
        "schema_version": "real_trial_loop_collection.v1",
        "generated_at_utc": "2026-05-29T00:00:00Z",
        "collected_real_launch_gate_eligible_loops": [
            {"loop_id": loop_id, "modality": "text"} for loop_id in loop_ids
        ],
        "launch_gate_alignment": {
            "launch_gate_eligible_complete_loop_count": sum(modality_counts.values()),
            "launch_gate_eligible_modality_count": len(
                [modality for modality, value in modality_counts.items() if value > 0]
            ),
            "missing_complete_loops_to_threshold": max(0, 10 - sum(modality_counts.values())),
            "missing_modalities_to_threshold": max(
                0,
                4 - len([modality for modality, value in modality_counts.items() if value > 0]),
            ),
            "recommended_backfill_slot_count": max(0, 10 - sum(modality_counts.values())),
            "target_launch_modality_loop_counts": modality_counts,
        },
    }


def _backfill_execution_report(*, remaining_slot_count: int, submission_backed_remaining_slot_count: int) -> dict[str, Any]:
    return {
        "schema_version": "real_trial_backfill_execution.v1",
        "generated_at_utc": "2026-05-29T00:00:00Z",
        "slot_counts": {"remaining_slot_count": remaining_slot_count},
        "submission_backed_slot_counts": {
            "submission_backed_remaining_slot_count": submission_backed_remaining_slot_count
        },
    }


def _submission_consumption_report(
    *,
    consumed_loop_count: int,
    status: str = "NO_SUBMISSIONS_PROVIDED",
    template_loop_count: int = 0,
    pending_template_loop_count: int = 0,
    invalid_submission_count: int = 0,
    unresolved_submission_count: int = 0,
    pending_template_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    rows = pending_template_rows if isinstance(pending_template_rows, list) else []
    return {
        "schema_version": "real_trial_backfill_submission_consumption.v1",
        "generated_at_utc": "2026-05-29T00:00:00Z",
        "consumption_status": status,
        "counts": {
            "template_loop_count": template_loop_count,
            "consumed_loop_count": consumed_loop_count,
            "pending_template_loop_count": pending_template_loop_count,
            "invalid_submission_count": invalid_submission_count,
            "unresolved_submission_count": unresolved_submission_count,
        },
        "pending_template_rows": rows,
    }


class RealTrialSubmissionThroughputScriptTests(unittest.TestCase):
    def test_baseline_initializes_when_no_previous_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            collection_report = root / "collection-report.json"
            backfill_execution_report = root / "backfill-execution-report.json"
            submission_consumption_report = root / "submission-consumption-report.json"
            output_report = root / "throughput-report.json"
            output_summary = root / "throughput-summary.md"

            _write_json(
                collection_report,
                _collection_report(
                    loop_ids=["real-text-001"],
                    modality_counts={"text": 1, "audio": 0, "image": 0, "video": 0},
                ),
            )
            _write_json(
                backfill_execution_report,
                _backfill_execution_report(
                    remaining_slot_count=9,
                    submission_backed_remaining_slot_count=9,
                ),
            )
            _write_json(
                submission_consumption_report,
                _submission_consumption_report(consumed_loop_count=0),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--collection-report",
                    str(collection_report),
                    "--backfill-execution-report",
                    str(backfill_execution_report),
                    "--backfill-submission-consumption-report",
                    str(submission_consumption_report),
                    "--output",
                    str(output_report),
                    "--summary-output",
                    str(output_summary),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            payload = json.loads(output_report.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("throughput_status"), "THROUGHPUT_BASELINE_INITIALIZED")
            self.assertFalse(payload.get("threshold_met"))
            snapshot = payload.get("snapshot", {})
            self.assertFalse(snapshot.get("previous_snapshot_available"))
            delta = snapshot.get("delta", {})
            self.assertEqual(delta.get("net_new_launch_gate_eligible_real_loop_count"), 1)
            self.assertEqual(delta.get("dropped_launch_gate_eligible_real_loop_count"), 0)
            self.assertIn("modality_gap_persists", payload.get("warning_codes", []))

    def test_progressing_status_when_snapshot_improves(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            collection_report = root / "collection-report.json"
            backfill_execution_report = root / "backfill-execution-report.json"
            submission_consumption_report = root / "submission-consumption-report.json"
            output_report = root / "throughput-report.json"
            output_summary = root / "throughput-summary.md"

            _write_json(
                collection_report,
                _collection_report(
                    loop_ids=["real-text-001"],
                    modality_counts={"text": 1, "audio": 0, "image": 0, "video": 0},
                ),
            )
            _write_json(
                backfill_execution_report,
                _backfill_execution_report(
                    remaining_slot_count=9,
                    submission_backed_remaining_slot_count=9,
                ),
            )
            _write_json(
                submission_consumption_report,
                _submission_consumption_report(consumed_loop_count=0),
            )
            baseline = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--collection-report",
                    str(collection_report),
                    "--backfill-execution-report",
                    str(backfill_execution_report),
                    "--backfill-submission-consumption-report",
                    str(submission_consumption_report),
                    "--output",
                    str(output_report),
                    "--summary-output",
                    str(output_summary),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(baseline.returncode, 0, baseline.stderr + baseline.stdout)

            _write_json(
                collection_report,
                _collection_report(
                    loop_ids=["real-text-001", "real-audio-001"],
                    modality_counts={"text": 1, "audio": 1, "image": 0, "video": 0},
                ),
            )
            _write_json(
                backfill_execution_report,
                _backfill_execution_report(
                    remaining_slot_count=8,
                    submission_backed_remaining_slot_count=8,
                ),
            )
            _write_json(
                submission_consumption_report,
                _submission_consumption_report(
                    consumed_loop_count=1,
                    status="CONSUMED_MANIFEST_READY",
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--collection-report",
                    str(collection_report),
                    "--backfill-execution-report",
                    str(backfill_execution_report),
                    "--backfill-submission-consumption-report",
                    str(submission_consumption_report),
                    "--output",
                    str(output_report),
                    "--summary-output",
                    str(output_summary),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            payload = json.loads(output_report.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("throughput_status"), "THROUGHPUT_PROGRESSING")
            snapshot = payload.get("snapshot", {})
            self.assertTrue(snapshot.get("previous_snapshot_available"))
            delta = snapshot.get("delta", {})
            self.assertEqual(delta.get("net_new_launch_gate_eligible_real_loop_count"), 1)
            self.assertEqual(delta.get("missing_complete_loops_to_threshold"), -1)
            self.assertEqual(delta.get("missing_modalities_to_threshold"), -1)
            self.assertEqual(delta.get("backfill_execution_remaining_slot_count"), -1)

    def test_fail_on_stalled_returns_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            collection_report = root / "collection-report.json"
            backfill_execution_report = root / "backfill-execution-report.json"
            submission_consumption_report = root / "submission-consumption-report.json"
            output_report = root / "throughput-report.json"

            _write_json(
                collection_report,
                _collection_report(
                    loop_ids=["real-text-001"],
                    modality_counts={"text": 1, "audio": 0, "image": 0, "video": 0},
                ),
            )
            _write_json(
                backfill_execution_report,
                _backfill_execution_report(
                    remaining_slot_count=9,
                    submission_backed_remaining_slot_count=9,
                ),
            )
            _write_json(
                submission_consumption_report,
                _submission_consumption_report(consumed_loop_count=0),
            )

            baseline = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--collection-report",
                    str(collection_report),
                    "--backfill-execution-report",
                    str(backfill_execution_report),
                    "--backfill-submission-consumption-report",
                    str(submission_consumption_report),
                    "--output",
                    str(output_report),
                    "--summary-output",
                    "-",
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
                    "--collection-report",
                    str(collection_report),
                    "--backfill-execution-report",
                    str(backfill_execution_report),
                    "--backfill-submission-consumption-report",
                    str(submission_consumption_report),
                    "--output",
                    str(output_report),
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
            payload = json.loads(output_report.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("throughput_status"), "THROUGHPUT_STALLED")
            self.assertIn("no_net_new_launch_gate_eligible_real_loops", payload.get("warning_codes", []))

    def test_threshold_met_status_when_gaps_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            collection_report = root / "collection-report.json"
            backfill_execution_report = root / "backfill-execution-report.json"
            submission_consumption_report = root / "submission-consumption-report.json"
            output_report = root / "throughput-report.json"

            _write_json(
                collection_report,
                _collection_report(
                    loop_ids=[
                        "real-text-001",
                        "real-audio-001",
                        "real-image-001",
                        "real-video-001",
                        "real-text-002",
                        "real-audio-002",
                        "real-image-002",
                        "real-video-002",
                        "real-text-003",
                        "real-audio-003",
                    ],
                    modality_counts={"text": 3, "audio": 3, "image": 2, "video": 2},
                ),
            )
            _write_json(
                backfill_execution_report,
                _backfill_execution_report(
                    remaining_slot_count=0,
                    submission_backed_remaining_slot_count=0,
                ),
            )
            _write_json(
                submission_consumption_report,
                _submission_consumption_report(
                    consumed_loop_count=2,
                    status="CONSUMED_MANIFEST_READY",
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--collection-report",
                    str(collection_report),
                    "--backfill-execution-report",
                    str(backfill_execution_report),
                    "--backfill-submission-consumption-report",
                    str(submission_consumption_report),
                    "--output",
                    str(output_report),
                    "--summary-output",
                    "-",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            payload = json.loads(output_report.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("throughput_status"), "THROUGHPUT_THRESHOLD_MET")
            self.assertTrue(payload.get("threshold_met"))
            current = payload.get("snapshot", {}).get("current", {})
            self.assertEqual(current.get("missing_complete_loops_to_threshold"), 0)
            self.assertEqual(current.get("missing_modalities_to_threshold"), 0)

    def test_stalled_status_exposes_gl36_execution_focus_actions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            collection_report = root / "collection-report.json"
            backfill_execution_report = root / "backfill-execution-report.json"
            submission_consumption_report = root / "submission-consumption-report.json"
            output_report = root / "throughput-report.json"

            _write_json(
                collection_report,
                _collection_report(
                    loop_ids=["real-text-001"],
                    modality_counts={"text": 1, "audio": 0, "image": 0, "video": 0},
                ),
            )
            _write_json(
                backfill_execution_report,
                _backfill_execution_report(
                    remaining_slot_count=9,
                    submission_backed_remaining_slot_count=9,
                ),
            )
            _write_json(
                submission_consumption_report,
                _submission_consumption_report(
                    consumed_loop_count=0,
                    template_loop_count=2,
                    pending_template_loop_count=2,
                    pending_template_rows=[
                        {
                            "backfill_action_id": "gl23-slot-002-audio",
                            "backfill_slot_index": 2,
                            "required_modality": "audio",
                        },
                        {
                            "backfill_action_id": "gl23-slot-004-video",
                            "backfill_slot_index": 4,
                            "required_modality": "video",
                        },
                    ],
                ),
            )

            baseline = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--collection-report",
                    str(collection_report),
                    "--backfill-execution-report",
                    str(backfill_execution_report),
                    "--backfill-submission-consumption-report",
                    str(submission_consumption_report),
                    "--output",
                    str(output_report),
                    "--summary-output",
                    "-",
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
                    "--collection-report",
                    str(collection_report),
                    "--backfill-execution-report",
                    str(backfill_execution_report),
                    "--backfill-submission-consumption-report",
                    str(submission_consumption_report),
                    "--output",
                    str(output_report),
                    "--summary-output",
                    "-",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            payload = json.loads(output_report.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("throughput_status"), "THROUGHPUT_STALLED")
            execution_focus = payload.get("execution_focus", {})
            self.assertEqual(execution_focus.get("action_plan_status"), "ACTION_PLAN_WAITING_FOR_SUBMISSIONS")
            self.assertEqual(execution_focus.get("pending_submission_action_count"), 2)
            self.assertEqual(execution_focus.get("recommended_submission_action_count"), 2)
            self.assertEqual(
                execution_focus.get("action_plan_blockers"),
                [
                    "real_loop_volume_below_threshold",
                    "real_loop_modality_coverage_below_threshold",
                    "throughput_not_progressing",
                    "no_real_submissions_provided",
                ],
            )
            priority_modalities = execution_focus.get("priority_modalities", [])
            self.assertEqual(priority_modalities[0], {"modality": "audio", "pending_slot_count": 1})
            self.assertEqual(priority_modalities[1], {"modality": "video", "pending_slot_count": 1})
            recommended_actions = execution_focus.get("recommended_submission_actions", [])
            self.assertEqual(recommended_actions[0].get("backfill_action_id"), "gl23-slot-002-audio")
            self.assertEqual(recommended_actions[0].get("reason"), "pending_template_submission_required")
            self.assertEqual(recommended_actions[1].get("backfill_action_id"), "gl23-slot-004-video")

    def test_gl36_execution_focus_blocked_by_submission_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            collection_report = root / "collection-report.json"
            backfill_execution_report = root / "backfill-execution-report.json"
            submission_consumption_report = root / "submission-consumption-report.json"
            output_report = root / "throughput-report.json"

            _write_json(
                collection_report,
                _collection_report(
                    loop_ids=[],
                    modality_counts={"text": 0, "audio": 0, "image": 0, "video": 0},
                ),
            )
            _write_json(
                backfill_execution_report,
                _backfill_execution_report(
                    remaining_slot_count=10,
                    submission_backed_remaining_slot_count=10,
                ),
            )
            _write_json(
                submission_consumption_report,
                _submission_consumption_report(
                    consumed_loop_count=0,
                    status="CONSUMPTION_INCOMPLETE",
                    template_loop_count=3,
                    pending_template_loop_count=1,
                    invalid_submission_count=1,
                    unresolved_submission_count=1,
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--collection-report",
                    str(collection_report),
                    "--backfill-execution-report",
                    str(backfill_execution_report),
                    "--backfill-submission-consumption-report",
                    str(submission_consumption_report),
                    "--output",
                    str(output_report),
                    "--summary-output",
                    "-",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            payload = json.loads(output_report.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("throughput_status"), "THROUGHPUT_BASELINE_INITIALIZED")
            warning_codes = payload.get("warning_codes", [])
            self.assertIn("invalid_submission_rows_present", warning_codes)
            self.assertIn("unresolved_submission_rows_present", warning_codes)
            execution_focus = payload.get("execution_focus", {})
            self.assertEqual(execution_focus.get("action_plan_status"), "ACTION_PLAN_BLOCKED_BY_SUBMISSION_ERRORS")
            self.assertEqual(execution_focus.get("submission_consumption_invalid_submission_count"), 1)
            self.assertEqual(execution_focus.get("submission_consumption_unresolved_submission_count"), 1)
            self.assertIn("invalid_submission_rows_present", execution_focus.get("action_plan_blockers", []))
            self.assertIn("unresolved_submission_rows_present", execution_focus.get("action_plan_blockers", []))


if __name__ == "__main__":
    unittest.main()
