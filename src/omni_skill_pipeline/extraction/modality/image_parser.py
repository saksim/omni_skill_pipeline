from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable

from omni_skill_pipeline.models import ContentType
from omni_skill_pipeline.providers.base import FrameAnalysis, OCRBlock, OCRResult
from omni_skill_pipeline.utils import unique_preserve_order


_METRIC_HINT_RE = re.compile(r"(\b\d+(?:\.\d+)?\s*(?:ms|s|sec|%|qps|rps|mb|gb)\b|\bp\d{2}\b)", re.IGNORECASE)


@dataclass(slots=True)
class ParsedImageEvidenceBlock:
    span_ref: str
    content_type: ContentType
    content: str
    confidence: float
    tags: list[str] = field(default_factory=list)


@dataclass(slots=True)
class _LineUnit:
    text: str
    confidence: float
    role: str


class ImageStructureParser(object):
    def parse_ocr_regions(self, ocr_result: OCRResult) -> list[ParsedImageEvidenceBlock]:
        lines = self._to_line_units(ocr_result)
        if not lines:
            return []
        grouped = self._group_by_role(lines)
        blocks: list[ParsedImageEvidenceBlock] = []
        for index, group in enumerate(grouped, start=1):
            confidence = sum(item.confidence for item in group) / max(len(group), 1)
            role = group[0].role
            blocks.append(
                ParsedImageEvidenceBlock(
                    span_ref="image:region:%04d" % index,
                    content_type=ContentType.OCR,
                    content="\n".join(item.text for item in group),
                    confidence=round(confidence, 3),
                    tags=unique_preserve_order(
                        [
                            "block:region",
                            "source:ocr_group",
                            "layout_role:%s" % role,
                            "region_size:%s" % len(group),
                        ]
                    ),
                )
            )
        return blocks

    def parse_layout_summary(self, analysis: FrameAnalysis) -> list[ParsedImageEvidenceBlock]:
        summary = analysis.summary.strip()
        if not summary:
            return []
        role_tags = self._extract_layout_roles(summary, analysis.tags)
        return [
            ParsedImageEvidenceBlock(
                span_ref="image:layout:0001",
                content_type=ContentType.SCENE,
                content=summary,
                confidence=0.74,
                tags=unique_preserve_order(["block:layout", "source:scene_summary"] + role_tags + list(analysis.tags)),
            )
        ]

    def _to_line_units(self, ocr_result: OCRResult) -> list[_LineUnit]:
        units: list[_LineUnit] = []
        for block in ocr_result.blocks:
            text = block.text.strip()
            if not text:
                continue
            units.append(
                _LineUnit(
                    text=text,
                    confidence=block.confidence if block.confidence > 0 else 0.72,
                    role=self._classify_layout_role(text),
                )
            )
        if units:
            return units
        for line in ocr_result.text.splitlines():
            text = line.strip()
            if not text:
                continue
            units.append(_LineUnit(text=text, confidence=0.72, role=self._classify_layout_role(text)))
        return units

    def _group_by_role(self, lines: list[_LineUnit]) -> list[list[_LineUnit]]:
        grouped: list[list[_LineUnit]] = []
        for line in lines:
            if not grouped:
                grouped.append([line])
                continue
            prev_group = grouped[-1]
            if prev_group[-1].role == line.role and len(prev_group) < 3:
                prev_group.append(line)
                continue
            grouped.append([line])
        return grouped

    def _classify_layout_role(self, text: str) -> str:
        lowered = text.strip().lower()
        if not lowered:
            return "text"
        if "legend" in lowered:
            return "legend"
        if any(token in lowered for token in ("status", "degraded", "healthy", "critical", "error", "warning")):
            return "status"
        if any(token in lowered for token in ("region", "zone", "location", "dc-", "cluster")):
            return "region"
        if _METRIC_HINT_RE.search(lowered) or any(
            token in lowered for token in ("latency", "throughput", "error rate", "cpu", "memory", "p95", "p99")
        ):
            return "metric"
        if any(token in lowered for token in ("chart", "graph", "trend", "timeline", "histogram")):
            return "chart"
        if any(token in lowered for token in ("button", "click", "submit", "retry", "cancel")):
            return "button"
        if any(token in lowered for token in ("input", "search", "filter", "query")):
            return "input"
        if len(lowered) <= 60 and (lowered.startswith("#") or lowered.endswith(":")):
            return "title"
        return "text"

    def _extract_layout_roles(self, summary: str, tags: Iterable[str]) -> list[str]:
        lowered = summary.lower()
        roles = []
        if any(token in lowered for token in ("dashboard", "screen", "ui")):
            roles.append("layout_role:dashboard")
        if any(token in lowered for token in ("banner", "alert", "degraded", "warning", "error")):
            roles.append("layout_role:status")
        if any(token in lowered for token in ("chart", "graph", "spike", "trend")):
            roles.append("layout_role:chart")
        for tag in tags:
            cleaned = str(tag).strip().lower()
            if cleaned in {"dashboard", "chart", "legend", "table", "latency"}:
                roles.append("layout_hint:%s" % cleaned)
        return unique_preserve_order(roles)
