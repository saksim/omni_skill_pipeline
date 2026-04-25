from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from omni_skill_pipeline.extraction.atom_extractor import LegacyInsightAtomExtractor
from omni_skill_pipeline.models import (
    AtomType,
    ContentType,
    DecisionNode,
    EvidenceNode,
    EvidenceUnit,
    Insight,
    InsightType,
    Modality,
    RiskNode,
    SkillGraph,
    StepNode,
    SkillType,
)
from omni_skill_pipeline.transformers import evidence_units_to_nodes, skill_graph_to_document


class _CapturingInsightExtractor(object):
    def __init__(self) -> None:
        self.last_units: list[EvidenceUnit] = []

    def extract(self, evidence_units) -> list[Insight]:
        self.last_units = list(evidence_units)
        if not self.last_units:
            return []
        return [
            Insight(
                insight_type=InsightType.PROCEDURE,
                summary="Use legacy payload content.",
                evidence_refs=[self.last_units[0].evidence_id],
            )
        ]


class TransformersRegressionTests(unittest.TestCase):
    def test_evidence_units_to_nodes_preserves_order_and_respects_override_modality(self) -> None:
        units = [
            EvidenceUnit(
                asset_id="asset-1",
                span_ref="timestamp:1.0-2.0",
                content_type=ContentType.SPEECH,
                content="First event.",
                evidence_id="ev-1",
            ),
            EvidenceUnit(
                asset_id="asset-2",
                span_ref="frame:0001",
                content_type=ContentType.OCR,
                content="Second event.",
                evidence_id="ev-2",
            ),
        ]

        nodes = evidence_units_to_nodes(units, modality=Modality.VIDEO)
        self.assertEqual([item.evidence_id for item in nodes], ["ev-1", "ev-2"])
        self.assertEqual([item.modality for item in nodes], [Modality.VIDEO, Modality.VIDEO])

    def test_skill_graph_to_document_falls_back_to_default_verification(self) -> None:
        graph = SkillGraph(
            name="Fallback Verification Graph",
            goal="Ensure verification fallback exists.",
            source_modalities=[Modality.TEXT],
            steps=[StepNode(step=1, action="Do action.", evidence_refs=["ev-1"])],
            evidence_refs=["ev-1"],
        )

        skill = skill_graph_to_document(graph)
        self.assertEqual(
            skill.verification,
            ["Confirm each key conclusion can be traced back to evidence_refs."],
        )

    def test_skill_graph_to_document_selects_skill_type_branches(self) -> None:
        decision_graph = SkillGraph(
            name="Decision Graph",
            goal="Use decision rules.",
            source_modalities=[Modality.TEXT],
            decisions=[DecisionNode(condition="if high error", decision="rollback")],
        )
        diagnostic_graph = SkillGraph(
            name="Diagnostic Graph",
            goal="Diagnose issue.",
            source_modalities=[Modality.TEXT],
            risks=[RiskNode(risk="No baseline available.")],
        )
        analysis_graph = SkillGraph(
            name="Analysis Graph",
            goal="Analyze tabular evidence.",
            source_modalities=[Modality.TABULAR],
        )

        self.assertEqual(skill_graph_to_document(decision_graph).skill_type, SkillType.DECISION)
        self.assertEqual(skill_graph_to_document(diagnostic_graph).skill_type, SkillType.DIAGNOSTIC)
        self.assertEqual(skill_graph_to_document(analysis_graph).skill_type, SkillType.ANALYSIS)

    def test_skill_graph_to_document_dedupes_evidence_refs_from_all_nodes(self) -> None:
        graph = SkillGraph(
            name="Evidence Dedupe Graph",
            goal="Collect evidence refs.",
            source_modalities=[Modality.AUDIO],
            steps=[StepNode(step=1, action="Step.", evidence_refs=["ev-2", "ev-3"])],
            decisions=[DecisionNode(condition="if needed", decision="continue", evidence_refs=["ev-1", "ev-4"])],
            evidence_refs=["ev-1", "ev-2", "ev-1"],
        )

        skill = skill_graph_to_document(graph)
        self.assertEqual(skill.evidence_refs, ["ev-1", "ev-2", "ev-3", "ev-4"])

    def test_legacy_insight_atom_extractor_uses_payload_legacy_content_when_text_missing(self) -> None:
        capturing_extractor = _CapturingInsightExtractor()
        bridge = LegacyInsightAtomExtractor(insight_extractor=capturing_extractor)
        node = EvidenceNode(
            asset_id="asset-1",
            modality=Modality.TEXT,
            content_type=ContentType.TEXT,
            span_ref="line:1",
            text_content="",
            payload={"legacy_content": "Legacy content from payload."},
            evidence_id="ev-legacy",
        )

        atoms = bridge.extract([node])
        self.assertEqual(capturing_extractor.last_units[0].content, "Legacy content from payload.")
        self.assertEqual(atoms[0].atom_type, AtomType.PROCEDURE)
        self.assertEqual(atoms[0].evidence_refs, ["ev-legacy"])
        self.assertEqual(atoms[0].attributes["legacy_insight_type"], InsightType.PROCEDURE.value)


if __name__ == "__main__":
    unittest.main()

