from __future__ import annotations

import importlib
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


class _StubBundle(object):
    def to_dict(self) -> dict[str, bool]:
        return {'ok': True}


class _StubService(object):
    class _StubReviewQueueRepository(object):
        def list_review_queue(self, *, queue_status='pending', limit=100, tenant_scope=None):
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

    repository = _StubReviewQueueRepository()

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


def _build_settings(*, template_path: Path, draft_dir: Path) -> SimpleNamespace:
    return SimpleNamespace(
        api_key='',
        rate_limit_requests=0,
        rate_limit_window_seconds=60,
        tenant_access_json='',
        tenant_access_file='',
        template_path=template_path,
        draft_dir=draft_dir,
        repo_root=REPO_ROOT,
        governance_ledger_dir=template_path.parent / 'governance',
    )


def _build_client(settings: SimpleNamespace):
    with (
        patch('omni_skill_pipeline.service.build_service', return_value=_StubService()),
        patch('omni_skill_pipeline.config.load_settings', return_value=settings),
    ):
        module = importlib.import_module('omni_skill_pipeline.api_app')
        module = importlib.reload(module)
        app = module.create_app()
    return TestClient(app)


@unittest.skipIf(TestClient is None, 'fastapi testclient is not installed')
class ApiHealthzReadinessTests(unittest.TestCase):
    def test_healthz_ready_when_template_and_draft_dir_are_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            template_path = root / 'SKILL.template.md'
            template_path.write_text('# template', encoding='utf-8')
            draft_dir = root / 'drafts'
            draft_dir.mkdir(parents=True, exist_ok=True)

            client = _build_client(_build_settings(template_path=template_path, draft_dir=draft_dir))
            response = client.get('/healthz')

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['status'], 'ready')
        checks = {item['name']: item for item in payload['checks']}
        self.assertTrue(checks['template_path']['ok'])
        self.assertTrue(checks['draft_dir']['ok'])
        self.assertTrue(checks['app_assembly']['ok'])
        self.assertEqual(checks['app_assembly']['missing_routes'], [])

    def test_healthz_degraded_when_template_file_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            template_path = root / 'missing.template.md'
            draft_dir = root / 'drafts'
            draft_dir.mkdir(parents=True, exist_ok=True)

            client = _build_client(_build_settings(template_path=template_path, draft_dir=draft_dir))
            response = client.get('/healthz')

        self.assertEqual(response.status_code, 503)
        payload = response.json()
        self.assertEqual(payload['status'], 'degraded')
        checks = {item['name']: item for item in payload['checks']}
        self.assertFalse(checks['template_path']['ok'])
        self.assertIn('missing', checks['template_path']['detail'])
        self.assertTrue(checks['draft_dir']['ok'])
        self.assertTrue(checks['app_assembly']['ok'])

    def test_healthz_degraded_when_draft_dir_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            template_path = root / 'SKILL.template.md'
            template_path.write_text('# template', encoding='utf-8')
            draft_dir = root / 'missing-drafts'

            client = _build_client(_build_settings(template_path=template_path, draft_dir=draft_dir))
            response = client.get('/healthz')

        self.assertEqual(response.status_code, 503)
        payload = response.json()
        self.assertEqual(payload['status'], 'degraded')
        checks = {item['name']: item for item in payload['checks']}
        self.assertTrue(checks['template_path']['ok'])
        self.assertFalse(checks['draft_dir']['ok'])
        self.assertIn('missing', checks['draft_dir']['detail'])


if __name__ == '__main__':
    unittest.main()
