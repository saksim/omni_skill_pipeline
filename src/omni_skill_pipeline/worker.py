from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from omni_skill_pipeline.models import (
    AudioDistillRequest,
    ImageDistillRequest,
    TabularDistillRequest,
    TextDistillRequest,
    VideoDistillRequest,
)
from omni_skill_pipeline.service import build_service


class LocalJobWorker(object):
    def __init__(self, jobs_root: Path) -> None:
        self.jobs_root = Path(jobs_root)
        self.pending_dir = self.jobs_root / 'pending'
        self.completed_dir = self.jobs_root / 'completed'
        self.failed_dir = self.jobs_root / 'failed'
        for directory in (self.pending_dir, self.completed_dir, self.failed_dir):
            directory.mkdir(parents=True, exist_ok=True)
        self.service = build_service()

    def run_once(self) -> int:
        processed = 0
        for job_file in sorted(self.pending_dir.glob('*.json')):
            processed += 1
            self._process_job(job_file)
        return processed

    def _process_job(self, job_file: Path) -> None:
        payload = json.loads(job_file.read_text(encoding='utf-8'))
        try:
            kind = payload['kind']
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
        except Exception as exc:
            failure_path = self.failed_dir / job_file.name
            failure_path.write_text(
                json.dumps({'error': str(exc), 'payload': payload}, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            job_file.unlink()


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
