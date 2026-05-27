from __future__ import annotations

import importlib
import io
import json
import tempfile
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


def _run_cli(argv: list[str], *, ledger_root: Path) -> tuple[int, str]:
    module = importlib.import_module('omni_skill_pipeline.cli')
    module = importlib.reload(module)
    settings = type('Settings', (), {'governance_ledger_dir': ledger_root})()
    service_stub = type('ServiceStub', (), {})()
    with (
        patch('omni_skill_pipeline.config.load_settings', return_value=settings),
        patch.object(module, 'build_service', return_value=service_stub),
    ):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = module.main(argv)
    return exit_code, stdout.getvalue()


class CliGovernanceTests(unittest.TestCase):
    def test_upsert_retention_policy_then_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger_root = Path(temp_dir)
            exit_code, output = _run_cli(
                [
                    'upsert-retention-policy',
                    '--organization-id',
                    'org-a',
                    '--project-id',
                    'proj-1',
                    '--retention-days',
                    '60',
                    '--updated-by',
                    'owner-1',
                ],
                ledger_root=ledger_root,
            )
            self.assertEqual(exit_code, 0)
            upsert_payload = json.loads(output)
            self.assertEqual(upsert_payload['policy']['retention_days'], 60)

            report_code, report_output = _run_cli(
                [
                    'governance-report',
                    '--organization-id',
                    'org-a',
                    '--project-id',
                    'proj-1',
                ],
                ledger_root=ledger_root,
            )
            self.assertEqual(report_code, 0)
            report_payload = json.loads(report_output)
            self.assertEqual(report_payload['retention_policy_summary']['policy_count'], 1)

    def test_record_deletion_then_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger_root = Path(temp_dir)
            exit_code, output = _run_cli(
                [
                    'record-deletion',
                    '--organization-id',
                    'org-a',
                    '--project-id',
                    'proj-1',
                    '--resource-id',
                    'artifact-1',
                    '--deletion-mode',
                    'hard_delete',
                    '--status',
                    'success',
                ],
                ledger_root=ledger_root,
            )
            self.assertEqual(exit_code, 0)
            deletion_payload = json.loads(output)
            self.assertEqual(deletion_payload['deletion_record']['resource_id'], 'artifact-1')

            report_code, report_output = _run_cli(
                [
                    'governance-report',
                    '--organization-id',
                    'org-a',
                    '--project-id',
                    'proj-1',
                    '--include-deletion-records',
                    '--include-audit-events',
                ],
                ledger_root=ledger_root,
            )
            self.assertEqual(report_code, 0)
            report_payload = json.loads(report_output)
            self.assertEqual(report_payload['deletion_summary']['record_count'], 1)
            self.assertGreaterEqual(report_payload['audit_summary']['event_count'], 1)


if __name__ == '__main__':
    unittest.main()
