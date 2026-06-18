from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "gl12_collect_loops.py"


def _loop_metrics(
    *,
    loop_id: str,
    modality: str,
    evidence_origin: str,
    launch_gate_eligible: bool,
    include_trace: bool = True,
    backfill_slot_index: int | None = None,
    backfill_action_id: str = "",
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "loop_id": loop_id,
        "status": "complete",
        "modality": modality,
        "evidence_origin": evidence_origin,
        "launch_gate_eligible": launch_gate_eligible,
        "review_outcome": "approved",
        "revisions_before_approval": 1,
        "reviewer_edit_distance_pct": 20.0,
        "agent_smoke_result": "passed",
        "published_without_review": False,
        "critical_secret_or_pii_leak": False,
        "high_severity_incident": False,
        "latency_ms": 800.0,
        "provider_failure_count": 0,
        "provider_call_count": 2,
        "retry_count": 0,
        "artifact_count": 8,
        "estimated_cost_usd": 0.25,
    }
    if not launch_gate_eligible:
        row["launch_gate_ineligible_reason"] = "fixture_evidence_not_launch_gate_eligible"
    if evidence_origin == "real" and include_trace:
        row["source_system"] = "pilot-ops"
        row["source_reference"] = "ticket://%s" % loop_id
        row["collected_at_utc"] = "2026-05-26T00:00:00Z"
        row["review_task_id"] = "review-%s" % loop_id
        row["reviewed_by"] = "reviewer-a"
        row["reviewed_at_utc"] = "2026-05-26T00:05:00Z"
    if backfill_slot_index is not None:
        row["backfill_slot_index"] = int(backfill_slot_index)
    if backfill_action_id:
        row["backfill_action_id"] = str(backfill_action_id)
    return row


def _run_report_payload(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "run_id": "gl12-script-test",
        "samples": [
            {
                "sample_id": str(row.get("loop_id", "")) or "sample",
                "loop_metrics": row,
            }
            for row in rows
        ],
    }


class RealTrialLoopCollectionScriptTests(unittest.TestCase):
    def test_fixture_only_input_stays_collection_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            run_report_path = tmp_path / "run-report.json"
            report_path = tmp_path / "collection-report.json"
            summary_path = tmp_path / "collection-summary.md"
            manifest_path = tmp_path / "trial-metrics-manifest.json"

            run_report_path.write_text(
                json.dumps(
                    _run_report_payload(
                        [
                            _loop_metrics(
                                loop_id="fixture-001",
                                modality="text",
                                evidence_origin="fixture",
                                launch_gate_eligible=False,
                            )
                        ]
                    ),
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--run-report",
                    str(run_report_path),
                    "--output",
                    str(report_path),
                    "--summary-output",
                    str(summary_path),
                    "--manifest-output",
                    str(manifest_path),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue(report_path.is_file())
            self.assertTrue(summary_path.is_file())
            self.assertTrue(manifest_path.is_file())

            report = json.loads(report_path.read_text(encoding="utf-8"))
            alignment = report.get("launch_gate_alignment", {})
            self.assertEqual(alignment.get("program_status"), "COLLECTION_INCOMPLETE")
            blockers = set(alignment.get("blockers", []))
            self.assertIn("real_loop_volume_below_threshold", blockers)
            self.assertIn("real_loop_modality_coverage_below_threshold", blockers)
            self.assertEqual(alignment.get("target_launch_modalities"), ["text", "audio", "image", "video"])
            self.assertEqual(alignment.get("covered_target_launch_modalities"), [])
            self.assertEqual(alignment.get("missing_target_launch_modalities"), ["text", "audio", "image", "video"])
            self.assertEqual(alignment.get("recommended_next_modalities"), ["text", "audio", "image", "video"])
            self.assertEqual(alignment.get("launch_gate_eligible_complete_loop_count_by_modality"), {})
            self.assertEqual(alignment.get("target_launch_modality_loop_counts"), {"text": 0, "audio": 0, "image": 0, "video": 0})
            self.assertEqual(alignment.get("recommended_backfill_slot_count"), 10)
            recommended_backfill_slots = alignment.get("recommended_backfill_slots", [])
            self.assertEqual(len(recommended_backfill_slots), 10)
            self.assertEqual(
                [item.get("required_modality") for item in recommended_backfill_slots[:4]],
                ["text", "audio", "image", "video"],
            )
            self.assertEqual(
                [item.get("reason") for item in recommended_backfill_slots[:4]],
                ["missing_target_launch_modality"] * 4,
            )
            self.assertEqual(
                [item.get("reason") for item in recommended_backfill_slots[4:]],
                ["loop_volume_gap_after_modality_coverage"] * 6,
            )

            summary_text = summary_path.read_text(encoding="utf-8")
            self.assertIn("Program status: `COLLECTION_INCOMPLETE`", summary_text)
            self.assertIn("Recommended backfill slots: `10`", summary_text)

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            loops = manifest.get("loops", [])
            self.assertEqual(len(loops), 1)
            self.assertEqual(loops[0].get("evidence_origin"), "fixture")

    def test_real_loops_meeting_thresholds_become_ready_for_beta_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            run_report_path = tmp_path / "run-report.json"
            report_path = tmp_path / "collection-report.json"

            rows = [
                _loop_metrics(
                    loop_id="real-text-001",
                    modality="text",
                    evidence_origin="real",
                    launch_gate_eligible=True,
                ),
                _loop_metrics(
                    loop_id="real-audio-001",
                    modality="audio",
                    evidence_origin="real",
                    launch_gate_eligible=True,
                ),
                _loop_metrics(
                    loop_id="real-image-001",
                    modality="image",
                    evidence_origin="real",
                    launch_gate_eligible=True,
                ),
            ]
            run_report_path.write_text(
                json.dumps(_run_report_payload(rows), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--run-report",
                    str(run_report_path),
                    "--output",
                    str(report_path),
                    "--summary-output",
                    "-",
                    "--manifest-output",
                    "-",
                    "--minimum-complete-loops",
                    "3",
                    "--minimum-modalities",
                    "3",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)

            report = json.loads(report_path.read_text(encoding="utf-8"))
            alignment = report.get("launch_gate_alignment", {})
            self.assertEqual(alignment.get("program_status"), "READY_FOR_CONTROLLED_BETA_EVIDENCE")
            self.assertEqual(alignment.get("blockers"), [])
            self.assertEqual(alignment.get("launch_gate_eligible_complete_loop_count"), 3)
            self.assertEqual(alignment.get("launch_gate_eligible_modality_count"), 3)
            self.assertEqual(
                alignment.get("launch_gate_eligible_complete_loop_count_by_modality"),
                {"text": 1, "audio": 1, "image": 1},
            )
            self.assertEqual(alignment.get("missing_target_launch_modalities"), ["video"])
            self.assertEqual(alignment.get("recommended_next_modalities"), [])
            self.assertEqual(alignment.get("recommended_backfill_slot_count"), 0)
            self.assertEqual(alignment.get("recommended_backfill_slots"), [])

    def test_real_loop_missing_trace_triggers_blocker_and_fail_on_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            run_report_path = tmp_path / "run-report.json"
            report_path = tmp_path / "collection-report.json"

            rows = [
                _loop_metrics(
                    loop_id="real-text-001",
                    modality="text",
                    evidence_origin="real",
                    launch_gate_eligible=True,
                    include_trace=False,
                )
            ]
            run_report_path.write_text(
                json.dumps(_run_report_payload(rows), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--run-report",
                    str(run_report_path),
                    "--output",
                    str(report_path),
                    "--summary-output",
                    "-",
                    "--manifest-output",
                    "-",
                    "--minimum-complete-loops",
                    "1",
                    "--minimum-modalities",
                    "1",
                    "--fail-on-blocker",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            blockers = set(report.get("launch_gate_alignment", {}).get("blockers", []))
            self.assertIn("real_loop_source_trace_incomplete", blockers)

    def test_real_loop_missing_review_trace_triggers_blocker_and_fail_on_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            run_report_path = tmp_path / "run-report.json"
            report_path = tmp_path / "collection-report.json"

            row = _loop_metrics(
                loop_id="real-text-001",
                modality="text",
                evidence_origin="real",
                launch_gate_eligible=True,
                include_trace=True,
            )
            row.pop("review_task_id", None)
            row.pop("reviewed_by", None)
            row.pop("reviewed_at_utc", None)
            run_report_path.write_text(
                json.dumps(_run_report_payload([row]), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--run-report",
                    str(run_report_path),
                    "--output",
                    str(report_path),
                    "--summary-output",
                    "-",
                    "--manifest-output",
                    "-",
                    "--minimum-complete-loops",
                    "1",
                    "--minimum-modalities",
                    "1",
                    "--fail-on-blocker",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            blockers = set(report.get("launch_gate_alignment", {}).get("blockers", []))
            self.assertIn("real_loop_review_trace_incomplete", blockers)

    def test_non_real_loop_cannot_be_launch_gate_eligible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            run_report_path = tmp_path / "run-report.json"

            rows = [
                _loop_metrics(
                    loop_id="bad-001",
                    modality="text",
                    evidence_origin="fixture",
                    launch_gate_eligible=True,
                )
            ]
            run_report_path.write_text(
                json.dumps(_run_report_payload(rows), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--run-report",
                    str(run_report_path),
                    "--output",
                    "-",
                    "--summary-output",
                    "-",
                    "--manifest-output",
                    "-",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertIn("cannot be launch_gate_eligible", completed.stderr)

    def test_loop_manifest_input_can_drive_ready_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            loop_manifest_path = tmp_path / "real-loop-manifest.json"
            report_path = tmp_path / "collection-report.json"

            rows = [
                _loop_metrics(
                    loop_id="real-text-001",
                    modality="text",
                    evidence_origin="real",
                    launch_gate_eligible=True,
                ),
                _loop_metrics(
                    loop_id="real-audio-001",
                    modality="audio",
                    evidence_origin="real",
                    launch_gate_eligible=True,
                ),
                _loop_metrics(
                    loop_id="real-image-001",
                    modality="image",
                    evidence_origin="real",
                    launch_gate_eligible=True,
                ),
                _loop_metrics(
                    loop_id="real-video-001",
                    modality="video",
                    evidence_origin="real",
                    launch_gate_eligible=True,
                ),
            ]
            loop_manifest_path.write_text(
                json.dumps(
                    {"manifest_id": "real-loop-manifest-test", "loops": rows},
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--loop-manifest",
                    str(loop_manifest_path),
                    "--output",
                    str(report_path),
                    "--summary-output",
                    "-",
                    "--manifest-output",
                    "-",
                    "--minimum-complete-loops",
                    "4",
                    "--minimum-modalities",
                    "4",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            alignment = report.get("launch_gate_alignment", {})
            self.assertEqual(alignment.get("program_status"), "READY_FOR_CONTROLLED_BETA_EVIDENCE")
            self.assertEqual(report.get("input_report_count"), 0)
            self.assertEqual(report.get("input_loop_manifest_count"), 1)

    def test_loop_manifest_dir_input_can_drive_ready_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            manifests_dir = tmp_path / "manifests"
            manifests_dir.mkdir(parents=True, exist_ok=True)
            report_path = tmp_path / "collection-report.json"

            manifest_a = manifests_dir / "manifest-a.json"
            manifest_b = manifests_dir / "manifest-b.json"
            _write_json_payload_a = {
                "manifest_id": "manifest-a",
                "loops": [
                    _loop_metrics(
                        loop_id="real-text-001",
                        modality="text",
                        evidence_origin="real",
                        launch_gate_eligible=True,
                    ),
                    _loop_metrics(
                        loop_id="real-audio-001",
                        modality="audio",
                        evidence_origin="real",
                        launch_gate_eligible=True,
                    ),
                ],
            }
            _write_json_payload_b = {
                "manifest_id": "manifest-b",
                "loops": [
                    _loop_metrics(
                        loop_id="real-image-001",
                        modality="image",
                        evidence_origin="real",
                        launch_gate_eligible=True,
                    ),
                    _loop_metrics(
                        loop_id="real-video-001",
                        modality="video",
                        evidence_origin="real",
                        launch_gate_eligible=True,
                    ),
                ],
            }
            manifest_a.write_text(json.dumps(_write_json_payload_a, ensure_ascii=False, indent=2), encoding="utf-8")
            manifest_b.write_text(json.dumps(_write_json_payload_b, ensure_ascii=False, indent=2), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--loop-manifest-dir",
                    str(manifests_dir),
                    "--loop-manifest-pattern",
                    "manifest-*.json",
                    "--output",
                    str(report_path),
                    "--summary-output",
                    "-",
                    "--manifest-output",
                    "-",
                    "--minimum-complete-loops",
                    "4",
                    "--minimum-modalities",
                    "4",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            alignment = report.get("launch_gate_alignment", {})
            self.assertEqual(alignment.get("program_status"), "READY_FOR_CONTROLLED_BETA_EVIDENCE")
            self.assertEqual(report.get("input_report_count"), 0)
            self.assertEqual(report.get("input_loop_manifest_count"), 2)
            self.assertEqual(report.get("input_loop_manifest_dir_count"), 1)
            self.assertEqual(alignment.get("missing_complete_loops_to_threshold"), 0)
            self.assertEqual(alignment.get("missing_modalities_to_threshold"), 0)
            self.assertEqual(alignment.get("missing_target_launch_modalities"), [])
            self.assertEqual(alignment.get("recommended_next_modalities"), [])
            self.assertEqual(
                alignment.get("launch_gate_eligible_complete_loop_count_by_modality"),
                {"audio": 1, "image": 1, "text": 1, "video": 1},
            )

    def test_empty_loop_manifest_dir_fails_without_default_fixture_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            manifests_dir = tmp_path / "manifests"
            manifests_dir.mkdir(parents=True, exist_ok=True)

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--loop-manifest-dir",
                    str(manifests_dir),
                    "--loop-manifest-pattern",
                    "*.json",
                    "--output",
                    "-",
                    "--summary-output",
                    "-",
                    "--manifest-output",
                    "-",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertIn("no loop manifest JSON files matched", completed.stderr)
            self.assertIn(str(manifests_dir.resolve()), completed.stderr)

    def test_loop_manifest_dir_skips_non_manifest_json_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            manifests_dir = tmp_path / "manifests"
            manifests_dir.mkdir(parents=True, exist_ok=True)
            report_path = tmp_path / "collection-report.json"

            valid_manifest_path = manifests_dir / "valid-manifest.json"
            non_manifest_path = manifests_dir / "not-a-loop-manifest.json"

            valid_manifest_payload = {
                "manifest_id": "valid-manifest",
                "loops": [
                    _loop_metrics(
                        loop_id="real-text-001",
                        modality="text",
                        evidence_origin="real",
                        launch_gate_eligible=True,
                    )
                ],
            }
            non_manifest_payload = {"schema_version": "auxiliary-json.v1", "notes": "not loop rows"}

            valid_manifest_path.write_text(
                json.dumps(valid_manifest_payload, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            non_manifest_path.write_text(
                json.dumps(non_manifest_payload, ensure_ascii=False, indent=2), encoding="utf-8"
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--loop-manifest-dir",
                    str(manifests_dir),
                    "--loop-manifest-pattern",
                    "*.json",
                    "--output",
                    str(report_path),
                    "--summary-output",
                    "-",
                    "--manifest-output",
                    "-",
                    "--minimum-complete-loops",
                    "1",
                    "--minimum-modalities",
                    "1",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report.get("input_loop_manifest_count"), 2)
            self.assertEqual(report.get("ingested_loop_manifest_count"), 1)
            self.assertEqual(report.get("skipped_non_loop_manifest_count"), 1)
            self.assertIn(str(non_manifest_path.resolve()), report.get("skipped_non_loop_manifest_paths", []))

    def test_strict_loop_manifest_contract_fails_on_non_manifest_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            manifests_dir = tmp_path / "manifests"
            manifests_dir.mkdir(parents=True, exist_ok=True)

            non_manifest_path = manifests_dir / "not-a-loop-manifest.json"
            non_manifest_path.write_text(
                json.dumps({"schema_version": "auxiliary-json.v1"}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--loop-manifest-dir",
                    str(manifests_dir),
                    "--loop-manifest-pattern",
                    "*.json",
                    "--strict-loop-manifest-contract",
                    "--output",
                    "-",
                    "--summary-output",
                    "-",
                    "--manifest-output",
                    "-",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertIn("Loop manifest loops must be a list", completed.stderr)

    def test_duplicate_loop_ids_keep_newer_review_trace_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            run_report_old = tmp_path / "run-report-old.json"
            run_report_new = tmp_path / "run-report-new.json"
            report_path = tmp_path / "collection-report.json"

            old_row = _loop_metrics(
                loop_id="real-text-dup-001",
                modality="text",
                evidence_origin="real",
                launch_gate_eligible=True,
            )
            old_row["reviewed_at_utc"] = "2026-05-26T00:05:00Z"
            old_row["collected_at_utc"] = "2026-05-26T00:00:00Z"
            old_row["source_reference"] = "ticket://old"
            run_report_old.write_text(
                json.dumps(_run_report_payload([old_row]), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            new_row = _loop_metrics(
                loop_id="real-text-dup-001",
                modality="text",
                evidence_origin="real",
                launch_gate_eligible=True,
            )
            new_row["reviewed_at_utc"] = "2026-05-27T00:05:00Z"
            new_row["collected_at_utc"] = "2026-05-27T00:00:00Z"
            new_row["source_reference"] = "ticket://new"
            run_report_new.write_text(
                json.dumps(_run_report_payload([new_row]), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--run-report",
                    str(run_report_old),
                    "--run-report",
                    str(run_report_new),
                    "--output",
                    str(report_path),
                    "--summary-output",
                    "-",
                    "--manifest-output",
                    "-",
                    "--minimum-complete-loops",
                    "1",
                    "--minimum-modalities",
                    "1",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report.get("duplicate_resolution_count"), 1)
            self.assertIn("real-text-dup-001", report.get("duplicate_loop_ids", []))
            resolution_records = report.get("duplicate_resolution_records", [])
            self.assertEqual(len(resolution_records), 1)
            self.assertEqual(
                resolution_records[0].get("resolution_reason"),
                "newer_reviewed_at_utc",
            )
            selected_loop_rows = report.get("collected_real_launch_gate_eligible_loops", [])
            self.assertEqual(len(selected_loop_rows), 1)
            self.assertEqual(selected_loop_rows[0].get("source_reference"), "ticket://new")

    def test_backfill_plan_output_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            run_report_path = tmp_path / "run-report.json"
            report_path = tmp_path / "collection-report.json"
            backfill_plan_path = tmp_path / "backfill-plan.json"

            run_report_path.write_text(
                json.dumps(
                    _run_report_payload(
                        [
                            _loop_metrics(
                                loop_id="fixture-001",
                                modality="text",
                                evidence_origin="fixture",
                                launch_gate_eligible=False,
                            )
                        ]
                    ),
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--run-report",
                    str(run_report_path),
                    "--output",
                    str(report_path),
                    "--summary-output",
                    "-",
                    "--manifest-output",
                    "-",
                    "--backfill-plan-output",
                    str(backfill_plan_path),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue(backfill_plan_path.is_file())
            backfill_plan = json.loads(backfill_plan_path.read_text(encoding="utf-8"))
            self.assertEqual(backfill_plan.get("schema_version"), "real_trial_loop_backfill_plan.v1")
            self.assertEqual(backfill_plan.get("plan_status"), "ACTION_REQUIRED")
            self.assertEqual(backfill_plan.get("recommended_backfill_slot_count"), 10)
            slots = backfill_plan.get("recommended_backfill_slots", [])
            self.assertEqual(len(slots), 10)
            self.assertEqual(slots[0].get("required_modality"), "text")
            self.assertEqual(slots[0].get("reason"), "missing_target_launch_modality")

    def test_real_loop_backfill_linkage_fields_are_collected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            run_report_path = tmp_path / "run-report.json"
            report_path = tmp_path / "collection-report.json"
            summary_path = tmp_path / "collection-summary.md"

            run_report_path.write_text(
                json.dumps(
                    _run_report_payload(
                        [
                            _loop_metrics(
                                loop_id="real-text-001",
                                modality="text",
                                evidence_origin="real",
                                launch_gate_eligible=True,
                                backfill_slot_index=1,
                                backfill_action_id="gl23-slot-001-text",
                            ),
                            _loop_metrics(
                                loop_id="real-audio-001",
                                modality="audio",
                                evidence_origin="real",
                                launch_gate_eligible=True,
                            ),
                        ]
                    ),
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--run-report",
                    str(run_report_path),
                    "--output",
                    str(report_path),
                    "--summary-output",
                    str(summary_path),
                    "--manifest-output",
                    "-",
                    "--minimum-complete-loops",
                    "2",
                    "--minimum-modalities",
                    "2",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            alignment = report.get("launch_gate_alignment", {})
            self.assertEqual(alignment.get("real_evidence_backfill_slot_linked_count"), 1)
            self.assertEqual(alignment.get("real_evidence_backfill_action_linked_count"), 1)
            self.assertEqual(alignment.get("real_evidence_backfill_linkage_complete_count"), 1)
            self.assertEqual(alignment.get("real_evidence_backfill_linkage_missing_count"), 1)
            collected = report.get("collected_real_launch_gate_eligible_loops", [])
            self.assertEqual(len(collected), 2)
            self.assertEqual(collected[0].get("backfill_slot_index"), 1)
            self.assertEqual(collected[0].get("backfill_action_id"), "gl23-slot-001-text")
            summary_text = summary_path.read_text(encoding="utf-8")
            self.assertIn("Real eligible loops with complete slot+action linkage: `1`", summary_text)

    def test_real_loop_template_placeholders_are_blocked_for_launch_gate_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            run_report_path = tmp_path / "run-report.json"
            report_path = tmp_path / "collection-report.json"
            summary_path = tmp_path / "collection-summary.md"

            placeholder_row = _loop_metrics(
                loop_id="real-text-template-001",
                modality="text",
                evidence_origin="real",
                launch_gate_eligible=True,
                include_trace=True,
            )
            placeholder_row["source_system"] = "TEMPLATE_REQUIRED_REPLACE_WITH_REAL_SOURCE_SYSTEM"
            placeholder_row["source_reference"] = "TEMPLATE_REQUIRED_REPLACE_WITH_REAL_SOURCE_REFERENCE"
            placeholder_row["collected_at_utc"] = "TEMPLATE_REQUIRED_REPLACE_WITH_UTC_TIMESTAMP"
            placeholder_row["review_task_id"] = "TEMPLATE_REQUIRED_REPLACE_WITH_REVIEW_TASK_ID"
            placeholder_row["reviewed_by"] = "TEMPLATE_REQUIRED_REPLACE_WITH_REVIEWER"
            placeholder_row["reviewed_at_utc"] = "TEMPLATE_REQUIRED_REPLACE_WITH_UTC_TIMESTAMP"

            run_report_path.write_text(
                json.dumps(_run_report_payload([placeholder_row]), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--run-report",
                    str(run_report_path),
                    "--output",
                    str(report_path),
                    "--summary-output",
                    str(summary_path),
                    "--manifest-output",
                    "-",
                    "--minimum-complete-loops",
                    "1",
                    "--minimum-modalities",
                    "1",
                    "--fail-on-blocker",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            alignment = report.get("launch_gate_alignment", {})
            blockers = set(alignment.get("blockers", []))
            self.assertIn("real_loop_template_placeholders_not_replaced", blockers)
            self.assertEqual(alignment.get("real_evidence_template_placeholder_loop_count"), 1)
            self.assertEqual(alignment.get("real_evidence_template_placeholder_field_count"), 6)
            placeholder_records = alignment.get("real_evidence_template_placeholder_records", [])
            self.assertEqual(len(placeholder_records), 1)
            self.assertEqual(placeholder_records[0].get("loop_id"), "real-text-template-001")
            self.assertEqual(
                sorted(placeholder_records[0].get("placeholder_fields", [])),
                [
                    "collected_at_utc",
                    "review_task_id",
                    "reviewed_at_utc",
                    "reviewed_by",
                    "source_reference",
                    "source_system",
                ],
            )
            self.assertEqual(alignment.get("launch_gate_eligible_complete_loop_count"), 0)
            self.assertEqual(report.get("collected_real_launch_gate_eligible_loops"), [])
            summary_text = summary_path.read_text(encoding="utf-8")
            self.assertIn("Real loops with template placeholders not replaced: `1`", summary_text)


if __name__ == "__main__":
    unittest.main()
