from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from omni_skill_pipeline.models import new_id, utc_now_iso
from omni_skill_pipeline.quality.feedback import ReviewFeedback
from omni_skill_pipeline.utils import unique_preserve_order


@dataclass(frozen=True, slots=True)
class RemediationPlanStep:
    step_id: str
    action_code: str
    target: str
    intent: str
    reason_code: str
    description: str
    priority: str = 'medium'
    params: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            'step_id': self.step_id,
            'action_code': self.action_code,
            'target': self.target,
            'intent': self.intent,
            'reason_code': self.reason_code,
            'description': self.description,
            'priority': self.priority,
            'params': dict(self.params),
        }


@dataclass(frozen=True, slots=True)
class RemediationPlan:
    plan_id: str
    review_task_id: str
    skill_id: str
    decision: str
    status: str
    next_action: str
    summary: str
    categories: list[str] = field(default_factory=list)
    reason_codes: list[str] = field(default_factory=list)
    revision_suggestions: list[str] = field(default_factory=list)
    follow_up_checks: list[str] = field(default_factory=list)
    steps: list[RemediationPlanStep] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            'plan_id': self.plan_id,
            'review_task_id': self.review_task_id,
            'skill_id': self.skill_id,
            'decision': self.decision,
            'status': self.status,
            'next_action': self.next_action,
            'summary': self.summary,
            'categories': list(self.categories),
            'reason_codes': list(self.reason_codes),
            'revision_suggestions': list(self.revision_suggestions),
            'follow_up_checks': list(self.follow_up_checks),
            'steps': [item.to_dict() for item in self.steps],
            'created_at': self.created_at,
        }


class ReviewFeedbackConsumer(object):
    """LC-L2-30: convert review feedback into an executable remediation plan skeleton."""

    def consume(self, feedback: ReviewFeedback | dict[str, Any]) -> RemediationPlan:
        payload = self._coerce_feedback_payload(feedback)
        steps = self._build_steps(payload)
        decision = str(payload.get('decision', '')).strip()
        next_action = self._resolve_next_action(decision=decision, has_steps=bool(steps))
        summary = self._build_summary(next_action=next_action, step_count=len(steps), decision=decision)
        return RemediationPlan(
            plan_id=new_id(),
            review_task_id=str(payload.get('review_task_id', '')).strip(),
            skill_id=str(payload.get('skill_id', '')).strip(),
            decision=decision,
            status=str(payload.get('status', '')).strip(),
            next_action=next_action,
            summary=summary,
            categories=unique_preserve_order(payload.get('categories', [])),
            reason_codes=unique_preserve_order(payload.get('reason_codes', [])),
            revision_suggestions=unique_preserve_order(payload.get('revision_suggestions', [])),
            follow_up_checks=unique_preserve_order(payload.get('follow_up_checks', [])),
            steps=steps,
        )

    def _coerce_feedback_payload(self, feedback: ReviewFeedback | dict[str, Any]) -> dict[str, Any]:
        if isinstance(feedback, ReviewFeedback):
            return feedback.to_dict()
        if isinstance(feedback, dict):
            return dict(feedback)
        raise TypeError('feedback must be ReviewFeedback or dict payload.')

    def _build_steps(self, payload: dict[str, Any]) -> list[RemediationPlanStep]:
        raw_actions: list[dict[str, Any]] = []
        for key in ('atom_actions', 'graph_actions', 'policy_actions'):
            value = payload.get(key, [])
            if not isinstance(value, list):
                continue
            for item in value:
                if isinstance(item, dict):
                    raw_actions.append(item)

        steps: list[RemediationPlanStep] = []
        seen: set[str] = set()
        for index, action in enumerate(raw_actions, start=1):
            action_code = str(action.get('action_code', '')).strip()
            if not action_code or action_code in seen:
                continue
            seen.add(action_code)
            step_id = 'remediate-%02d' % index
            reason_code = str(action.get('reason_code', '')).strip() or 'UNKNOWN_REASON'
            intent = str(action.get('intent', '')).strip() or 'adjust_assembly_policy'
            target = str(action.get('target', '')).strip() or 'policy'
            steps.append(
                RemediationPlanStep(
                    step_id=step_id,
                    action_code=action_code,
                    target=target,
                    intent=intent,
                    reason_code=reason_code,
                    description=self._build_step_description(action_code=action_code, target=target, intent=intent),
                    priority=self._infer_priority(reason_code=reason_code),
                    params=dict(action.get('params', {})) if isinstance(action.get('params'), dict) else {},
                )
            )

        if steps:
            return steps
        return [
            RemediationPlanStep(
                step_id='remediate-01',
                action_code='PLAN_MANUAL_REVIEW',
                target='policy',
                intent='escalate_manual_review',
                reason_code='NO_STRUCTURED_ACTIONS',
                description='Escalate manual review and capture remediation requirements.',
                priority='medium',
                params={},
            )
        ]

    def _resolve_next_action(self, *, decision: str, has_steps: bool) -> str:
        normalized = decision.strip().lower()
        if normalized == 'reject':
            return 'rebuild_from_evidence'
        if normalized == 'review_required':
            return 'run_targeted_remediation'
        if normalized == 'auto_publish':
            return 'monitor_post_publish'
        return 'manual_review_followup' if has_steps else 'await_human_triage'

    def _build_summary(self, *, next_action: str, step_count: int, decision: str) -> str:
        if step_count <= 0:
            return 'No actionable remediation steps; waiting for manual triage.'
        decision_text = decision.strip().lower() or 'unknown'
        return 'Prepared %s remediation steps for %s; next action: %s.' % (step_count, decision_text, next_action)

    def _build_step_description(self, *, action_code: str, target: str, intent: str) -> str:
        return 'Apply %s on %s via %s.' % (action_code, target, intent)

    def _infer_priority(self, *, reason_code: str) -> str:
        normalized = reason_code.strip().upper()
        if normalized.startswith('R_'):
            return 'high'
        if normalized.startswith('Q_'):
            return 'medium'
        return 'low'
