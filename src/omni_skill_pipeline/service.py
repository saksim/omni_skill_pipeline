from __future__ import annotations

from pathlib import Path
from typing import Optional

from omni_skill_pipeline.adapters.audio import AudioAdapter
from omni_skill_pipeline.adapters.image import ImageAdapter
from omni_skill_pipeline.adapters.tabular import TabularAdapter
from omni_skill_pipeline.adapters.text import TextAdapter
from omni_skill_pipeline.adapters.video import VideoAdapter
from omni_skill_pipeline.config import Settings, load_settings
from omni_skill_pipeline.exceptions import ProviderUnavailableError
from omni_skill_pipeline.interfaces import DistillAdapter, InsightExtractor, SkillComposer
from omni_skill_pipeline.models import (
    AudioDistillRequest,
    DistillBundle,
    ImageDistillRequest,
    TabularDistillRequest,
    TextDistillRequest,
    VideoDistillRequest,
)
from omni_skill_pipeline.pipeline import HeuristicInsightExtractor, HeuristicSkillComposer
from omni_skill_pipeline.providers.fallback import (
    FallbackAudioTranscriber,
    FallbackImageAnalyzer,
    FallbackOCRProvider,
    FallbackSkillComposer,
)
from omni_skill_pipeline.providers.media import FFmpegMediaProcessor
from omni_skill_pipeline.providers.openai_provider import OpenAIAudioTranscriber, OpenAILLMSkillComposer, OpenAIVisionAnalyzer
from omni_skill_pipeline.providers.tesseract import TesseractOCRProvider
from omni_skill_pipeline.render import render_skill_markdown
from omni_skill_pipeline.repository import FileArtifactRepository


class DistillationService(object):
    def __init__(
        self,
        repository: FileArtifactRepository,
        *,
        text_adapter: DistillAdapter[TextDistillRequest],
        audio_adapter: DistillAdapter[AudioDistillRequest],
        image_adapter: DistillAdapter[ImageDistillRequest],
        tabular_adapter: DistillAdapter[TabularDistillRequest],
        video_adapter: DistillAdapter[VideoDistillRequest],
        insight_extractor: InsightExtractor,
        skill_composer: SkillComposer,
    ) -> None:
        self.repository = repository
        self.text_adapter = text_adapter
        self.audio_adapter = audio_adapter
        self.image_adapter = image_adapter
        self.tabular_adapter = tabular_adapter
        self.video_adapter = video_adapter
        self.insight_extractor = insight_extractor
        self.skill_composer = skill_composer

    def distill_text(self, request: TextDistillRequest) -> DistillBundle:
        return self._distill(request, self.text_adapter)

    def distill_audio(self, request: AudioDistillRequest) -> DistillBundle:
        return self._distill(request, self.audio_adapter)

    def distill_image(self, request: ImageDistillRequest) -> DistillBundle:
        return self._distill(request, self.image_adapter)

    def distill_tabular(self, request: TabularDistillRequest) -> DistillBundle:
        return self._distill(request, self.tabular_adapter)

    def distill_video(self, request: VideoDistillRequest) -> DistillBundle:
        return self._distill(request, self.video_adapter)

    def _distill(self, request, adapter) -> DistillBundle:
        request.validate()
        loaded = adapter.load(request)
        insights = self.insight_extractor.extract(loaded.evidence_units)
        skill = self.skill_composer.compose(
            loaded.title_hint,
            request.goal,
            loaded.asset.modality,
            loaded.evidence_units,
            insights,
        )
        markdown = render_skill_markdown(skill)
        bundle = DistillBundle(
            asset=loaded.asset,
            evidence_units=loaded.evidence_units,
            insights=insights,
            skill=skill,
            skill_markdown=markdown,
            request_payload=request.to_dict(),
            adapter_metadata=loaded.adapter_metadata,
        )
        self.repository.save_bundle(bundle)
        return bundle


def _build_skill_composer(settings: Settings) -> SkillComposer:
    composers = []
    if settings.prefer_llm_composer:
        try:
            composers.append(OpenAILLMSkillComposer(settings))
        except ProviderUnavailableError:
            pass
    composers.append(HeuristicSkillComposer())
    return FallbackSkillComposer(composers)


def _build_audio_adapter(settings: Settings) -> AudioAdapter:
    transcribers = []
    try:
        transcribers.append(OpenAIAudioTranscriber(settings))
    except ProviderUnavailableError:
        pass
    transcriber = FallbackAudioTranscriber(transcribers) if transcribers else None
    return AudioAdapter(transcriber=transcriber)


def _build_image_capabilities(settings: Settings):
    ocr_providers = [TesseractOCRProvider(binary=settings.tesseract_bin, languages=settings.tesseract_languages)]
    analyzers = []
    try:
        vision = OpenAIVisionAnalyzer(settings)
    except ProviderUnavailableError:
        vision = None
    if vision is not None:
        ocr_providers.append(vision)
        analyzers.append(vision)
    ocr_provider = FallbackOCRProvider(ocr_providers) if ocr_providers else None
    analyzer = FallbackImageAnalyzer(analyzers) if analyzers else None
    return ocr_provider, analyzer


def build_service(repo_root: Optional[str] = None) -> DistillationService:
    settings = load_settings(Path(repo_root) if repo_root else None)
    repository = FileArtifactRepository(settings.draft_dir)
    audio_adapter = _build_audio_adapter(settings)
    ocr_provider, analyzer = _build_image_capabilities(settings)
    video_adapter = VideoAdapter(
        media_processor=FFmpegMediaProcessor(
            binary=settings.ffmpeg_bin,
            probe_binary=settings.ffprobe_bin,
            scene_threshold=settings.video_scene_threshold,
            dedupe_distance=settings.video_frame_dedupe_distance,
        ),
        audio_adapter=audio_adapter,
        ocr_provider=ocr_provider,
        analyzer=analyzer,
        default_interval_seconds=settings.keyframe_interval_seconds,
        default_max_keyframes=settings.max_keyframes,
        default_scene_threshold=settings.video_scene_threshold,
        default_dedupe_distance=settings.video_frame_dedupe_distance,
        scratch_root=settings.repo_root / '.tmp_omni_media',
    )
    return DistillationService(
        repository=repository,
        text_adapter=TextAdapter(),
        audio_adapter=audio_adapter,
        image_adapter=ImageAdapter(ocr_provider=ocr_provider, analyzer=analyzer),
        tabular_adapter=TabularAdapter(),
        video_adapter=video_adapter,
        insight_extractor=HeuristicInsightExtractor(),
        skill_composer=_build_skill_composer(settings),
    )
