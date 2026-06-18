from __future__ import annotations

from typing import Any, Sequence

from omni_skill_pipeline.models import (
    Corpus,
    EvidenceNode,
    EvidenceUnit,
    Insight,
    Publication,
    ReviewTask,
    SkillDocument,
    SkillGraph,
    utc_now_iso,
)
from omni_skill_pipeline.utils import unique_preserve_order
from omni_skill_pipeline.validation import collect_trial_security_risk_labels


class ReviewerPacketBuilder(object):
    def build(
        self,
        *,
        skill: SkillDocument,
        skill_markdown: str,
        evidence_units: Sequence[EvidenceUnit],
        insights: Sequence[Insight],
        quality_scores: dict[str, Any],
        review_task: ReviewTask,
        review_policy: dict[str, Any],
        review_feedback: dict[str, Any],
        publications: Sequence[Publication],
        skill_graph: SkillGraph | None = None,
        corpus: Corpus | None = None,
        evidence_nodes: Sequence[EvidenceNode] = (),
        corpus_assets: Sequence[dict[str, Any]] = (),
        cross_asset_refs: Sequence[dict[str, Any]] = (),
        request_payload: dict[str, Any] | None = None,
        references_payload: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        modalities = self._resolve_modalities(skill=skill, skill_graph=skill_graph, corpus=corpus)
        evidence_links = self._build_evidence_links(evidence_units=evidence_units, evidence_nodes=evidence_nodes)
        packet = {
            'schema_version': 'reviewer_packet.v1',
            'created_at': utc_now_iso(),
            'skill_id': skill.skill_id,
            'skill_name': skill.name,
            'review_task_id': review_task.review_task_id,
            'review_status': review_task.status.value,
            'decision': review_task.decision.value,
            'reason_codes': list(review_task.reason_codes),
            'input_summary': self._build_input_summary(
                skill=skill,
                corpus=corpus,
                modalities=modalities,
                evidence_units=evidence_units,
                evidence_nodes=evidence_nodes,
                corpus_assets=corpus_assets,
            ),
            'evidence_links': evidence_links,
            'generated_skill': self._build_generated_skill_payload(
                skill=skill,
                skill_markdown=skill_markdown,
                publications=publications,
                skill_graph=skill_graph,
            ),
            'quality_scores': dict(quality_scores),
            'review_policy': dict(review_policy),
            'review_feedback': dict(review_feedback),
            'risk_flags': self._build_risk_flags(
                modalities=modalities,
                review_task=review_task,
                quality_scores=quality_scores,
                cross_asset_refs=cross_asset_refs,
                skill_markdown=skill_markdown,
                request_payload=request_payload,
                references_payload=references_payload,
            ),
            'approval_checklist': self._build_approval_checklist(
                modalities=modalities,
                has_cross_asset_refs=bool(cross_asset_refs),
            ),
        }
        if corpus is not None:
            packet['corpus'] = {
                'corpus_id': corpus.corpus_id,
                'name': corpus.name,
                'asset_count': len(corpus.assets),
                'tags': list(corpus.tags),
            }
        if cross_asset_refs:
            packet['cross_asset_conflicts'] = list(cross_asset_refs)
        return packet

    def _resolve_modalities(
        self,
        *,
        skill: SkillDocument,
        skill_graph: SkillGraph | None,
        corpus: Corpus | None,
    ) -> list[str]:
        modalities: list[str] = []
        if corpus is not None:
            modalities.extend(item.modality.value for item in corpus.assets)
        source_modalities = getattr(skill_graph, 'source_modalities', []) if skill_graph is not None else []
        modalities.extend(getattr(item, 'value', str(item)) for item in source_modalities)
        modalities.append(skill.source_modality.value)
        return unique_preserve_order(modalities)

    def _build_input_summary(
        self,
        *,
        skill: SkillDocument,
        corpus: Corpus | None,
        modalities: Sequence[str],
        evidence_units: Sequence[EvidenceUnit],
        evidence_nodes: Sequence[EvidenceNode],
        corpus_assets: Sequence[dict[str, Any]],
    ) -> dict[str, Any]:
        return {
            'title': skill.name,
            'goal': skill.goal,
            'summary': skill.summary,
            'modalities': list(modalities),
            'evidence_unit_count': len(evidence_units),
            'evidence_node_count': len(evidence_nodes),
            'asset_count': len(corpus.assets) if corpus is not None else 1,
            'asset_refs': list(corpus_assets),
        }

    def _build_evidence_links(
        self,
        *,
        evidence_units: Sequence[EvidenceUnit],
        evidence_nodes: Sequence[EvidenceNode],
    ) -> list[dict[str, Any]]:
        node_index = {item.evidence_id: item for item in evidence_nodes}
        links: list[dict[str, Any]] = []
        for unit in evidence_units:
            node = node_index.get(unit.evidence_id)
            links.append(
                {
                    'evidence_id': unit.evidence_id,
                    'asset_id': unit.asset_id,
                    'span_ref': unit.span_ref,
                    'content_type': unit.content_type.value,
                    'modality': node.modality.value if node is not None else '',
                    'confidence': unit.confidence,
                    'summary': self._summarize_text(unit.content),
                    'tags': list(unit.tags),
                }
            )
        return links

    def _build_generated_skill_payload(
        self,
        *,
        skill: SkillDocument,
        skill_markdown: str,
        publications: Sequence[Publication],
        skill_graph: SkillGraph | None,
    ) -> dict[str, Any]:
        return {
            'skill': skill.to_dict(),
            'skill_markdown_preview': self._summarize_text(skill_markdown, max_chars=1200),
            'step_count': len(skill.steps),
            'decision_rule_count': len(skill.decision_rules),
            'verification_count': len(skill.verification),
            'publication_types': [item.publication_type.value for item in publications],
            'graph_id': str(getattr(skill_graph, 'graph_id', '')) if skill_graph is not None else '',
        }

    def _build_risk_flags(
        self,
        *,
        modalities: Sequence[str],
        review_task: ReviewTask,
        quality_scores: dict[str, Any],
        cross_asset_refs: Sequence[dict[str, Any]],
        skill_markdown: str,
        request_payload: dict[str, Any] | None,
        references_payload: dict[str, str] | None,
    ) -> list[dict[str, str]]:
        flags: list[dict[str, str]] = []
        for code in review_task.reason_codes:
            flags.append({'code': str(code), 'severity': self._severity_for_reason(code), 'source': 'review_policy'})
        if 'video' in modalities:
            flags.append({'code': 'video_requires_keyframe_review', 'severity': 'medium', 'source': 'modality'})
        if 'image' in modalities:
            flags.append({'code': 'image_requires_ocr_review', 'severity': 'medium', 'source': 'modality'})
        if 'audio' in modalities:
            flags.append({'code': 'audio_requires_transcript_review', 'severity': 'medium', 'source': 'modality'})
        if 'tabular' in modalities:
            flags.append({'code': 'tabular_requires_metric_review', 'severity': 'medium', 'source': 'modality'})
        if cross_asset_refs:
            flags.append({'code': 'cross_asset_consistency_required', 'severity': 'medium', 'source': 'corpus'})
        try:
            overall_score = float(quality_scores.get('overall_score', 0.0))
        except (TypeError, ValueError):
            overall_score = 0.0
        if overall_score < 0.5:
            flags.append({'code': 'low_overall_quality_score', 'severity': 'high', 'source': 'quality_score'})
        flags.extend(
            collect_trial_security_risk_labels(
                skill_markdown=skill_markdown,
                request_payload=request_payload or {},
                references=references_payload or {},
            )
        )
        return self._dedupe_flags(flags)

    def _build_approval_checklist(
        self,
        *,
        modalities: Sequence[str],
        has_cross_asset_refs: bool,
    ) -> list[dict[str, Any]]:
        checks = [
            {
                'check_id': 'factual_accuracy',
                'label': 'Confirm generated skill facts match evidence.',
                'required': True,
            },
            {
                'check_id': 'actionability',
                'label': 'Confirm steps are concrete and executable by the target agent.',
                'required': True,
            },
            {
                'check_id': 'dangerous_operations',
                'label': 'Confirm dangerous commands or production changes are clearly guarded.',
                'required': True,
            },
            {
                'check_id': 'description_trigger',
                'label': 'Confirm description would trigger only for the intended scenario.',
                'required': True,
            },
        ]
        modality_checks = {
            'audio': ('transcript_check', 'Compare decisions against transcript excerpts.'),
            'image': ('ocr_visual_check', 'Confirm OCR and visual interpretation.'),
            'video': ('keyframe_sequence_check', 'Inspect keyframes, transcript, OCR, and procedure order.'),
            'tabular': ('metric_check', 'Validate metric names, units, thresholds, and baseline windows.'),
        }
        for modality in modalities:
            item = modality_checks.get(modality)
            if item is None:
                continue
            checks.append({'check_id': item[0], 'label': item[1], 'required': True})
        if has_cross_asset_refs:
            checks.append(
                {
                    'check_id': 'cross_asset_consistency',
                    'label': 'Confirm source priority, conflicts, and cross-asset consistency.',
                    'required': True,
                }
            )
        return checks

    def _severity_for_reason(self, reason_code: str) -> str:
        normalized = str(reason_code).strip().upper()
        if 'CRITICAL' in normalized or normalized.startswith('R_'):
            return 'high'
        return 'medium'

    def _dedupe_flags(self, flags: Sequence[dict[str, str]]) -> list[dict[str, str]]:
        output: list[dict[str, str]] = []
        seen: set[tuple[str, str]] = set()
        for item in flags:
            key = (str(item.get('code', '')), str(item.get('source', '')))
            if key in seen:
                continue
            seen.add(key)
            output.append(dict(item))
        return output

    def _summarize_text(self, text: str, *, max_chars: int = 240) -> str:
        normalized = ' '.join(str(text).split())
        if len(normalized) <= max_chars:
            return normalized
        return normalized[: max_chars - 3].rstrip() + '...'
