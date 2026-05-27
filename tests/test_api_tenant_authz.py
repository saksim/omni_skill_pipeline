from __future__ import annotations

import importlib
import json
import sys
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
            'users': [
                {'user_id': 'owner-1', 'organization_id': 'org-a', 'name': 'Owner'},
                {'user_id': 'reviewer-1', 'organization_id': 'org-a', 'name': 'Reviewer'},
            ],
            'memberships': [
                {
                    'membership_id': 'mem-owner',
                    'organization_id': 'org-a',
                    'project_id': 'proj-1',
                    'user_id': 'owner-1',
                    'role': 'owner',
                },
                {
                    'membership_id': 'mem-reviewer',
                    'organization_id': 'org-a',
                    'project_id': 'proj-1',
                    'user_id': 'reviewer-1',
                    'role': 'reviewer',
                },
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
                        'distill_requests_per_window': 2,
                        'review_actions_per_window': 2,
                        'window_seconds': 60,
                    },
                },
                {
                    'api_key_id': 'key-reviewer-id',
                    'api_key': 'key-reviewer',
                    'organization_id': 'org-a',
                    'project_id': 'proj-1',
                    'user_id': 'reviewer-1',
                    'role': 'reviewer',
                    'scopes': ['review.read', 'review.write'],
                    'quota_policy': {
                        'quota_id': 'q-reviewer',
                        'organization_id': 'org-a',
                        'project_id': 'proj-1',
                        'distill_requests_per_window': 0,
                        'review_actions_per_window': 2,
                        'window_seconds': 60,
                    },
                },
                {
                    'api_key_id': 'key-owner-revoked-id',
                    'api_key': 'key-owner-revoked',
                    'organization_id': 'org-a',
                    'project_id': 'proj-1',
                    'user_id': 'owner-1',
                    'role': 'owner',
                    'scopes': ['distill.execute', 'review.read', 'review.write'],
                    'revoked': True,
                    'quota_policy': {
                        'quota_id': 'q-owner-revoked',
                        'organization_id': 'org-a',
                        'project_id': 'proj-1',
                        'distill_requests_per_window': 2,
                        'review_actions_per_window': 2,
                        'window_seconds': 60,
                    },
                },
            ],
            'quota_policies': [],
        },
        ensure_ascii=False,
    )


class _StubBundle(object):
    def to_dict(self) -> dict[str, bool]:
        return {'ok': True}


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


class _StubReviewQueueRepository(object):
    def __init__(self) -> None:
        self.items = [
            {
                'review_task_id': 'task-org-a',
                'queue_status': 'pending',
                'organization_id': 'org-a',
                'project_id': 'proj-1',
            },
            {
                'review_task_id': 'task-org-b',
                'queue_status': 'pending',
                'organization_id': 'org-b',
                'project_id': 'proj-x',
            },
        ]

    def list_review_queue(self, *, queue_status='pending', limit=100, tenant_scope=None):
        normalized_status = str(queue_status or '').strip().lower()
        scope = tenant_scope if isinstance(tenant_scope, dict) else {}
        org_id = str(scope.get('organization_id', '')).strip()
        project_id = str(scope.get('project_id', '')).strip()
        filtered = []
        for item in self.items:
            if normalized_status and normalized_status != 'all':
                if str(item.get('queue_status', '')).strip().lower() != normalized_status:
                    continue
            if org_id and str(item.get('organization_id', '')).strip() != org_id:
                continue
            if project_id and str(item.get('project_id', '')).strip() != project_id:
                continue
            filtered.append(dict(item))
        return filtered[: max(int(limit), 0)]

    def claim_review_task(self, review_task_id=None, *, consumer='review-consumer', tenant_scope=None):
        return None

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
        return None

    def consume_review_task(self, *, consumer='review-consumer', tenant_scope=None):
        return None


def _build_settings() -> SimpleNamespace:
    return SimpleNamespace(
        api_key='',
        rate_limit_requests=0,
        rate_limit_window_seconds=60,
        tenant_access_json=_tenant_access_payload(),
        tenant_access_file='',
        template_path=REPO_ROOT / 'docs' / 'current' / 'contracts' / 'SKILL.template.md',
        draft_dir=REPO_ROOT / 'skills' / 'drafts',
        repo_root=REPO_ROOT,
        governance_ledger_dir=REPO_ROOT / 'skills' / 'drafts' / 'governance-test',
    )


def _build_client():
    with (
        patch('omni_skill_pipeline.service.build_service', return_value=_StubService()),
        patch('omni_skill_pipeline.config.load_settings', return_value=_build_settings()),
    ):
        module = importlib.import_module('omni_skill_pipeline.api_app')
        module = importlib.reload(module)
        app = module.create_app()
    return TestClient(app)


@unittest.skipIf(TestClient is None, 'fastapi testclient is not installed')
class ApiTenantAuthzTests(unittest.TestCase):
    def test_distill_requires_tenant_api_key(self) -> None:
        client = _build_client()
        response = client.post('/v1/distill/text', json={'content': 'incident timeline'})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['error']['message'], 'Missing API key.')

    def test_reviewer_role_cannot_distill(self) -> None:
        client = _build_client()
        response = client.post(
            '/v1/distill/text',
            json={'content': 'incident timeline'},
            headers={'X-API-Key': 'key-reviewer'},
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn('not authorized', response.json()['error']['message'])

    def test_cross_tenant_scope_is_rejected(self) -> None:
        client = _build_client()
        response = client.post(
            '/v1/distill/text',
            json={
                'content': 'incident timeline',
                'tenant_scope': {
                    'organization_id': 'org-x',
                    'project_id': 'proj-1',
                },
            },
            headers={'X-API-Key': 'key-owner'},
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn('Cross-tenant scope', response.json()['error']['message'])

    def test_tenant_quota_enforced(self) -> None:
        client = _build_client()
        payload = {'content': 'incident timeline'}
        headers = {'X-API-Key': 'key-owner'}
        first = client.post('/v1/distill/text', json=payload, headers=headers)
        second = client.post('/v1/distill/text', json=payload, headers=headers)
        third = client.post('/v1/distill/text', json=payload, headers=headers)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(third.status_code, 429)
        self.assertEqual(third.json()['error']['message'], 'Tenant quota exceeded.')

    def test_revoked_tenant_api_key_is_rejected(self) -> None:
        client = _build_client()
        response = client.post(
            '/v1/distill/text',
            json={'content': 'incident timeline'},
            headers={'X-API-Key': 'key-owner-revoked'},
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['error']['message'], 'API key revoked.')

    def test_review_queue_list_is_tenant_scoped(self) -> None:
        client = _build_client()
        response = client.get('/v1/review/queue', headers={'X-API-Key': 'key-owner'})
        self.assertEqual(response.status_code, 200)
        items = response.json()['items']
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['organization_id'], 'org-a')
        self.assertEqual(items[0]['project_id'], 'proj-1')


if __name__ == '__main__':
    unittest.main()
