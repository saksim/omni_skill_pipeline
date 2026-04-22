from __future__ import annotations

from typing import Sequence

from omni_skill_pipeline.models import Publication, PublicationType, SkillGraph
from omni_skill_pipeline.render import render_skill_markdown
from omni_skill_pipeline.transformers import skill_graph_to_document
from omni_skill_pipeline.utils import unique_preserve_order


class PublicationBuilder(object):
    DEFAULT_PUBLICATION_TYPES = (
        PublicationType.SKILL_MARKDOWN,
        PublicationType.SKILL_JSON,
    )

    def build(
        self,
        graph: SkillGraph,
        *,
        publication_types: Sequence[PublicationType | str] | None = None,
    ) -> list[Publication]:
        graph.validate()
        skill = skill_graph_to_document(graph)
        types = self._resolve_publication_types(publication_types)
        publications: list[Publication] = []
        for publication_type in types:
            publications.append(self._build_single_publication(graph, skill, publication_type))
        return publications

    def _resolve_publication_types(
        self,
        publication_types: Sequence[PublicationType | str] | None,
    ) -> list[PublicationType]:
        requested = publication_types or self.DEFAULT_PUBLICATION_TYPES
        resolved: list[PublicationType] = []
        for item in requested:
            if isinstance(item, PublicationType):
                publication_type = item
            else:
                normalized = str(item).strip().lower()
                if not normalized:
                    raise ValueError('publication type cannot be empty.')
                try:
                    publication_type = PublicationType(normalized)
                except ValueError as exc:
                    valid = ', '.join(member.value for member in PublicationType)
                    raise ValueError('Unsupported publication type: %s (valid: %s)' % (normalized, valid)) from exc
            resolved.append(publication_type)

        return [PublicationType(item) for item in unique_preserve_order(entry.value for entry in resolved)]

    def _build_single_publication(self, graph: SkillGraph, skill, publication_type: PublicationType) -> Publication:
        metadata = {
            'source': 'skill_graph',
            'graph_id': graph.graph_id,
            'skill_id': skill.skill_id,
            'version': graph.version,
        }
        if publication_type == PublicationType.SKILL_MARKDOWN:
            return Publication(
                publication_type=publication_type,
                content={
                    'filename': 'SKILL.md',
                    'text': render_skill_markdown(skill),
                    'graph_id': graph.graph_id,
                    'skill_id': skill.skill_id,
                },
                path='SKILL.md',
                metadata={**metadata, 'renderer': 'skill_markdown_v1'},
            )
        if publication_type == PublicationType.SKILL_JSON:
            return Publication(
                publication_type=publication_type,
                content={
                    'filename': 'skill.json',
                    'skill': skill.to_dict(),
                    'graph_id': graph.graph_id,
                },
                path='skill.json',
                metadata={**metadata, 'renderer': 'skill_json_v1'},
            )
        if publication_type == PublicationType.CHECKLIST_JSON:
            items = []
            for step in sorted(skill.steps, key=lambda item: item.step):
                items.append(
                    {
                        'type': 'step',
                        'order': step.step,
                        'title': step.action,
                        'reason': step.why,
                    }
                )
            for check in skill.verification:
                items.append({'type': 'verification', 'title': check})
            return Publication(
                publication_type=publication_type,
                content={
                    'filename': 'checklist.json',
                    'graph_id': graph.graph_id,
                    'items': items,
                },
                path='checklist.json',
                metadata={**metadata, 'renderer': 'checklist_json_v1'},
            )
        if publication_type == PublicationType.DECISION_TREE_JSON:
            branches = []
            for item in graph.decisions:
                branches.append(
                    {
                        'condition': item.condition,
                        'decision': item.decision,
                        'rationale': item.rationale,
                        'evidence_refs': item.evidence_refs,
                    }
                )
            if not branches:
                branches.append(
                    {
                        'condition': 'default',
                        'decision': 'Execute step sequence in order.',
                        'rationale': 'No explicit decision nodes were provided.',
                        'evidence_refs': [],
                    }
                )
            return Publication(
                publication_type=publication_type,
                content={
                    'filename': 'decision_tree.json',
                    'graph_id': graph.graph_id,
                    'branches': branches,
                },
                path='decision_tree.json',
                metadata={**metadata, 'renderer': 'decision_tree_json_v1'},
            )
        raise ValueError('Unsupported publication type: %s' % publication_type.value)
