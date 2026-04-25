from __future__ import annotations

from pathlib import Path
from urllib.parse import unquote, urlparse

from omni_skill_pipeline.extraction import EvidenceBuilder
from omni_skill_pipeline.interfaces import AssetDistillRequest, DistillAdapter
from omni_skill_pipeline.models import (
    AudioDistillRequest,
    Corpus,
    CorpusAssetInput,
    CorpusAssetRef,
    CorpusDistillRequest,
    DistillGoal,
    ImageDistillRequest,
    LoadedAsset,
    LoadedCorpus,
    Modality,
    TabularDistillRequest,
    TextDistillRequest,
    VideoDistillRequest,
)
from omni_skill_pipeline.utils import unique_preserve_order


class DefaultCorpusLoader(object):
    def __init__(
        self,
        *,
        text_adapter: DistillAdapter[TextDistillRequest],
        audio_adapter: DistillAdapter[AudioDistillRequest],
        image_adapter: DistillAdapter[ImageDistillRequest],
        tabular_adapter: DistillAdapter[TabularDistillRequest],
        video_adapter: DistillAdapter[VideoDistillRequest],
        evidence_builder: EvidenceBuilder,
    ) -> None:
        self.text_adapter = text_adapter
        self.audio_adapter = audio_adapter
        self.image_adapter = image_adapter
        self.tabular_adapter = tabular_adapter
        self.video_adapter = video_adapter
        self.evidence_builder = evidence_builder

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
