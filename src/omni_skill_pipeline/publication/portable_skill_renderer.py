from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from omni_skill_pipeline.models import Modality, SkillDocument, SkillGraph
from omni_skill_pipeline.utils import unique_preserve_order

DEFAULT_PORTABLE_SKILL_LINE_LIMIT = 220
MIN_PORTABLE_SKILL_LINE_LIMIT = 21


@dataclass(frozen=True, slots=True)
class PortableSkillRenderResult:
    skill_markdown: str
    references: dict[str, str]
    description: str
    line_count: int
    line_limit: int


class PortableSkillRenderer(object):
    def __init__(self, *, line_limit: int = DEFAULT_PORTABLE_SKILL_LINE_LIMIT) -> None:
        if line_limit < MIN_PORTABLE_SKILL_LINE_LIMIT:
            raise ValueError(
                'Portable skill line limit must be >= %s (received %s).'
                % (MIN_PORTABLE_SKILL_LINE_LIMIT, line_limit)
            )
        self.line_limit = int(line_limit)

    def render(self, *, skill: SkillDocument, graph: SkillGraph) -> PortableSkillRenderResult:
        description = self._build_description(skill=skill, graph=graph)
        references = self._build_reference_documents(skill=skill, graph=graph)
        markdown = self._build_markdown(
            skill=skill,
            description=description,
            references=references,
            graph=graph,
        )
        line_count = len(markdown.splitlines())
        return PortableSkillRenderResult(
            skill_markdown=markdown,
            references=references,
            description=description,
            line_count=line_count,
            line_limit=self.line_limit,
        )

    def _build_markdown(
        self,
        *,
        skill: SkillDocument,
        description: str,
        references: dict[str, str],
        graph: SkillGraph,
    ) -> str:
        workflow_items = self._workflow_items(skill)
        decision_rule_items = self._decision_rule_items(skill=skill, graph=graph)
        validation_items = self._validation_items(skill)
        failure_mode_items = self._failure_mode_items(skill=skill, graph=graph)
        reference_items = self._reference_items(references)

        selected_items = self._select_section_items(
            workflow_items=workflow_items,
            decision_rule_items=decision_rule_items,
            validation_items=validation_items,
            failure_mode_items=failure_mode_items,
            reference_items=reference_items,
        )

        lines = [
            '---',
            'name: "%s"' % self._escape_yaml_inline(skill.name.strip() or 'untitled-skill'),
            'description: "%s"' % self._escape_yaml_inline(description),
            '---',
            '',
            '# %s' % (skill.name.strip() or 'Untitled Skill'),
            '',
            '## Workflow',
            *selected_items['workflow'],
            '',
            '## Decision Rules',
            *selected_items['decision_rules'],
            '',
            '## Validation',
            *selected_items['validation'],
            '',
            '## Failure Modes',
            *selected_items['failure_modes'],
            '',
            '## References',
            *selected_items['references'],
        ]
        return '\n'.join(lines) + '\n'

    def _select_section_items(
        self,
        *,
        workflow_items: list[str],
        decision_rule_items: list[str],
        validation_items: list[str],
        failure_mode_items: list[str],
        reference_items: list[str],
    ) -> dict[str, list[str]]:
        selected = {
            'workflow': [workflow_items[0]],
            'decision_rules': [decision_rule_items[0]],
            'validation': [validation_items[0]],
            'failure_modes': [failure_mode_items[0]],
            'references': [reference_items[0]],
        }
        extra_budget = self.line_limit - MIN_PORTABLE_SKILL_LINE_LIMIT
        if extra_budget <= 0:
            return selected

        extras = {
            'workflow': workflow_items[1:],
            'decision_rules': decision_rule_items[1:],
            'validation': validation_items[1:],
            'failure_modes': failure_mode_items[1:],
            'references': reference_items[1:],
        }
        fill_order = ['workflow', 'decision_rules', 'validation', 'failure_modes', 'references']
        for section in fill_order:
            for item in extras[section]:
                if extra_budget <= 0:
                    return selected
                selected[section].append(item)
                extra_budget -= 1
        return selected

    def _build_description(self, *, skill: SkillDocument, graph: SkillGraph) -> str:
        trigger_hints = unique_preserve_order(skill.trigger)
        if not trigger_hints:
            trigger_hints = unique_preserve_order(graph.trigger)
        if trigger_hints:
            use_case = trigger_hints[0]
        else:
            use_case = skill.goal
        summary = skill.summary.strip() or graph.summary.strip() or skill.goal.strip()
        text = 'Use when %s. %s' % (use_case, summary)
        return self._clip_sentence(text, max_chars=320)

    def _workflow_items(self, skill: SkillDocument) -> list[str]:
        steps = sorted(skill.steps, key=lambda item: item.step)
        items: list[str] = []
        for index, step in enumerate(steps, start=1):
            action = self._clip_sentence(step.action, max_chars=160)
            if step.why.strip():
                reason = self._clip_sentence(step.why, max_chars=96)
                items.append('%s. %s (Why: %s)' % (index, action, reason))
            else:
                items.append('%s. %s' % (index, action))
        if items:
            return items
        return ['1. Review the evidence artifacts and produce executable steps.']

    def _decision_rule_items(self, *, skill: SkillDocument, graph: SkillGraph) -> list[str]:
        items = unique_preserve_order(skill.decision_rules)
        if not items:
            for node in graph.decisions:
                condition = self._clip_sentence(node.condition, max_chars=120)
                decision = self._clip_sentence(node.decision, max_chars=120)
                if condition and decision:
                    items.append('%s -> %s' % (condition, decision))
                elif decision:
                    items.append(decision)
        if items:
            return ['- %s' % self._clip_sentence(item, max_chars=240) for item in items]
        return ['- No explicit branch rule was extracted; execute workflow order first.']

    def _validation_items(self, skill: SkillDocument) -> list[str]:
        if skill.verification:
            return ['- %s' % self._clip_sentence(item, max_chars=220) for item in skill.verification]
        return ['- Confirm each critical step maps back to evidence_refs before approval.']

    def _failure_mode_items(self, *, skill: SkillDocument, graph: SkillGraph) -> list[str]:
        items = list(unique_preserve_order(skill.anti_patterns))
        if not items:
            for node in graph.risks:
                risk = self._clip_sentence(node.risk, max_chars=120)
                mitigation = self._clip_sentence(node.mitigation, max_chars=120)
                if risk and mitigation:
                    items.append('%s; mitigate by %s.' % (risk, mitigation))
                elif risk:
                    items.append(risk)
        if items:
            return ['- %s' % self._clip_sentence(item, max_chars=240) for item in items]
        return ['- Do not auto-publish trial output before human review approval.']

    def _reference_items(self, references: dict[str, str]) -> list[str]:
        links: list[str] = []
        for relative_path in sorted(references.keys()):
            name = relative_path.split('/')[-1]
            title = name.replace('.md', '').replace('-', ' ').title()
            links.append('- [%s](%s)' % (title, relative_path))
        if links:
            return links
        return ['- [Evidence Digest](references/evidence.md)']

    def _build_reference_documents(self, *, skill: SkillDocument, graph: SkillGraph) -> dict[str, str]:
        modalities = self._resolve_modalities(skill=skill, graph=graph)
        evidence_refs = self._collect_evidence_refs(skill=skill, graph=graph)
        evidence_lines = [
            '# Evidence Digest',
            '',
            '## Context',
            '- review_status: `%s`' % skill.review_status.value,
            '- source_modalities: `%s`' % ', '.join(modalities),
            '- evidence_ref_count: `%s`' % len(evidence_refs),
            '',
            '## Evidence References',
        ]
        if evidence_refs:
            evidence_lines.extend('- `%s`' % item for item in evidence_refs)
        else:
            evidence_lines.append('- No explicit evidence references were provided.')

        if 'audio' in modalities or 'video' in modalities:
            evidence_lines.extend(
                [
                    '',
                    '## Transcript Notes',
                    '- Keep long transcript excerpts in this references file, not in main `SKILL.md`.',
                ]
            )
        if 'image' in modalities or 'video' in modalities:
            evidence_lines.extend(
                [
                    '',
                    '## OCR Notes',
                    '- Keep OCR details and uncertain fragments here for reviewer traceability.',
                ]
            )
        if 'video' in modalities:
            evidence_lines.extend(
                [
                    '',
                    '## Keyframe Notes',
                    '- Keep keyframe-level observations here and summarize only stable steps in main skill.',
                ]
            )

        references = {'references/evidence.md': '\n'.join(evidence_lines) + '\n'}
        references['references/examples.md'] = self._build_examples_reference(graph=graph)
        return references

    def _build_examples_reference(self, *, graph: SkillGraph) -> str:
        lines = ['# Examples', '']
        if graph.examples:
            for index, node in enumerate(graph.examples, start=1):
                lines.append('%s. [%s] %s' % (index, node.classification, self._clip_sentence(node.example, max_chars=220)))
            return '\n'.join(lines) + '\n'
        lines.append('No explicit example nodes were extracted for this skill.')
        return '\n'.join(lines) + '\n'

    def _resolve_modalities(self, *, skill: SkillDocument, graph: SkillGraph) -> list[str]:
        values: list[str] = [skill.source_modality.value]
        values.extend(item.value if isinstance(item, Modality) else str(item) for item in graph.source_modalities)
        return unique_preserve_order(values)

    def _collect_evidence_refs(self, *, skill: SkillDocument, graph: SkillGraph) -> list[str]:
        refs = list(skill.evidence_refs)
        refs.extend(graph.evidence_refs)
        for item in graph.steps:
            refs.extend(item.evidence_refs)
        for item in graph.decisions:
            refs.extend(item.evidence_refs)
        for item in graph.verifications:
            refs.extend(item.evidence_refs)
        for item in graph.risks:
            refs.extend(item.evidence_refs)
        return unique_preserve_order(refs)

    def _escape_yaml_inline(self, value: str) -> str:
        escaped = str(value).replace('\\', '\\\\').replace('"', '\\"')
        return escaped.replace('\n', ' ').strip() or 'untitled'

    def _clip_sentence(self, text: str, *, max_chars: int) -> str:
        normalized = ' '.join(str(text).split())
        if len(normalized) <= max_chars:
            return normalized
        return normalized[: max_chars - 3].rstrip() + '...'
