from __future__ import annotations

from typing import Sequence

from omni_skill_pipeline.models import EvidenceNode, EvidenceUnit, LoadedAsset, Modality
from omni_skill_pipeline.transformers import evidence_units_to_nodes


class EvidenceBuilder(object):
    def build_from_evidence_units(self, evidence_units: Sequence[EvidenceUnit], *, modality: Modality) -> list[EvidenceNode]:
        return evidence_units_to_nodes(evidence_units, modality=modality)

    def build_from_loaded_asset(self, loaded_asset: LoadedAsset) -> list[EvidenceNode]:
        return self.build_from_evidence_units(
            loaded_asset.evidence_units,
            modality=loaded_asset.asset.modality,
        )

    def build_from_loaded_assets(self, loaded_assets: Sequence[LoadedAsset]) -> list[EvidenceNode]:
        nodes: list[EvidenceNode] = []
        seen = set()
        for item in loaded_assets:
            for node in self.build_from_loaded_asset(item):
                if node.evidence_id in seen:
                    continue
                seen.add(node.evidence_id)
                nodes.append(node)
        return nodes
