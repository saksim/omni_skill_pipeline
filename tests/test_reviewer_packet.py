from __future__ import annotations

import json
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
    Corpus,
    CorpusAssetRef,
    CorpusDistillRequest,
    DistillGoal,
    EvidenceNode,
    EvidenceUnit,
    Insight,
    InsightType,
    LoadedAsset,
    LoadedCorpus,
    Modality,
    SkillDocument,
    SkillGraph,
    SkillStep,
    StepNode,
    TextDistillRequest,
)
from omni_skill_pipeline.repository import FileArtifactRepository
from omni_skill_pipeline.service import DistillationService


class ReviewerPacketTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace = REPO_ROOT / 'tests' / '.tmp_runtime' / ('reviewer_packet_%s' % uuid4().hex)
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.repository = FileArtifactRepository(self.workspace / 'drafts')

    def tearDown(self) -> None:
        shutil.rmtree(self.workspace, ignore_errors=True)

    def test_single_asset_distillation_persists_reviewer_packet(self) -> None:
        asset = Asset(modality=Modality.IMAGE, source_uri='memory://dashboard.png')
        evidence = EvidenceUnit(
            asset_id=asset.asset_id,
            span_ref='image:region:1',
            content_type=ContentType.OCR,
            content='Service status: degraded',
            tags=['layout_role:banner'],
        )
        node = EvidenceNode(
            asset_id=asset.asset_id,
            modality=Modality.IMAGE,
            content_type=ContentType.OCR,
            span_ref=evidence.span_ref,
            text_content=evidence.content,
            evidence_id=evidence.evidence_id,
        )
        loaded = LoadedAsset(
            asset=asset,
            evidence_units=[evidence],
            title_hint='Dashboard Review Skill',
            adapter_metadata={},
        )
        skill = SkillDocument(
            name='Dashboard Review Skill',
            goal='Review degraded dashboard screenshots.',
            source_modality=Modality.IMAGE,
            steps=[SkillStep(step=1, action='Check degraded service banner.')],
            evidence_refs=[evidence.evidence_id],
            summary='Review dashboard evidence before acting.',
        )
        service = self._build_mock_service(loaded=loaded, evidence_nodes=[node], skill=skill)

        bundle = service.distill_text(TextDistillRequest(content='dashboard evidence', goal=DistillGoal(domain='ops')))

        self.assertIn('reviewer_packet', bundle.artifacts)
        packet = json.loads(Path(bundle.artifacts['reviewer_packet']).read_text(encoding='utf-8'))
        self.assertEqual(packet['schema_version'], 'reviewer_packet.v1')
        self.assertEqual(packet['skill_id'], skill.skill_id)
        self.assertEqual(packet['review_task_id'], bundle.review_task.review_task_id)
        self.assertEqual(packet['input_summary']['modalities'], ['image'])
        self.assertEqual(packet['evidence_links'][0]['evidence_id'], evidence.evidence_id)
        self.assertIn('quality_scores', packet)
        self.assertTrue(any(item['code'] == 'image_requires_ocr_review' for item in packet['risk_flags']))
        checklist_ids = {item['check_id'] for item in packet['approval_checklist']}
        self.assertIn('ocr_visual_check', checklist_ids)

        pending = self.repository.list_review_queue()
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]['reviewer_packet_path'], bundle.artifacts['reviewer_packet'])

    def test_mixed_corpus_distillation_persists_cross_asset_reviewer_packet(self) -> None:
        text_asset = Asset(modality=Modality.TEXT, source_uri='memory://incident.md')
        audio_asset = Asset(modality=Modality.AUDIO, source_uri='memory://incident.wav')
        text_evidence = EvidenceUnit(
            asset_id=text_asset.asset_id,
            span_ref='text:line:1',
            content_type=ContentType.TEXT,
            content='Rebuild incident timeline.',
        )
        audio_evidence = EvidenceUnit(
            asset_id=audio_asset.asset_id,
            span_ref='audio:segment:1',
            content_type=ContentType.SPEECH,
            content='Verify recovery with latency.',
        )
        text_node = EvidenceNode(
            asset_id=text_asset.asset_id,
            modality=Modality.TEXT,
            content_type=ContentType.TEXT,
            span_ref=text_evidence.span_ref,
            text_content=text_evidence.content,
            evidence_id=text_evidence.evidence_id,
        )
        audio_node = EvidenceNode(
            asset_id=audio_asset.asset_id,
            modality=Modality.AUDIO,
            content_type=ContentType.SPEECH,
            span_ref=audio_evidence.span_ref,
            text_content=audio_evidence.content,
            evidence_id=audio_evidence.evidence_id,
        )
        corpus = Corpus(
            name='Incident mixed corpus',
            goal=DistillGoal(domain='incident_response'),
            assets=[
                CorpusAssetRef(
                    asset_id=text_asset.asset_id,
                    modality=Modality.TEXT,
                    source_uri=text_asset.source_uri,
                    role='primary',
                ),
                CorpusAssetRef(
                    asset_id=audio_asset.asset_id,
                    modality=Modality.AUDIO,
                    source_uri=audio_asset.source_uri,
                    role='context',
                ),
            ],
        )
        loaded_corpus = LoadedCorpus(
            corpus=corpus,
            loaded_assets=[
                LoadedAsset(asset=text_asset, evidence_units=[text_evidence], title_hint='Incident doc'),
                LoadedAsset(asset=audio_asset, evidence_units=[audio_evidence], title_hint='Incident call'),
            ],
            evidence_units=[text_evidence, audio_evidence],
            evidence_nodes=[text_node, audio_node],
            adapter_metadata={
                text_asset.asset_id: {
                    'role': 'primary',
                    'modality': 'text',
                    'source_uri': text_asset.source_uri,
                    'adapter_metadata': {},
                },
                audio_asset.asset_id: {
                    'role': 'context',
                    'modality': 'audio',
                    'source_uri': audio_asset.source_uri,
                    'adapter_metadata': {},
                },
            },
        )
        insight = Insight(
            insight_type=InsightType.PROCEDURE,
            summary='Use document and call evidence together.',
            evidence_refs=[text_evidence.evidence_id, audio_evidence.evidence_id],
        )
        skill = SkillDocument(
            name='Incident Mixed Corpus Skill',
            goal='Build incident runbook from mixed evidence.',
            source_modality=Modality.TEXT,
            steps=[SkillStep(step=1, action='Rebuild incident timeline from all assets.')],
            evidence_refs=[text_evidence.evidence_id, audio_evidence.evidence_id],
        )
        service = self._build_mock_service(
            loaded=loaded_corpus.loaded_assets[0],
            evidence_nodes=[text_node, audio_node],
            insights=[insight],
            skill=skill,
        )
        service.load_corpus = Mock(return_value=loaded_corpus)

        request = CorpusDistillRequest(
            name='Incident mixed corpus',
            assets=[],
            goal=DistillGoal(domain='incident_response'),
        )
        bundle = service.distill_corpus(request)

        self.assertIn('reviewer_packet', bundle.artifacts)
        packet = json.loads(Path(bundle.artifacts['reviewer_packet']).read_text(encoding='utf-8'))
        self.assertEqual(packet['input_summary']['asset_count'], 2)
        self.assertEqual(packet['input_summary']['modalities'], ['text', 'audio'])
        self.assertIn('corpus', packet)
        self.assertIn('cross_asset_conflicts', packet)
        self.assertTrue(packet['cross_asset_conflicts'])
        self.assertTrue(any(item['code'] == 'cross_asset_consistency_required' for item in packet['risk_flags']))
        checklist_ids = {item['check_id'] for item in packet['approval_checklist']}
        self.assertIn('cross_asset_consistency', checklist_ids)
        self.assertIn('transcript_check', checklist_ids)

    def _build_mock_service(
        self,
        *,
        loaded: LoadedAsset,
        evidence_nodes: list[EvidenceNode],
        skill: SkillDocument,
        insights: list[Insight] | None = None,
    ) -> DistillationService:
        insight_payload = insights or [
            Insight(
                insight_type=InsightType.PROCEDURE,
                summary='Escalate generated skill to manual review.',
                evidence_refs=[item.evidence_id for item in loaded.evidence_units],
            )
        ]
        text_adapter = Mock()
        text_adapter.load.return_value = loaded
        insight_extractor = Mock()
        insight_extractor.extract.return_value = insight_payload
        skill_composer = Mock()
        skill_composer.compose.return_value = skill
        quality_scorer = Mock()
        quality_scorer.score.return_value = SimpleNamespace(
            to_dict=lambda: {
                'overall_score': 0.92,
                'traceability_score': 0.9,
                'actionability_score': 0.88,
            }
        )
        review_policy = Mock()
        review_policy.decide.return_value = SimpleNamespace(
            to_dict=lambda: {
                'decision': 'review_required',
                'reason_codes': ['controlled_trial_requires_review'],
                'score_snapshot': {'overall_score': 0.92},
                'thresholds': {'auto_publish_min': 0.8},
            }
        )
        review_feedback_engine = Mock()
        review_feedback_engine.build.return_value = SimpleNamespace(
            to_dict=lambda: {
                'decision': 'review_required',
                'reason_codes': ['controlled_trial_requires_review'],
                'summary': 'Manual review required for controlled trial.',
                'follow_up_checks': ['Confirm evidence alignment.'],
            }
        )
        service = DistillationService(
            repository=self.repository,
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
        service.evidence_builder.build_from_loaded_asset.return_value = evidence_nodes
        service._build_publications = Mock(
            return_value=(
                SkillGraph(
                    name='%s graph' % skill.name,
                    goal=skill.goal,
                    source_modalities=[item.modality for item in evidence_nodes] or [skill.source_modality],
                    steps=[StepNode(step=1, action='Review generated skill.')],
                    evidence_refs=[item.evidence_id for item in evidence_nodes],
                ),
                [],
            )
        )
        return service


if __name__ == '__main__':
    unittest.main()
