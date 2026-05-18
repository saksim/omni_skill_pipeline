from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.adapters.text import TextAdapter
from omni_skill_pipeline.extraction.modality.document_parser import DocumentStructureParser
from omni_skill_pipeline.models import ContentType, DistillGoal, TextDistillRequest


class DocumentParserTests(unittest.TestCase):
    def test_parser_extracts_section_table_code_and_figure_blocks(self) -> None:
        parser = DocumentStructureParser()
        sample = (
            "# Incident Runbook\n\n"
            "Review timeline before triage.\n\n"
            "## Evidence Matrix\n\n"
            "| signal | status |\n"
            "| --- | --- |\n"
            "| latency | high |\n\n"
            "```sql\n"
            "select * from incidents;\n"
            "```\n\n"
            "![Latency chart](./latency.png)\n"
            "Figure 1: dashboard snapshot\n"
        )

        blocks = parser.parse(sample)
        spans = {item.span_ref for item in blocks}
        table_blocks = [item for item in blocks if item.content_type == ContentType.TABLE]
        code_blocks = [item for item in blocks if ":code:" in item.span_ref]
        figure_blocks = [item for item in blocks if ":figure:" in item.span_ref]

        self.assertIn("section:1", spans)
        self.assertIn("section:1.1", spans)
        self.assertTrue(table_blocks)
        self.assertTrue(code_blocks)
        self.assertGreaterEqual(len(figure_blocks), 1)
        self.assertTrue(any("section_path:1.1" in item.tags for item in table_blocks))

    def test_text_adapter_emits_structured_document_evidence(self) -> None:
        adapter = TextAdapter()
        sample = (
            "# Operations Guide\n\n"
            "## Query Review\n\n"
            "| query | p95 |\n"
            "| --- | --- |\n"
            "| find_users | 420ms |\n\n"
            "```python\n"
            "print('review')\n"
            "```\n\n"
            "![chart](./chart.png)\n"
        )
        loaded = adapter.load(
            TextDistillRequest(
                title="ops guide",
                content=sample,
                goal=DistillGoal.from_dict({"domain": "ops"}),
            )
        )

        spans = {item.span_ref for item in loaded.evidence_units}
        content_types = {item.content_type for item in loaded.evidence_units}

        self.assertIn("section:1", spans)
        self.assertIn("section:1.1", spans)
        self.assertTrue(any(":code:" in span for span in spans))
        self.assertTrue(any(":figure:" in span for span in spans))
        self.assertIn(ContentType.TABLE, content_types)
        self.assertTrue(
            any("section_path:1.1" in item.tags for item in loaded.evidence_units if ":table:" in item.span_ref)
        )

    def test_parser_extracts_toc_table_grid_and_code_style_for_pdf_docx_text(self) -> None:
        parser = DocumentStructureParser()
        sample = (
            "[TOC L1] Incident Response Overview\n"
            "1.1 Timeline Reconstruction ........ 12\n"
            "\n"
            "+-----------+-----------+\n"
            "| metric    | value     |\n"
            "+-----------+-----------+\n"
            "| latency   | 420ms     |\n"
            "+-----------+-----------+\n"
            "\n"
            "    def rebuild_timeline(events):\n"
            "        return sorted(events)\n"
        )
        blocks = parser.parse(sample, source_format=".pdf")

        toc_blocks = [item for item in blocks if "block:toc" in item.tags]
        table_grid_blocks = [item for item in blocks if "block:table_grid" in item.tags]
        code_style_blocks = [item for item in blocks if "code_style:indented" in item.tags]

        self.assertGreaterEqual(len(toc_blocks), 2)
        self.assertTrue(any("toc_level:1" in item.tags for item in toc_blocks))
        self.assertTrue(table_grid_blocks)
        self.assertEqual(table_grid_blocks[0].content_type, ContentType.TABLE)
        self.assertTrue(code_style_blocks)
        self.assertIn("def rebuild_timeline", code_style_blocks[0].content)


if __name__ == "__main__":
    unittest.main()
