from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from omni_skill_pipeline.models import utc_now_iso
from omni_skill_pipeline.quality.feedback import ReviewFeedbackEngine
from omni_skill_pipeline.quality.feedback_consumer import ReviewFeedbackConsumer
from omni_skill_pipeline.utils import slugify, unique_preserve_order


REVIEW_OUTCOME_TO_DECISION = {
    'approved': 'auto_publish',
    'rejected': 'reject',
}


@dataclass(frozen=True, slots=True)
class QualityFeedbackLoopConfig:
    repeat_threshold: int = 2
    reviewer_edit_distance_threshold: float = 25.0


class QualityFeedbackLoopBuilder(object):
    """Aggregate trial-loop feedback into remediation, regression, and calibration artifacts."""

    def __init__(self, config: QualityFeedbackLoopConfig | None = None) -> None:
        self.config = config or QualityFeedbackLoopConfig()
        self.feedback_engine = ReviewFeedbackEngine()
        self.feedback_consumer = ReviewFeedbackConsumer()

    def build_from_run_report(self, run_report: dict[str, Any], *, base_dir: Path | None = None) -> dict[str, Any]:
        if not isinstance(run_report, dict):
            raise ValueError('run_report must be a JSON object.')
        samples = run_report.get('samples')
        if not isinstance(samples, list) or not samples:
            raise ValueError('run_report.samples must be a non-empty list.')

        bundle_base_dir = Path(base_dir).resolve() if base_dir is not None else None
        sample_records: list[dict[str, Any]] = []
        defect_occurrences: list[dict[str, Any]] = []

        for item in samples:
            if not isinstance(item, dict):
                continue
            sample_id = str(item.get('sample_id', '')).strip()
            if not sample_id:
                continue
            modality = str(item.get('modality', 'unknown')).strip().lower() or 'unknown'
            loop_metrics = item.get('loop_metrics') if isinstance(item.get('loop_metrics'), dict) else {}
            approved_bundle_path = str(item.get('approved_bundle_path', '')).strip()
            bundle_payload = self._load_bundle_payload(approved_bundle_path, base_dir=bundle_base_dir)

            feedback_payload = self._resolve_review_feedback(bundle_payload)
            if feedback_payload is None:
                continue
            quality_scores = self._resolve_quality_scores(bundle_payload)
            plan = self.feedback_consumer.consume(feedback_payload).to_dict()

            sample_records.append(
                {
                    'sample_id': sample_id,
                    'modality': modality,
                    'review_outcome': str(loop_metrics.get('review_outcome', '')).strip().lower(),
                    'review_feedback': feedback_payload,
                    'quality_scores': quality_scores,
                    'remediation_plan': plan,
                    'reviewer_edit_distance_pct': self._to_non_negative_float(
                        loop_metrics.get('reviewer_edit_distance_pct', 0.0)
                    ),
                }
            )
            defect_occurrences.extend(
                self._extract_defect_occurrences(
                    sample_id=sample_id,
                    modality=modality,
                    feedback_payload=feedback_payload,
                    loop_metrics=loop_metrics,
                )
            )

        remediation_plans = [record['remediation_plan'] for record in sample_records]
        regression_cases = self._build_regression_cases(sample_records=sample_records, defect_occurrences=defect_occurrences)
        calibration_manifest = self._build_calibration_manifest(sample_records=sample_records)
        summary = self._build_summary(
            sample_records=sample_records,
            remediation_plans=remediation_plans,
            regression_cases=regression_cases,
            calibration_manifest=calibration_manifest,
        )

        return {
            'schema_version': 'quality_feedback_loop.v1',
            'generated_at_utc': utc_now_iso(),
            'source_run_id': str(run_report.get('run_id', '')).strip(),
            'config': {
                'repeat_threshold': int(self.config.repeat_threshold),
                'reviewer_edit_distance_threshold': float(self.config.reviewer_edit_distance_threshold),
            },
            'summary': summary,
            'remediation_plans': remediation_plans,
            'regression_cases': regression_cases,
            'calibration_manifest': calibration_manifest,
        }

    def render_summary_markdown(self, report: dict[str, Any]) -> str:
        summary = report.get('summary', {}) if isinstance(report, dict) else {}
        lines = [
            '# Quality Feedback Loop Summary',
            '',
            '- Source run id: `%s`' % str(report.get('source_run_id', '')).strip(),
            '- Samples analyzed: `%s`' % str(summary.get('sample_count', 0)),
            '- Remediation plans generated: `%s`' % str(summary.get('remediation_plan_count', 0)),
            '- Regression cases generated: `%s`' % str(summary.get('regression_case_count', 0)),
            '- Calibration samples generated: `%s`' % str(summary.get('calibration_sample_count', 0)),
            '',
            '## Repeated Defects',
        ]
        top_repeated = summary.get('top_repeated_defects', []) if isinstance(summary, dict) else []
        if not top_repeated:
            lines.append('- No repeated quality defects detected for current thresholds.')
        else:
            for item in top_repeated:
                lines.append(
                    '- `%s`: `%s` occurrences across `%s` samples'
                    % (
                        str(item.get('defect_key', 'unknown')),
                        str(item.get('occurrence_count', 0)),
                        str(item.get('sample_count', 0)),
                    )
                )
        return '\n'.join(lines).strip() + '\n'

    def _resolve_review_feedback(self, bundle_payload: dict[str, Any]) -> dict[str, Any] | None:
        adapter_metadata = bundle_payload.get('adapter_metadata') if isinstance(bundle_payload.get('adapter_metadata'), dict) else {}
        raw_feedback = adapter_metadata.get('review_feedback')
        if isinstance(raw_feedback, dict):
            feedback_payload = dict(raw_feedback)
            feedback_payload.setdefault('review_task_id', self._resolve_review_task_id(bundle_payload))
            feedback_payload.setdefault('skill_id', self._resolve_skill_id(bundle_payload))
            feedback_payload.setdefault('decision', self._resolve_review_decision(bundle_payload))
            feedback_payload.setdefault('status', self._resolve_review_status(bundle_payload))
            feedback_payload.setdefault('reason_codes', self._resolve_reason_codes(bundle_payload))
            return feedback_payload

        raw_review_task = adapter_metadata.get('review_task')
        if not isinstance(raw_review_task, dict):
            return None
        try:
            from omni_skill_pipeline.models import ReviewTask, ReviewDecision, ReviewStatus

            review_task = ReviewTask(
                skill_id=str(raw_review_task.get('skill_id', '')).strip() or self._resolve_skill_id(bundle_payload),
                decision=ReviewDecision(str(raw_review_task.get('decision', 'review_required')).strip().lower()),
                reason_codes=self._resolve_reason_codes(bundle_payload),
                revision_suggestions=[
                    str(item).strip()
                    for item in raw_review_task.get('revision_suggestions', [])
                    if str(item).strip()
                ],
                score_snapshot={
                    str(key): float(value)
                    for key, value in raw_review_task.get('score_snapshot', {}).items()
                    if self._is_number(value)
                }
                if isinstance(raw_review_task.get('score_snapshot'), dict)
                else {},
                thresholds={
                    str(key): float(value)
                    for key, value in raw_review_task.get('thresholds', {}).items()
                    if self._is_number(value)
                }
                if isinstance(raw_review_task.get('thresholds'), dict)
                else {},
                review_notes=str(raw_review_task.get('review_notes', '')).strip(),
                status=ReviewStatus(str(raw_review_task.get('status', 'review_pending')).strip().lower()),
                review_task_id=str(raw_review_task.get('review_task_id', '')).strip() or self._resolve_review_task_id(bundle_payload),
            )
        except Exception:
            return None
        return self.feedback_engine.build(review_task).to_dict()

    def _resolve_quality_scores(self, bundle_payload: dict[str, Any]) -> dict[str, float]:
        adapter_metadata = bundle_payload.get('adapter_metadata') if isinstance(bundle_payload.get('adapter_metadata'), dict) else {}
        raw_scores = adapter_metadata.get('quality_scores', {})
        if not isinstance(raw_scores, dict):
            return {}
        output: dict[str, float] = {}
        for key in (
            'traceability_score',
            'actionability_score',
            'coverage_score',
            'consistency_score',
            'noise_score',
            'novelty_score',
            'overall_score',
        ):
            output[key] = self._clamp_score(raw_scores.get(key, 0.0))
        return output

    def _extract_defect_occurrences(
        self,
        *,
        sample_id: str,
        modality: str,
        feedback_payload: dict[str, Any],
        loop_metrics: dict[str, Any],
    ) -> list[dict[str, Any]]:
        occurrences: list[dict[str, Any]] = []
        reason_codes = [str(item).strip() for item in feedback_payload.get('reason_codes', []) if str(item).strip()]
        for reason_code in reason_codes:
            if reason_code.startswith('Q_') or reason_code.startswith('R_'):
                occurrences.append(
                    {
                        'defect_key': reason_code,
                        'sample_id': sample_id,
                        'modality': modality,
                        'source': 'review_reason_code',
                    }
                )

        reviewer_edit_distance = self._to_non_negative_float(loop_metrics.get('reviewer_edit_distance_pct', 0.0))
        if reviewer_edit_distance >= float(self.config.reviewer_edit_distance_threshold):
            occurrences.append(
                {
                    'defect_key': 'REVIEWER_EDIT_DISTANCE_HIGH',
                    'sample_id': sample_id,
                    'modality': modality,
                    'source': 'loop_metric',
                }
            )

        review_outcome = str(loop_metrics.get('review_outcome', '')).strip().lower()
        if review_outcome == 'rejected':
            occurrences.append(
                {
                    'defect_key': 'REVIEW_OUTCOME_REJECTED',
                    'sample_id': sample_id,
                    'modality': modality,
                    'source': 'loop_metric',
                }
            )
        return occurrences

    def _build_regression_cases(
        self,
        *,
        sample_records: list[dict[str, Any]],
        defect_occurrences: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for occurrence in defect_occurrences:
            defect_key = str(occurrence.get('defect_key', '')).strip()
            if not defect_key:
                continue
            grouped.setdefault(defect_key, []).append(occurrence)

        plan_by_sample = {record['sample_id']: record['remediation_plan'] for record in sample_records}
        cases: list[dict[str, Any]] = []
        for defect_key, occurrences in sorted(grouped.items(), key=lambda item: item[0]):
            sample_ids = unique_preserve_order(str(item.get('sample_id', '')) for item in occurrences)
            modalities = unique_preserve_order(str(item.get('modality', '')) for item in occurrences)
            if len(sample_ids) < max(1, int(self.config.repeat_threshold)):
                continue

            action_codes: list[str] = []
            for sample_id in sample_ids:
                remediation_plan = plan_by_sample.get(sample_id, {})
                steps = remediation_plan.get('steps', []) if isinstance(remediation_plan, dict) else []
                for step in steps:
                    if not isinstance(step, dict):
                        continue
                    action_code = str(step.get('action_code', '')).strip()
                    if action_code:
                        action_codes.append(action_code)
            recommended_actions = unique_preserve_order(action_codes)

            case_id = 'regression-%s' % slugify(defect_key)
            cases.append(
                {
                    'case_id': case_id,
                    'defect_key': defect_key,
                    'occurrence_count': len(occurrences),
                    'sample_ids': sample_ids,
                    'modalities': modalities,
                    'sources': unique_preserve_order(str(item.get('source', '')) for item in occurrences),
                    'recommended_actions': recommended_actions,
                    'recommended_action_count': len(recommended_actions),
                }
            )
        return cases

    def _build_calibration_manifest(self, *, sample_records: list[dict[str, Any]]) -> dict[str, Any]:
        calibration_samples: list[dict[str, Any]] = []
        for record in sample_records:
            sample_id = str(record.get('sample_id', '')).strip()
            if not sample_id:
                continue
            quality_scores = record.get('quality_scores') if isinstance(record.get('quality_scores'), dict) else {}
            review_outcome = str(record.get('review_outcome', '')).strip().lower()
            reviewer_decision = REVIEW_OUTCOME_TO_DECISION.get(review_outcome, 'review_required')
            confidence = 0.85 if reviewer_decision == 'auto_publish' else 0.95 if reviewer_decision == 'reject' else 0.75
            calibration_samples.append(
                {
                    'sample_id': sample_id,
                    'modality': str(record.get('modality', 'unknown')),
                    'quality_scores': dict(quality_scores),
                    'reviewer_judgement': {
                        'decision': reviewer_decision,
                        'confidence': confidence,
                        'notes': 'Derived from loop review_outcome=%s' % (review_outcome or 'unknown'),
                    },
                }
            )

        return {
            'manifest_id': 'quality-feedback-loop-calibration',
            'manifest_version': '1.0',
            'generated_at_utc': utc_now_iso(),
            'description': 'Calibration dataset generated from controlled-trial feedback loop outputs.',
            'samples': calibration_samples,
        }

    def _build_summary(
        self,
        *,
        sample_records: list[dict[str, Any]],
        remediation_plans: list[dict[str, Any]],
        regression_cases: list[dict[str, Any]],
        calibration_manifest: dict[str, Any],
    ) -> dict[str, Any]:
        decision_counts: dict[str, int] = {}
        for plan in remediation_plans:
            decision = str(plan.get('decision', '')).strip().lower() or 'unknown'
            decision_counts[decision] = decision_counts.get(decision, 0) + 1

        top_repeated = sorted(
            regression_cases,
            key=lambda item: (-int(item.get('occurrence_count', 0)), str(item.get('defect_key', ''))),
        )[:5]

        return {
            'sample_count': len(sample_records),
            'remediation_plan_count': len(remediation_plans),
            'regression_case_count': len(regression_cases),
            'calibration_sample_count': len(calibration_manifest.get('samples', [])),
            'decision_counts': decision_counts,
            'top_repeated_defects': [
                {
                    'defect_key': str(item.get('defect_key', '')),
                    'occurrence_count': int(item.get('occurrence_count', 0)),
                    'sample_count': len(item.get('sample_ids', [])) if isinstance(item.get('sample_ids'), list) else 0,
                }
                for item in top_repeated
            ],
        }

    def _resolve_skill_id(self, bundle_payload: dict[str, Any]) -> str:
        skill = bundle_payload.get('skill') if isinstance(bundle_payload.get('skill'), dict) else {}
        return str(skill.get('skill_id', '')).strip()

    def _resolve_review_task_id(self, bundle_payload: dict[str, Any]) -> str:
        adapter_metadata = bundle_payload.get('adapter_metadata') if isinstance(bundle_payload.get('adapter_metadata'), dict) else {}
        review_task = adapter_metadata.get('review_task') if isinstance(adapter_metadata.get('review_task'), dict) else {}
        return str(review_task.get('review_task_id', '')).strip()

    def _resolve_review_decision(self, bundle_payload: dict[str, Any]) -> str:
        adapter_metadata = bundle_payload.get('adapter_metadata') if isinstance(bundle_payload.get('adapter_metadata'), dict) else {}
        review_task = adapter_metadata.get('review_task') if isinstance(adapter_metadata.get('review_task'), dict) else {}
        return str(review_task.get('decision', 'review_required')).strip().lower() or 'review_required'

    def _resolve_review_status(self, bundle_payload: dict[str, Any]) -> str:
        adapter_metadata = bundle_payload.get('adapter_metadata') if isinstance(bundle_payload.get('adapter_metadata'), dict) else {}
        review_task = adapter_metadata.get('review_task') if isinstance(adapter_metadata.get('review_task'), dict) else {}
        return str(review_task.get('status', 'review_pending')).strip().lower() or 'review_pending'

    def _resolve_reason_codes(self, bundle_payload: dict[str, Any]) -> list[str]:
        adapter_metadata = bundle_payload.get('adapter_metadata') if isinstance(bundle_payload.get('adapter_metadata'), dict) else {}
        review_task = adapter_metadata.get('review_task') if isinstance(adapter_metadata.get('review_task'), dict) else {}
        reason_codes = review_task.get('reason_codes', [])
        if not isinstance(reason_codes, list):
            return []
        return [str(item).strip() for item in reason_codes if str(item).strip()]

    def _load_bundle_payload(self, bundle_path: str, *, base_dir: Path | None) -> dict[str, Any]:
        if not bundle_path:
            return {}
        path = Path(bundle_path)
        if not path.is_absolute() and base_dir is not None:
            path = (base_dir / path).resolve()
        try:
            payload = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError):
            return {}
        return payload if isinstance(payload, dict) else {}

    def _clamp_score(self, value: Any) -> float:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            numeric = 0.0
        return max(0.0, min(1.0, numeric))

    def _to_non_negative_float(self, value: Any) -> float:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            numeric = 0.0
        return max(0.0, numeric)

    def _is_number(self, value: Any) -> bool:
        try:
            float(value)
            return True
        except (TypeError, ValueError):
            return False
