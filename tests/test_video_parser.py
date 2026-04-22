from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.extraction.modality.video_parser import VideoStructureParser
from omni_skill_pipeline.models import ContentType, EvidenceUnit
from omni_skill_pipeline.providers.base import SampledFrame


class VideoParserTests(unittest.TestCase):
    def test_video_parser_emits_scene_cluster_frame_event_and_subtitle_alignment(self) -> None:
        parser = VideoStructureParser()
        frames = [
            SampledFrame(path=Path("f1.jpg"), source="scene", timestamp_seconds=1.0, scene_score=0.68),
            SampledFrame(path=Path("f2.jpg"), source="timeline", timestamp_seconds=5.0),
            SampledFrame(path=Path("f3.jpg"), source="scene", timestamp_seconds=16.0, scene_score=0.71),
        ]
        evidence_units = [
            EvidenceUnit(
                asset_id="asset-video",
                span_ref="frame:0001@1.00s:ocr",
                content_type=ContentType.OCR,
                content="Service degraded, rollback started.",
                tags=["source:scene"],
            ),
            EvidenceUnit(
                asset_id="asset-video",
                span_ref="frame:0001@1.00s:scene",
                content_type=ContentType.SCENE,
                content="Dashboard shows incident banner and active rollback dialog.",
            ),
            EvidenceUnit(
                asset_id="asset-video",
                span_ref="frame:0002@5.00s:scene",
                content_type=ContentType.SCENE,
                content="Operator opens alert panel and checks latency chart.",
            ),
            EvidenceUnit(
                asset_id="asset-video",
                span_ref="video:timestamp:0.00-2.00",
                content_type=ContentType.SPEECH,
                content="Can we confirm the blast radius before rollback?",
                tags=["utterance_act:question", "source:audio_track"],
                confidence=0.82,
            ),
            EvidenceUnit(
                asset_id="asset-video",
                span_ref="video:timestamp:15.20-17.00",
                content_type=ContentType.SPEECH,
                content="Decision: rollback completed, verify p95 and error rate now.",
                tags=["utterance_act:decision", "source:audio_track"],
                confidence=0.85,
            ),
        ]

        parsed = parser.parse(frames=frames, evidence_units=evidence_units)

        scene_clusters = [item for item in parsed.evidence_blocks if item.span_ref.startswith("video:scene_cluster:")]
        frame_events = [item for item in parsed.evidence_blocks if item.span_ref.endswith(":event")]
        subtitle_alignments = [item for item in parsed.evidence_blocks if ":subtitle:" in item.span_ref]

        self.assertGreaterEqual(len(scene_clusters), 2)
        self.assertGreaterEqual(len(frame_events), 2)
        self.assertEqual(len(subtitle_alignments), 2)
        self.assertEqual(parsed.frame_event_count, len(frame_events))
        self.assertEqual(parsed.subtitle_alignment_count, len(subtitle_alignments))
        self.assertEqual(parsed.scene_clusters[0]["frame_count"], 2)
        self.assertEqual(parsed.scene_clusters[1]["frame_count"], 1)
        self.assertTrue(all(item.content_type == ContentType.EVENT for item in frame_events))
        self.assertTrue(all(item.content_type == ContentType.SPEECH for item in subtitle_alignments))
        self.assertTrue(any("aligned_frame:frame:0001@1.00s" in tag for item in subtitle_alignments for tag in item.tags))
        self.assertTrue(any("aligned_frame:frame:0003@16.00s" in tag for item in subtitle_alignments for tag in item.tags))


if __name__ == "__main__":
    unittest.main()
