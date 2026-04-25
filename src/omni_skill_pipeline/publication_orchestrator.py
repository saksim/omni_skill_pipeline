from __future__ import annotations

from omni_skill_pipeline.assembly.publication_builder import PublicationBuilder
from omni_skill_pipeline.assembly.skill_graph_builder import SkillGraphBuilder
from omni_skill_pipeline.interfaces import AtomExtractor
from omni_skill_pipeline.models import DistillGoal, Publication, PublicationType, SkillDocument, SkillGraph
from omni_skill_pipeline.render import render_skill_markdown
from omni_skill_pipeline.utils import unique_preserve_order


class PublicationHarmonizer(object):
    def harmonize(
        self,
        publications: list[Publication],
        *,
        skill: SkillDocument,
        skill_graph: SkillGraph,
    ) -> list[Publication]:
        markdown_text = render_skill_markdown(skill)
        has_markdown_publication = False

        for publication in publications:
            publication.metadata = dict(publication.metadata)
            publication.metadata.setdefault('evidence_refs', unique_preserve_order(skill_graph.evidence_refs))
            if publication.publication_type == PublicationType.SKILL_MARKDOWN:
                has_markdown_publication = True
                publication.path = 'SKILL.md'
                publication.content = {
                    **dict(publication.content),
                    'filename': 'SKILL.md',
                    'text': str(dict(publication.content).get('text') or markdown_text),
                    'graph_id': skill_graph.graph_id,
                    'skill_id': skill.skill_id,
                }
                publication.metadata['renderer'] = 'skill_markdown_v1_compat'
            elif publication.publication_type == PublicationType.SKILL_JSON:
                publication.path = 'skill.json'
                publication.content = {
                    **dict(publication.content),
                    'filename': 'skill.json',
                    'skill': skill.to_dict(),
                    'graph_id': skill_graph.graph_id,
                    'skill_id': skill.skill_id,
                }
                publication.metadata['renderer'] = 'skill_json_v1_compat'

        if not has_markdown_publication:
            publications.insert(
                0,
                Publication(
                    publication_type=PublicationType.SKILL_MARKDOWN,
                    content={
                        'filename': 'SKILL.md',
                        'text': markdown_text,
                        'graph_id': skill_graph.graph_id,
                        'skill_id': skill.skill_id,
                    },
                    path='SKILL.md',
                    metadata={
                        'source': 'skill_graph',
                        'graph_id': skill_graph.graph_id,
                        'skill_id': skill.skill_id,
                        'version': skill_graph.version,
                        'renderer': 'skill_markdown_v1_compat',
                        'evidence_refs': unique_preserve_order(skill_graph.evidence_refs),
                    },
                ),
            )
        return publications


class PublicationOrchestrator(object):
    def __init__(
        self,
        *,
        atom_extractor: AtomExtractor,
        skill_graph_builder: SkillGraphBuilder,
        publication_builder: PublicationBuilder,
        harmonizer: PublicationHarmonizer | None = None,
    ) -> None:
        self.atom_extractor = atom_extractor
        self.skill_graph_builder = skill_graph_builder
        self.publication_builder = publication_builder
        self.harmonizer = harmonizer or PublicationHarmonizer()

    def build_publications(
        self,
        *,
        title_hint: str,
        goal: DistillGoal,
        evidence_nodes,
        skill: SkillDocument,
    ) -> tuple[SkillGraph, list[Publication]]:
        atoms = self.atom_extractor.extract(evidence_nodes)
        graph_name = skill.name.strip() or title_hint.strip() or 'untitled skill'
        skill_graph = self.skill_graph_builder.build(graph_name, goal, evidence_nodes, atoms)
        publications = self.publication_builder.build(skill_graph)
        return skill_graph, self.harmonizer.harmonize(publications, skill=skill, skill_graph=skill_graph)
