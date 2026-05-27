from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNBOOK_PATH = (
    REPO_ROOT / "docs" / "current" / "operations" / "runbooks" / "production-operations-baseline.md"
)


class ProductionOpsRunbookTests(unittest.TestCase):
    def test_runbook_exists(self) -> None:
        self.assertTrue(RUNBOOK_PATH.exists(), "production-operations-baseline.md is missing")

    def test_runbook_contains_required_sections(self) -> None:
        content = RUNBOOK_PATH.read_text(encoding="utf-8")
        required_headings = [
            "## Deploy Workflow",
            "## Validation Workflow",
            "## Rollback Workflow",
            "## Backup Workflow",
            "## Restore Workflow",
            "## Incident Response Workflow",
            "## Log Inspection Workflow",
            "## Alert Workflow",
            "## Evidence Collection Workflow",
        ]
        for heading in required_headings:
            self.assertIn(heading, content, "Missing heading: %s" % heading)

    def test_runbook_references_gate_and_evidence_scripts(self) -> None:
        content = RUNBOOK_PATH.read_text(encoding="utf-8")
        required_commands = [
            "python scripts/run_release_gate_validation.py",
            "python scripts/run_launch_readiness_gate.py",
            "python scripts/run_doc_sync_check.py --output",
            "python scripts/run_ops_readiness_evidence.py",
        ]
        for command in required_commands:
            self.assertIn(command, content, "Missing command: %s" % command)


if __name__ == "__main__":
    unittest.main()
