from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "run_trial_metrics_collector.py"


def _build_loop(loop_id: str, modality: str) -> dict[str, object]:
    return {
        "loop_id": loop_id,
        "status": "complete",
        "modality": modality,
        "evidence_origin": "real",
        "launch_gate_eligible": True,
        "source_system": "pilot-ops",
        "source_reference": "ticket://%s" % loop_id,
        "collected_at_utc": "2026-05-26T00:00:00Z",
        "review_task_id": "review-%s" % loop_id,
        "reviewed_by": "reviewer-a",
        "reviewed_at_utc": "2026-05-26T00:05:00Z",
        "review_outcome": "approved",
        "revisions_before_approval": 1,
        "reviewer_edit_distance_pct": 20.0,
        "agent_smoke_result": "passed",
        "published_without_review": False,
        "critical_secret_or_pii_leak": False,
        "high_severity_incident": False,
        "latency_ms": 1000.0,
        "provider_failure_count": 0,
        "provider_call_count": 4,
        "retry_count": 1,
        "artifact_count": 8,
        "estimated_cost_usd": 0.4,
    }


def _manifest_payload() -> dict[str, object]:
    loops = [
        _build_loop("text-1", "text"),
        _build_loop("text-2", "text"),
        _build_loop("audio-1", "audio"),
        _build_loop("audio-2", "audio"),
        _build_loop("image-1", "image"),
        _build_loop("image-2", "image"),
        _build_loop("video-1", "video"),
        _build_loop("video-2", "video"),
        _build_loop("tabular-1", "tabular"),
        _build_loop("mixed-1", "mixed_corpus"),
    ]
    loops[0]["review_outcome"] = "rejected"
    loops[0]["revisions_before_approval"] = 2
    loops[0]["reviewer_edit_distance_pct"] = 29.0
    loops[1]["review_outcome"] = "rejected"
    loops[1]["revisions_before_approval"] = 2
    loops[1]["reviewer_edit_distance_pct"] = 27.0
    loops[6]["provider_failure_count"] = 1
    loops[7]["provider_failure_count"] = 1
    return {
        "manifest_id": "cbt-05-script-test",
        "manifest_version": "1.0",
        "release_gate": {
            "latest_release_decision": "GO",
        },
        "operator_signoff": {
            "cost_per_accepted_skill_accepted": True,
        },
        "loops": loops,
    }


class TrialMetricsCollectorScriptTests(unittest.TestCase):
    def test_script_smoke_emits_json_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            manifest_path = tmp_path / "trial-metrics-manifest.json"
            output_path = tmp_path / "trial-metrics-report.json"
            summary_path = tmp_path / "trial-metrics-summary.md"
            manifest_path.write_text(json.dumps(_manifest_payload(), ensure_ascii=False, indent=2), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--manifest",
                    str(manifest_path),
                    "--output",
                    str(output_path),
                    "--summary-output",
                    str(summary_path),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("Trial metrics loops=10 complete=10 modalities=6 status=pass blockers=no", completed.stdout)
            self.assertIn("Failed conditions: none", completed.stdout)

            report = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(report.get("overall_status"), "pass")
            self.assertFalse(report.get("ga_discussion_blocked"))
            summary = summary_path.read_text(encoding="utf-8")
            self.assertIn("Overall status: `pass`", summary)

    def test_script_fail_on_ga_blocker_returns_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            manifest_path = tmp_path / "trial-metrics-manifest.json"
            payload = _manifest_payload()
            payload["release_gate"] = {"latest_release_decision": "HOLD"}
            manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--manifest",
                    str(manifest_path),
                    "--output",
                    "-",
                    "--summary-output",
                    "-",
                    "--fail-on-ga-blocker",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1)
            self.assertIn("blockers=yes", completed.stdout)
            self.assertIn("release_run_go", completed.stdout)


if __name__ == "__main__":
    unittest.main()
