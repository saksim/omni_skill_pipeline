from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Sequence

from omni_skill_pipeline.extraction.modality.atom_strategy import ModalityAtomStrategy
from omni_skill_pipeline.models import AtomType, EvidenceNode, SemanticAtom
from omni_skill_pipeline.utils import split_sentences, unique_preserve_order

_STEP_LINE_RE = re.compile(r"^\s*(?:\d+[.)]|[-*+])\s+(?P<text>.+)$")
_PROCEDURE_HINT_RE = re.compile(
    r"^(?:first|then|next|finally|step\s+\d+|run|collect|build|apply|execute|review|检查|执行|先|然后|再|最后)\b",
    re.IGNORECASE,
)
_RULE_HINT_RE = re.compile(
    r"\b(if|when|unless|must|should|only if|if you|threshold|rollback|guardrail)\b|(?:如果|当|除非|必须|阈值|回滚|护栏)",
    re.IGNORECASE,
)
_VERIFY_HINT_RE = re.compile(
    r"\b(verify|validation|check|confirm|assert|test|smoke)\b|(?:验证|检查|确认|测试|回归)",
    re.IGNORECASE,
)
_ANTI_HINT_RE = re.compile(
    r"\b(avoid|do not|don't|never|anti-pattern|pitfall)\b|(?:避免|不要|禁止|误区|反模式)",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class _AtomCandidate:
    atom_type: AtomType
    summary: str
    source: EvidenceNode
    rule_name: str


class HeuristicAtomExtractor(object):
    """Rule-based atom extractor for TP-E5-02."""

    def __init__(
        self,
        *,
        max_atoms: int = 64,
        modality_strategy: ModalityAtomStrategy | None = None,
    ) -> None:
        self.max_atoms = max_atoms
        self.modality_strategy = modality_strategy or ModalityAtomStrategy()

    def extract(self, evidence_nodes: Sequence[EvidenceNode]) -> list[SemanticAtom]:
        candidates: list[_AtomCandidate] = []
        for node in evidence_nodes:
            text = self._node_text(node).strip()
            if not text:
                continue
            for line in self._candidate_lines(text):
                candidate = self._classify_line(line, node)
                if candidate is None:
                    continue
                candidates.append(candidate)
                if len(candidates) >= self.max_atoms:
                    break
            if len(candidates) >= self.max_atoms:
                break

        atoms = self._dedupe_and_materialize(candidates)
        if atoms:
            return atoms

        # Keep pipeline resilient when heuristics find no strong pattern.
        for node in evidence_nodes:
            text = self._node_text(node).strip()
            if not text:
                continue
            return [
                SemanticAtom(
                    atom_type=AtomType.CLAIM,
                    summary=text[:220],
                    evidence_refs=[node.evidence_id],
                    confidence=0.62,
                    attributes={
                        'source_span_ref': node.span_ref,
                        'source_modality': node.modality.value,
                        'source_content_type': node.content_type.value,
                        'heuristic_rule': 'fallback_claim',
                    },
                )
            ]
        return []

    def _node_text(self, node: EvidenceNode) -> str:
        text = node.text_content.strip() if node.text_content else ''
        if text:
            return text
        legacy = node.payload.get('legacy_content')
        if isinstance(legacy, str):
            return legacy.strip()
        return ''

    def _candidate_lines(self, text: str) -> list[str]:
        raw_lines = [item.strip() for item in text.splitlines() if item.strip()]
        candidates: list[str] = []
        for line in raw_lines:
            candidates.append(line)
            if len(line) > 100:
                candidates.extend(split_sentences(line))
        return unique_preserve_order(candidates)

    def _classify_line(self, line: str, node: EvidenceNode) -> _AtomCandidate | None:
        normalized = line.strip()
        if not normalized:
            return None

        modality_decision = self.modality_strategy.classify(node, normalized)
        if modality_decision is not None:
            return _AtomCandidate(modality_decision.atom_type, self._clean_step_prefix(normalized), node, modality_decision.rule_name)

        if _ANTI_HINT_RE.search(normalized):
            return _AtomCandidate(AtomType.ANTI_PATTERN, self._clean_step_prefix(normalized), node, 'anti_pattern_regex')
        if _VERIFY_HINT_RE.search(normalized):
            return _AtomCandidate(AtomType.VERIFICATION, self._clean_step_prefix(normalized), node, 'verification_regex')
        if _RULE_HINT_RE.search(normalized):
            return _AtomCandidate(AtomType.RULE, self._clean_step_prefix(normalized), node, 'rule_regex')
        if _STEP_LINE_RE.match(normalized) or _PROCEDURE_HINT_RE.search(normalized):
            return _AtomCandidate(AtomType.PROCEDURE, self._clean_step_prefix(normalized), node, 'procedure_regex')
        return None

    def _clean_step_prefix(self, text: str) -> str:
        match = _STEP_LINE_RE.match(text)
        if match is not None:
            return match.group('text').strip()
        return text.strip()

    def _dedupe_and_materialize(self, candidates: Sequence[_AtomCandidate]) -> list[SemanticAtom]:
        seen: set[tuple[AtomType, str]] = set()
        atoms: list[SemanticAtom] = []
        for item in candidates:
            key = (item.atom_type, item.summary.lower())
            if key in seen:
                continue
            seen.add(key)
            atoms.append(
                SemanticAtom(
                    atom_type=item.atom_type,
                    summary=item.summary,
                    evidence_refs=[item.source.evidence_id],
                    confidence=self._confidence_for(item.atom_type),
                    attributes={
                        'source_span_ref': item.source.span_ref,
                        'source_modality': item.source.modality.value,
                        'source_content_type': item.source.content_type.value,
                        'heuristic_rule': item.rule_name,
                    },
                )
            )
        return atoms

    def _confidence_for(self, atom_type: AtomType) -> float:
        if atom_type == AtomType.PROCEDURE:
            return 0.83
        if atom_type == AtomType.RULE:
            return 0.79
        if atom_type == AtomType.VERIFICATION:
            return 0.8
        if atom_type == AtomType.ANTI_PATTERN:
            return 0.78
        if atom_type == AtomType.EVENT:
            return 0.82
        if atom_type == AtomType.QUESTION:
            return 0.81
        if atom_type == AtomType.METRIC_GUARDRAIL:
            return 0.84
        return 0.62
