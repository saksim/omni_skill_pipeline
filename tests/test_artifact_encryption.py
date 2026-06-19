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

from omni_skill_pipeline.artifact_crypto import (
    ENCRYPTION_SCHEMA_VERSION,
    ArtifactEncryptionError,
    ArtifactEncryptor,
    generate_fernet_key,
)
from omni_skill_pipeline.models import (
    Asset,
    ContentType,
    DistillBundle,
    EvidenceUnit,
    Insight,
    InsightType,
    Modality,
    ReviewDecision,
    ReviewStatus,
    ReviewTask,
    SkillDocument,
    SkillStep,
)
from omni_skill_pipeline.repository import FileArtifactRepository


def _build_bundle(*, review_required: bool = False) -> DistillBundle:
    asset = Asset(modality=Modality.TEXT, source_uri='memory://artifact-encryption-source')
    evidence = EvidenceUnit(
        asset_id=asset.asset_id,
        span_ref='text:line:1',
        content_type=ContentType.TEXT,
        content='Sensitive internal evidence should not remain readable at rest.',
    )
    insight = Insight(
        insight_type=InsightType.PROCEDURE,
        summary='Encrypt local artifacts before internal dogfood launch.',
        evidence_refs=[evidence.evidence_id],
    )
    skill = SkillDocument(
        name='Artifact Encryption Skill',
        goal='Validate encrypted file artifact persistence.',
        source_modality=Modality.TEXT,
        steps=[SkillStep(step=1, action='Persist encrypted artifacts.', why='Security launch gate.')],
        evidence_refs=[evidence.evidence_id],
    )
    review_task = None
    adapter_metadata = {}
    if review_required:
        review_task = ReviewTask(
            skill_id=skill.skill_id,
            decision=ReviewDecision.REVIEW_REQUIRED,
            status=ReviewStatus.REVIEW_PENDING,
            reason_codes=['SECURITY_REVIEW_REQUIRED'],
        )
        adapter_metadata['review_task'] = review_task.to_dict()
    return DistillBundle(
        asset=asset,
        evidence_units=[evidence],
        insights=[insight],
        skill=skill,
        skill_markdown='# Artifact Encryption Skill\n\n- Persist encrypted artifacts.\n',
        review_task=review_task,
        adapter_metadata=adapter_metadata,
    )


class ArtifactEncryptionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace = REPO_ROOT / 'tests' / '.tmp_runtime' / ('artifact_encryption_%s' % uuid4().hex)
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.key = generate_fernet_key()

    def tearDown(self) -> None:
        shutil.rmtree(self.workspace, ignore_errors=True)

    def test_file_repository_encrypts_artifacts_without_plaintext_leakage(self) -> None:
        repository = FileArtifactRepository(
            self.workspace / 'drafts',
            encryption_mode='fernet',
            encryption_key=self.key,
            encryption_key_id='local-test-key',
        )

        artifacts = repository.save_bundle(_build_bundle())

        raw_evidence = Path(artifacts['evidence']).read_text(encoding='utf-8')
        self.assertNotIn('Sensitive internal evidence', raw_evidence)
        envelope = json.loads(raw_evidence)
        self.assertEqual(envelope['schema_version'], ENCRYPTION_SCHEMA_VERSION)
        self.assertEqual(envelope['algorithm'], 'fernet')
        self.assertEqual(envelope['key_id'], 'local-test-key')

        plaintext = ArtifactEncryptor(self.key, key_id='local-test-key').decrypt_text(raw_evidence)
        self.assertIn('Sensitive internal evidence should not remain readable at rest.', plaintext)

    def test_encrypted_review_queue_stays_queryable_and_consumable_with_key(self) -> None:
        repository = FileArtifactRepository(
            self.workspace / 'drafts',
            encryption_mode='fernet',
            encryption_key=self.key,
        )
        bundle = _build_bundle(review_required=True)

        artifacts = repository.save_bundle(bundle)

        queue_raw = Path(artifacts['review_queue_item']).read_text(encoding='utf-8')
        self.assertNotIn(bundle.review_task.review_task_id, queue_raw)
        pending = repository.list_review_queue()
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]['review_task_id'], bundle.review_task.review_task_id)

        consumed = repository.consume_review_task(consumer='security-reviewer')
        self.assertIsNotNone(consumed)
        self.assertEqual(consumed['queue_status'], 'consumed')
        self.assertEqual(consumed['claimed_by'], 'security-reviewer')

    def test_encryption_mode_requires_valid_key(self) -> None:
        with self.assertRaises(ArtifactEncryptionError):
            FileArtifactRepository(
                self.workspace / 'drafts',
                encryption_mode='fernet',
                encryption_key='',
            )


if __name__ == '__main__':
    unittest.main()
