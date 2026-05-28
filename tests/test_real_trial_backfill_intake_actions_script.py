from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "run_real_trial_backfill_intake_actions.py"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _backfill_plan(slots: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "real_trial_loop_backfill_plan.v1",
        "generated_at_utc": "2026-05-27T00:00:00Z",
        "plan_status": "ACTION_REQUIRED",
        "thresholds": {
            "minimum_complete_loops": 10,
            "minimum_modalities": 4,
            "target_launch_modalities": ["text", "audio", "image", "video"],
        },
        "recommended_backfill_slot_count": len(slots),
        "recommended_backfill_slots": slots,
    }


def _backfill_execution_report(records: list[dict[str, Any]]) -> dict[str, Any]:
    fulfilled = len([item for item in records if str(item.get("execution_status", "")).lower() == "fulfilled"])
    total = len(records)
    return {
        "schema_version": "real_trial_backfill_execution.v1",
        "generated_at_utc": "2026-05-27T00:10:00Z",
        "execution_status": "BACKFILL_COMPLETE" if total > 0 and fulfilled == total else "BACKFILL_IN_PROGRESS",
        "slot_counts": {
            "total_slots": total,
            "fulfilled_slot_count": fulfilled,
            "remaining_slot_count": max(0, total - fulfilled),
        },
        "slot_execution_records": records,
        "launch_gate_alignment_snapshot": {
            "program_status": "COLLECTION_INCOMPLETE",
            "missing_complete_loops_to_threshold": max(0, total - fulfilled),
            "missing_modalities_to_threshold": 1 if fulfilled < total else 0,
            "blockers": ["real_loop_volume_below_threshold"] if fulfilled < total else [],
        },
    }


class RealTrialBackfillIntakeActionsScriptTests(unittest.TestCase):
    def test_generates_pending_and_closed_actions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            backfill_plan = root / "backfill-plan.json"
            execution_report = root / "backfill-execution-report.json"
            intake_report = root / "intake-actions-report.json"
            intake_summary = root / "intake-actions-summary.md"

            _write_json(
                backfill_plan,
                _backfill_plan(
                    [
                        {"slot_index": 1, "required_modality": "text", "reason": "missing_target_launch_modality"},
                        {"slot_index": 2, "required_modality": "audio", "reason": "loop_volume_gap_after_modality_coverage"},
                    ]
                ),
            )
            _write_json(
                execution_report,
                _backfill_execution_report(
                    [
                        {
                            "slot_index": 1,
                            "required_modality": "text",
                            "reason": "missing_target_launch_modality",
                            "execution_status": "fulfilled",
                            "available_modality_delta_before_assignment": 1,
                            "consumed_modality_delta": 1,
                        },
                        {
                            "slot_index": 2,
                            "required_modality": "audio",
                            "reason": "loop_volume_gap_after_modality_coverage",
                            "execution_status": "pending",
                            "available_modality_delta_before_assignment": 0,
                            "consumed_modality_delta": 0,
                        },
                    ]
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--backfill-plan",
                    str(backfill_plan),
                    "--backfill-execution-report",
                    str(execution_report),
                    "--output",
                    str(intake_report),
                    "--summary-output",
                    str(intake_summary),
                    "--owner",
                    "beta-ops-a",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            self.assertIn("status=ACTIONS_PENDING", completed.stdout)

            payload = json.loads(intake_report.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("intake_status"), "ACTIONS_PENDING")
            action_counts = payload.get("action_counts", {})
            self.assertEqual(action_counts.get("total_actions"), 2)
            self.assertEqual(action_counts.get("pending_action_count"), 1)
            self.assertEqual(action_counts.get("closed_action_count"), 1)
            actions = payload.get("actions", [])
            self.assertEqual(len(actions), 2)
            self.assertEqual(actions[0].get("action_status"), "closed")
            self.assertEqual(actions[1].get("action_status"), "pending")
            self.assertEqual(actions[1].get("owner"), "beta-ops-a")
            required_fields = actions[1].get("closure_evidence_requirements", {}).get("required_loop_manifest_fields", [])
            self.assertIn("source_reference", required_fields)
            summary = intake_summary.read_text(encoding="utf-8")
            self.assertIn("Pending actions: `1`", summary)

    def test_fail_on_pending_returns_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            backfill_plan = root / "backfill-plan.json"
            execution_report = root / "backfill-execution-report.json"

            _write_json(
                backfill_plan,
                _backfill_plan([{"slot_index": 1, "required_modality": "video", "reason": "missing_target_launch_modality"}]),
            )
            _write_json(
                execution_report,
                _backfill_execution_report(
                    [
                        {
                            "slot_index": 1,
                            "required_modality": "video",
                            "reason": "missing_target_launch_modality",
                            "execution_status": "pending",
                        }
                    ]
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--backfill-plan",
                    str(backfill_plan),
                    "--backfill-execution-report",
                    str(execution_report),
                    "--output",
                    "-",
                    "--summary-output",
                    "-",
                    "--fail-on-pending",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr + completed.stdout)
            self.assertIn("status=ACTIONS_PENDING", completed.stdout)

    def test_no_actions_required_when_plan_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            backfill_plan = root / "backfill-plan.json"
            execution_report = root / "backfill-execution-report.json"
            intake_report = root / "intake-actions-report.json"

            _write_json(backfill_plan, _backfill_plan([]))
            _write_json(execution_report, _backfill_execution_report([]))

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--backfill-plan",
                    str(backfill_plan),
                    "--backfill-execution-report",
                    str(execution_report),
                    "--output",
                    str(intake_report),
                    "--summary-output",
                    "-",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            payload = json.loads(intake_report.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("intake_status"), "NO_ACTION_REQUIRED")
            self.assertEqual(payload.get("action_counts", {}).get("total_actions"), 0)


if __name__ == "__main__":
    unittest.main()
