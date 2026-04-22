from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.models import (
    DecisionNode,
    ExampleNode,
    GraphEdgeType,
    Modality,
    RiskNode,
    SkillGraph,
    SkillGraphEdge,
    StepNode,
    VariableNode,
    VerificationNode,
)


class SkillGraphModelTests(unittest.TestCase):
    def test_skill_graph_validate_and_serialize_with_all_min_nodes_and_edges(self) -> None:
        step = StepNode(step=1, action="Collect incident timeline.", node_id="step-1")
        decision = DecisionNode(condition="if p95 > 200ms", decision="rollback", node_id="decision-1")
        verification = VerificationNode(check="Confirm p95 < 200ms.", node_id="verify-1")
        risk = RiskNode(risk="Missing baseline causes false alarm.", node_id="risk-1")
        example = ExampleNode(example="Latency recovered after rollback.", node_id="example-1")
        variable = VariableNode(name="latency_threshold_ms", default_value="200", node_id="var-1")

        edges = [
            SkillGraphEdge(edge_type=GraphEdgeType.DEPENDS_ON, source_node_id="step-1", target_node_id="decision-1"),
            SkillGraphEdge(edge_type=GraphEdgeType.JUSTIFIED_BY, source_node_id="step-1", target_node_id="decision-1"),
            SkillGraphEdge(edge_type=GraphEdgeType.VERIFIED_BY, source_node_id="step-1", target_node_id="verify-1"),
            SkillGraphEdge(edge_type=GraphEdgeType.PARAMETERIZES, source_node_id="step-1", target_node_id="var-1"),
            SkillGraphEdge(edge_type=GraphEdgeType.SUPERSEDES, source_node_id="example-1", target_node_id="risk-1"),
        ]
        graph = SkillGraph(
            name="Incident Triage Graph",
            goal="Convert evidence into executable triage workflow.",
            source_modalities=[Modality.AUDIO, Modality.VIDEO, Modality.TABULAR],
            steps=[step],
            decisions=[decision],
            verifications=[verification],
            risks=[risk],
            examples=[example],
            variables=[variable],
            edges=edges,
            evidence_refs=["ev-1"],
            atom_refs=["atom-1"],
        )

        graph.validate()
        payload = json.loads(graph.to_json())
        edge_types = {item["edge_type"] for item in payload["edges"]}
        self.assertEqual(payload["steps"][0]["node_type"], "step")
        self.assertEqual(payload["decisions"][0]["node_type"], "decision")
        self.assertIn("depends_on", edge_types)
        self.assertIn("justified_by", edge_types)
        self.assertIn("verified_by", edge_types)
        self.assertIn("parameterizes", edge_types)
        self.assertIn("supersedes", edge_types)

    def test_skill_graph_validate_rejects_missing_edge_target(self) -> None:
        graph = SkillGraph(
            name="Broken Graph",
            goal="Should fail.",
            source_modalities=[Modality.TEXT],
            steps=[StepNode(step=1, action="noop", node_id="step-1")],
            edges=[SkillGraphEdge(edge_type=GraphEdgeType.DEPENDS_ON, source_node_id="step-1", target_node_id="missing")],
        )
        with self.assertRaises(ValueError):
            graph.validate()

    def test_skill_graph_validate_rejects_duplicate_node_ids(self) -> None:
        graph = SkillGraph(
            name="Duplicate Node Graph",
            goal="Should fail on duplicate ids.",
            source_modalities=[Modality.TEXT],
            steps=[StepNode(step=1, action="first", node_id="dup-node")],
            decisions=[DecisionNode(condition="if true", decision="do", node_id="dup-node")],
        )
        with self.assertRaises(ValueError):
            graph.validate()


if __name__ == "__main__":
    unittest.main()
