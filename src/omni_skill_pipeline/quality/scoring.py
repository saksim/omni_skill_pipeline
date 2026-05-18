from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from omni_skill_pipeline.models import EvidenceNode, Publication, SkillDocument, SkillGraph
from omni_skill_pipeline.utils import split_sentences, unique_preserve_order


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _round(value: float) -> float:
    return round(_clamp(value), 4)


@dataclass(frozen=True, slots=True)
class QualityScore:
    traceability_score: float
    actionability_score: float
    coverage_score: float
    consistency_score: float
    noise_score: float
    novelty_score: float
    overall_score: float
    diagnostics: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, float | dict[str, float]]:
        return {
            "traceability_score": self.traceability_score,
            "actionability_score": self.actionability_score,
            "coverage_score": self.coverage_score,
            "consistency_score": self.consistency_score,
            "noise_score": self.noise_score,
            "novelty_score": self.novelty_score,
            "overall_score": self.overall_score,
            "diagnostics": self.diagnostics,
        }


class QualityScorer(object):
    """Heuristic scorer for TP-E7-01 quality gate baseline."""

    def score(
        self,
        *,
        skill: SkillDocument,
        skill_graph: SkillGraph,
        evidence_nodes: Sequence[EvidenceNode],
        publications: Sequence[Publication],
    ) -> QualityScore:
        traceability = self._traceability(skill_graph, evidence_nodes)
        actionability = self._actionability(skill)
        coverage = self._coverage(skill_graph, evidence_nodes)
        consistency = self._consistency(skill, skill_graph)
        noise = self._noise(evidence_nodes)
        novelty = self._novelty(skill, publications)
        overall = _round((traceability + actionability + coverage + consistency + noise + novelty) / 6.0)
        diagnostics = {
            "step_count": float(len(skill.steps)),
            "evidence_node_count": float(len(evidence_nodes)),
            "publication_count": float(len(publications)),
        }
        return QualityScore(
            traceability_score=traceability,
            actionability_score=actionability,
            coverage_score=coverage,
            consistency_score=consistency,
            noise_score=noise,
            novelty_score=novelty,
            overall_score=overall,
            diagnostics=diagnostics,
        )

    def _traceability(self, skill_graph: SkillGraph, evidence_nodes: Sequence[EvidenceNode]) -> float:
        known = {item.evidence_id for item in evidence_nodes}
        if not known:
            return 0.0
        if not skill_graph.steps:
            return 0.2
        traced = 0
        for step in skill_graph.steps:
            refs = unique_preserve_order(step.evidence_refs + step.atom_refs)
            if refs and any(ref in known for ref in step.evidence_refs):
                traced += 1
        return _round(traced / max(len(skill_graph.steps), 1))

    def _actionability(self, skill: SkillDocument) -> float:
        if not skill.steps:
            return 0.1
        concrete = 0
        for step in skill.steps:
            action = step.action.strip()
            if len(action) < 8:
                continue
            sentences = split_sentences(action)
            has_verb_like_shape = bool(sentences) and any(token in action.lower() for token in (" ", "-", "_"))
            if has_verb_like_shape:
                concrete += 1
        why_ratio = sum(1 for step in skill.steps if step.why.strip()) / max(len(skill.steps), 1)
        return _round((concrete / len(skill.steps)) * 0.8 + why_ratio * 0.2)

    def _coverage(self, skill_graph: SkillGraph, evidence_nodes: Sequence[EvidenceNode]) -> float:
        total = len(evidence_nodes)
        if total == 0:
            return 0.0
        covered = {ref for ref in skill_graph.evidence_refs if ref}
        if not covered:
            for step in skill_graph.steps:
                covered.update(step.evidence_refs)
            for node in skill_graph.decisions:
                covered.update(node.evidence_refs)
            for node in skill_graph.verifications:
                covered.update(node.evidence_refs)
        known = {item.evidence_id for item in evidence_nodes}
        overlap = len(covered.intersection(known))
        return _round(overlap / total)

    def _consistency(self, skill: SkillDocument, skill_graph: SkillGraph) -> float:
        if not skill.steps:
            return 0.25
        penalty = 0.0
        seen_actions: set[str] = set()
        for step in skill.steps:
            normalized = step.action.strip().lower()
            if not normalized:
                penalty += 0.2
                continue
            if normalized in seen_actions:
                penalty += 0.1
            seen_actions.add(normalized)
        has_goal = 0.0 if skill.goal.strip() else 0.2
        has_edges = 0.0 if skill_graph.edges else 0.1
        return _round(1.0 - min(0.85, penalty + has_goal + has_edges))

    def _noise(self, evidence_nodes: Sequence[EvidenceNode]) -> float:
        if not evidence_nodes:
            return 0.0
        noisy = 0.0
        for node in evidence_nodes:
            text = node.text_content or ""
            if node.confidence < 0.5:
                noisy += 1.0
            if len(text.strip()) < 6:
                noisy += 0.4
            if text.count("?") >= 4 or "\ufffd" in text:
                noisy += 0.8
        penalty = noisy / max(len(evidence_nodes), 1)
        return _round(1.0 - min(1.0, penalty))

    def _novelty(self, skill: SkillDocument, publications: Sequence[Publication]) -> float:
        text = " ".join(
            [
                skill.name,
                skill.summary,
                skill.goal,
                " ".join(step.action for step in skill.steps),
                " ".join(skill.decision_rules),
                " ".join(skill.verification),
            ]
        ).lower()
        tokens = [item for item in text.replace("\n", " ").split(" ") if item]
        if not tokens:
            base = 0.2
        else:
            unique_ratio = len(set(tokens)) / len(tokens)
            base = 0.3 + unique_ratio * 0.7
        modality_bonus = 0.0
        if len(skill.tags) >= 3:
            modality_bonus += 0.05
        if len(publications) >= 2:
            modality_bonus += 0.05
        return _round(base + modality_bonus)
