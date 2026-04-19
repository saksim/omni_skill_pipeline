from __future__ import annotations

import re
from typing import Iterable, Sequence

from omni_skill_pipeline.interfaces import InsightExtractor, SkillComposer
from omni_skill_pipeline.models import (
    DistillGoal,
    EvidenceUnit,
    Insight,
    InsightType,
    Modality,
    SkillDocument,
    SkillStep,
    SkillType,
)
from omni_skill_pipeline.utils import split_sentences, unique_preserve_order


STEP_LINE_RE = re.compile(r'^\s*(?:\d+[.)]|[-*+])\s+(?P<text>.+)$')
DECISION_KEYWORDS = ('if ', 'when ', 'unless ', 'should ', 'must ', 'if you', '如果', '若', '当', '需要', '必须')
ANTI_KEYWORDS = ('avoid', 'do not', "don't", 'never', '不要', '避免', '禁忌', '误区', '常见错误')
VERIFY_KEYWORDS = ('verify', 'check', 'confirm', 'test', '验证', '检查', '确认', '测试')
PRECONDITION_KEYWORDS = ('before', 'prepare', 'prerequisite', '先', '准备', '前置', '前提')


class HeuristicInsightExtractor(InsightExtractor):
    def extract(self, evidence_units: Sequence[EvidenceUnit]) -> list[Insight]:
        insights: list[Insight] = []
        for evidence in evidence_units:
            insights.extend(self._extract_from_evidence(evidence))
        if insights:
            return insights
        if not evidence_units:
            return []
        first = evidence_units[0]
        return [
            Insight(
                insight_type=InsightType.CONCEPT,
                summary=first.content[:240].strip(),
                evidence_refs=[first.evidence_id],
                confidence=0.65,
            )
        ]

    def _extract_from_evidence(self, evidence: EvidenceUnit) -> list[Insight]:
        items: list[Insight] = []
        for line in self._candidate_lines(evidence.content):
            normalized = line.strip()
            lowered = normalized.lower()
            evidence_ref = [evidence.evidence_id]
            step_match = STEP_LINE_RE.match(normalized)
            if step_match:
                items.append(
                    Insight(
                        insight_type=InsightType.PROCEDURE,
                        summary=step_match.group('text').strip(),
                        evidence_refs=evidence_ref,
                        confidence=0.82,
                    )
                )
                continue
            if any(keyword in lowered for keyword in (item.lower() for item in ANTI_KEYWORDS)):
                items.append(Insight(InsightType.ANTI_PATTERN, normalized, evidence_ref, confidence=0.78))
                continue
            if any(keyword in lowered for keyword in (item.lower() for item in VERIFY_KEYWORDS)):
                items.append(Insight(InsightType.VERIFICATION, normalized, evidence_ref, confidence=0.75))
                continue
            if any(keyword in lowered for keyword in (item.lower() for item in PRECONDITION_KEYWORDS)):
                items.append(Insight(InsightType.PRECONDITION, normalized, evidence_ref, confidence=0.72))
                continue
            if any(keyword in lowered for keyword in (item.lower() for item in DECISION_KEYWORDS)):
                items.append(Insight(InsightType.RULE, normalized, evidence_ref, confidence=0.74))
        return items

    def _candidate_lines(self, text: str) -> list[str]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        candidates: list[str] = []
        for line in lines:
            candidates.append(line)
            if len(line) > 120:
                candidates.extend(split_sentences(line))
        return unique_preserve_order(candidates)


class HeuristicSkillComposer(SkillComposer):
    def compose(
        self,
        title_hint: str,
        goal: DistillGoal,
        modality: Modality,
        evidence_units: Sequence[EvidenceUnit],
        insights: Sequence[Insight],
    ) -> SkillDocument:
        insights_by_type = self._group_insights(insights)
        procedures = insights_by_type.get(InsightType.PROCEDURE, [])
        rules = insights_by_type.get(InsightType.RULE, [])
        anti_patterns = insights_by_type.get(InsightType.ANTI_PATTERN, [])
        verification = insights_by_type.get(InsightType.VERIFICATION, [])
        preconditions = insights_by_type.get(InsightType.PRECONDITION, [])
        summary = self._build_summary(evidence_units)
        steps = self._build_steps(procedures, evidence_units)

        if not verification:
            verification = [
                'Confirm each key conclusion can be traced back to evidence_refs.',
                'Run one manual rehearsal to verify the steps are executable.',
            ]
        if not preconditions:
            preconditions = ['Confirm the source material matches the declared distillation goal.']

        return SkillDocument(
            name=self._select_name(title_hint, evidence_units, goal),
            goal=self._build_goal(goal, summary),
            source_modality=modality,
            skill_type=self._select_skill_type(modality, steps, rules, anti_patterns),
            audience=goal.audience,
            trigger=self._build_trigger(goal, modality),
            inputs=self._build_inputs(modality),
            preconditions=unique_preserve_order(preconditions),
            steps=steps,
            decision_rules=unique_preserve_order(rules),
            anti_patterns=unique_preserve_order(anti_patterns),
            verification=unique_preserve_order(verification),
            evidence_refs=self._collect_evidence_refs(evidence_units),
            confidence=self._estimate_confidence(evidence_units, steps, rules, verification),
            summary=summary,
            tags=unique_preserve_order([goal.domain, modality.value, goal.goal_type.value, 'heuristic']),
        )

    def _group_insights(self, insights: Sequence[Insight]) -> dict[InsightType, list[str]]:
        grouped: dict[InsightType, list[str]] = {}
        for insight in insights:
            grouped.setdefault(insight.insight_type, []).append(insight.summary)
        return grouped

    def _build_summary(self, evidence_units: Sequence[EvidenceUnit]) -> str:
        if not evidence_units:
            return 'No evidence provided.'
        seed = evidence_units[0].content.replace('\n', ' ').strip()
        return seed[:280] if seed else 'No summary extracted.'

    def _build_steps(self, procedures: Sequence[str], evidence_units: Sequence[EvidenceUnit]) -> list[SkillStep]:
        actions = unique_preserve_order(procedures)
        if not actions:
            actions = self._fallback_steps(evidence_units)
        return [
            SkillStep(
                step=index,
                action=action,
                why='Derived from normalized evidence and intended to preserve the original reasoning chain.',
            )
            for index, action in enumerate(actions[:8], start=1)
        ]

    def _fallback_steps(self, evidence_units: Sequence[EvidenceUnit]) -> list[str]:
        fallback_steps: list[str] = []
        for evidence in evidence_units[:3]:
            sentences = split_sentences(evidence.content)
            if sentences:
                fallback_steps.append(sentences[0])
        return unique_preserve_order(fallback_steps)

    def _collect_evidence_refs(self, evidence_units: Sequence[EvidenceUnit]) -> list[str]:
        return unique_preserve_order('%s@%s' % (unit.evidence_id, unit.span_ref) for unit in evidence_units[:16])

    def _select_name(self, title_hint: str, evidence_units: Sequence[EvidenceUnit], goal: DistillGoal) -> str:
        if title_hint and title_hint.strip():
            return title_hint.strip()
        if evidence_units:
            sentence = split_sentences(evidence_units[0].content)
            if sentence:
                return sentence[0][:60]
        return '%s skill' % goal.domain.replace('_', ' ').strip()

    def _build_goal(self, goal: DistillGoal, summary: str) -> str:
        return 'Distill %s material into a %s for %s. Seed: %s' % (
            goal.domain,
            goal.goal_type.value,
            goal.audience.value,
            summary[:120],
        )

    def _build_trigger(self, goal: DistillGoal, modality: Modality) -> list[str]:
        return ['Use when you need to convert %s evidence into a reusable %s.' % (modality.value, goal.goal_type.value)]

    def _build_inputs(self, modality: Modality) -> list[str]:
        if modality == Modality.AUDIO:
            return ['Audio source or transcript', 'Distillation goal']
        if modality == Modality.VIDEO:
            return ['Video source', 'Distillation goal', 'Keyframe/OCR evidence']
        if modality == Modality.IMAGE:
            return ['Image source', 'Distillation goal']
        if modality == Modality.TABULAR:
            return ['Structured table or time-series dataset', 'Distillation goal']
        return ['Source document', 'Distillation goal']

    def _select_skill_type(
        self,
        modality: Modality,
        steps: Sequence[SkillStep],
        rules: Sequence[str],
        anti_patterns: Sequence[str],
    ) -> SkillType:
        if rules and len(steps) <= 1:
            return SkillType.DECISION
        if anti_patterns and not steps:
            return SkillType.DIAGNOSTIC
        if modality == Modality.TABULAR:
            return SkillType.ANALYSIS
        return SkillType.PROCEDURE

    def _estimate_confidence(
        self,
        evidence_units: Sequence[EvidenceUnit],
        steps: Sequence[SkillStep],
        rules: Sequence[str],
        verification: Sequence[str],
    ) -> float:
        score = 0.35
        score += min(0.25, len(evidence_units) * 0.04)
        score += min(0.2, len(steps) * 0.05)
        if rules:
            score += 0.1
        if verification:
            score += 0.1
        return round(min(score, 0.95), 2)
