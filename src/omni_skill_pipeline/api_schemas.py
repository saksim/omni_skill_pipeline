from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from omni_skill_pipeline.models import Audience, GoalType, Granularity, Modality, Rigor

__all__ = [
    'AudioDistillRequestSchema',
    'CorpusAssetRequestSchema',
    'CorpusDistillRequestSchema',
    'DistillGoalSchema',
    'ImageDistillRequestSchema',
    'ReviewQueueClaimRequestSchema',
    'ReviewQueueCloseRequestSchema',
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

    @field_validator('name', mode='before')
    @classmethod
    def _normalize_name(cls, value: Any) -> str:
        return str(value or '').strip()

    @field_validator('tags', mode='before')
    @classmethod
    def _normalize_tags(cls, value: Any) -> list[str]:
        return _normalize_string_list(value, 'tags', strip_items=True)

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

    @model_validator(mode='after')
    def _validate_source(self) -> 'TextDistillRequestSchema':
        if not (self.content or self.file_path):
            raise ValueError('Text request requires content or file_path.')
        return self


class AudioDistillRequestSchema(APISchemaBase):
    title: str | None = None
    audio_path: str | None = None
    transcript: str | None = None
    transcript_path: str | None = None
    language: str | None = None
    prompt: str | None = None
    goal: DistillGoalSchema = Field(default_factory=DistillGoalSchema)

    @model_validator(mode='after')
    def _validate_source(self) -> 'AudioDistillRequestSchema':
        if not (self.transcript or self.transcript_path or self.audio_path):
            raise ValueError('Audio request requires transcript, transcript_path, or audio_path.')
        return self


class ImageDistillRequestSchema(APISchemaBase):
    image_path: str
    title: str | None = None
    goal: DistillGoalSchema = Field(default_factory=DistillGoalSchema)

    @field_validator('image_path')
    @classmethod
    def _validate_image_path(cls, value: str) -> str:
        if not value:
            raise ValueError('Image request requires image_path.')
        return value


class TabularDistillRequestSchema(APISchemaBase):
    file_path: str
    title: str | None = None
    time_column: str | None = None
    value_columns: list[str] = Field(default_factory=list)
    entity_columns: list[str] = Field(default_factory=list)
    max_series: int = Field(default=6, ge=1)
    goal: DistillGoalSchema = Field(default_factory=DistillGoalSchema)

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

    @field_validator('video_path')
    @classmethod
    def _validate_video_path(cls, value: str) -> str:
        if not value:
            raise ValueError('Video request requires video_path.')
        return value


class ReviewQueueClaimRequestSchema(APISchemaBase):
    review_task_id: str | None = None
    consumer: str = 'review-consumer'

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
