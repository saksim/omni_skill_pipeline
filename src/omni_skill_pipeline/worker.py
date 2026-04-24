from __future__ import annotations

import argparse
import json
import logging
import shutil
from pathlib import Path

from omni_skill_pipeline.logging_utils import configure_logging
from omni_skill_pipeline.models import (
    AudioDistillRequest,
    ImageDistillRequest,
    TabularDistillRequest,
    TextDistillRequest,
    VideoDistillRequest,
)
from omni_skill_pipeline.service import build_service

logger = logging.getLogger(__name__)


class LocalJobWorker(object):
    def __init__(self, jobs_root: Path) -> None:
        configure_logging(service_name='worker')
        self.jobs_root = Path(jobs_root)
        self.pending_dir = self.jobs_root / 'pending'
        self.completed_dir = self.jobs_root / 'completed'
        self.failed_dir = self.jobs_root / 'failed'
        for directory in (self.pending_dir, self.completed_dir, self.failed_dir):
            directory.mkdir(parents=True, exist_ok=True)
        self.service = build_service()
        logger.info(
            'Worker initialized.',
            extra={
                'event': 'worker_init',
                'jobs_root': str(self.jobs_root),
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
            processed += 1
            self._process_job(job_file)
        logger.info(
            'Worker scan completed.',
            extra={
                'event': 'worker_scan_complete',
                'jobs_root': str(self.jobs_root),
                'processed': processed,
            },
        )
        return processed

    def _process_job(self, job_file: Path) -> None:
        payload = json.loads(job_file.read_text(encoding='utf-8'))
        kind = str(payload.get('kind', 'unknown')) if isinstance(payload, dict) else 'unknown'
        logger.info(
            'Worker job processing started.',
            extra={
                'event': 'worker_job_start',
                'job_file': job_file.name,
                'job_kind': kind,
            },
        )
        try:
            if kind == 'text':
                self.service.distill_text(TextDistillRequest.from_dict(payload))
            elif kind == 'audio':
                self.service.distill_audio(AudioDistillRequest.from_dict(payload))
            elif kind == 'image':
                self.service.distill_image(ImageDistillRequest.from_dict(payload))
            elif kind == 'tabular':
                self.service.distill_tabular(TabularDistillRequest.from_dict(payload))
            elif kind == 'video':
                self.service.distill_video(VideoDistillRequest.from_dict(payload))
            else:
                raise ValueError('Unsupported job kind: %s' % kind)
            shutil.move(str(job_file), str(self.completed_dir / job_file.name))
            logger.info(
                'Worker job completed.',
                extra={
                    'event': 'worker_job_complete',
                    'job_file': job_file.name,
                    'job_kind': kind,
                    'status': 'completed',
                },
            )
        except Exception as exc:
            failure_path = self.failed_dir / job_file.name
            failure_path.write_text(
                json.dumps({'error': str(exc), 'payload': payload}, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            job_file.unlink()
            logger.exception(
                'Worker job failed.',
                extra={
                    'event': 'worker_job_complete',
                    'job_file': job_file.name,
                    'job_kind': kind,
                    'status': 'failed',
                },
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Local worker for Omni Skill Pipeline')
    parser.add_argument('--jobs-root', default='data/jobs', help='Root directory containing pending/completed/failed job folders.')
    return parser


def main(argv: list = None) -> int:
    args = build_parser().parse_args(argv)
    worker = LocalJobWorker(Path(args.jobs_root))
    processed = worker.run_once()
    print('processed=%s' % processed)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
