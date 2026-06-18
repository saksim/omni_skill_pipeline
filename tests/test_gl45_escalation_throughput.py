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
    / "gl45_escalation_throughput.py"
)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _gl44_ack_report(
    *,
    status: str,
    rows: list[dict[str, Any]],
    counts_override: dict[str, int] | None = None,
) -> dict[str, Any]:
    counts = {
        "total_item_count": len(rows),
        "open_item_count": sum(
            1 for row in rows if str(row.get("acknowledgement_item_status", "")).strip() == "open"
        ),
        "resolved_acknowledged_item_count": sum(
            1 for row in rows if str(row.get("acknowledgement_status", "")).strip() == "resolved_acknowledged"
        ),
        "pending_ack_item_count": sum(
            1 for row in rows if str(row.get("acknowledgement_status", "")).strip() == "pending_ack"
        ),
        "blocked_item_count": sum(
            1 for row in rows if str(row.get("acknowledgement_status", "")).strip() == "blocked"
        ),
    }
    if isinstance(counts_override, dict):
        counts.update({key: int(value) for key, value in counts_override.items()})

    return {
        "schema_version": "real_trial_submission_queue_followup_resolution_escalation_acknowledgements.v1",
        "generated_at_utc": "2026-05-30T00:00:00Z",
        "followup_resolution_escalation_acknowledgement_status": status,
        "warning_codes": [],
        "followup_resolution_escalation_acknowledgement_counts": counts,
        "owner_followup_resolution_escalation_acknowledgement_counts": {},
        "followup_resolution_escalation_acknowledgement_rows": rows,
    }


def _gl12_collection_report(
    *,
    program_status: str,
    loops: list[dict[str, Any]],
    missing_complete_loops_to_threshold: int,
    missing_modalities_to_threshold: int,
) -> dict[str, Any]:
    modality_counts: dict[str, int] = {}
    for row in loops:
        modality = str(row.get("modality", "")).strip().lower()
        if modality:
            modality_counts[modality] = modality_counts.get(modality, 0) + 1
    return {
        "schema_version": "real_trial_loop_collection.v1",
        "generated_at_utc": "2026-05-30T00:01:00Z",
        "launch_gate_alignment": {
            "program_status": program_status,
            "launch_gate_eligible_complete_loop_count": len(loops),
            "launch_gate_eligible_modality_count": len([key for key, value in modality_counts.items() if value > 0]),
            "missing_complete_loops_to_threshold": missing_complete_loops_to_threshold,
            "missing_modalities_to_threshold": missing_modalities_to_threshold,
        },
        "collected_real_launch_gate_eligible_loops": loops,
    }


class RealTrialSubmissionQueueFollowupResolutionEscalationThroughputScriptTests(unittest.TestCase):
    def test_baseline_initialized_with_unmapped_ack_loop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            ack_report = root / "ack-report.json"
            collection_report = root / "collection-report.json"
            throughput_report = root / "throughput-report.json"

            _write_json(
                ack_report,
                _gl44_ack_report(
                    status="FOLLOWUP_RESOLUTION_ESCALATION_ACK_COMPLETE",
                    rows=[
                        {
                            "acknowledgement_item_id": "gl44-ack-001",
                            "acknowledgement_item_status": "closed",
                            "acknowledgement_status": "resolved_acknowledged",
                            "linked_submission_loop_id_gl24": "real-text-001",
                            "required_modality": "text",
                        }
                    ],
                ),
            )
            _write_json(
                collection_report,
                _gl12_collection_report(
                    program_status="COLLECTION_INCOMPLETE",
                    loops=[],
                    missing_complete_loops_to_threshold=10,
                    missing_modalities_to_threshold=4,
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-escalation-acknowledgements-report",
                    str(ack_report),
                    "--collection-report",
                    str(collection_report),
                    "--output",
                    str(throughput_report),
                    "--summary-output",
                    "-",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            payload = json.loads(throughput_report.read_text(encoding="utf-8"))
            self.assertEqual(
                payload.get("followup_resolution_escalation_throughput_status"),
                "ESCALATION_ACK_THROUGHPUT_BASELINE_INITIALIZED",
            )
            delta = payload.get("snapshot_delta", {})
            self.assertEqual(delta.get("net_new_resolved_acknowledged_item_count"), 1)
            self.assertEqual(delta.get("net_new_resolved_submission_loop_count"), 1)
            self.assertEqual(delta.get("net_new_launch_gate_eligible_loop_count"), 0)
            self.assertEqual(delta.get("unresolved_ack_closed_loop_count"), 1)
            warning_codes = payload.get("warning_codes", [])
            self.assertIn(
                "resolved_acknowledgements_not_visible_in_launch_gate_eligible_loops",
                warning_codes,
            )
            unresolved_loops = payload.get("unresolved_acknowledged_submission_loop_ids", [])
            self.assertEqual(unresolved_loops, ["real-text-001"])

    def test_progressing_when_net_new_ack_and_collection_loops_grow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            ack_report = root / "ack-report.json"
            collection_report = root / "collection-report.json"
            throughput_report = root / "throughput-report.json"

            _write_json(
                ack_report,
                _gl44_ack_report(
                    status="FOLLOWUP_RESOLUTION_ESCALATION_ACK_PENDING_ACTION_REQUIRED",
                    rows=[
                        {
                            "acknowledgement_item_id": "gl44-ack-001",
                            "acknowledgement_item_status": "open",
                            "acknowledgement_status": "pending_ack",
                            "linked_submission_loop_id_gl24": "",
                            "required_modality": "text",
                        }
                    ],
                ),
            )
            _write_json(
                collection_report,
                _gl12_collection_report(
                    program_status="COLLECTION_INCOMPLETE",
                    loops=[{"loop_id": "real-text-000", "modality": "text"}],
                    missing_complete_loops_to_threshold=9,
                    missing_modalities_to_threshold=3,
                ),
            )
            baseline = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-escalation-acknowledgements-report",
                    str(ack_report),
                    "--collection-report",
                    str(collection_report),
                    "--output",
                    str(throughput_report),
                    "--summary-output",
                    "-",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(baseline.returncode, 0, baseline.stderr + baseline.stdout)

            _write_json(
                ack_report,
                _gl44_ack_report(
                    status="FOLLOWUP_RESOLUTION_ESCALATION_ACK_COMPLETE",
                    rows=[
                        {
                            "acknowledgement_item_id": "gl44-ack-001",
                            "acknowledgement_item_status": "closed",
                            "acknowledgement_status": "resolved_acknowledged",
                            "linked_submission_loop_id_gl24": "real-text-000",
                            "required_modality": "text",
                        },
                        {
                            "acknowledgement_item_id": "gl44-ack-002",
                            "acknowledgement_item_status": "closed",
                            "acknowledgement_status": "resolved_acknowledged",
                            "linked_submission_loop_id_gl24": "real-audio-001",
                            "required_modality": "audio",
                        },
                    ],
                ),
            )
            _write_json(
                collection_report,
                _gl12_collection_report(
                    program_status="COLLECTION_INCOMPLETE",
                    loops=[
                        {"loop_id": "real-text-000", "modality": "text"},
                        {"loop_id": "real-audio-001", "modality": "audio"},
                    ],
                    missing_complete_loops_to_threshold=8,
                    missing_modalities_to_threshold=2,
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-escalation-acknowledgements-report",
                    str(ack_report),
                    "--collection-report",
                    str(collection_report),
                    "--output",
                    str(throughput_report),
                    "--summary-output",
                    "-",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            payload = json.loads(throughput_report.read_text(encoding="utf-8"))
            self.assertEqual(
                payload.get("followup_resolution_escalation_throughput_status"),
                "ESCALATION_ACK_THROUGHPUT_PROGRESSING",
            )
            delta = payload.get("snapshot_delta", {})
            self.assertEqual(delta.get("net_new_resolved_acknowledged_item_count"), 2)
            self.assertEqual(delta.get("net_new_resolved_submission_loop_count"), 2)
            self.assertEqual(delta.get("net_new_launch_gate_eligible_loop_count"), 1)
            self.assertEqual(delta.get("unresolved_ack_closed_loop_count"), 0)
            net_new_loop_ids = payload.get("net_new_launch_gate_eligible_loop_ids", [])
            self.assertEqual(net_new_loop_ids, ["real-audio-001"])

    def test_stalled_exit_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            ack_report = root / "ack-report.json"
            collection_report = root / "collection-report.json"
            throughput_report = root / "throughput-report.json"

            _write_json(
                ack_report,
                _gl44_ack_report(
                    status="FOLLOWUP_RESOLUTION_ESCALATION_ACK_PENDING_ACTION_REQUIRED",
                    rows=[
                        {
                            "acknowledgement_item_id": "gl44-ack-001",
                            "acknowledgement_item_status": "open",
                            "acknowledgement_status": "pending_ack",
                            "linked_submission_loop_id_gl24": "",
                            "required_modality": "text",
                        }
                    ],
                ),
            )
            _write_json(
                collection_report,
                _gl12_collection_report(
                    program_status="COLLECTION_INCOMPLETE",
                    loops=[],
                    missing_complete_loops_to_threshold=10,
                    missing_modalities_to_threshold=4,
                ),
            )

            baseline = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-escalation-acknowledgements-report",
                    str(ack_report),
                    "--collection-report",
                    str(collection_report),
                    "--output",
                    str(throughput_report),
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
                    "--submission-queue-followup-resolution-escalation-acknowledgements-report",
                    str(ack_report),
                    "--collection-report",
                    str(collection_report),
                    "--output",
                    str(throughput_report),
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
            payload = json.loads(throughput_report.read_text(encoding="utf-8"))
            self.assertEqual(
                payload.get("followup_resolution_escalation_throughput_status"),
                "ESCALATION_ACK_THROUGHPUT_STALLED",
            )
            warning_codes = payload.get("warning_codes", [])
            self.assertIn("no_net_new_resolved_acknowledgements", warning_codes)
            self.assertIn("no_net_new_launch_gate_eligible_real_loops", warning_codes)
            self.assertIn("open_acknowledgement_items_present", warning_codes)


if __name__ == "__main__":
    unittest.main()
