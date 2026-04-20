from __future__ import annotations

import re
from dataclasses import dataclass

from omni_skill_pipeline.utils import unique_preserve_order


@dataclass(slots=True)
class ParsedUtteranceSemantics:
    utterance_act: str
    speaker_role: str
    tags: list[str]


class AudioSemanticParser(object):
    _QUESTION_RE = re.compile(
        r"(\?|^(why|what|when|where|who|how|should|can|could|would|do|does|did|is|are|was|were)\b|(?:吗|是否|为何|怎么|什么))",
        re.IGNORECASE,
    )
    _DECISION_RE = re.compile(
        r"\b(decide|decided|decision|agreed|approve|approved|reject|rejected|finalize|finalized|chosen|choose|go with|settle|plan is)\b|(?:决定|同意|采用|拒绝|确认方案)",
        re.IGNORECASE,
    )
    _ACTION_RE = re.compile(
        r"\b(action|todo|to-do|follow[- ]?up|next step|owner|assign|assigned|need to|must|should|will)\b|(?:待办|跟进|负责人|需要|必须|执行)",
        re.IGNORECASE,
    )

    _SPEAKER_ROLE_RULES = [
        ("moderator", ("moderator", "host", "facilitator", "主持")),
        ("manager", ("manager", "pm", "product", "owner", "主管", "经理")),
        ("oncall", ("oncall", "sre", "ops", "运维", "值班")),
        ("engineer", ("dev", "engineer", "developer", "研发", "开发")),
        ("reviewer", ("qa", "reviewer", "审查", "测试")),
        ("customer", ("customer", "client", "user", "客户", "用户")),
    ]

    def parse(self, text: str, speaker: str | None) -> ParsedUtteranceSemantics:
        utterance_act = self._classify_utterance_act(text)
        speaker_role = self._infer_speaker_role(speaker)
        tags = unique_preserve_order(
            [
                "utterance_act:%s" % utterance_act,
                "speaker_role:%s" % speaker_role,
            ]
        )
        return ParsedUtteranceSemantics(
            utterance_act=utterance_act,
            speaker_role=speaker_role,
            tags=tags,
        )

    def _classify_utterance_act(self, text: str) -> str:
        normalized = text.strip()
        if not normalized:
            return "context"
        if self._QUESTION_RE.search(normalized):
            return "question"
        if self._DECISION_RE.search(normalized):
            return "decision"
        if self._ACTION_RE.search(normalized):
            return "action_item"
        return "context"

    def _infer_speaker_role(self, speaker: str | None) -> str:
        if not speaker:
            return "unknown"
        lowered = speaker.strip().lower()
        if not lowered:
            return "unknown"
        for role, keywords in self._SPEAKER_ROLE_RULES:
            if any(keyword in lowered for keyword in keywords):
                return role
        return "participant"
