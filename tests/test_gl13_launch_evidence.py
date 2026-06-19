from __future__ import annotations

import ast
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "gl13_launch_evidence.py"


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


def _gl13_temp_output_args(root: Path) -> list[str]:
    output_flags = [
        "backfill-plan-output",
        "backfill-execution-output",
        "backfill-execution-summary-output",
        "backfill-intake-actions-output",
        "backfill-intake-actions-summary-output",
        "backfill-submission-templates-output",
        "backfill-submission-templates-summary-output",
        "backfill-submission-manifest-template-output",
        "backfill-submission-consumption-output",
        "backfill-submission-consumption-summary-output",
        "backfill-submission-throughput-output",
        "backfill-submission-throughput-summary-output",
        "backfill-submission-queue-output",
        "backfill-submission-queue-summary-output",
        "backfill-submission-queue-completion-output",
        "backfill-submission-queue-completion-summary-output",
        "backfill-submission-queue-commitments-output",
        "backfill-submission-queue-commitments-summary-output",
        "backfill-submission-queue-commitment-closure-output",
        "backfill-submission-queue-commitment-closure-summary-output",
        "backfill-submission-queue-followup-output",
        "backfill-submission-queue-followup-summary-output",
        "backfill-submission-queue-followup-resolution-output",
        "backfill-submission-queue-followup-resolution-summary-output",
        "backfill-submission-queue-followup-resolution-escalations-output",
        "backfill-submission-queue-followup-resolution-escalations-summary-output",
        "backfill-submission-queue-followup-resolution-escalation-acknowledgements-output",
        "backfill-submission-queue-followup-resolution-escalation-acknowledgements-summary-output",
        "backfill-submission-queue-followup-resolution-escalation-throughput-output",
        "backfill-submission-queue-followup-resolution-escalation-throughput-summary-output",
        "backfill-submission-queue-followup-resolution-escalation-action-plan-output",
        "backfill-submission-queue-followup-resolution-escalation-action-plan-summary-output",
        "backfill-submission-queue-followup-resolution-escalation-action-plan-closure-output",
        "backfill-submission-queue-followup-resolution-escalation-action-plan-closure-summary-output",
        "backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-output",
        "backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-summary-output",
        "backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalations-output",
        "backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalations-summary-output",
        "backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-ingestion-output",
        "backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-ingestion-summary-output",
        "backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-output",
        "backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-summary-output",
        "backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-output",
        "backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-summary-output",
        "backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalations-output",
        "backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalations-summary-output",
        "backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-output",
        "backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-summary-output",
        "backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-output",
        "backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-summary-output",
        "backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalations-output",
        "backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalations-summary-output",
        "backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-output",
        "backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-summary-output",
        "backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-output",
        "backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-summary-output",
        "backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalations-output",
        "backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalations-summary-output",
        "backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalation-closure-output",
        "backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalation-closure-summary-output",
        "backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-output",
        "backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-summary-output",
        "backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalations-output",
        "backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalations-summary-output",
        "backfill-handoff-output",
        "backfill-handoff-summary-output",
        "backfill-handoff-escalations-output",
        "backfill-handoff-escalations-summary-output",
    ]
    args: list[str] = []
    for index, flag in enumerate(output_flags):
        suffix = ".md" if "summary" in flag else ".json"
        args.extend([f"--{flag}", str(root / f"gl13-output-{index:02d}{suffix}")])
    return args


class RealTrialLaunchEvidenceScriptTests(unittest.TestCase):
    def test_evidence_pack_signature_matches_main_call_keywords(self) -> None:
        tree = ast.parse(SCRIPT_PATH.read_text(encoding="utf-8-sig"))
        evidence_pack_function = next(
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "_build_evidence_pack"
        )
        signature_keywords = {argument.arg for argument in evidence_pack_function.args.kwonlyargs}
        evidence_pack_calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_build_evidence_pack"
        ]

        self.assertEqual(len(evidence_pack_calls), 1)
        call_keywords = {keyword.arg for keyword in evidence_pack_calls[0].keywords if keyword.arg}
        self.assertEqual(call_keywords - signature_keywords, set())
        self.assertEqual(signature_keywords - call_keywords, set())

    def test_evidence_pack_path_hygiene_normalizes_repo_paths_and_flags_old_current(self) -> None:
        spec = importlib.util.spec_from_file_location("gl13_launch_evidence_under_test", SCRIPT_PATH)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        pack = {
            "evidence_paths": {
                "collection_report": str(
                    REPO_ROOT
                    / "docs"
                    / "working"
                    / "status"
                    / "baselines"
                    / "real-trial-loop-collection"
                    / "real-trial-loop-collection-report.json"
                ),
                "stale_collection_report": str(
                    REPO_ROOT
                    / "docs"
                    / "current"
                    / "status"
                    / "baselines"
                    / "real-trial-loop-collection"
                    / "real-trial-loop-collection-report.json"
                ),
            },
            "input_sources": {
                "run_report_paths": [
                    str(REPO_ROOT / "docs" / "working" / "status" / "baselines" / "controlled-trial" / "run.json")
                ]
            },
        }

        module._normalize_evidence_pack_paths(pack)
        self.assertEqual(
            pack["evidence_paths"]["collection_report"],
            "docs/working/status/baselines/real-trial-loop-collection/real-trial-loop-collection-report.json",
        )
        self.assertEqual(
            pack["evidence_paths"]["stale_collection_report"],
            "docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-report.json",
        )
        self.assertEqual(
            pack["input_sources"]["run_report_paths"],
            ["docs/working/status/baselines/controlled-trial/run.json"],
        )

        hygiene = module._build_path_hygiene(pack)
        self.assertEqual(hygiene.get("repo_root_absolute_path_count"), 0)
        self.assertEqual(hygiene.get("old_docs_current_path_count"), 1)
        self.assertEqual(
            hygiene.get("old_docs_current_paths"),
            ["docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-report.json"],
        )

        long_default = (
            REPO_ROOT
            / "docs"
            / "working"
            / "status"
            / "baselines"
            / "real-trial-loop-collection"
            / (
                "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-"
                "cadence-escalation-acknowledgement-ingestion-report.json"
            )
        )
        label = (
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_"
            "escalation_acknowledgement_ingestion_output"
        )
        aliased_default = module._maybe_windows_shorten_output_path(str(long_default), label=label)
        if Path(aliased_default).resolve() != long_default.resolve():
            self.assertFalse(
                module._is_default_cli_path(
                    raw_value=aliased_default,
                    default_path=long_default,
                    label=label,
                )
            )

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
                    *_gl13_temp_output_args(root),
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
            self.assertEqual(classification.get("real_evidence_template_placeholder_loop_count"), 0)
            self.assertEqual(classification.get("real_evidence_template_placeholder_field_count"), 0)
            self.assertEqual(classification.get("real_evidence_template_placeholder_records"), [])
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
            self.assertEqual(classification.get("backfill_submission_consumption_status"), "NO_TEMPLATE_ROWS")
            self.assertEqual(classification.get("backfill_submission_consumption_template_loop_count"), 0)
            self.assertEqual(classification.get("backfill_submission_consumption_submitted_row_count"), 0)
            self.assertEqual(classification.get("backfill_submission_consumption_consumed_loop_count"), 0)
            self.assertEqual(classification.get("backfill_submission_consumption_pending_template_loop_count"), 0)
            self.assertEqual(classification.get("backfill_submission_consumption_invalid_submission_count"), 0)
            self.assertEqual(classification.get("backfill_submission_consumption_unresolved_submission_count"), 0)
            self.assertEqual(classification.get("backfill_submission_consumption_pending_template_rows"), [])
            self.assertEqual(classification.get("backfill_submission_consumption_invalid_submissions"), [])
            self.assertEqual(classification.get("backfill_submission_consumption_unresolved_submissions"), [])
            self.assertEqual(
                classification.get("backfill_submission_throughput_action_plan_status"),
                "ACTION_PLAN_NOT_REQUIRED",
            )
            self.assertEqual(classification.get("backfill_submission_throughput_action_plan_blockers"), [])
            self.assertEqual(classification.get("backfill_submission_throughput_pending_submission_action_count"), 0)
            self.assertEqual(
                classification.get("backfill_submission_throughput_recommended_submission_action_count"),
                0,
            )
            self.assertEqual(classification.get("backfill_submission_throughput_priority_modalities"), [])
            self.assertEqual(classification.get("backfill_submission_throughput_recommended_submission_actions"), [])
            self.assertEqual(
                classification.get("backfill_submission_throughput_submission_consumption_status"),
                "NO_TEMPLATE_ROWS",
            )
            self.assertEqual(classification.get("backfill_submission_throughput_submission_template_loop_count"), 0)
            self.assertEqual(
                classification.get("backfill_submission_throughput_submission_pending_template_loop_count"),
                0,
            )
            self.assertEqual(classification.get("backfill_submission_throughput_submission_invalid_count"), 0)
            self.assertEqual(classification.get("backfill_submission_throughput_submission_unresolved_count"), 0)
            self.assertEqual(classification.get("backfill_submission_queue_status"), "QUEUE_NOT_REQUIRED")
            self.assertEqual(classification.get("backfill_submission_queue_warning_codes"), [])
            self.assertEqual(classification.get("backfill_submission_queue_total_item_count"), 0)
            self.assertEqual(classification.get("backfill_submission_queue_pending_item_count"), 0)
            self.assertEqual(classification.get("backfill_submission_queue_blocked_item_count"), 0)
            self.assertEqual(classification.get("backfill_submission_queue_pending_item_count_by_modality"), {})
            self.assertEqual(classification.get("backfill_submission_queue_blocked_item_count_by_modality"), {})
            self.assertEqual(classification.get("backfill_submission_queue_item_action_plan_status"), "ACTION_PLAN_NOT_REQUIRED")
            self.assertEqual(classification.get("backfill_submission_queue_item_action_plan_blockers"), [])
            self.assertEqual(classification.get("backfill_submission_queue_item_priority_modalities"), [])
            self.assertEqual(classification.get("backfill_submission_queue_item_pending_submission_action_count"), 0)
            self.assertEqual(classification.get("backfill_submission_queue_item_recommended_submission_action_count"), 0)
            self.assertEqual(classification.get("backfill_submission_queue_items"), [])
            self.assertEqual(classification.get("backfill_submission_queue_refresh_interval_hours"), 24.0)
            self.assertEqual(classification.get("backfill_submission_queue_refresh_cadence_status"), "CADENCE_NOT_REQUIRED")
            self.assertEqual(classification.get("backfill_submission_queue_refresh_previous_generated_at_utc"), "")
            self.assertEqual(classification.get("backfill_submission_queue_refresh_next_due_utc"), "")
            self.assertEqual(classification.get("backfill_submission_queue_refresh_due_in_hours"), 0.0)
            self.assertNotEqual(classification.get("backfill_submission_queue_refresh_evaluated_at_utc"), "")
            self.assertEqual(classification.get("backfill_submission_queue_completion_status"), "COMPLETION_NOT_REQUIRED")
            self.assertEqual(
                classification.get("backfill_submission_queue_completion_progress_status"),
                "COMPLETION_NOT_REQUIRED",
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_cycle_verification_status"),
                "CYCLE_NOT_REQUIRED",
            )
            self.assertEqual(classification.get("backfill_submission_queue_completion_warning_codes"), [])
            self.assertEqual(classification.get("backfill_submission_queue_completion_submitted_item_count"), 0)
            self.assertEqual(classification.get("backfill_submission_queue_completion_closed_item_count"), 0)
            self.assertEqual(classification.get("backfill_submission_queue_completion_open_item_count"), 0)
            self.assertEqual(classification.get("backfill_submission_queue_completion_missing_handoff_item_count"), 0)
            self.assertEqual(classification.get("backfill_submission_queue_completion_unknown_transition_item_count"), 0)
            self.assertTrue(classification.get("backfill_submission_queue_cycle_net_new_movement_verified"))
            self.assertEqual(classification.get("backfill_submission_queue_cycle_throughput_net_new_loop_count"), 1)
            self.assertEqual(
                classification.get("backfill_submission_queue_cycle_throughput_net_new_loop_ids"),
                ["real-text-001"],
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_cycle_submitted_item_delta_from_previous_cycle"),
                0,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_cycle_closed_item_delta_from_previous_cycle"),
                0,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_cycle_open_item_delta_from_previous_cycle"),
                0,
            )
            self.assertEqual(classification.get("backfill_submission_queue_completion_transition_records"), [])
            self.assertEqual(classification.get("backfill_submission_queue_commitment_status"), "COMMITMENTS_NOT_REQUIRED")
            self.assertEqual(
                classification.get("backfill_submission_queue_cadence_run_obligation_status"),
                "RUN_NOT_REQUIRED",
            )
            self.assertEqual(classification.get("backfill_submission_queue_commitment_total_count"), 0)
            self.assertEqual(classification.get("backfill_submission_queue_commitment_pending_submission_count"), 0)
            self.assertEqual(classification.get("backfill_submission_queue_commitment_pending_acknowledgement_count"), 0)
            self.assertEqual(
                classification.get("backfill_submission_queue_commitment_blocked_submission_errors_count"),
                0,
            )
            self.assertEqual(classification.get("backfill_submission_queue_commitment_escalation_required_count"), 0)
            self.assertEqual(classification.get("backfill_submission_queue_commitment_rebuild_required_count"), 0)
            self.assertEqual(classification.get("backfill_submission_queue_owner_commitment_counts"), {})
            self.assertEqual(classification.get("backfill_submission_queue_unresolved_execution_blockers"), [])
            self.assertEqual(classification.get("backfill_submission_queue_commitment_rows"), [])
            commitment_cycle = classification.get("backfill_submission_queue_commitment_cycle_snapshot", {})
            self.assertEqual(commitment_cycle.get("queue_status"), "QUEUE_NOT_REQUIRED")
            self.assertEqual(commitment_cycle.get("throughput_status"), "THROUGHPUT_THRESHOLD_MET")
            self.assertEqual(
                classification.get("backfill_submission_queue_commitment_closure_status"),
                "CLOSURE_NOT_REQUIRED",
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_commitment_cadence_run_closure_status"),
                "CLOSURE_RUN_NOT_REQUIRED",
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_commitment_closure_total_count"),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_commitment_closure_closed_with_acknowledgement_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_commitment_closure_active_count"),
                0,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_commitment_stale_rollover_count"),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_commitment_net_new_closed_with_acknowledgement_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_commitment_closure_warning_codes"),
                [],
            )
            self.assertEqual(classification.get("backfill_submission_queue_commitment_closure_rows"), [])
            self.assertEqual(
                classification.get("backfill_submission_queue_commitment_closure_acknowledgement_rows"),
                [],
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_commitment_stale_rollover_rows"),
                [],
            )
            self.assertEqual(classification.get("backfill_submission_queue_followup_status"), "FOLLOWUP_NOT_REQUIRED")
            self.assertEqual(classification.get("backfill_submission_queue_followup_warning_codes"), [])
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_commitment_closure_status_gl40"),
                "CLOSURE_NOT_REQUIRED",
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_cadence_run_closure_status_gl40"),
                "CLOSURE_RUN_NOT_REQUIRED",
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_closure_warning_codes_gl40"),
                [],
            )
            self.assertEqual(classification.get("backfill_submission_queue_followup_total_action_count"), 0)
            self.assertEqual(classification.get("backfill_submission_queue_followup_open_action_count"), 0)
            self.assertEqual(classification.get("backfill_submission_queue_followup_closed_action_count"), 0)
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_stale_rollover_action_count"),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_acknowledgement_completion_action_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_acknowledgement_closed_action_count"),
                0,
            )
            self.assertEqual(classification.get("backfill_submission_queue_followup_blocked_action_count"), 0)
            self.assertEqual(classification.get("backfill_submission_queue_followup_owner_counts"), {})
            self.assertEqual(classification.get("backfill_submission_queue_followup_action_rows"), [])
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_status"),
                "FOLLOWUP_RESOLUTION_NOT_REQUIRED",
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_warning_codes"),
                ["submission_consumption_not_ready"],
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_total_action_count"),
                0,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_open_action_count_gl41"),
                0,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_closed_action_count_gl41"),
                0,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_resolved_action_count"),
                0,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_in_progress_action_count"),
                0,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_unresolved_action_count"),
                0,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_submission_linked_action_count"),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_closure_acknowledged_action_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_consumed_submission_action_count"),
                0,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_submission_invalid_count"),
                0,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_submission_unresolved_count"),
                0,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_owner_counts"),
                {},
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_rows"),
                [],
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_status"),
                "FOLLOWUP_RESOLUTION_ESCALATION_NOT_REQUIRED",
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_warning_codes"),
                [],
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_total_item_count"),
                0,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_open_item_count"),
                0,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_blocked_item_count"),
                0,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_pending_ack_item_count"),
                0,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_active_item_count"),
                0,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_owner_counts"),
                {},
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_rows"),
                [],
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_acknowledgement_status"),
                "FOLLOWUP_RESOLUTION_ESCALATION_ACK_NOT_REQUIRED",
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_acknowledgement_warning_codes"),
                [],
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_acknowledgement_total_item_count"),
                0,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_acknowledgement_open_item_count"),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_acknowledgement_resolved_acknowledged_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_acknowledgement_pending_ack_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_acknowledgement_blocked_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_acknowledgement_owner_counts"),
                {},
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_acknowledgement_rows"),
                [],
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_throughput_status"),
                "ESCALATION_ACK_THROUGHPUT_THRESHOLD_MET",
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_throughput_warning_codes"),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_throughput_net_new_resolved_acknowledged_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_throughput_net_new_resolved_submission_loop_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_throughput_net_new_launch_gate_eligible_loop_count"
                ),
                1,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_throughput_unresolved_ack_closed_loop_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_throughput_unresolved_acknowledged_submission_loop_ids"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_throughput_net_new_resolved_submission_loop_ids"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_throughput_net_new_launch_gate_eligible_loop_ids"
                ),
                ["real-text-001"],
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_action_plan_status"),
                "ACTION_PLAN_NOT_REQUIRED",
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_action_plan_warning_codes"),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_total_action_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_open_action_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closed_action_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_unresolved_ack_mapping_action_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_recommended_backfill_slot_action_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_action_plan_rows"),
                [],
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_action_plan_closure_status"),
                "ACTION_PLAN_CLOSURE_NOT_REQUIRED",
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_action_plan_closure_warning_codes"),
                [],
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_action_plan_closure_total_action_count"),
                0,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_action_plan_closure_open_action_count"),
                0,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_action_plan_closure_closed_action_count"),
                0,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_action_plan_closure_carried_open_action_count"),
                0,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_action_plan_closure_net_new_closed_action_count"),
                0,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_action_plan_closure_stale_open_action_count"),
                0,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_action_plan_closure_net_new_launch_gate_eligible_loop_count"),
                1,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_action_plan_closure_open_action_count_delta"),
                0,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_action_plan_closure_carried_open_action_ids"),
                [],
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_action_plan_closure_net_new_closed_action_ids"),
                [],
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_action_plan_closure_net_new_launch_gate_eligible_loop_ids"),
                ["real-text-001"],
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_action_plan_closure_rows"),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_status"
                ),
                "ACTION_PLAN_CLOSURE_CADENCE_NOT_REQUIRED",
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_warning_codes"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_total_action_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_open_action_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_stale_open_action_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_stall_cycle_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_overdue_stalled_cycles_threshold"
                ),
                2,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_refresh_interval_hours"
                ),
                24.0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_state"
                ),
                "CADENCE_NOT_REQUIRED",
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_previous_generated_at_utc"
                ),
                "",
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_next_refresh_due_utc"
                ),
                "",
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_due_in_hours"
                ),
                0.0,
            )
            self.assertNotEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_evaluated_at_utc"
                ),
                "",
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_rows"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_status"
                ),
                "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_NOT_REQUIRED",
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_warning_codes"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_total_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_blocked_overdue_stalled_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_due_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_monitor_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_cadence_stall_cycle_count_gl48"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_cadence_overdue_stalled_cycles_threshold_gl48"
                ),
                2,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_escalate_after_due_hours"
                ),
                24.0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_owner_counts"
                ),
                {},
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_rows"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_status"
                ),
                "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_NOT_REQUIRED",
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_warning_codes"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_total_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_closed_item_count"
                ),
                0,
            )
            self.assertFalse(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_input_present"
                )
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_input_acknowledgement_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_rows"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_status"
                ),
                "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_NOT_REQUIRED",
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_warning_codes"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_total_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_closed_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_previous_open_item_count_gl50"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_carried_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_stale_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_net_new_closed_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_ack_loop_mismatch_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_ack_missing_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_missing_handoff_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_net_new_launch_gate_eligible_loop_count"
                ),
                1,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_open_item_count_delta"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_carried_open_item_ids"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_net_new_closed_item_ids"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_net_new_launch_gate_eligible_loop_ids"
                ),
                ["real-text-001"],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_rows"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_status"
                ),
                "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_NOT_REQUIRED",
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_warning_codes"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_total_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_stale_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_net_new_closed_item_count_gl51"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_net_new_launch_gate_eligible_loop_count_gl51"
                ),
                1,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_stall_cycle_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_overdue_stalled_cycles_threshold"
                ),
                2,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_refresh_interval_hours"
                ),
                24.0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_state"
                ),
                "CADENCE_NOT_REQUIRED",
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_previous_generated_at_utc"
                ),
                "",
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_next_refresh_due_utc"
                ),
                "",
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_due_in_hours"
                ),
                0.0,
            )
            self.assertNotEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_evaluated_at_utc"
                ),
                "",
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_rows"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_status"
                ),
                "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_NOT_REQUIRED",
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_warning_codes"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_total_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_blocked_overdue_stalled_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_due_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_monitor_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_cadence_stall_cycle_count_gl52"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_cadence_overdue_stalled_cycles_threshold_gl52"
                ),
                2,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_escalate_after_due_hours"
                ),
                24.0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_owner_counts"
                ),
                {},
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_rows"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_status"
                ),
                "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_NOT_REQUIRED",
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_warning_codes"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_total_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_previous_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_carried_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_stale_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_net_new_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_net_new_closed_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_net_new_closed_backed_by_ack_ingestion_item_count_gl50"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_net_new_closed_without_ack_ingestion_item_count_gl50"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_ack_ingestion_closed_item_count_gl50"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_ack_ingestion_open_item_count_gl50"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_owner_counts"
                ),
                {},
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_carried_open_item_ids"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_net_new_open_item_ids"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_net_new_closed_item_ids"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_net_new_closed_backed_by_ack_ingestion_item_ids_gl50"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_net_new_closed_without_ack_ingestion_item_ids_gl50"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_rows"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_status"
                ),
                "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_NOT_REQUIRED",
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_warning_codes"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_total_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_stale_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_net_new_closed_item_count_gl54"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_net_new_closed_backed_by_ack_ingestion_item_count_gl50"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_stall_cycle_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_overdue_stalled_cycles_threshold"
                ),
                2,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_refresh_interval_hours"
                ),
                24.0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_state"
                ),
                "CADENCE_NOT_REQUIRED",
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_previous_generated_at_utc"
                ),
                "",
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_next_refresh_due_utc"
                ),
                "",
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_due_in_hours"
                ),
                0.0,
            )
            self.assertNotEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_evaluated_at_utc"
                ),
                "",
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_rows"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_status"
                ),
                "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLEARED",
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_warning_codes"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_total_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_blocked_overdue_stalled_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_due_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_monitor_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_cadence_stall_cycle_count_gl55"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_cadence_overdue_stalled_cycles_threshold_gl55"
                ),
                2,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_escalate_after_due_hours"
                ),
                24.0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_owner_counts"
                ),
                {},
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_rows"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_status"
                ),
                "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_BASELINE_INITIALIZED",
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_warning_codes"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_total_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_previous_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_carried_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_stale_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_backed_by_gl54_net_new_closed_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_without_gl54_net_new_closed_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_gl54_net_new_closed_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_gl54_net_new_closed_action_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_owner_counts"
                ),
                {},
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_carried_open_item_ids"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_open_item_ids"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_item_ids"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_backed_by_gl54_net_new_closed_item_ids"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_without_gl54_net_new_closed_item_ids"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_gl54_net_new_closed_item_ids"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_rows"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_status"
                ),
                "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_BASELINE_INITIALIZED",
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_warning_codes"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_total_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_stale_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_net_new_closed_item_count_gl57"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_net_new_closed_backed_by_gl54_net_new_closed_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_stall_cycle_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_overdue_stalled_cycles_threshold"
                ),
                2,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_refresh_interval_hours"
                ),
                24.0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_state"
                ),
                "CADENCE_BASELINE_INITIALIZED",
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_previous_generated_at_utc"
                ),
                "",
            )
            self.assertNotEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_next_refresh_due_utc"
                ),
                "",
            )
            self.assertGreater(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_due_in_hours"
                ),
                0.0,
            )
            self.assertNotEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_evaluated_at_utc"
                ),
                "",
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_rows"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_status"
                ),
                "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_NOT_REQUIRED",
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_warning_codes"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_total_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_blocked_overdue_stalled_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_due_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_monitor_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_cadence_stall_cycle_count_gl58"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_cadence_overdue_stalled_cycles_threshold_gl58"
                ),
                2,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_escalate_after_due_hours"
                ),
                24.0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_owner_counts"
                ),
                {},
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_rows"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_status"
                ),
                "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_BASELINE_INITIALIZED",
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_warning_codes"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_total_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_previous_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_carried_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_stale_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_backed_by_gl57_net_new_closed_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_without_gl57_net_new_closed_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_gl57_net_new_closed_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_gl57_net_new_closed_action_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_owner_counts"
                ),
                {},
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_carried_open_item_ids"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_open_item_ids"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_item_ids"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_backed_by_gl57_net_new_closed_item_ids"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_without_gl57_net_new_closed_item_ids"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_gl57_net_new_closed_item_ids"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_rows"
                ),
                [],
            )
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
            self.assertEqual(classification.get("backfill_submission_consumption_status"), "NO_SUBMISSIONS_PROVIDED")
            self.assertEqual(classification.get("backfill_submission_consumption_template_loop_count"), 10)
            self.assertEqual(classification.get("backfill_submission_consumption_submitted_row_count"), 0)
            self.assertEqual(classification.get("backfill_submission_consumption_consumed_loop_count"), 0)
            self.assertEqual(classification.get("backfill_submission_consumption_pending_template_loop_count"), 10)
            self.assertEqual(classification.get("backfill_submission_consumption_invalid_submission_count"), 0)
            self.assertEqual(classification.get("backfill_submission_consumption_unresolved_submission_count"), 0)
            pending_consumption_rows = classification.get("backfill_submission_consumption_pending_template_rows", [])
            self.assertEqual(len(pending_consumption_rows), 10)
            self.assertEqual(classification.get("backfill_submission_consumption_invalid_submissions"), [])
            self.assertEqual(classification.get("backfill_submission_consumption_unresolved_submissions"), [])
            self.assertEqual(classification.get("real_evidence_template_placeholder_loop_count"), 0)
            self.assertEqual(classification.get("real_evidence_template_placeholder_field_count"), 0)
            self.assertEqual(classification.get("real_evidence_template_placeholder_records"), [])
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
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_throughput_status"),
                "ESCALATION_ACK_THROUGHPUT_BASELINE_INITIALIZED",
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_throughput_warning_codes"),
                [
                    "modality_gap_persists",
                    "loop_volume_gap_persists",
                ],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_throughput_net_new_resolved_acknowledged_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_throughput_net_new_resolved_submission_loop_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_throughput_net_new_launch_gate_eligible_loop_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_throughput_unresolved_ack_closed_loop_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_throughput_unresolved_acknowledged_submission_loop_ids"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_throughput_net_new_resolved_submission_loop_ids"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_throughput_net_new_launch_gate_eligible_loop_ids"
                ),
                [],
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_action_plan_status"),
                "ACTION_PLAN_OPEN",
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_action_plan_warning_codes"),
                [
                    "modality_gap_persists",
                    "loop_volume_gap_persists",
                    "open_followup_resolution_escalation_action_plan_items_present",
                ],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_total_action_count"
                ),
                10,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_open_action_count"
                ),
                10,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closed_action_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_unresolved_ack_mapping_action_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_recommended_backfill_slot_action_count"
                ),
                10,
            )
            action_plan_rows = classification.get(
                "backfill_submission_queue_followup_resolution_escalation_action_plan_rows",
                [],
            )
            self.assertEqual(len(action_plan_rows), 10)
            self.assertEqual(action_plan_rows[0].get("action_type"), "collect_launch_gate_eligible_real_loop")
            self.assertEqual(action_plan_rows[0].get("required_modality"), "text")

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
            self.assertEqual(classification.get("backfill_submission_consumption_status"), "NO_SUBMISSIONS_PROVIDED")
            self.assertEqual(classification.get("backfill_submission_consumption_template_loop_count"), 1)
            self.assertEqual(classification.get("backfill_submission_consumption_submitted_row_count"), 0)
            self.assertEqual(classification.get("backfill_submission_consumption_consumed_loop_count"), 0)
            self.assertEqual(classification.get("backfill_submission_consumption_pending_template_loop_count"), 1)
            self.assertEqual(classification.get("backfill_submission_consumption_invalid_submission_count"), 0)
            self.assertEqual(classification.get("backfill_submission_consumption_unresolved_submission_count"), 0)
            self.assertEqual(
                classification.get("backfill_submission_throughput_action_plan_status"),
                "ACTION_PLAN_WAITING_FOR_SUBMISSIONS",
            )
            self.assertIn(
                "real_loop_volume_below_threshold",
                classification.get("backfill_submission_throughput_action_plan_blockers", []),
            )
            self.assertEqual(classification.get("backfill_submission_throughput_pending_submission_action_count"), 1)
            self.assertEqual(
                classification.get("backfill_submission_throughput_recommended_submission_action_count"),
                1,
            )
            priority_modalities = classification.get("backfill_submission_throughput_priority_modalities", [])
            self.assertEqual(len(priority_modalities), 1)
            self.assertEqual(priority_modalities[0].get("modality"), "text")
            recommended_actions = classification.get("backfill_submission_throughput_recommended_submission_actions", [])
            self.assertEqual(len(recommended_actions), 1)
            self.assertEqual(recommended_actions[0].get("backfill_action_id"), "gl23-slot-001-text")
            self.assertEqual(recommended_actions[0].get("required_modality"), "text")
            self.assertEqual(recommended_actions[0].get("reason"), "pending_template_submission_required")
            self.assertEqual(
                classification.get("backfill_submission_throughput_submission_consumption_status"),
                "NO_SUBMISSIONS_PROVIDED",
            )
            self.assertEqual(classification.get("backfill_submission_throughput_submission_template_loop_count"), 1)
            self.assertEqual(
                classification.get("backfill_submission_throughput_submission_pending_template_loop_count"),
                1,
            )
            self.assertEqual(classification.get("backfill_submission_throughput_submission_invalid_count"), 0)
            self.assertEqual(classification.get("backfill_submission_throughput_submission_unresolved_count"), 0)
            self.assertEqual(classification.get("backfill_submission_queue_status"), "QUEUE_ACTIVE")
            queue_warning_codes = classification.get("backfill_submission_queue_warning_codes", [])
            self.assertIn("submission_queue_refresh_required_until_threshold_met", queue_warning_codes)
            self.assertEqual(classification.get("backfill_submission_queue_total_item_count"), 1)
            self.assertEqual(classification.get("backfill_submission_queue_pending_item_count"), 1)
            self.assertEqual(classification.get("backfill_submission_queue_blocked_item_count"), 0)
            self.assertEqual(
                classification.get("backfill_submission_queue_pending_item_count_by_modality"),
                {"text": 1},
            )
            self.assertEqual(classification.get("backfill_submission_queue_blocked_item_count_by_modality"), {})
            self.assertEqual(
                classification.get("backfill_submission_queue_item_action_plan_status"),
                "ACTION_PLAN_WAITING_FOR_SUBMISSIONS",
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_item_pending_submission_action_count"),
                1,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_item_recommended_submission_action_count"),
                1,
            )
            queue_items = classification.get("backfill_submission_queue_items", [])
            self.assertEqual(len(queue_items), 1)
            self.assertEqual(queue_items[0].get("queue_item_status"), "pending_submission")
            self.assertEqual(classification.get("backfill_submission_queue_refresh_interval_hours"), 24.0)
            cadence_status = classification.get("backfill_submission_queue_refresh_cadence_status")
            self.assertIn(cadence_status, {"CADENCE_BASELINE_INITIALIZED", "CADENCE_ON_SCHEDULE", "CADENCE_DUE"})
            self.assertNotEqual(classification.get("backfill_submission_queue_refresh_evaluated_at_utc"), "")
            self.assertEqual(classification.get("backfill_submission_queue_completion_status"), "COMPLETION_SUBMISSION_LINKED")
            self.assertEqual(
                classification.get("backfill_submission_queue_completion_progress_status"),
                "COMPLETION_BASELINE_INITIALIZED",
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_cycle_verification_status"),
                "CYCLE_BASELINE_INITIALIZED",
            )
            completion_warnings = classification.get("backfill_submission_queue_completion_warning_codes", [])
            self.assertEqual(completion_warnings, ["submission_queue_refresh_required_until_threshold_met"])
            self.assertEqual(classification.get("backfill_submission_queue_completion_submitted_item_count"), 1)
            self.assertEqual(classification.get("backfill_submission_queue_completion_closed_item_count"), 0)
            self.assertEqual(classification.get("backfill_submission_queue_completion_open_item_count"), 0)
            self.assertEqual(classification.get("backfill_submission_queue_completion_missing_handoff_item_count"), 0)
            self.assertEqual(classification.get("backfill_submission_queue_completion_unknown_transition_item_count"), 0)
            self.assertTrue(classification.get("backfill_submission_queue_cycle_net_new_movement_verified"))
            self.assertEqual(classification.get("backfill_submission_queue_cycle_throughput_net_new_loop_count"), 1)
            self.assertEqual(
                classification.get("backfill_submission_queue_cycle_throughput_net_new_loop_ids"),
                ["real-text-001"],
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_cycle_submitted_item_delta_from_previous_cycle"),
                1,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_cycle_closed_item_delta_from_previous_cycle"),
                0,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_cycle_open_item_delta_from_previous_cycle"),
                0,
            )
            completion_records = classification.get("backfill_submission_queue_completion_transition_records", [])
            self.assertEqual(len(completion_records), 1)
            self.assertEqual(completion_records[0].get("transition_state"), "submitted_pending_ack")
            self.assertEqual(completion_records[0].get("linked_submission_loop_id"), "real-text-001")
            self.assertEqual(classification.get("backfill_submission_queue_commitment_status"), "COMMITMENTS_ESCALATION_REQUIRED")
            self.assertEqual(
                classification.get("backfill_submission_queue_cadence_run_obligation_status"),
                "RUN_ON_SCHEDULE_WITH_OPEN_COMMITMENTS",
            )
            self.assertEqual(classification.get("backfill_submission_queue_commitment_total_count"), 1)
            self.assertEqual(classification.get("backfill_submission_queue_commitment_pending_submission_count"), 0)
            self.assertEqual(classification.get("backfill_submission_queue_commitment_pending_acknowledgement_count"), 0)
            self.assertEqual(
                classification.get("backfill_submission_queue_commitment_blocked_submission_errors_count"),
                0,
            )
            self.assertEqual(classification.get("backfill_submission_queue_commitment_escalation_required_count"), 1)
            self.assertEqual(classification.get("backfill_submission_queue_commitment_rebuild_required_count"), 0)
            owner_commitment_counts = classification.get("backfill_submission_queue_owner_commitment_counts", {})
            self.assertIn("controlled-beta-ops", owner_commitment_counts)
            self.assertEqual(owner_commitment_counts["controlled-beta-ops"].get("escalation_required_count"), 1)
            unresolved_blockers = classification.get("backfill_submission_queue_unresolved_execution_blockers", [])
            self.assertIn("submission_queue_acknowledgement_escalation_required", unresolved_blockers)
            self.assertIn("submission_action_plan_waiting_for_submissions", unresolved_blockers)
            commitment_rows = classification.get("backfill_submission_queue_commitment_rows", [])
            self.assertEqual(len(commitment_rows), 1)
            self.assertEqual(commitment_rows[0].get("commitment_status"), "escalation_required")
            commitment_cycle = classification.get("backfill_submission_queue_commitment_cycle_snapshot", {})
            self.assertEqual(commitment_cycle.get("completion_progress_status"), "COMPLETION_BASELINE_INITIALIZED")
            self.assertEqual(commitment_cycle.get("throughput_status"), "THROUGHPUT_BASELINE_INITIALIZED")
            self.assertEqual(
                classification.get("backfill_submission_queue_commitment_closure_status"),
                "CLOSURE_ESCALATION_REQUIRED",
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_commitment_cadence_run_closure_status"),
                "CLOSURE_RUN_ACTIVE",
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_commitment_closure_total_count"),
                1,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_commitment_closure_closed_with_acknowledgement_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_commitment_closure_active_count"),
                1,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_commitment_stale_rollover_count"),
                0,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_commitment_closure_acknowledgement_rows"),
                [],
            )
            closure_rows = classification.get("backfill_submission_queue_commitment_closure_rows", [])
            self.assertEqual(len(closure_rows), 1)
            self.assertEqual(closure_rows[0].get("closure_state"), "escalation_required")
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_status"),
                "FOLLOWUP_BLOCKED_BY_CLOSURE_STATE",
            )
            followup_warning_codes = classification.get("backfill_submission_queue_followup_warning_codes", [])
            self.assertIn("escalation_required_followup_actions_required", followup_warning_codes)
            self.assertIn("open_followup_actions_present", followup_warning_codes)
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_commitment_closure_status_gl40"),
                "CLOSURE_ESCALATION_REQUIRED",
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_cadence_run_closure_status_gl40"),
                "CLOSURE_RUN_ACTIVE",
            )
            self.assertEqual(classification.get("backfill_submission_queue_followup_total_action_count"), 1)
            self.assertEqual(classification.get("backfill_submission_queue_followup_open_action_count"), 1)
            self.assertEqual(classification.get("backfill_submission_queue_followup_closed_action_count"), 0)
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_stale_rollover_action_count"),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_acknowledgement_completion_action_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_acknowledgement_closed_action_count"),
                0,
            )
            self.assertEqual(classification.get("backfill_submission_queue_followup_blocked_action_count"), 1)
            followup_owner_counts = classification.get("backfill_submission_queue_followup_owner_counts", {})
            self.assertIn("controlled-beta-ops", followup_owner_counts)
            self.assertEqual(
                followup_owner_counts["controlled-beta-ops"].get("open_action_count"),
                1,
            )
            followup_actions = classification.get("backfill_submission_queue_followup_action_rows", [])
            self.assertEqual(len(followup_actions), 1)
            self.assertEqual(followup_actions[0].get("followup_action_status"), "open")
            self.assertEqual(
                followup_actions[0].get("followup_action_type"),
                "resolve_escalation_required_closure",
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_status"),
                "FOLLOWUP_RESOLUTION_IN_PROGRESS",
            )
            resolution_warning_codes = classification.get(
                "backfill_submission_queue_followup_resolution_warning_codes",
                [],
            )
            self.assertEqual(
                resolution_warning_codes,
                ["submission_consumption_not_ready"],
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_total_action_count"),
                1,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_open_action_count_gl41"),
                1,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_closed_action_count_gl41"),
                0,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_resolved_action_count"),
                0,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_in_progress_action_count"),
                1,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_unresolved_action_count"),
                0,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_submission_linked_action_count"),
                1,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_closure_acknowledged_action_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_consumed_submission_action_count"),
                0,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_submission_invalid_count"),
                0,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_submission_unresolved_count"),
                0,
            )
            resolution_owner_counts = classification.get(
                "backfill_submission_queue_followup_resolution_owner_counts",
                {},
            )
            self.assertIn("controlled-beta-ops", resolution_owner_counts)
            self.assertEqual(
                resolution_owner_counts["controlled-beta-ops"].get("total_action_count"),
                1,
            )
            self.assertEqual(
                resolution_owner_counts["controlled-beta-ops"].get("open_action_count_gl41"),
                1,
            )
            self.assertEqual(
                resolution_owner_counts["controlled-beta-ops"].get("in_progress_action_count"),
                1,
            )
            resolution_rows = classification.get("backfill_submission_queue_followup_resolution_rows", [])
            self.assertEqual(len(resolution_rows), 1)
            self.assertEqual(resolution_rows[0].get("resolution_status"), "in_progress")
            self.assertEqual(
                resolution_rows[0].get("resolution_state"),
                "in_progress_submission_linked_pending_ack",
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_status"),
                "FOLLOWUP_RESOLUTION_ESCALATION_PENDING_ACK_ACTION_REQUIRED",
            )
            escalation_warning_codes = classification.get(
                "backfill_submission_queue_followup_resolution_escalation_warning_codes",
                [],
            )
            self.assertIn(
                "followup_resolution_in_progress_pending_ack_escalations_required",
                escalation_warning_codes,
            )
            self.assertIn(
                "open_followup_resolution_escalation_items_present",
                escalation_warning_codes,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_total_item_count"),
                1,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_open_item_count"),
                1,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_blocked_item_count"),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_pending_ack_item_count"
                ),
                1,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_active_item_count"),
                0,
            )
            escalation_owner_counts = classification.get(
                "backfill_submission_queue_followup_resolution_escalation_owner_counts",
                {},
            )
            self.assertIn("controlled-beta-ops", escalation_owner_counts)
            self.assertEqual(
                escalation_owner_counts["controlled-beta-ops"].get("total_item_count"),
                1,
            )
            self.assertEqual(
                escalation_owner_counts["controlled-beta-ops"].get("pending_ack_item_count"),
                1,
            )
            escalation_rows = classification.get(
                "backfill_submission_queue_followup_resolution_escalation_rows",
                [],
            )
            self.assertEqual(len(escalation_rows), 1)
            self.assertEqual(escalation_rows[0].get("escalation_severity"), "pending_ack")
            self.assertEqual(
                escalation_rows[0].get("escalation_reason_code"),
                "followup_resolution_in_progress_pending_ack",
            )
            self.assertEqual(
                escalation_rows[0].get("escalation_action"),
                "track_submission_linked_acknowledgement_closure",
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_acknowledgement_status"),
                "FOLLOWUP_RESOLUTION_ESCALATION_ACK_PENDING_ACTION_REQUIRED",
            )
            ack_warning_codes = classification.get(
                "backfill_submission_queue_followup_resolution_escalation_acknowledgement_warning_codes",
                [],
            )
            self.assertIn("escalation_ack_pending_operator_acknowledgement", ack_warning_codes)
            self.assertIn("open_escalation_acknowledgement_items_present", ack_warning_codes)
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_acknowledgement_total_item_count"),
                1,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_acknowledgement_open_item_count"),
                1,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_acknowledgement_resolved_acknowledged_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_acknowledgement_pending_ack_item_count"
                ),
                1,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_acknowledgement_blocked_item_count"
                ),
                0,
            )
            ack_owner_counts = classification.get(
                "backfill_submission_queue_followup_resolution_escalation_acknowledgement_owner_counts",
                {},
            )
            self.assertIn("controlled-beta-ops", ack_owner_counts)
            self.assertEqual(
                ack_owner_counts["controlled-beta-ops"].get("pending_ack_item_count"),
                1,
            )
            ack_rows = classification.get(
                "backfill_submission_queue_followup_resolution_escalation_acknowledgement_rows",
                [],
            )
            self.assertEqual(len(ack_rows), 1)
            self.assertEqual(ack_rows[0].get("acknowledgement_status"), "pending_ack")
            self.assertEqual(ack_rows[0].get("acknowledgement_state"), "pending_operator_acknowledgement")
            self.assertEqual(
                ack_rows[0].get("escalation_item_id_gl43"),
                escalation_rows[0].get("escalation_item_id"),
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_throughput_status"),
                "ESCALATION_ACK_THROUGHPUT_BASELINE_INITIALIZED",
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_throughput_warning_codes"),
                [
                    "loop_volume_gap_persists",
                    "open_acknowledgement_items_present",
                    "escalation_ack_pending_operator_acknowledgement",
                    "open_escalation_acknowledgement_items_present",
                ],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_throughput_net_new_resolved_acknowledged_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_throughput_net_new_resolved_submission_loop_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_throughput_net_new_launch_gate_eligible_loop_count"
                ),
                1,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_throughput_unresolved_ack_closed_loop_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_throughput_unresolved_acknowledged_submission_loop_ids"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_throughput_net_new_resolved_submission_loop_ids"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_throughput_net_new_launch_gate_eligible_loop_ids"
                ),
                ["real-text-001"],
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_action_plan_status"),
                "ACTION_PLAN_OPEN",
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_action_plan_warning_codes"),
                [
                    "loop_volume_gap_persists",
                    "open_acknowledgement_items_present",
                    "escalation_ack_pending_operator_acknowledgement",
                    "open_escalation_acknowledgement_items_present",
                    "open_followup_resolution_escalation_action_plan_items_present",
                ],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_total_action_count"
                ),
                1,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_open_action_count"
                ),
                1,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closed_action_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_unresolved_ack_mapping_action_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_recommended_backfill_slot_action_count"
                ),
                1,
            )
            action_plan_rows = classification.get(
                "backfill_submission_queue_followup_resolution_escalation_action_plan_rows",
                [],
            )
            self.assertEqual(len(action_plan_rows), 1)
            self.assertEqual(action_plan_rows[0].get("action_type"), "collect_launch_gate_eligible_real_loop")
            self.assertEqual(action_plan_rows[0].get("required_modality"), "text")
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_action_plan_closure_status"),
                "ACTION_PLAN_CLOSURE_BASELINE_INITIALIZED",
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_action_plan_closure_warning_codes"),
                [
                    "open_followup_resolution_escalation_action_plan_items_present",
                    "loop_volume_gap_persists",
                    "open_acknowledgement_items_present",
                    "escalation_ack_pending_operator_acknowledgement",
                    "open_escalation_acknowledgement_items_present",
                ],
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_action_plan_closure_total_action_count"),
                1,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_action_plan_closure_open_action_count"),
                1,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_action_plan_closure_closed_action_count"),
                0,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_action_plan_closure_carried_open_action_count"),
                0,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_action_plan_closure_net_new_closed_action_count"),
                0,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_action_plan_closure_stale_open_action_count"),
                0,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_action_plan_closure_net_new_launch_gate_eligible_loop_count"),
                1,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_action_plan_closure_open_action_count_delta"),
                1,
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_action_plan_closure_carried_open_action_ids"),
                [],
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_action_plan_closure_net_new_closed_action_ids"),
                [],
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_followup_resolution_escalation_action_plan_closure_net_new_launch_gate_eligible_loop_ids"),
                ["real-text-001"],
            )
            closure_rows = classification.get(
                "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_rows",
                [],
            )
            self.assertEqual(len(closure_rows), 1)
            self.assertEqual(closure_rows[0].get("action_id"), "gl46-slot-001-text")
            self.assertEqual(closure_rows[0].get("closure_state"), "open_new")
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_status"
                ),
                "ACTION_PLAN_CLOSURE_CADENCE_BASELINE_INITIALIZED",
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_warning_codes"
                ),
                [
                    "open_followup_resolution_escalation_action_plan_closure_items_present",
                    "open_followup_resolution_escalation_action_plan_items_present",
                    "loop_volume_gap_persists",
                    "open_acknowledgement_items_present",
                    "escalation_ack_pending_operator_acknowledgement",
                    "open_escalation_acknowledgement_items_present",
                ],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_total_action_count"
                ),
                1,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_open_action_count"
                ),
                1,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_stale_open_action_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_stall_cycle_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_overdue_stalled_cycles_threshold"
                ),
                2,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_refresh_interval_hours"
                ),
                24.0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_state"
                ),
                "CADENCE_BASELINE_INITIALIZED",
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_previous_generated_at_utc"
                ),
                "",
            )
            next_due_utc = classification.get(
                "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_next_refresh_due_utc"
            )
            self.assertTrue(str(next_due_utc).endswith("Z"))
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_due_in_hours"
                ),
                24.0,
            )
            self.assertNotEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_evaluated_at_utc"
                ),
                "",
            )
            cadence_rows = classification.get(
                "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_rows",
                [],
            )
            self.assertEqual(len(cadence_rows), 1)
            self.assertEqual(cadence_rows[0].get("action_id"), "gl46-slot-001-text")
            self.assertEqual(cadence_rows[0].get("closure_state_gl47"), "open_new")
            self.assertEqual(cadence_rows[0].get("cadence_item_status"), "baseline_open")
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_status"
                ),
                "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_MONITORING",
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_warning_codes"
                ),
                [
                    "open_action_plan_closure_cadence_escalation_items_present",
                    "open_followup_resolution_escalation_action_plan_closure_items_present",
                    "open_followup_resolution_escalation_action_plan_items_present",
                    "loop_volume_gap_persists",
                    "open_acknowledgement_items_present",
                    "escalation_ack_pending_operator_acknowledgement",
                    "open_escalation_acknowledgement_items_present",
                ],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_total_item_count"
                ),
                1,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_open_item_count"
                ),
                1,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_blocked_overdue_stalled_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_due_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_monitor_item_count"
                ),
                1,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_cadence_stall_cycle_count_gl48"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_cadence_overdue_stalled_cycles_threshold_gl48"
                ),
                2,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_escalate_after_due_hours"
                ),
                24.0,
            )
            escalation_owner_counts = classification.get(
                "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_owner_counts",
                {},
            )
            self.assertIn("controlled-beta-ops", escalation_owner_counts)
            escalation_rows = classification.get(
                "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_rows",
                [],
            )
            self.assertEqual(len(escalation_rows), 1)
            self.assertEqual(escalation_rows[0].get("action_id_gl48"), "gl46-slot-001-text")
            self.assertEqual(escalation_rows[0].get("escalation_severity"), "baseline_open")
            self.assertEqual(escalation_rows[0].get("escalation_action"), "start_first_refresh_cycle")
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_status"
                ),
                "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_ACTION_REQUIRED",
            )
            gl50_warning_codes = classification.get(
                "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_warning_codes",
                [],
            )
            self.assertIn(
                "open_action_plan_closure_cadence_escalation_acknowledgement_ingestion_items_present",
                gl50_warning_codes,
            )
            self.assertIn("escalation_rows_acknowledgement_loop_mismatch", gl50_warning_codes)
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_total_item_count"
                ),
                1,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_open_item_count"
                ),
                1,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_with_ack_record_item_count"
                ),
                1,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_with_matching_ack_loop_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_with_mismatched_ack_loop_item_count"
                ),
                1,
            )
            self.assertTrue(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_input_present"
                )
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_valid_acknowledgement_count"
                ),
                1,
            )
            gl50_rows = classification.get(
                "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_rows",
                [],
            )
            self.assertEqual(len(gl50_rows), 1)
            self.assertEqual(gl50_rows[0].get("acknowledgement_ingestion_state"), "ack_loop_mismatch")
            self.assertIn(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_status"
                ),
                {
                    "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_BASELINE_INITIALIZED",
                    "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_PROGRESSING",
                    "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_STALLED",
                },
            )
            gl51_warning_codes = classification.get(
                "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_warning_codes",
                [],
            )
            self.assertIn(
                "open_action_plan_closure_cadence_escalation_acknowledgement_ingestion_closure_items_present",
                gl51_warning_codes,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_total_item_count"
                ),
                1,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_open_item_count"
                ),
                1,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_closed_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_previous_open_item_count_gl50"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_carried_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_stale_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_net_new_closed_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_ack_loop_mismatch_open_item_count"
                ),
                1,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_ack_missing_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_missing_handoff_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_net_new_launch_gate_eligible_loop_count"
                ),
                1,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_open_item_count_delta"
                ),
                1,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_carried_open_item_ids"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_net_new_closed_item_ids"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_net_new_launch_gate_eligible_loop_ids"
                ),
                ["real-text-001"],
            )
            gl51_rows = classification.get(
                "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_rows",
                [],
            )
            self.assertEqual(len(gl51_rows), 1)
            self.assertEqual(gl51_rows[0].get("closure_state"), "open_new")
            self.assertIn(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_status"
                ),
                {
                    "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_BASELINE_INITIALIZED",
                    "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ON_SCHEDULE",
                    "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_DUE",
                },
            )
            gl52_warning_codes = classification.get(
                "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_warning_codes",
                [],
            )
            self.assertIn(
                "open_action_plan_closure_cadence_escalation_acknowledgement_ingestion_closure_cadence_items_present",
                gl52_warning_codes,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_total_item_count"
                ),
                1,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_open_item_count"
                ),
                1,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_stale_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_net_new_closed_item_count_gl51"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_net_new_launch_gate_eligible_loop_count_gl51"
                ),
                1,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_stall_cycle_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_overdue_stalled_cycles_threshold"
                ),
                2,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_refresh_interval_hours"
                ),
                24.0,
            )
            self.assertIn(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_state"
                ),
                {"CADENCE_BASELINE_INITIALIZED", "CADENCE_ON_SCHEDULE", "CADENCE_DUE"},
            )
            self.assertIsInstance(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_previous_generated_at_utc"
                ),
                str,
            )
            self.assertNotEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_next_refresh_due_utc"
                ),
                "",
            )
            self.assertGreater(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_due_in_hours"
                ),
                0.0,
            )
            self.assertNotEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_evaluated_at_utc"
                ),
                "",
            )
            gl52_rows = classification.get(
                "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_rows",
                [],
            )
            self.assertEqual(len(gl52_rows), 1)
            self.assertIn(gl52_rows[0].get("cadence_item_status"), {"baseline_open", "on_schedule", "due"})
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_status"
                ),
                "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_MONITORING",
            )
            gl53_warning_codes = classification.get(
                "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_warning_codes",
                [],
            )
            self.assertIn(
                "open_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_items_present",
                gl53_warning_codes,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_total_item_count"
                ),
                1,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_open_item_count"
                ),
                1,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_blocked_overdue_stalled_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_due_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_monitor_item_count"
                ),
                1,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_cadence_stall_cycle_count_gl52"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_cadence_overdue_stalled_cycles_threshold_gl52"
                ),
                2,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_escalate_after_due_hours"
                ),
                24.0,
            )
            gl53_owner_counts = classification.get(
                "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_owner_counts",
                {},
            )
            self.assertIn("controlled-beta-ops", gl53_owner_counts)
            gl53_rows = classification.get(
                "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_rows",
                [],
            )
            self.assertEqual(len(gl53_rows), 1)
            self.assertEqual(gl53_rows[0].get("action_id_gl48"), "gl46-slot-001-text")
            self.assertIn(gl53_rows[0].get("escalation_severity"), {"baseline_open", "on_schedule", "due"})
            self.assertIn(
                gl53_rows[0].get("escalation_action"),
                {"start_first_refresh_cycle", "monitor_until_due", "escalate_due_item"},
            )
            self.assertIn(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_status"
                ),
                {
                    "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_BASELINE_INITIALIZED",
                    "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_PROGRESSING",
                },
            )
            gl54_warning_codes = classification.get(
                "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_warning_codes",
                [],
            )
            self.assertIn(
                "open_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_items_present",
                gl54_warning_codes,
            )
            self.assertIn(
                "open_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_items_present",
                gl54_warning_codes,
            )
            self.assertIn(
                "open_action_plan_closure_cadence_escalation_acknowledgement_ingestion_items_present",
                gl54_warning_codes,
            )
            self.assertIn(
                "escalation_rows_acknowledgement_loop_mismatch",
                gl54_warning_codes,
            )
            self.assertIn(
                "open_action_plan_closure_cadence_escalation_items_present",
                gl54_warning_codes,
            )
            self.assertIn(
                "open_followup_resolution_escalation_action_plan_closure_items_present",
                gl54_warning_codes,
            )
            self.assertIn(
                "open_followup_resolution_escalation_action_plan_items_present",
                gl54_warning_codes,
            )
            self.assertIn("loop_volume_gap_persists", gl54_warning_codes)
            self.assertIn("open_acknowledgement_items_present", gl54_warning_codes)
            self.assertIn(
                "escalation_ack_pending_operator_acknowledgement",
                gl54_warning_codes,
            )
            self.assertIn(
                "open_escalation_acknowledgement_items_present",
                gl54_warning_codes,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_total_item_count"
                ),
                1,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_open_item_count"
                ),
                1,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_previous_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_carried_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_stale_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_net_new_open_item_count"
                ),
                1,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_net_new_closed_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_net_new_closed_backed_by_ack_ingestion_item_count_gl50"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_net_new_closed_without_ack_ingestion_item_count_gl50"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_ack_ingestion_closed_item_count_gl50"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_ack_ingestion_open_item_count_gl50"
                ),
                1,
            )
            gl54_owner_counts = classification.get(
                "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_owner_counts",
                {},
            )
            self.assertIn("controlled-beta-ops", gl54_owner_counts)
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_carried_open_item_ids"
                ),
                [],
            )
            gl54_net_new_open_item_ids = classification.get(
                "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_net_new_open_item_ids",
                [],
            )
            self.assertEqual(len(gl54_net_new_open_item_ids), 1)
            self.assertTrue(str(gl54_net_new_open_item_ids[0]).endswith("gl46-slot-001-text"))
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_net_new_closed_item_ids"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_net_new_closed_backed_by_ack_ingestion_item_ids_gl50"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_net_new_closed_without_ack_ingestion_item_ids_gl50"
                ),
                [],
            )
            gl54_rows = classification.get(
                "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_rows",
                [],
            )
            self.assertEqual(len(gl54_rows), 1)
            self.assertEqual(
                gl54_rows[0].get("closure_progress_state"),
                "net_new_open",
            )
            self.assertTrue(
                str(gl54_rows[0].get("escalation_item_id_gl53", "")).endswith("gl46-slot-001-text")
            )
            self.assertIn(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_status"
                ),
                {
                    "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_BASELINE_INITIALIZED",
                    "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ON_SCHEDULE",
                    "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_DUE",
                },
            )
            gl55_warning_codes = classification.get(
                "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_warning_codes",
                [],
            )
            self.assertIn(
                "open_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_items_present",
                gl55_warning_codes,
            )
            self.assertIn(
                "open_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_items_present",
                gl55_warning_codes,
            )
            self.assertIn(
                "open_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_items_present",
                gl55_warning_codes,
            )
            self.assertIn(
                "open_action_plan_closure_cadence_escalation_acknowledgement_ingestion_items_present",
                gl55_warning_codes,
            )
            self.assertTrue(
                any(
                    code in gl55_warning_codes
                    for code in (
                        "acknowledgement_input_missing",
                        "escalation_ack_pending_operator_acknowledgement",
                    )
                )
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_total_item_count"
                ),
                1,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_open_item_count"
                ),
                1,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_stale_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_net_new_closed_item_count_gl54"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_net_new_closed_backed_by_ack_ingestion_item_count_gl50"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_stall_cycle_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_overdue_stalled_cycles_threshold"
                ),
                2,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_refresh_interval_hours"
                ),
                24.0,
            )
            self.assertIn(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_state"
                ),
                {"CADENCE_BASELINE_INITIALIZED", "CADENCE_ON_SCHEDULE", "CADENCE_DUE"},
            )
            self.assertIsInstance(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_previous_generated_at_utc"
                ),
                str,
            )
            self.assertNotEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_next_refresh_due_utc"
                ),
                "",
            )
            self.assertGreater(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_due_in_hours"
                ),
                0.0,
            )
            self.assertNotEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_evaluated_at_utc"
                ),
                "",
            )
            gl55_rows = classification.get(
                "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_rows",
                [],
            )
            self.assertEqual(len(gl55_rows), 1)
            self.assertIn(gl55_rows[0].get("cadence_item_status"), {"baseline_open", "on_schedule", "due"})
            self.assertTrue(
                str(gl55_rows[0].get("closure_item_id_gl54", "")).endswith("gl46-slot-001-text")
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_status"
                ),
                "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_MONITORING",
            )
            gl56_warning_codes = classification.get(
                "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_warning_codes",
                [],
            )
            self.assertIn(
                "open_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_items_present",
                gl56_warning_codes,
            )
            self.assertIn(
                "open_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_items_present",
                gl56_warning_codes,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_total_item_count"
                ),
                1,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_open_item_count"
                ),
                1,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_blocked_overdue_stalled_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_due_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_monitor_item_count"
                ),
                1,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_cadence_stall_cycle_count_gl55"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_cadence_overdue_stalled_cycles_threshold_gl55"
                ),
                2,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_escalate_after_due_hours"
                ),
                24.0,
            )
            gl56_owner_counts = classification.get(
                "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_owner_counts",
                {},
            )
            self.assertIn("controlled-beta-ops", gl56_owner_counts)
            gl56_rows = classification.get(
                "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_rows",
                [],
            )
            self.assertEqual(len(gl56_rows), 1)
            self.assertIn(
                gl56_rows[0].get("escalation_severity"),
                {"baseline_open", "on_schedule", "monitor"},
            )
            self.assertTrue(
                str(gl56_rows[0].get("escalation_item_id", "")).endswith("gl46-slot-001-text")
            )
            self.assertIn(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_status"
                ),
                {
                    "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_BASELINE_INITIALIZED",
                    "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_PROGRESSING",
                },
            )
            gl57_warning_codes = classification.get(
                "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_warning_codes",
                [],
            )
            self.assertIn(
                "open_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_items_present",
                gl57_warning_codes,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_total_item_count"
                ),
                1,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_open_item_count"
                ),
                1,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_previous_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_carried_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_stale_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_open_item_count"
                ),
                1,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_backed_by_gl54_net_new_closed_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_without_gl54_net_new_closed_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_gl54_net_new_closed_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_gl54_net_new_closed_action_item_count"
                ),
                0,
            )
            gl57_owner_counts = classification.get(
                "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_owner_counts",
                {},
            )
            self.assertIn("controlled-beta-ops", gl57_owner_counts)
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_carried_open_item_ids"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_open_item_ids"
                ),
                ["gl56-escalation-closure-cadence-escalation-gl46-slot-001-text"],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_item_ids"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_backed_by_gl54_net_new_closed_item_ids"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_without_gl54_net_new_closed_item_ids"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_gl54_net_new_closed_item_ids"
                ),
                [],
            )
            gl57_rows = classification.get(
                "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_rows",
                [],
            )
            self.assertEqual(len(gl57_rows), 1)
            self.assertEqual(gl57_rows[0].get("closure_progress_state"), "net_new_open")
            self.assertTrue(
                str(gl57_rows[0].get("closure_item_id", "")).endswith("gl46-slot-001-text")
            )
            self.assertIn(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_status"
                ),
                {
                    "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_BASELINE_INITIALIZED",
                    "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ON_SCHEDULE",
                    "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_DUE",
                },
            )
            gl58_warning_codes = classification.get(
                "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_warning_codes",
                [],
            )
            self.assertIn(
                "open_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_items_present",
                gl58_warning_codes,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_total_item_count"
                ),
                1,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_open_item_count"
                ),
                1,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_stale_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_net_new_closed_item_count_gl57"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_net_new_closed_backed_by_gl54_net_new_closed_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_stall_cycle_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_overdue_stalled_cycles_threshold"
                ),
                2,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_refresh_interval_hours"
                ),
                24.0,
            )
            self.assertIn(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_state"
                ),
                {"CADENCE_BASELINE_INITIALIZED", "CADENCE_ON_SCHEDULE", "CADENCE_DUE"},
            )
            self.assertIsInstance(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_previous_generated_at_utc"
                ),
                str,
            )
            self.assertNotEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_next_refresh_due_utc"
                ),
                "",
            )
            self.assertGreater(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_due_in_hours"
                ),
                0.0,
            )
            self.assertNotEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_evaluated_at_utc"
                ),
                "",
            )
            gl58_rows = classification.get(
                "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_rows",
                [],
            )
            self.assertEqual(len(gl58_rows), 1)
            self.assertEqual(gl58_rows[0].get("closure_progress_state_gl57"), "net_new_open")
            self.assertIn(gl58_rows[0].get("cadence_item_status"), {"baseline_open", "on_schedule", "due"})
            self.assertTrue(
                str(gl58_rows[0].get("closure_item_id_gl57", "")).endswith("gl46-slot-001-text")
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_status"
                ),
                "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_MONITORING",
            )
            gl59_warning_codes = classification.get(
                "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_warning_codes",
                [],
            )
            self.assertIn(
                "open_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_items_present",
                gl59_warning_codes,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_total_item_count"
                ),
                1,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_open_item_count"
                ),
                1,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_blocked_overdue_stalled_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_due_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_monitor_item_count"
                ),
                1,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_cadence_stall_cycle_count_gl58"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_cadence_overdue_stalled_cycles_threshold_gl58"
                ),
                2,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_escalate_after_due_hours"
                ),
                24.0,
            )
            gl59_owner_counts = classification.get(
                "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_owner_counts",
                {},
            )
            self.assertEqual(
                gl59_owner_counts.get("controlled-beta-ops", {}).get("open_item_count"),
                1,
            )
            gl59_rows = classification.get(
                "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_rows",
                [],
            )
            self.assertEqual(len(gl59_rows), 1)
            self.assertIn(gl59_rows[0].get("escalation_severity"), {"baseline_open", "on_schedule", "due"})
            self.assertIn(gl59_rows[0].get("cadence_item_status_gl58"), {"baseline_open", "on_schedule", "due"})
            self.assertIn(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_status"
                ),
                {
                    "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_BASELINE_INITIALIZED",
                    "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_PROGRESSING",
                },
            )
            self.assertIsInstance(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_warning_codes"
                ),
                list,
            )
            self.assertIn(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_total_item_count"
                ),
                {0, 1},
            )
            self.assertIn(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_open_item_count"
                ),
                {0, 1},
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_previous_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_carried_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_stale_open_item_count"
                ),
                0,
            )
            self.assertIn(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_open_item_count"
                ),
                {0, 1},
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_backed_by_gl57_net_new_closed_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_without_gl57_net_new_closed_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_gl57_net_new_closed_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_gl57_net_new_closed_action_item_count"
                ),
                0,
            )
            self.assertIsInstance(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_owner_counts"
                ),
                dict,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_carried_open_item_ids"
                ),
                [],
            )
            self.assertIn(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_open_item_ids"
                ),
                [
                    [],
                    ["gl59-escalation-closure-cadence-escalation-closure-cadence-escalation-gl46-slot-001-text"],
                ],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_item_ids"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_backed_by_gl57_net_new_closed_item_ids"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_without_gl57_net_new_closed_item_ids"
                ),
                [],
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_gl57_net_new_closed_item_ids"
                ),
                [],
            )
            gl60_rows = classification.get(
                "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_rows",
                [],
            )
            self.assertIn(len(gl60_rows), {0, 1})
            self.assertIn(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_status"
                ),
                {
                    "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_BASELINE_INITIALIZED",
                    "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ON_SCHEDULE",
                    "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_DUE",
                },
            )
            self.assertIsInstance(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_warning_codes"
                ),
                list,
            )
            self.assertIn(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_total_item_count"
                ),
                {0, 1},
            )
            self.assertIn(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_open_item_count"
                ),
                {0, 1},
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_stale_open_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_net_new_closed_item_count_gl60"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_net_new_closed_backed_by_gl57_net_new_closed_item_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_stall_cycle_count"
                ),
                0,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_overdue_stalled_cycles_threshold"
                ),
                2,
            )
            self.assertEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_refresh_interval_hours"
                ),
                24.0,
            )
            self.assertIn(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_state"
                ),
                {"CADENCE_BASELINE_INITIALIZED", "CADENCE_ON_SCHEDULE", "CADENCE_DUE"},
            )
            self.assertIsInstance(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_previous_generated_at_utc"
                ),
                str,
            )
            self.assertNotEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_next_refresh_due_utc"
                ),
                "",
            )
            self.assertGreater(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_due_in_hours"
                ),
                0.0,
            )
            self.assertNotEqual(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_evaluated_at_utc"
                ),
                "",
            )
            self.assertIsInstance(
                classification.get(
                    "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_rows"
                ),
                list,
            )
            pending_consumption_rows = classification.get("backfill_submission_consumption_pending_template_rows", [])
            self.assertEqual(len(pending_consumption_rows), 1)
            self.assertEqual(classification.get("backfill_submission_consumption_invalid_submissions"), [])
            self.assertEqual(classification.get("backfill_submission_consumption_unresolved_submissions"), [])
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
            self.assertEqual(classification.get("backfill_submission_consumption_status"), "NO_SUBMISSIONS_PROVIDED")
            self.assertEqual(classification.get("backfill_submission_consumption_template_loop_count"), 1)
            self.assertEqual(classification.get("backfill_submission_consumption_submitted_row_count"), 0)
            self.assertEqual(classification.get("backfill_submission_consumption_consumed_loop_count"), 0)
            self.assertEqual(classification.get("backfill_submission_consumption_pending_template_loop_count"), 1)
            self.assertEqual(classification.get("backfill_submission_consumption_invalid_submission_count"), 0)
            self.assertEqual(classification.get("backfill_submission_consumption_unresolved_submission_count"), 0)
            pending_consumption_rows = classification.get("backfill_submission_consumption_pending_template_rows", [])
            self.assertEqual(len(pending_consumption_rows), 1)
            self.assertEqual(classification.get("backfill_submission_consumption_invalid_submissions"), [])
            self.assertEqual(classification.get("backfill_submission_consumption_unresolved_submissions"), [])
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

    def test_pipeline_replays_collection_with_consumed_manifest_for_ingestion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            loop_manifest = root / "real-loop-manifest.json"
            real_submissions_input = root / "real-submissions-input.json"
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
                    "manifest_id": "gl34-ingestion-replay",
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
                real_submissions_input,
                {
                    "schema_version": "real_trial_backfill_submission_real_inputs.v1",
                    "generated_at_utc": "2026-05-28T00:00:00Z",
                    "owner": "controlled-beta-ops",
                    "submissions": [
                        {
                            "backfill_slot_index": 1,
                            "backfill_action_id": "gl23-slot-001-audio",
                            "modality": "audio",
                            "loop_id": "real-audio-002",
                            "source_system": "pilot-ops",
                            "source_reference": "ticket://real-audio-002",
                            "collected_at_utc": "2026-05-28T00:30:00Z",
                            "review_task_id": "review-real-audio-002",
                            "reviewed_by": "reviewer-b",
                            "reviewed_at_utc": "2026-05-28T00:35:00Z",
                            "review_outcome": "approved",
                            "revisions_before_approval": 0,
                            "reviewer_edit_distance_pct": 10.0,
                            "agent_smoke_result": "passed",
                            "published_without_review": False,
                            "critical_secret_or_pii_leak": False,
                            "high_severity_incident": False,
                            "latency_ms": 650.0,
                            "provider_failure_count": 0,
                            "provider_call_count": 2,
                            "retry_count": 0,
                            "artifact_count": 5,
                            "estimated_cost_usd": 0.25,
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
                    "--backfill-submission-real-inputs",
                    str(real_submissions_input),
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
                    "--backfill-submission-consumption-output",
                    str(root / "real-trial-backfill-submission-consumption-report.json"),
                    "--backfill-submission-consumption-summary-output",
                    str(root / "real-trial-backfill-submission-consumption-summary.md"),
                    "--backfill-submission-consumed-manifest-output",
                    str(root / "manifests" / "real-trial-backfill-submission-manifest.consumed.json"),
                    "--backfill-handoff-output",
                    str(root / "real-trial-backfill-handoff-report.json"),
                    "--backfill-handoff-summary-output",
                    str(root / "real-trial-backfill-handoff-summary.md"),
                    "--backfill-handoff-escalations-output",
                    str(root / "real-trial-backfill-handoff-escalations-report.json"),
                    "--backfill-handoff-escalations-summary-output",
                    str(root / "real-trial-backfill-handoff-escalations-summary.md"),
                    *_gl13_temp_output_args(root),
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
                    "2",
                    "--max-evidence-age-hours",
                    "0",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            self.assertIn("real-trial-loop-collection-replay stdout", completed.stdout)

            launch_payload = json.loads(launch_report.read_text(encoding="utf-8"))
            self.assertEqual(launch_payload.get("decision"), "READY_FOR_CONTROLLED_BETA")

            evidence_pack_payload = json.loads(evidence_pack.read_text(encoding="utf-8"))
            self.assertEqual(evidence_pack_payload.get("launch_decision"), "READY_FOR_CONTROLLED_BETA")
            classification = evidence_pack_payload.get("evidence_classification", {})
            input_sources = evidence_pack_payload.get("input_sources", {})
            self.assertEqual(classification.get("launch_gate_eligible_complete_loop_count"), 2)
            self.assertEqual(
                sorted(classification.get("launch_gate_eligible_complete_modalities", [])),
                ["audio", "text"],
            )
            self.assertTrue(classification.get("backfill_submission_ingestion_replay_applied"))
            self.assertEqual(classification.get("backfill_submission_ingestion_consumed_loop_count"), 1)
            self.assertEqual(classification.get("backfill_submission_ingestion_status"), "CONSUMED_MANIFEST_READY")
            self.assertEqual(classification.get("backfill_execution_remaining_slot_count"), 0)
            self.assertEqual(classification.get("backfill_execution_submission_backed_remaining_slot_count"), 0)
            self.assertEqual(classification.get("backfill_submission_template_status"), "NO_PENDING_ACTIONS")
            self.assertEqual(classification.get("backfill_submission_template_pending_action_count"), 0)
            self.assertEqual(classification.get("backfill_submission_consumption_status"), "CONSUMED_MANIFEST_READY")
            self.assertEqual(classification.get("backfill_submission_consumption_consumed_loop_count"), 1)
            self.assertEqual(classification.get("backfill_submission_consumption_pending_template_loop_count"), 0)
            self.assertEqual(
                classification.get("backfill_submission_throughput_action_plan_status"),
                "ACTION_PLAN_NOT_REQUIRED",
            )
            self.assertEqual(classification.get("backfill_submission_throughput_action_plan_blockers"), [])
            self.assertEqual(classification.get("backfill_submission_throughput_pending_submission_action_count"), 0)
            self.assertEqual(
                classification.get("backfill_submission_throughput_recommended_submission_action_count"),
                0,
            )
            self.assertEqual(classification.get("backfill_submission_throughput_priority_modalities"), [])
            self.assertEqual(classification.get("backfill_submission_throughput_recommended_submission_actions"), [])
            self.assertEqual(
                classification.get("backfill_submission_throughput_submission_consumption_status"),
                "CONSUMED_MANIFEST_READY",
            )
            self.assertEqual(classification.get("backfill_submission_throughput_submission_template_loop_count"), 1)
            self.assertEqual(
                classification.get("backfill_submission_throughput_submission_pending_template_loop_count"),
                0,
            )
            self.assertEqual(classification.get("backfill_submission_throughput_submission_invalid_count"), 0)
            self.assertEqual(classification.get("backfill_submission_throughput_submission_unresolved_count"), 0)
            self.assertEqual(classification.get("backfill_submission_queue_status"), "QUEUE_NOT_REQUIRED")
            self.assertEqual(classification.get("backfill_submission_queue_total_item_count"), 0)
            self.assertEqual(classification.get("backfill_submission_queue_pending_item_count"), 0)
            self.assertEqual(classification.get("backfill_submission_queue_blocked_item_count"), 0)
            self.assertEqual(classification.get("backfill_submission_queue_items"), [])
            self.assertEqual(classification.get("backfill_submission_queue_completion_status"), "COMPLETION_NOT_REQUIRED")
            self.assertEqual(
                classification.get("backfill_submission_queue_completion_progress_status"),
                "COMPLETION_NOT_REQUIRED",
            )
            self.assertEqual(
                classification.get("backfill_submission_queue_cycle_verification_status"),
                "CYCLE_NOT_REQUIRED",
            )
            self.assertEqual(classification.get("backfill_submission_queue_completion_submitted_item_count"), 0)
            self.assertEqual(classification.get("backfill_submission_queue_completion_closed_item_count"), 0)
            self.assertEqual(classification.get("backfill_submission_queue_completion_open_item_count"), 0)
            self.assertTrue(classification.get("backfill_submission_queue_cycle_net_new_movement_verified"))
            self.assertEqual(classification.get("backfill_submission_queue_cycle_throughput_net_new_loop_count"), 1)
            self.assertEqual(classification.get("backfill_submission_queue_completion_transition_records"), [])
            self.assertTrue(input_sources.get("backfill_submission_ingestion_replay_applied"))
            self.assertEqual(input_sources.get("backfill_submission_ingestion_consumed_loop_count"), 1)
            self.assertEqual(input_sources.get("backfill_submission_ingestion_status"), "CONSUMED_MANIFEST_READY")
            replay_paths = input_sources.get("backfill_submission_ingestion_replay_manifest_paths", [])
            self.assertEqual(len(replay_paths), 1)
            self.assertTrue(str(replay_paths[0]).endswith("real-trial-backfill-submission-manifest.consumed.json"))

    def test_pipeline_holds_when_real_manifest_has_gl31_template_placeholders(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            loop_manifest = root / "real-loop-manifest-template-placeholders.json"
            release_report = root / "release-switch.json"
            current_status = root / "CURRENT_STATUS.md"
            agent_smoke = root / "agent-smoke.json"
            doc_sync = root / "doc-sync.json"
            ops_readiness = root / "ops-readiness.json"
            launch_report = root / "launch-readiness-report.json"
            evidence_pack = root / "real-trial-launch-evidence-pack.json"

            row = _loop_row(
                loop_id="real-text-template-001",
                modality="text",
                evidence_origin="real",
                launch_gate_eligible=True,
            )
            row["source_system"] = "TEMPLATE_REQUIRED_REPLACE_WITH_REAL_SOURCE_SYSTEM"
            row["source_reference"] = "TEMPLATE_REQUIRED_REPLACE_WITH_REAL_SOURCE_REFERENCE"
            row["collected_at_utc"] = "TEMPLATE_REQUIRED_REPLACE_WITH_UTC_TIMESTAMP"
            row["review_task_id"] = "TEMPLATE_REQUIRED_REPLACE_WITH_REVIEW_TASK_ID"
            row["reviewed_by"] = "TEMPLATE_REQUIRED_REPLACE_WITH_REVIEWER"
            row["reviewed_at_utc"] = "TEMPLATE_REQUIRED_REPLACE_WITH_UTC_TIMESTAMP"

            _write_json(
                loop_manifest,
                {
                    "manifest_id": "gl32-template-placeholder-block",
                    "loops": [row],
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
                    *_gl13_temp_output_args(root),
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
            self.assertIn("decision=HOLD", completed.stdout)

            launch_payload = json.loads(launch_report.read_text(encoding="utf-8"))
            self.assertEqual(launch_payload.get("decision"), "HOLD")
            failed_checks = launch_payload.get("failed_checks", [])
            self.assertIn("trial_real_evidence_source_trace_complete", failed_checks)
            self.assertIn("trial_real_evidence_review_trace_complete", failed_checks)
            self.assertIn("trial_real_evidence_template_placeholders_replaced", failed_checks)
            evidence_pack_payload = json.loads(evidence_pack.read_text(encoding="utf-8"))
            classification = evidence_pack_payload.get("evidence_classification", {})
            self.assertEqual(classification.get("launch_gate_eligible_complete_loop_count"), 0)
            self.assertEqual(classification.get("real_evidence_template_placeholder_loop_count"), 1)
            self.assertEqual(classification.get("real_evidence_template_placeholder_field_count"), 6)
            placeholder_records = classification.get("real_evidence_template_placeholder_records", [])
            self.assertEqual(len(placeholder_records), 1)
            self.assertEqual(placeholder_records[0].get("loop_id"), "real-text-template-001")
            self.assertIn("real_loop_template_placeholders_not_replaced", classification.get("collection_blockers", []))


if __name__ == "__main__":
    unittest.main()





