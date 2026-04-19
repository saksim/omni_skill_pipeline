from __future__ import annotations

from pathlib import Path
from typing import Protocol, Sequence, TypeVar, runtime_checkable

from omni_skill_pipeline.models import (
    DistillGoal,
    EvidenceUnit,
    Insight,
    LoadedAsset,
    Modality,
    SkillDocument,
)
from omni_skill_pipeline.providers.base import (
    FrameAnalysis,
    OCRResult,
    SampledFrame,
    TranscriptionResult,
    VideoMetadata,
)

ReqT = TypeVar('ReqT')


@runtime_checkable
class DistillAdapter(Protocol[ReqT]):
    def load(self, request: ReqT) -> LoadedAsset:
        ...


@runtime_checkable
class InsightExtractor(Protocol):
    def extract(self, evidence_units: Sequence[EvidenceUnit]) -> list[Insight]:
        ...


@runtime_checkable
class SkillComposer(Protocol):
    def compose(
        self,
        title_hint: str,
        goal: DistillGoal,
        modality: Modality,
        evidence_units: Sequence[EvidenceUnit],
        insights: Sequence[Insight],
    ) -> SkillDocument:
        ...


@runtime_checkable
class AudioTranscriber(Protocol):
    def transcribe(
        self,
        audio_path: Path,
        *,
        language: str | None = None,
        prompt: str | None = None,
    ) -> TranscriptionResult:
        ...


@runtime_checkable
class OCRProvider(Protocol):
    def extract(self, image_path: Path) -> OCRResult:
        ...


@runtime_checkable
class ImageAnalyzer(Protocol):
    def analyze(self, image_path: Path, *, prompt: str | None = None) -> FrameAnalysis:
        ...


@runtime_checkable
class MediaProcessor(Protocol):
    def probe(self, video_path: Path) -> VideoMetadata:
        ...

    def extract_audio(self, video_path: Path, work_dir: Path) -> Path:
        ...

    def extract_keyframes(
        self,
        video_path: Path,
        work_dir: Path,
        *,
        interval_seconds: int,
        max_frames: int,
        scene_threshold: float | None = None,
        dedupe_distance: int | None = None,
    ) -> list[SampledFrame]:
        ...
