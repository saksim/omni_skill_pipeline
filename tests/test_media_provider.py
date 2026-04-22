from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.providers.media import FFmpegMediaProcessor


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


if __name__ == "__main__":
    unittest.main()
