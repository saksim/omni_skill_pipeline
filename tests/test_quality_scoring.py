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
    ContentType,
    EvidenceNode,
    Modality,
    Publication,
    PublicationType,
    SkillDocument,
    SkillGraph,
    SkillStep,
    StepNode,
)
from omni_skill_pipeline.quality.scoring import QualityScorer


class QualityScorerTests(unittest.TestCase):
    def _fixtures(self, *, with_step_refs: bool = True):
        skill = SkillDocument(
            name="Incident Triage",
            goal="Recover service quickly.",
            source_modality=Modality.TEXT,
            audience=Audience.EXPERT,
            summary="Triage runbook.",
            steps=[
                SkillStep(step=1, action="Rebuild timeline from logs.", why="Establish causal chain."),
                SkillStep(step=2, action="Rollback recent deployment.", why="Reduce blast radius."),
            ],
            evidence_refs=["ev-1", "ev-2"],
            tags=["incident", "triage", "ops"],
            skill_id="skill-1",
        )
        step_refs = ["ev-1"] if with_step_refs else []
        graph = SkillGraph(
            graph_id="graph-1",
            name="Incident Triage Graph",
            goal="Convert evidence into triage steps.",
            source_modalities=[Modality.TEXT],
            steps=[
                StepNode(step=1, action="Rebuild timeline from logs.", why="Establish causal chain.", evidence_refs=step_refs),
                StepNode(step=2, action="Rollback recent deployment.", why="Reduce blast radius.", evidence_refs=step_refs),
            ],
            evidence_refs=["ev-1", "ev-2"],
        )
        evidence_nodes = [
            EvidenceNode(
                asset_id="asset-1",
                modality=Modality.TEXT,
                content_type=ContentType.TEXT,
                span_ref="line:1",
                text_content="Rebuild timeline from logs and metrics.",
                evidence_id="ev-1",
                confidence=0.9,
            ),
            EvidenceNode(
                asset_id="asset-1",
                modality=Modality.TEXT,
                content_type=ContentType.TEXT,
                span_ref="line:2",
                text_content="Rollback recent deployment when error rate spikes.",
                evidence_id="ev-2",
                confidence=0.85,
            ),
        ]
        publications = [
            Publication(
                publication_type=PublicationType.SKILL_MARKDOWN,
                content={"filename": "SKILL.md", "text": "# Incident Triage"},
                path="SKILL.md",
            ),
            Publication(
                publication_type=PublicationType.SKILL_JSON,
                content={"filename": "skill.json", "skill": {"name": "Incident Triage"}},
                path="skill.json",
            ),
        ]
        return skill, graph, evidence_nodes, publications

    def test_scorer_outputs_all_required_metrics(self) -> None:
        scorer = QualityScorer()
        skill, graph, evidence_nodes, publications = self._fixtures()
        payload = scorer.score(skill=skill, skill_graph=graph, evidence_nodes=evidence_nodes, publications=publications).to_dict()

        for key in (
            "traceability_score",
            "actionability_score",
            "coverage_score",
            "consistency_score",
            "noise_score",
            "novelty_score",
            "overall_score",
        ):
            self.assertIn(key, payload)
            self.assertGreaterEqual(float(payload[key]), 0.0)
            self.assertLessEqual(float(payload[key]), 1.0)

    def test_traceability_drops_when_step_lacks_evidence_refs(self) -> None:
        scorer = QualityScorer()
        good_skill, good_graph, evidence_nodes, publications = self._fixtures(with_step_refs=True)
        weak_skill, weak_graph, _, _ = self._fixtures(with_step_refs=False)
        strong = scorer.score(skill=good_skill, skill_graph=good_graph, evidence_nodes=evidence_nodes, publications=publications)
        weak = scorer.score(skill=weak_skill, skill_graph=weak_graph, evidence_nodes=evidence_nodes, publications=publications)
        self.assertGreater(strong.traceability_score, weak.traceability_score)


if __name__ == "__main__":
    unittest.main()
