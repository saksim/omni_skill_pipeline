from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "run_real_trial_loop_collection.py"


def _loop_metrics(
    *,
    loop_id: str,
    modality: str,
    evidence_origin: str,
    launch_gate_eligible: bool,
    include_trace: bool = True,
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

            summary_text = summary_path.read_text(encoding="utf-8")
            self.assertIn("Program status: `COLLECTION_INCOMPLETE`", summary_text)

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


if __name__ == "__main__":
    unittest.main()
