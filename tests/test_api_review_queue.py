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


class _StubReviewQueueRepository(object):
    def __init__(self) -> None:
        self.pending: dict[str, dict[str, str]] = {
            'task-1': {
                'review_task_id': 'task-1',
                'skill_id': 'skill-1',
                'decision': 'review_required',
                'status': 'review_pending',
                'queue_status': 'pending',
                'enqueued_at': '2026-04-25T10:00:00Z',
            }
        }
        self.consumed: dict[str, dict[str, str]] = {}
        self.closed: dict[str, dict[str, str]] = {}

    def list_review_queue(
        self,
        *,
        queue_status: str | None = 'pending',
        limit: int = 100,
    ) -> list[dict[str, str]]:
        if limit <= 0:
            return []
        normalized = str(queue_status or '').strip().lower()
        buckets: list[dict[str, dict[str, str]]]
        if normalized in {'', 'all'}:
            buckets = [self.pending, self.consumed, self.closed]
        elif normalized == 'pending':
            buckets = [self.pending]
        elif normalized == 'consumed':
            buckets = [self.consumed]
        elif normalized == 'closed':
            buckets = [self.closed]
        else:
            return []
        items: list[dict[str, str]] = []
        for bucket in buckets:
            items.extend(dict(item) for item in bucket.values())
        items.sort(key=lambda item: item.get('review_task_id', ''))
        return items[:limit]

    def claim_review_task(
        self,
        review_task_id: str | None = None,
        *,
        consumer: str = 'review-consumer',
    ) -> dict[str, str] | None:
        target_review_task_id = str(review_task_id or '').strip()
        if not target_review_task_id:
            target_review_task_id = next(iter(sorted(self.pending.keys())), '')
        if not target_review_task_id:
            return None
        pending_item = self.pending.pop(target_review_task_id, None)
        if pending_item is None:
            return None
        claimed = dict(pending_item)
        claimed['queue_status'] = 'consumed'
        claimed['claimed_by'] = consumer.strip() or 'review-consumer'
        claimed['claimed_at'] = '2026-04-25T10:01:00Z'
        claimed['consumed_at'] = '2026-04-25T10:01:00Z'
        self.consumed[target_review_task_id] = claimed
        return dict(claimed)

    def consume_review_task(self, *, consumer: str = 'review-consumer') -> dict[str, str] | None:
        return self.claim_review_task(consumer=consumer)

    def close_review_task(
        self,
        review_task_id: str,
        *,
        status: str = 'published',
        closed_by: str = 'review-operator',
        review_notes: str = '',
    ) -> dict[str, str] | None:
        target_review_task_id = str(review_task_id).strip()
        if not target_review_task_id:
            return None
        source = self.consumed.pop(target_review_task_id, None)
        if source is None:
            source = self.pending.pop(target_review_task_id, None)
        if source is None:
            source = self.closed.get(target_review_task_id)
        if source is None:
            return None
        closed = dict(source)
        closed['queue_status'] = 'closed'
        closed['status'] = str(status).strip().lower() or 'published'
        closed['closed_by'] = closed_by.strip() or 'review-operator'
        closed['closed_at'] = '2026-04-25T10:05:00Z'
        if review_notes.strip():
            closed['review_notes'] = review_notes.strip()
        self.closed[target_review_task_id] = closed
        return dict(closed)


class _StubService(object):
    def __init__(self, repository: _StubReviewQueueRepository) -> None:
        self.repository = repository

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
        template_path=template_path,
        draft_dir=draft_dir,
    )


def _build_client(repository: _StubReviewQueueRepository, *, template_path: Path, draft_dir: Path):
    with (
        patch('omni_skill_pipeline.service.build_service', return_value=_StubService(repository)),
        patch(
            'omni_skill_pipeline.config.load_settings',
            return_value=_build_settings(template_path=template_path, draft_dir=draft_dir),
        ),
    ):
        module = importlib.import_module('omni_skill_pipeline.api_app')
        module = importlib.reload(module)
        app = module.create_app()
    return TestClient(app)


@unittest.skipIf(TestClient is None, 'fastapi testclient is not installed')
class ApiReviewQueueEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        self.template_path = root / 'SKILL.template.md'
        self.template_path.write_text('# template', encoding='utf-8')
        self.draft_dir = root / 'drafts'
        self.draft_dir.mkdir(parents=True, exist_ok=True)
        self.repository = _StubReviewQueueRepository()
        self.client = _build_client(
            self.repository,
            template_path=self.template_path,
            draft_dir=self.draft_dir,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_list_review_queue_returns_pending_items(self) -> None:
        response = self.client.get('/v1/review/queue')
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload['items']), 1)
        self.assertEqual(payload['items'][0]['review_task_id'], 'task-1')
        self.assertEqual(payload['items'][0]['queue_status'], 'pending')

    def test_claim_review_queue_item_marks_consumed(self) -> None:
        response = self.client.post('/v1/review/queue/claim', json={'consumer': 'ops-reviewer'})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['review_task_id'], 'task-1')
        self.assertEqual(payload['queue_status'], 'consumed')
        self.assertEqual(payload['claimed_by'], 'ops-reviewer')

        pending = self.client.get('/v1/review/queue').json()['items']
        self.assertEqual(pending, [])
        consumed = self.client.get('/v1/review/queue', params={'queue_status': 'consumed'}).json()['items']
        self.assertEqual(len(consumed), 1)
        self.assertEqual(consumed[0]['review_task_id'], 'task-1')

    def test_close_review_queue_item_marks_closed(self) -> None:
        claim = self.client.post('/v1/review/queue/claim', json={'review_task_id': 'task-1', 'consumer': 'ops'})
        self.assertEqual(claim.status_code, 200)

        response = self.client.post(
            '/v1/review/queue/task-1/close',
            json={
                'status': 'published',
                'closed_by': 'ops-lead',
                'review_notes': 'manual checklist passed',
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['review_task_id'], 'task-1')
        self.assertEqual(payload['queue_status'], 'closed')
        self.assertEqual(payload['status'], 'published')
        self.assertEqual(payload['closed_by'], 'ops-lead')
        self.assertEqual(payload['review_notes'], 'manual checklist passed')

        closed = self.client.get('/v1/review/queue', params={'queue_status': 'closed'}).json()['items']
        self.assertEqual(len(closed), 1)
        self.assertEqual(closed[0]['review_task_id'], 'task-1')

    def test_claim_returns_404_when_queue_is_empty(self) -> None:
        first = self.client.post('/v1/review/queue/claim', json={'consumer': 'ops-reviewer'})
        self.assertEqual(first.status_code, 200)

        second = self.client.post('/v1/review/queue/claim', json={'consumer': 'ops-reviewer'})
        self.assertEqual(second.status_code, 404)
        payload = second.json()['error']
        self.assertEqual(payload['type'], 'http')
        self.assertEqual(payload['code'], 'http_error')
        self.assertIn('No review task available', payload['message'])


if __name__ == '__main__':
    unittest.main()
