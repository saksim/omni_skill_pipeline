from __future__ import annotations

from typing import Optional
from typing import Sequence

from omni_skill_pipeline.models import ContentType, EvidenceNode, EvidenceUnit, LoadedAsset, Modality, TimeRangeRef
from omni_skill_pipeline.transformers import evidence_units_to_nodes


class EvidenceBuilder(object):
    def build_from_evidence_units(self, evidence_units: Sequence[EvidenceUnit], *, modality: Modality) -> list[EvidenceNode]:
        nodes = evidence_units_to_nodes(evidence_units, modality=modality)
        if modality == Modality.VIDEO:
            return self._attach_video_frame_lineage(nodes)
        if modality == Modality.TABULAR:
            return self._attach_timeseries_lineage(nodes)
        return nodes

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

    def _attach_video_frame_lineage(self, nodes: Sequence[EvidenceNode]) -> list[EvidenceNode]:
        frame_parents: dict[str, EvidenceNode] = {}
        ordered: list[EvidenceNode] = []
        inserted_parents: set[str] = set()

        for node in nodes:
            frame_span = self._extract_frame_parent_span(node)
            if frame_span is not None:
                parent = frame_parents.get(frame_span)
                if parent is None:
                    parent = EvidenceNode(
                        asset_id=node.asset_id,
                        modality=node.modality,
                        content_type=ContentType.SCENE,
                        span_ref=frame_span,
                        text_content='Frame evidence group %s' % frame_span,
                        payload={
                            'lineage_role': 'frame_anchor',
                            'lineage_span': frame_span,
                            'child_types': [],
                        },
                        time_range=self._frame_time_range(frame_span),
                        tags=['lineage:frame_anchor'],
                    )
                    frame_parents[frame_span] = parent
                self._link_parent_child(parent=parent, child=node)
                child_types = parent.payload.get('child_types', [])
                if isinstance(child_types, list):
                    self._append_unique(child_types, node.content_type.value)
                    parent.payload['child_types'] = child_types
                if parent.evidence_id not in inserted_parents:
                    ordered.append(parent)
                    inserted_parents.add(parent.evidence_id)
            ordered.append(node)

        return ordered

    def _attach_timeseries_lineage(self, nodes: Sequence[EvidenceNode]) -> list[EvidenceNode]:
        metric_nodes = {
            node.span_ref: node
            for node in nodes
            if node.content_type == ContentType.METRIC and node.span_ref.startswith('timeseries:metric:')
        }
        overview_node = next(
            (
                node
                for node in nodes
                if node.content_type == ContentType.METRIC and node.span_ref == 'timeseries:overview:0001'
            ),
            None,
        )

        for node in nodes:
            if node.content_type != ContentType.EVENT or not node.span_ref.startswith('timeseries:event:'):
                continue
            metric_span = node.span_ref.replace('timeseries:event:', 'timeseries:metric:', 1)
            parent = metric_nodes.get(metric_span) or overview_node
            if parent is None:
                continue
            self._link_parent_child(parent=parent, child=node)

        return list(nodes)

    def _extract_frame_parent_span(self, node: EvidenceNode) -> Optional[str]:
        if node.content_type not in {ContentType.OCR, ContentType.SCENE, ContentType.EVENT, ContentType.SPEECH}:
            return None
        if not node.span_ref.startswith('frame:'):
            return None
        parts = node.span_ref.split(':')
        if len(parts) < 3:
            return None
        if parts[2] in {'ocr', 'scene', 'event', 'subtitle', 'speech'}:
            return ':'.join(parts[:2])
        return None

    def _frame_time_range(self, frame_span: str) -> Optional[TimeRangeRef]:
        if '@' not in frame_span:
            return None
        raw_time = frame_span.split('@', 1)[1]
        if raw_time.endswith('s'):
            raw_time = raw_time[:-1]
        try:
            millis = int(round(float(raw_time) * 1000))
        except ValueError:
            return None
        return TimeRangeRef(start_ms=millis, end_ms=millis)

    def _link_parent_child(self, *, parent: EvidenceNode, child: EvidenceNode) -> None:
        self._append_unique(parent.children, child.evidence_id)
        self._append_unique(child.parents, parent.evidence_id)
        self._append_unique(child.derived_from, parent.evidence_id)

    def _append_unique(self, items: list[str], value: str) -> None:
        if value and value not in items:
            items.append(value)
