from __future__ import annotations

import sys
import typing
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.interfaces import ArtifactRepository
from omni_skill_pipeline.models import (
    Asset,
    ContentType,
    DistillGoal,
    EvidenceUnit,
    Insight,
    InsightType,
    LoadedAsset,
    Modality,
    SkillDocument,
    SkillStep,
    TextDistillRequest,
)
from omni_skill_pipeline.service import DistillationService


class _CapturingRepository(object):
    def __init__(self) -> None:
        self.saved_bundles = []

    def save_bundle(self, bundle) -> dict[str, str]:
        self.saved_bundles.append(bundle)
        return {'bundle': '/virtual/bundle.json', 'skill_markdown': '/virtual/SKILL.md'}


def _build_service_with_protocol_repo(repository: ArtifactRepository, *, loaded: LoadedAsset, insights: list[Insight], skill: SkillDocument):
    text_adapter = Mock()
    text_adapter.load.return_value = loaded

    insight_extractor = Mock()
    insight_extractor.extract.return_value = insights

    skill_composer = Mock()
    skill_composer.compose.return_value = skill

    quality_scorer = Mock()
    quality_scorer.score.return_value = SimpleNamespace(to_dict=lambda: {'overall': 0.73})

    review_policy = Mock()
    review_policy.decide.return_value = SimpleNamespace(
        to_dict=lambda: {
            'decision': 'review_required',
            'reason_codes': ['Q_MANUAL_REVIEW_DEFAULT'],
            'score_snapshot': {'overall': 0.73},
            'thresholds': {},
        }
    )

    review_feedback_engine = Mock()
    review_feedback_engine.build.return_value = SimpleNamespace(to_dict=lambda: {'summary': 'manual review required'})

    service = DistillationService(
        repository=repository,
        text_adapter=text_adapter,
        audio_adapter=Mock(),
        image_adapter=Mock(),
        tabular_adapter=Mock(),
        video_adapter=Mock(),
        insight_extractor=insight_extractor,
        skill_composer=skill_composer,
        evidence_builder=Mock(),
        atom_extractor=Mock(),
        skill_graph_builder=Mock(),
        publication_builder=Mock(),
        quality_scorer=quality_scorer,
        review_policy=review_policy,
        review_feedback_engine=review_feedback_engine,
    )
    service._build_publications = Mock(return_value=(SimpleNamespace(graph_id='graph-1', version='0.1.0', evidence_refs=[]), []))
    service.evidence_builder.build_from_loaded_asset.return_value = []
    return service, text_adapter


class ServiceRepositoryProtocolTests(unittest.TestCase):
    def test_constructor_annotation_uses_repository_protocol(self) -> None:
        annotation = typing.get_type_hints(DistillationService.__init__).get('repository')
        self.assertIs(annotation, ArtifactRepository)

    def test_distill_text_accepts_protocol_repository_and_invokes_save_bundle(self) -> None:
        repository = _CapturingRepository()
        self.assertIsInstance(repository, ArtifactRepository)

        asset = Asset(modality=Modality.TEXT, source_uri='memory://service-protocol')
        evidence = EvidenceUnit(
            asset_id=asset.asset_id,
            span_ref='text:line:1',
            content_type=ContentType.TEXT,
            content='Incident note line one.',
        )
        loaded = LoadedAsset(
            asset=asset,
            evidence_units=[evidence],
            title_hint='Service Protocol Skill',
            adapter_metadata={},
        )
        insight = Insight(
            insight_type=InsightType.PROCEDURE,
            summary='Extract actionable procedure from text evidence.',
            evidence_refs=[evidence.evidence_id],
        )
        skill = SkillDocument(
            name='Service Protocol Skill',
            goal='Validate repository protocol injection.',
            source_modality=Modality.TEXT,
            steps=[SkillStep(step=1, action='Save artifacts through repository protocol.', why='Contract test')],
            evidence_refs=[evidence.evidence_id],
            summary='Service should call repository.save_bundle without concrete coupling.',
        )

        service, text_adapter = _build_service_with_protocol_repo(
            repository,
            loaded=loaded,
            insights=[insight],
            skill=skill,
        )
        request = TextDistillRequest(
            content='incident timeline',
            goal=DistillGoal(domain='ops'),
        )

        bundle = service.distill_text(request)

        text_adapter.load.assert_called_once()
        self.assertEqual(len(repository.saved_bundles), 1)
        self.assertIs(repository.saved_bundles[0], bundle)
        self.assertEqual(bundle.skill.name, 'Service Protocol Skill')


if __name__ == '__main__':
    unittest.main()
