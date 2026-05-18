from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.extraction.modality.timeseries_parser import TimeSeriesSemanticParser


class TimeSeriesParserTests(unittest.TestCase):
    def test_parser_extracts_baseline_change_points_and_drift(self) -> None:
        parser = TimeSeriesSemanticParser()
        timestamps = [
            "2026-04-21T00:00:00",
            "2026-04-21T00:01:00",
            "2026-04-21T00:02:00",
            "2026-04-21T00:03:00",
            "2026-04-21T00:04:00",
            "2026-04-21T00:05:00",
            "2026-04-21T00:06:00",
            "2026-04-21T00:07:00",
            "2026-04-21T00:08:00",
            "2026-04-21T00:09:00",
            "2026-04-21T00:10:00",
            "2026-04-21T00:11:00",
        ]
        values = [100.0, 102.0, 101.0, 103.0, 100.0, 102.0, 150.0, 158.0, 166.0, 174.0, 182.0, 190.0]

        parsed = parser.parse(timestamps=timestamps, values=values)

        self.assertGreater(parsed.baseline_mean, 99.0)
        self.assertLess(parsed.baseline_mean, 105.0)
        self.assertIn(parsed.drift_label, {"upward_drift", "stable"})
        self.assertGreaterEqual(parsed.drift_score, 0.0)
        self.assertTrue(parsed.change_points)
        self.assertTrue(any(item.timestamp == "2026-04-21T00:06:00" for item in parsed.change_points))
        self.assertTrue(parsed.anomaly_intervals)
        self.assertIn("2026-04-21T00:06:00", parsed.anomaly_timestamps)


if __name__ == "__main__":
    unittest.main()
