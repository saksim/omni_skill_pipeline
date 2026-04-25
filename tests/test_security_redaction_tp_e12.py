from __future__ import annotations

import json
import shutil
import sys
import unittest
from pathlib import Path
from uuid import uuid4

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.adapters.text import TextAdapter
from omni_skill_pipeline.models import (
    Asset,
    ContentType,
    Corpus,
    CorpusAssetInput,
    CorpusAssetRef,
    CorpusDistillRequest,
    DistillBundle,
    DistillGoal,
    EvidenceUnit,
    Insight,
    InsightType,
    Modality,
    SkillDocument,
    SkillStep,
)
from omni_skill_pipeline.pipeline import HeuristicInsightExtractor, HeuristicSkillComposer
from omni_skill_pipeline.repository import FileArtifactRepository
from omni_skill_pipeline.service import DistillationService


class _UnsupportedAdapter(object):
    def load(self, request):  # pragma: no cover - guard path
        raise AssertionError('Unexpected adapter invocation in security redaction tests.')


class SecurityRedactionTpE12Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace = REPO_ROOT / 'tests' / '.tmp_runtime' / uuid4().hex
        self.workspace.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.workspace, ignore_errors=True)

    def test_service_redacts_sensitive_fields_in_request_payload(self) -> None:
        text_file = self.workspace / 'incident.md'
        text_file.write_text(
            '\n'.join(
                [
                    '# Incident Notes',
                    'Capture timeline and verify rollback strategy.',
                ]
            ),
            encoding='utf-8',
        )

        service = DistillationService(
            repository=FileArtifactRepository(self.workspace / 'drafts-service'),
            text_adapter=TextAdapter(),
            audio_adapter=_UnsupportedAdapter(),
            image_adapter=_UnsupportedAdapter(),
            tabular_adapter=_UnsupportedAdapter(),
            video_adapter=_UnsupportedAdapter(),
            insight_extractor=HeuristicInsightExtractor(),
            skill_composer=HeuristicSkillComposer(),
        )
        request = CorpusDistillRequest(
            name='security-redaction-corpus',
            assets=[
                CorpusAssetInput(
                    source_uri=str(text_file),
                    modality=Modality.TEXT,
                    role='primary',
                    metadata={
                        'api_key': 'sk-live-service-sensitive',
                        'note': 'keep-observable',
                    },
                ),
            ],
            goal=DistillGoal.from_dict({'domain': 'incident_response'}),
            metadata={
                'credential': 'postgres://admin:plainpass@localhost/db',
                'authorization': 'Bearer top-secret-token',
                'token_usage': 7,
            },
        )

        bundle = service.distill_corpus(request)

        self.assertEqual(bundle.request_payload['assets'][0]['metadata']['api_key'], '[REDACTED]')
        self.assertEqual(bundle.request_payload['metadata']['credential'], '[REDACTED]')
        self.assertEqual(bundle.request_payload['metadata']['authorization'], '[REDACTED]')
        self.assertEqual(bundle.request_payload['metadata']['token_usage'], 7)
        self.assertEqual(bundle.request_payload['assets'][0]['metadata']['note'], 'keep-observable')

    def test_file_repository_redacts_sensitive_strings_before_persisting_artifacts(self) -> None:
        repository = FileArtifactRepository(self.workspace / 'drafts-repository')

        sensitive_source_uri = 'https://alice:plainpass@example.com/incident.md?token=inline-secret&mode=raw'
        asset = Asset(modality=Modality.TEXT, source_uri=sensitive_source_uri, metadata={'credential': 'rawCredential'})
        evidence = EvidenceUnit(
            asset_id=asset.asset_id,
            span_ref='text:line:1',
            content_type=ContentType.TEXT,
            content='Authorization: Bearer top-secret-token',
        )
        insight = Insight(
            insight_type=InsightType.PROCEDURE,
            summary='Rotate credentials and validate cleanup.',
            evidence_refs=[evidence.evidence_id],
        )
        skill = SkillDocument(
            name='Security Redaction Skill',
            goal='Verify redaction in persisted artifacts.',
            source_modality=Modality.TEXT,
            steps=[SkillStep(step=1, action='Persist sanitized artifacts.', why='TP-E12-03 contract')],
            evidence_refs=[evidence.evidence_id],
        )
        corpus = Corpus(
            name='sensitive-corpus',
            goal=DistillGoal.from_dict({'domain': 'security'}),
            assets=[
                CorpusAssetRef(
                    asset_id=asset.asset_id,
                    modality=Modality.TEXT,
                    source_uri='https://bob:p4ss@example.com/corpus.md?credential=db-pass&mode=full',
                    role='primary',
                    metadata={'access_token': 'tok-corpus'},
                )
            ],
            metadata={'secret': 'corpus-secret'},
        )
        bundle = DistillBundle(
            asset=asset,
            evidence_units=[evidence],
            insights=[insight],
            skill=skill,
            skill_markdown='# Security Redaction Skill\n\nAuthorization: Bearer top-secret-token\n',
            corpus=corpus,
            request_payload={
                'api_key': 'sk-live-repository-sensitive',
                'authorization': 'Bearer top-secret-token',
                'source': 'https://svc:pwd@host.example/path?secret=svc-secret&trace=1',
                'token_usage': 5,
            },
            adapter_metadata={
                'provider_footprint': {
                    'asset_breakdown': [
                        {
                            'asset_id': asset.asset_id,
                            'source_uri': 'https://worker:pw@infra.example/logs?credential=runtime-secret&view=raw',
                        }
                    ]
                },
                'secret': 'adapter-secret',
            },
        )

        artifacts = repository.save_bundle(bundle)

        asset_payload = json.loads(Path(artifacts['asset']).read_text(encoding='utf-8'))
        self.assertIn('[REDACTED]@example.com', asset_payload['source_uri'])
        self.assertIn('token=%5BREDACTED%5D', asset_payload['source_uri'])
        self.assertEqual(asset_payload['metadata']['credential'], '[REDACTED]')

        bundle_text = Path(artifacts['bundle']).read_text(encoding='utf-8')
        for leaked in (
            'plainpass',
            'inline-secret',
            'rawCredential',
            'top-secret-token',
            'sk-live-repository-sensitive',
            'svc-secret',
            'adapter-secret',
            'runtime-secret',
        ):
            self.assertNotIn(leaked, bundle_text)
        self.assertIn('[REDACTED]', bundle_text)

        bundle_payload = json.loads(bundle_text)
        self.assertEqual(bundle_payload['request_payload']['api_key'], '[REDACTED]')
        self.assertEqual(bundle_payload['request_payload']['authorization'], '[REDACTED]')
        self.assertEqual(bundle_payload['request_payload']['token_usage'], 5)

        skill_markdown = Path(artifacts['skill_markdown']).read_text(encoding='utf-8')
        self.assertIn('Bearer [REDACTED]', skill_markdown)
        self.assertNotIn('top-secret-token', skill_markdown)


if __name__ == '__main__':
    unittest.main()
