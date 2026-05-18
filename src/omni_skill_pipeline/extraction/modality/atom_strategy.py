from __future__ import annotations

import re
from dataclasses import dataclass

from omni_skill_pipeline.models import AtomType, ContentType, EvidenceNode, Modality

_QUESTION_HINT_RE = re.compile(
    r"(\?|^(why|what|when|where|who|how|should|can|could|would|do|does|did|is|are|was|were)\b|(?:吗|是否|为何|怎么|什么))",
    re.IGNORECASE,
)
_EVENT_HINT_RE = re.compile(
    r"\b(decision|decide|action item|incident|rollback|deploy|release|clicked|click|opened|open|trigger|triggered)\b|"
    r"(?:决定|行动项|故障|回滚|发布|点击|触发)",
    re.IGNORECASE,
)
_GUARDRAIL_HINT_RE = re.compile(
    r"(baseline|drift|change[_\s-]?point|threshold|guardrail|anomaly|slo|sla|error rate|latency|p95|p99)|"
    r"(?:基线|漂移|变点|阈值|护栏|异常)",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class ModalityAtomDecision:
    atom_type: AtomType
    rule_name: str


class ModalityAtomStrategy(object):
    def classify(self, node: EvidenceNode, line: str) -> ModalityAtomDecision | None:
        normalized = line.strip()
        if not normalized:
            return None

        if node.modality == Modality.VIDEO:
            return self._classify_video(node, normalized)
        if node.modality == Modality.TABULAR:
            return self._classify_tabular(node, normalized)
        if node.modality == Modality.AUDIO:
            return self._classify_audio(node, normalized)
        return None

    def _classify_video(self, node: EvidenceNode, line: str) -> ModalityAtomDecision | None:
        if node.content_type == ContentType.EVENT or node.span_ref.endswith(':event') or ':event:' in node.span_ref:
            return ModalityAtomDecision(atom_type=AtomType.EVENT, rule_name='video_event_span')
        if any(tag in node.tags for tag in ('block:frame_event', 'timeline:frame_event')):
            return ModalityAtomDecision(atom_type=AtomType.EVENT, rule_name='video_event_tag')
        if _EVENT_HINT_RE.search(line):
            return ModalityAtomDecision(atom_type=AtomType.EVENT, rule_name='video_event_regex')
        return None

    def _classify_tabular(self, node: EvidenceNode, line: str) -> ModalityAtomDecision | None:
        if node.content_type not in {ContentType.METRIC, ContentType.EVENT}:
            return None
        if _GUARDRAIL_HINT_RE.search(line):
            return ModalityAtomDecision(atom_type=AtomType.METRIC_GUARDRAIL, rule_name='tabular_guardrail_regex')
        return None

    def _classify_audio(self, node: EvidenceNode, line: str) -> ModalityAtomDecision | None:
        utterance_tags = {tag for tag in node.tags if tag.startswith('utterance_act:')}
        if 'utterance_act:question' in utterance_tags:
            return ModalityAtomDecision(atom_type=AtomType.QUESTION, rule_name='audio_utterance_tag')
        if _QUESTION_HINT_RE.search(line):
            return ModalityAtomDecision(atom_type=AtomType.QUESTION, rule_name='audio_question_regex')
        if 'utterance_act:decision' in utterance_tags or 'utterance_act:action_item' in utterance_tags:
            return ModalityAtomDecision(atom_type=AtomType.EVENT, rule_name='audio_utterance_tag')
        if _EVENT_HINT_RE.search(line):
            return ModalityAtomDecision(atom_type=AtomType.EVENT, rule_name='audio_event_regex')
        return None
