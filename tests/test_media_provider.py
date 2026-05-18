from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.providers.media import FFmpegMediaProcessor
from omni_skill_pipeline.providers.base import SampledFrame


class MediaProcessorTests(unittest.TestCase):
    def test_parse_showinfo_scene_scores_extracts_numeric_scores(self) -> None:
        processor = FFmpegMediaProcessor()
        stderr_payload = "\n".join(
            [
                "[Parsed_showinfo_0 @ 000001] n:1 pts_time:1.00 lavfi.scene_score=0.632",
                "[Parsed_showinfo_0 @ 000001] n:2 pts_time:2.00 scene_score:0.781",
                "[Parsed_showinfo_0 @ 000001] n:3 pts_time:3.00 scene:0.455",
                "[Parsed_showinfo_0 @ 000001] n:4 pts_time:4.00 no_score_here",
            ]
        )

        scores = processor._parse_showinfo_scene_scores(stderr_payload)
        self.assertEqual(scores, [0.632, 0.781, 0.455])

    def test_cleanup_unselected_frames_keeps_selected_only(self) -> None:
        processor = FFmpegMediaProcessor()
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            kept = root / 'selected_001.jpg'
            stale_a = root / 'candidate_001.jpg'
            stale_b = root / 'candidate_002.jpg'
            for path in (kept, stale_a, stale_b):
                path.write_bytes(b'frame')

            candidates = [
                SampledFrame(path=kept, source='scene', timestamp_seconds=1.0),
                SampledFrame(path=stale_a, source='timeline', timestamp_seconds=2.0),
                SampledFrame(path=stale_b, source='fallback', timestamp_seconds=3.0),
            ]
            selected = [SampledFrame(path=kept, source='scene', timestamp_seconds=1.0)]

            processor._cleanup_unselected_frames(candidates, selected)

            self.assertTrue(kept.exists())
            self.assertFalse(stale_a.exists())
            self.assertFalse(stale_b.exists())


if __name__ == "__main__":
    unittest.main()
