from __future__ import annotations

from pathlib import Path
from typing import Optional
from urllib.parse import unquote, urlparse

from omni_skill_pipeline.adapters.audio import AudioAdapter
from omni_skill_pipeline.adapters.image import ImageAdapter
from omni_skill_pipeline.adapters.tabular import TabularAdapter
from omni_skill_pipeline.adapters.text import TextAdapter
from omni_skill_pipeline.adapters.video import VideoAdapter
from omni_skill_pipeline.config import Settings, load_settings
from omni_skill_pipeline.extraction import EvidenceBuilder
from omni_skill_pipeline.exceptions import ProviderUnavailableError
from omni_skill_pipeline.interfaces import AssetDistillRequest, DistillAdapter, InsightExtractor, SkillComposer
from omni_skill_pipeline.models import (
    AudioDistillRequest,
    Corpus,
    CorpusAssetInput,
    CorpusAssetRef,
    CorpusDistillRequest,
    DistillBundle,
    DistillGoal,
    ImageDistillRequest,
    LoadedCorpus,
    LoadedAsset,
    Modality,
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
from omni_skill_pipeline.utils import unique_preserve_order


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
        evidence_builder: EvidenceBuilder | None = None,
    ) -> None:
        self.repository = repository
        self.text_adapter = text_adapter
        self.audio_adapter = audio_adapter
        self.image_adapter = image_adapter
        self.tabular_adapter = tabular_adapter
        self.video_adapter = video_adapter
        self.insight_extractor = insight_extractor
        self.skill_composer = skill_composer
        self.evidence_builder = evidence_builder or EvidenceBuilder()

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

    def distill_corpus(self, request: CorpusDistillRequest) -> DistillBundle:
        loaded_corpus = self.load_corpus(request)
        insights = self.insight_extractor.extract(loaded_corpus.evidence_units)
        primary_index = min(request.primary_asset_index(), max(len(loaded_corpus.loaded_assets) - 1, 0))
        primary_loaded = loaded_corpus.loaded_assets[primary_index]
        skill = self.skill_composer.compose(
            request.name.strip() or loaded_corpus.corpus.name,
            request.goal,
            primary_loaded.asset.modality,
            loaded_corpus.evidence_units,
            insights,
        )
        markdown = render_skill_markdown(skill)
        bundle = DistillBundle(
            asset=primary_loaded.asset,
            evidence_units=loaded_corpus.evidence_units,
            insights=insights,
            skill=skill,
            skill_markdown=markdown,
            corpus=loaded_corpus.corpus,
            evidence_nodes=loaded_corpus.evidence_nodes,
            request_payload=request.to_dict(),
            adapter_metadata={
                'corpus_id': loaded_corpus.corpus.corpus_id,
                'corpus_name': loaded_corpus.corpus.name,
                'asset_count': len(loaded_corpus.loaded_assets),
                'cross_asset': len(loaded_corpus.loaded_assets) > 1,
                'evidence_node_count': len(loaded_corpus.evidence_nodes),
                'corpus_assets': [item.to_dict() for item in loaded_corpus.corpus.assets],
                'asset_adapter_metadata': loaded_corpus.adapter_metadata,
            },
        )
        self.repository.save_bundle(bundle)
        return bundle

    def load_corpus(self, request: CorpusDistillRequest) -> LoadedCorpus:
        request.validate()
        loaded_assets: list[LoadedAsset] = []
        corpus_assets: list[CorpusAssetRef] = []
        evidence_units = []
        adapter_metadata: dict[str, object] = {}

        for asset_input in request.assets:
            adapter = self._adapter_for_modality(asset_input.modality)
            asset_request = self._build_corpus_asset_request(asset_input, request.goal)
            loaded = adapter.load(asset_request)
            loaded_assets.append(loaded)
            evidence_units.extend(loaded.evidence_units)
            merged_metadata = dict(loaded.asset.metadata)
            merged_metadata.update(asset_input.metadata)
            corpus_assets.append(
                CorpusAssetRef(
                    asset_id=loaded.asset.asset_id,
                    modality=loaded.asset.modality,
                    source_uri=loaded.asset.source_uri,
                    role=asset_input.role,
                    title_hint=asset_input.title_hint or loaded.title_hint,
                    metadata=merged_metadata,
                )
            )
            adapter_metadata[loaded.asset.asset_id] = {
                'role': asset_input.role,
                'modality': loaded.asset.modality.value,
                'source_uri': loaded.asset.source_uri,
                'adapter_metadata': loaded.adapter_metadata,
            }

        corpus_name = request.name.strip() or self._derive_corpus_name(loaded_assets)
        corpus_metadata = dict(request.metadata)
        corpus_metadata.setdefault('asset_count', len(corpus_assets))
        corpus_metadata.setdefault(
            'modalities',
            unique_preserve_order(item.modality.value for item in corpus_assets),
        )
        corpus = Corpus(
            name=corpus_name,
            goal=request.goal,
            assets=corpus_assets,
            tags=list(request.tags),
            metadata=corpus_metadata,
        )
        evidence_nodes = self.evidence_builder.build_from_loaded_assets(loaded_assets)
        return LoadedCorpus(
            corpus=corpus,
            loaded_assets=loaded_assets,
            evidence_units=evidence_units,
            evidence_nodes=evidence_nodes,
            adapter_metadata=adapter_metadata,
        )

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

    def _adapter_for_modality(self, modality: Modality):
        if modality == Modality.TEXT:
            return self.text_adapter
        if modality == Modality.AUDIO:
            return self.audio_adapter
        if modality == Modality.IMAGE:
            return self.image_adapter
        if modality == Modality.TABULAR:
            return self.tabular_adapter
        if modality == Modality.VIDEO:
            return self.video_adapter
        raise ValueError('Unsupported modality for corpus distill: %s' % modality.value)

    def _build_corpus_asset_request(self, asset: CorpusAssetInput, goal: DistillGoal) -> AssetDistillRequest:
        source_uri = self._resolve_source_uri(asset.source_uri)
        title_hint = asset.title_hint or None
        if asset.modality == Modality.TEXT:
            return TextDistillRequest(title=title_hint, file_path=source_uri, goal=goal)
        if asset.modality == Modality.AUDIO:
            return AudioDistillRequest(title=title_hint, audio_path=source_uri, goal=goal)
        if asset.modality == Modality.IMAGE:
            return ImageDistillRequest(image_path=source_uri, title=title_hint, goal=goal)
        if asset.modality == Modality.TABULAR:
            return TabularDistillRequest(file_path=source_uri, title=title_hint, goal=goal)
        if asset.modality == Modality.VIDEO:
            return VideoDistillRequest(video_path=source_uri, title=title_hint, goal=goal)
        raise ValueError('Unsupported modality for corpus request: %s' % asset.modality.value)

    def _derive_corpus_name(self, loaded_assets: list[LoadedAsset]) -> str:
        for loaded in loaded_assets:
            if loaded.title_hint.strip():
                return loaded.title_hint.strip()
        if loaded_assets:
            return Path(loaded_assets[0].asset.source_uri).stem.replace('_', ' ')
        return 'corpus-distill'

    def _resolve_source_uri(self, source_uri: str) -> str:
        raw = source_uri.strip()
        parsed = urlparse(raw)
        if parsed.scheme.lower() != 'file':
            return raw
        resolved = unquote(parsed.path or '')
        if parsed.netloc and resolved and not resolved.startswith('/'):
            resolved = '/%s/%s' % (parsed.netloc, resolved)
        if len(resolved) >= 3 and resolved[0] == '/' and resolved[2] == ':':
            resolved = resolved[1:]
        return resolved or raw


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
