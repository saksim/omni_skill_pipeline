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
from omni_skill_pipeline.persistence import DualWriteArtifactRepository
from omni_skill_pipeline.repository import FileArtifactRepository


class _SecondaryStubRepository(object):
    def __init__(self, *, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.call_count = 0
        self.saved_skill_ids: list[str] = []

    def save_bundle(self, bundle: DistillBundle) -> dict[str, str]:
        self.call_count += 1
        self.saved_skill_ids.append(bundle.skill.skill_id)
        if self.should_fail:
            raise RuntimeError('secondary write failed')
        return {
            'skill': 'postgres://skills/%s' % bundle.skill.skill_id,
            'skill_version': 'postgres://skill_versions/%s/%s' % (bundle.skill.skill_id, bundle.skill.version),
        }


def _build_bundle() -> DistillBundle:
    asset = Asset(modality=Modality.TEXT, source_uri='memory://dual-write-repo')
    evidence = EvidenceUnit(
        asset_id=asset.asset_id,
        span_ref='text:line:1',
        content_type=ContentType.TEXT,
        content='Dual-write should preserve file artifacts even when secondary fails.',
    )
    insight = Insight(
        insight_type=InsightType.PROCEDURE,
        summary='Persist artifacts to primary then mirror to secondary.',
        evidence_refs=[evidence.evidence_id],
    )
    skill = SkillDocument(
        name='Dual Write Skill',
        goal='Verify dual-write repository behavior.',
        source_modality=Modality.TEXT,
        steps=[SkillStep(step=1, action='Write to primary repository first.', why='preserve baseline behavior')],
        evidence_refs=[evidence.evidence_id],
    )
    return DistillBundle(
        asset=asset,
        evidence_units=[evidence],
        insights=[insight],
        skill=skill,
        skill_markdown='# Dual Write Skill\n\n- Write to primary repository first.\n',
    )


class DualWriteRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace = REPO_ROOT / 'tests' / '.tmp_runtime' / ('dual_write_repo_%s' % uuid4().hex)
        self.workspace.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.workspace, ignore_errors=True)

    def test_dual_write_repository_is_artifact_repository_protocol_compatible(self) -> None:
        primary = FileArtifactRepository(self.workspace / 'drafts')
        secondary = _SecondaryStubRepository()
        repository = DualWriteArtifactRepository(primary=primary, secondary=secondary)
        self.assertIsInstance(repository, ArtifactRepository)

    def test_dual_write_success_adds_prefixed_secondary_artifacts(self) -> None:
        primary = FileArtifactRepository(self.workspace / 'drafts')
        secondary = _SecondaryStubRepository()
        repository = DualWriteArtifactRepository(primary=primary, secondary=secondary)
        bundle = _build_bundle()

        artifacts = repository.save_bundle(bundle)

        self.assertEqual(secondary.call_count, 1)
        self.assertIn('skill', artifacts)
        self.assertIn('bundle', artifacts)
        self.assertIn('secondary_skill', artifacts)
        self.assertIn('secondary_skill_version', artifacts)
        self.assertTrue(Path(artifacts['bundle']).exists())
        self.assertEqual(bundle.artifacts, artifacts)

    def test_dual_write_secondary_failure_does_not_break_primary_file_artifacts(self) -> None:
        primary = FileArtifactRepository(self.workspace / 'drafts')
        secondary = _SecondaryStubRepository(should_fail=True)
        repository = DualWriteArtifactRepository(primary=primary, secondary=secondary)
        bundle = _build_bundle()

        artifacts = repository.save_bundle(bundle)

        self.assertEqual(secondary.call_count, 1)
        self.assertIn('skill', artifacts)
        self.assertIn('bundle', artifacts)
        self.assertIn('secondary_error', artifacts)
        self.assertTrue(Path(artifacts['skill']).exists())
        self.assertTrue(Path(artifacts['bundle']).exists())
        self.assertNotIn('secondary_skill', artifacts)

    def test_dual_write_can_raise_when_secondary_failure_is_not_allowed(self) -> None:
        primary = FileArtifactRepository(self.workspace / 'drafts')
        secondary = _SecondaryStubRepository(should_fail=True)
        repository = DualWriteArtifactRepository(
            primary=primary,
            secondary=secondary,
            continue_on_secondary_error=False,
        )
        bundle = _build_bundle()

        with self.assertRaises(RuntimeError):
            repository.save_bundle(bundle)
        self.assertEqual(secondary.call_count, 1)


if __name__ == '__main__':
    unittest.main()
