from __future__ import annotations

import logging
from typing import Optional

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
from omni_skill_pipeline.logging_utils import get_request_context
from omni_skill_pipeline.publication_orchestrator import PublicationOrchestrator
from omni_skill_pipeline.quality.feedback import ReviewFeedbackEngine
from omni_skill_pipeline.quality.review_policy import ReviewPolicy
from omni_skill_pipeline.quality.scoring import QualityScorer
from omni_skill_pipeline.render import render_skill_markdown_compat

logger = logging.getLogger(__name__)


def _request_context_extra() -> dict[str, str]:
    request_id, trace_id = get_request_context()
    return {
        'request_id': request_id,
        'trace_id': trace_id,
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
            request_payload=request.to_dict(),
            adapter_metadata={
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
            },
        )
        self.repository.save_bundle(bundle)
        logger.info(
            'Corpus distillation completed.',
            extra={
                **_request_context_extra(),
                'event': 'distill_complete',
                'modality': 'corpus',
                'asset_count': len(request.assets),
                'skill_id': bundle.skill.skill_id,
                'evidence_count': len(bundle.evidence_units),
            },
        )
        return bundle

    def _distill_with_logging(self, *, modality: str, request, adapter) -> DistillBundle:
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
                'event': 'distill_complete',
                'modality': modality,
                'skill_id': bundle.skill.skill_id,
                'evidence_count': len(bundle.evidence_units),
            },
        )
        return bundle

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
            request_payload=request.to_dict(),
            adapter_metadata={
                **loaded.adapter_metadata,
                'evidence_node_count': len(evidence_nodes),
                'publication_types': [item.publication_type.value for item in publications],
                'quality_scores': quality_scores,
                'review_policy': review_decision,
                'review_task': review_task.to_dict(),
                'review_feedback': review_feedback,
            },
        )
        self.repository.save_bundle(bundle)
        return bundle

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
