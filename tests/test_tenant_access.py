from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.tenant_access import TenantAccessRegistry


def _tenant_payload() -> dict[str, object]:
    return {
        'organizations': [
            {
                'organization_id': 'org-a',
                'name': 'Org A',
            }
        ],
        'projects': [
            {
                'project_id': 'proj-1',
                'organization_id': 'org-a',
                'name': 'Project 1',
            }
        ],
        'users': [
            {
                'user_id': 'user-1',
                'organization_id': 'org-a',
                'name': 'Alice',
            },
            {
                'user_id': 'user-2',
                'organization_id': 'org-a',
                'name': 'Bob',
            },
        ],
        'memberships': [
            {
                'membership_id': 'm-1',
                'organization_id': 'org-a',
                'project_id': 'proj-1',
                'user_id': 'user-1',
                'role': 'owner',
            },
            {
                'membership_id': 'm-2',
                'organization_id': 'org-a',
                'project_id': 'proj-1',
                'user_id': 'user-2',
                'role': 'reviewer',
            },
        ],
        'api_keys': [
            {
                'api_key_id': 'k-owner',
                'api_key': 'key-owner',
                'organization_id': 'org-a',
                'project_id': 'proj-1',
                'user_id': 'user-1',
                'role': 'owner',
                'scopes': ['distill.execute', 'review.read', 'review.write'],
                'quota_policy': {
                    'quota_id': 'q-owner',
                    'organization_id': 'org-a',
                    'project_id': 'proj-1',
                    'distill_requests_per_window': 2,
                    'review_actions_per_window': 1,
                    'window_seconds': 60,
                },
            },
            {
                'api_key_id': 'k-reviewer',
                'api_key': 'key-reviewer',
                'organization_id': 'org-a',
                'project_id': 'proj-1',
                'user_id': 'user-2',
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
                'api_key_id': 'k-revoked',
                'api_key': 'key-revoked',
                'organization_id': 'org-a',
                'project_id': 'proj-1',
                'user_id': 'user-1',
                'role': 'owner',
                'scopes': ['distill.execute', 'review.read', 'review.write'],
                'revoked': True,
                'quota_policy': {
                    'quota_id': 'q-revoked',
                    'organization_id': 'org-a',
                    'project_id': 'proj-1',
                    'distill_requests_per_window': 1,
                    'review_actions_per_window': 1,
                    'window_seconds': 60,
                },
            },
        ],
        'quota_policies': [],
    }


class TenantAccessRegistryTests(unittest.TestCase):
    def test_authenticate_and_authorize_owner(self) -> None:
        registry = TenantAccessRegistry.from_dict(_tenant_payload())
        auth_result = registry.authenticate('key-owner')
        self.assertIsNotNone(auth_result.identity)
        identity = auth_result.identity
        assert identity is not None
        self.assertEqual(identity.organization_id, 'org-a')
        self.assertEqual(identity.project_id, 'proj-1')
        self.assertTrue(registry.authorize(identity=identity, action='distill.execute'))
        self.assertTrue(registry.authorize(identity=identity, action='review.write'))

    def test_reviewer_cannot_distill(self) -> None:
        registry = TenantAccessRegistry.from_dict(_tenant_payload())
        auth_result = registry.authenticate('key-reviewer')
        self.assertIsNotNone(auth_result.identity)
        identity = auth_result.identity
        assert identity is not None
        self.assertFalse(registry.authorize(identity=identity, action='distill.execute'))
        self.assertTrue(registry.authorize(identity=identity, action='review.read'))

    def test_scope_validation_rejects_cross_tenant(self) -> None:
        registry = TenantAccessRegistry.from_dict(_tenant_payload())
        auth_result = registry.authenticate('key-owner')
        self.assertIsNotNone(auth_result.identity)
        identity = auth_result.identity
        assert identity is not None
        self.assertTrue(
            registry.validate_requested_scope(
                identity=identity,
                requested_scope={'organization_id': 'org-a', 'project_id': 'proj-1'},
            )
        )
        self.assertFalse(
            registry.validate_requested_scope(
                identity=identity,
                requested_scope={'organization_id': 'org-b', 'project_id': 'proj-1'},
            )
        )
        self.assertFalse(
            registry.validate_requested_scope(
                identity=identity,
                requested_scope={'organization_id': 'org-a', 'project_id': 'proj-x'},
            )
        )

    def test_quota_enforcement(self) -> None:
        registry = TenantAccessRegistry.from_dict(_tenant_payload())
        auth_result = registry.authenticate('key-owner')
        self.assertIsNotNone(auth_result.identity)
        identity = auth_result.identity
        assert identity is not None

        first_allowed, _ = registry.enforce_quota(identity=identity, action='distill.execute')
        second_allowed, _ = registry.enforce_quota(identity=identity, action='distill.execute')
        third_allowed, retry_after = registry.enforce_quota(identity=identity, action='distill.execute')
        self.assertTrue(first_allowed)
        self.assertTrue(second_allowed)
        self.assertFalse(third_allowed)
        self.assertGreaterEqual(retry_after, 1)

    def test_revoked_api_key_is_rejected(self) -> None:
        registry = TenantAccessRegistry.from_dict(_tenant_payload())
        auth_result = registry.authenticate('key-revoked')
        self.assertIsNone(auth_result.identity)
        self.assertEqual(auth_result.failure_code, 'revoked_api_key')
        self.assertEqual(auth_result.message, 'API key revoked.')


if __name__ == '__main__':
    unittest.main()
