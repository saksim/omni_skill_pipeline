from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from omni_skill_pipeline.adapters.audio import AudioAdapter
from omni_skill_pipeline.adapters.image import ImageAdapter
from omni_skill_pipeline.adapters.tabular import TabularAdapter
from omni_skill_pipeline.adapters.text import TextAdapter
from omni_skill_pipeline.adapters.video import VideoAdapter
from omni_skill_pipeline.config import Settings, load_settings
from omni_skill_pipeline.exceptions import ProviderUnavailableError
from omni_skill_pipeline.interfaces import SkillComposer
from omni_skill_pipeline.logging_utils import get_request_context
from omni_skill_pipeline.pipeline import HeuristicInsightExtractor, HeuristicSkillComposer
from omni_skill_pipeline.providers.fallback import (
    FallbackAudioTranscriber,
    FallbackImageAnalyzer,
    FallbackOCRProvider,
    FallbackSkillComposer,
)
from omni_skill_pipeline.providers.media import FFmpegMediaProcessor
from omni_skill_pipeline.providers.openai_provider import OpenAIAudioTranscriber, OpenAILLMSkillComposer, OpenAIVisionAnalyzer
from omni_skill_pipeline.publication import PortableSkillRenderer
from omni_skill_pipeline.providers.tesseract import TesseractOCRProvider
from omni_skill_pipeline.quality.review_policy import ReviewPolicy
from omni_skill_pipeline.repository import FileArtifactRepository
from omni_skill_pipeline.service import DistillationService

logger = logging.getLogger(__name__)


def _request_context_extra() -> dict[str, str]:
    request_id, trace_id = get_request_context()
    return {
        'request_id': request_id,
        'trace_id': trace_id,
    }


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
    insight_extractor = HeuristicInsightExtractor()
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
    service = DistillationService(
        repository=repository,
        text_adapter=TextAdapter(),
        audio_adapter=audio_adapter,
        image_adapter=ImageAdapter(ocr_provider=ocr_provider, analyzer=analyzer),
        tabular_adapter=TabularAdapter(),
        video_adapter=video_adapter,
        insight_extractor=insight_extractor,
        skill_composer=_build_skill_composer(settings),
        publication_orchestrator=_build_publication_orchestrator(
            insight_extractor=insight_extractor,
            portable_skill_line_limit=settings.portable_skill_markdown_line_limit,
        ),
        review_policy=ReviewPolicy(
            force_review_mode=bool(getattr(settings, 'controlled_trial_review_mode', False)),
            force_review_reason_code=str(
                getattr(settings, 'controlled_trial_review_reason_code', 'controlled_trial_requires_review')
            ),
        ),
    )
    logger.info(
        'Distillation service initialized.',
        extra={
            **_request_context_extra(),
            'event': 'service_bootstrap_complete',
            'draft_dir': str(settings.draft_dir),
            'template_path': str(settings.template_path),
        },
    )
    return service


def _build_publication_orchestrator(*, insight_extractor, portable_skill_line_limit: int):
    from omni_skill_pipeline.assembly.publication_builder import PublicationBuilder
    from omni_skill_pipeline.assembly.skill_graph_builder import SkillGraphBuilder
    from omni_skill_pipeline.extraction import LegacyInsightAtomExtractor
    from omni_skill_pipeline.publication_orchestrator import PublicationHarmonizer, PublicationOrchestrator

    atom_extractor = LegacyInsightAtomExtractor(insight_extractor=insight_extractor)
    publication_builder = PublicationBuilder(
        portable_skill_line_limit=portable_skill_line_limit,
        portable_skill_renderer=PortableSkillRenderer(line_limit=portable_skill_line_limit),
    )
    harmonizer = PublicationHarmonizer(portable_skill_line_limit=portable_skill_line_limit)
    return PublicationOrchestrator(
        atom_extractor=atom_extractor,
        skill_graph_builder=SkillGraphBuilder(),
        publication_builder=publication_builder,
        harmonizer=harmonizer,
    )
