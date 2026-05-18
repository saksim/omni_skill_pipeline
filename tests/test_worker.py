from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.exceptions import ProviderExecutionError
from omni_skill_pipeline.models import CorpusDistillRequest, TextDistillRequest


class _CapturingService(object):
    def __init__(self) -> None:
        self.corpus_requests: list[CorpusDistillRequest] = []

    def distill_corpus(self, request: CorpusDistillRequest) -> None:
        request.validate()
        self.corpus_requests.append(request)

    def distill_text(self, request):  # pragma: no cover - defensive guard
        raise AssertionError('Unexpected distill_text call')

    def distill_audio(self, request):  # pragma: no cover - defensive guard
        raise AssertionError('Unexpected distill_audio call')

    def distill_image(self, request):  # pragma: no cover - defensive guard
        raise AssertionError('Unexpected distill_image call')

    def distill_tabular(self, request):  # pragma: no cover - defensive guard
        raise AssertionError('Unexpected distill_tabular call')

    def distill_video(self, request):  # pragma: no cover - defensive guard
        raise AssertionError('Unexpected distill_video call')


class _TransientTextService(object):
    def __init__(self, transient_failures: int) -> None:
        self.transient_failures = transient_failures
        self.text_calls = 0

    def distill_text(self, request) -> None:
        self.text_calls += 1
        if self.text_calls <= self.transient_failures:
            raise ProviderExecutionError('temporary provider failure')

    def distill_corpus(self, request):  # pragma: no cover - defensive guard
        raise AssertionError('Unexpected distill_corpus call')

    def distill_audio(self, request):  # pragma: no cover - defensive guard
        raise AssertionError('Unexpected distill_audio call')

    def distill_image(self, request):  # pragma: no cover - defensive guard
        raise AssertionError('Unexpected distill_image call')

    def distill_tabular(self, request):  # pragma: no cover - defensive guard
        raise AssertionError('Unexpected distill_tabular call')

    def distill_video(self, request):  # pragma: no cover - defensive guard
        raise AssertionError('Unexpected distill_video call')


class _PermanentTextService(object):
    def __init__(self) -> None:
        self.text_calls = 0

    def distill_text(self, request) -> None:
        self.text_calls += 1
        raise ValueError('permanent payload validation failure')

    def distill_corpus(self, request):  # pragma: no cover - defensive guard
        raise AssertionError('Unexpected distill_corpus call')

    def distill_audio(self, request):  # pragma: no cover - defensive guard
        raise AssertionError('Unexpected distill_audio call')

    def distill_image(self, request):  # pragma: no cover - defensive guard
        raise AssertionError('Unexpected distill_image call')

    def distill_tabular(self, request):  # pragma: no cover - defensive guard
        raise AssertionError('Unexpected distill_tabular call')

    def distill_video(self, request):  # pragma: no cover - defensive guard
        raise AssertionError('Unexpected distill_video call')


class _CapturingTextService(object):
    def __init__(self) -> None:
        self.text_calls = 0
        self._lock = threading.Lock()

    def distill_text(self, request) -> None:
        with self._lock:
            self.text_calls += 1

    def distill_corpus(self, request):  # pragma: no cover - defensive guard
        raise AssertionError('Unexpected distill_corpus call')

    def distill_audio(self, request):  # pragma: no cover - defensive guard
        raise AssertionError('Unexpected distill_audio call')

    def distill_image(self, request):  # pragma: no cover - defensive guard
        raise AssertionError('Unexpected distill_image call')

    def distill_tabular(self, request):  # pragma: no cover - defensive guard
        raise AssertionError('Unexpected distill_tabular call')

    def distill_video(self, request):  # pragma: no cover - defensive guard
        raise AssertionError('Unexpected distill_video call')


class _StubReviewQueueRepository(object):
    def __init__(self) -> None:
        self.pending: dict[str, dict[str, str]] = {
            'task-1': {
                'review_task_id': 'task-1',
                'skill_id': 'skill-1',
                'decision': 'review_required',
                'status': 'review_pending',
                'queue_status': 'pending',
            }
        }
        self.consumed: dict[str, dict[str, str]] = {}
        self.closed: dict[str, dict[str, str]] = {}
        self.list_calls = 0
        self.claim_calls = 0
        self.close_calls = 0

    def list_review_queue(self, *, queue_status: str | None = 'pending', limit: int = 100) -> list[dict[str, str]]:
        self.list_calls += 1
        normalized = str(queue_status or '').strip().lower()
        items: list[dict[str, str]]
        if normalized in {'', 'pending'}:
            items = [dict(item) for item in self.pending.values()]
        elif normalized == 'consumed':
            items = [dict(item) for item in self.consumed.values()]
        elif normalized == 'closed':
            items = [dict(item) for item in self.closed.values()]
        elif normalized == 'all':
            items = [*self.pending.values(), *self.consumed.values(), *self.closed.values()]
            items = [dict(item) for item in items]
        else:
            items = []
        return items[: max(limit, 0)]

    def claim_review_task(self, review_task_id: str | None = None, *, consumer: str = 'review-consumer') -> dict[str, str] | None:
        self.claim_calls += 1
        target = str(review_task_id or '').strip()
        if not target:
            target = next(iter(sorted(self.pending.keys())), '')
        if not target:
            return None
        pending_item = self.pending.pop(target, None)
        if pending_item is None:
            return None
        claimed = dict(pending_item)
        claimed['queue_status'] = 'consumed'
        claimed['claimed_by'] = consumer.strip() or 'review-consumer'
        self.consumed[target] = claimed
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
        self.close_calls += 1
        target = str(review_task_id).strip()
        if not target:
            return None
        source = self.consumed.pop(target, None) or self.pending.pop(target, None)
        if source is None:
            return None
        closed = dict(source)
        closed['queue_status'] = 'closed'
        closed['status'] = str(status).strip().lower() or 'published'
        closed['closed_by'] = closed_by.strip() or 'review-operator'
        closed['review_notes'] = review_notes.strip()
        self.closed[target] = closed
        return dict(closed)


class _ReviewQueueOnlyService(object):
    def __init__(self, repository: _StubReviewQueueRepository) -> None:
        self.repository = repository

    def distill_text(self, request):  # pragma: no cover - defensive guard
        raise AssertionError('Unexpected distill_text call')

    def distill_corpus(self, request):  # pragma: no cover - defensive guard
        raise AssertionError('Unexpected distill_corpus call')

    def distill_audio(self, request):  # pragma: no cover - defensive guard
        raise AssertionError('Unexpected distill_audio call')

    def distill_image(self, request):  # pragma: no cover - defensive guard
        raise AssertionError('Unexpected distill_image call')

    def distill_tabular(self, request):  # pragma: no cover - defensive guard
        raise AssertionError('Unexpected distill_tabular call')

    def distill_video(self, request):  # pragma: no cover - defensive guard
        raise AssertionError('Unexpected distill_video call')


class _ReplayCapturingService(object):
    def __init__(self) -> None:
        self.text_requests: list[TextDistillRequest] = []
        self.corpus_requests: list[CorpusDistillRequest] = []

    def distill_text(self, request) -> None:
        self.text_requests.append(request)

    def distill_corpus(self, request) -> None:
        self.corpus_requests.append(request)

    def distill_audio(self, request):  # pragma: no cover - defensive guard
        raise AssertionError('Unexpected distill_audio call')

    def distill_image(self, request):  # pragma: no cover - defensive guard
        raise AssertionError('Unexpected distill_image call')

    def distill_tabular(self, request):  # pragma: no cover - defensive guard
        raise AssertionError('Unexpected distill_tabular call')

    def distill_video(self, request):  # pragma: no cover - defensive guard
        raise AssertionError('Unexpected distill_video call')


def _write_pending_job(jobs_root: Path, filename: str, payload: dict) -> Path:
    pending_dir = jobs_root / 'pending'
    pending_dir.mkdir(parents=True, exist_ok=True)
    job_path = pending_dir / filename
    job_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return job_path


class WorkerCorpusIntegrationTests(unittest.TestCase):
    def test_worker_processes_corpus_job_and_moves_to_completed(self) -> None:
        from omni_skill_pipeline import worker as worker_module

        payload = {
            'kind': 'corpus',
            'name': 'beta-corpus',
            'assets': [
                {'source_uri': 'file://examples/text_note.md', 'modality': 'text', 'role': 'primary'},
                {'source_uri': 'file://examples/audio_transcript.srt', 'modality': 'audio', 'role': 'supporting'},
            ],
            'goal': {'domain': 'operations'},
            'tags': ['beta', 'ops'],
        }
        service = _CapturingService()

        with tempfile.TemporaryDirectory() as temp_dir:
            jobs_root = Path(temp_dir) / 'jobs'
            _write_pending_job(jobs_root, 'job-corpus.json', payload)

            with (
                patch.object(worker_module, 'build_service', return_value=service),
                patch.object(worker_module, 'configure_logging', return_value=None),
            ):
                worker = worker_module.LocalJobWorker(jobs_root)
                processed = worker.run_once()

            self.assertEqual(processed, 1)
            self.assertEqual(len(service.corpus_requests), 1)
            request = service.corpus_requests[0]
            self.assertIsInstance(request, CorpusDistillRequest)
            self.assertEqual(request.name, 'beta-corpus')
            self.assertEqual(len(request.assets), 2)
            self.assertEqual(request.assets[0].modality.value, 'text')
            self.assertEqual(request.assets[1].modality.value, 'audio')
            self.assertTrue((jobs_root / 'completed' / 'job-corpus.json').exists())
            self.assertFalse((jobs_root / 'failed' / 'job-corpus.json').exists())

    def test_worker_moves_invalid_corpus_job_to_failed(self) -> None:
        from omni_skill_pipeline import worker as worker_module

        invalid_payload = {
            'kind': 'corpus',
            'name': 'broken-corpus',
            'assets': [],
        }
        service = _CapturingService()

        with tempfile.TemporaryDirectory() as temp_dir:
            jobs_root = Path(temp_dir) / 'jobs'
            _write_pending_job(jobs_root, 'job-invalid-corpus.json', invalid_payload)

            with (
                patch.object(worker_module, 'build_service', return_value=service),
                patch.object(worker_module, 'configure_logging', return_value=None),
            ):
                worker = worker_module.LocalJobWorker(jobs_root)
                processed = worker.run_once()

            self.assertEqual(processed, 1)
            self.assertEqual(len(service.corpus_requests), 0)
            failed_path = jobs_root / 'failed' / 'job-invalid-corpus.json'
            self.assertTrue(failed_path.exists())
            self.assertFalse((jobs_root / 'completed' / 'job-invalid-corpus.json').exists())
            failed_payload = json.loads(failed_path.read_text(encoding='utf-8'))
            self.assertIn('error', failed_payload)
            self.assertIn('Corpus request requires at least one asset.', failed_payload['error'])


class WorkerRetryPolicyTests(unittest.TestCase):
    def test_transient_failure_retries_then_completes(self) -> None:
        from omni_skill_pipeline import worker as worker_module

        payload = {
            'kind': 'text',
            'content': 'incident timeline',
        }
        service = _TransientTextService(transient_failures=1)

        with tempfile.TemporaryDirectory() as temp_dir:
            jobs_root = Path(temp_dir) / 'jobs'
            _write_pending_job(jobs_root, 'job-retry-success.json', payload)

            with (
                patch.object(worker_module, 'build_service', return_value=service),
                patch.object(worker_module, 'configure_logging', return_value=None),
            ):
                worker = worker_module.LocalJobWorker(
                    jobs_root,
                    max_attempts=3,
                    retry_base_delay_seconds=0.0,
                    retry_backoff_multiplier=2.0,
                )
                processed = worker.run_once()

            self.assertEqual(processed, 1)
            self.assertEqual(service.text_calls, 2)
            self.assertTrue((jobs_root / 'completed' / 'job-retry-success.json').exists())
            self.assertFalse((jobs_root / 'failed' / 'job-retry-success.json').exists())

    def test_transient_failure_exhausts_retry_and_moves_to_failed(self) -> None:
        from omni_skill_pipeline import worker as worker_module

        payload = {
            'kind': 'text',
            'content': 'incident timeline',
        }
        service = _TransientTextService(transient_failures=5)

        with tempfile.TemporaryDirectory() as temp_dir:
            jobs_root = Path(temp_dir) / 'jobs'
            _write_pending_job(jobs_root, 'job-retry-failed.json', payload)

            with (
                patch.object(worker_module, 'build_service', return_value=service),
                patch.object(worker_module, 'configure_logging', return_value=None),
            ):
                worker = worker_module.LocalJobWorker(
                    jobs_root,
                    max_attempts=2,
                    retry_base_delay_seconds=0.0,
                    retry_backoff_multiplier=2.0,
                )
                processed = worker.run_once()

            self.assertEqual(processed, 1)
            self.assertEqual(service.text_calls, 2)
            failed_path = jobs_root / 'failed' / 'job-retry-failed.json'
            self.assertTrue(failed_path.exists())
            self.assertFalse((jobs_root / 'completed' / 'job-retry-failed.json').exists())
            failed_payload = json.loads(failed_path.read_text(encoding='utf-8'))
            self.assertEqual(failed_payload.get('attempts'), 2)
            self.assertEqual(failed_payload.get('transient'), True)
            self.assertEqual(failed_payload.get('retry_exhausted'), True)

    def test_permanent_failure_is_not_retried(self) -> None:
        from omni_skill_pipeline import worker as worker_module

        payload = {
            'kind': 'text',
            'content': 'incident timeline',
        }
        service = _PermanentTextService()

        with tempfile.TemporaryDirectory() as temp_dir:
            jobs_root = Path(temp_dir) / 'jobs'
            _write_pending_job(jobs_root, 'job-permanent-failed.json', payload)

            with (
                patch.object(worker_module, 'build_service', return_value=service),
                patch.object(worker_module, 'configure_logging', return_value=None),
            ):
                worker = worker_module.LocalJobWorker(
                    jobs_root,
                    max_attempts=5,
                    retry_base_delay_seconds=0.0,
                    retry_backoff_multiplier=2.0,
                )
                processed = worker.run_once()

            self.assertEqual(processed, 1)
            self.assertEqual(service.text_calls, 1)
            failed_path = jobs_root / 'failed' / 'job-permanent-failed.json'
            self.assertTrue(failed_path.exists())
            self.assertFalse((jobs_root / 'completed' / 'job-permanent-failed.json').exists())
            failed_payload = json.loads(failed_path.read_text(encoding='utf-8'))
            self.assertEqual(failed_payload.get('attempts'), 1)
            self.assertEqual(failed_payload.get('transient'), False)
            self.assertEqual(failed_payload.get('retry_exhausted'), False)


class WorkerIdempotencyTests(unittest.TestCase):
    def test_duplicate_payload_jobs_only_execute_once(self) -> None:
        from omni_skill_pipeline import worker as worker_module

        payload = {
            'kind': 'text',
            'content': 'repeat-safe payload',
        }
        service = _CapturingTextService()

        with tempfile.TemporaryDirectory() as temp_dir:
            jobs_root = Path(temp_dir) / 'jobs'
            _write_pending_job(jobs_root, 'job-1.json', payload)
            _write_pending_job(jobs_root, 'job-2.json', payload)

            with (
                patch.object(worker_module, 'build_service', return_value=service),
                patch.object(worker_module, 'configure_logging', return_value=None),
            ):
                worker = worker_module.LocalJobWorker(jobs_root)
                processed = worker.run_once()

            self.assertEqual(processed, 2)
            self.assertEqual(service.text_calls, 1)
            self.assertTrue((jobs_root / 'completed' / 'job-1.json').exists())
            duplicate_path = jobs_root / 'completed' / 'job-2.duplicate.json'
            self.assertTrue(duplicate_path.exists())
            duplicate_payload = json.loads(duplicate_path.read_text(encoding='utf-8'))
            self.assertEqual(duplicate_payload.get('status'), 'duplicate_skipped')
            self.assertEqual(duplicate_payload.get('duplicate_of'), 'job-1.json')
            self.assertEqual(duplicate_payload.get('job_file'), 'job-2.json')
            self.assertFalse((jobs_root / 'pending' / 'job-1.json').exists())
            self.assertFalse((jobs_root / 'pending' / 'job-2.json').exists())

    def test_explicit_idempotency_key_short_circuits_duplicate_job(self) -> None:
        from omni_skill_pipeline import worker as worker_module

        payload_1 = {
            'kind': 'text',
            'content': 'first payload',
            'idempotency_key': 'same-key',
        }
        payload_2 = {
            'kind': 'text',
            'content': 'second payload should be skipped',
            'idempotency_key': 'same-key',
        }
        service = _CapturingTextService()

        with tempfile.TemporaryDirectory() as temp_dir:
            jobs_root = Path(temp_dir) / 'jobs'
            _write_pending_job(jobs_root, 'job-key-1.json', payload_1)
            _write_pending_job(jobs_root, 'job-key-2.json', payload_2)

            with (
                patch.object(worker_module, 'build_service', return_value=service),
                patch.object(worker_module, 'configure_logging', return_value=None),
            ):
                worker = worker_module.LocalJobWorker(jobs_root)
                processed = worker.run_once()

            self.assertEqual(processed, 2)
            self.assertEqual(service.text_calls, 1)
            duplicate_path = jobs_root / 'completed' / 'job-key-2.duplicate.json'
            self.assertTrue(duplicate_path.exists())
            duplicate_payload = json.loads(duplicate_path.read_text(encoding='utf-8'))
            self.assertEqual(duplicate_payload.get('idempotency_key'), 'idempotency_key:same-key')
            self.assertEqual(duplicate_payload.get('duplicate_of'), 'job-key-1.json')


class WorkerConcurrencyClaimTests(unittest.TestCase):
    def test_two_workers_do_not_consume_same_job_concurrently(self) -> None:
        from omni_skill_pipeline import worker as worker_module

        payload = {
            'kind': 'text',
            'content': 'concurrency-simulation',
        }
        service = _CapturingTextService()

        with tempfile.TemporaryDirectory() as temp_dir:
            jobs_root = Path(temp_dir) / 'jobs'
            _write_pending_job(jobs_root, 'job-race.json', payload)

            with (
                patch.object(worker_module, 'build_service', return_value=service),
                patch.object(worker_module, 'configure_logging', return_value=None),
            ):
                worker_a = worker_module.LocalJobWorker(jobs_root)
                worker_b = worker_module.LocalJobWorker(jobs_root)
                results = {'a': 0, 'b': 0}

                thread_a = threading.Thread(target=lambda: results.__setitem__('a', worker_a.run_once()))
                thread_b = threading.Thread(target=lambda: results.__setitem__('b', worker_b.run_once()))
                thread_a.start()
                thread_b.start()
                thread_a.join()
                thread_b.join()

            self.assertEqual(results['a'] + results['b'], 1)
            self.assertEqual(service.text_calls, 1)
            self.assertTrue((jobs_root / 'completed' / 'job-race.json').exists())
            self.assertFalse((jobs_root / 'pending' / 'job-race.json').exists())
            self.assertEqual(list((jobs_root / 'inflight').glob('*.json')), [])


class WorkerTaskTypeUpgradeTests(unittest.TestCase):
    def test_review_queue_claim_job_is_supported(self) -> None:
        from omni_skill_pipeline import worker as worker_module

        queue_repository = _StubReviewQueueRepository()
        service = _ReviewQueueOnlyService(queue_repository)
        payload = {
            'kind': 'review_queue',
            'action': 'claim',
            'consumer': 'queue-worker',
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            jobs_root = Path(temp_dir) / 'jobs'
            _write_pending_job(jobs_root, 'job-review-claim.json', payload)

            with (
                patch.object(worker_module, 'build_service', return_value=service),
                patch.object(worker_module, 'configure_logging', return_value=None),
            ):
                worker = worker_module.LocalJobWorker(jobs_root)
                processed = worker.run_once()

            self.assertEqual(processed, 1)
            self.assertEqual(queue_repository.claim_calls, 1)
            self.assertEqual(queue_repository.pending, {})
            self.assertIn('task-1', queue_repository.consumed)
            self.assertTrue((jobs_root / 'completed' / 'job-review-claim.json').exists())

    def test_rebuild_publication_job_replays_text_request(self) -> None:
        from omni_skill_pipeline import worker as worker_module

        service = _ReplayCapturingService()
        payload = {
            'kind': 'rebuild_publication',
            'request_kind': 'text',
            'request': {
                'content': 'rebuild publication from known request',
                'goal': {'domain': 'operations'},
            },
            'goal_overrides': {'domain': 'sre'},
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            jobs_root = Path(temp_dir) / 'jobs'
            _write_pending_job(jobs_root, 'job-rebuild-publication.json', payload)

            with (
                patch.object(worker_module, 'build_service', return_value=service),
                patch.object(worker_module, 'configure_logging', return_value=None),
            ):
                worker = worker_module.LocalJobWorker(jobs_root)
                processed = worker.run_once()

            self.assertEqual(processed, 1)
            self.assertEqual(len(service.text_requests), 1)
            request = service.text_requests[0]
            self.assertIsInstance(request, TextDistillRequest)
            self.assertEqual(request.content, 'rebuild publication from known request')
            self.assertEqual(request.goal.domain, 'sre')
            self.assertTrue((jobs_root / 'completed' / 'job-rebuild-publication.json').exists())

    def test_rebuild_publication_can_load_request_payload_from_bundle(self) -> None:
        from omni_skill_pipeline import worker as worker_module

        service = _ReplayCapturingService()

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            jobs_root = root / 'jobs'
            bundle_path = root / 'bundle.json'
            bundle_path.write_text(
                json.dumps(
                    {
                        'request_payload': {
                            'content': 'rebuild from bundle request payload',
                            'goal': {'domain': 'platform'},
                        }
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + '\n',
                encoding='utf-8',
            )
            _write_pending_job(
                jobs_root,
                'job-rebuild-from-bundle.json',
                {
                    'kind': 'rebuild_publication',
                    'request_kind': 'text',
                    'bundle_path': str(bundle_path),
                },
            )

            with (
                patch.object(worker_module, 'build_service', return_value=service),
                patch.object(worker_module, 'configure_logging', return_value=None),
            ):
                worker = worker_module.LocalJobWorker(jobs_root)
                processed = worker.run_once()

            self.assertEqual(processed, 1)
            self.assertEqual(len(service.text_requests), 1)
            self.assertEqual(service.text_requests[0].content, 'rebuild from bundle request payload')

    def test_revise_skill_requires_existing_skill_id(self) -> None:
        from omni_skill_pipeline import worker as worker_module

        service = _ReplayCapturingService()
        payload = {
            'kind': 'revise_skill',
            'request_kind': 'text',
            'request': {
                'content': 'revise without explicit skill id',
            },
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            jobs_root = Path(temp_dir) / 'jobs'
            _write_pending_job(jobs_root, 'job-revise-missing-id.json', payload)

            with (
                patch.object(worker_module, 'build_service', return_value=service),
                patch.object(worker_module, 'configure_logging', return_value=None),
            ):
                worker = worker_module.LocalJobWorker(jobs_root)
                processed = worker.run_once()

            self.assertEqual(processed, 1)
            self.assertEqual(len(service.text_requests), 0)
            failed_path = jobs_root / 'failed' / 'job-revise-missing-id.json'
            self.assertTrue(failed_path.exists())
            failed_payload = json.loads(failed_path.read_text(encoding='utf-8'))
            self.assertIn('existing_skill_id', failed_payload.get('error', ''))

    def test_revise_skill_injects_existing_skill_id_into_corpus_metadata(self) -> None:
        from omni_skill_pipeline import worker as worker_module

        service = _ReplayCapturingService()
        payload = {
            'kind': 'revise_skill',
            'existing_skill_id': 'skill-legacy-1',
            'request_kind': 'corpus',
            'request': {
                'name': 'revise-corpus',
                'assets': [
                    {'source_uri': 'file://examples/text_note.md', 'modality': 'text', 'role': 'primary'},
                ],
                'metadata': {'source': 'review-loop'},
                'goal': {'domain': 'operations'},
            },
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            jobs_root = Path(temp_dir) / 'jobs'
            _write_pending_job(jobs_root, 'job-revise-corpus.json', payload)

            with (
                patch.object(worker_module, 'build_service', return_value=service),
                patch.object(worker_module, 'configure_logging', return_value=None),
            ):
                worker = worker_module.LocalJobWorker(jobs_root)
                processed = worker.run_once()

            self.assertEqual(processed, 1)
            self.assertEqual(len(service.corpus_requests), 1)
            request = service.corpus_requests[0]
            self.assertIsInstance(request, CorpusDistillRequest)
            self.assertEqual(request.metadata.get('source'), 'review-loop')
            self.assertEqual(request.metadata.get('revise_existing_skill_id'), 'skill-legacy-1')
            self.assertTrue((jobs_root / 'completed' / 'job-revise-corpus.json').exists())


if __name__ == '__main__':
    unittest.main()
