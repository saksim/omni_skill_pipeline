from __future__ import annotations

import shutil
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

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
from omni_skill_pipeline.repository import FileArtifactRepository
from omni_skill_pipeline.service import DistillationService


class ReviewQueueIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace = REPO_ROOT / 'tests' / '.tmp_runtime' / ('review_queue_integration_%s' % uuid4().hex)
        self.workspace.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.workspace, ignore_errors=True)

    def test_service_review_required_flow_persists_queryable_review_queue(self) -> None:
        repository = FileArtifactRepository(self.workspace / 'drafts')

        asset = Asset(modality=Modality.TEXT, source_uri='memory://integration-review-queue')
        evidence = EvidenceUnit(
            asset_id=asset.asset_id,
            span_ref='text:line:1',
            content_type=ContentType.TEXT,
            content='Integration flow should enqueue review_required tasks.',
        )
        loaded = LoadedAsset(
            asset=asset,
            evidence_units=[evidence],
            title_hint='Integration Review Skill',
            adapter_metadata={},
        )
        insight = Insight(
            insight_type=InsightType.PROCEDURE,
            summary='Escalate to manual review queue.',
            evidence_refs=[evidence.evidence_id],
        )
        skill = SkillDocument(
            name='Integration Review Skill',
            goal='Ensure review queue can be queried and consumed.',
            source_modality=Modality.TEXT,
            steps=[SkillStep(step=1, action='Create review-required output')],
            evidence_refs=[evidence.evidence_id],
        )

        text_adapter = Mock()
        text_adapter.load.return_value = loaded

        insight_extractor = Mock()
        insight_extractor.extract.return_value = [insight]

        skill_composer = Mock()
        skill_composer.compose.return_value = skill

        quality_scorer = Mock()
        quality_scorer.score.return_value = SimpleNamespace(to_dict=lambda: {'overall_score': 0.51})

        review_policy = Mock()
        review_policy.decide.return_value = SimpleNamespace(
            to_dict=lambda: {
                'decision': 'review_required',
                'reason_codes': ['Q_MANUAL_REVIEW_DEFAULT'],
                'score_snapshot': {'overall_score': 0.51},
                'thresholds': {'auto_publish_min': 0.75},
            }
        )

        review_feedback_engine = Mock()
        review_feedback_engine.build.return_value = SimpleNamespace(
            to_dict=lambda: {
                'decision': 'review_required',
                'reason_codes': ['Q_MANUAL_REVIEW_DEFAULT'],
                'summary': 'manual review required',
            }
        )

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

        bundle = service.distill_text(TextDistillRequest(content='trigger review queue', goal=DistillGoal(domain='ops')))

        pending = repository.list_review_queue()
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]['review_task_id'], bundle.review_task.review_task_id)
        self.assertEqual(pending[0]['decision'], 'review_required')

        consumed = repository.consume_review_task(consumer='review-worker')
        self.assertIsNotNone(consumed)
        self.assertEqual(consumed['review_task_id'], bundle.review_task.review_task_id)
        self.assertEqual(consumed['queue_status'], 'consumed')
        self.assertEqual(consumed['claimed_by'], 'review-worker')
        self.assertEqual(repository.list_review_queue(), [])

        closed = repository.close_review_task(
            bundle.review_task.review_task_id,
            status='published',
            closed_by='review-worker',
            review_notes='accepted during manual pass',
        )
        self.assertIsNotNone(closed)
        self.assertEqual(closed['queue_status'], 'closed')
        self.assertEqual(closed['status'], 'published')
        self.assertEqual(closed['closed_by'], 'review-worker')
        self.assertEqual(closed['review_notes'], 'accepted during manual pass')
        self.assertEqual(len(repository.list_review_queue(queue_status='closed')), 1)


if __name__ == '__main__':
    unittest.main()
