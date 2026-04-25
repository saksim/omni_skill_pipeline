from __future__ import annotations

import logging
from typing import Any, Optional
from uuid import uuid4

from omni_skill_pipeline.assembly.publication_builder import PublicationBuilder
from omni_skill_pipeline.assembly.skill_graph_builder import SkillGraphBuilder
from omni_skill_pipeline.corpus_loader import DefaultCorpusLoader
from omni_skill_pipeline.extraction import EvidenceBuilder, LegacyInsightAtomExtractor
from omni_skill_pipeline.interfaces import (
    ArtifactRepository,
    AtomExtractor,
    CorpusLoader,
    DistillAdapter,
    InsightExtractor,
    SkillComposer,
)
from omni_skill_pipeline.models import (
    AudioDistillRequest,
    CorpusDistillRequest,
    DistillBundle,
    DistillGoal,
    ImageDistillRequest,
    LoadedCorpus,
    Publication,
    ReviewTask,
    SkillDocument,
    SkillGraph,
    TabularDistillRequest,
    TextDistillRequest,
    VideoDistillRequest,
)
from omni_skill_pipeline.logging_utils import get_request_context, reset_request_context, set_request_context
from omni_skill_pipeline.publication_orchestrator import PublicationOrchestrator
from omni_skill_pipeline.quality.feedback import ReviewFeedbackEngine
from omni_skill_pipeline.quality.review_policy import ReviewPolicy
from omni_skill_pipeline.quality.scoring import QualityScorer
from omni_skill_pipeline.redaction import redact_sensitive_data
from omni_skill_pipeline.render import render_skill_markdown_compat

logger = logging.getLogger(__name__)


def _request_context_extra() -> dict[str, str]:
    request_id, trace_id = get_request_context()
    return {
        'request_id': request_id,
        'trace_id': trace_id,
    }


def _ensure_request_context(prefix: str) -> tuple[tuple | None, str, str]:
    request_id, trace_id = get_request_context()
    if request_id and trace_id:
        return None, request_id, trace_id

    normalized_prefix = str(prefix).strip().replace(' ', '-') or 'distill'
    if not request_id:
        request_id = '%s-%s' % (normalized_prefix, uuid4().hex[:12])
    if not trace_id:
        trace_id = request_id

    request_token, trace_token = set_request_context(request_id=request_id, trace_id=trace_id)
    return (request_token, trace_token), request_id, trace_id


def _reset_context_if_needed(tokens: tuple | None) -> None:
    if tokens is None:
        return
    request_token, trace_token = tokens
    reset_request_context(request_token=request_token, trace_token=trace_token)


def _bundle_trace_extra(bundle: DistillBundle) -> dict[str, object]:
    publication_types = [item.publication_type.value for item in bundle.publications]
    publication_ids = [item.publication_id for item in bundle.publications]
    graph_id = bundle.skill_graph.graph_id if bundle.skill_graph is not None else ''
    review_status = ''
    if bundle.review_task is not None:
        review_status = bundle.review_task.status.value
    elif bundle.skill_graph is not None:
        review_status = bundle.skill_graph.review_status.value
    return {
        'asset_id': bundle.asset.asset_id,
        'asset_modality': bundle.asset.modality.value,
        'graph_id': graph_id,
        'publication_count': len(bundle.publications),
        'publication_types': publication_types,
        'publication_ids': publication_ids,
        'review_status': review_status,
    }


class DistillationService(object):
    def __init__(
        self,
        repository: ArtifactRepository,
        *,
        text_adapter: DistillAdapter[TextDistillRequest],
        audio_adapter: DistillAdapter[AudioDistillRequest],
        image_adapter: DistillAdapter[ImageDistillRequest],
        tabular_adapter: DistillAdapter[TabularDistillRequest],
        video_adapter: DistillAdapter[VideoDistillRequest],
        insight_extractor: InsightExtractor,
        skill_composer: SkillComposer,
        evidence_builder: EvidenceBuilder | None = None,
        atom_extractor: AtomExtractor | None = None,
        skill_graph_builder: SkillGraphBuilder | None = None,
        publication_builder: PublicationBuilder | None = None,
        quality_scorer: QualityScorer | None = None,
        review_policy: ReviewPolicy | None = None,
        review_feedback_engine: ReviewFeedbackEngine | None = None,
        corpus_loader: CorpusLoader | None = None,
        publication_orchestrator: PublicationOrchestrator | None = None,
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
        self.atom_extractor = atom_extractor or LegacyInsightAtomExtractor(insight_extractor=insight_extractor)
        self.skill_graph_builder = skill_graph_builder or SkillGraphBuilder()
        self.publication_builder = publication_builder or PublicationBuilder()
        self.quality_scorer = quality_scorer or QualityScorer()
        self.review_policy = review_policy or ReviewPolicy()
        self.review_feedback_engine = review_feedback_engine or ReviewFeedbackEngine()
        self.corpus_loader = corpus_loader or DefaultCorpusLoader(
            text_adapter=self.text_adapter,
            audio_adapter=self.audio_adapter,
            image_adapter=self.image_adapter,
            tabular_adapter=self.tabular_adapter,
            video_adapter=self.video_adapter,
            evidence_builder=self.evidence_builder,
        )
        self.publication_orchestrator = publication_orchestrator or PublicationOrchestrator(
            atom_extractor=self.atom_extractor,
            skill_graph_builder=self.skill_graph_builder,
            publication_builder=self.publication_builder,
        )

    def distill_text(self, request: TextDistillRequest) -> DistillBundle:
        return self._distill_with_logging(modality='text', request=request, adapter=self.text_adapter)

    def distill_audio(self, request: AudioDistillRequest) -> DistillBundle:
        return self._distill_with_logging(modality='audio', request=request, adapter=self.audio_adapter)

    def distill_image(self, request: ImageDistillRequest) -> DistillBundle:
        return self._distill_with_logging(modality='image', request=request, adapter=self.image_adapter)

    def distill_tabular(self, request: TabularDistillRequest) -> DistillBundle:
        return self._distill_with_logging(modality='tabular', request=request, adapter=self.tabular_adapter)

    def distill_video(self, request: VideoDistillRequest) -> DistillBundle:
        return self._distill_with_logging(modality='video', request=request, adapter=self.video_adapter)

    def distill_corpus(self, request: CorpusDistillRequest) -> DistillBundle:
        context_tokens, _, _ = _ensure_request_context('distill-corpus')
        try:
            logger.info(
                'Corpus distillation started.',
                extra={
                    **_request_context_extra(),
                    'event': 'distill_start',
                    'modality': 'corpus',
                    'asset_count': len(request.assets),
                    'goal_domain': request.goal.domain,
                },
            )
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
            skill_graph, publications = self._build_publications(
                title_hint=request.name.strip() or loaded_corpus.corpus.name,
                goal=request.goal,
                evidence_nodes=loaded_corpus.evidence_nodes,
                skill=skill,
            )
            markdown = render_skill_markdown_compat(publications=publications, skill=skill, graph=skill_graph)
            quality_scores = self.quality_scorer.score(
                skill=skill,
                skill_graph=skill_graph,
                evidence_nodes=loaded_corpus.evidence_nodes,
                publications=publications,
            ).to_dict()
            review_decision = self.review_policy.decide(quality_scores).to_dict()
            review_task = ReviewTask.from_review_policy(skill_id=skill.skill_id, review_policy=review_decision)
            review_feedback = self.review_feedback_engine.build(review_task).to_dict()
            provider_footprint = self._build_provider_footprint(
                asset_adapter_metadata=loaded_corpus.adapter_metadata,
                corpus_id=loaded_corpus.corpus.corpus_id,
            )
            bundle = DistillBundle(
                asset=primary_loaded.asset,
                evidence_units=loaded_corpus.evidence_units,
                insights=insights,
                skill=skill,
                skill_markdown=markdown,
                skill_graph=skill_graph,
                publications=publications,
                quality_scores=quality_scores,
                review_task=review_task,
                corpus=loaded_corpus.corpus,
                evidence_nodes=loaded_corpus.evidence_nodes,
                request_payload=redact_sensitive_data(request.to_dict()),
                adapter_metadata=redact_sensitive_data({
                    'corpus_id': loaded_corpus.corpus.corpus_id,
                    'corpus_name': loaded_corpus.corpus.name,
                    'asset_count': len(loaded_corpus.loaded_assets),
                    'cross_asset': len(loaded_corpus.loaded_assets) > 1,
                    'evidence_node_count': len(loaded_corpus.evidence_nodes),
                    'publication_types': [item.publication_type.value for item in publications],
                    'quality_scores': quality_scores,
                    'review_policy': review_decision,
                    'review_task': review_task.to_dict(),
                    'review_feedback': review_feedback,
                    'corpus_assets': [item.to_dict() for item in loaded_corpus.corpus.assets],
                    'asset_adapter_metadata': loaded_corpus.adapter_metadata,
                    'provider_footprint': provider_footprint,
                }),
            )
            self.repository.save_bundle(bundle)
            logger.info(
                'Corpus distillation completed.',
                extra={
                    **_request_context_extra(),
                    **_bundle_trace_extra(bundle),
                    'event': 'distill_complete',
                    'modality': 'corpus',
                    'asset_count': len(request.assets),
                    'asset_ids': [item.asset_id for item in loaded_corpus.corpus.assets],
                    'corpus_id': loaded_corpus.corpus.corpus_id,
                    'skill_id': bundle.skill.skill_id,
                    'evidence_count': len(bundle.evidence_units),
                    'provider_call_total': provider_footprint.get('summary', {}).get('total_calls', 0),
                    'provider_count': len(provider_footprint.get('summary', {}).get('providers', {})),
                },
            )
            return bundle
        finally:
            _reset_context_if_needed(context_tokens)

    def _distill_with_logging(self, *, modality: str, request, adapter) -> DistillBundle:
        context_tokens, _, _ = _ensure_request_context('distill-%s' % modality)
        try:
            logger.info(
                'Distillation started.',
                extra={
                    **_request_context_extra(),
                    'event': 'distill_start',
                    'modality': modality,
                    'goal_domain': getattr(getattr(request, 'goal', None), 'domain', ''),
                },
            )
            bundle = self._distill(request, adapter)
            logger.info(
                'Distillation completed.',
                extra={
                    **_request_context_extra(),
                    **_bundle_trace_extra(bundle),
                    'event': 'distill_complete',
                    'modality': modality,
                    'skill_id': bundle.skill.skill_id,
                    'evidence_count': len(bundle.evidence_units),
                },
            )
            return bundle
        finally:
            _reset_context_if_needed(context_tokens)

    def load_corpus(self, request: CorpusDistillRequest) -> LoadedCorpus:
        return self.corpus_loader.load_corpus(request)

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
        evidence_nodes = self.evidence_builder.build_from_loaded_asset(loaded)
        skill_graph, publications = self._build_publications(
            title_hint=loaded.title_hint,
            goal=request.goal,
            evidence_nodes=evidence_nodes,
            skill=skill,
        )
        markdown = render_skill_markdown_compat(publications=publications, skill=skill, graph=skill_graph)
        quality_scores = self.quality_scorer.score(
            skill=skill,
            skill_graph=skill_graph,
            evidence_nodes=evidence_nodes,
            publications=publications,
        ).to_dict()
        review_decision = self.review_policy.decide(quality_scores).to_dict()
        review_task = ReviewTask.from_review_policy(skill_id=skill.skill_id, review_policy=review_decision)
        review_feedback = self.review_feedback_engine.build(review_task).to_dict()
        provider_footprint = self._build_provider_footprint(
            asset_adapter_metadata={
                loaded.asset.asset_id: {
                    'role': 'primary',
                    'modality': loaded.asset.modality.value,
                    'source_uri': loaded.asset.source_uri,
                    'adapter_metadata': loaded.adapter_metadata,
                }
            }
        )
        bundle = DistillBundle(
            asset=loaded.asset,
            evidence_units=loaded.evidence_units,
            insights=insights,
            skill=skill,
            skill_markdown=markdown,
            skill_graph=skill_graph,
            publications=publications,
            quality_scores=quality_scores,
            review_task=review_task,
            evidence_nodes=evidence_nodes,
            request_payload=redact_sensitive_data(request.to_dict()),
            adapter_metadata=redact_sensitive_data({
                **loaded.adapter_metadata,
                'evidence_node_count': len(evidence_nodes),
                'publication_types': [item.publication_type.value for item in publications],
                'quality_scores': quality_scores,
                'review_policy': review_decision,
                'review_task': review_task.to_dict(),
                'review_feedback': review_feedback,
                'provider_footprint': provider_footprint,
            }),
        )
        self.repository.save_bundle(bundle)
        return bundle

    def _build_provider_footprint(
        self,
        *,
        asset_adapter_metadata: dict[str, object],
        corpus_id: str = '',
    ) -> dict[str, object]:
        asset_breakdown: list[dict[str, object]] = []
        provider_totals: dict[str, dict[str, int]] = {}
        channel_totals: dict[str, dict[str, int]] = {}
        total_calls = 0
        total_successes = 0
        total_failures = 0

        for asset_id, raw_item in asset_adapter_metadata.items():
            if not isinstance(raw_item, dict):
                continue
            adapter_metadata = raw_item.get('adapter_metadata', {})
            if not isinstance(adapter_metadata, dict):
                adapter_metadata = {}
            provider_calls = self._extract_provider_calls(adapter_metadata)
            asset_call_total = 0
            for call in provider_calls:
                channel = str(call.get('channel', '')).strip() or 'provider'
                provider = str(call.get('provider', '')).strip() or 'unknown'
                calls = self._safe_int(call.get('calls', 0))
                successes = self._safe_int(call.get('successes', 0))
                failures = self._safe_int(call.get('failures', 0))
                asset_call_total += calls
                total_calls += calls
                total_successes += successes
                total_failures += failures
                provider_entry = provider_totals.setdefault(provider, {'calls': 0, 'successes': 0, 'failures': 0})
                provider_entry['calls'] += calls
                provider_entry['successes'] += successes
                provider_entry['failures'] += failures
                channel_entry = channel_totals.setdefault(channel, {'calls': 0, 'successes': 0, 'failures': 0})
                channel_entry['calls'] += calls
                channel_entry['successes'] += successes
                channel_entry['failures'] += failures
            asset_breakdown.append(
                {
                    'asset_id': str(asset_id).strip(),
                    'role': str(raw_item.get('role', '')).strip(),
                    'modality': str(raw_item.get('modality', '')).strip(),
                    'source_uri': str(raw_item.get('source_uri', '')).strip(),
                    'call_total': asset_call_total,
                    'provider_calls': provider_calls,
                }
            )
        asset_breakdown.sort(key=lambda item: item.get('asset_id', ''))

        runtime_provider_audits = self._collect_runtime_provider_audits()
        return {
            'corpus_id': str(corpus_id).strip(),
            'asset_breakdown': asset_breakdown,
            'summary': {
                'total_calls': total_calls,
                'total_successes': total_successes,
                'total_failures': total_failures,
                'providers': dict(sorted(provider_totals.items())),
                'channels': dict(sorted(channel_totals.items())),
            },
            'runtime_provider_audits': runtime_provider_audits,
        }

    def _extract_provider_calls(self, adapter_metadata: dict[str, object]) -> list[dict[str, object]]:
        calls: list[dict[str, object]] = []
        raw_provider_calls = adapter_metadata.get('provider_calls')
        if isinstance(raw_provider_calls, list):
            for item in raw_provider_calls:
                if not isinstance(item, dict):
                    continue
                calls.append(
                    {
                        'channel': str(item.get('channel', '')).strip() or 'provider',
                        'provider': str(item.get('provider', '')).strip() or 'unknown',
                        'calls': self._safe_int(item.get('calls', 0)),
                        'successes': self._safe_int(item.get('successes', 0)),
                        'failures': self._safe_int(item.get('failures', 0)),
                    }
                )

        transcript_source = str(adapter_metadata.get('transcript_source', '')).strip()
        has_audio_transcription = any(str(item.get('channel', '')).strip() == 'audio_transcription' for item in calls)
        if transcript_source.startswith('provider:') and not has_audio_transcription:
            provider_name = transcript_source.split(':', 1)[1].strip() or 'unknown'
            calls.append(
                {
                    'channel': 'audio_transcription',
                    'provider': provider_name,
                    'calls': 1,
                    'successes': 1,
                    'failures': 0,
                }
            )
        return self._merge_provider_calls(calls)

    def _merge_provider_calls(self, calls: list[dict[str, object]]) -> list[dict[str, object]]:
        merged: dict[tuple[str, str], dict[str, object]] = {}
        for item in calls:
            if not isinstance(item, dict):
                continue
            channel = str(item.get('channel', '')).strip() or 'provider'
            provider = str(item.get('provider', '')).strip() or 'unknown'
            key = (channel, provider)
            if key not in merged:
                merged[key] = {
                    'channel': channel,
                    'provider': provider,
                    'calls': 0,
                    'successes': 0,
                    'failures': 0,
                }
            merged[key]['calls'] += self._safe_int(item.get('calls', 0))
            merged[key]['successes'] += self._safe_int(item.get('successes', 0))
            merged[key]['failures'] += self._safe_int(item.get('failures', 0))
        return sorted(merged.values(), key=lambda item: (str(item['channel']), str(item['provider'])))

    def _collect_runtime_provider_audits(self) -> list[dict[str, object]]:
        roots: list[object] = [
            self.text_adapter,
            self.audio_adapter,
            self.image_adapter,
            self.tabular_adapter,
            self.video_adapter,
            self.skill_composer,
            self.atom_extractor,
        ]
        stack = [item for item in roots if item is not None]
        visited: set[int] = set()
        audits: list[dict[str, object]] = []
        while stack:
            component = stack.pop()
            component_id = id(component)
            if component_id in visited:
                continue
            visited.add(component_id)
            snapshot_fn = getattr(component, 'provider_call_audit_snapshot', None)
            if callable(snapshot_fn):
                try:
                    snapshot = snapshot_fn()
                except Exception:
                    snapshot = None
                if isinstance(snapshot, dict) and snapshot:
                    snapshot = dict(snapshot)
                    snapshot.setdefault('component', component.__class__.__name__)
                    audits.append(snapshot)
            for attr_name in (
                'transcriber',
                'providers',
                'analyzers',
                'composers',
                'ocr_provider',
                'analyzer',
                'media_processor',
                'audio_adapter',
            ):
                child = getattr(component, attr_name, None)
                if isinstance(child, (list, tuple, set)):
                    stack.extend(item for item in child if item is not None)
                elif child is not None:
                    stack.append(child)
        return sorted(audits, key=lambda item: str(item.get('component', '')))

    def _safe_int(self, value: Any) -> int:
        try:
            return max(0, int(value))
        except (TypeError, ValueError):
            return 0

    def _build_publications(
        self,
        *,
        title_hint: str,
        goal: DistillGoal,
        evidence_nodes,
        skill: SkillDocument,
    ) -> tuple[SkillGraph, list[Publication]]:
        return self.publication_orchestrator.build_publications(
            title_hint=title_hint,
            goal=goal,
            evidence_nodes=evidence_nodes,
            skill=skill,
        )


def build_service(repo_root: Optional[str] = None) -> DistillationService:
    # composition root moved to service_factory.py; keep this thin adapter for API stability
    from omni_skill_pipeline.service_factory import build_service as build_service_factory

    return build_service_factory(repo_root=repo_root)
