from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

SCRIPT_PATH = REPO_ROOT / 'scripts' / 'prune_tmp_media.py'
SPEC = importlib.util.spec_from_file_location('prune_tmp_media', SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:  # pragma: no cover - guard for import loader failures
    raise RuntimeError('Failed to load prune_tmp_media script module.')
PRUNE_MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PRUNE_MODULE
SPEC.loader.exec_module(PRUNE_MODULE)


def _touch_file(path: Path, *, mtime: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('artifact', encoding='utf-8')
    os.utime(path, (mtime, mtime))


class TmpMediaPruneTests(unittest.TestCase):
    def test_dry_run_reports_old_entries_without_deleting(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir) / '.tmp_omni_media'
            old_file = root / 'old' / 'chunk.bin'
            fresh_file = root / 'fresh' / 'chunk.bin'

            _touch_file(old_file, mtime=100.0)
            _touch_file(fresh_file, mtime=9800.0)

            result = PRUNE_MODULE.prune_scratch_root(
                root,
                retention_hours=1.0,
                now_epoch=10000.0,
                dry_run=True,
            )

            self.assertEqual(result.scanned_entries, 2)
            self.assertEqual(result.removed_entries, 1)
            self.assertIn(str(root / 'old'), result.candidates)
            self.assertTrue((root / 'old').exists())
            self.assertTrue((root / 'fresh').exists())

    def test_prune_removes_only_expired_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir) / '.tmp_omni_media'
            old_file = root / 'stale' / 'chunk.bin'
            fresh_file = root / 'hot' / 'chunk.bin'

            _touch_file(old_file, mtime=100.0)
            _touch_file(fresh_file, mtime=9950.0)

            result = PRUNE_MODULE.prune_scratch_root(
                root,
                retention_hours=1.0,
                now_epoch=10000.0,
                dry_run=False,
            )

            self.assertEqual(result.removed_entries, 1)
            self.assertFalse((root / 'stale').exists())
            self.assertTrue((root / 'hot').exists())
            self.assertGreater(result.reclaimed_bytes, 0)

    def test_missing_root_returns_clean_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir) / '.tmp_omni_media'
            result = PRUNE_MODULE.prune_scratch_root(
                root,
                retention_hours=24.0,
                now_epoch=20000.0,
                dry_run=False,
            )
            self.assertEqual(result.scanned_entries, 0)
            self.assertEqual(result.removed_entries, 0)
            self.assertEqual(result.failures, [])

    def test_resolve_retention_hours_falls_back_on_invalid_env_value(self) -> None:
        env_name = 'OMNI_TMP_MEDIA_RETENTION_HOURS'
        previous = os.environ.get(env_name)
        try:
            os.environ[env_name] = 'not-a-number'
            hours = PRUNE_MODULE._resolve_retention_hours(None)
        finally:
            if previous is None:
                os.environ.pop(env_name, None)
            else:
                os.environ[env_name] = previous

        self.assertEqual(hours, PRUNE_MODULE.DEFAULT_RETENTION_HOURS)


if __name__ == '__main__':
    unittest.main()
