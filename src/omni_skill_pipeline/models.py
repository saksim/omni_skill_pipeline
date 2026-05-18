from __future__ import annotations

import json
from dataclasses import dataclass, field, fields, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar
from uuid import uuid4


class Modality(str, Enum):
    TEXT = 'text'
    AUDIO = 'audio'
    VIDEO = 'video'
    IMAGE = 'image'
    TABULAR = 'tabular'


class ContentType(str, Enum):
    TEXT = 'text'
    SPEECH = 'speech'
    TABLE = 'table'
    OCR = 'ocr'
    SCENE = 'scene'
    METRIC = 'metric'
    EVENT = 'event'


class InsightType(str, Enum):
    CONCEPT = 'concept'
    PROCEDURE = 'procedure'
    RULE = 'rule'
    ANTI_PATTERN = 'anti_pattern'
    VERIFICATION = 'verification'
    PRECONDITION = 'precondition'


class SkillType(str, Enum):
    PROCEDURE = 'procedure'
    DECISION = 'decision'
    DIAGNOSTIC = 'diagnostic'
    ANALYSIS = 'analysis'
    COMMUNICATION = 'communication'
    AUTOMATION = 'automation'


class ReviewStatus(str, Enum):
    DRAFT = 'draft'
    REVIEW_PENDING = 'review_pending'
    PUBLISHED = 'published'
    REJECTED = 'rejected'


class GoalType(str, Enum):
    BUILD_SKILL = 'build_skill'
    BUILD_PLAYBOOK = 'build_playbook'
    EXTRACT_DECISION_TREE = 'extract_decision_tree'
    EXTRACT_CHECKLIST = 'extract_checklist'


class Audience(str, Enum):
    SELF = 'self'
    JUNIOR = 'junior'
    EXPERT = 'expert'


class Rigor(str, Enum):
    DRAFT = 'draft'
    REVIEWED = 'reviewed'
    PUBLISHABLE = 'publishable'


class Granularity(str, Enum):
    MICRO = 'micro'
    TASK = 'task'
    WORKFLOW = 'workflow'


class AtomType(str, Enum):
    CLAIM = 'claim'
    PROCEDURE = 'procedure'
    RULE = 'rule'
    VERIFICATION = 'verification'
    ANTI_PATTERN = 'anti_pattern'
    ENTITY = 'entity'
    EVENT = 'event'
    EXAMPLE = 'example'
    METRIC_GUARDRAIL = 'metric_guardrail'
    QUESTION = 'question'


class GraphNodeType(str, Enum):
    STEP = 'step'
    DECISION = 'decision'
    VERIFICATION = 'verification'
    RISK = 'risk'
    EXAMPLE = 'example'
    VARIABLE = 'variable'


class GraphEdgeType(str, Enum):
    DEPENDS_ON = 'depends_on'
    JUSTIFIED_BY = 'justified_by'
    VERIFIED_BY = 'verified_by'
    PARAMETERIZES = 'parameterizes'
    SUPERSEDES = 'supersedes'
    CONFLICTS_WITH = 'conflicts_with'


class PublicationType(str, Enum):
    SKILL_MARKDOWN = 'skill_markdown'
    SKILL_JSON = 'skill_json'
    CHECKLIST_JSON = 'checklist_json'
    DECISION_TREE_JSON = 'decision_tree_json'
    PLAYBOOK_JSON = 'playbook_json'
    EMBEDDING_DOCUMENT = 'embedding_document'


class LifecycleDecisionType(str, Enum):
    NEW = 'new'
    REVISE = 'revise'
    MERGE = 'merge'
    SUPERSEDE = 'supersede'
    REJECT = 'reject'


class ReviewDecision(str, Enum):
    AUTO_PUBLISH = 'auto_publish'
    REVIEW_REQUIRED = 'review_required'
    REJECT = 'reject'


EnumType = TypeVar('EnumType', bound=Enum)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def new_id() -> str:
    return str(uuid4())


def parse_enum(enum_type: Type[EnumType], value: Any, field_name: str) -> EnumType:
    if isinstance(value, enum_type):
        return value
    if value is None:
        raise ValueError('Missing enum value for %s' % field_name)
    try:
        return enum_type(value)
    except ValueError as exc:
        valid = ', '.join(member.value for member in enum_type)
        raise ValueError('%s must be one of: %s' % (field_name, valid)) from exc


def to_primitive(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {
            field_info.name: to_primitive(getattr(value, field_info.name))
            for field_info in fields(value)
        }
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, list):
        return [to_primitive(item) for item in value]
    if isinstance(value, tuple):
        return [to_primitive(item) for item in value]
    if isinstance(value, dict):
        return {str(key): to_primitive(item) for key, item in value.items()}
    return value


class SerializableMixin(object):
    def to_dict(self) -> Dict[str, Any]:
        return to_primitive(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


@dataclass(slots=True)
class DistillGoal(SerializableMixin):
    goal_type: GoalType = GoalType.BUILD_SKILL
    audience: Audience = Audience.SELF
    rigor: Rigor = Rigor.DRAFT
    granularity: Granularity = Granularity.TASK
    domain: str = 'general'

    @classmethod
    def from_dict(cls, payload: Optional[Dict[str, Any]]) -> 'DistillGoal':
        payload = payload or {}
        return cls(
            goal_type=parse_enum(GoalType, payload.get('goal_type', GoalType.BUILD_SKILL.value), 'goal_type'),
            audience=parse_enum(Audience, payload.get('audience', Audience.SELF.value), 'audience'),
            rigor=parse_enum(Rigor, payload.get('rigor', Rigor.DRAFT.value), 'rigor'),
            granularity=parse_enum(
                Granularity,
                payload.get('granularity', Granularity.TASK.value),
                'granularity',
            ),
            domain=str(payload.get('domain', 'general')).strip() or 'general',
        )


@dataclass(slots=True)
class Asset(SerializableMixin):
    modality: Modality
    source_uri: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    asset_id: str = field(default_factory=new_id)


@dataclass(slots=True)
class EvidenceUnit(SerializableMixin):
    asset_id: str
    span_ref: str
    content_type: ContentType
    content: str
    speaker: Optional[str] = None
    confidence: float = 0.8
    tags: List[str] = field(default_factory=list)
    evidence_id: str = field(default_factory=new_id)


@dataclass(slots=True)
class TimeRangeRef(SerializableMixin):
    start_ms: Optional[int] = None
    end_ms: Optional[int] = None


@dataclass(slots=True)
class SpatialRef(SerializableMixin):
    x: Optional[float] = None
    y: Optional[float] = None
    w: Optional[float] = None
    h: Optional[float] = None
    page: Optional[int] = None


@dataclass(slots=True)
class StructuralRef(SerializableMixin):
    section: Optional[str] = None
    row: Optional[int] = None
    column: Optional[str] = None
    paragraph_index: Optional[int] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None


@dataclass(slots=True)
class EvidenceNode(SerializableMixin):
    asset_id: str
    modality: Modality
    content_type: ContentType
    span_ref: str
    text_content: str = ''
    payload: Dict[str, Any] = field(default_factory=dict)
    time_range: Optional[TimeRangeRef] = None
    spatial_ref: Optional[SpatialRef] = None
    structural_ref: Optional[StructuralRef] = None
    speaker: Optional[str] = None
    confidence: float = 0.8
    tags: List[str] = field(default_factory=list)
    parents: List[str] = field(default_factory=list)
    children: List[str] = field(default_factory=list)
    derived_from: List[str] = field(default_factory=list)
    evidence_id: str = field(default_factory=new_id)


@dataclass(slots=True)
class Insight(SerializableMixin):
    insight_type: InsightType
    summary: str
    evidence_refs: List[str]
    confidence: float = 0.7
    insight_id: str = field(default_factory=new_id)


@dataclass(slots=True)
class SemanticAtom(SerializableMixin):
    atom_type: AtomType
    summary: str
    evidence_refs: List[str]
    confidence: float = 0.7
    attributes: Dict[str, Any] = field(default_factory=dict)
    atom_id: str = field(default_factory=new_id)


@dataclass(slots=True)
class CorpusAssetRef(SerializableMixin):
    asset_id: str
    modality: Modality
    source_uri: str
    role: str = 'primary'
    title_hint: str = ''
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Corpus(SerializableMixin):
    name: str
    goal: DistillGoal
    assets: List[CorpusAssetRef] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)
    corpus_id: str = field(default_factory=new_id)


@dataclass(slots=True)
class SkillStep(SerializableMixin):
    step: int
    action: str
    why: str = ''


@dataclass(slots=True)
class StepNode(SerializableMixin):
    step: int
    action: str
    why: str = ''
    atom_refs: List[str] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    node_type: GraphNodeType = GraphNodeType.STEP
    node_id: str = field(default_factory=new_id)


@dataclass(slots=True)
class DecisionNode(SerializableMixin):
    condition: str
    decision: str
    rationale: str = ''
    atom_refs: List[str] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    node_type: GraphNodeType = GraphNodeType.DECISION
    node_id: str = field(default_factory=new_id)


@dataclass(slots=True)
class VerificationNode(SerializableMixin):
    check: str
    expected: str = ''
    atom_refs: List[str] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    node_type: GraphNodeType = GraphNodeType.VERIFICATION
    node_id: str = field(default_factory=new_id)


@dataclass(slots=True)
class RiskNode(SerializableMixin):
    risk: str
    mitigation: str = ''
    atom_refs: List[str] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    node_type: GraphNodeType = GraphNodeType.RISK
    node_id: str = field(default_factory=new_id)


@dataclass(slots=True)
class ExampleNode(SerializableMixin):
    example: str
    classification: str = 'positive'
    atom_refs: List[str] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    node_type: GraphNodeType = GraphNodeType.EXAMPLE
    node_id: str = field(default_factory=new_id)


@dataclass(slots=True)
class VariableNode(SerializableMixin):
    name: str
    description: str = ''
    default_value: Optional[str] = None
    required: bool = False
    atom_refs: List[str] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    node_type: GraphNodeType = GraphNodeType.VARIABLE
    node_id: str = field(default_factory=new_id)


@dataclass(slots=True)
class SkillGraphEdge(SerializableMixin):
    edge_type: GraphEdgeType
    source_node_id: str
    target_node_id: str
    rationale: str = ''
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    edge_id: str = field(default_factory=new_id)

    def validate(self) -> None:
        if not self.source_node_id.strip():
            raise ValueError('SkillGraphEdge.source_node_id is required.')
        if not self.target_node_id.strip():
            raise ValueError('SkillGraphEdge.target_node_id is required.')
        if self.weight <= 0:
            raise ValueError('SkillGraphEdge.weight must be > 0.')


@dataclass(slots=True)
class SkillGraph(SerializableMixin):
    name: str
    goal: str
    source_modalities: List[Modality]
    audience: Audience = Audience.SELF
    summary: str = ''
    tags: List[str] = field(default_factory=list)
    domain: str = 'general'
    trigger: List[str] = field(default_factory=list)
    inputs: List[str] = field(default_factory=list)
    preconditions: List[str] = field(default_factory=list)
    steps: List[StepNode] = field(default_factory=list)
    decisions: List[DecisionNode] = field(default_factory=list)
    verifications: List[VerificationNode] = field(default_factory=list)
    risks: List[RiskNode] = field(default_factory=list)
    examples: List[ExampleNode] = field(default_factory=list)
    variables: List[VariableNode] = field(default_factory=list)
    edges: List[SkillGraphEdge] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)
    atom_refs: List[str] = field(default_factory=list)
    confidence: float = 0.6
    version: str = '0.1.0'
    review_status: ReviewStatus = ReviewStatus.DRAFT
    created_at: str = field(default_factory=utc_now_iso)
    graph_id: str = field(default_factory=new_id)

    def node_ids(self) -> List[str]:
        return [item.node_id for item in self.all_nodes()]

    def all_nodes(self) -> List[Any]:
        return [
            *self.steps,
            *self.decisions,
            *self.verifications,
            *self.risks,
            *self.examples,
            *self.variables,
        ]

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError('SkillGraph.name is required.')
        if not self.goal.strip():
            raise ValueError('SkillGraph.goal is required.')
        if not self.source_modalities:
            raise ValueError('SkillGraph.source_modalities cannot be empty.')
        nodes = self.all_nodes()
        if not nodes:
            raise ValueError('SkillGraph requires at least one node.')

        seen: set[str] = set()
        for node in nodes:
            node_id = str(getattr(node, 'node_id', '')).strip()
            if not node_id:
                raise ValueError('Each SkillGraph node requires node_id.')
            if node_id in seen:
                raise ValueError('Duplicate SkillGraph node_id: %s' % node_id)
            seen.add(node_id)

        for edge in self.edges:
            edge.validate()
            if edge.source_node_id not in seen:
                raise ValueError('Edge source_node_id not found: %s' % edge.source_node_id)
            if edge.target_node_id not in seen:
                raise ValueError('Edge target_node_id not found: %s' % edge.target_node_id)


@dataclass(slots=True)
class SkillDocument(SerializableMixin):
    name: str
    goal: str
    source_modality: Modality
    skill_type: SkillType = SkillType.PROCEDURE
    audience: Audience = Audience.SELF
    trigger: List[str] = field(default_factory=list)
    inputs: List[str] = field(default_factory=list)
    preconditions: List[str] = field(default_factory=list)
    steps: List[SkillStep] = field(default_factory=list)
    decision_rules: List[str] = field(default_factory=list)
    anti_patterns: List[str] = field(default_factory=list)
    verification: List[str] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)
    confidence: float = 0.6
    version: str = '0.1.0'
    summary: str = ''
    tags: List[str] = field(default_factory=list)
    review_status: ReviewStatus = ReviewStatus.DRAFT
    created_at: str = field(default_factory=utc_now_iso)
    skill_id: str = field(default_factory=new_id)


@dataclass(slots=True)
class Publication(SerializableMixin):
    publication_type: PublicationType
    content: Dict[str, Any]
    path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)
    publication_id: str = field(default_factory=new_id)


@dataclass(slots=True)
class LifecycleDecision(SerializableMixin):
    decision: LifecycleDecisionType
    reason: str
    related_graph_ids: List[str] = field(default_factory=list)
    confidence: float = 0.7
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)
    decision_id: str = field(default_factory=new_id)


@dataclass(slots=True)
class SkillLineageLink(SerializableMixin):
    skill_id: str
    related_skill_id: str
    relation_type: str
    confidence: float = 0.0
    reason: str = ''
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)
    lineage_link_id: str = field(default_factory=new_id)

    @classmethod
    def from_lifecycle_decision(
        cls,
        *,
        skill_id: str,
        lifecycle_decision: Any,
    ) -> List['SkillLineageLink']:
        if hasattr(lifecycle_decision, 'to_dict'):
            lifecycle_decision = lifecycle_decision.to_dict()
        if not isinstance(lifecycle_decision, dict):
            return []

        relation_type = str(lifecycle_decision.get('decision', '')).strip().lower()
        if relation_type in {'', LifecycleDecisionType.NEW.value, LifecycleDecisionType.REJECT.value}:
            return []

        related_graph_ids = lifecycle_decision.get('related_graph_ids', [])
        if not isinstance(related_graph_ids, list):
            return []

        reason = str(lifecycle_decision.get('reason', '')).strip()
        confidence = cls._coerce_confidence(lifecycle_decision.get('confidence', 0.0))
        metadata = lifecycle_decision.get('metadata')
        metadata_payload = metadata if isinstance(metadata, dict) else {}

        links: List['SkillLineageLink'] = []
        seen: set[str] = set()
        for item in related_graph_ids:
            related_skill_id = str(item).strip()
            if not related_skill_id or related_skill_id in seen:
                continue
            seen.add(related_skill_id)
            links.append(
                cls(
                    skill_id=str(skill_id).strip(),
                    related_skill_id=related_skill_id,
                    relation_type=relation_type,
                    confidence=confidence,
                    reason=reason,
                    metadata=dict(metadata_payload),
                )
            )
        return links

    @staticmethod
    def _coerce_confidence(value: Any) -> float:
        try:
            return max(0.0, min(1.0, float(value)))
        except (TypeError, ValueError):
            return 0.0


@dataclass(slots=True)
class ReviewTask(SerializableMixin):
    skill_id: str
    decision: ReviewDecision
    reason_codes: List[str] = field(default_factory=list)
    revision_suggestions: List[str] = field(default_factory=list)
    score_snapshot: Dict[str, float] = field(default_factory=dict)
    thresholds: Dict[str, float] = field(default_factory=dict)
    review_notes: str = ''
    status: ReviewStatus = ReviewStatus.REVIEW_PENDING
    created_at: str = field(default_factory=utc_now_iso)
    review_task_id: str = field(default_factory=new_id)

    @classmethod
    def from_review_policy(
        cls,
        *,
        skill_id: str,
        review_policy: Dict[str, Any],
        review_notes: str = '',
    ) -> 'ReviewTask':
        reason_codes_raw = review_policy.get('reason_codes', [])
        reason_codes = [str(item).strip() for item in reason_codes_raw if str(item).strip()]
        decision = parse_enum(
            ReviewDecision,
            review_policy.get('decision', ReviewDecision.REVIEW_REQUIRED.value),
            'decision',
        )
        return cls(
            skill_id=skill_id,
            decision=decision,
            reason_codes=reason_codes,
            revision_suggestions=cls._build_revision_suggestions(reason_codes, decision),
            score_snapshot=cls._coerce_float_dict(review_policy.get('score_snapshot')),
            thresholds=cls._coerce_float_dict(review_policy.get('thresholds')),
            review_notes=review_notes.strip(),
            status=(
                ReviewStatus.PUBLISHED
                if decision == ReviewDecision.AUTO_PUBLISH
                else ReviewStatus.REJECTED if decision == ReviewDecision.REJECT else ReviewStatus.REVIEW_PENDING
            ),
        )

    @staticmethod
    def _coerce_float_dict(payload: Any) -> Dict[str, float]:
        if not isinstance(payload, dict):
            return {}
        output: Dict[str, float] = {}
        for key, value in payload.items():
            try:
                output[str(key)] = float(value)
            except (TypeError, ValueError):
                continue
        return output

    @staticmethod
    def _build_revision_suggestions(reason_codes: List[str], decision: ReviewDecision) -> List[str]:
        reason_to_suggestion = {
            'R_LOW_OVERALL': ['S_REBUILD_FROM_EVIDENCE'],
            'R_TRACEABILITY_CRITICAL': ['S_ADD_TRACEABLE_EVIDENCE'],
            'R_ACTIONABILITY_CRITICAL': ['S_REWRITE_ACTIONABLE_STEPS'],
            'R_COVERAGE_CRITICAL': ['S_EXPAND_EVIDENCE_COVERAGE'],
            'R_CONSISTENCY_CRITICAL': ['S_RESOLVE_CONFLICTING_STATEMENTS'],
            'R_NOISE_CRITICAL': ['S_FILTER_NOISY_EVIDENCE'],
            'Q_TRACEABILITY_LOW': ['S_ADD_TRACEABLE_EVIDENCE'],
            'Q_ACTIONABILITY_LOW': ['S_REWRITE_ACTIONABLE_STEPS'],
            'Q_COVERAGE_LOW': ['S_EXPAND_EVIDENCE_COVERAGE'],
            'Q_CONSISTENCY_LOW': ['S_RESOLVE_CONFLICTING_STATEMENTS'],
            'Q_NOISE_HIGH': ['S_FILTER_NOISY_EVIDENCE'],
            'Q_NOVELTY_LOW': ['S_INCREASE_NOVELTY_SIGNAL'],
            'Q_OVERALL_BELOW_AUTO': ['S_RERUN_AFTER_REBALANCING_SCORES'],
            'Q_MANUAL_REVIEW_DEFAULT': ['S_MANUAL_REVIEW_REQUIRED'],
            'A_MEETS_ALL_THRESHOLDS': ['S_MONITOR_POST_PUBLISH'],
            'A_HIGH_NOVELTY': ['S_CAPTURE_NOVEL_PATTERN_FOR_REUSE'],
        }
        suggestions: List[str] = []
        seen: set[str] = set()
        for code in reason_codes:
            for suggestion in reason_to_suggestion.get(code, []):
                if suggestion in seen:
                    continue
                seen.add(suggestion)
                suggestions.append(suggestion)
        if suggestions:
            return suggestions
        if decision == ReviewDecision.AUTO_PUBLISH:
            return ['S_MONITOR_POST_PUBLISH']
        if decision == ReviewDecision.REJECT:
            return ['S_REBUILD_FROM_EVIDENCE']
        return ['S_MANUAL_REVIEW_REQUIRED']


@dataclass(slots=True)
class LoadedAsset(SerializableMixin):
    asset: Asset
    evidence_units: List[EvidenceUnit]
    title_hint: str
    adapter_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class DistillBundle(SerializableMixin):
    asset: Asset
    evidence_units: List[EvidenceUnit]
    insights: List[Insight]
    skill: SkillDocument
    skill_markdown: str
    skill_graph: Optional[SkillGraph] = None
    publications: List[Publication] = field(default_factory=list)
    quality_scores: Dict[str, Any] = field(default_factory=dict)
    review_task: Optional[ReviewTask] = None
    corpus: Optional[Corpus] = None
    evidence_nodes: List[EvidenceNode] = field(default_factory=list)
    request_payload: Dict[str, Any] = field(default_factory=dict)
    artifacts: Dict[str, str] = field(default_factory=dict)
    adapter_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class LoadedCorpus(SerializableMixin):
    corpus: Corpus
    loaded_assets: List[LoadedAsset]
    evidence_units: List[EvidenceUnit]
    evidence_nodes: List[EvidenceNode] = field(default_factory=list)
    adapter_metadata: Dict[str, Any] = field(default_factory=dict)


class RequestMixin(SerializableMixin):
    def validate(self) -> None:  # pragma: no cover - interface default
        raise NotImplementedError


@dataclass(slots=True)
class CorpusAssetInput(SerializableMixin):
    source_uri: str
    modality: Modality
    title_hint: str = ''
    role: str = 'primary'
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> 'CorpusAssetInput':
        source_uri = str(payload.get('source_uri', '')).strip()
        if not source_uri:
            raise ValueError('Corpus asset input requires source_uri.')
        return cls(
            source_uri=source_uri,
            modality=parse_enum(Modality, payload.get('modality'), 'modality'),
            title_hint=str(payload.get('title_hint', '')).strip(),
            role=str(payload.get('role', 'primary')).strip() or 'primary',
            metadata=payload.get('metadata', {}) if isinstance(payload.get('metadata'), dict) else {},
        )


@dataclass(slots=True)
class CorpusDistillRequest(RequestMixin):
    name: str = ''
    assets: List[CorpusAssetInput] = field(default_factory=list)
    goal: DistillGoal = field(default_factory=DistillGoal)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> 'CorpusDistillRequest':
        assets_payload = payload.get('assets', []) if isinstance(payload, dict) else []
        assets: List[CorpusAssetInput] = []
        for item in assets_payload:
            if not isinstance(item, dict):
                raise ValueError('Each corpus asset must be an object.')
            assets.append(CorpusAssetInput.from_dict(item))
        raw_tags = payload.get('tags', []) if isinstance(payload.get('tags', []), list) else []
        tags = [str(item).strip() for item in raw_tags if str(item).strip()]
        return cls(
            name=str(payload.get('name', '')).strip(),
            assets=assets,
            goal=DistillGoal.from_dict(payload.get('goal') if isinstance(payload, dict) else None),
            tags=tags,
            metadata=payload.get('metadata', {}) if isinstance(payload.get('metadata'), dict) else {},
        )

    def validate(self) -> None:
        if not self.assets:
            raise ValueError('Corpus request requires at least one asset.')
        for index, item in enumerate(self.assets, start=1):
            if not item.source_uri.strip():
                raise ValueError('Corpus asset #%s source_uri is empty.' % index)
            if not item.role.strip():
                raise ValueError('Corpus asset #%s role is empty.' % index)

    def primary_asset_index(self) -> int:
        for index, item in enumerate(self.assets):
            if item.role.lower() == 'primary':
                return index
        return 0


@dataclass(slots=True)
class TextDistillRequest(RequestMixin):
    title: Optional[str] = None
    content: Optional[str] = None
    file_path: Optional[str] = None
    goal: DistillGoal = field(default_factory=DistillGoal)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> 'TextDistillRequest':
        return cls(
            title=payload.get('title'),
            content=payload.get('content'),
            file_path=payload.get('file_path'),
            goal=DistillGoal.from_dict(payload.get('goal')),
        )

    def validate(self) -> None:
        if not (self.content or self.file_path):
            raise ValueError('Text request requires content or file_path.')


@dataclass(slots=True)
class AudioDistillRequest(RequestMixin):
    title: Optional[str] = None
    audio_path: Optional[str] = None
    transcript: Optional[str] = None
    transcript_path: Optional[str] = None
    language: Optional[str] = None
    prompt: Optional[str] = None
    goal: DistillGoal = field(default_factory=DistillGoal)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> 'AudioDistillRequest':
        return cls(
            title=payload.get('title'),
            audio_path=payload.get('audio_path'),
            transcript=payload.get('transcript'),
            transcript_path=payload.get('transcript_path'),
            language=payload.get('language'),
            prompt=payload.get('prompt'),
            goal=DistillGoal.from_dict(payload.get('goal')),
        )

    def validate(self) -> None:
        if not (self.transcript or self.transcript_path or self.audio_path):
            raise ValueError('Audio request requires transcript, transcript_path, or audio_path.')


@dataclass(slots=True)
class ImageDistillRequest(RequestMixin):
    image_path: str
    title: Optional[str] = None
    goal: DistillGoal = field(default_factory=DistillGoal)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> 'ImageDistillRequest':
        return cls(
            image_path=payload['image_path'],
            title=payload.get('title'),
            goal=DistillGoal.from_dict(payload.get('goal')),
        )

    def validate(self) -> None:
        if not self.image_path:
            raise ValueError('Image request requires image_path.')


@dataclass(slots=True)
class TabularDistillRequest(RequestMixin):
    file_path: str
    title: Optional[str] = None
    time_column: Optional[str] = None
    value_columns: List[str] = field(default_factory=list)
    entity_columns: List[str] = field(default_factory=list)
    max_series: int = 6
    goal: DistillGoal = field(default_factory=DistillGoal)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> 'TabularDistillRequest':
        return cls(
            file_path=payload['file_path'],
            title=payload.get('title'),
            time_column=payload.get('time_column'),
            value_columns=[str(item) for item in payload.get('value_columns', [])],
            entity_columns=[str(item) for item in payload.get('entity_columns', [])],
            max_series=int(payload.get('max_series', 6)),
            goal=DistillGoal.from_dict(payload.get('goal')),
        )

    def validate(self) -> None:
        if not self.file_path:
            raise ValueError('Tabular request requires file_path.')
        if self.max_series < 1:
            raise ValueError('max_series must be >= 1.')


@dataclass(slots=True)
class VideoDistillRequest(RequestMixin):
    video_path: str
    title: Optional[str] = None
    transcript: Optional[str] = None
    transcript_path: Optional[str] = None
    language: Optional[str] = None
    prompt: Optional[str] = None
    keyframe_interval_seconds: Optional[int] = None
    max_keyframes: Optional[int] = None
    scene_threshold: Optional[float] = None
    dedupe_distance: Optional[int] = None
    goal: DistillGoal = field(default_factory=DistillGoal)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> 'VideoDistillRequest':
        return cls(
            video_path=payload['video_path'],
            title=payload.get('title'),
            transcript=payload.get('transcript'),
            transcript_path=payload.get('transcript_path'),
            language=payload.get('language'),
            prompt=payload.get('prompt'),
            keyframe_interval_seconds=payload.get('keyframe_interval_seconds'),
            max_keyframes=payload.get('max_keyframes'),
            scene_threshold=payload.get('scene_threshold'),
            dedupe_distance=payload.get('dedupe_distance'),
            goal=DistillGoal.from_dict(payload.get('goal')),
        )

    def validate(self) -> None:
        if not self.video_path:
            raise ValueError('Video request requires video_path.')
        if self.max_keyframes is not None and self.max_keyframes < 1:
            raise ValueError('max_keyframes must be >= 1.')
        if self.dedupe_distance is not None and self.dedupe_distance < 0:
            raise ValueError('dedupe_distance must be >= 0.')
        if self.scene_threshold is not None and not 0 <= self.scene_threshold <= 1:
            raise ValueError('scene_threshold must be between 0 and 1.')


DistillRequest = TypeVar('DistillRequest', bound=RequestMixin)
