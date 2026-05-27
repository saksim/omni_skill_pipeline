from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.quality.trial_metrics import TrialMetricsCollector, render_trial_metrics_markdown_summary


def _build_loop(
    loop_id: str,
    modality: str,
    *,
    evidence_origin: str = "real",
    launch_gate_eligible: bool = True,
    launch_gate_ineligible_reason: str = "",
    review_outcome: str = "approved",
    revisions_before_approval: int = 1,
    reviewer_edit_distance_pct: float = 20.0,
    agent_smoke_result: str = "passed",
    provider_failure_count: int = 0,
    provider_call_count: int = 4,
    estimated_cost_usd: float = 0.4,
) -> dict[str, object]:
    loop = {
        "loop_id": loop_id,
        "status": "complete",
        "modality": modality,
        "evidence_origin": evidence_origin,
        "launch_gate_eligible": launch_gate_eligible,
        "launch_gate_ineligible_reason": launch_gate_ineligible_reason,
        "review_outcome": review_outcome,
        "revisions_before_approval": revisions_before_approval,
        "reviewer_edit_distance_pct": reviewer_edit_distance_pct,
        "agent_smoke_result": agent_smoke_result,
        "published_without_review": False,
        "critical_secret_or_pii_leak": False,
        "high_severity_incident": False,
        "latency_ms": 1000.0,
        "provider_failure_count": provider_failure_count,
        "provider_call_count": provider_call_count,
        "retry_count": 1,
        "artifact_count": 8,
        "estimated_cost_usd": estimated_cost_usd,
    }
    if evidence_origin == "real":
        loop["source_system"] = "pilot-ops"
        loop["source_reference"] = "ticket://%s" % loop_id
        loop["collected_at_utc"] = "2026-05-26T00:00:00Z"
        loop["review_task_id"] = "review-%s" % loop_id
        loop["reviewed_by"] = "reviewer-a"
        loop["reviewed_at_utc"] = "2026-05-26T00:05:00Z"
    return loop


def _passing_payload() -> dict[str, object]:
    loops = [
        _build_loop("text-1", "text"),
        _build_loop("text-2", "text", review_outcome="rejected", revisions_before_approval=2, reviewer_edit_distance_pct=28.0),
        _build_loop("audio-1", "audio"),
        _build_loop("audio-2", "audio"),
        _build_loop("image-1", "image"),
        _build_loop("image-2", "image"),
        _build_loop("video-1", "video"),
        _build_loop("video-2", "video"),
        _build_loop("tabular-1", "tabular"),
        _build_loop("mixed-1", "mixed_corpus", review_outcome="rejected", revisions_before_approval=2, reviewer_edit_distance_pct=27.0),
    ]
    loops[6]["provider_failure_count"] = 1
    loops[7]["provider_failure_count"] = 1
    return {
        "manifest_id": "cbt-05-test",
        "manifest_version": "1.0",
        "release_gate": {
            "latest_release_decision": "GO",
        },
        "operator_signoff": {
            "cost_per_accepted_skill_accepted": True,
        },
        "loops": loops,
    }


class TrialMetricsCollectorTests(unittest.TestCase):
    def test_collect_passes_when_success_criteria_are_met(self) -> None:
        collector = TrialMetricsCollector()
        report = collector.collect(_passing_payload())
        self.assertEqual(report.get("overall_status"), "pass")
        self.assertFalse(report.get("ga_discussion_blocked"))
        self.assertEqual(report.get("trial_metrics", {}).get("loop_count"), 10)
        self.assertEqual(report.get("trial_metrics", {}).get("complete_loop_count"), 10)
        self.assertGreaterEqual(len(report.get("trial_metrics", {}).get("complete_modalities", [])), 4)
        launch_gate_evidence = report.get("trial_metrics", {}).get("launch_gate_evidence", {})
        self.assertEqual(launch_gate_evidence.get("complete_loop_count"), 10)
        self.assertEqual(launch_gate_evidence.get("unlabeled_loop_count"), 0)
        self.assertEqual(launch_gate_evidence.get("real_evidence_missing_source_trace_count"), 0)
        self.assertEqual(launch_gate_evidence.get("real_evidence_missing_review_trace_count"), 0)
        self.assertEqual(launch_gate_evidence.get("evidence_origin_counts", {}).get("real"), 10)
        conditions = report.get("success_criteria", {}).get("conditions", [])
        self.assertEqual(len(conditions), 14)
        self.assertIn("review_outcome_counts", report.get("trial_metrics", {}))
        markdown = render_trial_metrics_markdown_summary(report)
        self.assertIn("Overall status: `pass`", markdown)
        self.assertIn("Real evidence missing review trace count: `0`", markdown)
        self.assertIn("All trial success criteria passed.", markdown)

    def test_collect_flags_ga_blockers_on_critical_failure(self) -> None:
        payload = _passing_payload()
        payload["release_gate"] = {"latest_release_decision": "HOLD"}
        payload["loops"][0]["published_without_review"] = True
        collector = TrialMetricsCollector()
        report = collector.collect(payload)
        self.assertEqual(report.get("overall_status"), "fail")
        self.assertTrue(report.get("ga_discussion_blocked"))
        failed_ids = {
            str(item.get("id", ""))
            for item in report.get("success_criteria", {}).get("failed_conditions", [])
        }
        self.assertIn("release_run_go", failed_ids)
        self.assertIn("no_unreviewed_publication", failed_ids)
        markdown = render_trial_metrics_markdown_summary(report)
        self.assertIn("GA discussion blocked: `yes`", markdown)
        self.assertIn("release_run_go", markdown)

    def test_collect_flags_launch_gate_coverage_when_fixture_or_synthetic_only(self) -> None:
        payload = _passing_payload()
        for loop in payload["loops"]:
            loop["evidence_origin"] = "fixture"
            loop["launch_gate_eligible"] = False
            loop["launch_gate_ineligible_reason"] = "fixture_evidence_not_launch_gate_eligible"
        collector = TrialMetricsCollector()
        report = collector.collect(payload)
        self.assertEqual(report.get("overall_status"), "fail")
        self.assertTrue(report.get("ga_discussion_blocked"))
        failed_ids = {
            str(item.get("id", ""))
            for item in report.get("success_criteria", {}).get("failed_conditions", [])
        }
        self.assertIn("launch_gate_eligible_loop_volume_and_modality_coverage", failed_ids)
        launch_gate_evidence = report.get("trial_metrics", {}).get("launch_gate_evidence", {})
        self.assertEqual(launch_gate_evidence.get("complete_loop_count"), 0)
        self.assertEqual(launch_gate_evidence.get("ineligible_loop_count"), 10)
        self.assertEqual(launch_gate_evidence.get("evidence_origin_counts", {}).get("fixture"), 10)

    def test_collect_rejects_non_real_loop_marked_launch_gate_eligible(self) -> None:
        payload = _passing_payload()
        payload["loops"][0]["evidence_origin"] = "synthetic"
        payload["loops"][0]["launch_gate_eligible"] = True
        collector = TrialMetricsCollector()
        with self.assertRaises(ValueError):
            collector.collect(payload)

    def test_collect_flags_real_evidence_missing_source_trace(self) -> None:
        payload = _passing_payload()
        payload["loops"][0].pop("source_system", None)
        payload["loops"][0].pop("source_reference", None)
        payload["loops"][0].pop("collected_at_utc", None)
        collector = TrialMetricsCollector()
        report = collector.collect(payload)
        self.assertEqual(report.get("overall_status"), "fail")
        self.assertTrue(report.get("ga_discussion_blocked"))
        launch_gate_evidence = report.get("trial_metrics", {}).get("launch_gate_evidence", {})
        self.assertEqual(launch_gate_evidence.get("real_evidence_missing_source_trace_count"), 1)
        failed_ids = {
            str(item.get("id", ""))
            for item in report.get("success_criteria", {}).get("failed_conditions", [])
        }
        self.assertIn("real_evidence_source_trace_complete", failed_ids)

    def test_collect_flags_real_evidence_missing_review_trace(self) -> None:
        payload = _passing_payload()
        payload["loops"][0].pop("review_task_id", None)
        payload["loops"][0].pop("reviewed_by", None)
        payload["loops"][0].pop("reviewed_at_utc", None)
        collector = TrialMetricsCollector()
        report = collector.collect(payload)
        self.assertEqual(report.get("overall_status"), "fail")
        self.assertTrue(report.get("ga_discussion_blocked"))
        launch_gate_evidence = report.get("trial_metrics", {}).get("launch_gate_evidence", {})
        self.assertEqual(launch_gate_evidence.get("real_evidence_missing_review_trace_count"), 1)
        failed_ids = {
            str(item.get("id", ""))
            for item in report.get("success_criteria", {}).get("failed_conditions", [])
        }
        self.assertIn("real_evidence_review_trace_complete", failed_ids)

    def test_collect_rejects_empty_loops(self) -> None:
        collector = TrialMetricsCollector()
        with self.assertRaises(ValueError):
            collector.collect(
                {
                    "manifest_id": "invalid",
                    "release_gate": {"latest_release_decision": "GO"},
                    "operator_signoff": {"cost_per_accepted_skill_accepted": True},
                    "loops": [],
                }
            )


if __name__ == "__main__":
    unittest.main()
