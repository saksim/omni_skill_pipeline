from __future__ import annotations

import shutil
import sys
import unittest
from pathlib import Path
from uuid import uuid4

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.interfaces import ArtifactRepository
from omni_skill_pipeline.models import (
    Asset,
    ContentType,
    DistillBundle,
    EvidenceUnit,
    Insight,
    InsightType,
    Modality,
    SkillDocument,
    SkillStep,
)
from omni_skill_pipeline.repository import FileArtifactRepository


def _build_minimal_bundle() -> DistillBundle:
    asset = Asset(modality=Modality.TEXT, source_uri='memory://contract-source')
    evidence = EvidenceUnit(
        asset_id=asset.asset_id,
        span_ref='text:line:1',
        content_type=ContentType.TEXT,
        content='Collect evidence and keep traceability.',
    )
    insight = Insight(
        insight_type=InsightType.PROCEDURE,
        summary='Process evidence into a reusable skill.',
        evidence_refs=[evidence.evidence_id],
    )
    skill = SkillDocument(
        name='Repository Contract Skill',
        goal='Validate artifact repository protocol contract.',
        source_modality=Modality.TEXT,
        steps=[SkillStep(step=1, action='Persist bundle artifacts.', why='Contract conformance smoke check.')],
        evidence_refs=[evidence.evidence_id],
        summary='Contract-level save_bundle smoke payload.',
    )
    return DistillBundle(
        asset=asset,
        evidence_units=[evidence],
        insights=[insight],
        skill=skill,
        skill_markdown='# Repository Contract Skill\n\n- Persist bundle artifacts.\n',
    )


class ArtifactRepositoryContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace = REPO_ROOT / 'tests' / '.tmp_runtime' / ('repository_contract_%s' % uuid4().hex)
        self.workspace.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.workspace, ignore_errors=True)

    def test_file_repository_declares_protocol_compatibility(self) -> None:
        repository = FileArtifactRepository(self.workspace / 'drafts')
        self.assertIsInstance(repository, ArtifactRepository)

    def test_save_bundle_protocol_contract_writes_required_artifacts(self) -> None:
        repository = FileArtifactRepository(self.workspace / 'drafts')
        bundle = _build_minimal_bundle()

        artifacts = repository.save_bundle(bundle)

        required_keys = {'asset', 'evidence', 'insights', 'skill', 'skill_markdown', 'bundle'}
        self.assertTrue(required_keys.issubset(set(artifacts.keys())))
        for key in required_keys:
            self.assertTrue(Path(artifacts[key]).exists(), msg='missing artifact for key=%s' % key)
        self.assertEqual(bundle.artifacts, artifacts)


if __name__ == '__main__':
    unittest.main()
