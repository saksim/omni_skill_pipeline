from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.models import DistillGoal
from omni_skill_pipeline.service import DistillationService


class _CapturingCorpusLoader(object):
    def __init__(self, result) -> None:
        self.result = result
        self.requests = []

    def load_corpus(self, request):
        self.requests.append(request)
        return self.result


class _CapturingPublicationOrchestrator(object):
    def __init__(self, result) -> None:
        self.result = result
        self.calls = []

    def build_publications(self, **kwargs):
        self.calls.append(kwargs)
        return self.result


def _build_service(*, corpus_loader, publication_orchestrator) -> DistillationService:
    return DistillationService(
        repository=Mock(),
        text_adapter=Mock(),
        audio_adapter=Mock(),
        image_adapter=Mock(),
        tabular_adapter=Mock(),
        video_adapter=Mock(),
        insight_extractor=Mock(),
        skill_composer=Mock(),
        evidence_builder=Mock(),
        atom_extractor=Mock(),
        skill_graph_builder=Mock(),
        publication_builder=Mock(),
        quality_scorer=Mock(),
        review_policy=Mock(),
        review_feedback_engine=Mock(),
        corpus_loader=corpus_loader,
        publication_orchestrator=publication_orchestrator,
    )


class ServiceSplitL228Tests(unittest.TestCase):
    def test_service_no_longer_owns_corpus_and_publication_helpers(self) -> None:
        self.assertFalse(hasattr(DistillationService, '_adapter_for_modality'))
        self.assertFalse(hasattr(DistillationService, '_build_corpus_asset_request'))
        self.assertFalse(hasattr(DistillationService, '_derive_corpus_name'))
        self.assertFalse(hasattr(DistillationService, '_resolve_source_uri'))
        self.assertFalse(hasattr(DistillationService, '_harmonize_publications'))

    def test_load_corpus_delegates_to_corpus_loader(self) -> None:
        expected = SimpleNamespace(corpus_id='loaded-corpus')
        corpus_loader = _CapturingCorpusLoader(result=expected)
        publication_orchestrator = _CapturingPublicationOrchestrator(result=('graph', []))
        service = _build_service(corpus_loader=corpus_loader, publication_orchestrator=publication_orchestrator)

        request = SimpleNamespace(name='corpus-request')
        result = service.load_corpus(request)

        self.assertIs(result, expected)
        self.assertEqual(corpus_loader.requests, [request])

    def test_build_publications_delegates_to_publication_orchestrator(self) -> None:
        expected_graph = SimpleNamespace(graph_id='graph-1')
        expected_publications = [SimpleNamespace(path='SKILL.md')]
        corpus_loader = _CapturingCorpusLoader(result=SimpleNamespace())
        publication_orchestrator = _CapturingPublicationOrchestrator(result=(expected_graph, expected_publications))
        service = _build_service(corpus_loader=corpus_loader, publication_orchestrator=publication_orchestrator)

        skill = SimpleNamespace(name='skill', skill_id='skill-1')
        evidence_nodes = [SimpleNamespace(node_id='n1')]
        goal = DistillGoal(domain='ops')
        result_graph, result_publications = service._build_publications(
            title_hint='incident skill',
            goal=goal,
            evidence_nodes=evidence_nodes,
            skill=skill,
        )

        self.assertIs(result_graph, expected_graph)
        self.assertIs(result_publications, expected_publications)
        self.assertEqual(len(publication_orchestrator.calls), 1)
        self.assertEqual(publication_orchestrator.calls[0]['title_hint'], 'incident skill')
        self.assertIs(publication_orchestrator.calls[0]['goal'], goal)
        self.assertIs(publication_orchestrator.calls[0]['skill'], skill)
        self.assertIs(publication_orchestrator.calls[0]['evidence_nodes'], evidence_nodes)


if __name__ == '__main__':
    unittest.main()
