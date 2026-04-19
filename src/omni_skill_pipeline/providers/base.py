from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass(slots=True)
class TranscriptSegment:
    text: str
    start: Optional[float] = None
    end: Optional[float] = None
    speaker: Optional[str] = None
    confidence: float = 0.0


@dataclass(slots=True)
class TranscriptionResult:
    text: str
    segments: List[TranscriptSegment]
    language: Optional[str] = None
    model_name: Optional[str] = None
    metadata: Dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class OCRBlock:
    text: str
    confidence: float = 0.0


@dataclass(slots=True)
class OCRResult:
    text: str
    blocks: List[OCRBlock]
    engine: str
    metadata: Dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class FrameAnalysis:
    image_path: Path
    summary: str
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class VideoMetadata:
    duration_seconds: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    frame_count: Optional[int] = None


@dataclass(slots=True)
class SampledFrame:
    path: Path
    source: str
    timestamp_seconds: Optional[float] = None
    scene_score: Optional[float] = None
    dedupe_hash: Optional[int] = None
