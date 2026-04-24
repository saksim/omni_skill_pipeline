from __future__ import annotations

import argparse
import json
import os
import shutil
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

DEFAULT_ROOT = '.tmp_omni_media'
DEFAULT_RETENTION_HOURS = 24.0
ENV_ROOT = 'OMNI_TMP_MEDIA_ROOT'
ENV_RETENTION_HOURS = 'OMNI_TMP_MEDIA_RETENTION_HOURS'


@dataclass(slots=True)
class PruneResult:
    root: str
    dry_run: bool
    retention_hours: float
    cutoff_epoch: float
    scanned_entries: int = 0
    removed_entries: int = 0
    reclaimed_bytes: int = 0
    candidates: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)


def _resolve_root(cli_root: str | None) -> Path:
    raw = (cli_root or os.getenv(ENV_ROOT) or DEFAULT_ROOT).strip()
    return Path(raw).resolve()


def _resolve_retention_hours(cli_hours: float | None) -> float:
    if cli_hours is not None:
        return max(float(cli_hours), 0.0)
    raw = str(os.getenv(ENV_RETENTION_HOURS, str(DEFAULT_RETENTION_HOURS))).strip()
    try:
        return max(float(raw), 0.0)
    except ValueError:
        return DEFAULT_RETENTION_HOURS


def _path_size_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file() or path.is_symlink():
        try:
            return int(path.stat().st_size)
        except OSError:
            return 0

    total = 0
    for child in path.rglob('*'):
        if not child.is_file():
            continue
        try:
            total += int(child.stat().st_size)
        except OSError:
            continue
    return total


def _latest_mtime(path: Path) -> float:
    try:
        latest = float(path.stat().st_mtime)
    except OSError:
        return time.time()

    if path.is_dir():
        for child in path.rglob('*'):
            try:
                child_mtime = float(child.stat().st_mtime)
            except OSError:
                # Permission-denied children are treated as active to avoid accidental deletion.
                return time.time()
            if child_mtime > latest:
                latest = child_mtime
    return latest


def _remove_path(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
        return
    path.unlink()


def prune_scratch_root(
    root: Path,
    *,
    retention_hours: float,
    now_epoch: float | None = None,
    dry_run: bool = False,
) -> PruneResult:
    now = float(time.time() if now_epoch is None else now_epoch)
    retention_seconds = max(float(retention_hours), 0.0) * 3600.0
    cutoff = now - retention_seconds

    result = PruneResult(
        root=str(root),
        dry_run=dry_run,
        retention_hours=float(retention_hours),
        cutoff_epoch=cutoff,
    )

    if not root.exists():
        return result
    if not root.is_dir():
        result.failures.append('Scratch root is not a directory: %s' % root)
        return result

    try:
        entries = sorted(root.iterdir(), key=lambda item: item.name)
    except OSError as exc:
        result.failures.append('Cannot iterate scratch root %s :: %s' % (root, exc))
        return result

    for entry in entries:
        result.scanned_entries += 1
        latest_mtime = _latest_mtime(entry)
        if latest_mtime > cutoff:
            continue

        result.candidates.append(str(entry))
        reclaimed_bytes = _path_size_bytes(entry)
        try:
            if not dry_run:
                _remove_path(entry)
            result.removed_entries += 1
            result.reclaimed_bytes += reclaimed_bytes
        except OSError as exc:
            result.failures.append('%s :: %s' % (entry, exc))

    return result


def _format_human_result(result: PruneResult) -> str:
    lines = [
        'Scratch root: %s' % result.root,
        'Dry run: %s' % str(result.dry_run).lower(),
        'Retention hours: %s' % result.retention_hours,
        'Scanned entries: %s' % result.scanned_entries,
        'Removed entries: %s' % result.removed_entries,
        'Reclaimed bytes: %s' % result.reclaimed_bytes,
    ]
    if result.candidates:
        lines.append('Candidates:')
        lines.extend('- %s' % item for item in result.candidates)
    if result.failures:
        lines.append('Failures:')
        lines.extend('- %s' % item for item in result.failures)
    return '\n'.join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Prune stale artifacts under .tmp_omni_media scratch root.',
    )
    parser.add_argument(
        '--root',
        default=None,
        help='Scratch root path. Defaults to env %s or %s.' % (ENV_ROOT, DEFAULT_ROOT),
    )
    parser.add_argument(
        '--retention-hours',
        type=float,
        default=None,
        help='Delete entries older than this many hours. Defaults to env %s or %s.'
        % (ENV_RETENTION_HOURS, DEFAULT_RETENTION_HOURS),
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Only report deletion candidates; do not remove files.',
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Emit machine-readable JSON output.',
    )
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    root = _resolve_root(args.root)
    retention_hours = _resolve_retention_hours(args.retention_hours)
    result = prune_scratch_root(
        root,
        retention_hours=retention_hours,
        dry_run=bool(args.dry_run),
    )

    if args.json:
        print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    else:
        print(_format_human_result(result))

    if result.failures:
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
