from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = (
    REPO_ROOT
    / "scripts"
    / "gl46_action_plan.py"
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _gl45_report(*, status: str, unresolved_loop_ids: list[str], warning_codes: list[str]) -> dict:
    return {
        "schema_version": "real_trial_submission_queue_followup_resolution_escalation_throughput.v1",
        "generated_at_utc": "2026-05-30T00:00:00Z",
        "followup_resolution_escalation_throughput_status": status,
        "warning_codes": warning_codes,
        "acknowledgement_snapshot": {
            "open_item_count": 0,
            "resolved_acknowledged_item_count": len(unresolved_loop_ids),
        },
        "collection_snapshot": {
            "missing_complete_loops_to_threshold": 0,
            "missing_modalities_to_threshold": 0,
        },
        "snapshot_delta": {
            "net_new_resolved_acknowledged_item_count": 0,
            "net_new_launch_gate_eligible_loop_count": 0,
        },
        "unresolved_acknowledged_submission_loop_ids": unresolved_loop_ids,
    }


def _collection_report(*, slots: list[dict], missing_loops: int, missing_modalities: int) -> dict:
    return {
        "schema_version": "real_trial_loop_collection.v1",
        "generated_at_utc": "2026-05-30T00:01:00Z",
        "launch_gate_alignment": {
            "missing_complete_loops_to_threshold": missing_loops,
            "missing_modalities_to_threshold": missing_modalities,
            "recommended_backfill_slots": slots,
        },
    }


class RealTrialSubmissionQueueFollowupResolutionEscalationActionPlanScriptTests(unittest.TestCase):
    def test_threshold_met_with_no_open_items(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            gl45 = root / "gl45.json"
            gl12 = root / "gl12.json"
            output = root / "gl46.json"

            _write_json(
                gl45,
                _gl45_report(
                    status="ESCALATION_ACK_THROUGHPUT_THRESHOLD_MET",
                    unresolved_loop_ids=[],
                    warning_codes=[],
                ),
            )
            _write_json(gl12, _collection_report(slots=[], missing_loops=0, missing_modalities=0))

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-escalation-throughput-report",
                    str(gl45),
                    "--collection-report",
                    str(gl12),
                    "--output",
                    str(output),
                    "--summary-output",
                    "-",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(
                payload.get("followup_resolution_escalation_action_plan_status"),
                "ACTION_PLAN_NOT_REQUIRED",
            )
            counts = payload.get("followup_resolution_escalation_action_plan_counts", {})
            self.assertEqual(counts.get("open_action_count"), 0)
            self.assertEqual(payload.get("followup_resolution_escalation_action_plan_rows"), [])

    def test_open_items_from_unresolved_and_recommended_slots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            gl45 = root / "gl45.json"
            gl12 = root / "gl12.json"
            output = root / "gl46.json"

            _write_json(
                gl45,
                _gl45_report(
                    status="ESCALATION_ACK_THROUGHPUT_STALLED",
                    unresolved_loop_ids=["real-audio-001"],
                    warning_codes=["loop_volume_gap_persists"],
                ),
            )
            _write_json(
                gl12,
                _collection_report(
                    slots=[
                        {"slot_index": 1, "required_modality": "video", "reason": "missing_target_launch_modality"},
                        {"slot_index": 2, "required_modality": "image", "reason": "loop_volume_gap_after_modality_coverage"},
                    ],
                    missing_loops=2,
                    missing_modalities=1,
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-escalation-throughput-report",
                    str(gl45),
                    "--collection-report",
                    str(gl12),
                    "--output",
                    str(output),
                    "--summary-output",
                    "-",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(
                payload.get("followup_resolution_escalation_action_plan_status"),
                "ACTION_PLAN_OPEN",
            )
            counts = payload.get("followup_resolution_escalation_action_plan_counts", {})
            self.assertEqual(counts.get("open_action_count"), 3)
            self.assertEqual(counts.get("unresolved_ack_mapping_action_count"), 1)
            self.assertEqual(counts.get("recommended_backfill_slot_action_count"), 2)
            warning_codes = payload.get("warning_codes", [])
            self.assertIn("loop_volume_gap_persists", warning_codes)
            self.assertIn("open_followup_resolution_escalation_action_plan_items_present", warning_codes)
            rows = payload.get("followup_resolution_escalation_action_plan_rows", [])
            self.assertEqual(len(rows), 3)
            self.assertEqual(rows[0].get("action_type"), "resolve_acknowledged_loop_mapping_gap")
            self.assertEqual(rows[1].get("required_modality"), "video")
            self.assertEqual(rows[2].get("required_modality"), "image")

    def test_fail_on_open(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            gl45 = root / "gl45.json"
            gl12 = root / "gl12.json"
            output = root / "gl46.json"

            _write_json(
                gl45,
                _gl45_report(
                    status="ESCALATION_ACK_THROUGHPUT_BASELINE_INITIALIZED",
                    unresolved_loop_ids=["real-text-001"],
                    warning_codes=[],
                ),
            )
            _write_json(gl12, _collection_report(slots=[], missing_loops=1, missing_modalities=0))

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-escalation-throughput-report",
                    str(gl45),
                    "--collection-report",
                    str(gl12),
                    "--output",
                    str(output),
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
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(
                payload.get("followup_resolution_escalation_action_plan_status"),
                "ACTION_PLAN_OPEN",
            )


if __name__ == "__main__":
    unittest.main()
