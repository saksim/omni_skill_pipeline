from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from omni_skill_pipeline.models import ContentType


_HEADING_RE = re.compile(r"^(?P<marks>#{1,6})\s+(?P<title>.+?)\s*$")
_FIGURE_MARKDOWN_RE = re.compile(r"^!\[(?P<alt>[^\]]*)\]\((?P<src>[^)]+)\)\s*$")
_FIGURE_CAPTION_RE = re.compile(r"^(?:figure|fig)\s*[\dA-Za-z\-_.]*\s*[:.)\-]\s+.+$", re.IGNORECASE)
_TOC_LINE_RE = re.compile(
    r"^(?:(?P<idx>\d+(?:\.\d+)*)\s+)?(?P<title>[^\n]+?)\s*\.{2,}\s*(?P<page>\d+)\s*$",
    re.IGNORECASE,
)
_TOC_MARKER_RE = re.compile(r"^\[TOC(?:\s+L(?P<level>\d+))?\]\s+(?P<title>.+?)\s*$", re.IGNORECASE)
_ASCII_GRID_BORDER_RE = re.compile(r"^\+(?:[-=]+\+){2,}\s*$")
_CODE_STYLE_RE = re.compile(
    r"^(?:\s{4,}|\t+|def\s+|class\s+|if\s+|for\s+|while\s+|return\b|select\b|with\b|insert\b|update\b|delete\b|create\b|"
    r"function\s+|const\s+|let\s+|var\s+|public\s+|private\s+|#include\b|</?\w+)",
    re.IGNORECASE,
)


@dataclass(slots=True)
class ParsedDocumentBlock:
    span_ref: str
    content_type: ContentType
    content: str
    confidence: float
    tags: list[str] = field(default_factory=list)


class DocumentStructureParser(object):
    def parse(self, raw_text: str, *, source_format: str = "") -> list[ParsedDocumentBlock]:
        normalized = raw_text.replace("\r\n", "\n").replace("\r", "\n")
        lines = normalized.split("\n")
        blocks: list[ParsedDocumentBlock] = []
        paragraph_buffer: list[str] = []

        section_counters = [0] * 6
        current_section = "root"

        paragraph_index = 0
        table_index = 0
        code_index = 0
        figure_index = 0
        toc_index = 0

        def section_tag() -> str:
            return "section_path:%s" % current_section

        def flush_paragraph() -> None:
            nonlocal paragraph_index
            text = "\n".join(item for item in paragraph_buffer if item.strip()).strip()
            paragraph_buffer.clear()
            if not text:
                return
            paragraph_index += 1
            blocks.append(
                ParsedDocumentBlock(
                    span_ref="section:%s:paragraph:%04d" % (current_section, paragraph_index),
                    content_type=ContentType.TEXT,
                    content=text,
                    confidence=0.86,
                    tags=[section_tag(), "block:paragraph"],
                )
            )

        line_count = len(lines)
        index = 0
        while index < line_count:
            line = lines[index]
            stripped = line.strip()

            if not stripped:
                flush_paragraph()
                index += 1
                continue

            heading_match = _HEADING_RE.match(stripped)
            if heading_match:
                flush_paragraph()
                level = len(heading_match.group("marks"))
                title = heading_match.group("title").strip()
                section_counters[level - 1] += 1
                for reset_level in range(level, len(section_counters)):
                    section_counters[reset_level] = 0
                current_section = ".".join(
                    str(section_counters[item]) for item in range(level) if section_counters[item] > 0
                ) or "root"
                parent_section = ".".join(
                    str(section_counters[item]) for item in range(level - 1) if section_counters[item] > 0
                ) or "root"
                blocks.append(
                    ParsedDocumentBlock(
                        span_ref="section:%s" % current_section,
                        content_type=ContentType.TEXT,
                        content=title,
                        confidence=0.9,
                        tags=[
                            section_tag(),
                            "block:section",
                            "section_level:%s" % level,
                            "section_parent:%s" % parent_section,
                        ],
                    )
                )
                index += 1
                continue

            if self._is_code_fence_start(stripped):
                flush_paragraph()
                code_index += 1
                fence = stripped[:3]
                code_lines: list[str] = []
                index += 1
                while index < line_count:
                    candidate = lines[index]
                    if candidate.strip().startswith(fence):
                        break
                    code_lines.append(candidate)
                    index += 1
                if index < line_count and lines[index].strip().startswith(fence):
                    index += 1
                content = "\n".join(code_lines).strip()
                if not content:
                    content = "(empty code block)"
                blocks.append(
                    ParsedDocumentBlock(
                        span_ref="section:%s:code:%04d" % (current_section, code_index),
                        content_type=ContentType.TEXT,
                        content=content,
                        confidence=0.84,
                        tags=[section_tag(), "block:code"],
                    )
                )
                continue

            toc_payload = self._parse_toc_line(stripped, source_format=source_format)
            if toc_payload is not None:
                flush_paragraph()
                toc_index += 1
                toc_title, toc_level, toc_page = toc_payload
                blocks.append(
                    ParsedDocumentBlock(
                        span_ref="section:%s:toc:%04d" % (current_section, toc_index),
                        content_type=ContentType.TEXT,
                        content=toc_title,
                        confidence=0.78,
                        tags=[
                            section_tag(),
                            "block:toc",
                            "toc_level:%s" % toc_level,
                            "toc_page:%s" % toc_page,
                        ],
                    )
                )
                index += 1
                continue

            if self._looks_like_ascii_grid_start(lines, index):
                flush_paragraph()
                table_index += 1
                grid_lines, consumed = self._collect_ascii_grid(lines, index)
                blocks.append(
                    ParsedDocumentBlock(
                        span_ref="section:%s:table:%04d" % (current_section, table_index),
                        content_type=ContentType.TABLE,
                        content="\n".join(grid_lines).strip(),
                        confidence=0.86,
                        tags=[section_tag(), "block:table", "block:table_grid"],
                    )
                )
                index += consumed
                continue

            if self._looks_like_table_header(lines, index):
                flush_paragraph()
                table_index += 1
                table_lines = [lines[index].rstrip(), lines[index + 1].rstrip()]
                index += 2
                while index < line_count:
                    candidate = lines[index].rstrip()
                    if not candidate.strip() or "|" not in candidate:
                        break
                    table_lines.append(candidate)
                    index += 1
                blocks.append(
                    ParsedDocumentBlock(
                        span_ref="section:%s:table:%04d" % (current_section, table_index),
                        content_type=ContentType.TABLE,
                        content="\n".join(table_lines).strip(),
                        confidence=0.88,
                        tags=[section_tag(), "block:table"],
                    )
                )
                continue

            if self._looks_like_space_table_start(lines, index, source_format=source_format):
                flush_paragraph()
                table_index += 1
                table_lines, consumed = self._collect_space_table(lines, index)
                blocks.append(
                    ParsedDocumentBlock(
                        span_ref="section:%s:table:%04d" % (current_section, table_index),
                        content_type=ContentType.TABLE,
                        content="\n".join(table_lines).strip(),
                        confidence=0.82,
                        tags=[section_tag(), "block:table", "block:table_grid", "table_style:layout"],
                    )
                )
                index += consumed
                continue

            if self._looks_like_code_style_start(lines, index, source_format=source_format):
                flush_paragraph()
                code_index += 1
                code_lines, consumed = self._collect_code_style_block(lines, index)
                code_style = "indented" if lines[index].startswith(" ") or lines[index].startswith("\t") else "plain"
                blocks.append(
                    ParsedDocumentBlock(
                        span_ref="section:%s:code:%04d" % (current_section, code_index),
                        content_type=ContentType.TEXT,
                        content="\n".join(code_lines).strip(),
                        confidence=0.81,
                        tags=[section_tag(), "block:code", "code_style:%s" % code_style],
                    )
                )
                index += consumed
                continue

            figure_match = _FIGURE_MARKDOWN_RE.match(stripped)
            if figure_match or _FIGURE_CAPTION_RE.match(stripped):
                flush_paragraph()
                figure_index += 1
                tags = [section_tag(), "block:figure"]
                if figure_match:
                    src = figure_match.group("src").strip()
                    if src:
                        tags.append("figure_src:%s" % src)
                blocks.append(
                    ParsedDocumentBlock(
                        span_ref="section:%s:figure:%04d" % (current_section, figure_index),
                        content_type=ContentType.TEXT,
                        content=stripped,
                        confidence=0.8,
                        tags=tags,
                    )
                )
                index += 1
                continue

            paragraph_buffer.append(line)
            index += 1

        flush_paragraph()
        return blocks

    def _is_code_fence_start(self, stripped_line: str) -> bool:
        return stripped_line.startswith("```") or stripped_line.startswith("~~~")

    def _parse_toc_line(self, stripped_line: str, *, source_format: str) -> Optional[tuple[str, int, str]]:
        marker_match = _TOC_MARKER_RE.match(stripped_line)
        if marker_match is not None:
            title = marker_match.group("title").strip()
            level = int(marker_match.group("level") or "1")
            return title, max(level, 1), "unknown"

        # TOC heuristics are mostly useful for docx/pdf-derived text.
        if source_format not in {".docx", ".pdf", ".doc"} and ".." not in stripped_line:
            return None
        match = _TOC_LINE_RE.match(stripped_line)
        if match is None:
            return None
        title = match.group("title").strip()
        if not title:
            return None
        idx = (match.group("idx") or "").strip()
        if idx:
            level = idx.count(".") + 1
            title = "%s %s" % (idx, title)
        else:
            level = 1
        return title, level, match.group("page").strip()

    def _looks_like_ascii_grid_start(self, lines: list[str], index: int) -> bool:
        if index >= len(lines):
            return False
        line = lines[index].strip()
        if not _ASCII_GRID_BORDER_RE.match(line):
            return False
        if index + 1 >= len(lines):
            return False
        next_line = lines[index + 1].strip()
        return "|" in next_line or _ASCII_GRID_BORDER_RE.match(next_line) is not None

    def _collect_ascii_grid(self, lines: list[str], start: int) -> tuple[list[str], int]:
        collected: list[str] = []
        index = start
        while index < len(lines):
            stripped = lines[index].strip()
            if not stripped:
                break
            if "|" not in stripped and _ASCII_GRID_BORDER_RE.match(stripped) is None:
                break
            collected.append(lines[index].rstrip())
            index += 1
        consumed = max(1, index - start)
        return collected, consumed

    def _looks_like_table_header(self, lines: list[str], index: int) -> bool:
        if index + 1 >= len(lines):
            return False
        header = lines[index].strip()
        separator = lines[index + 1].strip()
        if "|" not in header:
            return False
        if "|" not in separator:
            return False
        cleaned = separator.replace("|", "").replace(":", "").replace("-", "").replace(" ", "")
        if cleaned:
            return False
        return "-" in separator

    def _looks_like_space_table_start(self, lines: list[str], index: int, *, source_format: str) -> bool:
        if source_format not in {".docx", ".pdf", ".doc"}:
            return False
        if index + 1 >= len(lines):
            return False
        first_cols = self._split_layout_columns(lines[index])
        second_cols = self._split_layout_columns(lines[index + 1])
        if len(first_cols) < 2 or len(second_cols) < 2:
            return False
        if abs(len(first_cols) - len(second_cols)) > 1:
            return False
        # Guard against prose lines accidentally containing double-spaces.
        return len(lines[index].strip()) >= 8 and len(lines[index + 1].strip()) >= 8

    def _collect_space_table(self, lines: list[str], start: int) -> tuple[list[str], int]:
        collected: list[str] = []
        index = start
        while index < len(lines):
            raw = lines[index].rstrip()
            if not raw.strip():
                break
            cols = self._split_layout_columns(raw)
            if len(cols) < 2:
                break
            collected.append(raw)
            index += 1
        consumed = max(1, index - start)
        return collected, consumed

    def _split_layout_columns(self, line: str) -> list[str]:
        return [item.strip() for item in re.split(r"\s{2,}", line.strip()) if item.strip()]

    def _looks_like_code_style_start(self, lines: list[str], index: int, *, source_format: str) -> bool:
        if index >= len(lines):
            return False
        stripped = lines[index].rstrip()
        if not stripped.strip():
            return False
        if stripped.startswith("    ") or stripped.startswith("\t"):
            return True
        if source_format in {".docx", ".pdf", ".doc"} and _CODE_STYLE_RE.match(stripped.strip()):
            if index + 1 < len(lines):
                next_line = lines[index + 1].rstrip()
                if next_line.startswith("    ") or next_line.startswith("\t") or _CODE_STYLE_RE.match(next_line.strip()):
                    return True
        return False

    def _collect_code_style_block(self, lines: list[str], start: int) -> tuple[list[str], int]:
        collected: list[str] = []
        index = start
        while index < len(lines):
            raw = lines[index].rstrip("\n")
            if not raw.strip():
                break
            stripped = raw.strip()
            if not (
                raw.startswith("    ")
                or raw.startswith("\t")
                or _CODE_STYLE_RE.match(stripped)
                or stripped in {"{", "}", ");", "];"}
            ):
                break
            collected.append(raw)
            index += 1
        consumed = max(1, index - start)
        return collected, consumed
