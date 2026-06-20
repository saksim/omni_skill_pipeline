from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "gl64_real_loop_manifest_preflight.py"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _workpack(*, work_items: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "real_trial_loop_intake_workpack.v1",
        "status": "REAL_LOOP_INTAKE_ACTION_REQUIRED" if work_items else "REAL_LOOP_INTAKE_NOT_REQUIRED",
        "launch_gate_policy_unchanged": True,
        "input_paths": {
            "operator_manifest_dir": "docs/working/status/baselines/real-trial-loop-collection/manifests",
        },
        "work_items": work_items,
    }


def _work_item(*, slot_index: int = 1, modality: str = "text") -> dict[str, Any]:
    return {
        "intake_item_id": "gl63-real-loop-intake-slot-%03d-%s" % (slot_index, modality),
        "required_modality": modality,
        "slot_index": slot_index,
        "manifest_drop_path": "docs/working/status/baselines/real-trial-loop-collection/manifests/real-loop-%03d-%s.json"
        % (slot_index, modality),
    }


def _valid_loop(
    *,
    loop_id: str = "real-text-001",
    modality: str = "text",
    slot_index: int = 1,
    backfill_action_id: str = "",
) -> dict[str, Any]:
    return {
        "loop_id": loop_id,
        "status": "complete",
        "modality": modality,
        "evidence_origin": "real",
        "launch_gate_eligible": True,
        "source_system": "pilot-ops",
        "source_reference": "ticket://INC-2001",
        "collected_at_utc": "2026-06-19T00:00:00Z",
        "review_task_id": "review-INC-2001",
        "reviewed_by": "reviewer-a",
        "reviewed_at_utc": "2026-06-19T00:05:00Z",
        "review_outcome": "approved",
        "revisions_before_approval": 1,
        "reviewer_edit_distance_pct": 18.0,
        "agent_smoke_result": "passed",
        "published_without_review": False,
        "critical_secret_or_pii_leak": False,
        "high_severity_incident": False,
        "latency_ms": 910.0,
        "provider_failure_count": 0,
        "provider_call_count": 2,
        "retry_count": 0,
        "artifact_count": 8,
        "estimated_cost_usd": 0.31,
        "backfill_slot_index": slot_index,
        "backfill_action_id": backfill_action_id or "gl23-slot-%03d-%s" % (slot_index, modality),
    }


class RealTrialLoopManifestPreflightScriptTests(unittest.TestCase):
    def test_not_required_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            workpack_path = root / "workpack.json"
            report_path = root / "preflight.json"
            _write_json(workpack_path, _workpack(work_items=[]))

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--workpack",
                    str(workpack_path),
                    "--output",
                    str(report_path),
                    "--summary-output",
                    "-",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("status"), "REAL_LOOP_MANIFEST_PREFLIGHT_NOT_REQUIRED")
            self.assertEqual(payload.get("counts", {}).get("total_intake_item_count"), 0)
            self.assertTrue(payload.get("launch_gate_policy_unchanged"))

    def test_missing_expected_manifest_is_pending_and_can_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            manifest_dir = root / "manifests"
            workpack_path = root / "workpack.json"
            report_path = root / "preflight.json"
            _write_json(workpack_path, _workpack(work_items=[_work_item(modality="audio")]))

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--workpack",
                    str(workpack_path),
                    "--manifest-dir",
                    str(manifest_dir),
                    "--output",
                    str(report_path),
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
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("status"), "REAL_LOOP_MANIFEST_PREFLIGHT_PENDING")
            self.assertEqual(payload.get("counts", {}).get("missing_item_count"), 1)
            self.assertEqual(payload.get("slot_readiness", {}).get("blocked_slot_count"), 1)
            self.assertEqual(payload.get("slot_readiness", {}).get("missing_slot_count"), 1)
            self.assertIn(
                "real-loop-001-audio.json",
                payload.get("slot_readiness", {}).get("missing_manifest_paths", [""])[0],
            )
            self.assertEqual(
                payload.get("modality_readiness", {}).get("missing_slot_count_by_modality", {}).get("audio"),
                1,
            )
            self.assertEqual(payload.get("operator_action_plan", {}).get("pending_action_count"), 1)
            self.assertEqual(
                payload.get("operator_action_plan", {}).get("next_actions", [{}])[0].get("action"),
                "drop_real_manifest",
            )
            self.assertIn("real_loop_manifests_missing", payload.get("warning_codes", []))
            self.assertIn("real_loop_slot_gap_action_plan_required", payload.get("warning_codes", []))

    def test_valid_real_manifest_is_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            manifest_dir = root / "manifests"
            workpack_path = root / "workpack.json"
            report_path = root / "preflight.json"
            _write_json(workpack_path, _workpack(work_items=[_work_item(modality="text")]))
            _write_json(
                manifest_dir / "real-loop-001-text.json",
                {
                    "manifest_id": "operator-real-text-001",
                    "manifest_version": "1.0",
                    "loops": [_valid_loop()],
                },
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--workpack",
                    str(workpack_path),
                    "--manifest-dir",
                    str(manifest_dir),
                    "--output",
                    str(report_path),
                    "--summary-output",
                    "-",
                    "--fail-on-invalid",
                    "--fail-on-pending",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("status"), "REAL_LOOP_MANIFEST_PREFLIGHT_READY")
            self.assertEqual(payload.get("counts", {}).get("valid_item_count"), 1)
            self.assertEqual(payload.get("slot_readiness", {}).get("ready_slot_count"), 1)
            self.assertEqual(payload.get("slot_readiness", {}).get("blocked_slot_count"), 0)
            self.assertEqual(
                payload.get("modality_readiness", {}).get("covered_target_launch_modalities"),
                ["text"],
            )
            self.assertEqual(payload.get("operator_action_plan", {}).get("status"), "ready_for_gl13")
            self.assertEqual(payload.get("operator_action_plan", {}).get("next_actions"), [])
            self.assertEqual(payload.get("items", [])[0].get("accepted_loop_ids"), ["real-text-001"])

    def test_fixture_manifest_is_invalid_and_can_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            manifest_dir = root / "manifests"
            workpack_path = root / "workpack.json"
            report_path = root / "preflight.json"
            fixture_loop = _valid_loop(loop_id="fixture-text-001", modality="text")
            fixture_loop["evidence_origin"] = "fixture"
            fixture_loop["launch_gate_eligible"] = False
            fixture_loop["source_system"] = "fixture-runner"
            _write_json(workpack_path, _workpack(work_items=[_work_item(modality="text")]))
            _write_json(
                manifest_dir / "real-loop-001-text.json",
                {
                    "manifest_id": "fixture-text-001",
                    "manifest_version": "1.0",
                    "loops": [fixture_loop],
                },
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--workpack",
                    str(workpack_path),
                    "--manifest-dir",
                    str(manifest_dir),
                    "--output",
                    str(report_path),
                    "--summary-output",
                    "-",
                    "--fail-on-invalid",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 1, completed.stderr + completed.stdout)
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("status"), "REAL_LOOP_MANIFEST_PREFLIGHT_INVALID")
            item = payload.get("items", [])[0]
            self.assertIn("fixture_or_simulated_loop_rejected", item.get("failure_codes", []))
            self.assertEqual(payload.get("slot_readiness", {}).get("invalid_slot_count"), 1)
            self.assertEqual(
                payload.get("operator_action_plan", {}).get("next_actions", [{}])[0].get("action"),
                "repair_real_manifest",
            )
            self.assertIn("real_loop_manifests_invalid", payload.get("warning_codes", []))

    def test_manifest_missing_backfill_linkage_is_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            manifest_dir = root / "manifests"
            workpack_path = root / "workpack.json"
            report_path = root / "preflight.json"
            loop = _valid_loop()
            loop.pop("backfill_slot_index", None)
            loop.pop("backfill_action_id", None)
            _write_json(workpack_path, _workpack(work_items=[_work_item(modality="text")]))
            _write_json(
                manifest_dir / "real-loop-001-text.json",
                {
                    "manifest_id": "operator-real-text-001",
                    "manifest_version": "1.0",
                    "loops": [loop],
                },
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--workpack",
                    str(workpack_path),
                    "--manifest-dir",
                    str(manifest_dir),
                    "--output",
                    str(report_path),
                    "--summary-output",
                    "-",
                    "--fail-on-invalid",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 1, completed.stderr + completed.stdout)
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            item = payload.get("items", [])[0]
            self.assertIn("backfill_slot_index_missing", item.get("failure_codes", []))
            self.assertIn("backfill_action_id_missing_or_placeholder", item.get("failure_codes", []))

    def test_manifest_backfill_linkage_must_match_workpack_slot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            manifest_dir = root / "manifests"
            workpack_path = root / "workpack.json"
            report_path = root / "preflight.json"
            loop = _valid_loop(slot_index=2, backfill_action_id="gl23-slot-002-text")
            _write_json(workpack_path, _workpack(work_items=[_work_item(slot_index=1, modality="text")]))
            _write_json(
                manifest_dir / "real-loop-001-text.json",
                {
                    "manifest_id": "operator-real-text-001",
                    "manifest_version": "1.0",
                    "loops": [loop],
                },
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--workpack",
                    str(workpack_path),
                    "--manifest-dir",
                    str(manifest_dir),
                    "--output",
                    str(report_path),
                    "--summary-output",
                    "-",
                    "--fail-on-invalid",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 1, completed.stderr + completed.stdout)
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            item = payload.get("items", [])[0]
            self.assertIn("backfill_slot_index_mismatch", item.get("failure_codes", []))
            self.assertIn("backfill_action_id_mismatch", item.get("failure_codes", []))


if __name__ == "__main__":
    unittest.main()
