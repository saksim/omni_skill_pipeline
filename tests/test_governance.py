from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.governance import GovernanceLedger


class GovernanceLedgerTests(unittest.TestCase):
    def test_build_report_filters_by_tenant_scope(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger = GovernanceLedger(Path(temp_dir))
            ledger.record_cost_entry(
                {
                    'organization_id': 'org-a',
                    'project_id': 'proj-1',
                    'event_kind': 'provider_call',
                    'provider': 'openai',
                    'call_count': 3,
                    'failure_count': 1,
                    'estimated_cost_usd': 1.25,
                }
            )
            ledger.record_cost_entry(
                {
                    'organization_id': 'org-b',
                    'project_id': 'proj-2',
                    'event_kind': 'provider_call',
                    'provider': 'openai',
                    'call_count': 2,
                    'failure_count': 0,
                    'estimated_cost_usd': 0.5,
                }
            )
            ledger.record_audit_event(
                {
                    'organization_id': 'org-a',
                    'project_id': 'proj-1',
                    'event_type': 'review_closed',
                    'status': 'success',
                }
            )
            report = ledger.build_report(
                tenant_scope={'organization_id': 'org-a', 'project_id': 'proj-1'},
                include_cost_entries=True,
                include_audit_events=True,
            )
            self.assertEqual(report['cost_summary']['entry_count'], 1)
            self.assertEqual(report['audit_summary']['event_count'], 1)
            self.assertEqual(report['cost_summary']['by_provider']['openai'], 1)
            self.assertEqual(report['cost_entries'][0]['organization_id'], 'org-a')
            self.assertEqual(report['audit_events'][0]['event_type'], 'review_closed')

    def test_deletion_event_also_records_audit_event(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger = GovernanceLedger(Path(temp_dir))
            deletion = ledger.record_deletion_event(
                {
                    'organization_id': 'org-a',
                    'project_id': 'proj-1',
                    'resource_id': 'artifact-1',
                    'resource_type': 'artifact',
                    'deletion_mode': 'hard_delete',
                    'status': 'success',
                }
            )
            report = ledger.build_report(
                tenant_scope={'organization_id': 'org-a', 'project_id': 'proj-1'},
                include_deletion_records=True,
                include_audit_events=True,
            )
            self.assertEqual(deletion['resource_id'], 'artifact-1')
            self.assertEqual(report['deletion_summary']['record_count'], 1)
            self.assertEqual(report['deletion_summary']['hard_delete_count'], 1)
            self.assertEqual(report['audit_summary']['by_event_type']['deletion_recorded'], 1)

    def test_upsert_retention_policy_replaces_existing_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger = GovernanceLedger(Path(temp_dir))
            first = ledger.upsert_retention_policy(
                {
                    'organization_id': 'org-a',
                    'project_id': 'proj-1',
                    'policy_type': 'artifact_retention',
                    'retention_days': 30,
                    'updated_by': 'alice',
                }
            )
            second = ledger.upsert_retention_policy(
                {
                    'policy_id': first['policy_id'],
                    'organization_id': 'org-a',
                    'project_id': 'proj-1',
                    'policy_type': 'artifact_retention',
                    'retention_days': 90,
                    'updated_by': 'bob',
                }
            )
            policies = ledger.list_retention_policies(tenant_scope={'organization_id': 'org-a', 'project_id': 'proj-1'})
            self.assertEqual(len(policies), 1)
            self.assertEqual(policies[0]['retention_days'], 90)
            self.assertEqual(second['updated_by'], 'bob')

            raw_file = Path(temp_dir) / 'retention-policies.json'
            payload = json.loads(raw_file.read_text(encoding='utf-8'))
            self.assertEqual(len(payload), 1)


if __name__ == '__main__':
    unittest.main()
