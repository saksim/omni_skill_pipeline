from __future__ import annotations

from typing import Iterable, Optional, Sequence

from omni_skill_pipeline.models import (
    Audience,
    ContentType,
    DecisionNode,
    EvidenceNode,
    EvidenceUnit,
    Modality,
    ReviewStatus,
    SkillDocument,
    SkillGraph,
    SkillStep,
    SkillType,
)
from omni_skill_pipeline.utils import unique_preserve_order


def _infer_modality_from_content_type(content_type: ContentType) -> Modality:
    if content_type == ContentType.SPEECH:
        return Modality.AUDIO
    if content_type in {ContentType.OCR, ContentType.SCENE}:
        return Modality.IMAGE
    if content_type in {ContentType.TABLE, ContentType.METRIC, ContentType.EVENT}:
        return Modality.TABULAR
    return Modality.TEXT


def evidence_unit_to_node(unit: EvidenceUnit, modality: Optional[Modality] = None) -> EvidenceNode:
    resolved_modality = modality or _infer_modality_from_content_type(unit.content_type)
    return EvidenceNode(
        asset_id=unit.asset_id,
        modality=resolved_modality,
        content_type=unit.content_type,
        span_ref=unit.span_ref,
        text_content=unit.content,
        payload={'legacy_content': unit.content},
        speaker=unit.speaker,
        confidence=unit.confidence,
        tags=list(unit.tags),
        evidence_id=unit.evidence_id,
    )


def evidence_units_to_nodes(units: Sequence[EvidenceUnit], modality: Optional[Modality] = None) -> list[EvidenceNode]:
    return [evidence_unit_to_node(unit, modality=modality) for unit in units]


def _render_decision_rule(node: DecisionNode) -> str:
    if node.condition and node.decision:
        return '%s -> %s' % (node.condition, node.decision)
    return node.decision or node.condition


def _collect_evidence_refs(graph: SkillGraph) -> list[str]:
    refs = list(graph.evidence_refs)
    for step in graph.steps:
        refs.extend(step.evidence_refs)
    for node in graph.decisions:
        refs.extend(node.evidence_refs)
    for node in graph.verifications:
        refs.extend(node.evidence_refs)
    for node in graph.risks:
        refs.extend(node.evidence_refs)
    return unique_preserve_order(refs)


def _select_skill_type(graph: SkillGraph) -> SkillType:
    if graph.steps:
        return SkillType.PROCEDURE
    if graph.decisions:
        return SkillType.DECISION
    if graph.risks and not graph.steps:
        return SkillType.DIAGNOSTIC
    if Modality.TABULAR in graph.source_modalities:
        return SkillType.ANALYSIS
    return SkillType.PROCEDURE


def _graph_steps_to_skill_steps(graph: SkillGraph) -> list[SkillStep]:
    if not graph.steps:
        return []
    sorted_steps = sorted(graph.steps, key=lambda item: item.step)
    return [SkillStep(step=item.step, action=item.action, why=item.why) for item in sorted_steps]


def _coerce_source_modality(source_modalities: Iterable[Modality]) -> Modality:
    materialized = list(source_modalities)
    if not materialized:
        return Modality.TEXT
    return materialized[0]


def skill_graph_to_document(
    graph: SkillGraph,
    *,
    fallback_audience: Audience = Audience.SELF,
    fallback_review_status: ReviewStatus = ReviewStatus.DRAFT,
) -> SkillDocument:
    decision_rules = unique_preserve_order(_render_decision_rule(node) for node in graph.decisions)
    anti_patterns = unique_preserve_order(node.risk for node in graph.risks if node.risk)
    verification = unique_preserve_order(node.check for node in graph.verifications if node.check)
    preconditions = unique_preserve_order(graph.preconditions)
    if not verification:
        verification = ['Confirm each key conclusion can be traced back to evidence_refs.']

    return SkillDocument(
        name=graph.name.strip() or 'Untitled skill graph',
        goal=graph.goal.strip() or 'No goal provided.',
        source_modality=_coerce_source_modality(graph.source_modalities),
        skill_type=_select_skill_type(graph),
        audience=graph.audience or fallback_audience,
        trigger=unique_preserve_order(graph.trigger),
        inputs=unique_preserve_order(graph.inputs + [node.name for node in graph.variables if node.name]),
        preconditions=preconditions,
        steps=_graph_steps_to_skill_steps(graph),
        decision_rules=decision_rules,
        anti_patterns=anti_patterns,
        verification=verification,
        evidence_refs=_collect_evidence_refs(graph),
        confidence=graph.confidence,
        version=graph.version,
        summary=graph.summary,
        tags=unique_preserve_order(graph.tags + [graph.domain]),
        review_status=graph.review_status or fallback_review_status,
        created_at=graph.created_at,
        skill_id=graph.graph_id,
    )
