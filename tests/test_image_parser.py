from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.extraction.modality.image_parser import ImageStructureParser
from omni_skill_pipeline.models import ContentType
from omni_skill_pipeline.providers.base import FrameAnalysis, OCRBlock, OCRResult


class ImageParserTests(unittest.TestCase):
    def test_parser_groups_ocr_into_regions_with_layout_roles(self) -> None:
        parser = ImageStructureParser()
        ocr_result = OCRResult(
            text="Service status: degraded\nPrimary region: shanghai\np95 latency: 420ms",
            blocks=[
                OCRBlock(text="Service status: degraded", confidence=0.91),
                OCRBlock(text="Primary region: shanghai", confidence=0.9),
                OCRBlock(text="p95 latency: 420ms", confidence=0.89),
            ],
            engine="fake-ocr",
        )
        blocks = parser.parse_ocr_regions(ocr_result)

        self.assertGreaterEqual(len(blocks), 3)
        self.assertTrue(all(item.content_type == ContentType.OCR for item in blocks))
        self.assertTrue(any("layout_role:status" in item.tags for item in blocks))
        self.assertTrue(any("layout_role:region" in item.tags for item in blocks))
        self.assertTrue(any("layout_role:metric" in item.tags for item in blocks))

    def test_parser_emits_layout_summary_block(self) -> None:
        parser = ImageStructureParser()
        analysis = FrameAnalysis(
            image_path=Path("demo.png"),
            summary="Dashboard shows degraded banner and latency spike chart.",
            tags=["dashboard", "latency"],
        )
        blocks = parser.parse_layout_summary(analysis)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].content_type, ContentType.SCENE)
        self.assertIn("block:layout", blocks[0].tags)
        self.assertIn("layout_role:chart", blocks[0].tags)


if __name__ == "__main__":
    unittest.main()
