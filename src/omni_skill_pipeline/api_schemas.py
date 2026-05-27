from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from omni_skill_pipeline.models import Audience, GoalType, Granularity, Modality, Rigor

__all__ = [
    'AudioDistillRequestSchema',
    'CorpusAssetRequestSchema',
    'CorpusDistillRequestSchema',
    'DistillGoalSchema',
    'ConsoleViewsRequestSchema',
    'GovernanceDeletionRequestSchema',
    'GovernanceRetentionPolicyUpsertRequestSchema',
    'GovernanceScopeRequestSchema',
    'ImageDistillRequestSchema',
    'ReviewQueueClaimRequestSchema',
    'ReviewQueueCloseRequestSchema',
    'ReviewQueueDecisionRequestSchema',
    'TenantScopeSchema',
    'TabularDistillRequestSchema',
    'TextDistillRequestSchema',
    'VideoDistillRequestSchema',
]


def _normalize_string_list(value: Any, field_name: str, *, strip_items: bool) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, (list, tuple)):
        raise TypeError('%s must be a list.' % field_name)

    items: list[str] = []
    for raw_item in value:
        item = str(raw_item)
        if strip_items:
            item = item.strip()
        if strip_items and not item:
            continue
        items.append(item)
    return items


class APISchemaBase(BaseModel):
    model_config = ConfigDict(extra='forbid')


class TenantScopeSchema(APISchemaBase):
    organization_id: str = ''
    project_id: str = ''

    @field_validator('organization_id', mode='before')
    @classmethod
    def _normalize_organization_id(cls, value: Any) -> str:
        return str(value or '').strip()

    @field_validator('project_id', mode='before')
    @classmethod
    def _normalize_project_id(cls, value: Any) -> str:
        return str(value or '').strip()


class DistillGoalSchema(APISchemaBase):
    goal_type: GoalType = GoalType.BUILD_SKILL
    audience: Audience = Audience.SELF
    rigor: Rigor = Rigor.DRAFT
    granularity: Granularity = Granularity.TASK
    domain: str = 'general'

    @field_validator('domain', mode='before')
    @classmethod
    def _normalize_domain(cls, value: Any) -> str:
        text = str(value or '').strip()
        return text or 'general'


class CorpusAssetRequestSchema(APISchemaBase):
    source_uri: str
    modality: Modality
    title_hint: str = ''
    role: str = 'primary'
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator('source_uri', mode='before')
    @classmethod
    def _normalize_source_uri(cls, value: Any) -> str:
        text = str(value or '').strip()
        if not text:
            raise ValueError('Corpus asset input requires source_uri.')
        return text

    @field_validator('title_hint', mode='before')
    @classmethod
    def _normalize_title_hint(cls, value: Any) -> str:
        return str(value or '').strip()

    @field_validator('role', mode='before')
    @classmethod
    def _normalize_role(cls, value: Any) -> str:
        text = str(value or 'primary').strip()
        if not text:
            raise ValueError('Corpus asset role is empty.')
        return text


class CorpusDistillRequestSchema(APISchemaBase):
    name: str = ''
    assets: list[CorpusAssetRequestSchema] = Field(default_factory=list)
    goal: DistillGoalSchema = Field(default_factory=DistillGoalSchema)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    tenant_scope: TenantScopeSchema | None = None

    @field_validator('name', mode='before')
    @classmethod
    def _normalize_name(cls, value: Any) -> str:
        return str(value or '').strip()

    @field_validator('tags', mode='before')
    @classmethod
    def _normalize_tags(cls, value: Any) -> list[str]:
        return _normalize_string_list(value, 'tags', strip_items=True)

    @field_validator('metadata', mode='before')
    @classmethod
    def _normalize_metadata(cls, value: Any) -> dict[str, Any]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise TypeError('metadata must be an object.')
        return dict(value)

    @model_validator(mode='after')
    def _validate_assets(self) -> 'CorpusDistillRequestSchema':
        if not self.assets:
            raise ValueError('Corpus request requires at least one asset.')
        return self


class TextDistillRequestSchema(APISchemaBase):
    title: str | None = None
    content: str | None = None
    file_path: str | None = None
    goal: DistillGoalSchema = Field(default_factory=DistillGoalSchema)
    tenant_scope: TenantScopeSchema | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode='after')
    def _validate_source(self) -> 'TextDistillRequestSchema':
        if not (self.content or self.file_path):
            raise ValueError('Text request requires content or file_path.')
        return self

    @field_validator('metadata', mode='before')
    @classmethod
    def _normalize_metadata(cls, value: Any) -> dict[str, Any]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise TypeError('metadata must be an object.')
        return dict(value)


class AudioDistillRequestSchema(APISchemaBase):
    title: str | None = None
    audio_path: str | None = None
    transcript: str | None = None
    transcript_path: str | None = None
    language: str | None = None
    prompt: str | None = None
    goal: DistillGoalSchema = Field(default_factory=DistillGoalSchema)
    tenant_scope: TenantScopeSchema | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode='after')
    def _validate_source(self) -> 'AudioDistillRequestSchema':
        if not (self.transcript or self.transcript_path or self.audio_path):
            raise ValueError('Audio request requires transcript, transcript_path, or audio_path.')
        return self

    @field_validator('metadata', mode='before')
    @classmethod
    def _normalize_metadata(cls, value: Any) -> dict[str, Any]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise TypeError('metadata must be an object.')
        return dict(value)


class ImageDistillRequestSchema(APISchemaBase):
    image_path: str
    title: str | None = None
    goal: DistillGoalSchema = Field(default_factory=DistillGoalSchema)
    tenant_scope: TenantScopeSchema | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator('image_path')
    @classmethod
    def _validate_image_path(cls, value: str) -> str:
        if not value:
            raise ValueError('Image request requires image_path.')
        return value

    @field_validator('metadata', mode='before')
    @classmethod
    def _normalize_metadata(cls, value: Any) -> dict[str, Any]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise TypeError('metadata must be an object.')
        return dict(value)


class TabularDistillRequestSchema(APISchemaBase):
    file_path: str
    title: str | None = None
    time_column: str | None = None
    value_columns: list[str] = Field(default_factory=list)
    entity_columns: list[str] = Field(default_factory=list)
    max_series: int = Field(default=6, ge=1)
    goal: DistillGoalSchema = Field(default_factory=DistillGoalSchema)
    tenant_scope: TenantScopeSchema | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator('file_path')
    @classmethod
    def _validate_file_path(cls, value: str) -> str:
        if not value:
            raise ValueError('Tabular request requires file_path.')
        return value

    @field_validator('value_columns', mode='before')
    @classmethod
    def _normalize_value_columns(cls, value: Any) -> list[str]:
        return _normalize_string_list(value, 'value_columns', strip_items=False)

    @field_validator('entity_columns', mode='before')
    @classmethod
    def _normalize_entity_columns(cls, value: Any) -> list[str]:
        return _normalize_string_list(value, 'entity_columns', strip_items=False)

    @field_validator('metadata', mode='before')
    @classmethod
    def _normalize_metadata(cls, value: Any) -> dict[str, Any]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise TypeError('metadata must be an object.')
        return dict(value)


class VideoDistillRequestSchema(APISchemaBase):
    video_path: str
    title: str | None = None
    transcript: str | None = None
    transcript_path: str | None = None
    language: str | None = None
    prompt: str | None = None
    keyframe_interval_seconds: int | None = None
    max_keyframes: int | None = Field(default=None, ge=1)
    scene_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    dedupe_distance: int | None = Field(default=None, ge=0)
    goal: DistillGoalSchema = Field(default_factory=DistillGoalSchema)
    tenant_scope: TenantScopeSchema | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator('video_path')
    @classmethod
    def _validate_video_path(cls, value: str) -> str:
        if not value:
            raise ValueError('Video request requires video_path.')
        return value

    @field_validator('metadata', mode='before')
    @classmethod
    def _normalize_metadata(cls, value: Any) -> dict[str, Any]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise TypeError('metadata must be an object.')
        return dict(value)


class ReviewQueueClaimRequestSchema(APISchemaBase):
    review_task_id: str | None = None
    consumer: str = 'review-consumer'
    tenant_scope: TenantScopeSchema | None = None

    @field_validator('review_task_id', mode='before')
    @classmethod
    def _normalize_review_task_id(cls, value: Any) -> str | None:
        text = str(value or '').strip()
        return text or None

    @field_validator('consumer', mode='before')
    @classmethod
    def _normalize_consumer(cls, value: Any) -> str:
        text = str(value or '').strip()
        return text or 'review-consumer'


class ReviewQueueCloseRequestSchema(APISchemaBase):
    status: str = 'published'
    closed_by: str = 'review-operator'
    review_notes: str = ''
    decision: str | None = None
    reason_codes: list[str] = Field(default_factory=list)
    reviewer_edits: dict[str, Any] = Field(default_factory=dict)
    tenant_scope: TenantScopeSchema | None = None

    @field_validator('status', mode='before')
    @classmethod
    def _normalize_status(cls, value: Any) -> str:
        text = str(value or '').strip().lower()
        return text or 'published'

    @field_validator('closed_by', mode='before')
    @classmethod
    def _normalize_closed_by(cls, value: Any) -> str:
        text = str(value or '').strip()
        return text or 'review-operator'

    @field_validator('review_notes', mode='before')
    @classmethod
    def _normalize_review_notes(cls, value: Any) -> str:
        return str(value or '').strip()

    @field_validator('decision', mode='before')
    @classmethod
    def _normalize_decision(cls, value: Any) -> str | None:
        text = str(value or '').strip().lower()
        if not text:
            return None
        mapping = {
            'approve': 'approve',
            'approved': 'approve',
            'reject': 'reject',
            'rejected': 'reject',
            'needs_rework': 'needs_rework',
            'needs-rework': 'needs_rework',
            'needs rework': 'needs_rework',
        }
        if text not in mapping:
            raise ValueError('decision must be one of approve/reject/needs_rework.')
        return mapping[text]

    @field_validator('reason_codes', mode='before')
    @classmethod
    def _normalize_reason_codes(cls, value: Any) -> list[str]:
        return _normalize_string_list(value, 'reason_codes', strip_items=True)

    @field_validator('reviewer_edits', mode='before')
    @classmethod
    def _normalize_reviewer_edits(cls, value: Any) -> dict[str, Any]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise TypeError('reviewer_edits must be an object.')
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key).strip()
            if key_text:
                normalized[key_text] = item
        return normalized


class ReviewQueueDecisionRequestSchema(APISchemaBase):
    decision: str
    reviewer: str = 'review-operator'
    reason_codes: list[str] = Field(default_factory=list)
    review_notes: str = ''
    reviewer_edits: dict[str, Any] = Field(default_factory=dict)
    status: str | None = None
    tenant_scope: TenantScopeSchema | None = None

    @field_validator('decision', mode='before')
    @classmethod
    def _normalize_decision(cls, value: Any) -> str:
        text = str(value or '').strip().lower()
        mapping = {
            'approve': 'approve',
            'approved': 'approve',
            'reject': 'reject',
            'rejected': 'reject',
            'needs_rework': 'needs_rework',
            'needs-rework': 'needs_rework',
            'needs rework': 'needs_rework',
        }
        if text not in mapping:
            raise ValueError('decision must be one of approve/reject/needs_rework.')
        return mapping[text]

    @field_validator('reviewer', mode='before')
    @classmethod
    def _normalize_reviewer(cls, value: Any) -> str:
        text = str(value or '').strip()
        return text or 'review-operator'

    @field_validator('reason_codes', mode='before')
    @classmethod
    def _normalize_reason_codes(cls, value: Any) -> list[str]:
        return _normalize_string_list(value, 'reason_codes', strip_items=True)

    @field_validator('review_notes', mode='before')
    @classmethod
    def _normalize_review_notes(cls, value: Any) -> str:
        return str(value or '').strip()

    @field_validator('reviewer_edits', mode='before')
    @classmethod
    def _normalize_reviewer_edits(cls, value: Any) -> dict[str, Any]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise TypeError('reviewer_edits must be an object.')
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key).strip()
            if key_text:
                normalized[key_text] = item
        return normalized

    @field_validator('status', mode='before')
    @classmethod
    def _normalize_status(cls, value: Any) -> str | None:
        text = str(value or '').strip().lower()
        return text or None


class GovernanceScopeRequestSchema(APISchemaBase):
    organization_id: str = ''
    project_id: str = ''
    include_cost_entries: bool = False
    include_audit_events: bool = False
    include_deletion_records: bool = False
    include_retention_policies: bool = True
    limit: int = Field(default=200, ge=1, le=2000)

    @field_validator('organization_id', mode='before')
    @classmethod
    def _normalize_organization_id(cls, value: Any) -> str:
        return str(value or '').strip()

    @field_validator('project_id', mode='before')
    @classmethod
    def _normalize_project_id(cls, value: Any) -> str:
        return str(value or '').strip()


class ConsoleViewsRequestSchema(APISchemaBase):
    organization_id: str = ''
    project_id: str = ''
    limit: int = Field(default=50, ge=1, le=500)
    queue_status: str = 'pending'

    @field_validator('organization_id', mode='before')
    @classmethod
    def _normalize_organization_id(cls, value: Any) -> str:
        return str(value or '').strip()

    @field_validator('project_id', mode='before')
    @classmethod
    def _normalize_project_id(cls, value: Any) -> str:
        return str(value or '').strip()

    @field_validator('queue_status', mode='before')
    @classmethod
    def _normalize_queue_status(cls, value: Any) -> str:
        text = str(value or '').strip().lower()
        if text not in {'pending', 'consumed', 'closed', 'all'}:
            raise ValueError('queue_status must be one of pending/consumed/closed/all.')
        return text


class GovernanceRetentionPolicyUpsertRequestSchema(APISchemaBase):
    policy_id: str = ''
    organization_id: str = ''
    project_id: str = ''
    policy_type: str = 'artifact_retention'
    retention_days: int = Field(default=30, ge=0)
    deletion_mode: str = 'soft_delete'
    delete_requires_review_approval: bool = True
    enabled: bool = True
    updated_by: str = 'governance-operator'
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator('policy_id', mode='before')
    @classmethod
    def _normalize_policy_id(cls, value: Any) -> str:
        return str(value or '').strip()

    @field_validator('organization_id', mode='before')
    @classmethod
    def _normalize_organization_id(cls, value: Any) -> str:
        return str(value or '').strip()

    @field_validator('project_id', mode='before')
    @classmethod
    def _normalize_project_id(cls, value: Any) -> str:
        return str(value or '').strip()

    @field_validator('policy_type', mode='before')
    @classmethod
    def _normalize_policy_type(cls, value: Any) -> str:
        text = str(value or '').strip()
        return text or 'artifact_retention'

    @field_validator('deletion_mode', mode='before')
    @classmethod
    def _normalize_deletion_mode(cls, value: Any) -> str:
        text = str(value or '').strip()
        return text or 'soft_delete'

    @field_validator('updated_by', mode='before')
    @classmethod
    def _normalize_updated_by(cls, value: Any) -> str:
        text = str(value or '').strip()
        return text or 'governance-operator'

    @field_validator('metadata', mode='before')
    @classmethod
    def _normalize_metadata(cls, value: Any) -> dict[str, Any]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise TypeError('metadata must be an object.')
        return dict(value)


class GovernanceDeletionRequestSchema(APISchemaBase):
    organization_id: str = ''
    project_id: str = ''
    resource_type: str = 'artifact'
    resource_id: str
    resource_path: str = ''
    deletion_mode: str = 'soft_delete'
    status: str = 'recorded'
    actor: str = 'governance-operator'
    api_key_id: str = ''
    skill_id: str = ''
    reason: str = ''
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator('organization_id', mode='before')
    @classmethod
    def _normalize_organization_id(cls, value: Any) -> str:
        return str(value or '').strip()

    @field_validator('project_id', mode='before')
    @classmethod
    def _normalize_project_id(cls, value: Any) -> str:
        return str(value or '').strip()

    @field_validator('resource_type', mode='before')
    @classmethod
    def _normalize_resource_type(cls, value: Any) -> str:
        text = str(value or '').strip()
        return text or 'artifact'

    @field_validator('resource_id', mode='before')
    @classmethod
    def _normalize_resource_id(cls, value: Any) -> str:
        text = str(value or '').strip()
        if not text:
            raise ValueError('resource_id is required.')
        return text

    @field_validator('resource_path', mode='before')
    @classmethod
    def _normalize_resource_path(cls, value: Any) -> str:
        return str(value or '').strip()

    @field_validator('deletion_mode', mode='before')
    @classmethod
    def _normalize_deletion_mode(cls, value: Any) -> str:
        text = str(value or '').strip()
        return text or 'soft_delete'

    @field_validator('status', mode='before')
    @classmethod
    def _normalize_status(cls, value: Any) -> str:
        text = str(value or '').strip()
        return text or 'recorded'

    @field_validator('actor', mode='before')
    @classmethod
    def _normalize_actor(cls, value: Any) -> str:
        text = str(value or '').strip()
        return text or 'governance-operator'

    @field_validator('api_key_id', mode='before')
    @classmethod
    def _normalize_api_key_id(cls, value: Any) -> str:
        return str(value or '').strip()

    @field_validator('skill_id', mode='before')
    @classmethod
    def _normalize_skill_id(cls, value: Any) -> str:
        return str(value or '').strip()

    @field_validator('reason', mode='before')
    @classmethod
    def _normalize_reason(cls, value: Any) -> str:
        return str(value or '').strip()

    @field_validator('metadata', mode='before')
    @classmethod
    def _normalize_metadata(cls, value: Any) -> dict[str, Any]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise TypeError('metadata must be an object.')
        return dict(value)
