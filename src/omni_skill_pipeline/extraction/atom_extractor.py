from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from omni_skill_pipeline.interfaces import InsightExtractor
from omni_skill_pipeline.models import (
    AtomType,
    EvidenceNode,
    EvidenceUnit,
    InsightType,
    SemanticAtom,
)

_INSIGHT_TO_ATOM_TYPE = {
    InsightType.CONCEPT: AtomType.CLAIM,
    InsightType.PROCEDURE: AtomType.PROCEDURE,
    InsightType.RULE: AtomType.RULE,
    InsightType.ANTI_PATTERN: AtomType.ANTI_PATTERN,
    InsightType.VERIFICATION: AtomType.VERIFICATION,
    InsightType.PRECONDITION: AtomType.RULE,
}


def _to_legacy_evidence_unit(node: EvidenceNode) -> EvidenceUnit:
    content = node.text_content.strip() if node.text_content else ''
    if not content:
        legacy_content = node.payload.get('legacy_content')
        if isinstance(legacy_content, str):
            content = legacy_content
    return EvidenceUnit(
        asset_id=node.asset_id,
        span_ref=node.span_ref,
        content_type=node.content_type,
        content=content,
        speaker=node.speaker,
        confidence=node.confidence,
        tags=list(node.tags),
        evidence_id=node.evidence_id,
    )


@dataclass(slots=True)
class LegacyInsightAtomExtractor(object):
    """Bridge extractor for TP-E5-01 before dedicated atom strategies land."""

    insight_extractor: InsightExtractor

    def extract(self, evidence_nodes: Sequence[EvidenceNode]) -> list[SemanticAtom]:
        legacy_units = [_to_legacy_evidence_unit(node) for node in evidence_nodes]
        insights = self.insight_extractor.extract(legacy_units)
        atoms: list[SemanticAtom] = []
        for insight in insights:
            atom_type = _INSIGHT_TO_ATOM_TYPE.get(insight.insight_type, AtomType.CLAIM)
            atoms.append(
                SemanticAtom(
                    atom_type=atom_type,
                    summary=insight.summary,
                    evidence_refs=list(insight.evidence_refs),
                    confidence=insight.confidence,
                    attributes={
                        'legacy_insight_id': insight.insight_id,
                        'legacy_insight_type': insight.insight_type.value,
                    },
                )
            )
        return atoms
