from __future__ import annotations

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
    Publication,
    PublicationType,
    ReviewDecision,
    ReviewTask,
    SkillDocument,
    SkillStep,
)
from omni_skill_pipeline.persistence import PostgresRepository


class _FakeCursor(object):
    def __init__(self, connection: '_FakeConnection') -> None:
        self.connection = connection
        self.closed = False

    def execute(self, query: str, params=None) -> None:
        self.connection.executions.append((query, params))
        if self.connection.fail_on_query and self.connection.fail_on_query in query:
            raise RuntimeError('simulated postgres failure')

    def close(self) -> None:
        self.closed = True


class _FakeConnection(object):
    def __init__(self, *, fail_on_query: str | None = None) -> None:
        self.executions: list[tuple[str, tuple | None]] = []
        self.fail_on_query = fail_on_query
        self.commit_calls = 0
        self.rollback_calls = 0
        self.closed = False
        self.cursors: list[_FakeCursor] = []

    def cursor(self) -> _FakeCursor:
        cursor = _FakeCursor(self)
        self.cursors.append(cursor)
        return cursor

    def commit(self) -> None:
        self.commit_calls += 1

    def rollback(self) -> None:
        self.rollback_calls += 1

    def close(self) -> None:
        self.closed = True


def _build_bundle(
    *,
    include_review_task: bool = True,
    include_publications: bool = True,
    include_lineage: bool = False,
) -> DistillBundle:
    asset = Asset(modality=Modality.TEXT, source_uri='memory://postgres-repo-contract')
    evidence = EvidenceUnit(
        asset_id=asset.asset_id,
        span_ref='text:line:1',
        content_type=ContentType.TEXT,
        content='Persist repository state into PostgreSQL tables.',
    )
    insight = Insight(
        insight_type=InsightType.PROCEDURE,
        summary='Save skill + review + publications into relational storage.',
        evidence_refs=[evidence.evidence_id],
    )
    skill = SkillDocument(
        name='Postgres Repository Skill',
        goal='Validate PostgresRepository save contract.',
        source_modality=Modality.TEXT,
        steps=[SkillStep(step=1, action='Write skill rows into postgres.', why='LC-L2-32')],
        evidence_refs=[evidence.evidence_id],
    )
    review_task = (
        ReviewTask(
            skill_id=skill.skill_id,
            decision=ReviewDecision.REVIEW_REQUIRED,
            reason_codes=['Q_MANUAL_REVIEW_DEFAULT'],
            revision_suggestions=['S_MANUAL_REVIEW_REQUIRED'],
        )
        if include_review_task
        else None
    )

    publications: list[Publication] = []
    if include_publications:
        publications = [
            Publication(
                publication_type=PublicationType.SKILL_MARKDOWN,
                content={'text': '# Postgres Repository Skill\n\n- Write skill rows into postgres.\n'},
                path='SKILL.md',
            ),
            Publication(
                publication_type=PublicationType.SKILL_JSON,
                content={'name': skill.name, 'goal': skill.goal},
                path='skill.json',
            ),
        ]

    adapter_metadata = {}
    if include_lineage:
        adapter_metadata['lifecycle_decision'] = {
            'decision': 'supersede',
            'reason': 'High-quality near-identical output supersedes legacy skill.',
            'related_graph_ids': [str(uuid4())],
            'confidence': 0.97,
            'metadata': {
                'source': 'unit-test',
                'thresholds': {'supersede_min_similarity': 0.95},
            },
        }

    return DistillBundle(
        asset=asset,
        evidence_units=[evidence],
        insights=[insight],
        skill=skill,
        skill_markdown='# Postgres Repository Skill\n\n- Write skill rows into postgres.\n',
        review_task=review_task,
        publications=publications,
        adapter_metadata=adapter_metadata,
    )


class PostgresRepositoryTests(unittest.TestCase):
    def test_repository_declares_artifact_protocol_compatibility(self) -> None:
        connection = _FakeConnection()
        repository = PostgresRepository('postgresql://example', connect=lambda _: connection)
        self.assertIsInstance(repository, ArtifactRepository)

    def test_save_bundle_writes_skill_review_and_publication_rows(self) -> None:
        connection = _FakeConnection()
        repository = PostgresRepository('postgresql://example', connect=lambda _: connection)
        bundle = _build_bundle(include_review_task=True, include_publications=True)

        artifacts = repository.save_bundle(bundle)

        self.assertEqual(connection.commit_calls, 1)
        self.assertEqual(connection.rollback_calls, 0)
        self.assertTrue(connection.closed)
        self.assertTrue(all(cursor.closed for cursor in connection.cursors))

        sql_text = '\n'.join(query for query, _ in connection.executions)
        self.assertIn('INSERT INTO skills', sql_text)
        self.assertIn('INSERT INTO skill_versions', sql_text)
        self.assertIn('INSERT INTO review_tasks', sql_text)
        self.assertIn('INSERT INTO publications', sql_text)

        self.assertIn('skill', artifacts)
        self.assertIn('skill_version', artifacts)
        self.assertIn('review_task', artifacts)
        self.assertIn('publication_manifest', artifacts)
        self.assertEqual(bundle.artifacts, artifacts)

    def test_save_bundle_without_review_task_skips_review_task_insert(self) -> None:
        connection = _FakeConnection()
        repository = PostgresRepository('postgresql://example', connect=lambda _: connection)
        bundle = _build_bundle(include_review_task=False, include_publications=True)

        artifacts = repository.save_bundle(bundle)

        sql_text = '\n'.join(query for query, _ in connection.executions)
        self.assertIn('INSERT INTO skills', sql_text)
        self.assertIn('INSERT INTO skill_versions', sql_text)
        self.assertNotIn('INSERT INTO review_tasks', sql_text)
        self.assertIn('INSERT INTO publications', sql_text)
        self.assertNotIn('review_task', artifacts)

    def test_save_bundle_writes_lineage_links_for_supersede_decision(self) -> None:
        connection = _FakeConnection()
        repository = PostgresRepository('postgresql://example', connect=lambda _: connection)
        bundle = _build_bundle(include_review_task=True, include_publications=True, include_lineage=True)

        artifacts = repository.save_bundle(bundle)

        sql_text = '\n'.join(query for query, _ in connection.executions)
        self.assertIn('INSERT INTO lineage_links', sql_text)
        self.assertIn('lineage_manifest', artifacts)
        self.assertIn('lineage_supersede', artifacts)

        lineage_query = next(
            params
            for query, params in connection.executions
            if 'INSERT INTO lineage_links' in query
        )
        self.assertEqual(lineage_query[1], bundle.skill.skill_id)
        self.assertEqual(lineage_query[3], 'supersede')

    def test_save_bundle_rolls_back_on_database_failure(self) -> None:
        connection = _FakeConnection(fail_on_query='INSERT INTO skill_versions')
        repository = PostgresRepository('postgresql://example', connect=lambda _: connection)
        bundle = _build_bundle(include_review_task=True, include_publications=True)

        with self.assertRaises(RuntimeError):
            repository.save_bundle(bundle)

        self.assertEqual(connection.commit_calls, 0)
        self.assertEqual(connection.rollback_calls, 1)
        self.assertTrue(connection.closed)
        self.assertTrue(all(cursor.closed for cursor in connection.cursors))


if __name__ == '__main__':
    unittest.main()
