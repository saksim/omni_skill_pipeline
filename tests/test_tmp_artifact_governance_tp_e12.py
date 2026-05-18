from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.adapters.video import VideoAdapter
from omni_skill_pipeline.models import Asset, ContentType, EvidenceUnit, LoadedAsset, Modality, VideoDistillRequest
from omni_skill_pipeline.providers.base import SampledFrame, VideoMetadata


class _FakeMediaProcessor(object):
    def probe(self, video_path: Path) -> VideoMetadata:
        return VideoMetadata(duration_seconds=12.0, width=320, height=200, fps=1.0, frame_count=12)

    def extract_audio(self, video_path: Path, work_dir: Path) -> Path:
        audio_path = work_dir / 'audio_track.mp3'
        audio_path.write_bytes(b'fake-audio')
        return audio_path

    def extract_keyframes(
        self,
        video_path: Path,
        work_dir: Path,
        *,
        interval_seconds: int,
        max_frames: int,
        scene_threshold: float | None = None,
        dedupe_distance: int | None = None,
    ) -> list[SampledFrame]:
        frame_path = work_dir / 'frame_001.jpg'
        frame_path.write_bytes(b'frame')
        return [SampledFrame(path=frame_path, source='scene', timestamp_seconds=1.0, scene_score=0.61)]


class _FakeAudioAdapter(object):
    def load(self, request: object) -> LoadedAsset:
        asset = Asset(modality=Modality.AUDIO, source_uri='inline://audio')
        evidence = EvidenceUnit(
            asset_id=asset.asset_id,
            span_ref='timestamp:0.00-1.00',
            content_type=ContentType.SPEECH,
            content='Rebuild the incident timeline.',
            confidence=0.9,
        )
        return LoadedAsset(
            asset=asset,
            evidence_units=[evidence],
            title_hint='fake-audio',
            adapter_metadata={},
        )


class TempArtifactGovernanceTpE12Tests(unittest.TestCase):
    def test_video_adapter_marks_scratch_cleanup_cleaned_on_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            scratch_root = root / '.tmp_omni_media'
            video_path = root / 'fixture.mp4'
            video_path.write_bytes(b'fake-video')

            adapter = VideoAdapter(
                media_processor=_FakeMediaProcessor(),
                audio_adapter=_FakeAudioAdapter(),
                scratch_root=scratch_root,
            )
            loaded = adapter.load(VideoDistillRequest(video_path=str(video_path), title='cleanup-success'))

            cleanup = loaded.adapter_metadata.get('scratch_cleanup')
            self.assertIsInstance(cleanup, dict)
            self.assertEqual(cleanup.get('status'), 'cleaned')
            self.assertEqual(list(scratch_root.glob('omni_video_*')), [])

    def test_video_adapter_records_deferred_cleanup_when_rmtree_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            scratch_root = root / '.tmp_omni_media'
            video_path = root / 'fixture.mp4'
            video_path.write_bytes(b'fake-video')

            adapter = VideoAdapter(
                media_processor=_FakeMediaProcessor(),
                audio_adapter=_FakeAudioAdapter(),
                scratch_root=scratch_root,
            )
            with patch('omni_skill_pipeline.adapters.video.shutil.rmtree', side_effect=OSError('cleanup locked')):
                loaded = adapter.load(VideoDistillRequest(video_path=str(video_path), title='cleanup-failure'))

            cleanup = loaded.adapter_metadata.get('scratch_cleanup')
            self.assertIsInstance(cleanup, dict)
            self.assertEqual(cleanup.get('status'), 'deferred')
            self.assertEqual(cleanup.get('strategy'), 'prune_tmp_media')

            recovery_log = Path(str(cleanup.get('recovery_log')))
            self.assertTrue(recovery_log.exists())
            entries = [
                json.loads(line)
                for line in recovery_log.read_text(encoding='utf-8').splitlines()
                if line.strip()
            ]
            self.assertGreaterEqual(len(entries), 1)
            self.assertEqual(entries[-1].get('strategy'), 'prune_tmp_media')


if __name__ == '__main__':
    unittest.main()
