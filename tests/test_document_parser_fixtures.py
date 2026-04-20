from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.extraction.modality.document_parser import DocumentStructureParser
from omni_skill_pipeline.models import ContentType


class DocumentParserFixtureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = DocumentStructureParser()
        self.fixture_root = REPO_ROOT / "tests" / "fixtures" / "document_parser"

    def test_docx_fixture_preserves_toc_table_code_and_figure(self) -> None:
        text = (self.fixture_root / "docx_real_sample.txt").read_text(encoding="utf-8")
        blocks = self.parser.parse(text, source_format=".docx")
        tags = {tag for item in blocks for tag in item.tags}
        content_types = {item.content_type for item in blocks}

        self.assertIn("block:toc", tags)
        self.assertIn("block:table", tags)
        self.assertIn("block:code", tags)
        self.assertIn("block:figure", tags)
        self.assertIn(ContentType.TABLE, content_types)

    def test_pdf_fixture_preserves_toc_table_grid_and_code_style(self) -> None:
        text = (self.fixture_root / "pdf_real_sample.txt").read_text(encoding="utf-8")
        blocks = self.parser.parse(text, source_format=".pdf")
        tags = {tag for item in blocks for tag in item.tags}
        content_types = {item.content_type for item in blocks}

        self.assertIn("block:toc", tags)
        self.assertIn("block:table_grid", tags)
        self.assertIn("code_style:indented", tags)
        self.assertIn(ContentType.TABLE, content_types)


if __name__ == "__main__":
    unittest.main()
