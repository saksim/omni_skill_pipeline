from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "launch_gate.py"


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _release_report(decision: str = "GO") -> dict[str, object]:
    return {
        "schema_version": "test.release_switch.v1",
        "decision": decision,
        "gate_rows": [{"name": "strict_release_gate", "status": "pass"}],
    }


def _trial_metrics_report(*, loops: int, modalities: int) -> dict[str, object]:
    return {
        "manifest_id": "launch-readiness-test",
        "trial_metrics": {
            "complete_loop_count": loops,
            "complete_modalities": ["modality-%s" % index for index in range(modalities)],
            "launch_gate_evidence": {
                "complete_loop_count": loops,
                "complete_modalities": ["modality-%s" % index for index in range(modalities)],
                "eligible_loop_count": loops,
                "ineligible_loop_count": 0,
                "unlabeled_loop_count": 0,
                "real_evidence_missing_source_trace_count": 0,
                "real_evidence_missing_review_trace_count": 0,
                "evidence_origin_counts": {"real": loops},
                "ineligible_reason_counts": {},
            },
            "provider_runtime": {
                "provider_failure_rate": 0.0,
            },
            "cost_placeholder": {
                "approved_skill_count": loops,
                "approved_skill_missing_cost_count": 0,
                "accepted_by_operator": True,
            },
            "safety": {
                "unreviewed_published_count": 0,
                "critical_secret_or_pii_leak_count": 0,
                "high_severity_incident_count": 0,
            },
            "review_quality": {
                "approval_rate_after_one_revision": 1.0,
                "agent_smoke_success_rate": 1.0,
            },
        },
        "success_criteria": {
            "status": "pass" if loops >= 10 and modalities >= 4 else "fail",
            "conditions": [
                {"id": "release_run_go", "status": "pass", "actual": "GO", "expected": "GO"},
                {
                    "id": "loop_volume_and_modality_coverage",
                    "status": "pass" if loops >= 10 and modalities >= 4 else "fail",
                    "actual": {"complete_loops": loops, "modalities": modalities},
                    "expected": {"minimum_complete_loops": 10, "minimum_modalities": 4},
                },
                {
                    "id": "launch_gate_eligible_loop_volume_and_modality_coverage",
                    "status": "pass" if loops >= 10 and modalities >= 4 else "fail",
                    "actual": {"complete_loops": loops, "modalities": modalities},
                    "expected": {
                        "minimum_complete_loops": 10,
                        "minimum_modalities": 4,
                        "evidence_origin": "real",
                    },
                },
                {
                    "id": "loop_evidence_origin_labeled",
                    "status": "pass",
                    "actual": {"unlabeled_loop_count": 0},
                    "expected": {"unlabeled_loop_count": 0},
                },
                {
                    "id": "real_evidence_source_trace_complete",
                    "status": "pass",
                    "actual": {"missing_source_trace_count": 0},
                    "expected": {"missing_source_trace_count": 0},
                },
                {
                    "id": "real_evidence_review_trace_complete",
                    "status": "pass",
                    "actual": {"missing_review_trace_count": 0},
                    "expected": {"missing_review_trace_count": 0},
                },
                {
                    "id": "real_evidence_template_placeholders_replaced",
                    "status": "pass",
                    "actual": {"placeholder_loop_count": 0, "placeholder_field_count": 0},
                    "expected": {"placeholder_loop_count": 0, "placeholder_field_count": 0},
                },
                {"id": "no_unreviewed_publication", "status": "pass", "actual": 0, "expected": 0},
                {"id": "no_critical_secret_or_pii_leak", "status": "pass", "actual": 0, "expected": 0},
                {"id": "no_high_severity_trial_incident", "status": "pass", "actual": 0, "expected": 0},
                {"id": "reviewer_approval_rate", "status": "pass", "actual": 1.0, "expected_min": 0.8},
                {"id": "median_reviewer_edit_distance", "status": "pass", "actual": 20.0, "expected_max": 25.0},
                {"id": "agent_smoke_success_rate", "status": "pass", "actual": 1.0, "expected_min": 0.8},
                {"id": "provider_failure_rate", "status": "pass", "actual": 0.0, "expected_max": 0.05},
                {
                    "id": "cost_per_accepted_skill",
                    "status": "pass",
                    "actual": {
                        "approved_skill_count": loops,
                        "approved_skill_missing_cost_count": 0,
                        "accepted_by_operator": True,
                    },
                    "expected": {
                        "approved_skill_count_gt": 0,
                        "approved_skill_missing_cost_count": 0,
                        "accepted_by_operator": True,
                    },
                },
            ],
        },
        "overall_status": "pass" if loops >= 10 and modalities >= 4 else "fail",
    }


def _agent_smoke_record(agent: str, *, status: str = "agent_smoke_passed") -> dict[str, object]:
    record: dict[str, object] = {
        "skill_id": "skill-1",
        "agent": agent,
        "status": status,
        "metrics_agent_smoke_result": "not_run" if status == "not_run" else "passed",
        "reason": "%s selected expected skill." % agent,
        "trigger_prompt": "Use the approved skill to produce the expected runbook.",
        "expected_skill_selection": "skill-1",
        "expected_task_output": "Runbook with validation checklist.",
        "selected_skill": "" if status == "not_run" else "skill-1",
        "observed_task_output": "" if status == "not_run" else "Runbook with validation checklist produced.",
        "failure_code": "",
    }
    if status == "not_run":
        record["reason"] = "%s environment unavailable in this test window." % agent
    return record


def _agent_smoke_report(*, complete_matrix: bool = True, unavailable_agents: bool = False) -> dict[str, object]:
    agents = ["codex", "claude-code", "opencode"] if complete_matrix else ["codex"]
    records = []
    for agent in agents:
        status = "not_run" if unavailable_agents and agent in {"claude-code", "opencode"} else "agent_smoke_passed"
        records.append(_agent_smoke_record(agent, status=status))
    return {
        "schema_version": "test.agent_smoke.v1",
        "records": records,
    }


def _trial_run_report_with_real_export(skill_id: str) -> dict[str, object]:
    skill_dir = Path("exports") / "real-text-001" / "skills" / "portable" / skill_id
    return {
        "samples": [
            {
                "sample_id": "real-text-001",
                "loop_metrics": {
                    "loop_id": "real-text-001",
                    "status": "complete",
                    "modality": "text",
                    "evidence_origin": "real",
                    "launch_gate_eligible": True,
                },
                "export_results": [
                    {
                        "target": "portable",
                        "skill_path": str(skill_dir / "SKILL.md"),
                        "package_path": str(skill_dir / "agent_skill_package.json"),
                    }
                ],
            }
        ]
    }


def _security_report() -> dict[str, object]:
    return {
        "schema_version": "test.security_gate.v1",
        "status": "pass",
        "failure_codes": [],
    }


def _doc_sync_report(status: str = "pass") -> dict[str, object]:
    return {
        "generated_at_utc": "2026-05-25T00:00:00+00:00",
        "status": status,
        "failed_count": 0 if status == "pass" else 1,
    }


def _operations_readiness_report(status: str = "pass") -> dict[str, object]:
    return {
        "schema_version": "operations_readiness.v1",
        "overall_status": status,
        "check_count": 5,
        "pass_count": 5 if status == "pass" else 4,
        "fail_count": 0 if status == "pass" else 1,
    }


def _secrets_readiness_report(status: str = "SECRETS_READINESS_READY") -> dict[str, object]:
    fail_count = 0 if status == "SECRETS_READINESS_READY" else 1
    return {
        "schema_version": "secrets_readiness.v1",
        "status": status,
        "check_count": 5,
        "pass_count": 5 - fail_count,
        "fail_count": fail_count,
        "failed_checks": [] if fail_count == 0 else ["production_secret_manager_evidence"],
    }


def _run_gate(root: Path, *extra_args: str) -> dict[str, object]:
    output_path = root / "launch-readiness-report.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--release-switch-report",
            str(root / "release.json"),
            "--current-status-doc",
            str(root / "CURRENT_STATUS.md"),
            "--trial-metrics-report",
            str(root / "trial-metrics.json"),
            "--controlled-trial-run-report",
            str(root / "trial-run.json"),
            "--agent-smoke-report",
            str(root / "agent-smoke.json"),
            "--security-gate-report",
            str(root / "security.json"),
            "--doc-sync-report",
            str(root / "doc-sync.json"),
            "--operations-readiness-report",
            str(root / "ops-readiness.json"),
            "--secrets-readiness-report",
            str(root / "secrets-readiness.json"),
            "--no-run-doc-sync",
            "--max-evidence-age-hours",
            "0",
            "--output",
            str(output_path),
            "--summary-output",
            "-",
            *extra_args,
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr + completed.stdout)
    return json.loads(output_path.read_text(encoding="utf-8"))


class LaunchReadinessGateScriptTests(unittest.TestCase):
    def test_current_repository_evidence_holds_for_trial_coverage(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--output",
                "-",
                "--summary-output",
                "-",
                "--max-evidence-age-hours",
                "0",
                "--print-json",
            ],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Launch readiness decision=HOLD", completed.stdout)
        self.assertIn("trial_loop_volume_and_modality_coverage", completed.stdout)

    def test_fixture_can_reach_controlled_beta_when_all_evidence_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "CURRENT_STATUS.md").write_text("Release switch decision: `GO`\n", encoding="utf-8")
            _write_json(root / "release.json", _release_report())
            _write_json(root / "trial-metrics.json", _trial_metrics_report(loops=10, modalities=4))
            _write_json(root / "trial-run.json", {"samples": []})
            _write_json(root / "agent-smoke.json", _agent_smoke_report())
            _write_json(root / "security.json", _security_report())
            _write_json(root / "doc-sync.json", _doc_sync_report())
            _write_json(root / "ops-readiness.json", _operations_readiness_report())

            report = _run_gate(root)

            self.assertEqual(report.get("decision"), "READY_FOR_CONTROLLED_BETA")
            self.assertEqual(report.get("failed_checks"), [])

    def test_incomplete_agent_smoke_matrix_keeps_hold(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "CURRENT_STATUS.md").write_text("Release switch decision: `GO`\n", encoding="utf-8")
            _write_json(root / "release.json", _release_report())
            _write_json(root / "trial-metrics.json", _trial_metrics_report(loops=10, modalities=4))
            _write_json(root / "trial-run.json", {"samples": []})
            _write_json(root / "agent-smoke.json", _agent_smoke_report(complete_matrix=False))
            _write_json(root / "security.json", _security_report())
            _write_json(root / "doc-sync.json", _doc_sync_report())
            _write_json(root / "ops-readiness.json", _operations_readiness_report())

            report = _run_gate(root)

            self.assertEqual(report.get("decision"), "HOLD")
            self.assertIn("agent_smoke_matrix_coverage", report.get("failed_checks", []))
            matrix_check = next(
                check for check in report.get("checks", []) if check.get("id") == "agent_smoke_matrix_coverage"
            )
            self.assertEqual(matrix_check.get("status"), "fail")
            self.assertEqual(matrix_check.get("actual", {}).get("missing_cell_count"), 2)

    def test_real_export_without_agent_smoke_records_keeps_hold(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "CURRENT_STATUS.md").write_text("Release switch decision: `GO`\n", encoding="utf-8")
            _write_json(root / "release.json", _release_report())
            _write_json(root / "trial-metrics.json", _trial_metrics_report(loops=10, modalities=4))
            _write_json(root / "trial-run.json", _trial_run_report_with_real_export("real-text-skill"))
            _write_json(root / "agent-smoke.json", _agent_smoke_report())
            _write_json(root / "security.json", _security_report())
            _write_json(root / "doc-sync.json", _doc_sync_report())
            _write_json(root / "ops-readiness.json", _operations_readiness_report())

            report = _run_gate(root)

            self.assertEqual(report.get("decision"), "HOLD")
            self.assertIn("agent_smoke_matrix_coverage", report.get("failed_checks", []))
            matrix_check = next(
                check for check in report.get("checks", []) if check.get("id") == "agent_smoke_matrix_coverage"
            )
            self.assertEqual(matrix_check.get("status"), "fail")
            self.assertIn("real-text-skill", matrix_check.get("actual", {}).get("required_skill_ids", []))
            self.assertEqual(matrix_check.get("actual", {}).get("missing_cell_count"), 3)
            self.assertEqual(
                {cell.get("agent") for cell in matrix_check.get("actual", {}).get("missing_cells", [])},
                {"codex", "claude-code", "opencode"},
            )

    def test_not_run_agent_cells_complete_matrix_without_lowering_executed_success_rate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "CURRENT_STATUS.md").write_text("Release switch decision: `GO`\n", encoding="utf-8")
            _write_json(root / "release.json", _release_report())
            _write_json(root / "trial-metrics.json", _trial_metrics_report(loops=10, modalities=4))
            _write_json(root / "trial-run.json", {"samples": []})
            _write_json(root / "agent-smoke.json", _agent_smoke_report(unavailable_agents=True))
            _write_json(root / "security.json", _security_report())
            _write_json(root / "doc-sync.json", _doc_sync_report())
            _write_json(root / "ops-readiness.json", _operations_readiness_report())

            report = _run_gate(root)

            self.assertEqual(report.get("decision"), "READY_FOR_CONTROLLED_BETA")
            success_check = next(
                check for check in report.get("checks", []) if check.get("id") == "agent_smoke_success_rate"
            )
            matrix_check = next(
                check for check in report.get("checks", []) if check.get("id") == "agent_smoke_matrix_coverage"
            )
            self.assertEqual(success_check.get("status"), "pass")
            self.assertEqual(success_check.get("actual", {}).get("executable_record_count"), 1)
            self.assertEqual(success_check.get("actual", {}).get("not_run_record_count"), 2)
            self.assertEqual(matrix_check.get("status"), "pass")

    def test_require_real_agent_smoke_blocks_not_run_cells(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "CURRENT_STATUS.md").write_text("Release switch decision: `GO`\n", encoding="utf-8")
            _write_json(root / "release.json", _release_report())
            _write_json(root / "trial-metrics.json", _trial_metrics_report(loops=10, modalities=4))
            _write_json(root / "trial-run.json", {"samples": []})
            _write_json(root / "agent-smoke.json", _agent_smoke_report(unavailable_agents=True))
            _write_json(root / "security.json", _security_report())
            _write_json(root / "doc-sync.json", _doc_sync_report())
            _write_json(root / "ops-readiness.json", _operations_readiness_report())

            report = _run_gate(root, "--require-real-agent-smoke")

            self.assertEqual(report.get("decision"), "HOLD")
            self.assertIn("agent_smoke_real_evidence", report.get("failed_checks", []))
            real_check = next(
                check for check in report.get("checks", []) if check.get("id") == "agent_smoke_real_evidence"
            )
            self.assertEqual(real_check.get("status"), "fail")
            self.assertEqual(
                real_check.get("actual", {}).get("real_run_status"),
                "AGENT_SMOKE_REAL_EVIDENCE_INCOMPLETE",
            )
            self.assertEqual(real_check.get("actual", {}).get("agents_passed"), 1)
            self.assertEqual(
                {cell.get("agent") for cell in real_check.get("actual", {}).get("non_passed_cells", [])},
                {"claude-code", "opencode"},
            )

    def test_require_real_agent_smoke_passes_when_all_agents_passed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "CURRENT_STATUS.md").write_text("Release switch decision: `GO`\n", encoding="utf-8")
            _write_json(root / "release.json", _release_report())
            _write_json(root / "trial-metrics.json", _trial_metrics_report(loops=10, modalities=4))
            _write_json(root / "trial-run.json", {"samples": []})
            _write_json(root / "agent-smoke.json", _agent_smoke_report())
            _write_json(root / "security.json", _security_report())
            _write_json(root / "doc-sync.json", _doc_sync_report())
            _write_json(root / "ops-readiness.json", _operations_readiness_report())

            report = _run_gate(root, "--require-real-agent-smoke")

            self.assertEqual(report.get("decision"), "READY_FOR_CONTROLLED_BETA")
            real_check = next(
                check for check in report.get("checks", []) if check.get("id") == "agent_smoke_real_evidence"
            )
            self.assertEqual(real_check.get("status"), "pass")
            self.assertEqual(
                real_check.get("actual", {}).get("real_run_status"),
                "AGENT_SMOKE_REAL_EVIDENCE_READY",
            )
            self.assertEqual(real_check.get("actual", {}).get("agents_passed"), 3)

    def test_missing_security_evidence_keeps_hold(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "CURRENT_STATUS.md").write_text("Release switch decision: `GO`\n", encoding="utf-8")
            _write_json(root / "release.json", _release_report())
            payload = _trial_metrics_report(loops=10, modalities=4)
            payload["success_criteria"] = {"status": "pass", "conditions": []}
            _write_json(root / "trial-metrics.json", payload)
            _write_json(root / "trial-run.json", {"samples": []})
            _write_json(root / "agent-smoke.json", _agent_smoke_report())
            _write_json(root / "doc-sync.json", _doc_sync_report())
            _write_json(root / "ops-readiness.json", _operations_readiness_report())

            report = _run_gate(root)

            self.assertEqual(report.get("decision"), "HOLD")
            self.assertIn("security_gate_evidence", report.get("failed_checks", []))

    def test_missing_doc_sync_evidence_keeps_hold(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "CURRENT_STATUS.md").write_text("Release switch decision: `GO`\n", encoding="utf-8")
            _write_json(root / "release.json", _release_report())
            _write_json(root / "trial-metrics.json", _trial_metrics_report(loops=10, modalities=4))
            _write_json(root / "trial-run.json", {"samples": []})
            _write_json(root / "agent-smoke.json", _agent_smoke_report())
            _write_json(root / "security.json", _security_report())
            _write_json(root / "ops-readiness.json", _operations_readiness_report())

            report = _run_gate(root)

            self.assertEqual(report.get("decision"), "HOLD")
            self.assertIn("doc_sync_status", report.get("failed_checks", []))

    def test_dry_run_marker_keeps_hold(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "CURRENT_STATUS.md").write_text("Release switch decision: `GO`\n", encoding="utf-8")
            _write_json(root / "release.json", {**_release_report(), "command": "python release.py --dry-run"})
            _write_json(root / "trial-metrics.json", _trial_metrics_report(loops=10, modalities=4))
            _write_json(root / "trial-run.json", {"samples": []})
            _write_json(root / "agent-smoke.json", _agent_smoke_report())
            _write_json(root / "security.json", _security_report())
            _write_json(root / "doc-sync.json", _doc_sync_report())
            _write_json(root / "ops-readiness.json", _operations_readiness_report())

            report = _run_gate(root)

            self.assertEqual(report.get("decision"), "HOLD")
            self.assertIn("no_dry_run_relaxed_or_skipped_evidence", report.get("failed_checks", []))

    def test_fixture_only_trial_metrics_keeps_hold_for_launch_gate_eligible_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "CURRENT_STATUS.md").write_text("Release switch decision: `GO`\n", encoding="utf-8")
            _write_json(root / "release.json", _release_report())
            trial_metrics = _trial_metrics_report(loops=10, modalities=4)
            trial_metrics["trial_metrics"]["launch_gate_evidence"] = {
                "complete_loop_count": 0,
                "complete_modalities": [],
                "eligible_loop_count": 0,
                "ineligible_loop_count": 10,
                "unlabeled_loop_count": 0,
                "evidence_origin_counts": {"fixture": 10},
                "ineligible_reason_counts": {"fixture_evidence_not_launch_gate_eligible": 10},
            }
            for condition in trial_metrics["success_criteria"]["conditions"]:
                if condition.get("id") == "launch_gate_eligible_loop_volume_and_modality_coverage":
                    condition["status"] = "fail"
                    condition["actual"] = {"complete_loops": 0, "modalities": 0}
            _write_json(root / "trial-metrics.json", trial_metrics)
            _write_json(root / "trial-run.json", {"samples": []})
            _write_json(root / "agent-smoke.json", _agent_smoke_report())
            _write_json(root / "security.json", _security_report())
            _write_json(root / "doc-sync.json", _doc_sync_report())
            _write_json(root / "ops-readiness.json", _operations_readiness_report())

            report = _run_gate(root)

            self.assertEqual(report.get("decision"), "HOLD")
            self.assertIn("trial_loop_volume_and_modality_coverage", report.get("failed_checks", []))

    def test_missing_real_evidence_source_trace_keeps_hold(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "CURRENT_STATUS.md").write_text("Release switch decision: `GO`\n", encoding="utf-8")
            _write_json(root / "release.json", _release_report())
            trial_metrics = _trial_metrics_report(loops=10, modalities=4)
            trial_metrics["trial_metrics"]["launch_gate_evidence"]["real_evidence_missing_source_trace_count"] = 2
            for condition in trial_metrics["success_criteria"]["conditions"]:
                if condition.get("id") == "real_evidence_source_trace_complete":
                    condition["status"] = "fail"
                    condition["actual"] = {"missing_source_trace_count": 2}
            _write_json(root / "trial-metrics.json", trial_metrics)
            _write_json(root / "trial-run.json", {"samples": []})
            _write_json(root / "agent-smoke.json", _agent_smoke_report())
            _write_json(root / "security.json", _security_report())
            _write_json(root / "doc-sync.json", _doc_sync_report())
            _write_json(root / "ops-readiness.json", _operations_readiness_report())

            report = _run_gate(root)

            self.assertEqual(report.get("decision"), "HOLD")
            self.assertIn("trial_real_evidence_source_trace_complete", report.get("failed_checks", []))

    def test_missing_real_evidence_review_trace_keeps_hold(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "CURRENT_STATUS.md").write_text("Release switch decision: `GO`\n", encoding="utf-8")
            _write_json(root / "release.json", _release_report())
            trial_metrics = _trial_metrics_report(loops=10, modalities=4)
            trial_metrics["trial_metrics"]["launch_gate_evidence"]["real_evidence_missing_review_trace_count"] = 2
            for condition in trial_metrics["success_criteria"]["conditions"]:
                if condition.get("id") == "real_evidence_review_trace_complete":
                    condition["status"] = "fail"
                    condition["actual"] = {"missing_review_trace_count": 2}
            _write_json(root / "trial-metrics.json", trial_metrics)
            _write_json(root / "trial-run.json", {"samples": []})
            _write_json(root / "agent-smoke.json", _agent_smoke_report())
            _write_json(root / "security.json", _security_report())
            _write_json(root / "doc-sync.json", _doc_sync_report())
            _write_json(root / "ops-readiness.json", _operations_readiness_report())

            report = _run_gate(root)

            self.assertEqual(report.get("decision"), "HOLD")
            self.assertIn("trial_real_evidence_review_trace_complete", report.get("failed_checks", []))

    def test_unreplaced_real_evidence_template_placeholders_keep_hold(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "CURRENT_STATUS.md").write_text("Release switch decision: `GO`\n", encoding="utf-8")
            _write_json(root / "release.json", _release_report())
            trial_metrics = _trial_metrics_report(loops=10, modalities=4)
            trial_metrics["trial_metrics"]["launch_gate_evidence"]["real_evidence_template_placeholder_loop_count"] = 2
            trial_metrics["trial_metrics"]["launch_gate_evidence"]["real_evidence_template_placeholder_field_count"] = 12
            for condition in trial_metrics["success_criteria"]["conditions"]:
                if condition.get("id") == "real_evidence_template_placeholders_replaced":
                    condition["status"] = "fail"
                    condition["actual"] = {"placeholder_loop_count": 2, "placeholder_field_count": 12}
            _write_json(root / "trial-metrics.json", trial_metrics)
            _write_json(root / "trial-run.json", {"samples": []})
            _write_json(root / "agent-smoke.json", _agent_smoke_report())
            _write_json(root / "security.json", _security_report())
            _write_json(root / "doc-sync.json", _doc_sync_report())
            _write_json(root / "ops-readiness.json", _operations_readiness_report())

            report = _run_gate(root)

            self.assertEqual(report.get("decision"), "HOLD")
            self.assertIn("trial_real_evidence_template_placeholders_replaced", report.get("failed_checks", []))

    def test_missing_operations_readiness_evidence_keeps_hold(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "CURRENT_STATUS.md").write_text("Release switch decision: `GO`\n", encoding="utf-8")
            _write_json(root / "release.json", _release_report())
            _write_json(root / "trial-metrics.json", _trial_metrics_report(loops=10, modalities=4))
            _write_json(root / "trial-run.json", {"samples": []})
            _write_json(root / "agent-smoke.json", _agent_smoke_report())
            _write_json(root / "security.json", _security_report())
            _write_json(root / "doc-sync.json", _doc_sync_report())

            report = _run_gate(root)

            self.assertEqual(report.get("decision"), "HOLD")
            self.assertIn("operations_readiness_evidence", report.get("failed_checks", []))

    def test_require_secrets_readiness_missing_evidence_keeps_hold(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "CURRENT_STATUS.md").write_text("Release switch decision: `GO`\n", encoding="utf-8")
            _write_json(root / "release.json", _release_report())
            _write_json(root / "trial-metrics.json", _trial_metrics_report(loops=10, modalities=4))
            _write_json(root / "trial-run.json", {"samples": []})
            _write_json(root / "agent-smoke.json", _agent_smoke_report())
            _write_json(root / "security.json", _security_report())
            _write_json(root / "doc-sync.json", _doc_sync_report())
            _write_json(root / "ops-readiness.json", _operations_readiness_report())

            report = _run_gate(root, "--require-secrets-readiness")

            self.assertEqual(report.get("decision"), "HOLD")
            self.assertIn("secrets_readiness_evidence", report.get("failed_checks", []))
            self.assertIn("secrets_readiness_status", report.get("failed_checks", []))

    def test_require_secrets_readiness_failed_report_keeps_hold(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "CURRENT_STATUS.md").write_text("Release switch decision: `GO`\n", encoding="utf-8")
            _write_json(root / "release.json", _release_report())
            _write_json(root / "trial-metrics.json", _trial_metrics_report(loops=10, modalities=4))
            _write_json(root / "trial-run.json", {"samples": []})
            _write_json(root / "agent-smoke.json", _agent_smoke_report())
            _write_json(root / "security.json", _security_report())
            _write_json(root / "doc-sync.json", _doc_sync_report())
            _write_json(root / "ops-readiness.json", _operations_readiness_report())
            _write_json(root / "secrets-readiness.json", _secrets_readiness_report("SECRETS_READINESS_BLOCKED"))

            report = _run_gate(root, "--require-secrets-readiness")

            self.assertEqual(report.get("decision"), "HOLD")
            self.assertIn("secrets_readiness_status", report.get("failed_checks", []))
            check = next(check for check in report.get("checks", []) if check.get("id") == "secrets_readiness_status")
            self.assertEqual(check.get("actual", {}).get("status"), "SECRETS_READINESS_BLOCKED")

    def test_require_secrets_readiness_passes_with_ready_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "CURRENT_STATUS.md").write_text("Release switch decision: `GO`\n", encoding="utf-8")
            _write_json(root / "release.json", _release_report())
            _write_json(root / "trial-metrics.json", _trial_metrics_report(loops=10, modalities=4))
            _write_json(root / "trial-run.json", {"samples": []})
            _write_json(root / "agent-smoke.json", _agent_smoke_report())
            _write_json(root / "security.json", _security_report())
            _write_json(root / "doc-sync.json", _doc_sync_report())
            _write_json(root / "ops-readiness.json", _operations_readiness_report())
            _write_json(root / "secrets-readiness.json", _secrets_readiness_report())

            report = _run_gate(root, "--require-secrets-readiness")

            self.assertEqual(report.get("decision"), "READY_FOR_CONTROLLED_BETA")
            check = next(check for check in report.get("checks", []) if check.get("id") == "secrets_readiness_status")
            self.assertEqual(check.get("status"), "pass")


if __name__ == "__main__":
    unittest.main()
