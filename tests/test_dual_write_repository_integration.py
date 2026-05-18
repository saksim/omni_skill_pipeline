from __future__ import annotations

import os
import shutil
import sys
import unittest
from pathlib import Path
from uuid import uuid4

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

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
from omni_skill_pipeline.persistence import DualWriteArtifactRepository, PostgresRepository
from omni_skill_pipeline.repository import FileArtifactRepository


def _build_bundle() -> DistillBundle:
    asset = Asset(modality=Modality.TEXT, source_uri='memory://dual-write-integration')
    evidence = EvidenceUnit(
        asset_id=asset.asset_id,
        span_ref='text:line:1',
        content_type=ContentType.TEXT,
        content='Integration-level dual-write should persist file and postgres targets.',
    )
    insight = Insight(
        insight_type=InsightType.PROCEDURE,
        summary='Mirror primary artifact writes into postgres.',
        evidence_refs=[evidence.evidence_id],
    )
    skill = SkillDocument(
        name='Dual Write Integration Skill',
        goal='Validate file + postgres dual-write persistence.',
        source_modality=Modality.TEXT,
        steps=[SkillStep(step=1, action='Save to file and postgres repositories.', why='LC-L2-33')],
        evidence_refs=[evidence.evidence_id],
    )
    return DistillBundle(
        asset=asset,
        evidence_units=[evidence],
        insights=[insight],
        skill=skill,
        skill_markdown='# Dual Write Integration Skill\n\n- Save to file and postgres repositories.\n',
    )


class DualWriteRepositoryIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dsn = os.getenv('OMNI_TEST_POSTGRES_DSN', '').strip()
        if not cls.dsn:
            raise unittest.SkipTest('OMNI_TEST_POSTGRES_DSN is not set; skip dual-write integration test.')
        try:
            import psycopg  # type: ignore
        except ImportError as exc:
            raise unittest.SkipTest('psycopg is not installed: %s' % exc) from exc

        cls.psycopg = psycopg
        cls.schema = 'omni_l2_33_%s' % uuid4().hex[:10]
        schema_sql = (REPO_ROOT / 'infra' / 'sql' / '001_init.sql').read_text(encoding='utf-8')

        with cls.psycopg.connect(cls.dsn, autocommit=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute('CREATE SCHEMA "%s"' % cls.schema)
                cursor.execute('SET search_path TO "%s"' % cls.schema)
                cls._run_ddl(cursor, schema_sql)

    @classmethod
    def tearDownClass(cls) -> None:
        if not getattr(cls, 'dsn', '') or not hasattr(cls, 'psycopg') or not getattr(cls, 'schema', ''):
            return
        with cls.psycopg.connect(cls.dsn, autocommit=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute('DROP SCHEMA IF EXISTS "%s" CASCADE' % cls.schema)

    @classmethod
    def _run_ddl(cls, cursor, sql_text: str) -> None:
        for statement in sql_text.split(';'):
            normalized = statement.strip()
            if not normalized:
                continue
            cursor.execute(normalized)

    def setUp(self) -> None:
        self.workspace = REPO_ROOT / 'tests' / '.tmp_runtime' / ('dual_write_pg_%s' % uuid4().hex)
        self.workspace.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.workspace, ignore_errors=True)

    def _connect_with_schema(self, dsn: str):
        connection = self.psycopg.connect(dsn)
        with connection.cursor() as cursor:
            cursor.execute('SET search_path TO "%s"' % self.schema)
        return connection

    def test_file_and_postgres_dual_write_persists_both_targets(self) -> None:
        bundle = _build_bundle()
        file_repository = FileArtifactRepository(self.workspace / 'drafts')
        postgres_repository = PostgresRepository(self.dsn, connect=self._connect_with_schema)
        dual_repository = DualWriteArtifactRepository(
            primary=file_repository,
            secondary=postgres_repository,
            continue_on_secondary_error=False,
        )

        artifacts = dual_repository.save_bundle(bundle)

        self.assertIn('skill', artifacts)
        self.assertIn('bundle', artifacts)
        self.assertIn('secondary_skill', artifacts)
        self.assertIn('secondary_skill_version', artifacts)
        self.assertTrue(Path(artifacts['skill']).exists())
        self.assertTrue(Path(artifacts['bundle']).exists())

        with self.psycopg.connect(self.dsn) as connection:
            with connection.cursor() as cursor:
                cursor.execute('SET search_path TO "%s"' % self.schema)
                cursor.execute(
                    'SELECT COUNT(*) FROM skills WHERE skill_id = %s::uuid',
                    (bundle.skill.skill_id,),
                )
                skill_count = int(cursor.fetchone()[0])
                cursor.execute(
                    'SELECT COUNT(*) FROM skill_versions WHERE skill_id = %s::uuid',
                    (bundle.skill.skill_id,),
                )
                version_count = int(cursor.fetchone()[0])

        self.assertEqual(skill_count, 1)
        self.assertEqual(version_count, 1)


if __name__ == '__main__':
    unittest.main()
