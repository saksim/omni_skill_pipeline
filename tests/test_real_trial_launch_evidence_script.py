from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "run_real_trial_launch_evidence.py"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _release_report(decision: str = "GO") -> dict[str, Any]:
    return {
        "schema_version": "test.release_switch.v1",
        "decision": decision,
        "gate_rows": [{"name": "strict_release_gate", "status": "pass"}],
    }


def _agent_smoke_report() -> dict[str, Any]:
    return {
        "schema_version": "test.agent_smoke.v1",
        "records": [
            {
                "skill_id": "skill-1",
                "agent": "codex",
                "status": "agent_smoke_passed",
                "metrics_agent_smoke_result": "passed",
            }
        ],
    }


def _doc_sync_report() -> dict[str, Any]:
    return {"generated_at_utc": "2026-05-26T00:00:00+00:00", "status": "pass", "failed_count": 0}


def _ops_readiness_report() -> dict[str, Any]:
    return {
        "schema_version": "operations_readiness.v1",
        "overall_status": "pass",
        "check_count": 1,
        "pass_count": 1,
        "fail_count": 0,
    }


def _loop_row(*, loop_id: str, modality: str, evidence_origin: str, launch_gate_eligible: bool) -> dict[str, Any]:
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
        "latency_ms": 700.0,
        "provider_failure_count": 0,
        "provider_call_count": 2,
        "retry_count": 0,
        "artifact_count": 6,
        "estimated_cost_usd": 0.3,
    }
    if evidence_origin == "real":
        row["source_system"] = "pilot-ops"
        row["source_reference"] = "ticket://%s" % loop_id
        row["collected_at_utc"] = "2026-05-26T00:00:00Z"
        row["review_task_id"] = "review-%s" % loop_id
        row["reviewed_by"] = "reviewer-a"
        row["reviewed_at_utc"] = "2026-05-26T00:05:00Z"
    elif not launch_gate_eligible:
        row["launch_gate_ineligible_reason"] = "%s_evidence_not_launch_gate_eligible" % evidence_origin
    return row


def _run_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "run_id": "gl13-script-test",
        "samples": [{"sample_id": str(item.get("loop_id", "")), "loop_metrics": item} for item in rows],
    }


class RealTrialLaunchEvidenceScriptTests(unittest.TestCase):
    def test_pipeline_produces_ready_for_controlled_beta_with_real_loop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            run_report = root / "run-report.json"
            release_report = root / "release-switch.json"
            current_status = root / "CURRENT_STATUS.md"
            agent_smoke = root / "agent-smoke.json"
            doc_sync = root / "doc-sync.json"
            ops_readiness = root / "ops-readiness.json"
            collection_report = root / "collection-report.json"
            collection_summary = root / "collection-summary.md"
            real_manifest = root / "real-manifest.json"
            trial_metrics_report = root / "trial-metrics-report.json"
            trial_metrics_summary = root / "trial-metrics-summary.md"
            launch_report = root / "launch-readiness-report.json"
            launch_summary = root / "launch-readiness-summary.md"
            evidence_pack = root / "real-trial-launch-evidence-pack.json"

            _write_json(
                run_report,
                _run_report(
                    [
                        _loop_row(
                            loop_id="real-text-001",
                            modality="text",
                            evidence_origin="real",
                            launch_gate_eligible=True,
                        )
                    ]
                ),
            )
            _write_json(release_report, _release_report("GO"))
            current_status.write_text("Release switch decision: `GO`\n", encoding="utf-8")
            _write_json(agent_smoke, _agent_smoke_report())
            _write_json(doc_sync, _doc_sync_report())
            _write_json(ops_readiness, _ops_readiness_report())

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--run-report",
                    str(run_report),
                    "--collection-report-output",
                    str(collection_report),
                    "--collection-summary-output",
                    str(collection_summary),
                    "--real-trial-manifest-output",
                    str(real_manifest),
                    "--trial-metrics-report-output",
                    str(trial_metrics_report),
                    "--trial-metrics-summary-output",
                    str(trial_metrics_summary),
                    "--launch-readiness-output",
                    str(launch_report),
                    "--launch-readiness-summary-output",
                    str(launch_summary),
                    "--evidence-pack-output",
                    str(evidence_pack),
                    "--backfill-execution-output",
                    str(root / "real-trial-backfill-execution-report.json"),
                    "--backfill-execution-summary-output",
                    str(root / "real-trial-backfill-execution-summary.md"),
                    "--backfill-intake-actions-output",
                    str(root / "real-trial-backfill-intake-actions-report.json"),
                    "--backfill-intake-actions-summary-output",
                    str(root / "real-trial-backfill-intake-actions-summary.md"),
                    "--backfill-submission-templates-output",
                    str(root / "real-trial-backfill-submission-templates-report.json"),
                    "--backfill-submission-templates-summary-output",
                    str(root / "real-trial-backfill-submission-templates-summary.md"),
                    "--backfill-submission-manifest-template-output",
                    str(root / "real-trial-backfill-submission-manifest.template.json"),
                    "--backfill-handoff-output",
                    str(root / "real-trial-backfill-handoff-report.json"),
                    "--backfill-handoff-summary-output",
                    str(root / "real-trial-backfill-handoff-summary.md"),
                    "--backfill-handoff-escalations-output",
                    str(root / "real-trial-backfill-handoff-escalations-report.json"),
                    "--backfill-handoff-escalations-summary-output",
                    str(root / "real-trial-backfill-handoff-escalations-summary.md"),
                    "--release-switch-report",
                    str(release_report),
                    "--current-status-doc",
                    str(current_status),
                    "--agent-smoke-report",
                    str(agent_smoke),
                    "--doc-sync-report",
                    str(doc_sync),
                    "--operations-readiness-report",
                    str(ops_readiness),
                    "--no-run-doc-sync",
                    "--minimum-complete-loops",
                    "1",
                    "--minimum-modalities",
                    "1",
                    "--max-evidence-age-hours",
                    "0",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            self.assertIn("decision=READY_FOR_CONTROLLED_BETA", completed.stdout)

            launch_payload = json.loads(launch_report.read_text(encoding="utf-8"))
            self.assertEqual(launch_payload.get("decision"), "READY_FOR_CONTROLLED_BETA")
            self.assertEqual(launch_payload.get("failed_checks"), [])
            self.assertTrue(evidence_pack.is_file())
            evidence_pack_payload = json.loads(evidence_pack.read_text(encoding="utf-8"))
            self.assertEqual(evidence_pack_payload.get("launch_decision"), "READY_FOR_CONTROLLED_BETA")
            self.assertTrue(evidence_pack_payload.get("ready_for_controlled_beta"))
            classification = evidence_pack_payload.get("evidence_classification", {})
            self.assertEqual(classification.get("launch_gate_eligible_complete_loop_count"), 1)
            self.assertEqual(
                classification.get("launch_gate_eligible_complete_modalities"),
                ["text"],
            )
            self.assertEqual(classification.get("target_launch_modalities"), ["text", "audio", "image", "video"])
            self.assertEqual(classification.get("covered_target_launch_modalities"), ["text"])
            self.assertEqual(classification.get("missing_target_launch_modalities"), ["audio", "image", "video"])
            self.assertEqual(classification.get("recommended_next_modalities"), [])
            self.assertEqual(
                classification.get("launch_gate_eligible_complete_loop_count_by_modality"),
                {"text": 1},
            )
            self.assertEqual(classification.get("target_launch_modality_loop_counts"), {"text": 1, "audio": 0, "image": 0, "video": 0})
            self.assertEqual(classification.get("recommended_backfill_slot_count"), 0)
            self.assertEqual(classification.get("recommended_backfill_slots"), [])
            self.assertEqual(classification.get("backfill_execution_status"), "NO_ACTION_REQUIRED")
            self.assertEqual(classification.get("backfill_execution_fulfilled_slot_count"), 0)
            self.assertEqual(classification.get("backfill_execution_remaining_slot_count"), 0)
            self.assertEqual(classification.get("backfill_execution_submission_backed_status"), "NO_ACTION_REQUIRED")
            self.assertEqual(classification.get("backfill_execution_submission_backed_fulfilled_slot_count"), 0)
            self.assertEqual(classification.get("backfill_execution_submission_backed_remaining_slot_count"), 0)
            self.assertEqual(classification.get("backfill_execution_fulfilled_without_submission_linkage_count"), 0)
            self.assertEqual(classification.get("backfill_execution_submission_linked_without_modality_delta_count"), 0)
            self.assertEqual(
                classification.get("backfill_execution_gained_target_launch_modality_loop_counts"),
                {"audio": 0, "image": 0, "text": 0, "video": 0},
            )
            self.assertEqual(classification.get("backfill_execution_submission_linked_slot_count"), 0)
            self.assertEqual(classification.get("backfill_execution_submission_slot_linked_count"), 0)
            self.assertEqual(classification.get("backfill_execution_submission_action_linked_count"), 0)
            self.assertEqual(classification.get("backfill_execution_unmatched_submission_linkage_count"), 0)
            self.assertEqual(classification.get("backfill_execution_submission_linkage_records"), [])
            self.assertEqual(classification.get("backfill_execution_unmatched_submission_linkages"), [])
            self.assertEqual(classification.get("backfill_intake_status"), "NO_ACTION_REQUIRED")
            self.assertEqual(classification.get("backfill_intake_total_action_count"), 0)
            self.assertEqual(classification.get("backfill_intake_pending_action_count"), 0)
            self.assertEqual(classification.get("backfill_intake_closed_action_count"), 0)
            self.assertEqual(classification.get("backfill_intake_owner"), "controlled-beta-ops")
            self.assertEqual(classification.get("backfill_submission_template_status"), "NO_PENDING_ACTIONS")
            self.assertEqual(classification.get("backfill_submission_template_total_action_count"), 0)
            self.assertEqual(classification.get("backfill_submission_template_pending_action_count"), 0)
            self.assertEqual(classification.get("backfill_submission_template_generated_count"), 0)
            self.assertEqual(classification.get("backfill_submission_template_missing_count"), 0)
            self.assertEqual(classification.get("backfill_submission_template_owner"), "controlled-beta-ops")
            self.assertEqual(classification.get("backfill_submission_template_missing_actions"), [])
            self.assertEqual(classification.get("backfill_handoff_status"), "HANDOFF_NOT_REQUIRED")
            self.assertEqual(classification.get("backfill_handoff_total_queue_item_count"), 0)
            self.assertEqual(classification.get("backfill_handoff_open_queue_item_count"), 0)
            self.assertEqual(classification.get("backfill_handoff_submission_linked_pending_ack_count"), 0)
            self.assertEqual(classification.get("backfill_handoff_closure_acknowledged_count"), 0)
            self.assertEqual(classification.get("backfill_handoff_owner"), "controlled-beta-ops")
            self.assertEqual(
                classification.get("backfill_handoff_submission_linkage_strategy_counts"),
                {
                    "action_id_and_slot_index": 0,
                    "action_id_only": 0,
                    "slot_index_only": 0,
                    "modality_fallback": 0,
                    "none": 0,
                },
            )
            self.assertEqual(classification.get("backfill_handoff_submission_unlinked_count"), 1)
            unlinked_records = classification.get("backfill_handoff_submission_unlinked_records", [])
            self.assertEqual(len(unlinked_records), 1)
            self.assertEqual(unlinked_records[0].get("loop_id"), "real-text-001")
            self.assertEqual(classification.get("backfill_handoff_acknowledgement_input_count"), 0)
            self.assertEqual(classification.get("backfill_handoff_acknowledgement_valid_count"), 0)
            self.assertEqual(classification.get("backfill_handoff_acknowledgement_invalid_count"), 0)
            self.assertEqual(classification.get("backfill_handoff_acknowledgement_invalid_records"), [])
            self.assertEqual(classification.get("backfill_handoff_acknowledgement_sla_status"), "ACK_SLA_NOT_REQUIRED")
            self.assertEqual(classification.get("backfill_handoff_acknowledgement_sla_hours"), 24.0)
            self.assertEqual(classification.get("backfill_handoff_acknowledgement_overdue_hours"), 72.0)
            self.assertEqual(classification.get("backfill_handoff_acknowledgement_within_sla_count"), 0)
            self.assertEqual(classification.get("backfill_handoff_acknowledgement_sla_breached_count"), 0)
            self.assertEqual(classification.get("backfill_handoff_acknowledgement_overdue_count"), 0)
            self.assertEqual(classification.get("backfill_handoff_acknowledgement_tracking_incomplete_count"), 0)
            self.assertEqual(classification.get("backfill_handoff_acknowledgement_sla_breached_queue_items"), [])
            self.assertEqual(classification.get("backfill_handoff_acknowledgement_overdue_queue_items"), [])
            self.assertEqual(classification.get("backfill_handoff_acknowledgement_tracking_incomplete_queue_items"), [])
            self.assertEqual(classification.get("backfill_handoff_escalation_status"), "ESCALATION_NOT_REQUIRED")
            self.assertEqual(classification.get("backfill_handoff_escalation_owner"), "controlled-beta-ops")
            self.assertEqual(classification.get("backfill_handoff_escalation_total_item_count"), 0)
            self.assertEqual(classification.get("backfill_handoff_escalation_sla_breached_item_count"), 0)
            self.assertEqual(classification.get("backfill_handoff_escalation_overdue_item_count"), 0)
            self.assertEqual(classification.get("backfill_handoff_escalation_tracking_incomplete_item_count"), 0)
            self.assertEqual(classification.get("backfill_handoff_escalation_sla_breached_items"), [])
            self.assertEqual(classification.get("backfill_handoff_escalation_overdue_items"), [])
            self.assertEqual(classification.get("backfill_handoff_escalation_tracking_incomplete_items"), [])
            self.assertEqual(evidence_pack_payload.get("stage"), "controlled_external_beta")
            self.assertEqual(evidence_pack_payload.get("gate_summary", {}).get("failed_checks"), [])

    def test_pipeline_fail_on_hold_returns_nonzero_for_fixture_only_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            run_report = root / "run-report.json"
            release_report = root / "release-switch.json"
            current_status = root / "CURRENT_STATUS.md"
            agent_smoke = root / "agent-smoke.json"
            doc_sync = root / "doc-sync.json"
            ops_readiness = root / "ops-readiness.json"
            launch_report = root / "launch-readiness-report.json"
            evidence_pack = root / "real-trial-launch-evidence-pack.json"

            _write_json(
                run_report,
                _run_report(
                    [
                        _loop_row(
                            loop_id="fixture-text-001",
                            modality="text",
                            evidence_origin="fixture",
                            launch_gate_eligible=False,
                        )
                    ]
                ),
            )
            _write_json(release_report, _release_report("GO"))
            current_status.write_text("Release switch decision: `GO`\n", encoding="utf-8")
            _write_json(agent_smoke, _agent_smoke_report())
            _write_json(doc_sync, _doc_sync_report())
            _write_json(ops_readiness, _ops_readiness_report())

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--run-report",
                    str(run_report),
                    "--collection-report-output",
                    str(root / "collection-report.json"),
                    "--collection-summary-output",
                    str(root / "collection-summary.md"),
                    "--real-trial-manifest-output",
                    str(root / "real-manifest.json"),
                    "--trial-metrics-report-output",
                    str(root / "trial-metrics-report.json"),
                    "--trial-metrics-summary-output",
                    str(root / "trial-metrics-summary.md"),
                    "--launch-readiness-output",
                    str(launch_report),
                    "--launch-readiness-summary-output",
                    str(root / "launch-readiness-summary.md"),
                    "--evidence-pack-output",
                    str(evidence_pack),
                    "--backfill-execution-output",
                    str(root / "real-trial-backfill-execution-report.json"),
                    "--backfill-execution-summary-output",
                    str(root / "real-trial-backfill-execution-summary.md"),
                    "--backfill-intake-actions-output",
                    str(root / "real-trial-backfill-intake-actions-report.json"),
                    "--backfill-intake-actions-summary-output",
                    str(root / "real-trial-backfill-intake-actions-summary.md"),
                    "--backfill-submission-templates-output",
                    str(root / "real-trial-backfill-submission-templates-report.json"),
                    "--backfill-submission-templates-summary-output",
                    str(root / "real-trial-backfill-submission-templates-summary.md"),
                    "--backfill-submission-manifest-template-output",
                    str(root / "real-trial-backfill-submission-manifest.template.json"),
                    "--backfill-handoff-output",
                    str(root / "real-trial-backfill-handoff-report.json"),
                    "--backfill-handoff-summary-output",
                    str(root / "real-trial-backfill-handoff-summary.md"),
                    "--backfill-handoff-escalations-output",
                    str(root / "real-trial-backfill-handoff-escalations-report.json"),
                    "--backfill-handoff-escalations-summary-output",
                    str(root / "real-trial-backfill-handoff-escalations-summary.md"),
                    "--release-switch-report",
                    str(release_report),
                    "--current-status-doc",
                    str(current_status),
                    "--agent-smoke-report",
                    str(agent_smoke),
                    "--doc-sync-report",
                    str(doc_sync),
                    "--operations-readiness-report",
                    str(ops_readiness),
                    "--no-run-doc-sync",
                    "--max-evidence-age-hours",
                    "0",
                    "--fail-on-hold",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr + completed.stdout)
            self.assertIn("decision=HOLD", completed.stdout)
            self.assertIn("trial_loop_volume_and_modality_coverage", completed.stdout)

            launch_payload = json.loads(launch_report.read_text(encoding="utf-8"))
            self.assertEqual(launch_payload.get("decision"), "HOLD")
            evidence_pack_payload = json.loads(evidence_pack.read_text(encoding="utf-8"))
            self.assertEqual(evidence_pack_payload.get("launch_decision"), "HOLD")
            self.assertFalse(evidence_pack_payload.get("ready_for_controlled_beta"))
            failed_checks = evidence_pack_payload.get("gate_summary", {}).get("failed_checks", [])
            self.assertIn("trial_loop_volume_and_modality_coverage", failed_checks)
            classification = evidence_pack_payload.get("evidence_classification", {})
            self.assertEqual(classification.get("recommended_backfill_slot_count"), 10)
            slots = classification.get("recommended_backfill_slots", [])
            self.assertEqual(len(slots), 10)
            self.assertEqual(slots[0].get("required_modality"), "text")
            self.assertEqual(slots[0].get("reason"), "missing_target_launch_modality")
            self.assertEqual(classification.get("backfill_execution_status"), "BACKFILL_IN_PROGRESS")
            self.assertEqual(classification.get("backfill_execution_fulfilled_slot_count"), 0)
            self.assertEqual(classification.get("backfill_execution_remaining_slot_count"), 10)
            self.assertEqual(classification.get("backfill_execution_submission_backed_status"), "SUBMISSION_BACKED_IN_PROGRESS")
            self.assertEqual(classification.get("backfill_execution_submission_backed_fulfilled_slot_count"), 0)
            self.assertEqual(classification.get("backfill_execution_submission_backed_remaining_slot_count"), 10)
            self.assertEqual(classification.get("backfill_execution_fulfilled_without_submission_linkage_count"), 0)
            self.assertEqual(classification.get("backfill_execution_submission_linked_without_modality_delta_count"), 0)
            self.assertEqual(
                classification.get("backfill_execution_gained_target_launch_modality_loop_counts"),
                {"audio": 0, "image": 0, "text": 0, "video": 0},
            )
            self.assertEqual(classification.get("backfill_execution_submission_linked_slot_count"), 0)
            self.assertEqual(classification.get("backfill_execution_submission_slot_linked_count"), 0)
            self.assertEqual(classification.get("backfill_execution_submission_action_linked_count"), 0)
            self.assertEqual(classification.get("backfill_execution_unmatched_submission_linkage_count"), 0)
            self.assertEqual(classification.get("backfill_execution_submission_linkage_records"), [])
            self.assertEqual(classification.get("backfill_execution_unmatched_submission_linkages"), [])
            self.assertEqual(classification.get("backfill_intake_status"), "ACTIONS_PENDING")
            self.assertEqual(classification.get("backfill_intake_total_action_count"), 10)
            self.assertEqual(classification.get("backfill_intake_pending_action_count"), 10)
            self.assertEqual(classification.get("backfill_intake_closed_action_count"), 0)
            self.assertEqual(classification.get("backfill_intake_owner"), "controlled-beta-ops")
            self.assertEqual(classification.get("backfill_submission_template_status"), "TEMPLATES_READY")
            self.assertEqual(classification.get("backfill_submission_template_total_action_count"), 10)
            self.assertEqual(classification.get("backfill_submission_template_pending_action_count"), 10)
            self.assertEqual(classification.get("backfill_submission_template_generated_count"), 10)
            self.assertEqual(classification.get("backfill_submission_template_missing_count"), 0)
            self.assertEqual(classification.get("backfill_submission_template_owner"), "controlled-beta-ops")
            self.assertEqual(classification.get("backfill_submission_template_missing_actions"), [])
            self.assertEqual(classification.get("backfill_handoff_status"), "HANDOFF_ACTIONS_PENDING")
            self.assertEqual(classification.get("backfill_handoff_total_queue_item_count"), 10)
            self.assertEqual(classification.get("backfill_handoff_open_queue_item_count"), 10)
            self.assertEqual(classification.get("backfill_handoff_submission_linked_pending_ack_count"), 0)
            self.assertEqual(classification.get("backfill_handoff_closure_acknowledged_count"), 0)
            self.assertEqual(classification.get("backfill_handoff_owner"), "controlled-beta-ops")
            self.assertEqual(
                classification.get("backfill_handoff_submission_linkage_strategy_counts"),
                {
                    "action_id_and_slot_index": 0,
                    "action_id_only": 0,
                    "slot_index_only": 0,
                    "modality_fallback": 0,
                    "none": 10,
                },
            )
            self.assertEqual(classification.get("backfill_handoff_submission_unlinked_count"), 0)
            self.assertEqual(classification.get("backfill_handoff_submission_unlinked_records"), [])
            self.assertEqual(classification.get("backfill_handoff_acknowledgement_input_count"), 0)
            self.assertEqual(classification.get("backfill_handoff_acknowledgement_valid_count"), 0)
            self.assertEqual(classification.get("backfill_handoff_acknowledgement_invalid_count"), 0)
            self.assertEqual(classification.get("backfill_handoff_acknowledgement_invalid_records"), [])
            self.assertEqual(classification.get("backfill_handoff_acknowledgement_sla_status"), "ACK_SLA_NOT_REQUIRED")
            self.assertEqual(classification.get("backfill_handoff_acknowledgement_sla_hours"), 24.0)
            self.assertEqual(classification.get("backfill_handoff_acknowledgement_overdue_hours"), 72.0)
            self.assertEqual(classification.get("backfill_handoff_acknowledgement_within_sla_count"), 0)
            self.assertEqual(classification.get("backfill_handoff_acknowledgement_sla_breached_count"), 0)
            self.assertEqual(classification.get("backfill_handoff_acknowledgement_overdue_count"), 0)
            self.assertEqual(classification.get("backfill_handoff_acknowledgement_tracking_incomplete_count"), 0)
            self.assertEqual(classification.get("backfill_handoff_acknowledgement_sla_breached_queue_items"), [])
            self.assertEqual(classification.get("backfill_handoff_acknowledgement_overdue_queue_items"), [])
            self.assertEqual(classification.get("backfill_handoff_escalation_status"), "ESCALATION_NOT_REQUIRED")
            self.assertEqual(classification.get("backfill_handoff_escalation_total_item_count"), 0)
            self.assertEqual(classification.get("backfill_handoff_acknowledgement_tracking_incomplete_queue_items"), [])

    def test_pipeline_accepts_loop_manifest_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            loop_manifest = root / "real-loop-manifest.json"
            release_report = root / "release-switch.json"
            current_status = root / "CURRENT_STATUS.md"
            agent_smoke = root / "agent-smoke.json"
            doc_sync = root / "doc-sync.json"
            ops_readiness = root / "ops-readiness.json"
            launch_report = root / "launch-readiness-report.json"
            evidence_pack = root / "real-trial-launch-evidence-pack.json"

            _write_json(
                loop_manifest,
                {
                    "manifest_id": "gl15-real-loop-manifest-test",
                    "loops": [
                        _loop_row(
                            loop_id="real-text-001",
                            modality="text",
                            evidence_origin="real",
                            launch_gate_eligible=True,
                        ),
                        _loop_row(
                            loop_id="real-audio-001",
                            modality="audio",
                            evidence_origin="real",
                            launch_gate_eligible=True,
                        ),
                        _loop_row(
                            loop_id="real-image-001",
                            modality="image",
                            evidence_origin="real",
                            launch_gate_eligible=True,
                        ),
                        _loop_row(
                            loop_id="real-video-001",
                            modality="video",
                            evidence_origin="real",
                            launch_gate_eligible=True,
                        ),
                    ],
                },
            )
            _write_json(release_report, _release_report("GO"))
            current_status.write_text("Release switch decision: `GO`\n", encoding="utf-8")
            _write_json(agent_smoke, _agent_smoke_report())
            _write_json(doc_sync, _doc_sync_report())
            _write_json(ops_readiness, _ops_readiness_report())

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--loop-manifest",
                    str(loop_manifest),
                    "--collection-report-output",
                    str(root / "collection-report.json"),
                    "--collection-summary-output",
                    str(root / "collection-summary.md"),
                    "--real-trial-manifest-output",
                    str(root / "real-manifest.json"),
                    "--trial-metrics-report-output",
                    str(root / "trial-metrics-report.json"),
                    "--trial-metrics-summary-output",
                    str(root / "trial-metrics-summary.md"),
                    "--launch-readiness-output",
                    str(launch_report),
                    "--launch-readiness-summary-output",
                    str(root / "launch-readiness-summary.md"),
                    "--evidence-pack-output",
                    str(evidence_pack),
                    "--backfill-execution-output",
                    str(root / "real-trial-backfill-execution-report.json"),
                    "--backfill-execution-summary-output",
                    str(root / "real-trial-backfill-execution-summary.md"),
                    "--backfill-intake-actions-output",
                    str(root / "real-trial-backfill-intake-actions-report.json"),
                    "--backfill-intake-actions-summary-output",
                    str(root / "real-trial-backfill-intake-actions-summary.md"),
                    "--backfill-submission-templates-output",
                    str(root / "real-trial-backfill-submission-templates-report.json"),
                    "--backfill-submission-templates-summary-output",
                    str(root / "real-trial-backfill-submission-templates-summary.md"),
                    "--backfill-submission-manifest-template-output",
                    str(root / "real-trial-backfill-submission-manifest.template.json"),
                    "--backfill-handoff-output",
                    str(root / "real-trial-backfill-handoff-report.json"),
                    "--backfill-handoff-summary-output",
                    str(root / "real-trial-backfill-handoff-summary.md"),
                    "--backfill-handoff-escalations-output",
                    str(root / "real-trial-backfill-handoff-escalations-report.json"),
                    "--backfill-handoff-escalations-summary-output",
                    str(root / "real-trial-backfill-handoff-escalations-summary.md"),
                    "--release-switch-report",
                    str(release_report),
                    "--current-status-doc",
                    str(current_status),
                    "--agent-smoke-report",
                    str(agent_smoke),
                    "--doc-sync-report",
                    str(doc_sync),
                    "--operations-readiness-report",
                    str(ops_readiness),
                    "--no-run-doc-sync",
                    "--minimum-complete-loops",
                    "4",
                    "--minimum-modalities",
                    "4",
                    "--max-evidence-age-hours",
                    "0",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            self.assertIn("decision=READY_FOR_CONTROLLED_BETA", completed.stdout)
            launch_payload = json.loads(launch_report.read_text(encoding="utf-8"))
            self.assertEqual(launch_payload.get("decision"), "READY_FOR_CONTROLLED_BETA")
            evidence_pack_payload = json.loads(evidence_pack.read_text(encoding="utf-8"))
            self.assertEqual(evidence_pack_payload.get("launch_decision"), "READY_FOR_CONTROLLED_BETA")
            self.assertEqual(
                evidence_pack_payload.get("input_sources", {}).get("input_loop_manifest_count"),
                1,
            )

    def test_pipeline_accepts_loop_manifest_dir_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            manifests_dir = root / "real-loop-manifests"
            manifests_dir.mkdir(parents=True, exist_ok=True)
            release_report = root / "release-switch.json"
            current_status = root / "CURRENT_STATUS.md"
            agent_smoke = root / "agent-smoke.json"
            doc_sync = root / "doc-sync.json"
            ops_readiness = root / "ops-readiness.json"
            launch_report = root / "launch-readiness-report.json"
            evidence_pack = root / "real-trial-launch-evidence-pack.json"

            _write_json(
                manifests_dir / "manifest-a.json",
                {
                    "manifest_id": "gl17-manifest-a",
                    "loops": [
                        _loop_row(
                            loop_id="real-text-001",
                            modality="text",
                            evidence_origin="real",
                            launch_gate_eligible=True,
                        ),
                        _loop_row(
                            loop_id="real-audio-001",
                            modality="audio",
                            evidence_origin="real",
                            launch_gate_eligible=True,
                        ),
                    ],
                },
            )
            _write_json(
                manifests_dir / "manifest-b.json",
                {
                    "manifest_id": "gl17-manifest-b",
                    "loops": [
                        _loop_row(
                            loop_id="real-image-001",
                            modality="image",
                            evidence_origin="real",
                            launch_gate_eligible=True,
                        ),
                        _loop_row(
                            loop_id="real-video-001",
                            modality="video",
                            evidence_origin="real",
                            launch_gate_eligible=True,
                        ),
                    ],
                },
            )
            _write_json(release_report, _release_report("GO"))
            current_status.write_text("Release switch decision: `GO`\n", encoding="utf-8")
            _write_json(agent_smoke, _agent_smoke_report())
            _write_json(doc_sync, _doc_sync_report())
            _write_json(ops_readiness, _ops_readiness_report())

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--loop-manifest-dir",
                    str(manifests_dir),
                    "--loop-manifest-pattern",
                    "manifest-*.json",
                    "--collection-report-output",
                    str(root / "collection-report.json"),
                    "--collection-summary-output",
                    str(root / "collection-summary.md"),
                    "--real-trial-manifest-output",
                    str(root / "real-manifest.json"),
                    "--trial-metrics-report-output",
                    str(root / "trial-metrics-report.json"),
                    "--trial-metrics-summary-output",
                    str(root / "trial-metrics-summary.md"),
                    "--launch-readiness-output",
                    str(launch_report),
                    "--launch-readiness-summary-output",
                    str(root / "launch-readiness-summary.md"),
                    "--evidence-pack-output",
                    str(evidence_pack),
                    "--backfill-execution-output",
                    str(root / "real-trial-backfill-execution-report.json"),
                    "--backfill-execution-summary-output",
                    str(root / "real-trial-backfill-execution-summary.md"),
                    "--backfill-intake-actions-output",
                    str(root / "real-trial-backfill-intake-actions-report.json"),
                    "--backfill-intake-actions-summary-output",
                    str(root / "real-trial-backfill-intake-actions-summary.md"),
                    "--backfill-submission-templates-output",
                    str(root / "real-trial-backfill-submission-templates-report.json"),
                    "--backfill-submission-templates-summary-output",
                    str(root / "real-trial-backfill-submission-templates-summary.md"),
                    "--backfill-submission-manifest-template-output",
                    str(root / "real-trial-backfill-submission-manifest.template.json"),
                    "--backfill-handoff-output",
                    str(root / "real-trial-backfill-handoff-report.json"),
                    "--backfill-handoff-summary-output",
                    str(root / "real-trial-backfill-handoff-summary.md"),
                    "--backfill-handoff-escalations-output",
                    str(root / "real-trial-backfill-handoff-escalations-report.json"),
                    "--backfill-handoff-escalations-summary-output",
                    str(root / "real-trial-backfill-handoff-escalations-summary.md"),
                    "--release-switch-report",
                    str(release_report),
                    "--current-status-doc",
                    str(current_status),
                    "--agent-smoke-report",
                    str(agent_smoke),
                    "--doc-sync-report",
                    str(doc_sync),
                    "--operations-readiness-report",
                    str(ops_readiness),
                    "--no-run-doc-sync",
                    "--minimum-complete-loops",
                    "4",
                    "--minimum-modalities",
                    "4",
                    "--max-evidence-age-hours",
                    "0",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            self.assertIn("decision=READY_FOR_CONTROLLED_BETA", completed.stdout)
            evidence_pack_payload = json.loads(evidence_pack.read_text(encoding="utf-8"))
            input_sources = evidence_pack_payload.get("input_sources", {})
            self.assertEqual(input_sources.get("input_loop_manifest_count"), 2)
            self.assertEqual(input_sources.get("input_loop_manifest_dir_count"), 1)
            self.assertEqual(len(input_sources.get("loop_manifest_dirs", [])), 1)
            classification = evidence_pack_payload.get("evidence_classification", {})
            self.assertEqual(classification.get("missing_complete_loops_to_threshold"), 0)
            self.assertEqual(classification.get("missing_modalities_to_threshold"), 0)
            self.assertEqual(classification.get("missing_target_launch_modalities"), [])
            self.assertEqual(classification.get("recommended_next_modalities"), [])
            self.assertEqual(
                classification.get("launch_gate_eligible_complete_loop_count_by_modality"),
                {"audio": 1, "image": 1, "text": 1, "video": 1},
            )

    def test_pipeline_empty_loop_manifest_dir_fails_without_default_fixture_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            manifests_dir = root / "real-loop-manifests"
            manifests_dir.mkdir(parents=True, exist_ok=True)
            evidence_pack = root / "real-trial-launch-evidence-pack.json"

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--loop-manifest-dir",
                    str(manifests_dir),
                    "--loop-manifest-pattern",
                    "*.json",
                    "--collection-report-output",
                    str(root / "collection-report.json"),
                    "--collection-summary-output",
                    str(root / "collection-summary.md"),
                    "--real-trial-manifest-output",
                    str(root / "real-manifest.json"),
                    "--trial-metrics-report-output",
                    str(root / "trial-metrics-report.json"),
                    "--trial-metrics-summary-output",
                    str(root / "trial-metrics-summary.md"),
                    "--launch-readiness-output",
                    str(root / "launch-readiness-report.json"),
                    "--launch-readiness-summary-output",
                    str(root / "launch-readiness-summary.md"),
                    "--evidence-pack-output",
                    str(evidence_pack),
                    "--max-evidence-age-hours",
                    "0",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertIn("no loop manifest JSON files matched", completed.stderr)
            self.assertIn(str(manifests_dir.resolve()), completed.stderr)
            self.assertFalse(evidence_pack.exists())

    def test_pipeline_manifest_dir_skips_non_manifest_json_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            manifests_dir = root / "real-loop-manifests"
            manifests_dir.mkdir(parents=True, exist_ok=True)
            release_report = root / "release-switch.json"
            current_status = root / "CURRENT_STATUS.md"
            agent_smoke = root / "agent-smoke.json"
            doc_sync = root / "doc-sync.json"
            ops_readiness = root / "ops-readiness.json"
            launch_report = root / "launch-readiness-report.json"
            evidence_pack = root / "real-trial-launch-evidence-pack.json"

            _write_json(
                manifests_dir / "manifest-a.json",
                {
                    "manifest_id": "gl18-manifest-a",
                    "loops": [
                        _loop_row(
                            loop_id="real-text-001",
                            modality="text",
                            evidence_origin="real",
                            launch_gate_eligible=True,
                        )
                    ],
                },
            )
            _write_json(
                manifests_dir / "metadata.json",
                {
                    "schema_version": "metadata.v1",
                    "notes": "not a loop manifest",
                },
            )
            _write_json(release_report, _release_report("GO"))
            current_status.write_text("Release switch decision: `GO`\n", encoding="utf-8")
            _write_json(agent_smoke, _agent_smoke_report())
            _write_json(doc_sync, _doc_sync_report())
            _write_json(ops_readiness, _ops_readiness_report())

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--loop-manifest-dir",
                    str(manifests_dir),
                    "--loop-manifest-pattern",
                    "*.json",
                    "--collection-report-output",
                    str(root / "collection-report.json"),
                    "--collection-summary-output",
                    str(root / "collection-summary.md"),
                    "--real-trial-manifest-output",
                    str(root / "real-manifest.json"),
                    "--trial-metrics-report-output",
                    str(root / "trial-metrics-report.json"),
                    "--trial-metrics-summary-output",
                    str(root / "trial-metrics-summary.md"),
                    "--launch-readiness-output",
                    str(launch_report),
                    "--launch-readiness-summary-output",
                    str(root / "launch-readiness-summary.md"),
                    "--evidence-pack-output",
                    str(evidence_pack),
                    "--backfill-execution-output",
                    str(root / "real-trial-backfill-execution-report.json"),
                    "--backfill-execution-summary-output",
                    str(root / "real-trial-backfill-execution-summary.md"),
                    "--backfill-intake-actions-output",
                    str(root / "real-trial-backfill-intake-actions-report.json"),
                    "--backfill-intake-actions-summary-output",
                    str(root / "real-trial-backfill-intake-actions-summary.md"),
                    "--backfill-submission-templates-output",
                    str(root / "real-trial-backfill-submission-templates-report.json"),
                    "--backfill-submission-templates-summary-output",
                    str(root / "real-trial-backfill-submission-templates-summary.md"),
                    "--backfill-submission-manifest-template-output",
                    str(root / "real-trial-backfill-submission-manifest.template.json"),
                    "--backfill-handoff-output",
                    str(root / "real-trial-backfill-handoff-report.json"),
                    "--backfill-handoff-summary-output",
                    str(root / "real-trial-backfill-handoff-summary.md"),
                    "--backfill-handoff-escalations-output",
                    str(root / "real-trial-backfill-handoff-escalations-report.json"),
                    "--backfill-handoff-escalations-summary-output",
                    str(root / "real-trial-backfill-handoff-escalations-summary.md"),
                    "--release-switch-report",
                    str(release_report),
                    "--current-status-doc",
                    str(current_status),
                    "--agent-smoke-report",
                    str(agent_smoke),
                    "--doc-sync-report",
                    str(doc_sync),
                    "--operations-readiness-report",
                    str(ops_readiness),
                    "--no-run-doc-sync",
                    "--minimum-complete-loops",
                    "1",
                    "--minimum-modalities",
                    "1",
                    "--max-evidence-age-hours",
                    "0",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            evidence_pack_payload = json.loads(evidence_pack.read_text(encoding="utf-8"))
            input_sources = evidence_pack_payload.get("input_sources", {})
            self.assertEqual(input_sources.get("input_loop_manifest_count"), 2)
            self.assertEqual(input_sources.get("ingested_loop_manifest_count"), 1)
            self.assertEqual(input_sources.get("skipped_non_loop_manifest_count"), 1)
            skipped_paths = input_sources.get("skipped_non_loop_manifest_paths", [])
            self.assertIn(str((manifests_dir / "metadata.json").resolve()), skipped_paths)

    def test_pipeline_strict_loop_manifest_contract_fails_on_non_manifest_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            manifests_dir = root / "real-loop-manifests"
            manifests_dir.mkdir(parents=True, exist_ok=True)
            release_report = root / "release-switch.json"
            current_status = root / "CURRENT_STATUS.md"
            agent_smoke = root / "agent-smoke.json"
            doc_sync = root / "doc-sync.json"
            ops_readiness = root / "ops-readiness.json"

            _write_json(manifests_dir / "metadata.json", {"schema_version": "metadata.v1"})
            _write_json(release_report, _release_report("GO"))
            current_status.write_text("Release switch decision: `GO`\n", encoding="utf-8")
            _write_json(agent_smoke, _agent_smoke_report())
            _write_json(doc_sync, _doc_sync_report())
            _write_json(ops_readiness, _ops_readiness_report())

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--loop-manifest-dir",
                    str(manifests_dir),
                    "--loop-manifest-pattern",
                    "*.json",
                    "--strict-loop-manifest-contract",
                    "--collection-report-output",
                    str(root / "collection-report.json"),
                    "--collection-summary-output",
                    str(root / "collection-summary.md"),
                    "--real-trial-manifest-output",
                    str(root / "real-manifest.json"),
                    "--trial-metrics-report-output",
                    str(root / "trial-metrics-report.json"),
                    "--trial-metrics-summary-output",
                    str(root / "trial-metrics-summary.md"),
                    "--launch-readiness-output",
                    str(root / "launch-readiness-report.json"),
                    "--launch-readiness-summary-output",
                    str(root / "launch-readiness-summary.md"),
                    "--evidence-pack-output",
                    str(root / "real-trial-launch-evidence-pack.json"),
                    "--release-switch-report",
                    str(release_report),
                    "--current-status-doc",
                    str(current_status),
                    "--agent-smoke-report",
                    str(agent_smoke),
                    "--doc-sync-report",
                    str(doc_sync),
                    "--operations-readiness-report",
                    str(ops_readiness),
                    "--no-run-doc-sync",
                    "--max-evidence-age-hours",
                    "0",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 2, completed.stderr + completed.stdout)
            self.assertIn("Loop manifest loops must be a list", completed.stderr)

    def test_pipeline_evidence_pack_exposes_duplicate_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            manifest_old = root / "manifest-old.json"
            manifest_new = root / "manifest-new.json"
            release_report = root / "release-switch.json"
            current_status = root / "CURRENT_STATUS.md"
            agent_smoke = root / "agent-smoke.json"
            doc_sync = root / "doc-sync.json"
            ops_readiness = root / "ops-readiness.json"
            evidence_pack = root / "real-trial-launch-evidence-pack.json"

            old_row = _loop_row(
                loop_id="real-text-dup-001",
                modality="text",
                evidence_origin="real",
                launch_gate_eligible=True,
            )
            old_row["reviewed_at_utc"] = "2026-05-26T00:05:00Z"
            old_row["collected_at_utc"] = "2026-05-26T00:00:00Z"

            new_row = _loop_row(
                loop_id="real-text-dup-001",
                modality="text",
                evidence_origin="real",
                launch_gate_eligible=True,
            )
            new_row["reviewed_at_utc"] = "2026-05-27T00:05:00Z"
            new_row["collected_at_utc"] = "2026-05-27T00:00:00Z"

            _write_json(manifest_old, {"manifest_id": "old", "loops": [old_row]})
            _write_json(manifest_new, {"manifest_id": "new", "loops": [new_row]})
            _write_json(release_report, _release_report("GO"))
            current_status.write_text("Release switch decision: `GO`\n", encoding="utf-8")
            _write_json(agent_smoke, _agent_smoke_report())
            _write_json(doc_sync, _doc_sync_report())
            _write_json(ops_readiness, _ops_readiness_report())

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--loop-manifest",
                    str(manifest_old),
                    "--loop-manifest",
                    str(manifest_new),
                    "--collection-report-output",
                    str(root / "collection-report.json"),
                    "--collection-summary-output",
                    str(root / "collection-summary.md"),
                    "--real-trial-manifest-output",
                    str(root / "real-manifest.json"),
                    "--trial-metrics-report-output",
                    str(root / "trial-metrics-report.json"),
                    "--trial-metrics-summary-output",
                    str(root / "trial-metrics-summary.md"),
                    "--launch-readiness-output",
                    str(root / "launch-readiness-report.json"),
                    "--launch-readiness-summary-output",
                    str(root / "launch-readiness-summary.md"),
                    "--evidence-pack-output",
                    str(evidence_pack),
                    "--backfill-execution-output",
                    str(root / "real-trial-backfill-execution-report.json"),
                    "--backfill-execution-summary-output",
                    str(root / "real-trial-backfill-execution-summary.md"),
                    "--backfill-intake-actions-output",
                    str(root / "real-trial-backfill-intake-actions-report.json"),
                    "--backfill-intake-actions-summary-output",
                    str(root / "real-trial-backfill-intake-actions-summary.md"),
                    "--backfill-submission-templates-output",
                    str(root / "real-trial-backfill-submission-templates-report.json"),
                    "--backfill-submission-templates-summary-output",
                    str(root / "real-trial-backfill-submission-templates-summary.md"),
                    "--backfill-submission-manifest-template-output",
                    str(root / "real-trial-backfill-submission-manifest.template.json"),
                    "--backfill-handoff-output",
                    str(root / "real-trial-backfill-handoff-report.json"),
                    "--backfill-handoff-summary-output",
                    str(root / "real-trial-backfill-handoff-summary.md"),
                    "--backfill-handoff-escalations-output",
                    str(root / "real-trial-backfill-handoff-escalations-report.json"),
                    "--backfill-handoff-escalations-summary-output",
                    str(root / "real-trial-backfill-handoff-escalations-summary.md"),
                    "--release-switch-report",
                    str(release_report),
                    "--current-status-doc",
                    str(current_status),
                    "--agent-smoke-report",
                    str(agent_smoke),
                    "--doc-sync-report",
                    str(doc_sync),
                    "--operations-readiness-report",
                    str(ops_readiness),
                    "--no-run-doc-sync",
                    "--minimum-complete-loops",
                    "1",
                    "--minimum-modalities",
                    "1",
                    "--max-evidence-age-hours",
                    "0",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            evidence_pack_payload = json.loads(evidence_pack.read_text(encoding="utf-8"))
            input_sources = evidence_pack_payload.get("input_sources", {})
            self.assertEqual(input_sources.get("duplicate_resolution_count"), 1)
            records = input_sources.get("duplicate_resolution_records", [])
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].get("resolution_reason"), "newer_reviewed_at_utc")

    def test_pipeline_evidence_pack_reports_submission_linked_pending_ack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            loop_manifest = root / "real-loop-manifest.json"
            release_report = root / "release-switch.json"
            current_status = root / "CURRENT_STATUS.md"
            agent_smoke = root / "agent-smoke.json"
            doc_sync = root / "doc-sync.json"
            ops_readiness = root / "ops-readiness.json"
            launch_report = root / "launch-readiness-report.json"
            evidence_pack = root / "real-trial-launch-evidence-pack.json"
            acknowledgements_report = root / "handoff-acknowledgements.json"

            _write_json(
                loop_manifest,
                {
                    "manifest_id": "gl25-ack-pending",
                    "loops": [
                        _loop_row(
                            loop_id="real-text-001",
                            modality="text",
                            evidence_origin="real",
                            launch_gate_eligible=True,
                        )
                    ],
                },
            )
            _write_json(
                acknowledgements_report,
                {
                    "schema_version": "real_trial_backfill_handoff_acknowledgements.v1",
                    "generated_at_utc": "2026-05-27T00:15:00Z",
                    "acknowledgements": [
                        {
                            "queue_item_id": "gl24-queue-gl23-slot-001-text",
                            "action_id": "gl23-slot-001-text",
                            "submitted_loop_id": "real-text-999",
                            "submitted_modality": "text",
                            "acknowledged_by": "ops-reviewer-1",
                            "acknowledged_at_utc": "2026-05-27T00:16:00Z",
                            "notes": "mismatch on purpose",
                        }
                    ],
                },
            )
            _write_json(release_report, _release_report("GO"))
            current_status.write_text("Release switch decision: `GO`\n", encoding="utf-8")
            _write_json(agent_smoke, _agent_smoke_report())
            _write_json(doc_sync, _doc_sync_report())
            _write_json(ops_readiness, _ops_readiness_report())

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--loop-manifest",
                    str(loop_manifest),
                    "--collection-report-output",
                    str(root / "collection-report.json"),
                    "--collection-summary-output",
                    str(root / "collection-summary.md"),
                    "--real-trial-manifest-output",
                    str(root / "real-manifest.json"),
                    "--trial-metrics-report-output",
                    str(root / "trial-metrics-report.json"),
                    "--trial-metrics-summary-output",
                    str(root / "trial-metrics-summary.md"),
                    "--launch-readiness-output",
                    str(launch_report),
                    "--launch-readiness-summary-output",
                    str(root / "launch-readiness-summary.md"),
                    "--evidence-pack-output",
                    str(evidence_pack),
                    "--backfill-execution-output",
                    str(root / "real-trial-backfill-execution-report.json"),
                    "--backfill-execution-summary-output",
                    str(root / "real-trial-backfill-execution-summary.md"),
                    "--backfill-intake-actions-output",
                    str(root / "real-trial-backfill-intake-actions-report.json"),
                    "--backfill-intake-actions-summary-output",
                    str(root / "real-trial-backfill-intake-actions-summary.md"),
                    "--backfill-submission-templates-output",
                    str(root / "real-trial-backfill-submission-templates-report.json"),
                    "--backfill-submission-templates-summary-output",
                    str(root / "real-trial-backfill-submission-templates-summary.md"),
                    "--backfill-submission-manifest-template-output",
                    str(root / "real-trial-backfill-submission-manifest.template.json"),
                    "--backfill-handoff-output",
                    str(root / "real-trial-backfill-handoff-report.json"),
                    "--backfill-handoff-summary-output",
                    str(root / "real-trial-backfill-handoff-summary.md"),
                    "--backfill-handoff-escalations-output",
                    str(root / "real-trial-backfill-handoff-escalations-report.json"),
                    "--backfill-handoff-escalations-summary-output",
                    str(root / "real-trial-backfill-handoff-escalations-summary.md"),
                    "--backfill-handoff-acknowledgements-report",
                    str(acknowledgements_report),
                    "--backfill-handoff-now-utc",
                    "2026-05-31T12:00:00Z",
                    "--release-switch-report",
                    str(release_report),
                    "--current-status-doc",
                    str(current_status),
                    "--agent-smoke-report",
                    str(agent_smoke),
                    "--doc-sync-report",
                    str(doc_sync),
                    "--operations-readiness-report",
                    str(ops_readiness),
                    "--no-run-doc-sync",
                    "--minimum-complete-loops",
                    "2",
                    "--minimum-modalities",
                    "1",
                    "--max-evidence-age-hours",
                    "0",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            evidence_pack_payload = json.loads(evidence_pack.read_text(encoding="utf-8"))
            classification = evidence_pack_payload.get("evidence_classification", {})
            self.assertEqual(classification.get("backfill_handoff_status"), "HANDOFF_OPERATOR_ACK_PENDING")
            self.assertEqual(classification.get("backfill_handoff_total_queue_item_count"), 1)
            self.assertEqual(classification.get("backfill_handoff_open_queue_item_count"), 0)
            self.assertEqual(classification.get("backfill_handoff_submission_linked_pending_ack_count"), 1)
            self.assertEqual(classification.get("backfill_handoff_closure_acknowledged_count"), 0)
            self.assertEqual(classification.get("backfill_submission_template_status"), "TEMPLATES_READY")
            self.assertEqual(classification.get("backfill_submission_template_total_action_count"), 1)
            self.assertEqual(classification.get("backfill_submission_template_pending_action_count"), 1)
            self.assertEqual(classification.get("backfill_submission_template_generated_count"), 1)
            self.assertEqual(classification.get("backfill_submission_template_missing_count"), 0)
            self.assertEqual(classification.get("backfill_submission_template_missing_actions"), [])
            self.assertEqual(
                classification.get("backfill_handoff_submission_linkage_strategy_counts"),
                {
                    "action_id_and_slot_index": 0,
                    "action_id_only": 0,
                    "slot_index_only": 0,
                    "modality_fallback": 1,
                    "none": 0,
                },
            )
            self.assertEqual(classification.get("backfill_handoff_submission_unlinked_count"), 0)
            self.assertEqual(classification.get("backfill_handoff_submission_unlinked_records"), [])
            self.assertEqual(classification.get("backfill_handoff_acknowledgement_input_count"), 1)
            self.assertEqual(classification.get("backfill_handoff_acknowledgement_valid_count"), 1)
            self.assertEqual(classification.get("backfill_handoff_acknowledgement_invalid_count"), 0)
            self.assertEqual(classification.get("backfill_handoff_acknowledgement_invalid_records"), [])
            self.assertEqual(classification.get("backfill_handoff_acknowledgement_sla_status"), "ACK_SLA_OVERDUE_ESCALATION")
            self.assertEqual(classification.get("backfill_handoff_acknowledgement_sla_hours"), 24.0)
            self.assertEqual(classification.get("backfill_handoff_acknowledgement_overdue_hours"), 72.0)
            self.assertEqual(classification.get("backfill_handoff_acknowledgement_within_sla_count"), 0)
            self.assertEqual(classification.get("backfill_handoff_acknowledgement_sla_breached_count"), 0)
            self.assertEqual(classification.get("backfill_handoff_acknowledgement_overdue_count"), 1)
            self.assertEqual(classification.get("backfill_handoff_acknowledgement_tracking_incomplete_count"), 0)
            overdue_items = classification.get("backfill_handoff_acknowledgement_overdue_queue_items", [])
            self.assertEqual(len(overdue_items), 1)
            self.assertEqual(overdue_items[0].get("queue_item_id"), "gl24-queue-gl23-slot-001-text")
            self.assertEqual(overdue_items[0].get("escalation_action"), "escalate_immediately")
            self.assertEqual(classification.get("backfill_handoff_escalation_status"), "ESCALATION_OVERDUE_ACTION_REQUIRED")
            self.assertEqual(classification.get("backfill_handoff_escalation_total_item_count"), 1)
            self.assertEqual(classification.get("backfill_handoff_escalation_sla_breached_item_count"), 0)
            self.assertEqual(classification.get("backfill_handoff_escalation_overdue_item_count"), 1)
            escalation_overdue_items = classification.get("backfill_handoff_escalation_overdue_items", [])
            self.assertEqual(len(escalation_overdue_items), 1)
            self.assertEqual(escalation_overdue_items[0].get("queue_item_id"), "gl24-queue-gl23-slot-001-text")
            self.assertEqual(escalation_overdue_items[0].get("escalation_severity"), "overdue")

    def test_pipeline_evidence_pack_reports_submission_linked_pending_ack_sla_breached(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            loop_manifest = root / "real-loop-manifest.json"
            release_report = root / "release-switch.json"
            current_status = root / "CURRENT_STATUS.md"
            agent_smoke = root / "agent-smoke.json"
            doc_sync = root / "doc-sync.json"
            ops_readiness = root / "ops-readiness.json"
            launch_report = root / "launch-readiness-report.json"
            evidence_pack = root / "real-trial-launch-evidence-pack.json"
            acknowledgements_report = root / "handoff-acknowledgements.json"

            _write_json(
                loop_manifest,
                {
                    "manifest_id": "gl26-ack-sla-breached",
                    "loops": [
                        _loop_row(
                            loop_id="real-text-001",
                            modality="text",
                            evidence_origin="real",
                            launch_gate_eligible=True,
                        )
                    ],
                },
            )
            _write_json(
                acknowledgements_report,
                {
                    "schema_version": "real_trial_backfill_handoff_acknowledgements.v1",
                    "generated_at_utc": "2026-05-27T00:15:00Z",
                    "acknowledgements": [
                        {
                            "queue_item_id": "gl24-queue-gl23-slot-001-text",
                            "action_id": "gl23-slot-001-text",
                            "submitted_loop_id": "real-text-999",
                            "submitted_modality": "text",
                            "acknowledged_by": "ops-reviewer-1",
                            "acknowledged_at_utc": "2026-05-27T00:16:00Z",
                            "notes": "mismatch on purpose",
                        }
                    ],
                },
            )
            _write_json(release_report, _release_report("GO"))
            current_status.write_text("Release switch decision: `GO`\n", encoding="utf-8")
            _write_json(agent_smoke, _agent_smoke_report())
            _write_json(doc_sync, _doc_sync_report())
            _write_json(ops_readiness, _ops_readiness_report())

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--loop-manifest",
                    str(loop_manifest),
                    "--collection-report-output",
                    str(root / "collection-report.json"),
                    "--collection-summary-output",
                    str(root / "collection-summary.md"),
                    "--real-trial-manifest-output",
                    str(root / "real-manifest.json"),
                    "--trial-metrics-report-output",
                    str(root / "trial-metrics-report.json"),
                    "--trial-metrics-summary-output",
                    str(root / "trial-metrics-summary.md"),
                    "--launch-readiness-output",
                    str(launch_report),
                    "--launch-readiness-summary-output",
                    str(root / "launch-readiness-summary.md"),
                    "--evidence-pack-output",
                    str(evidence_pack),
                    "--backfill-execution-output",
                    str(root / "real-trial-backfill-execution-report.json"),
                    "--backfill-execution-summary-output",
                    str(root / "real-trial-backfill-execution-summary.md"),
                    "--backfill-intake-actions-output",
                    str(root / "real-trial-backfill-intake-actions-report.json"),
                    "--backfill-intake-actions-summary-output",
                    str(root / "real-trial-backfill-intake-actions-summary.md"),
                    "--backfill-submission-templates-output",
                    str(root / "real-trial-backfill-submission-templates-report.json"),
                    "--backfill-submission-templates-summary-output",
                    str(root / "real-trial-backfill-submission-templates-summary.md"),
                    "--backfill-submission-manifest-template-output",
                    str(root / "real-trial-backfill-submission-manifest.template.json"),
                    "--backfill-handoff-output",
                    str(root / "real-trial-backfill-handoff-report.json"),
                    "--backfill-handoff-summary-output",
                    str(root / "real-trial-backfill-handoff-summary.md"),
                    "--backfill-handoff-escalations-output",
                    str(root / "real-trial-backfill-handoff-escalations-report.json"),
                    "--backfill-handoff-escalations-summary-output",
                    str(root / "real-trial-backfill-handoff-escalations-summary.md"),
                    "--backfill-handoff-escalations-output",
                    str(root / "real-trial-backfill-handoff-escalations-report.json"),
                    "--backfill-handoff-escalations-summary-output",
                    str(root / "real-trial-backfill-handoff-escalations-summary.md"),
                    "--backfill-handoff-acknowledgements-report",
                    str(acknowledgements_report),
                    "--backfill-handoff-now-utc",
                    "2026-05-28T12:30:00Z",
                    "--release-switch-report",
                    str(release_report),
                    "--current-status-doc",
                    str(current_status),
                    "--agent-smoke-report",
                    str(agent_smoke),
                    "--doc-sync-report",
                    str(doc_sync),
                    "--operations-readiness-report",
                    str(ops_readiness),
                    "--no-run-doc-sync",
                    "--minimum-complete-loops",
                    "2",
                    "--minimum-modalities",
                    "1",
                    "--max-evidence-age-hours",
                    "0",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            evidence_pack_payload = json.loads(evidence_pack.read_text(encoding="utf-8"))
            classification = evidence_pack_payload.get("evidence_classification", {})
            self.assertEqual(classification.get("backfill_handoff_status"), "HANDOFF_OPERATOR_ACK_PENDING")
            self.assertEqual(classification.get("backfill_handoff_acknowledgement_sla_status"), "ACK_SLA_BREACH_PENDING_ACTION")
            self.assertEqual(classification.get("backfill_handoff_acknowledgement_within_sla_count"), 0)
            self.assertEqual(classification.get("backfill_handoff_acknowledgement_sla_breached_count"), 1)
            self.assertEqual(classification.get("backfill_handoff_acknowledgement_overdue_count"), 0)
            self.assertEqual(classification.get("backfill_submission_template_status"), "TEMPLATES_READY")
            self.assertEqual(classification.get("backfill_submission_template_total_action_count"), 1)
            self.assertEqual(classification.get("backfill_submission_template_pending_action_count"), 1)
            self.assertEqual(classification.get("backfill_submission_template_generated_count"), 1)
            self.assertEqual(classification.get("backfill_submission_template_missing_count"), 0)
            self.assertEqual(classification.get("backfill_submission_template_missing_actions"), [])
            self.assertEqual(
                classification.get("backfill_handoff_submission_linkage_strategy_counts"),
                {
                    "action_id_and_slot_index": 0,
                    "action_id_only": 0,
                    "slot_index_only": 0,
                    "modality_fallback": 1,
                    "none": 0,
                },
            )
            self.assertEqual(classification.get("backfill_handoff_submission_unlinked_count"), 0)
            self.assertEqual(classification.get("backfill_handoff_submission_unlinked_records"), [])
            breached_items = classification.get("backfill_handoff_acknowledgement_sla_breached_queue_items", [])
            self.assertEqual(len(breached_items), 1)
            self.assertEqual(
                breached_items[0].get("escalation_action"),
                "notify_owner_and_track_until_acknowledged",
            )
            self.assertEqual(classification.get("backfill_handoff_acknowledgement_overdue_queue_items"), [])
            self.assertEqual(classification.get("backfill_handoff_escalation_status"), "ESCALATION_BREACH_ACTION_REQUIRED")
            self.assertEqual(classification.get("backfill_handoff_escalation_total_item_count"), 1)
            self.assertEqual(classification.get("backfill_handoff_escalation_sla_breached_item_count"), 1)
            self.assertEqual(classification.get("backfill_handoff_escalation_overdue_item_count"), 0)
            escalation_breached_items = classification.get("backfill_handoff_escalation_sla_breached_items", [])
            self.assertEqual(len(escalation_breached_items), 1)
            self.assertEqual(
                escalation_breached_items[0].get("escalation_action"),
                "notify_owner_and_track_until_acknowledged",
            )


if __name__ == "__main__":
    unittest.main()





