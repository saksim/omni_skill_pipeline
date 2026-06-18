from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "gl22_backfill_exec.py"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _backfill_plan(*, slots: list[dict[str, Any]], plan_status: str = "ACTION_REQUIRED") -> dict[str, Any]:
    return {
        "schema_version": "real_trial_loop_backfill_plan.v1",
        "generated_at_utc": "2026-05-27T00:00:00Z",
        "plan_status": plan_status,
        "thresholds": {
            "minimum_complete_loops": 10,
            "minimum_modalities": 4,
            "target_launch_modalities": ["text", "audio", "image", "video"],
        },
        "current_coverage": {
            "launch_gate_eligible_complete_loop_count": 0,
            "launch_gate_eligible_modality_count": 0,
            "launch_gate_eligible_modalities": [],
            "target_launch_modality_loop_counts": {"text": 0, "audio": 0, "image": 0, "video": 0},
        },
        "remaining_gap": {
            "missing_complete_loops_to_threshold": 10,
            "missing_modalities_to_threshold": 4,
            "missing_target_launch_modalities": ["text", "audio", "image", "video"],
        },
        "recommended_backfill_slot_count": len(slots),
        "recommended_backfill_slots": slots,
        "blockers": ["real_loop_volume_below_threshold", "real_loop_modality_coverage_below_threshold"],
    }


def _collection_report(
    *,
    modality_counts: dict[str, int],
    blockers: list[str] | None = None,
    collected_real_launch_gate_eligible_loops: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": "real_trial_loop_collection.v1",
        "generated_at_utc": "2026-05-27T00:10:00Z",
        "collected_real_launch_gate_eligible_loops": collected_real_launch_gate_eligible_loops or [],
        "launch_gate_alignment": {
            "program_status": "COLLECTION_INCOMPLETE",
            "launch_gate_eligible_complete_loop_count": sum(modality_counts.values()),
            "launch_gate_eligible_modality_count": len([key for key, value in modality_counts.items() if value > 0]),
            "missing_complete_loops_to_threshold": max(0, 10 - sum(modality_counts.values())),
            "missing_modalities_to_threshold": max(0, 4 - len([key for key, value in modality_counts.items() if value > 0])),
            "target_launch_modality_loop_counts": modality_counts,
            "blockers": blockers if blockers is not None else ["real_loop_volume_below_threshold"],
        },
    }


class RealTrialBackfillExecutionScriptTests(unittest.TestCase):
    def test_backfill_execution_reports_progress(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            backfill_plan = root / "backfill-plan.json"
            collection_report = root / "collection-report.json"
            execution_report = root / "backfill-execution-report.json"
            execution_summary = root / "backfill-execution-summary.md"

            _write_json(
                backfill_plan,
                _backfill_plan(
                    slots=[
                        {
                            "slot_index": 1,
                            "required_modality": "text",
                            "reason": "missing_target_launch_modality",
                        },
                        {
                            "slot_index": 2,
                            "required_modality": "audio",
                            "reason": "missing_target_launch_modality",
                        },
                        {
                            "slot_index": 3,
                            "required_modality": "image",
                            "reason": "loop_volume_gap_after_modality_coverage",
                        },
                    ]
                ),
            )
            _write_json(
                collection_report,
                _collection_report(modality_counts={"text": 1, "audio": 0, "image": 2, "video": 0}),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--backfill-plan",
                    str(backfill_plan),
                    "--collection-report",
                    str(collection_report),
                    "--output",
                    str(execution_report),
                    "--summary-output",
                    str(execution_summary),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            self.assertIn("status=BACKFILL_IN_PROGRESS", completed.stdout)

            report_payload = json.loads(execution_report.read_text(encoding="utf-8"))
            self.assertEqual(report_payload.get("execution_status"), "BACKFILL_IN_PROGRESS")
            self.assertEqual(report_payload.get("submission_backed_execution_status"), "SUBMISSION_BACKED_IN_PROGRESS")
            slot_counts = report_payload.get("slot_counts", {})
            self.assertEqual(slot_counts.get("total_slots"), 3)
            self.assertEqual(slot_counts.get("fulfilled_slot_count"), 2)
            self.assertEqual(slot_counts.get("remaining_slot_count"), 1)
            submission_backed_slot_counts = report_payload.get("submission_backed_slot_counts", {})
            self.assertEqual(submission_backed_slot_counts.get("submission_backed_fulfilled_slot_count"), 0)
            self.assertEqual(submission_backed_slot_counts.get("submission_backed_remaining_slot_count"), 3)
            self.assertEqual(submission_backed_slot_counts.get("fulfilled_without_submission_linkage_count"), 2)
            self.assertEqual(submission_backed_slot_counts.get("submission_linked_without_modality_delta_count"), 0)

            records = report_payload.get("slot_execution_records", [])
            self.assertEqual([item.get("execution_status") for item in records], ["fulfilled", "pending", "fulfilled"])
            self.assertEqual(
                report_payload.get("coverage_delta", {}).get("gained_target_launch_modality_loop_counts", {}),
                {"audio": 0, "image": 2, "text": 1, "video": 0},
            )
            self.assertEqual(
                report_payload.get("submission_linkage_counts", {}).get("submission_linked_slot_count"),
                0,
            )

            summary = execution_summary.read_text(encoding="utf-8")
            self.assertIn("Execution status: `BACKFILL_IN_PROGRESS`", summary)
            self.assertIn("Fulfilled slots: `2`", summary)

    def test_fail_on_incomplete_returns_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            backfill_plan = root / "backfill-plan.json"
            collection_report = root / "collection-report.json"

            _write_json(
                backfill_plan,
                _backfill_plan(
                    slots=[
                        {
                            "slot_index": 1,
                            "required_modality": "audio",
                            "reason": "missing_target_launch_modality",
                        }
                    ]
                ),
            )
            _write_json(
                collection_report,
                _collection_report(modality_counts={"text": 1, "audio": 0, "image": 0, "video": 0}),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--backfill-plan",
                    str(backfill_plan),
                    "--collection-report",
                    str(collection_report),
                    "--output",
                    "-",
                    "--summary-output",
                    "-",
                    "--fail-on-incomplete",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr + completed.stdout)
            self.assertIn("status=BACKFILL_IN_PROGRESS", completed.stdout)

    def test_no_action_required_when_plan_already_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            backfill_plan = root / "backfill-plan.json"
            collection_report = root / "collection-report.json"
            execution_report = root / "backfill-execution-report.json"

            _write_json(
                backfill_plan,
                _backfill_plan(slots=[], plan_status="ALREADY_THRESHOLD_READY"),
            )
            _write_json(
                collection_report,
                _collection_report(modality_counts={"text": 3, "audio": 3, "image": 2, "video": 2}, blockers=[]),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--backfill-plan",
                    str(backfill_plan),
                    "--collection-report",
                    str(collection_report),
                    "--output",
                    str(execution_report),
                    "--summary-output",
                    "-",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            report_payload = json.loads(execution_report.read_text(encoding="utf-8"))
            self.assertEqual(report_payload.get("execution_status"), "NO_ACTION_REQUIRED")
            self.assertEqual(report_payload.get("submission_backed_execution_status"), "NO_ACTION_REQUIRED")
            self.assertEqual(report_payload.get("slot_counts", {}).get("total_slots"), 0)

    def test_submission_linkage_maps_to_slots_and_reports_unmatched_linkages(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            backfill_plan = root / "backfill-plan.json"
            collection_report = root / "collection-report.json"
            execution_report = root / "backfill-execution-report.json"

            _write_json(
                backfill_plan,
                _backfill_plan(
                    slots=[
                        {
                            "slot_index": 1,
                            "required_modality": "text",
                            "reason": "missing_target_launch_modality",
                        },
                        {
                            "slot_index": 2,
                            "required_modality": "audio",
                            "reason": "loop_volume_gap_after_modality_coverage",
                        },
                    ]
                ),
            )
            _write_json(
                collection_report,
                _collection_report(
                    modality_counts={"text": 1, "audio": 1, "image": 0, "video": 0},
                    collected_real_launch_gate_eligible_loops=[
                        {
                            "loop_id": "real-text-001",
                            "modality": "text",
                            "backfill_slot_index": 1,
                            "backfill_action_id": "gl23-slot-001-text",
                        },
                        {
                            "loop_id": "real-image-unmatched",
                            "modality": "image",
                            "backfill_slot_index": 9,
                            "backfill_action_id": "gl23-slot-009-image",
                        },
                    ],
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--backfill-plan",
                    str(backfill_plan),
                    "--collection-report",
                    str(collection_report),
                    "--output",
                    str(execution_report),
                    "--summary-output",
                    "-",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            payload = json.loads(execution_report.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("execution_status"), "BACKFILL_COMPLETE")
            self.assertEqual(payload.get("submission_backed_execution_status"), "SUBMISSION_BACKED_IN_PROGRESS")
            linkage_counts = payload.get("submission_linkage_counts", {})
            self.assertEqual(linkage_counts.get("submission_linked_slot_count"), 1)
            self.assertEqual(linkage_counts.get("slot_linked_count"), 1)
            self.assertEqual(linkage_counts.get("action_linked_count"), 1)
            self.assertEqual(linkage_counts.get("unmatched_submission_linkage_count"), 2)
            submission_backed_slot_counts = payload.get("submission_backed_slot_counts", {})
            self.assertEqual(submission_backed_slot_counts.get("submission_backed_fulfilled_slot_count"), 1)
            self.assertEqual(submission_backed_slot_counts.get("submission_backed_remaining_slot_count"), 1)
            self.assertEqual(submission_backed_slot_counts.get("fulfilled_without_submission_linkage_count"), 1)
            self.assertEqual(submission_backed_slot_counts.get("submission_linked_without_modality_delta_count"), 0)
            slot_records = payload.get("slot_execution_records", [])
            self.assertEqual(slot_records[0].get("submission_linked"), True)
            self.assertEqual(slot_records[0].get("submission_linkage_resolution"), "slot_index_and_action_id")
            self.assertEqual(slot_records[0].get("expected_action_id"), "gl23-slot-001-text")
            self.assertEqual(slot_records[1].get("submission_linked"), False)
            unmatched = payload.get("unmatched_submission_linkages", [])
            self.assertEqual(len(unmatched), 2)

    def test_submission_backed_status_complete_with_linked_pending_and_fulfilled_slots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            backfill_plan = root / "backfill-plan.json"
            collection_report = root / "collection-report.json"
            execution_report = root / "backfill-execution-report.json"

            _write_json(
                backfill_plan,
                _backfill_plan(
                    slots=[
                        {
                            "slot_index": 1,
                            "required_modality": "text",
                            "reason": "missing_target_launch_modality",
                        },
                        {
                            "slot_index": 2,
                            "required_modality": "audio",
                            "reason": "missing_target_launch_modality",
                        },
                    ]
                ),
            )
            _write_json(
                collection_report,
                _collection_report(
                    modality_counts={"text": 1, "audio": 0, "image": 0, "video": 0},
                    collected_real_launch_gate_eligible_loops=[
                        {
                            "loop_id": "real-text-001",
                            "modality": "text",
                            "backfill_slot_index": 1,
                            "backfill_action_id": "gl23-slot-001-text",
                        },
                        {
                            "loop_id": "real-audio-linked-without-delta",
                            "modality": "audio",
                            "backfill_slot_index": 2,
                            "backfill_action_id": "gl23-slot-002-audio",
                        },
                    ],
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--backfill-plan",
                    str(backfill_plan),
                    "--collection-report",
                    str(collection_report),
                    "--output",
                    str(execution_report),
                    "--summary-output",
                    "-",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            payload = json.loads(execution_report.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("execution_status"), "BACKFILL_IN_PROGRESS")
            self.assertEqual(payload.get("submission_backed_execution_status"), "SUBMISSION_BACKED_COMPLETE")
            submission_backed_slot_counts = payload.get("submission_backed_slot_counts", {})
            self.assertEqual(submission_backed_slot_counts.get("submission_backed_fulfilled_slot_count"), 2)
            self.assertEqual(submission_backed_slot_counts.get("submission_backed_remaining_slot_count"), 0)
            self.assertEqual(submission_backed_slot_counts.get("fulfilled_without_submission_linkage_count"), 0)
            self.assertEqual(submission_backed_slot_counts.get("submission_linked_without_modality_delta_count"), 1)


if __name__ == "__main__":
    unittest.main()
