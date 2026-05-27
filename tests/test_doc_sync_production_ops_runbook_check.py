from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "run_doc_sync_check.py"


class DocSyncProductionOpsRunbookCheckTests(unittest.TestCase):
    def _load_module(self):
        spec = importlib.util.spec_from_file_location("run_doc_sync_check", SCRIPT_PATH)
        self.assertIsNotNone(spec)
        assert spec is not None
        module = importlib.util.module_from_spec(spec)
        self.assertIsNotNone(spec.loader)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module

    def test_production_ops_check_reports_missing_sections(self) -> None:
        module = self._load_module()
        check = module._check_production_ops_runbook_completeness(
            "# Production Operations Baseline\n\n## Deploy Workflow\n\nincomplete\n"
        )
        self.assertEqual(check.get("status"), "fail")
        self.assertEqual(check.get("name"), "production_ops_runbook_completeness")
        self.assertIn("## Backup Workflow", check["details"]["missing_required_headings"])
        self.assertIn(
            "python scripts/run_ops_readiness_evidence.py",
            check["details"]["missing_required_markers"],
        )

    def test_production_ops_check_passes_for_complete_contract(self) -> None:
        module = self._load_module()
        check = module._check_production_ops_runbook_completeness(
            """# Production Operations Baseline

## Deploy Workflow
docker run --rm -d

## Validation Workflow
python scripts/run_release_gate_validation.py
python scripts/run_launch_readiness_gate.py
python scripts/run_doc_sync_check.py --output
python scripts/run_ops_readiness_evidence.py

## Rollback Workflow
rollback

## Backup Workflow
backup

## Restore Workflow
restore

## Incident Response Workflow
incident

## Log Inspection Workflow
docker logs

## Alert Workflow
alert

## Evidence Collection Workflow
evidence
"""
        )
        self.assertEqual(check.get("status"), "pass")
        self.assertEqual(check["details"]["missing_required_headings"], [])
        self.assertEqual(check["details"]["missing_required_markers"], [])


if __name__ == "__main__":
    unittest.main()
