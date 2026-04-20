from __future__ import annotations

from typing import Sequence

from omni_skill_pipeline.models import (
    AtomType,
    DistillGoal,
    EvidenceNode,
    GraphEdgeType,
    Modality,
    SemanticAtom,
    SkillGraph,
    SkillGraphEdge,
    StepNode,
    VerificationNode,
    DecisionNode,
    RiskNode,
    ExampleNode,
    VariableNode,
)
from omni_skill_pipeline.utils import split_sentences, unique_preserve_order


class SkillGraphBuilder(object):
    def build(
        self,
        name: str,
        goal: DistillGoal,
        evidence_nodes: Sequence[EvidenceNode],
        atoms: Sequence[SemanticAtom],
    ) -> SkillGraph:
        source_modalities = self._collect_modalities(evidence_nodes)
        steps = self._build_steps(atoms, evidence_nodes)
        decisions = self._build_decisions(atoms)
        verifications = self._build_verifications(atoms)
        risks = self._build_risks(atoms)
        examples = self._build_examples(atoms)
        variables = self._build_variables(atoms)
        edges = self._build_edges(steps, decisions, verifications)
        return SkillGraph(
            name=name.strip() or self._fallback_name(goal, evidence_nodes),
            goal=self._build_goal(goal),
            source_modalities=source_modalities,
            audience=goal.audience,
            summary=self._build_summary(atoms, evidence_nodes),
            tags=unique_preserve_order([goal.domain, 'skill_graph']),
            domain=goal.domain,
            trigger=[self._build_trigger(goal, source_modalities)],
            inputs=self._build_inputs(source_modalities),
            preconditions=['Confirm source evidence is complete and correctly scoped to the goal.'],
            steps=steps,
            decisions=decisions,
            verifications=verifications,
            risks=risks,
            examples=examples,
            variables=variables,
            edges=edges,
            evidence_refs=unique_preserve_order(item.evidence_id for item in evidence_nodes),
            atom_refs=unique_preserve_order(item.atom_id for item in atoms),
            confidence=self._estimate_confidence(evidence_nodes, atoms, steps),
        )

    def _collect_modalities(self, evidence_nodes: Sequence[EvidenceNode]) -> list[Modality]:
        if not evidence_nodes:
            return [Modality.TEXT]
        seen = set()
        modalities: list[Modality] = []
        for node in evidence_nodes:
            key = node.modality.value
            if key in seen:
                continue
            seen.add(key)
            modalities.append(node.modality)
        return modalities

    def _build_steps(self, atoms: Sequence[SemanticAtom], evidence_nodes: Sequence[EvidenceNode]) -> list[StepNode]:
        procedure_atoms = [item for item in atoms if item.atom_type == AtomType.PROCEDURE]
        steps: list[StepNode] = []
        for index, atom in enumerate(procedure_atoms, start=1):
            why = str(atom.attributes.get('why', '')).strip() or 'Derived from semantic atom.'
            steps.append(
                StepNode(
                    step=index,
                    action=atom.summary.strip(),
                    why=why,
                    atom_refs=[atom.atom_id],
                    evidence_refs=list(atom.evidence_refs),
                )
            )
        if steps:
            return steps
        fallback_actions = self._fallback_actions(evidence_nodes)
        for index, action in enumerate(fallback_actions, start=1):
            steps.append(
                StepNode(
                    step=index,
                    action=action,
                    why='Derived from evidence fallback because no procedure atoms were found.',
                )
            )
        return steps

    def _fallback_actions(self, evidence_nodes: Sequence[EvidenceNode]) -> list[str]:
        actions: list[str] = []
        for item in evidence_nodes[:3]:
            sentences = split_sentences(item.text_content)
            if sentences:
                actions.append(sentences[0])
        return unique_preserve_order(actions) or ['Review the available evidence and define concrete procedural steps.']

    def _build_decisions(self, atoms: Sequence[SemanticAtom]) -> list[DecisionNode]:
        rules = [item for item in atoms if item.atom_type == AtomType.RULE]
        nodes: list[DecisionNode] = []
        for atom in rules:
            condition, decision = self._split_rule(atom.summary)
            nodes.append(
                DecisionNode(
                    condition=condition,
                    decision=decision,
                    rationale=str(atom.attributes.get('rationale', '')).strip(),
                    atom_refs=[atom.atom_id],
                    evidence_refs=list(atom.evidence_refs),
                )
            )
        return nodes

    def _split_rule(self, text: str) -> tuple[str, str]:
        normalized = text.strip()
        if '->' in normalized:
            left, right = normalized.split('->', 1)
            return left.strip(), right.strip()
        if normalized.lower().startswith('if '):
            return normalized, 'Apply the matching action.'
        return 'When rule conditions are met.', normalized

    def _build_verifications(self, atoms: Sequence[SemanticAtom]) -> list[VerificationNode]:
        verifications = [item for item in atoms if item.atom_type == AtomType.VERIFICATION]
        return [
            VerificationNode(
                check=atom.summary.strip(),
                expected=str(atom.attributes.get('expected', '')).strip(),
                atom_refs=[atom.atom_id],
                evidence_refs=list(atom.evidence_refs),
            )
            for atom in verifications
        ]

    def _build_risks(self, atoms: Sequence[SemanticAtom]) -> list[RiskNode]:
        anti_patterns = [item for item in atoms if item.atom_type == AtomType.ANTI_PATTERN]
        return [
            RiskNode(
                risk=atom.summary.strip(),
                mitigation=str(atom.attributes.get('mitigation', '')).strip(),
                atom_refs=[atom.atom_id],
                evidence_refs=list(atom.evidence_refs),
            )
            for atom in anti_patterns
        ]

    def _build_examples(self, atoms: Sequence[SemanticAtom]) -> list[ExampleNode]:
        examples = [item for item in atoms if item.atom_type == AtomType.EXAMPLE]
        return [
            ExampleNode(
                example=atom.summary.strip(),
                classification=str(atom.attributes.get('classification', 'positive')).strip() or 'positive',
                atom_refs=[atom.atom_id],
                evidence_refs=list(atom.evidence_refs),
            )
            for atom in examples
        ]

    def _build_variables(self, atoms: Sequence[SemanticAtom]) -> list[VariableNode]:
        entities = [item for item in atoms if item.atom_type == AtomType.ENTITY]
        variables: list[VariableNode] = []
        seen = set()
        for atom in entities:
            name = str(atom.attributes.get('name', atom.summary)).strip()
            if not name:
                continue
            key = name.lower()
            if key in seen:
                continue
            seen.add(key)
            variables.append(
                VariableNode(
                    name=name,
                    description=str(atom.attributes.get('description', '')).strip(),
                    default_value=str(atom.attributes.get('default', '')).strip() or None,
                    atom_refs=[atom.atom_id],
                    evidence_refs=list(atom.evidence_refs),
                )
            )
        return variables

    def _build_edges(
        self,
        steps: Sequence[StepNode],
        decisions: Sequence[DecisionNode],
        verifications: Sequence[VerificationNode],
    ) -> list[SkillGraphEdge]:
        edges: list[SkillGraphEdge] = []
        for index in range(1, len(steps)):
            edges.append(
                SkillGraphEdge(
                    edge_type=GraphEdgeType.DEPENDS_ON,
                    source_node_id=steps[index].node_id,
                    target_node_id=steps[index - 1].node_id,
                    rationale='Step ordering dependency.',
                )
            )
        for node in decisions:
            if not steps:
                break
            edges.append(
                SkillGraphEdge(
                    edge_type=GraphEdgeType.JUSTIFIED_BY,
                    source_node_id=steps[0].node_id,
                    target_node_id=node.node_id,
                    rationale='Decision informs initial execution branch.',
                )
            )
        for node in verifications:
            if not steps:
                break
            edges.append(
                SkillGraphEdge(
                    edge_type=GraphEdgeType.VERIFIED_BY,
                    source_node_id=steps[-1].node_id,
                    target_node_id=node.node_id,
                    rationale='Final step should be validated explicitly.',
                )
            )
        return edges

    def _build_summary(self, atoms: Sequence[SemanticAtom], evidence_nodes: Sequence[EvidenceNode]) -> str:
        for atom in atoms:
            if atom.summary.strip():
                return atom.summary.strip()[:280]
        for item in evidence_nodes:
            if item.text_content.strip():
                return item.text_content.strip().replace('\n', ' ')[:280]
        return 'No summary generated.'

    def _fallback_name(self, goal: DistillGoal, evidence_nodes: Sequence[EvidenceNode]) -> str:
        if evidence_nodes and evidence_nodes[0].text_content.strip():
            sentence = split_sentences(evidence_nodes[0].text_content)
            if sentence:
                return sentence[0][:60]
        return '%s skill graph' % goal.domain.replace('_', ' ').strip()

    def _build_goal(self, goal: DistillGoal) -> str:
        return 'Distill %s material into %s for %s.' % (
            goal.domain,
            goal.goal_type.value,
            goal.audience.value,
        )

    def _build_trigger(self, goal: DistillGoal, source_modalities: Sequence[Modality]) -> str:
        modality_hint = '/'.join(item.value for item in source_modalities)
        return 'Use when converting %s evidence into %s.' % (modality_hint, goal.goal_type.value)

    def _build_inputs(self, source_modalities: Sequence[Modality]) -> list[str]:
        mapping = {
            Modality.TEXT: 'Source document',
            Modality.AUDIO: 'Audio transcript or source',
            Modality.IMAGE: 'Image frames or screenshots',
            Modality.VIDEO: 'Video source and sampled frames',
            Modality.TABULAR: 'Structured table or time-series dataset',
        }
        return unique_preserve_order(mapping.get(item, item.value) for item in source_modalities)

    def _estimate_confidence(
        self,
        evidence_nodes: Sequence[EvidenceNode],
        atoms: Sequence[SemanticAtom],
        steps: Sequence[StepNode],
    ) -> float:
        score = 0.35
        score += min(0.25, len(evidence_nodes) * 0.03)
        score += min(0.25, len(atoms) * 0.02)
        score += min(0.15, len(steps) * 0.04)
        return round(min(score, 0.95), 2)
