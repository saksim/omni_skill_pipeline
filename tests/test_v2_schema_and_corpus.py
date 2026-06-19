from __future__ import annotations

import json
import shutil
import sys
import unittest
from dataclasses import fields
from pathlib import Path
from uuid import uuid4

from jsonschema import ValidationError, validate

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.adapters.audio import AudioAdapter
from omni_skill_pipeline.adapters.text import TextAdapter
from omni_skill_pipeline.models import (
    ContentType,
    CorpusAssetInput,
    CorpusDistillRequest,
    DistillGoal,
    GraphEdgeType,
    Modality,
    SkillGraph,
    SkillGraphEdge,
    StepNode,
    TextDistillRequest,
)
from omni_skill_pipeline.pipeline import HeuristicInsightExtractor, HeuristicSkillComposer
from omni_skill_pipeline.providers.base import TranscriptSegment, TranscriptionResult
from omni_skill_pipeline.repository import FileArtifactRepository
from omni_skill_pipeline.schema import SKILL_GRAPH_SCHEMA
from omni_skill_pipeline.service import DistillationService


class _FakeTranscriber(object):
    def transcribe(self, audio_path: Path, *, language: str | None = None, prompt: str | None = None) -> TranscriptionResult:
        return TranscriptionResult(
            text='Rebuild incident timeline and verify recovery.',
            segments=[
                TranscriptSegment(text='Rebuild incident timeline.', start=0.0, end=2.0, confidence=0.9),
                TranscriptSegment(text='Verify recovery with latency and error rate.', start=2.0, end=5.0, confidence=0.86),
            ],
            language=language,
            model_name='fake-transcriber',
        )


class _UnsupportedAdapter(object):
    def load(self, request):
        raise AssertionError('This adapter should not be invoked by the current test.')


class SkillGraphSchemaTests(unittest.TestCase):
    def test_skill_graph_contract_file_matches_runtime_schema(self) -> None:
        contract_path = REPO_ROOT / 'docs' / 'latest' / 'contracts' / 'skill-graph.schema.json'
        file_payload = json.loads(contract_path.read_text(encoding='utf-8'))
        self.assertEqual(file_payload, SKILL_GRAPH_SCHEMA)

    def test_skill_graph_required_fields_align_with_dataclass(self) -> None:
        dataclass_fields = {item.name for item in fields(SkillGraph)}
        required = set(SKILL_GRAPH_SCHEMA['required'])
        self.assertEqual(dataclass_fields, required)

    def test_skill_graph_schema_validation_accepts_and_rejects_payloads(self) -> None:
        graph = SkillGraph(
            name='Incident triage graph',
            goal='Convert evidence to triage steps.',
            source_modalities=[Modality.TEXT],
            steps=[StepNode(step=1, action='Rebuild timeline.', why='Anchor incident context.')],
            edges=[
                SkillGraphEdge(
                    edge_type=GraphEdgeType.DEPENDS_ON,
                    source_node_id='node-2',
                    target_node_id='node-1',
                )
            ],
        )
        payload = graph.to_dict()
        validate(instance=payload, schema=SKILL_GRAPH_SCHEMA)

        invalid = dict(payload)
        invalid.pop('graph_id', None)
        with self.assertRaises(ValidationError):
            validate(instance=invalid, schema=SKILL_GRAPH_SCHEMA)

        invalid_edge = dict(payload)
        invalid_edge['edges'] = [dict(payload['edges'][0], edge_type='bad-edge')]
        with self.assertRaises(ValidationError):
            validate(instance=invalid_edge, schema=SKILL_GRAPH_SCHEMA)


class CorpusServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace = REPO_ROOT / 'tests' / '.tmp_runtime' / uuid4().hex
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.repository = FileArtifactRepository(self.workspace / 'drafts')
        self.text_file = self.workspace / 'incident.md'
        self.text_file.write_text(
            '\n'.join(
                [
                    '# Incident Runbook',
                    '1. Rebuild the timeline.',
                    '2. Merge duplicate alerts.',
                    'Verify recovery with latency and error rate.',
                ]
            ),
            encoding='utf-8',
        )
        self.audio_file = self.workspace / 'incident.wav'
        self.audio_file.write_bytes(b'fake-wav')
        self.service = DistillationService(
            repository=self.repository,
            text_adapter=TextAdapter(),
            audio_adapter=AudioAdapter(transcriber=_FakeTranscriber()),
            image_adapter=_UnsupportedAdapter(),
            tabular_adapter=_UnsupportedAdapter(),
            video_adapter=_UnsupportedAdapter(),
            insight_extractor=HeuristicInsightExtractor(),
            skill_composer=HeuristicSkillComposer(),
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.workspace, ignore_errors=True)

    def test_load_corpus_assembles_multi_asset_corpus(self) -> None:
        request = CorpusDistillRequest.from_dict(
            {
                'name': 'incident corpus',
                'goal': {'domain': 'incident_response'},
                'assets': [
                    {'source_uri': str(self.text_file), 'modality': 'text', 'role': 'primary'},
                    {'source_uri': str(self.audio_file), 'modality': 'audio', 'role': 'context'},
                ],
                'tags': ['incident', 'corpus'],
            }
        )
        loaded = self.service.load_corpus(request)
        self.assertEqual(loaded.corpus.name, 'incident corpus')
        self.assertEqual(len(loaded.corpus.assets), 2)
        self.assertEqual(loaded.corpus.metadata['asset_count'], 2)
        self.assertEqual(len(loaded.evidence_nodes), len(loaded.evidence_units))
        modalities = {item.modality for item in loaded.corpus.assets}
        self.assertEqual(modalities, {Modality.TEXT, Modality.AUDIO})
        content_types = {item.content_type for item in loaded.evidence_units}
        self.assertIn(ContentType.TEXT, content_types)
        self.assertIn(ContentType.SPEECH, content_types)
        node_modalities = {item.modality for item in loaded.evidence_nodes}
        self.assertEqual(node_modalities, {Modality.TEXT, Modality.AUDIO})

    def test_distill_corpus_keeps_single_asset_paths_compatible(self) -> None:
        corpus_request = CorpusDistillRequest(
            name='cross asset incident skill',
            assets=[
                CorpusAssetInput(source_uri=str(self.text_file), modality=Modality.TEXT, role='primary'),
                CorpusAssetInput(source_uri=str(self.audio_file), modality=Modality.AUDIO, role='context'),
            ],
            goal=DistillGoal.from_dict({'domain': 'incident_response'}),
            tags=['cross_asset'],
        )
        bundle = self.service.distill_corpus(corpus_request)
        self.assertTrue(bundle.adapter_metadata['cross_asset'])
        self.assertEqual(bundle.adapter_metadata['asset_count'], 2)
        self.assertEqual(bundle.adapter_metadata['evidence_node_count'], len(bundle.evidence_nodes))
        self.assertTrue(bundle.skill.steps)
        self.assertIsNotNone(bundle.corpus)
        self.assertIn('corpus', bundle.artifacts)
        self.assertIn('corpus_assets', bundle.artifacts)
        self.assertIn('evidence_nodes', bundle.artifacts)
        self.assertIn('cross_asset_refs', bundle.artifacts)
        self.assertIn('publication_manifest', bundle.artifacts)
        self.assertIn('publication_skill_markdown', bundle.artifacts)
        self.assertIn('publication_skill_json', bundle.artifacts)
        self.assertIn('quality_score', bundle.artifacts)
        self.assertIn('review_policy', bundle.artifacts)
        self.assertIn('review_task', bundle.artifacts)
        self.assertIn('review_feedback', bundle.artifacts)

        corpus_payload = json.loads(Path(bundle.artifacts['corpus']).read_text(encoding='utf-8'))
        self.assertEqual(corpus_payload['metadata']['asset_count'], 2)
        corpus_assets_payload = json.loads(Path(bundle.artifacts['corpus_assets']).read_text(encoding='utf-8'))
        self.assertEqual(len(corpus_assets_payload), 2)
        evidence_nodes_payload = json.loads(Path(bundle.artifacts['evidence_nodes']).read_text(encoding='utf-8'))
        self.assertEqual(len(evidence_nodes_payload), len(bundle.evidence_nodes))
        cross_asset_payload = json.loads(Path(bundle.artifacts['cross_asset_refs']).read_text(encoding='utf-8'))
        self.assertTrue(cross_asset_payload)
        self.assertTrue(any(len(item['asset_ids']) == 2 for item in cross_asset_payload))
        self.assertTrue(any(item['reference_type'] == 'skill' for item in cross_asset_payload))
        publication_manifest = json.loads(Path(bundle.artifacts['publication_manifest']).read_text(encoding='utf-8'))
        publication_types = {item['publication_type'] for item in publication_manifest}
        self.assertIn('skill_markdown', publication_types)
        self.assertIn('skill_json', publication_types)
        self.assertTrue(any(item.get('evidence_refs') for item in publication_manifest))
        self.assertTrue(all('graph_id' in item.get('metadata', {}) for item in publication_manifest))
        legacy_markdown = Path(bundle.artifacts['skill_markdown']).read_text(encoding='utf-8')
        publication_markdown = Path(bundle.artifacts['publication_skill_markdown']).read_text(encoding='utf-8')
        self.assertEqual(bundle.skill_markdown, legacy_markdown)
        self.assertEqual(bundle.skill_markdown, publication_markdown)
        references_dir = Path(bundle.artifacts['publication_skill_markdown']).parent / 'references'
        self.assertTrue((references_dir / 'evidence.md').exists())
        self.assertTrue((references_dir / 'examples.md').exists())
        quality_payload = json.loads(Path(bundle.artifacts['quality_score']).read_text(encoding='utf-8'))
        for key in (
            'traceability_score',
            'actionability_score',
            'coverage_score',
            'consistency_score',
            'noise_score',
            'novelty_score',
        ):
            self.assertIn(key, quality_payload)
            self.assertIn(key, bundle.adapter_metadata['quality_scores'])
        review_policy_payload = json.loads(Path(bundle.artifacts['review_policy']).read_text(encoding='utf-8'))
        self.assertIn(review_policy_payload['decision'], {'auto_publish', 'review_required', 'reject'})
        self.assertTrue(review_policy_payload['reason_codes'])
        self.assertIn('thresholds', review_policy_payload)
        self.assertIn('score_snapshot', review_policy_payload)
        self.assertEqual(bundle.adapter_metadata['review_policy']['decision'], review_policy_payload['decision'])
        review_task_payload = json.loads(Path(bundle.artifacts['review_task']).read_text(encoding='utf-8'))
        self.assertEqual(review_task_payload['decision'], review_policy_payload['decision'])
        self.assertEqual(review_task_payload['reason_codes'], review_policy_payload['reason_codes'])
        self.assertTrue(review_task_payload['revision_suggestions'])
        self.assertIn(review_task_payload['status'], {'review_pending', 'published', 'rejected'})
        review_feedback_payload = json.loads(Path(bundle.artifacts['review_feedback']).read_text(encoding='utf-8'))
        self.assertEqual(review_feedback_payload['decision'], review_task_payload['decision'])
        self.assertEqual(review_feedback_payload['reason_codes'], review_task_payload['reason_codes'])
        self.assertTrue(review_feedback_payload['categories'])
        self.assertTrue(
            review_feedback_payload['atom_actions']
            or review_feedback_payload['graph_actions']
            or review_feedback_payload['policy_actions']
        )
        self.assertTrue(review_feedback_payload['follow_up_checks'])
        self.assertEqual(bundle.adapter_metadata['review_feedback']['decision'], review_feedback_payload['decision'])

        single_bundle = self.service.distill_text(
            TextDistillRequest(
                file_path=str(self.text_file),
                title='single text skill',
                goal=DistillGoal.from_dict({'domain': 'incident_response'}),
            )
        )
        self.assertEqual(single_bundle.asset.modality, Modality.TEXT)
        self.assertTrue(single_bundle.skill.steps)
        self.assertNotIn('corpus', single_bundle.artifacts)
        self.assertNotIn('cross_asset_refs', single_bundle.artifacts)
        self.assertIn('publication_manifest', single_bundle.artifacts)
        single_publication_manifest = json.loads(Path(single_bundle.artifacts['publication_manifest']).read_text(encoding='utf-8'))
        self.assertGreaterEqual(len(single_publication_manifest), 2)
        self.assertEqual(
            single_bundle.skill_markdown,
            Path(single_bundle.artifacts['publication_skill_markdown']).read_text(encoding='utf-8'),
        )
        self.assertIn('quality_score', single_bundle.artifacts)
        single_quality_payload = json.loads(Path(single_bundle.artifacts['quality_score']).read_text(encoding='utf-8'))
        self.assertIn('overall_score', single_quality_payload)
        self.assertIn('review_policy', single_bundle.artifacts)
        single_review_policy = json.loads(Path(single_bundle.artifacts['review_policy']).read_text(encoding='utf-8'))
        self.assertIn(single_review_policy['decision'], {'auto_publish', 'review_required', 'reject'})
        self.assertIn('review_task', single_bundle.artifacts)
        single_review_task = json.loads(Path(single_bundle.artifacts['review_task']).read_text(encoding='utf-8'))
        self.assertEqual(single_review_task['decision'], single_review_policy['decision'])
        self.assertTrue(single_review_task['revision_suggestions'])
        self.assertIn('review_feedback', single_bundle.artifacts)
        single_review_feedback = json.loads(Path(single_bundle.artifacts['review_feedback']).read_text(encoding='utf-8'))
        self.assertEqual(single_review_feedback['decision'], single_review_task['decision'])
        self.assertTrue(single_review_feedback['follow_up_checks'])


if __name__ == '__main__':
    unittest.main()
