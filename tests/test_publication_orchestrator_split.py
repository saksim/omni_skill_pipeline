from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.models import (
    DistillGoal,
    Modality,
    Publication,
    PublicationType,
    SkillDocument,
    SkillGraph,
    SkillStep,
)
from omni_skill_pipeline.publication_orchestrator import PublicationHarmonizer, PublicationOrchestrator


class PublicationHarmonizerTests(unittest.TestCase):
    def test_harmonizer_adds_markdown_and_normalizes_skill_json(self) -> None:
        skill = SkillDocument(
            name='Incident Recovery',
            goal='Recover service safely.',
            source_modality=Modality.TEXT,
            steps=[SkillStep(step=1, action='Rollback bad release.', why='reduce blast radius')],
            evidence_refs=['ev-1'],
        )
        skill_graph = SkillGraph(
            graph_id='graph-1',
            name='Incident Recovery Graph',
            goal='Recover service safely.',
            source_modalities=[Modality.TEXT],
            evidence_refs=['ev-1'],
        )
        publications = [
            Publication(
                publication_type=PublicationType.SKILL_JSON,
                content={'raw': 'payload'},
                path='old.json',
            )
        ]

        result = PublicationHarmonizer().harmonize(publications, skill=skill, skill_graph=skill_graph)

        self.assertEqual(result[0].publication_type, PublicationType.SKILL_MARKDOWN)
        self.assertEqual(result[0].path, 'SKILL.md')
        self.assertEqual(result[0].content['graph_id'], 'graph-1')
        self.assertEqual(result[0].content['skill_id'], skill.skill_id)
        self.assertIn('Rollback bad release.', result[0].content['text'])

        self.assertEqual(result[1].publication_type, PublicationType.SKILL_JSON)
        self.assertEqual(result[1].path, 'skill.json')
        self.assertEqual(result[1].content['graph_id'], 'graph-1')
        self.assertEqual(result[1].content['skill_id'], skill.skill_id)
        self.assertEqual(result[1].metadata['renderer'], 'skill_json_v1_compat')
        self.assertEqual(result[1].metadata['evidence_refs'], ['ev-1'])


class PublicationOrchestratorTests(unittest.TestCase):
    def test_orchestrator_builds_graph_then_harmonizes(self) -> None:
        atom_extractor = Mock()
        atom_extractor.extract.return_value = ['atom-1']

        skill_graph = SkillGraph(
            graph_id='graph-2',
            name='Graph Name',
            goal='Goal',
            source_modalities=[Modality.TEXT],
        )
        skill_graph_builder = Mock()
        skill_graph_builder.build.return_value = skill_graph

        base_publications = [Publication(publication_type=PublicationType.SKILL_MARKDOWN, content={'text': 'x'})]
        publication_builder = Mock()
        publication_builder.build.return_value = base_publications

        harmonized_publications = [Publication(publication_type=PublicationType.SKILL_MARKDOWN, content={'text': 'ok'})]
        harmonizer = Mock()
        harmonizer.harmonize.return_value = harmonized_publications

        orchestrator = PublicationOrchestrator(
            atom_extractor=atom_extractor,
            skill_graph_builder=skill_graph_builder,
            publication_builder=publication_builder,
            harmonizer=harmonizer,
        )

        goal = DistillGoal(domain='ops')
        evidence_nodes = [object()]
        skill = SkillDocument(
            name='Skill Name',
            goal='Goal',
            source_modality=Modality.TEXT,
            steps=[SkillStep(step=1, action='Do thing')],
        )

        result_graph, result_publications = orchestrator.build_publications(
            title_hint='title-hint',
            goal=goal,
            evidence_nodes=evidence_nodes,
            skill=skill,
        )

        atom_extractor.extract.assert_called_once_with(evidence_nodes)
        skill_graph_builder.build.assert_called_once_with('Skill Name', goal, evidence_nodes, ['atom-1'])
        publication_builder.build.assert_called_once_with(
            skill_graph,
            publication_types=[PublicationType.SKILL_MARKDOWN, PublicationType.SKILL_JSON],
        )
        harmonizer.harmonize.assert_called_once_with(base_publications, skill=skill, skill_graph=skill_graph)
        self.assertIs(result_graph, skill_graph)
        self.assertIs(result_publications, harmonized_publications)

    def test_orchestrator_chooses_goal_specific_publication_types(self) -> None:
        matrix = [
            ('extract_checklist', PublicationType.CHECKLIST_JSON),
            ('extract_decision_tree', PublicationType.DECISION_TREE_JSON),
        ]
        for goal_type, expected_tail in matrix:
            with self.subTest(goal_type=goal_type):
                atom_extractor = Mock()
                atom_extractor.extract.return_value = ['atom-1']
                skill_graph = SkillGraph(
                    graph_id='graph-3',
                    name='Graph Name',
                    goal='Goal',
                    source_modalities=[Modality.TEXT],
                )
                skill_graph_builder = Mock()
                skill_graph_builder.build.return_value = skill_graph
                publication_builder = Mock()
                publication_builder.build.return_value = [
                    Publication(publication_type=PublicationType.SKILL_MARKDOWN, content={'text': 'x'})
                ]
                harmonizer = Mock()
                harmonizer.harmonize.return_value = []
                orchestrator = PublicationOrchestrator(
                    atom_extractor=atom_extractor,
                    skill_graph_builder=skill_graph_builder,
                    publication_builder=publication_builder,
                    harmonizer=harmonizer,
                )
                goal = DistillGoal.from_dict({'goal_type': goal_type, 'domain': 'ops'})
                skill = SkillDocument(
                    name='Skill Name',
                    goal='Goal',
                    source_modality=Modality.TEXT,
                    steps=[SkillStep(step=1, action='Do thing')],
                )
                orchestrator.build_publications(
                    title_hint='title-hint',
                    goal=goal,
                    evidence_nodes=[object()],
                    skill=skill,
                )
                publication_builder.build.assert_called_once_with(
                    skill_graph,
                    publication_types=[
                        PublicationType.SKILL_MARKDOWN,
                        PublicationType.SKILL_JSON,
                        expected_tail,
                    ],
                )


if __name__ == '__main__':
    unittest.main()
