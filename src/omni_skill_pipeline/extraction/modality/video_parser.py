from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Sequence

from omni_skill_pipeline.models import ContentType, EvidenceUnit
from omni_skill_pipeline.providers.base import SampledFrame
from omni_skill_pipeline.utils import unique_preserve_order

_FRAME_TS_RE = re.compile(r"@(?P<ts>\d+(?:\.\d+)?)s$")
_KEYWORD_GROUPS = [
    ("incident_signal", ("degraded", "error", "fail", "outage", "rollback", "alert", "incident")),
    ("ui_action", ("click", "submit", "open", "dialog", "button", "toggle", "input", "menu")),
    ("metric_shift", ("latency", "cpu", "memory", "p95", "p99", "throughput", "error rate", "qps", "rps")),
    ("release_change", ("release", "deploy", "version", "upgrade", "hotfix", "patch")),
]


@dataclass(slots=True)
class ParsedVideoEvidenceBlock:
    span_ref: str
    content_type: ContentType
    content: str
    confidence: float
    tags: list[str] = field(default_factory=list)


@dataclass(slots=True)
class VideoParseResult:
    evidence_blocks: list[ParsedVideoEvidenceBlock] = field(default_factory=list)
    scene_clusters: list[dict[str, object]] = field(default_factory=list)
    frame_event_count: int = 0
    subtitle_alignment_count: int = 0


@dataclass(slots=True)
class _FrameAnchor:
    span_ref: str
    timestamp_seconds: float | None
    source: str
    scene_score: float | None
    order: int


@dataclass(slots=True)
class _FrameContext:
    ocr_lines: list[str] = field(default_factory=list)
    scene_lines: list[str] = field(default_factory=list)


class VideoStructureParser(object):
    def __init__(
        self,
        *,
        scene_gap_seconds: float = 8.0,
        hard_gap_seconds: float = 14.0,
        scene_break_score: float = 0.45,
        max_subtitle_alignments: int = 24,
    ) -> None:
        self.scene_gap_seconds = scene_gap_seconds
        self.hard_gap_seconds = hard_gap_seconds
        self.scene_break_score = scene_break_score
        self.max_subtitle_alignments = max_subtitle_alignments

    def parse(self, *, frames: Sequence[SampledFrame], evidence_units: Sequence[EvidenceUnit]) -> VideoParseResult:
        anchors = self._build_anchors(frames, evidence_units)
        if not anchors:
            return VideoParseResult()

        context_map = self._collect_frame_context(evidence_units)
        scene_blocks, cluster_metadata = self._build_scene_clusters(anchors)
        event_blocks = self._build_frame_events(anchors, context_map)
        subtitle_blocks = self._build_subtitle_alignment(anchors, evidence_units)

        return VideoParseResult(
            evidence_blocks=scene_blocks + event_blocks + subtitle_blocks,
            scene_clusters=cluster_metadata,
            frame_event_count=len(event_blocks),
            subtitle_alignment_count=len(subtitle_blocks),
        )

    def _build_anchors(self, frames: Sequence[SampledFrame], evidence_units: Sequence[EvidenceUnit]) -> list[_FrameAnchor]:
        anchors: list[_FrameAnchor] = []
        for index, frame in enumerate(frames, start=1):
            anchors.append(
                _FrameAnchor(
                    span_ref=self._build_frame_span(index, frame),
                    timestamp_seconds=frame.timestamp_seconds,
                    source=frame.source,
                    scene_score=frame.scene_score,
                    order=index,
                )
            )

        existing = {item.span_ref for item in anchors}
        for unit in evidence_units:
            base = self._frame_base_span(unit.span_ref)
            if not base or base in existing:
                continue
            anchors.append(
                _FrameAnchor(
                    span_ref=base,
                    timestamp_seconds=self._parse_frame_timestamp(base),
                    source="evidence",
                    scene_score=None,
                    order=len(anchors) + 1,
                )
            )
            existing.add(base)

        return sorted(anchors, key=self._anchor_sort_key)

    def _collect_frame_context(self, evidence_units: Sequence[EvidenceUnit]) -> dict[str, _FrameContext]:
        context_map: dict[str, _FrameContext] = {}
        for unit in evidence_units:
            base = self._frame_base_span(unit.span_ref)
            if not base:
                continue
            ctx = context_map.setdefault(base, _FrameContext())
            text = unit.content.strip()
            if not text:
                continue
            if unit.span_ref.endswith(":ocr") or unit.content_type == ContentType.OCR:
                ctx.ocr_lines.append(text)
            elif unit.span_ref.endswith(":scene") or unit.content_type == ContentType.SCENE:
                ctx.scene_lines.append(text)
        return context_map

    def _build_scene_clusters(
        self,
        anchors: Sequence[_FrameAnchor],
    ) -> tuple[list[ParsedVideoEvidenceBlock], list[dict[str, object]]]:
        if not anchors:
            return [], []

        clusters: list[list[_FrameAnchor]] = []
        current: list[_FrameAnchor] = [anchors[0]]
        for anchor in anchors[1:]:
            if self._should_split_cluster(current[-1], anchor):
                clusters.append(current)
                current = [anchor]
            else:
                current.append(anchor)
        clusters.append(current)

        blocks: list[ParsedVideoEvidenceBlock] = []
        metadata: list[dict[str, object]] = []
        for index, cluster in enumerate(clusters, start=1):
            start_ts = cluster[0].timestamp_seconds
            end_ts = cluster[-1].timestamp_seconds
            span_ref = "video:scene_cluster:%04d" % index
            if start_ts is not None and end_ts is not None:
                span_ref = "%s@%.2fs-%.2fs" % (span_ref, start_ts, end_ts)

            sources = unique_preserve_order(item.source for item in cluster)
            frame_spans = [item.span_ref for item in cluster]
            max_scene_score = max((item.scene_score for item in cluster if item.scene_score is not None), default=None)
            cluster_text = self._describe_cluster(index, len(cluster), start_ts, end_ts, sources)
            tags = unique_preserve_order(
                [
                    "block:scene_cluster",
                    "timeline:scene",
                    "cluster_size:%s" % len(cluster),
                    "source_mix:%s" % ",".join(sources),
                ]
            )
            if max_scene_score is not None:
                tags = unique_preserve_order(tags + ["cluster_scene_score:%.3f" % max_scene_score])

            blocks.append(
                ParsedVideoEvidenceBlock(
                    span_ref=span_ref,
                    content_type=ContentType.SCENE,
                    content=cluster_text,
                    confidence=0.77 if "scene" in sources else 0.71,
                    tags=tags,
                )
            )
            metadata.append(
                {
                    "cluster_id": index,
                    "span_ref": span_ref,
                    "start_seconds": start_ts,
                    "end_seconds": end_ts,
                    "frame_count": len(cluster),
                    "sources": sources,
                    "frame_spans": frame_spans,
                    "max_scene_score": max_scene_score,
                }
            )
        return blocks, metadata

    def _build_frame_events(
        self,
        anchors: Sequence[_FrameAnchor],
        context_map: dict[str, _FrameContext],
    ) -> list[ParsedVideoEvidenceBlock]:
        blocks: list[ParsedVideoEvidenceBlock] = []
        for anchor in anchors:
            context = context_map.get(anchor.span_ref)
            if context is None:
                continue
            scene_text = " ".join(unique_preserve_order(context.scene_lines)).strip()
            ocr_text = " ".join(unique_preserve_order(context.ocr_lines)).strip()
            if not scene_text and not ocr_text:
                continue

            event_type = self._classify_event_type(scene_text, ocr_text)
            fragments = []
            if scene_text:
                fragments.append(scene_text)
            if ocr_text:
                fragments.append("OCR: %s" % ocr_text)
            content = " | ".join(fragments).strip()
            if len(content) > 320:
                content = "%s..." % content[:317]

            tags = unique_preserve_order(
                [
                    "block:frame_event",
                    "event_type:%s" % event_type,
                    "timeline:frame_event",
                    "frame_anchor:%s" % anchor.span_ref,
                    "frame_source:%s" % anchor.source,
                ]
            )
            if anchor.scene_score is not None:
                tags = unique_preserve_order(tags + ["scene_score:%.3f" % anchor.scene_score])

            confidence = 0.66
            if scene_text:
                confidence += 0.06
            if ocr_text:
                confidence += 0.05
            if anchor.source == "scene":
                confidence += 0.04

            blocks.append(
                ParsedVideoEvidenceBlock(
                    span_ref="%s:event" % anchor.span_ref,
                    content_type=ContentType.EVENT,
                    content=content,
                    confidence=round(min(confidence, 0.9), 3),
                    tags=tags,
                )
            )
        return blocks

    def _build_subtitle_alignment(
        self,
        anchors: Sequence[_FrameAnchor],
        evidence_units: Sequence[EvidenceUnit],
    ) -> list[ParsedVideoEvidenceBlock]:
        if not anchors:
            return []
        blocks: list[ParsedVideoEvidenceBlock] = []
        speech_units = [
            unit
            for unit in evidence_units
            if unit.content_type == ContentType.SPEECH and unit.span_ref.startswith("video:")
        ]
        for index, unit in enumerate(speech_units, start=1):
            if len(blocks) >= self.max_subtitle_alignments:
                break
            anchor, mode = self._align_unit_to_frame(unit, anchors, index=index)
            if anchor is None:
                continue
            summary = " ".join(unit.content.split()).strip()
            if not summary:
                continue
            if len(summary) > 220:
                summary = "%s..." % summary[:217]
            semantic_tags = [tag for tag in unit.tags if tag.startswith("utterance_act:") or tag.startswith("speaker_role:")]
            tags = unique_preserve_order(
                [
                    "block:subtitle_alignment",
                    "timeline:subtitle",
                    "aligned_frame:%s" % anchor.span_ref,
                    "alignment_mode:%s" % mode,
                    "source_span:%s" % unit.span_ref,
                ]
                + semantic_tags
            )
            blocks.append(
                ParsedVideoEvidenceBlock(
                    span_ref="%s:subtitle:%04d" % (anchor.span_ref, index),
                    content_type=ContentType.SPEECH,
                    content=summary,
                    confidence=round(min(0.9, max(0.58, unit.confidence)), 3),
                    tags=tags,
                )
            )
        return blocks

    def _align_unit_to_frame(
        self,
        unit: EvidenceUnit,
        anchors: Sequence[_FrameAnchor],
        *,
        index: int,
    ) -> tuple[_FrameAnchor | None, str]:
        start, end = self._parse_video_time_range(unit.span_ref)
        if start is None and end is None:
            return anchors[min(index - 1, len(anchors) - 1)], "sequential"

        midpoint = start if end is None else ((start + end) / 2.0 if start is not None else None)
        if midpoint is None:
            midpoint = end
        if midpoint is None:
            return anchors[min(index - 1, len(anchors) - 1)], "sequential"

        with_ts = [anchor for anchor in anchors if anchor.timestamp_seconds is not None]
        if not with_ts:
            return anchors[min(index - 1, len(anchors) - 1)], "sequential"

        if start is not None and end is not None:
            in_window = [anchor for anchor in with_ts if start - 0.15 <= anchor.timestamp_seconds <= end + 0.15]
            if in_window:
                return min(in_window, key=lambda item: abs(item.timestamp_seconds - midpoint)), "time_window"

        return min(with_ts, key=lambda item: abs(item.timestamp_seconds - midpoint)), "nearest_time"

    def _parse_video_time_range(self, span_ref: str) -> tuple[float | None, float | None]:
        prefix = "video:timestamp:"
        if not span_ref.startswith(prefix):
            return None, None
        payload = span_ref[len(prefix) :]
        if "-" in payload:
            left, right = payload.split("-", 1)
            return self._to_float(left), self._to_float(right)
        value = self._to_float(payload)
        return value, value

    def _build_frame_span(self, index: int, frame: SampledFrame) -> str:
        if frame.timestamp_seconds is None:
            return "frame:%04d" % index
        return "frame:%04d@%.2fs" % (index, frame.timestamp_seconds)

    def _frame_base_span(self, span_ref: str) -> str | None:
        if not span_ref.startswith("frame:"):
            return None
        parts = span_ref.split(":")
        if len(parts) < 2:
            return None
        if len(parts) == 2:
            return span_ref
        if parts[2] in {"ocr", "scene", "event", "subtitle", "speech"}:
            return ":".join(parts[:2])
        return None

    def _parse_frame_timestamp(self, frame_span: str) -> float | None:
        match = _FRAME_TS_RE.search(frame_span)
        if match is None:
            return None
        return self._to_float(match.group("ts"))

    def _anchor_sort_key(self, anchor: _FrameAnchor) -> tuple[float, int]:
        timestamp = anchor.timestamp_seconds if anchor.timestamp_seconds is not None else float("inf")
        return timestamp, anchor.order

    def _should_split_cluster(self, previous: _FrameAnchor, current: _FrameAnchor) -> bool:
        if previous.timestamp_seconds is None or current.timestamp_seconds is None:
            return current.source == "scene" and previous.source != "scene"

        gap = current.timestamp_seconds - previous.timestamp_seconds
        if gap >= self.hard_gap_seconds:
            return True
        if gap >= self.scene_gap_seconds:
            return True
        if current.source == "scene" and previous.source != "scene" and gap >= 1.0:
            return True
        return current.scene_score is not None and current.scene_score >= self.scene_break_score and gap >= 1.0

    def _describe_cluster(
        self,
        cluster_id: int,
        frame_count: int,
        start_ts: float | None,
        end_ts: float | None,
        sources: Sequence[str],
    ) -> str:
        if start_ts is not None and end_ts is not None:
            return "Scene cluster %s covers %s keyframes from %.2fs to %.2fs. Sources: %s." % (
                cluster_id,
                frame_count,
                start_ts,
                end_ts,
                ", ".join(sources),
            )
        return "Scene cluster %s covers %s keyframes. Sources: %s." % (cluster_id, frame_count, ", ".join(sources))

    def _classify_event_type(self, scene_text: str, ocr_text: str) -> str:
        merged = ("%s %s" % (scene_text, ocr_text)).lower()
        for event_type, keywords in _KEYWORD_GROUPS:
            if any(token in merged for token in keywords):
                return event_type
        return "visual_update"

    def _to_float(self, value: object) -> float | None:
        if value in (None, ""):
            return None
        text = str(value).strip().lower()
        if not text:
            return None
        if text.endswith("s"):
            text = text[:-1].strip()
        try:
            return float(text)
        except ValueError:
            return None
