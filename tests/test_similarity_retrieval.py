from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.models import Modality, SkillDocument
from omni_skill_pipeline.retrieval import (
    BackendNotReadyError,
    InMemorySimilarityBackend,
    SimilarityQuery,
    SimilarityRetriever,
    SkillSearchDocument,
    build_similarity_backend,
)


class SimilarityRetrievalTests(unittest.TestCase):
    def test_inmemory_backend_returns_relevant_skill_first(self) -> None:
        backend = InMemorySimilarityBackend()
        backend.index(
            [
                SkillSearchDocument(
                    skill_id='skill-retry',
                    name='Handle API timeout with retry backoff',
                    summary='Set timeout, retry, and jitter strategy for external calls.',
                    domain='devops',
                    tags=('api', 'retry', 'timeout'),
                ),
                SkillSearchDocument(
                    skill_id='skill-logging',
                    name='Structured request logging',
                    summary='Attach request_id and trace_id to all logs.',
                    domain='devops',
                    tags=('logging', 'trace'),
                ),
            ]
        )

        results = backend.search(
            SimilarityQuery(
                text='api timeout retry strategy',
                top_k=2,
                domain='devops',
                tags=('retry',),
            )
        )

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].skill_id, 'skill-retry')
        self.assertGreater(results[0].score, results[1].score)
        self.assertEqual(results[0].backend, 'inmemory')

    def test_domain_and_tag_boost_breaks_lexical_tie(self) -> None:
        backend = InMemorySimilarityBackend(domain_bonus=0.2, tag_bonus=0.1)
        backend.index(
            [
                SkillSearchDocument(
                    skill_id='skill-release-devops',
                    name='Release checklist execution',
                    summary='Run pre-release checklist and rollback plan.',
                    domain='devops',
                    tags=('release', 'checklist'),
                ),
                SkillSearchDocument(
                    skill_id='skill-release-design',
                    name='Release checklist execution',
                    summary='Run pre-release checklist and rollback plan.',
                    domain='design',
                    tags=('release', 'checklist'),
                ),
            ]
        )

        results = backend.search(
            SimilarityQuery(
                text='release checklist',
                top_k=2,
                domain='devops',
                tags=('checklist',),
            )
        )

        self.assertEqual(results[0].skill_id, 'skill-release-devops')
        self.assertGreater(results[0].score, results[1].score)

    def test_retriever_indexes_skill_document_smoke(self) -> None:
        retriever = SimilarityRetriever()
        skill = SkillDocument(
            name='Investigate flaky CI test failures',
            goal='Debug transient CI pipeline issues.',
            source_modality=Modality.TEXT,
            summary='Capture failing tests and rerun with focused diagnostics.',
            tags=['ci', 'testing', 'flake'],
        )
        retriever.index_skill_documents([skill], domain='devops')

        results = retriever.search(
            text='ci flaky tests diagnostics',
            top_k=3,
            domain='devops',
            tags=('ci',),
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].skill_id, skill.skill_id)

    def test_backend_factory_exposes_pgvector_placeholder(self) -> None:
        backend = build_similarity_backend('pgvector', pgvector_dsn='postgresql://example')
        with self.assertRaises(BackendNotReadyError):
            backend.search(SimilarityQuery(text='retry policy', top_k=1))

    def test_query_validation_rejects_empty_search_hint(self) -> None:
        backend = InMemorySimilarityBackend()
        backend.index(
            [
                SkillSearchDocument(
                    skill_id='skill-any',
                    name='Any skill',
                    summary='Any summary',
                )
            ]
        )
        with self.assertRaises(ValueError):
            backend.search(SimilarityQuery(text='   ', top_k=1))

    def test_query_validation_rejects_whitespace_only_tags_without_text_and_domain(self) -> None:
        backend = InMemorySimilarityBackend()
        backend.index(
            [
                SkillSearchDocument(
                    skill_id='skill-any',
                    name='Any skill',
                    summary='Any summary',
                )
            ]
        )
        with self.assertRaises(ValueError):
            backend.search(SimilarityQuery(text='   ', top_k=1, tags=('   ',)))

    def test_inmemory_backend_uses_step_and_graph_overlap_when_lexical_base_ties(self) -> None:
        backend = InMemorySimilarityBackend(domain_bonus=0.0, tag_bonus=0.0, step_bonus=0.3, graph_bonus=0.2)
        backend.index(
            [
                SkillSearchDocument(
                    skill_id='skill-with-structure',
                    name='Release runbook',
                    summary='Operational checklist',
                    step_hints=('verify rollback readiness and canary metrics',),
                    graph_hints=('if gate fails then rollback immediately',),
                ),
                SkillSearchDocument(
                    skill_id='skill-plain',
                    name='Release runbook',
                    summary='Operational checklist',
                    step_hints=(),
                    graph_hints=(),
                ),
            ]
        )

        results = backend.search(SimilarityQuery(text='rollback gate verify metrics', top_k=2))

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].skill_id, 'skill-with-structure')
        self.assertGreater(results[0].score, results[1].score)
        self.assertGreater(results[0].metadata.get('step_score', 0.0), 0.0)
        self.assertGreater(results[0].metadata.get('graph_score', 0.0), 0.0)


if __name__ == '__main__':
    unittest.main()
