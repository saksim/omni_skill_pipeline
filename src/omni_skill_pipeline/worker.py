from __future__ import annotations

import argparse
import hashlib
import json
import logging
import shutil
import time
import uuid
from pathlib import Path
from typing import Any

from omni_skill_pipeline.exceptions import MediaProcessingError, ProviderExecutionError
from omni_skill_pipeline.interfaces import ReviewQueueRepository
from omni_skill_pipeline.logging_utils import configure_logging, reset_request_context, set_request_context
from omni_skill_pipeline.models import (
    AudioDistillRequest,
    CorpusDistillRequest,
    ImageDistillRequest,
    TabularDistillRequest,
    TextDistillRequest,
    VideoDistillRequest,
)
from omni_skill_pipeline.service import build_service

logger = logging.getLogger(__name__)

DEFAULT_WORKER_MAX_ATTEMPTS = 3
DEFAULT_WORKER_RETRY_BASE_DELAY_SECONDS = 0.5
DEFAULT_WORKER_RETRY_BACKOFF_MULTIPLIER = 2.0


class LocalJobWorker(object):
    def __init__(
        self,
        jobs_root: Path,
        *,
        max_attempts: int = DEFAULT_WORKER_MAX_ATTEMPTS,
        retry_base_delay_seconds: float = DEFAULT_WORKER_RETRY_BASE_DELAY_SECONDS,
        retry_backoff_multiplier: float = DEFAULT_WORKER_RETRY_BACKOFF_MULTIPLIER,
    ) -> None:
        if max_attempts < 1:
            raise ValueError('max_attempts must be >= 1.')
        if retry_base_delay_seconds < 0:
            raise ValueError('retry_base_delay_seconds must be >= 0.')
        if retry_backoff_multiplier < 1:
            raise ValueError('retry_backoff_multiplier must be >= 1.')

        configure_logging(service_name='worker')
        self.jobs_root = Path(jobs_root)
        self.max_attempts = max_attempts
        self.retry_base_delay_seconds = retry_base_delay_seconds
        self.retry_backoff_multiplier = retry_backoff_multiplier
        self.pending_dir = self.jobs_root / 'pending'
        self.inflight_dir = self.jobs_root / 'inflight'
        self.completed_dir = self.jobs_root / 'completed'
        self.failed_dir = self.jobs_root / 'failed'
        self.worker_id = uuid.uuid4().hex[:12]
        for directory in (self.pending_dir, self.inflight_dir, self.completed_dir, self.failed_dir):
            directory.mkdir(parents=True, exist_ok=True)
        self.service = build_service()
        self._completed_jobs_by_key = self._load_completed_job_index()
        logger.info(
            'Worker initialized.',
            extra={
                'event': 'worker_init',
                'jobs_root': str(self.jobs_root),
                'max_attempts': self.max_attempts,
                'retry_base_delay_seconds': self.retry_base_delay_seconds,
                'retry_backoff_multiplier': self.retry_backoff_multiplier,
                'known_completed_idempotency_keys': len(self._completed_jobs_by_key),
                'worker_id': self.worker_id,
            },
        )

    def run_once(self) -> int:
        processed = 0
        logger.info(
            'Worker scan started.',
            extra={
                'event': 'worker_scan_start',
                'jobs_root': str(self.jobs_root),
            },
        )
        for job_file in sorted(self.pending_dir.glob('*.json')):
            claimed_job_file = self._claim_job(job_file)
            if claimed_job_file is None:
                continue
            processed += 1
            self._process_job(claimed_job_file, original_job_name=job_file.name)
        logger.info(
            'Worker scan completed.',
            extra={
                'event': 'worker_scan_complete',
                'jobs_root': str(self.jobs_root),
                'processed': processed,
            },
        )
        return processed

    def _claim_job(self, job_file: Path) -> Path | None:
        claimed_name = '%s.claim-%s.json' % (Path(job_file.name).stem, self.worker_id)
        claimed_path = self.inflight_dir / claimed_name
        try:
            job_file.replace(claimed_path)
            logger.info(
                'Worker job claimed.',
                extra={
                    'event': 'worker_job_claimed',
                    'worker_id': self.worker_id,
                    'job_file': job_file.name,
                    'claimed_file': claimed_path.name,
                },
            )
            return claimed_path
        except FileNotFoundError:
            logger.info(
                'Worker claim skipped because job was already claimed.',
                extra={
                    'event': 'worker_job_claim_skipped',
                    'worker_id': self.worker_id,
                    'job_file': job_file.name,
                },
            )
            return None

    def _process_job(self, job_file: Path, *, original_job_name: str) -> None:
        payload = json.loads(job_file.read_text(encoding='utf-8'))
        idempotency_key = self._job_idempotency_key(payload)
        kind = str(payload.get('kind', 'unknown')) if isinstance(payload, dict) else 'unknown'
        request_id, trace_id = self._resolve_job_context(
            payload=payload,
            original_job_name=original_job_name,
            idempotency_key=idempotency_key,
        )
        request_token, trace_token = set_request_context(request_id=request_id, trace_id=trace_id)
        try:
            logger.info(
                'Worker job processing started.',
                extra={
                    **self._context_extra(request_id, trace_id),
                    'event': 'worker_job_start',
                    'job_file': original_job_name,
                    'claimed_file': job_file.name,
                    'job_kind': kind,
                    'max_attempts': self.max_attempts,
                    'idempotency_key': idempotency_key,
                    'worker_id': self.worker_id,
                },
            )
            if idempotency_key in self._completed_jobs_by_key:
                self._write_duplicate_record(
                    job_file=job_file,
                    original_job_name=original_job_name,
                    kind=kind,
                    payload=payload,
                    idempotency_key=idempotency_key,
                    completed_job_file=self._completed_jobs_by_key[idempotency_key],
                    request_id=request_id,
                    trace_id=trace_id,
                )
                return

            attempt = 0
            while attempt < self.max_attempts:
                attempt += 1
                try:
                    self._dispatch_job(kind=kind, payload=payload)
                    completed_path = self.completed_dir / original_job_name
                    shutil.move(str(job_file), str(completed_path))
                    self._completed_jobs_by_key[idempotency_key] = completed_path.name
                    logger.info(
                        'Worker job completed.',
                        extra={
                            **self._context_extra(request_id, trace_id),
                            'event': 'worker_job_complete',
                            'job_file': original_job_name,
                            'claimed_file': job_file.name,
                            'job_kind': kind,
                            'status': 'completed',
                            'attempts': attempt,
                            'retries': max(0, attempt - 1),
                            'idempotency_key': idempotency_key,
                            'worker_id': self.worker_id,
                        },
                    )
                    return
                except Exception as exc:
                    transient = self._is_transient_failure(exc)
                    should_retry = transient and attempt < self.max_attempts
                    if should_retry:
                        delay_seconds = self._retry_delay_seconds(attempt)
                        logger.warning(
                            'Worker job attempt failed; retry scheduled.',
                            extra={
                                **self._context_extra(request_id, trace_id),
                                'event': 'worker_job_retry',
                                'job_file': original_job_name,
                                'claimed_file': job_file.name,
                                'job_kind': kind,
                                'attempt': attempt,
                                'max_attempts': self.max_attempts,
                                'retry_in_seconds': delay_seconds,
                                'error': str(exc),
                                'worker_id': self.worker_id,
                            },
                        )
                        if delay_seconds > 0:
                            time.sleep(delay_seconds)
                        continue
                    self._write_failed_job(
                        job_file=job_file,
                        original_job_name=original_job_name,
                        kind=kind,
                        payload=payload,
                        error=exc,
                        attempts=attempt,
                        transient=transient,
                        idempotency_key=idempotency_key,
                        request_id=request_id,
                        trace_id=trace_id,
                    )
                    return
        finally:
            reset_request_context(request_token=request_token, trace_token=trace_token)

    def _load_completed_job_index(self) -> dict:
        index = {}
        for completed_file in sorted(self.completed_dir.glob('*.json')):
            if '.duplicate' in completed_file.stem:
                continue
            try:
                payload = json.loads(completed_file.read_text(encoding='utf-8'))
            except Exception:
                logger.warning(
                    'Worker completed payload parsing failed; skipping idempotency indexing.',
                    extra={
                        'event': 'worker_completed_index_skip',
                        'completed_file': completed_file.name,
                    },
                )
                continue
            key = self._job_idempotency_key(payload)
            index.setdefault(key, completed_file.name)
        return index

    def _job_idempotency_key(self, payload) -> str:
        if isinstance(payload, dict):
            explicit = str(payload.get('idempotency_key', '')).strip()
            if explicit:
                return 'idempotency_key:%s' % explicit
            metadata = payload.get('metadata')
            if isinstance(metadata, dict):
                metadata_key = str(metadata.get('idempotency_key', '')).strip()
                if metadata_key:
                    return 'metadata.idempotency_key:%s' % metadata_key
        canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
        digest = hashlib.sha256(canonical.encode('utf-8')).hexdigest()
        return 'payload_sha256:%s' % digest

    def _resolve_job_context(
        self,
        *,
        payload: dict[str, Any],
        original_job_name: str,
        idempotency_key: str,
    ) -> tuple[str, str]:
        request_id = str(payload.get('request_id', '')).strip()
        trace_id = str(payload.get('trace_id', '')).strip()
        metadata = payload.get('metadata')
        if isinstance(metadata, dict):
            if not request_id:
                request_id = str(metadata.get('request_id', '')).strip()
            if not trace_id:
                trace_id = str(metadata.get('trace_id', '')).strip()

        if not request_id:
            seed = '%s|%s|%s' % (original_job_name, idempotency_key, self.worker_id)
            digest = hashlib.sha1(seed.encode('utf-8')).hexdigest()[:16]
            request_id = 'job-%s' % digest
        if not trace_id:
            trace_id = request_id
        return request_id, trace_id

    @staticmethod
    def _context_extra(request_id: str, trace_id: str) -> dict[str, str]:
        return {
            'request_id': request_id,
            'trace_id': trace_id,
        }

    def _write_duplicate_record(
        self,
        *,
        job_file: Path,
        original_job_name: str,
        kind: str,
        payload,
        idempotency_key: str,
        completed_job_file: str,
        request_id: str,
        trace_id: str,
    ) -> None:
        duplicate_path = self._reserve_duplicate_record_path(original_job_name)
        duplicate_payload = {
            'status': 'duplicate_skipped',
            'idempotency_key': idempotency_key,
            'request_id': request_id,
            'trace_id': trace_id,
            'job_file': original_job_name,
            'claimed_file': job_file.name,
            'job_kind': kind,
            'duplicate_of': completed_job_file,
            'payload': payload,
        }
        duplicate_path.write_text(
            json.dumps(duplicate_payload, ensure_ascii=False, indent=2) + '\n',
            encoding='utf-8',
        )
        if job_file.exists():
            job_file.unlink()
        logger.info(
            'Worker duplicate job skipped.',
            extra={
                **self._context_extra(request_id, trace_id),
                'event': 'worker_job_duplicate',
                'job_file': original_job_name,
                'claimed_file': job_file.name,
                'job_kind': kind,
                'idempotency_key': idempotency_key,
                'duplicate_record': duplicate_path.name,
                'duplicate_of': completed_job_file,
                'worker_id': self.worker_id,
            },
        )

    def _reserve_duplicate_record_path(self, job_filename: str) -> Path:
        stem = Path(job_filename).stem
        candidate = self.completed_dir / ('%s.duplicate.json' % stem)
        suffix = 2
        while candidate.exists():
            candidate = self.completed_dir / ('%s.duplicate-%s.json' % (stem, suffix))
            suffix += 1
        return candidate

    def _dispatch_job(self, *, kind: str, payload: dict) -> None:
        if kind == 'review_queue':
            self._dispatch_review_queue_job(payload)
            return
        if kind == 'rebuild_publication':
            self._dispatch_rebuild_publication_job(payload)
            return
        if kind == 'revise_skill':
            self._dispatch_revise_skill_job(payload)
            return
        self._dispatch_distill_request(kind=kind, payload=payload)

    def _dispatch_distill_request(self, *, kind: str, payload: dict) -> None:
        if kind == 'text':
            self.service.distill_text(TextDistillRequest.from_dict(payload))
            return
        if kind == 'audio':
            self.service.distill_audio(AudioDistillRequest.from_dict(payload))
            return
        if kind == 'image':
            self.service.distill_image(ImageDistillRequest.from_dict(payload))
            return
        if kind == 'tabular':
            self.service.distill_tabular(TabularDistillRequest.from_dict(payload))
            return
        if kind == 'video':
            self.service.distill_video(VideoDistillRequest.from_dict(payload))
            return
        if kind == 'corpus':
            self.service.distill_corpus(CorpusDistillRequest.from_dict(payload))
            return
        raise ValueError('Unsupported job kind: %s' % kind)

    def _dispatch_review_queue_job(self, payload: dict[str, Any]) -> None:
        repository = self._require_review_queue_repository()
        action = str(payload.get('action', 'claim')).strip().lower() or 'claim'
        if action == 'list':
            queue_status = str(payload.get('queue_status', 'pending')).strip() or 'pending'
            limit_raw = payload.get('limit', 100)
            limit = int(limit_raw) if str(limit_raw).strip() else 100
            repository.list_review_queue(queue_status=queue_status, limit=limit)
            return
        if action == 'claim':
            review_task_id = str(payload.get('review_task_id', '')).strip() or None
            consumer = str(payload.get('consumer', 'review-consumer')).strip() or 'review-consumer'
            repository.claim_review_task(review_task_id=review_task_id, consumer=consumer)
            return
        if action == 'consume':
            consumer = str(payload.get('consumer', 'review-consumer')).strip() or 'review-consumer'
            repository.consume_review_task(consumer=consumer)
            return
        if action == 'close':
            review_task_id = str(payload.get('review_task_id', '')).strip()
            if not review_task_id:
                raise ValueError('review_queue close action requires review_task_id.')
            status = str(payload.get('status', 'published')).strip() or 'published'
            closed_by = str(payload.get('closed_by', 'review-operator')).strip() or 'review-operator'
            review_notes = str(payload.get('review_notes', '')).strip()
            repository.close_review_task(
                review_task_id,
                status=status,
                closed_by=closed_by,
                review_notes=review_notes,
            )
            return
        raise ValueError('Unsupported review_queue action: %s' % action)

    def _dispatch_rebuild_publication_job(self, payload: dict[str, Any]) -> None:
        request_kind, request_payload = self._resolve_replay_request(payload)
        self._dispatch_distill_request(kind=request_kind, payload=request_payload)

    def _dispatch_revise_skill_job(self, payload: dict[str, Any]) -> None:
        existing_skill_id = str(payload.get('existing_skill_id', '')).strip()
        if not existing_skill_id:
            raise ValueError('revise_skill job requires existing_skill_id.')

        request_kind, request_payload = self._resolve_replay_request(payload)
        request_payload = dict(request_payload)
        if request_kind == 'corpus':
            metadata = request_payload.get('metadata')
            metadata_payload = dict(metadata) if isinstance(metadata, dict) else {}
            metadata_payload.setdefault('revise_existing_skill_id', existing_skill_id)
            request_payload['metadata'] = metadata_payload

        logger.info(
            'Worker revise_skill dispatched.',
            extra={
                'event': 'worker_revise_skill_dispatch',
                'existing_skill_id': existing_skill_id,
                'request_kind': request_kind,
            },
        )
        self._dispatch_distill_request(kind=request_kind, payload=request_payload)

    def _resolve_replay_request(self, payload: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        request_payload: dict[str, Any]
        raw_request_payload = payload.get('request')
        if isinstance(raw_request_payload, dict):
            request_payload = dict(raw_request_payload)
        else:
            bundle_path = str(payload.get('bundle_path', '')).strip()
            if not bundle_path:
                raise ValueError('Replay job requires request payload or bundle_path.')
            request_payload = self._load_request_payload_from_bundle(Path(bundle_path))

        goal_overrides = payload.get('goal_overrides')
        if isinstance(goal_overrides, dict) and goal_overrides:
            request_payload = self._apply_goal_overrides(request_payload, goal_overrides)

        request_kind = self._resolve_request_kind(payload=payload, request_payload=request_payload)
        return request_kind, request_payload

    def _load_request_payload_from_bundle(self, bundle_path: Path) -> dict[str, Any]:
        if not bundle_path.exists():
            raise ValueError('bundle_path does not exist: %s' % bundle_path)
        payload = json.loads(bundle_path.read_text(encoding='utf-8'))
        if not isinstance(payload, dict):
            raise ValueError('bundle_path payload must be a JSON object: %s' % bundle_path)
        request_payload = payload.get('request_payload')
        if not isinstance(request_payload, dict):
            raise ValueError('bundle_path payload does not include request_payload: %s' % bundle_path)
        return dict(request_payload)

    def _apply_goal_overrides(self, request_payload: dict[str, Any], goal_overrides: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(request_payload)
        current_goal = normalized.get('goal')
        goal_payload = dict(current_goal) if isinstance(current_goal, dict) else {}
        goal_payload.update(goal_overrides)
        normalized['goal'] = goal_payload
        return normalized

    def _resolve_request_kind(self, *, payload: dict[str, Any], request_payload: dict[str, Any]) -> str:
        request_kind = str(payload.get('request_kind', '')).strip().lower()
        if request_kind:
            return request_kind

        embedded_kind = str(request_payload.get('kind', '')).strip().lower()
        if embedded_kind:
            return embedded_kind

        if isinstance(request_payload.get('assets'), list):
            return 'corpus'
        if str(request_payload.get('video_path', '')).strip():
            return 'video'
        if str(request_payload.get('image_path', '')).strip():
            return 'image'
        if str(request_payload.get('audio_path', '')).strip() or str(request_payload.get('transcript_path', '')).strip():
            return 'audio'
        if str(request_payload.get('file_path', '')).strip():
            value_columns = request_payload.get('value_columns')
            entity_columns = request_payload.get('entity_columns')
            if value_columns is not None or entity_columns is not None:
                return 'tabular'
            return 'text'
        if str(request_payload.get('content', '')).strip():
            return 'text'
        raise ValueError('Unable to infer request kind for replay job.')

    def _require_review_queue_repository(self) -> ReviewQueueRepository:
        repository = getattr(self.service, 'repository', None)
        if not isinstance(repository, ReviewQueueRepository):
            raise ValueError('Service repository does not implement ReviewQueueRepository.')
        return repository

    def _write_failed_job(
        self,
        *,
        job_file: Path,
        original_job_name: str,
        kind: str,
        payload: dict,
        error: Exception,
        attempts: int,
        transient: bool,
        idempotency_key: str,
        request_id: str,
        trace_id: str,
    ) -> None:
        failure_path = self.failed_dir / original_job_name
        failure_payload = {
            'error': str(error),
            'payload': payload,
            'request_id': request_id,
            'trace_id': trace_id,
            'job_file': original_job_name,
            'claimed_file': job_file.name,
            'attempts': attempts,
            'transient': transient,
            'retry_exhausted': transient and attempts >= self.max_attempts,
            'idempotency_key': idempotency_key,
        }
        failure_path.write_text(
            json.dumps(failure_payload, ensure_ascii=False, indent=2) + '\n',
            encoding='utf-8',
        )
        if job_file.exists():
            job_file.unlink()
        logger.exception(
            'Worker job failed.',
            extra={
                **self._context_extra(request_id, trace_id),
                'event': 'worker_job_complete',
                'job_file': original_job_name,
                'claimed_file': job_file.name,
                'job_kind': kind,
                'status': 'failed',
                'attempts': attempts,
                'transient': transient,
                'worker_id': self.worker_id,
            },
        )

    def _is_transient_failure(self, error: Exception) -> bool:
        transient_error_types = (
            ProviderExecutionError,
            MediaProcessingError,
            TimeoutError,
            ConnectionError,
        )
        return isinstance(error, transient_error_types)

    def _retry_delay_seconds(self, attempt: int) -> float:
        if self.retry_base_delay_seconds <= 0:
            return 0.0
        exponent = max(attempt - 1, 0)
        return self.retry_base_delay_seconds * (self.retry_backoff_multiplier ** exponent)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Local worker for Omni Skill Pipeline')
    parser.add_argument('--jobs-root', default='data/jobs', help='Root directory containing pending/completed/failed job folders.')
    parser.add_argument(
        '--max-attempts',
        type=int,
        default=DEFAULT_WORKER_MAX_ATTEMPTS,
        help='Max attempts per job (includes first attempt).',
    )
    parser.add_argument(
        '--retry-base-delay-seconds',
        type=float,
        default=DEFAULT_WORKER_RETRY_BASE_DELAY_SECONDS,
        help='Base delay before retrying transient failures.',
    )
    parser.add_argument(
        '--retry-backoff-multiplier',
        type=float,
        default=DEFAULT_WORKER_RETRY_BACKOFF_MULTIPLIER,
        help='Exponential backoff multiplier for transient retry delay.',
    )
    return parser


def main(argv: list = None) -> int:
    args = build_parser().parse_args(argv)
    worker = LocalJobWorker(
        Path(args.jobs_root),
        max_attempts=args.max_attempts,
        retry_base_delay_seconds=args.retry_base_delay_seconds,
        retry_backoff_multiplier=args.retry_backoff_multiplier,
    )
    processed = worker.run_once()
    print('processed=%s' % processed)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
