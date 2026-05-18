from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.assembly.skill_graph_builder import SkillGraphBuilder
from omni_skill_pipeline.models import (
    AtomType,
    ContentType,
    DistillGoal,
    EvidenceNode,
    Modality,
    SemanticAtom,
)


class SkillGraphBuilderTests(unittest.TestCase):
    def test_builder_constructs_graph_from_minimal_atoms(self) -> None:
        builder = SkillGraphBuilder()
        goal = DistillGoal.from_dict({"domain": "incident_response", "audience": "expert"})
        evidence_nodes = [
            EvidenceNode(
                asset_id="asset-1",
                modality=Modality.AUDIO,
                content_type=ContentType.SPEECH,
                span_ref="video:timestamp:1.00-3.00",
                text_content="Roll back deployment and verify p95 latency.",
                evidence_id="ev-1",
            )
        ]
        atoms = [
            SemanticAtom(
                atom_type=AtomType.PROCEDURE,
                summary="Rollback deployment.",
                evidence_refs=["ev-1"],
                atom_id="atom-proc",
            ),
            SemanticAtom(
                atom_type=AtomType.RULE,
                summary="If error rate exceeds 5% -> rollback.",
                evidence_refs=["ev-1"],
                atom_id="atom-rule",
            ),
            SemanticAtom(
                atom_type=AtomType.VERIFICATION,
                summary="Verify p95 latency recovers below 200ms.",
                evidence_refs=["ev-1"],
                atom_id="atom-verify",
            ),
        ]

        graph = builder.build("Incident Graph", goal, evidence_nodes, atoms)
        graph.validate()
        self.assertTrue(graph.steps)
        self.assertIn("atom-proc", graph.steps[0].atom_refs)
        self.assertIn("ev-1", graph.steps[0].evidence_refs)
        self.assertTrue(any(edge.edge_type.value == "justified_by" for edge in graph.edges))
        self.assertTrue(any(edge.edge_type.value == "verified_by" for edge in graph.edges))

    def test_builder_fallback_step_traces_to_atoms_when_no_procedure(self) -> None:
        builder = SkillGraphBuilder()
        goal = DistillGoal.from_dict({"domain": "incident_response"})
        evidence_nodes = [
            EvidenceNode(
                asset_id="asset-2",
                modality=Modality.VIDEO,
                content_type=ContentType.EVENT,
                span_ref="frame:0001@1.00s:event",
                text_content="Rollback button clicked.",
                evidence_id="ev-2",
            )
        ]
        atoms = [
            SemanticAtom(
                atom_type=AtomType.EVENT,
                summary="Rollback button clicked.",
                evidence_refs=["ev-2"],
                atom_id="atom-event",
            )
        ]

        graph = builder.build("Fallback Atom Graph", goal, evidence_nodes, atoms)
        graph.validate()
        self.assertTrue(graph.steps)
        self.assertIn("atom-event", graph.steps[0].atom_refs)
        self.assertIn("ev-2", graph.steps[0].evidence_refs)

    def test_builder_fallback_step_traces_to_evidence_when_no_atoms(self) -> None:
        builder = SkillGraphBuilder()
        goal = DistillGoal.from_dict({"domain": "ops"})
        evidence_nodes = [
            EvidenceNode(
                asset_id="asset-3",
                modality=Modality.TEXT,
                content_type=ContentType.TEXT,
                span_ref="line:0001",
                text_content="Collect baseline metrics before deploy.",
                evidence_id="ev-3",
            )
        ]

        graph = builder.build("Evidence Fallback Graph", goal, evidence_nodes, [])
        graph.validate()
        self.assertTrue(graph.steps)
        self.assertIn("ev-3", graph.steps[0].evidence_refs)
        self.assertEqual(graph.steps[0].metadata.get("source_span_ref"), "line:0001")


if __name__ == "__main__":
    unittest.main()
