from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, Sequence

from omni_skill_pipeline.exceptions import ProviderExecutionError, ProviderUnavailableError
from omni_skill_pipeline.extraction.heuristic_atom_extractor import HeuristicAtomExtractor
from omni_skill_pipeline.interfaces import AtomExtractor
from omni_skill_pipeline.models import EvidenceNode, SemanticAtom
from omni_skill_pipeline.utils import unique_preserve_order


class LLMAtomEnhancer(Protocol):
    def extract_atoms(
        self,
        evidence_nodes: Sequence[EvidenceNode],
        *,
        seed_atoms: Sequence[SemanticAtom] | None = None,
    ) -> list[SemanticAtom]:
        ...


@dataclass(slots=True)
class LLMAtomExtractor(object):
    """LLM-enhanced atom extractor with heuristic fallback as source of truth."""

    base_extractor: AtomExtractor = field(default_factory=HeuristicAtomExtractor)
    llm_enhancer: LLMAtomEnhancer | None = None
    max_enhanced_atoms: int = 96

    def extract(self, evidence_nodes: Sequence[EvidenceNode]) -> list[SemanticAtom]:
        base_atoms = list(self.base_extractor.extract(evidence_nodes))
        if self.llm_enhancer is None or not evidence_nodes:
            return base_atoms
        try:
            llm_atoms = self.llm_enhancer.extract_atoms(evidence_nodes, seed_atoms=base_atoms)
        except (ProviderUnavailableError, ProviderExecutionError, ValueError, RuntimeError):
            return base_atoms
        except Exception:
            # Keep extraction resilient to any unexpected provider failure.
            return base_atoms
        return self._merge_atoms(base_atoms, llm_atoms)

    def _merge_atoms(self, base_atoms: Sequence[SemanticAtom], llm_atoms: Sequence[SemanticAtom]) -> list[SemanticAtom]:
        merged: list[SemanticAtom] = [item for item in base_atoms]
        seen = {
            self._atom_key(item)
            for item in base_atoms
            if item.summary.strip()
        }
        for item in llm_atoms:
            if len(merged) >= self.max_enhanced_atoms:
                break
            summary = item.summary.strip()
            if not summary:
                continue
            key = self._atom_key(item)
            if key in seen:
                continue
            seen.add(key)
            item.summary = summary
            item.evidence_refs = unique_preserve_order(item.evidence_refs)
            merged.append(item)
        return merged

    def _atom_key(self, atom: SemanticAtom) -> tuple[str, str, tuple[str, ...]]:
        refs = tuple(sorted(unique_preserve_order(atom.evidence_refs)))
        return atom.atom_type.value, atom.summary.strip().lower(), refs
