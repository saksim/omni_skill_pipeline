from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.interfaces import AtomExtractor
from omni_skill_pipeline.extraction.atom_extractor import LegacyInsightAtomExtractor
from omni_skill_pipeline.extraction.evidence_builder import EvidenceBuilder
from omni_skill_pipeline.models import (
    AgentSkillPackage,
    AgentSkillPackageFile,
    AgentSkillPackageReference,
    AgentSkillPackageSourceBundle,
    AgentSkillTarget,
    AgentSkillValidationStatus,
    Asset,
    AtomType,
    Corpus,
    CorpusAssetRef,
    CorpusDistillRequest,
    ContentType,
    DecisionNode,
    DistillGoal,
    EvidenceUnit,
    EvidenceNode,
    GraphEdgeType,
    Insight,
    InsightType,
    LoadedAsset,
    Modality,
    ReviewStatus,
    ReviewDecision,
    ReviewTask,
    SemanticAtom,
    SpatialRef,
    StructuralRef,
    SkillLineageLink,
    SkillGraph,
    SkillGraphEdge,
    StepNode,
    TimeRangeRef,
    VerificationNode,
)
from omni_skill_pipeline.render import render_skill_graph_markdown
from omni_skill_pipeline.transformers import evidence_unit_to_node, skill_graph_to_document


class _DummyAtomExtractor(object):
    def extract(self, evidence_nodes):
        return [
            SemanticAtom(
                atom_type=AtomType.CLAIM,
                summary='sample',
                evidence_refs=[item.evidence_id for item in evidence_nodes],
            )
        ]


class _DummyInsightExtractor(object):
    def extract(self, evidence_units):
        refs = [item.evidence_id for item in evidence_units]
        return [
            Insight(
                insight_type=InsightType.PROCEDURE,
                summary='Normalize source evidence.',
                evidence_refs=refs,
            ),
            Insight(
                insight_type=InsightType.VERIFICATION,
                summary='Confirm normalized output can be traced.',
                evidence_refs=refs,
            ),
        ]


class V2ModelTests(unittest.TestCase):
    def test_evidence_node_serialization_keeps_structured_fields(self) -> None:
        node = EvidenceNode(
            asset_id='asset-1',
            modality=Modality.VIDEO,
            content_type=ContentType.OCR,
            span_ref='frame:0003',
            text_content='Service degraded',
            payload={'bbox': [1, 2, 3, 4]},
            time_range=TimeRangeRef(start_ms=1300, end_ms=1600),
            spatial_ref=SpatialRef(x=0.1, y=0.2, w=0.3, h=0.4, page=1),
            structural_ref=StructuralRef(section='incident.timeline', line_start=4, line_end=5),
            parents=['parent-1'],
            derived_from=['frame-raw'],
        )
        payload = node.to_dict()
        self.assertEqual(payload['modality'], Modality.VIDEO.value)
        self.assertEqual(payload['content_type'], ContentType.OCR.value)
        self.assertEqual(payload['payload']['bbox'], [1, 2, 3, 4])
        self.assertEqual(payload['time_range']['start_ms'], 1300)
        self.assertEqual(payload['spatial_ref']['w'], 0.3)
        self.assertEqual(payload['structural_ref']['section'], 'incident.timeline')
        self.assertEqual(payload['parents'], ['parent-1'])
        self.assertEqual(payload['derived_from'], ['frame-raw'])

    def test_evidence_unit_to_node_transforms_legacy_fields(self) -> None:
        unit = EvidenceUnit(
            asset_id='asset-2',
            span_ref='timestamp:1.0-2.0',
            content_type=ContentType.SPEECH,
            content='Investigate latency spike',
            speaker='oncall',
            confidence=0.83,
            tags=['speech'],
            evidence_id='ev-1',
        )
        node = evidence_unit_to_node(unit)
        self.assertEqual(node.modality, Modality.AUDIO)
        self.assertEqual(node.text_content, 'Investigate latency spike')
        self.assertEqual(node.payload['legacy_content'], 'Investigate latency spike')
        self.assertEqual(node.speaker, 'oncall')
        self.assertEqual(node.evidence_id, 'ev-1')

    def test_v2_core_models_are_json_serializable(self) -> None:
        goal = DistillGoal.from_dict({'goal_type': 'build_skill', 'audience': 'expert', 'domain': 'ops'})
        corpus = Corpus(
            name='incident corpus',
            goal=goal,
            assets=[
                CorpusAssetRef(
                    asset_id='asset-1',
                    modality=Modality.TEXT,
                    source_uri='file:///incident.md',
                )
            ],
        )
        atom = SemanticAtom(atom_type=AtomType.CLAIM, summary='Service health regressed.', evidence_refs=['ev-1'])
        graph = SkillGraph(
            name='Incident triage graph',
            goal='Convert evidence into triage actions.',
            source_modalities=[Modality.TEXT],
            steps=[StepNode(step=1, action='Build timeline.', evidence_refs=['ev-1'])],
            verifications=[VerificationNode(check='Validate timeline against logs.', evidence_refs=['ev-1'])],
            edges=[
                SkillGraphEdge(
                    edge_type=GraphEdgeType.VERIFIED_BY,
                    source_node_id='step-1',
                    target_node_id='verify-1',
                )
            ],
            atom_refs=[atom.atom_id],
            evidence_refs=['ev-1'],
        )
        payload = json.loads(graph.to_json())
        self.assertEqual(payload['steps'][0]['node_type'], 'step')
        self.assertEqual(payload['edges'][0]['edge_type'], 'verified_by')
        self.assertEqual(json.loads(corpus.to_json())['assets'][0]['source_uri'], 'file:///incident.md')
        self.assertEqual(json.loads(atom.to_json())['atom_type'], 'claim')

    def test_agent_skill_package_serialization_and_validation(self) -> None:
        package = AgentSkillPackage(
            package_name='postgres-slow-query-review',
            description='Review PostgreSQL slow query plans before changing indexes.',
            target=AgentSkillTarget.CODEX,
            files=[
                AgentSkillPackageFile(
                    relative_path='SKILL.md',
                    category='primary',
                    required=True,
                    media_type='text/markdown',
                    size_bytes=1024,
                    sha256='a' * 64,
                ),
                AgentSkillPackageFile(
                    relative_path='references/evidence.md',
                    category='reference',
                    required=False,
                    media_type='text/markdown',
                    size_bytes=2048,
                    sha256='b' * 64,
                ),
            ],
            references=[
                AgentSkillPackageReference(
                    reference_id='ref-incident-postmortem',
                    title='Incident Postmortem',
                    source_uri='file:///tmp/incident-postmortem.md',
                    reference_type='evidence',
                    evidence_refs=['ev-1', 'ev-2'],
                )
            ],
            validation_status=AgentSkillValidationStatus.PASSED,
            source_bundle=AgentSkillPackageSourceBundle(
                bundle_id='bundle-1',
                graph_id='graph-1',
                skill_id='skill-1',
                corpus_id='corpus-1',
                artifact_manifest_path='skills/drafts/postgres-slow-query-review/publication_manifest.json',
            ),
            review_status=ReviewStatus.REVIEW_PENDING,
            hashes={
                'package_sha256': 'c' * 64,
                'skill_markdown_sha256': 'd' * 64,
            },
            metadata={
                'target_layout': '.codex/skills/postgres-slow-query-review',
                'schema_version': 'agent_skill_package.v1',
            },
        )
        package.validate()
        payload = package.to_dict()
        self.assertEqual(payload['target'], AgentSkillTarget.CODEX.value)
        self.assertEqual(payload['validation_status'], AgentSkillValidationStatus.PASSED.value)
        self.assertEqual(payload['review_status'], ReviewStatus.REVIEW_PENDING.value)
        self.assertEqual(payload['files'][0]['relative_path'], 'SKILL.md')
        self.assertEqual(payload['references'][0]['source_uri'], 'file:///tmp/incident-postmortem.md')
        self.assertEqual(payload['source_bundle']['graph_id'], 'graph-1')
        self.assertEqual(payload['hashes']['package_sha256'], 'c' * 64)

    def test_agent_skill_package_validate_requires_source_bundle_identifier(self) -> None:
        package = AgentSkillPackage(
            package_name='invalid-package',
            description='Missing source bundle identifiers should fail.',
            target=AgentSkillTarget.PORTABLE,
            files=[AgentSkillPackageFile(relative_path='SKILL.md')],
            source_bundle=AgentSkillPackageSourceBundle(),
        )
        with self.assertRaises(ValueError):
            package.validate()

    def test_corpus_request_can_represent_multi_asset_distillation(self) -> None:
        request = CorpusDistillRequest.from_dict(
            {
                'name': 'incident corpus',
                'goal': {'domain': 'incident_response', 'audience': 'expert'},
                'assets': [
                    {'source_uri': 'D:/tmp/incident.md', 'modality': 'text', 'role': 'primary'},
                    {'source_uri': 'D:/tmp/incident.wav', 'modality': 'audio', 'role': 'context'},
                    {'source_uri': 'D:/tmp/dashboard.png', 'modality': 'image', 'role': 'evidence'},
                ],
                'tags': ['incident', 'multi_asset'],
                'metadata': {'ticket': 'INC-42'},
            }
        )
        request.validate()
        self.assertEqual(request.name, 'incident corpus')
        self.assertEqual(len(request.assets), 3)
        self.assertEqual(request.assets[0].modality, Modality.TEXT)
        self.assertEqual(request.assets[1].modality, Modality.AUDIO)
        self.assertEqual(request.assets[2].role, 'evidence')
        self.assertEqual(request.primary_asset_index(), 0)
        serialized = request.to_dict()
        self.assertEqual(serialized['assets'][1]['source_uri'], 'D:/tmp/incident.wav')
        self.assertEqual(serialized['metadata']['ticket'], 'INC-42')

    def test_corpus_request_requires_at_least_one_asset(self) -> None:
        request = CorpusDistillRequest(
            name='empty corpus',
            assets=[],
            goal=DistillGoal(),
        )
        with self.assertRaises(ValueError):
            request.validate()

    def test_review_task_from_policy_keeps_reason_codes_and_revision_suggestions(self) -> None:
        task = ReviewTask.from_review_policy(
            skill_id='skill-1',
            review_policy={
                'decision': ReviewDecision.REVIEW_REQUIRED.value,
                'reason_codes': ['Q_TRACEABILITY_LOW', 'Q_ACTIONABILITY_LOW'],
                'score_snapshot': {'traceability_score': 0.61, 'actionability_score': 0.58, 'overall_score': 0.69},
                'thresholds': {'auto_publish_min_traceability': 0.78, 'auto_publish_min_actionability': 0.72},
            },
            review_notes='Need stronger evidence links.',
        )
        payload = task.to_dict()
        self.assertEqual(payload['decision'], 'review_required')
        self.assertEqual(payload['status'], 'review_pending')
        self.assertEqual(payload['reason_codes'], ['Q_TRACEABILITY_LOW', 'Q_ACTIONABILITY_LOW'])
        self.assertIn('S_ADD_TRACEABLE_EVIDENCE', payload['revision_suggestions'])
        self.assertIn('S_REWRITE_ACTIONABLE_STEPS', payload['revision_suggestions'])
        self.assertEqual(payload['score_snapshot']['overall_score'], 0.69)
        self.assertEqual(payload['thresholds']['auto_publish_min_actionability'], 0.72)

    def test_review_task_controlled_trial_reason_code_maps_to_manual_review_suggestion(self) -> None:
        task = ReviewTask.from_review_policy(
            skill_id='skill-controlled-trial',
            review_policy={
                'decision': ReviewDecision.REVIEW_REQUIRED.value,
                'reason_codes': ['controlled_trial_requires_review'],
                'score_snapshot': {'overall_score': 0.91},
            },
        )
        payload = task.to_dict()
        self.assertEqual(payload['decision'], 'review_required')
        self.assertIn('controlled_trial_requires_review', payload['reason_codes'])
        self.assertIn('S_MANUAL_REVIEW_REQUIRED', payload['revision_suggestions'])

    def test_review_task_auto_publish_is_marked_published(self) -> None:
        task = ReviewTask.from_review_policy(
            skill_id='skill-2',
            review_policy={
                'decision': ReviewDecision.AUTO_PUBLISH.value,
                'reason_codes': ['A_MEETS_ALL_THRESHOLDS'],
            },
        )
        payload = task.to_dict()
        self.assertEqual(payload['status'], 'published')
        self.assertTrue(payload['revision_suggestions'])

    def test_review_task_reject_is_marked_rejected(self) -> None:
        task = ReviewTask.from_review_policy(
            skill_id='skill-3',
            review_policy={
                'decision': ReviewDecision.REJECT.value,
                'reason_codes': ['R_LOW_OVERALL'],
            },
        )
        payload = task.to_dict()
        self.assertEqual(payload['status'], 'rejected')
        self.assertIn('S_REBUILD_FROM_EVIDENCE', payload['revision_suggestions'])

    def test_skill_lineage_link_can_be_derived_from_lifecycle_decision(self) -> None:
        links = SkillLineageLink.from_lifecycle_decision(
            skill_id='skill-new',
            lifecycle_decision={
                'decision': 'supersede',
                'reason': 'Near-identical replacement approved.',
                'related_graph_ids': ['skill-old-1', 'skill-old-1', '', 'skill-old-2'],
                'confidence': 0.91,
                'metadata': {'source': 'unit-test'},
            },
        )

        self.assertEqual(len(links), 2)
        first_payload = links[0].to_dict()
        second_payload = links[1].to_dict()
        self.assertEqual(first_payload['skill_id'], 'skill-new')
        self.assertEqual(first_payload['related_skill_id'], 'skill-old-1')
        self.assertEqual(first_payload['relation_type'], 'supersede')
        self.assertEqual(first_payload['confidence'], 0.91)
        self.assertEqual(first_payload['metadata']['source'], 'unit-test')
        self.assertEqual(second_payload['related_skill_id'], 'skill-old-2')

    def test_evidence_builder_creates_video_frame_lineage(self) -> None:
        builder = EvidenceBuilder()
        loaded_asset = LoadedAsset(
            asset=Asset(modality=Modality.VIDEO, source_uri='file:///demo.mp4'),
            evidence_units=[
                EvidenceUnit(
                    asset_id='asset-video',
                    span_ref='frame:0001@1.00s:ocr',
                    content_type=ContentType.OCR,
                    content='Service degraded',
                    evidence_id='ev-ocr',
                ),
                EvidenceUnit(
                    asset_id='asset-video',
                    span_ref='frame:0001@1.00s:scene',
                    content_type=ContentType.SCENE,
                    content='Dashboard shows alert banner',
                    evidence_id='ev-scene',
                ),
                EvidenceUnit(
                    asset_id='asset-video',
                    span_ref='frame:0001@1.00s:event',
                    content_type=ContentType.EVENT,
                    content='Rollback button pressed',
                    evidence_id='ev-event',
                ),
                EvidenceUnit(
                    asset_id='asset-video',
                    span_ref='frame:0001@1.00s:subtitle:0001',
                    content_type=ContentType.SPEECH,
                    content='Decision confirmed.',
                    evidence_id='ev-subtitle',
                ),
            ],
            title_hint='demo video',
        )
        nodes = builder.build_from_loaded_asset(loaded_asset)
        frame_node = next(item for item in nodes if item.span_ref == 'frame:0001@1.00s')
        ocr_node = next(item for item in nodes if item.evidence_id == 'ev-ocr')
        scene_node = next(item for item in nodes if item.evidence_id == 'ev-scene')
        event_node = next(item for item in nodes if item.evidence_id == 'ev-event')
        subtitle_node = next(item for item in nodes if item.evidence_id == 'ev-subtitle')

        self.assertIn('lineage:frame_anchor', frame_node.tags)
        self.assertEqual(frame_node.time_range.start_ms, 1000)
        self.assertEqual(frame_node.time_range.end_ms, 1000)
        self.assertIn(ocr_node.evidence_id, frame_node.children)
        self.assertIn(scene_node.evidence_id, frame_node.children)
        self.assertIn(event_node.evidence_id, frame_node.children)
        self.assertIn(subtitle_node.evidence_id, frame_node.children)
        self.assertIn(frame_node.evidence_id, ocr_node.parents)
        self.assertIn(frame_node.evidence_id, scene_node.parents)
        self.assertIn(frame_node.evidence_id, event_node.parents)
        self.assertIn(frame_node.evidence_id, subtitle_node.parents)
        self.assertIn(frame_node.evidence_id, ocr_node.derived_from)
        self.assertIn(frame_node.evidence_id, scene_node.derived_from)
        self.assertIn(frame_node.evidence_id, event_node.derived_from)
        self.assertIn(frame_node.evidence_id, subtitle_node.derived_from)

    def test_evidence_builder_links_timeseries_event_to_metric(self) -> None:
        builder = EvidenceBuilder()
        loaded_asset = LoadedAsset(
            asset=Asset(modality=Modality.TABULAR, source_uri='file:///metric.csv'),
            evidence_units=[
                EvidenceUnit(
                    asset_id='asset-tabular',
                    span_ref='timeseries:overview:0001',
                    content_type=ContentType.METRIC,
                    content='overview',
                    evidence_id='ev-overview',
                ),
                EvidenceUnit(
                    asset_id='asset-tabular',
                    span_ref='timeseries:metric:0001',
                    content_type=ContentType.METRIC,
                    content='latency series',
                    evidence_id='ev-metric',
                ),
                EvidenceUnit(
                    asset_id='asset-tabular',
                    span_ref='timeseries:event:0001',
                    content_type=ContentType.EVENT,
                    content='anomaly at t=10',
                    evidence_id='ev-event',
                ),
            ],
            title_hint='demo table',
        )
        nodes = builder.build_from_loaded_asset(loaded_asset)
        metric_node = next(item for item in nodes if item.evidence_id == 'ev-metric')
        event_node = next(item for item in nodes if item.evidence_id == 'ev-event')

        self.assertIn(event_node.evidence_id, metric_node.children)
        self.assertIn(metric_node.evidence_id, event_node.parents)
        self.assertIn(metric_node.evidence_id, event_node.derived_from)

    def test_skill_graph_to_document_builds_skill_document(self) -> None:
        graph = SkillGraph(
            name='Incident triage graph',
            goal='Convert incident evidence into a repeatable triage skill.',
            source_modalities=[Modality.AUDIO, Modality.VIDEO],
            audience=DistillGoal().audience,
            domain='incident_response',
            trigger=['When production alerts spike.'],
            inputs=['Incident transcript'],
            preconditions=['Timeline is reconstructed first.'],
            steps=[
                StepNode(step=1, action='Rebuild timeline.', why='Anchor all hypotheses.', evidence_refs=['ev-1']),
                StepNode(step=2, action='Merge duplicate alerts.', why='Reduce noise.', evidence_refs=['ev-2']),
            ],
            decisions=[
                DecisionNode(condition='if alerts share one dependency', decision='merge alerts', evidence_refs=['ev-3'])
            ],
            verifications=[VerificationNode(check='Verify latency and error rate normalize.', evidence_refs=['ev-4'])],
            edges=[SkillGraphEdge(edge_type=GraphEdgeType.DEPENDS_ON, source_node_id='a', target_node_id='b')],
            evidence_refs=['ev-root'],
            confidence=0.88,
            summary='Triage flow for incident bursts.',
        )
        skill = skill_graph_to_document(graph)
        self.assertEqual(skill.name, 'Incident triage graph')
        self.assertEqual(skill.source_modality, Modality.AUDIO)
        self.assertEqual(len(skill.steps), 2)
        self.assertIn('if alerts share one dependency -> merge alerts', skill.decision_rules)
        self.assertIn('Verify latency and error rate normalize.', skill.verification)
        self.assertIn('ev-root', skill.evidence_refs)
        self.assertIn('incident_response', skill.tags)
        self.assertEqual(skill.skill_id, graph.graph_id)
        markdown = render_skill_graph_markdown(graph)
        self.assertIn('# Incident triage graph', markdown)
        self.assertIn('## 操作步骤', markdown)

    def test_atom_extractor_protocol_runtime_check(self) -> None:
        extractor = _DummyAtomExtractor()
        self.assertTrue(isinstance(extractor, AtomExtractor))

    def test_legacy_insight_atom_extractor_is_atom_extractor_compatible(self) -> None:
        bridge = LegacyInsightAtomExtractor(insight_extractor=_DummyInsightExtractor())
        self.assertTrue(isinstance(bridge, AtomExtractor))
        evidence_nodes = [
            EvidenceNode(
                asset_id='asset-1',
                modality=Modality.TEXT,
                content_type=ContentType.TEXT,
                span_ref='line:1',
                text_content='Normalize source evidence and verify output.',
                evidence_id='ev-bridge',
            )
        ]
        atoms = bridge.extract(evidence_nodes)
        atom_types = {item.atom_type for item in atoms}
        self.assertIn(AtomType.PROCEDURE, atom_types)
        self.assertIn(AtomType.VERIFICATION, atom_types)
        self.assertEqual(atoms[0].attributes['legacy_insight_type'], InsightType.PROCEDURE.value)


if __name__ == '__main__':
    unittest.main()
