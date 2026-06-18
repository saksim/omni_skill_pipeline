from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, Sequence, TypeAlias, TypeVar, runtime_checkable

from omni_skill_pipeline.models import (
    AudioDistillRequest,
    CorpusAssetInput,
    CorpusDistillRequest,
    DistillBundle,
    DistillGoal,
    EvidenceNode,
    EvidenceUnit,
    ImageDistillRequest,
    Insight,
    LoadedCorpus,
    LoadedAsset,
    Modality,
    RequestMixin,
    SemanticAtom,
    SkillDocument,
    TabularDistillRequest,
    TextDistillRequest,
    VideoDistillRequest,
)
from omni_skill_pipeline.providers.base import (
    FrameAnalysis,
    OCRResult,
    SampledFrame,
    TranscriptionResult,
    VideoMetadata,
)

ReqT = TypeVar('ReqT')
AssetRequestT = TypeVar('AssetRequestT', bound=RequestMixin)
AssetDistillRequest: TypeAlias = (
    TextDistillRequest
    | AudioDistillRequest
    | ImageDistillRequest
    | TabularDistillRequest
    | VideoDistillRequest
)


@runtime_checkable
class DistillAdapter(Protocol[ReqT]):
    def load(self, request: ReqT) -> LoadedAsset:
        ...


@runtime_checkable
class ArtifactRepository(Protocol):
    def save_bundle(self, bundle: DistillBundle) -> dict[str, str]:
        ...


@runtime_checkable
class ReviewQueueRepository(Protocol):
    def list_review_queue(
        self,
        *,
        queue_status: str | None = 'pending',
        limit: int = 100,
        tenant_scope: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        ...

    def claim_review_task(
        self,
        review_task_id: str | None = None,
        *,
        consumer: str = 'review-consumer',
        tenant_scope: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        ...

    def close_review_task(
        self,
        review_task_id: str,
        *,
        status: str = 'published',
        closed_by: str = 'review-operator',
        review_notes: str = '',
        decision: str | None = None,
        reason_codes: Sequence[str] | None = None,
        reviewer_edits: dict[str, Any] | None = None,
        tenant_scope: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        ...

    def consume_review_task(
        self,
        *,
        consumer: str = 'review-consumer',
        tenant_scope: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        ...


@runtime_checkable
class InsightExtractor(Protocol):
    def extract(self, evidence_units: Sequence[EvidenceUnit]) -> list[Insight]:
        ...


@runtime_checkable
class AtomExtractor(Protocol):
    def extract(self, evidence_nodes: Sequence[EvidenceNode]) -> list[SemanticAtom]:
        ...


@runtime_checkable
class CorpusAssetRequestBuilder(Protocol):
    def build(self, asset: CorpusAssetInput, goal: DistillGoal) -> AssetDistillRequest:
        ...


@runtime_checkable
class CorpusLoader(Protocol):
    def load_corpus(self, request: CorpusDistillRequest) -> LoadedCorpus:
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
