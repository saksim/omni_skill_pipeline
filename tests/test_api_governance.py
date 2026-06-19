from __future__ import annotations

import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

try:
    from fastapi.testclient import TestClient
except ImportError:  # pragma: no cover
    TestClient = None


def _tenant_access_payload() -> str:
    return json.dumps(
        {
            'organizations': [{'organization_id': 'org-a', 'name': 'Org A'}],
            'projects': [{'project_id': 'proj-1', 'organization_id': 'org-a', 'name': 'Project 1'}],
            'users': [{'user_id': 'owner-1', 'organization_id': 'org-a', 'name': 'Owner'}],
            'memberships': [
                {
                    'membership_id': 'mem-owner',
                    'organization_id': 'org-a',
                    'project_id': 'proj-1',
                    'user_id': 'owner-1',
                    'role': 'owner',
                }
            ],
            'api_keys': [
                {
                    'api_key_id': 'key-owner-id',
                    'api_key': 'key-owner',
                    'organization_id': 'org-a',
                    'project_id': 'proj-1',
                    'user_id': 'owner-1',
                    'role': 'owner',
                    'scopes': ['distill.execute', 'review.read', 'review.write'],
                    'quota_policy': {
                        'quota_id': 'q-owner',
                        'organization_id': 'org-a',
                        'project_id': 'proj-1',
                        'distill_requests_per_window': 10,
                        'review_actions_per_window': 10,
                        'window_seconds': 60,
                    },
                }
            ],
            'quota_policies': [],
        },
        ensure_ascii=False,
    )


class _StubBundle(object):
    def to_dict(self) -> dict[str, bool]:
        return {'ok': True}


class _StubReviewQueueRepository(object):
    def __init__(self) -> None:
        self.items = {
            'task-1': {
                'review_task_id': 'task-1',
                'skill_id': 'skill-1',
                'queue_status': 'pending',
                'status': 'review_pending',
                'decision': 'review_required',
                'organization_id': 'org-a',
                'project_id': 'proj-1',
            }
        }

    def list_review_queue(self, *, queue_status='pending', limit=100, tenant_scope=None):
        return [dict(item) for item in self.items.values()]

    def claim_review_task(self, review_task_id=None, *, consumer='review-consumer', tenant_scope=None):
        return dict(self.items['task-1'])

    def close_review_task(
        self,
        review_task_id,
        *,
        status='published',
        closed_by='review-operator',
        review_notes='',
        decision=None,
        reason_codes=None,
        reviewer_edits=None,
        tenant_scope=None,
    ):
        payload = dict(self.items['task-1'])
        payload['queue_status'] = 'closed'
        payload['status'] = status
        payload['decision'] = decision or 'approve'
        payload['closed_by'] = closed_by
        if isinstance(reason_codes, list):
            payload['reason_codes'] = list(reason_codes)
        return payload

    def consume_review_task(self, *, consumer='review-consumer', tenant_scope=None):
        return dict(self.items['task-1'])

    def update_review_task_decision(
        self,
        review_task_id,
        *,
        decision,
        reviewer='review-operator',
        reason_codes=None,
        review_notes='',
        reviewer_edits=None,
        status=None,
        tenant_scope=None,
    ):
        payload = dict(self.items['task-1'])
        payload['queue_status'] = 'closed'
        payload['decision'] = decision
        payload['status'] = status or ('published' if decision == 'approve' else 'needs_rework')
        payload['closed_by'] = reviewer
        if isinstance(reason_codes, list):
            payload['reason_codes'] = list(reason_codes)
        return payload


class _StubService(object):
    def __init__(self) -> None:
        self.repository = _StubReviewQueueRepository()

    def distill_text(self, request):
        return _StubBundle()

    def distill_audio(self, request):
        return _StubBundle()

    def distill_image(self, request):
        return _StubBundle()

    def distill_tabular(self, request):
        return _StubBundle()

    def distill_video(self, request):
        return _StubBundle()

    def distill_corpus(self, request):
        return _StubBundle()


def _build_settings(*, ledger_dir: Path) -> SimpleNamespace:
    return SimpleNamespace(
        api_key='',
        rate_limit_requests=0,
        rate_limit_window_seconds=60,
        tenant_access_json=_tenant_access_payload(),
        tenant_access_file='',
        template_path=REPO_ROOT / 'docs' / 'latest' / 'contracts' / 'SKILL.template.md',
        draft_dir=REPO_ROOT / 'skills' / 'drafts',
        governance_ledger_dir=ledger_dir,
    )


def _build_client(*, ledger_dir: Path):
    with (
        patch('omni_skill_pipeline.service.build_service', return_value=_StubService()),
        patch('omni_skill_pipeline.config.load_settings', return_value=_build_settings(ledger_dir=ledger_dir)),
    ):
        module = importlib.import_module('omni_skill_pipeline.api_app')
        module = importlib.reload(module)
        app = module.create_app()
    return TestClient(app)


@unittest.skipIf(TestClient is None, 'fastapi testclient is not installed')
class ApiGovernanceTests(unittest.TestCase):
    def test_governance_retention_upsert_and_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            client = _build_client(ledger_dir=Path(temp_dir))
            headers = {'X-API-Key': 'key-owner'}
            upsert = client.post(
                '/v1/governance/retention-policy',
                headers=headers,
                json={
                    'organization_id': 'org-a',
                    'project_id': 'proj-1',
                    'policy_type': 'artifact_retention',
                    'retention_days': 45,
                    'updated_by': 'owner-1',
                },
            )
            self.assertEqual(upsert.status_code, 200)
            self.assertEqual(upsert.json()['policy']['retention_days'], 45)

            report = client.post(
                '/v1/governance/report',
                headers=headers,
                json={
                    'organization_id': 'org-a',
                    'project_id': 'proj-1',
                    'include_retention_policies': True,
                    'include_audit_events': True,
                },
            )
            self.assertEqual(report.status_code, 200)
            payload = report.json()
            self.assertEqual(payload['retention_policy_summary']['policy_count'], 1)
            self.assertGreaterEqual(payload['audit_summary']['event_count'], 1)

    def test_governance_deletion_records_visible_in_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            client = _build_client(ledger_dir=Path(temp_dir))
            headers = {'X-API-Key': 'key-owner'}
            deletion = client.post(
                '/v1/governance/deletion',
                headers=headers,
                json={
                    'organization_id': 'org-a',
                    'project_id': 'proj-1',
                    'resource_id': 'artifact-1',
                    'resource_type': 'artifact',
                    'deletion_mode': 'hard_delete',
                    'status': 'success',
                    'reason': 'retention-expired',
                },
            )
            self.assertEqual(deletion.status_code, 200)
            self.assertEqual(deletion.json()['deletion_record']['resource_id'], 'artifact-1')

            report = client.post(
                '/v1/governance/report',
                headers=headers,
                json={
                    'organization_id': 'org-a',
                    'project_id': 'proj-1',
                    'include_deletion_records': True,
                    'include_audit_events': True,
                },
            )
            self.assertEqual(report.status_code, 200)
            payload = report.json()
            self.assertEqual(payload['deletion_summary']['record_count'], 1)
            self.assertEqual(payload['deletion_summary']['hard_delete_count'], 1)
            self.assertGreaterEqual(payload['audit_summary']['event_count'], 1)

    def test_review_decision_approve_records_accepted_package_cost_event(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger_dir = Path(temp_dir)
            client = _build_client(ledger_dir=ledger_dir)
            headers = {'X-API-Key': 'key-owner'}
            response = client.post(
                '/v1/review/queue/task-1/decision',
                headers=headers,
                json={
                    'decision': 'approve',
                    'reviewer': 'owner-1',
                    'reason_codes': ['SAFE'],
                },
            )
            self.assertEqual(response.status_code, 200)

            report = client.post(
                '/v1/governance/report',
                headers=headers,
                json={
                    'organization_id': 'org-a',
                    'project_id': 'proj-1',
                    'include_cost_entries': True,
                    'include_audit_events': True,
                },
            )
            self.assertEqual(report.status_code, 200)
            payload = report.json()
            self.assertEqual(payload['cost_summary']['by_event_kind'].get('accepted_package', 0), 1)
            self.assertGreaterEqual(payload['audit_summary']['by_event_type'].get('review_decision_applied', 0), 1)


if __name__ == '__main__':
    unittest.main()
