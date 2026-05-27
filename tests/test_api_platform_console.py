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
                        'distill_requests_per_window': 20,
                        'review_actions_per_window': 20,
                        'window_seconds': 60,
                    },
                }
            ],
            'quota_policies': [],
        },
        ensure_ascii=False,
    )


class _StubReviewQueueRepository(object):
    def list_review_queue(self, *, queue_status='pending', limit=100, tenant_scope=None):
        scope = tenant_scope if isinstance(tenant_scope, dict) else {}
        org = str(scope.get('organization_id', '')).strip()
        project = str(scope.get('project_id', '')).strip()
        if org == 'org-a' and project == 'proj-1':
            return [
                {
                    'review_task_id': 'task-1',
                    'skill_id': 'skill-1',
                    'queue_status': str(queue_status),
                    'status': 'review_pending',
                    'decision': 'review_required',
                    'organization_id': 'org-a',
                    'project_id': 'proj-1',
                }
            ][: max(1, int(limit))]
        return []

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


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def _prepare_repo_fixtures(repo_root: Path) -> None:
    trial_run = {
        'run_id': 'controlled-trial-001',
        'generated_at_utc': '2026-05-26T10:00:00Z',
        'sample_count': 1,
        'metrics_status': 'fail',
        'ga_discussion_blocked': True,
        'samples': [
            {
                'sample_id': 'loop-1',
                'modality': 'text',
                'target': 'portable',
                'trial_security_gate_report': {'status': 'pass'},
                'loop_metrics': {
                    'status': 'complete',
                    'review_outcome': 'approved',
                    'agent_smoke_result': 'passed',
                    'launch_gate_eligible': False,
                    'evidence_origin': 'fixture',
                },
            }
        ],
    }
    trial_metrics = {
        'overall_status': 'fail',
        'ga_discussion_blocked': True,
        'trial_metrics': {
            'complete_loop_count': 1,
            'complete_modalities': ['text'],
            'launch_gate_evidence': {
                'complete_loop_count': 0,
                'complete_modalities': [],
            },
        },
    }
    launch_readiness = {
        'decision': 'HOLD',
        'fail_count': 1,
        'failed_checks': ['trial_loop_volume_and_modality_coverage'],
        'summary': {'complete_loops': 0, 'modalities': 0},
        'checks': [],
    }
    ops_readiness = {
        'overall_status': 'pass',
        'fail_count': 0,
        'failed_checks': [],
    }

    _write_json(
        repo_root
        / 'docs'
        / 'current'
        / 'status'
        / 'baselines'
        / 'controlled-trial'
        / 'controlled-trial-run-report.json',
        trial_run,
    )
    _write_json(
        repo_root
        / 'docs'
        / 'current'
        / 'status'
        / 'baselines'
        / 'controlled-trial'
        / 'trial-metrics-report.json',
        trial_metrics,
    )
    _write_json(
        repo_root / 'docs' / 'current' / 'status' / 'baselines' / 'broad-launch-readiness-report.json',
        launch_readiness,
    )
    _write_json(
        repo_root / 'docs' / 'current' / 'status' / 'baselines' / 'operations-readiness-report.json',
        ops_readiness,
    )

    bundle_payload = {
        'skill': {
            'skill_id': 'skill-1',
            'name': 'Incident triage skill',
            'review_status': 'review_pending',
        },
        'review_task': {
            'status': 'review_pending',
            'decision': 'review_required',
            'organization_id': 'org-a',
            'project_id': 'proj-1',
        },
    }
    _write_json(repo_root / 'skills' / 'drafts' / 'incident-triage-skill' / 'bundle.json', bundle_payload)


def _build_settings(*, repo_root: Path, ledger_dir: Path) -> SimpleNamespace:
    return SimpleNamespace(
        api_key='',
        rate_limit_requests=0,
        rate_limit_window_seconds=60,
        tenant_access_json=_tenant_access_payload(),
        tenant_access_file='',
        template_path=repo_root / 'docs' / 'current' / 'contracts' / 'SKILL.template.md',
        draft_dir=repo_root / 'skills' / 'drafts',
        repo_root=repo_root,
        governance_ledger_dir=ledger_dir,
    )


def _build_client(*, repo_root: Path, ledger_dir: Path):
    with (
        patch('omni_skill_pipeline.service.build_service', return_value=_StubService()),
        patch(
            'omni_skill_pipeline.config.load_settings',
            return_value=_build_settings(repo_root=repo_root, ledger_dir=ledger_dir),
        ),
    ):
        module = importlib.import_module('omni_skill_pipeline.api_app')
        module = importlib.reload(module)
        app = module.create_app()
    return TestClient(app)


@unittest.skipIf(TestClient is None, 'fastapi testclient is not installed')
class ApiPlatformConsoleTests(unittest.TestCase):
    def test_console_views_aggregate_trial_review_skills_metrics_security_and_cost(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _prepare_repo_fixtures(root)
            client = _build_client(repo_root=root, ledger_dir=root / 'governance')

            response = client.post(
                '/v1/console/views',
                headers={'X-API-Key': 'key-owner'},
                json={
                    'organization_id': 'org-a',
                    'project_id': 'proj-1',
                    'limit': 10,
                    'queue_status': 'pending',
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['schema_version'], 'platform_console_views.v1')
        self.assertEqual(payload['tenant_scope'], {'organization_id': 'org-a', 'project_id': 'proj-1'})
        views = payload['views']
        self.assertIn('trial_runs', views)
        self.assertIn('review_queue', views)
        self.assertIn('skill_registry', views)
        self.assertIn('metrics', views)
        self.assertIn('security_failures', views)
        self.assertIn('cost', views)
        self.assertEqual(views['trial_runs']['run_id'], 'controlled-trial-001')
        self.assertEqual(views['review_queue']['item_count'], 1)
        self.assertEqual(views['skill_registry']['item_count'], 1)
        self.assertEqual(views['metrics']['launch_readiness']['decision'], 'HOLD')
        self.assertEqual(views['cost']['cost_summary']['entry_count'], 0)


if __name__ == '__main__':
    unittest.main()
