from __future__ import annotations

import json
import os
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
    Publication,
    PublicationType,
    ReviewDecision,
    ReviewTask,
    SkillDocument,
    SkillStep,
)
from omni_skill_pipeline.persistence import PostgresRepository


def _build_bundle(*, include_lineage: bool = False) -> DistillBundle:
    asset = Asset(modality=Modality.TEXT, source_uri='memory://postgres-integration')
    evidence = EvidenceUnit(
        asset_id=asset.asset_id,
        span_ref='text:line:1',
        content_type=ContentType.TEXT,
        content='Persist this bundle into PostgreSQL for integration verification.',
    )
    insight = Insight(
        insight_type=InsightType.PROCEDURE,
        summary='Insert skill/review/publication rows into postgres.',
        evidence_refs=[evidence.evidence_id],
    )
    skill = SkillDocument(
        name='Postgres Integration Skill',
        goal='Verify postgres repository integration write path.',
        source_modality=Modality.TEXT,
        steps=[SkillStep(step=1, action='Save bundle into Postgres tables.', why='integration test')],
        evidence_refs=[evidence.evidence_id],
    )
    review_task = ReviewTask(
        skill_id=skill.skill_id,
        decision=ReviewDecision.REVIEW_REQUIRED,
        reason_codes=['Q_MANUAL_REVIEW_DEFAULT'],
        revision_suggestions=['S_MANUAL_REVIEW_REQUIRED'],
    )
    publications = [
        Publication(
            publication_type=PublicationType.SKILL_MARKDOWN,
            content={'text': '# Postgres Integration Skill\n\n- Save bundle into Postgres tables.\n'},
            path='SKILL.md',
        ),
        Publication(
            publication_type=PublicationType.SKILL_JSON,
            content={'name': skill.name, 'goal': skill.goal},
            path='skill.json',
        ),
    ]
    adapter_metadata = {}
    related_skill_id = str(uuid4())
    if include_lineage:
        adapter_metadata['lifecycle_decision'] = {
            'decision': 'supersede',
            'reason': 'Integration lineage verification.',
            'related_graph_ids': [related_skill_id],
            'confidence': 0.96,
            'metadata': {
                'source': 'integration-test',
            },
        }

    return DistillBundle(
        asset=asset,
        evidence_units=[evidence],
        insights=[insight],
        skill=skill,
        skill_markdown='# Postgres Integration Skill\n\n- Save bundle into Postgres tables.\n',
        review_task=review_task,
        publications=publications,
        adapter_metadata=adapter_metadata,
    )


class PostgresRepositoryIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dsn = os.getenv('OMNI_TEST_POSTGRES_DSN', '').strip()
        if not cls.dsn:
            raise unittest.SkipTest('OMNI_TEST_POSTGRES_DSN is not set; skip postgres integration tests.')
        try:
            import psycopg  # type: ignore
        except ImportError as exc:
            raise unittest.SkipTest('psycopg is not installed: %s' % exc) from exc

        cls.psycopg = psycopg
        cls.schema = 'omni_l2_32_%s' % uuid4().hex[:10]
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

    def _connect_with_schema(self, dsn: str):
        connection = self.psycopg.connect(dsn)
        with connection.cursor() as cursor:
            cursor.execute('SET search_path TO "%s"' % self.schema)
        return connection

    def test_save_bundle_persists_rows_into_postgres(self) -> None:
        repository = PostgresRepository(self.dsn, connect=self._connect_with_schema)
        bundle = _build_bundle()

        artifacts = repository.save_bundle(bundle)

        self.assertIn('skill', artifacts)
        self.assertIn('review_task', artifacts)
        self.assertIn('publication_manifest', artifacts)

        with self.psycopg.connect(self.dsn) as connection:
            with connection.cursor() as cursor:
                cursor.execute('SET search_path TO "%s"' % self.schema)
                cursor.execute(
                    'SELECT COUNT(*) FROM skills WHERE skill_id = %s::uuid',
                    (bundle.skill.skill_id,),
                )
                skill_count = int(cursor.fetchone()[0])
                cursor.execute(
                    'SELECT COUNT(*) FROM review_tasks WHERE review_task_id = %s::uuid',
                    (bundle.review_task.review_task_id,),
                )
                review_task_count = int(cursor.fetchone()[0])
                cursor.execute(
                    'SELECT COUNT(*) FROM publications WHERE skill_id = %s::uuid',
                    (bundle.skill.skill_id,),
                )
                publication_count = int(cursor.fetchone()[0])
                cursor.execute(
                    'SELECT skill_body FROM skill_versions WHERE skill_id = %s::uuid AND version = %s',
                    (bundle.skill.skill_id, bundle.skill.version),
                )
                skill_body_row = cursor.fetchone()

        self.assertEqual(skill_count, 1)
        self.assertEqual(review_task_count, 1)
        self.assertEqual(publication_count, len(bundle.publications))
        self.assertIsNotNone(skill_body_row)
        parsed_skill_body = skill_body_row[0]
        if isinstance(parsed_skill_body, str):
            parsed_skill_body = json.loads(parsed_skill_body)
        self.assertEqual(parsed_skill_body.get('skill_id'), bundle.skill.skill_id)

    def test_save_bundle_persists_lineage_links_into_postgres(self) -> None:
        repository = PostgresRepository(self.dsn, connect=self._connect_with_schema)
        bundle = _build_bundle(include_lineage=True)

        artifacts = repository.save_bundle(bundle)

        self.assertIn('lineage_manifest', artifacts)
        self.assertIn('lineage_supersede', artifacts)
        lifecycle_decision = bundle.adapter_metadata['lifecycle_decision']
        related_skill_id = lifecycle_decision['related_graph_ids'][0]

        with self.psycopg.connect(self.dsn) as connection:
            with connection.cursor() as cursor:
                cursor.execute('SET search_path TO "%s"' % self.schema)
                cursor.execute(
                    'SELECT COUNT(*) FROM lineage_links WHERE skill_id = %s::uuid AND related_skill_id = %s AND relation_type = %s',
                    (bundle.skill.skill_id, related_skill_id, 'supersede'),
                )
                lineage_count = int(cursor.fetchone()[0])
                cursor.execute(
                    'SELECT metadata FROM lineage_links WHERE skill_id = %s::uuid AND related_skill_id = %s AND relation_type = %s',
                    (bundle.skill.skill_id, related_skill_id, 'supersede'),
                )
                lineage_metadata_row = cursor.fetchone()

        self.assertEqual(lineage_count, 1)
        self.assertIsNotNone(lineage_metadata_row)
        lineage_metadata = lineage_metadata_row[0]
        if isinstance(lineage_metadata, str):
            lineage_metadata = json.loads(lineage_metadata)
        self.assertEqual(lineage_metadata.get('source'), 'integration-test')


if __name__ == '__main__':
    unittest.main()
