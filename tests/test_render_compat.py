from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.models import (
    Audience,
    Modality,
    Publication,
    PublicationType,
    SkillDocument,
    SkillGraph,
    SkillStep,
    StepNode,
)
from omni_skill_pipeline.render import (
    render_skill_graph_markdown,
    render_skill_markdown,
    render_skill_markdown_compat,
    resolve_skill_markdown,
)


class RenderCompatibilityTests(unittest.TestCase):
    def _build_skill(self) -> SkillDocument:
        return SkillDocument(
            name="Incident Recovery",
            goal="Recover service after incident.",
            source_modality=Modality.TEXT,
            audience=Audience.EXPERT,
            steps=[
                SkillStep(step=1, action="Rebuild timeline.", why="Anchor facts."),
                SkillStep(step=2, action="Rollback deployment.", why="Reduce blast radius."),
            ],
            summary="Recovery checklist",
            evidence_refs=["ev-1"],
            tags=["incident"],
            skill_id="skill-1",
        )

    def _build_graph(self) -> SkillGraph:
        return SkillGraph(
            name="Incident Recovery Graph",
            goal="Convert incident evidence into steps.",
            source_modalities=[Modality.TEXT],
            steps=[StepNode(step=1, action="Rebuild timeline.", why="Anchor facts.", evidence_refs=["ev-1"])],
            evidence_refs=["ev-1"],
            graph_id="graph-1",
        )

    def test_resolve_skill_markdown_from_publication(self) -> None:
        publication = Publication(
            publication_type=PublicationType.SKILL_MARKDOWN,
            content={"filename": "SKILL.md", "text": "# publication markdown"},
            path="SKILL.md",
        )
        resolved = resolve_skill_markdown([publication])
        self.assertEqual(resolved, "# publication markdown")

    def test_render_skill_markdown_compat_prefers_publication_payload(self) -> None:
        skill = self._build_skill()
        publication = Publication(
            publication_type=PublicationType.SKILL_MARKDOWN,
            content={"filename": "SKILL.md", "text": "# publication markdown"},
            path="SKILL.md",
        )
        output = render_skill_markdown_compat(publications=[publication], skill=skill)
        self.assertEqual(output, "# publication markdown")

    def test_render_skill_markdown_compat_falls_back_to_skill_document(self) -> None:
        skill = self._build_skill()
        publication = Publication(
            publication_type=PublicationType.SKILL_JSON,
            content={"filename": "skill.json", "skill": {"name": "x"}},
            path="skill.json",
        )
        output = render_skill_markdown_compat(publications=[publication], skill=skill)
        self.assertEqual(output, render_skill_markdown(skill))

    def test_render_skill_markdown_compat_supports_graph_fallback(self) -> None:
        graph = self._build_graph()
        output = render_skill_markdown_compat(graph=graph)
        self.assertEqual(output, render_skill_graph_markdown(graph))
        self.assertIn("# Incident Recovery Graph", output)


if __name__ == "__main__":
    unittest.main()
