from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "agent_smoke.py"


class AgentSmokeRecordScriptTests(unittest.TestCase):
    def test_script_records_passed_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            report_path = tmp_path / "agent-smoke-report.json"

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--report",
                    str(report_path),
                    "--skill-id",
                    "trial-skill-001",
                    "--agent",
                    "codex",
                    "--status",
                    "agent_smoke_passed",
                    "--reason",
                    "Selected expected skill and produced expected checklist.",
                    "--trigger-prompt",
                    "Use the incident runbook skill to triage the sample issue.",
                    "--expected-skill-selection",
                    "incident-runbook-skill",
                    "--expected-task-output",
                    "Checklist with rollback and validation steps.",
                    "--selected-skill",
                    "incident-runbook-skill",
                    "--observed-task-output",
                    "Produced checklist with rollback and validation.",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("status=agent_smoke_passed", completed.stdout)

            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report.get("schema_version"), "cbt12.agent_smoke_report.v1")
            self.assertEqual(report.get("record_count"), 1)
            records = report.get("records", [])
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].get("status"), "agent_smoke_passed")
            self.assertEqual(records[0].get("metrics_agent_smoke_result"), "passed")

    def test_script_requires_failure_code_for_failed_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            report_path = tmp_path / "agent-smoke-report.json"

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--report",
                    str(report_path),
                    "--skill-id",
                    "trial-skill-002",
                    "--agent",
                    "claude-code",
                    "--status",
                    "agent_smoke_failed",
                    "--reason",
                    "Skill selected but output omitted validation section.",
                    "--trigger-prompt",
                    "Use the release-check skill on the sample rollout bundle.",
                    "--expected-skill-selection",
                    "release-check-skill",
                    "--expected-task-output",
                    "Validation report with risk gates.",
                    "--selected-skill",
                    "release-check-skill",
                    "--observed-task-output",
                    "Only partial checklist without validation.",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertIn("--failure-code", completed.stderr)

    def test_script_updates_existing_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            report_path = tmp_path / "agent-smoke-report.json"

            first = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--report",
                    str(report_path),
                    "--skill-id",
                    "trial-skill-003",
                    "--agent",
                    "opencode",
                    "--status",
                    "not_run",
                    "--reason",
                    "Awaiting scheduler window.",
                    "--trigger-prompt",
                    "Use the support playbook skill for ticket triage.",
                    "--expected-skill-selection",
                    "support-playbook-skill",
                    "--expected-task-output",
                    "Escalation decision tree with response template.",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertIn("status=not_run", first.stdout)

            second = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--report",
                    str(report_path),
                    "--skill-id",
                    "trial-skill-003",
                    "--agent",
                    "opencode",
                    "--status",
                    "agent_smoke_failed",
                    "--reason",
                    "Wrong skill selected.",
                    "--trigger-prompt",
                    "Use the support playbook skill for ticket triage.",
                    "--expected-skill-selection",
                    "support-playbook-skill",
                    "--expected-task-output",
                    "Escalation decision tree with response template.",
                    "--selected-skill",
                    "unrelated-skill",
                    "--observed-task-output",
                    "Produced unrelated deployment notes.",
                    "--failure-code",
                    "wrong_skill_selected",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertIn("Agent smoke record updated", second.stdout)

            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report.get("record_count"), 1)
            records = report.get("records", [])
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].get("status"), "agent_smoke_failed")
            self.assertEqual(records[0].get("failure_code"), "wrong_skill_selected")
            self.assertEqual(records[0].get("metrics_agent_smoke_result"), "failed")


if __name__ == "__main__":
    unittest.main()
