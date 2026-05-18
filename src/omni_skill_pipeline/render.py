from __future__ import annotations

from typing import Iterable, Sequence

from omni_skill_pipeline.models import Publication, PublicationType, SkillDocument, SkillGraph, SkillStep


def _render_list(items: Iterable[str], empty_text: str = "- None") -> str:
    materialized = [item for item in items if item]
    if not materialized:
        return empty_text
    return "\n".join("- %s" % item for item in materialized)


def _render_steps(steps: Iterable[SkillStep]) -> str:
    materialized = list(steps)
    if not materialized:
        return "1. Review the evidence and add concrete steps."
    lines = []
    for step in materialized:
        detail = step.action
        if step.why:
            detail = "%s\nReason: %s" % (detail, step.why)
        lines.append("%s. %s" % (step.step, detail))
    return "\n".join(lines)


def render_skill_markdown(skill: SkillDocument) -> str:
    return """# {name}

## 判词
{summary}

## 元信息
- skill_id: {skill_id}
- version: {version}
- skill_type: {skill_type}
- audience: {audience}
- source_modality: {source_modality}
- review_status: {review_status}
- confidence: {confidence:.2f}
- created_at: {created_at}

## 目标
{goal}

## 触发条件
{trigger}

## 输入
{inputs}

## 前置条件
{preconditions}

## 操作步骤
{steps}

## 决策规则
{decision_rules}

## 反模式
{anti_patterns}

## 验证方式
{verification}

## 证据链
{evidence_refs}

## 标签
{tags}
""".format(
        name=skill.name,
        summary=skill.summary or "Pending summary.",
        skill_id=skill.skill_id,
        version=skill.version,
        skill_type=skill.skill_type.value,
        audience=skill.audience.value,
        source_modality=skill.source_modality.value,
        review_status=skill.review_status.value,
        confidence=skill.confidence,
        created_at=skill.created_at,
        goal=skill.goal,
        trigger=_render_list(skill.trigger),
        inputs=_render_list(skill.inputs),
        preconditions=_render_list(skill.preconditions),
        steps=_render_steps(skill.steps),
        decision_rules=_render_list(skill.decision_rules),
        anti_patterns=_render_list(skill.anti_patterns),
        verification=_render_list(skill.verification),
        evidence_refs=_render_list(skill.evidence_refs),
        tags=_render_list(skill.tags),
    )


def resolve_skill_markdown(publications: Sequence[Publication]) -> str | None:
    for publication in publications:
        if publication.publication_type != PublicationType.SKILL_MARKDOWN:
            continue
        if isinstance(publication.content, dict):
            text = publication.content.get('text')
            if isinstance(text, str) and text:
                return text
        if isinstance(publication.content, str) and publication.content:
            return publication.content
    return None


def render_skill_graph_markdown(graph: SkillGraph) -> str:
    from omni_skill_pipeline.transformers import skill_graph_to_document

    return render_skill_markdown(skill_graph_to_document(graph))


def render_skill_markdown_compat(
    *,
    publications: Sequence[Publication] | None = None,
    skill: SkillDocument | None = None,
    graph: SkillGraph | None = None,
) -> str:
    if publications:
        resolved = resolve_skill_markdown(publications)
        if resolved:
            return resolved
    if skill is not None:
        return render_skill_markdown(skill)
    if graph is not None:
        return render_skill_graph_markdown(graph)
    raise ValueError('render_skill_markdown_compat requires publications, skill, or graph.')
