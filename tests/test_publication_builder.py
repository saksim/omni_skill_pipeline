from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.assembly.publication_builder import PublicationBuilder
from omni_skill_pipeline.models import (
    Audience,
    DecisionNode,
    Modality,
    PublicationType,
    SkillGraph,
    StepNode,
    VerificationNode,
)


class PublicationBuilderTests(unittest.TestCase):
    def _build_graph(self) -> SkillGraph:
        return SkillGraph(
            graph_id="graph-1",
            name="Incident Response Graph",
            goal="Convert evidence into executable response steps.",
            source_modalities=[Modality.TEXT],
            audience=Audience.EXPERT,
            summary="Incident response skill graph.",
            trigger=["error rate > 5%"],
            inputs=["error dashboard", "deploy history"],
            preconditions=["on-call engineer assigned"],
            steps=[
                StepNode(
                    step=1,
                    action="Rollback the latest deployment.",
                    why="Restore service stability before deeper debugging.",
                    atom_refs=["atom-1"],
                    evidence_refs=["ev-1"],
                    node_id="step-1",
                )
            ],
            decisions=[
                DecisionNode(
                    condition="error rate remains above threshold after rollback",
                    decision="Escalate to incident commander.",
                    rationale="Potential multi-component failure.",
                    evidence_refs=["ev-1"],
                    node_id="decision-1",
                )
            ],
            verifications=[
                VerificationNode(
                    check="p95 latency returns below 200ms.",
                    expected="Latency recovers within 10 minutes.",
                    evidence_refs=["ev-1"],
                    node_id="verification-1",
                )
            ],
            evidence_refs=["ev-1"],
            atom_refs=["atom-1"],
        )

    def test_builder_default_emits_markdown_and_json(self) -> None:
        graph = self._build_graph()
        builder = PublicationBuilder()
        publications = builder.build(graph)

        self.assertEqual([item.publication_type for item in publications], [PublicationType.SKILL_MARKDOWN, PublicationType.SKILL_JSON])
        markdown = publications[0]
        self.assertEqual(markdown.path, "SKILL.md")
        self.assertIn("Rollback the latest deployment.", markdown.content["text"])
        as_json = publications[1]
        self.assertEqual(as_json.path, "skill.json")
        self.assertEqual(as_json.content["graph_id"], graph.graph_id)

    def test_builder_emits_checklist_and_decision_tree(self) -> None:
        graph = self._build_graph()
        builder = PublicationBuilder()
        publications = builder.build(graph, publication_types=["checklist_json", "decision_tree_json"])

        self.assertEqual([item.publication_type for item in publications], [PublicationType.CHECKLIST_JSON, PublicationType.DECISION_TREE_JSON])
        checklist = publications[0]
        self.assertTrue(any(item["type"] == "step" for item in checklist.content["items"]))
        self.assertTrue(any(item["type"] == "verification" for item in checklist.content["items"]))
        decision_tree = publications[1]
        self.assertEqual(decision_tree.content["branches"][0]["condition"], graph.decisions[0].condition)

    def test_builder_dedupes_publication_types(self) -> None:
        graph = self._build_graph()
        builder = PublicationBuilder()
        publications = builder.build(
            graph,
            publication_types=[PublicationType.SKILL_JSON, "skill_json", PublicationType.SKILL_MARKDOWN],
        )

        self.assertEqual([item.publication_type for item in publications], [PublicationType.SKILL_JSON, PublicationType.SKILL_MARKDOWN])

    def test_builder_rejects_empty_publication_type(self) -> None:
        graph = self._build_graph()
        builder = PublicationBuilder()
        with self.assertRaises(ValueError):
            builder.build(graph, publication_types=[""])


if __name__ == "__main__":
    unittest.main()
