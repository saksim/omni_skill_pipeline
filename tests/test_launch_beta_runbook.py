from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNBOOK_PATH = REPO_ROOT / "docs" / "current" / "operations" / "runbooks" / "launch-beta.md"


class LaunchBetaRunbookTests(unittest.TestCase):
    def test_runbook_exists(self) -> None:
        self.assertTrue(RUNBOOK_PATH.exists(), "launch-beta.md is missing")

    def test_runbook_contains_required_sections(self) -> None:
        content = RUNBOOK_PATH.read_text(encoding="utf-8")
        required_headings = [
            "## Deploy",
            "## Acceptance",
            "## Log Inspection",
            "## Temp Cleanup",
            "## Rollback",
        ]
        for heading in required_headings:
            self.assertIn(heading, content, "Missing heading: %s" % heading)

    def test_runbook_references_operational_scripts(self) -> None:
        content = RUNBOOK_PATH.read_text(encoding="utf-8")
        required_commands = [
            "python scripts/run_ci.py",
            "python scripts/run_container_smoke.py",
            "python scripts/prune_tmp_media.py",
        ]
        for command in required_commands:
            self.assertIn(command, content, "Missing command: %s" % command)


if __name__ == "__main__":
    unittest.main()
