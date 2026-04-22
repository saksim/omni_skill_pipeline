from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Sequence

from omni_skill_pipeline.models import CorpusAssetRef, DistillBundle, EvidenceNode, EvidenceUnit, Publication
from omni_skill_pipeline.utils import slugify, unique_preserve_order


class FileArtifactRepository(object):
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_bundle(self, bundle: DistillBundle) -> Dict[str, str]:
        slug = slugify(bundle.skill.name)
        bundle_dir = self.base_dir / ("%s-%s" % (slug, bundle.skill.skill_id[:8]))
        bundle_dir.mkdir(parents=True, exist_ok=True)

        artifacts = {
            "asset": bundle_dir / "asset.json",
            "evidence": bundle_dir / "evidence.json",
            "insights": bundle_dir / "insights.json",
            "skill": bundle_dir / "skill.json",
            "skill_markdown": bundle_dir / "SKILL.md",
            "bundle": bundle_dir / "bundle.json",
        }
        cross_asset_refs = self._build_cross_asset_refs(bundle)
        if bundle.corpus is not None:
            artifacts["corpus"] = bundle_dir / "corpus.json"
            artifacts["corpus_assets"] = bundle_dir / "corpus_assets.json"
        if bundle.evidence_nodes:
            artifacts["evidence_nodes"] = bundle_dir / "evidence_nodes.json"
        if cross_asset_refs:
            artifacts["cross_asset_refs"] = bundle_dir / "cross_asset_refs.json"
        if bundle.publications:
            artifacts["publications_dir"] = bundle_dir / "publications"
            artifacts["publication_manifest"] = artifacts["publications_dir"] / "manifest.json"

        artifacts["asset"].write_text(bundle.asset.to_json() + "\n", encoding="utf-8")
        self._write_json_array(artifacts["evidence"], bundle.evidence_units)
        self._write_json_array(artifacts["insights"], bundle.insights)
        artifacts["skill"].write_text(bundle.skill.to_json() + "\n", encoding="utf-8")
        artifacts["skill_markdown"].write_text(bundle.skill_markdown, encoding="utf-8")
        if bundle.corpus is not None:
            artifacts["corpus"].write_text(bundle.corpus.to_json() + "\n", encoding="utf-8")
            self._write_json_array(artifacts["corpus_assets"], bundle.corpus.assets)
        if bundle.evidence_nodes:
            self._write_json_array(artifacts["evidence_nodes"], bundle.evidence_nodes)
        if cross_asset_refs:
            self._write_json_array(artifacts["cross_asset_refs"], cross_asset_refs)
        if bundle.publications:
            publication_entries = self._write_publications(artifacts["publications_dir"], bundle.publications, artifacts)
            self._write_json_array(artifacts["publication_manifest"], publication_entries)

        artifact_strings = {name: str(path) for name, path in artifacts.items()}
        bundle.artifacts = artifact_strings
        artifacts["bundle"].write_text(bundle.to_json() + "\n", encoding="utf-8")
        return artifact_strings

    def _write_json_array(self, target: Path, items: Sequence[Any]) -> None:
        payload = []
        for item in items:
            if hasattr(item, 'to_dict'):
                payload.append(item.to_dict())
            else:
                payload.append(item)
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def _write_publications(
        self,
        publications_dir: Path,
        publications: Sequence[Publication],
        artifacts: dict[str, Path],
    ) -> list[dict[str, Any]]:
        publications_dir.mkdir(parents=True, exist_ok=True)
        manifest: list[dict[str, Any]] = []
        key_counter: dict[str, int] = {}
        for publication in publications:
            key_base = "publication_%s" % publication.publication_type.value
            key_index = key_counter.get(key_base, 0) + 1
            key_counter[key_base] = key_index
            artifact_key = key_base if key_index == 1 else "%s_%s" % (key_base, key_index)
            output_path = publications_dir / self._resolve_publication_filename(publication)
            self._write_publication_file(output_path, publication)
            artifacts[artifact_key] = output_path
            manifest.append(
                {
                    'publication_id': publication.publication_id,
                    'publication_type': publication.publication_type.value,
                    'path': str(output_path),
                    'relative_path': output_path.name,
                    'metadata': publication.metadata,
                    'evidence_refs': unique_preserve_order(publication.metadata.get('evidence_refs', [])),
                }
            )
        return manifest

    def _resolve_publication_filename(self, publication: Publication) -> str:
        if publication.path:
            candidate = Path(publication.path).name.strip()
            if candidate:
                return candidate
        if isinstance(publication.content, dict):
            filename = str(publication.content.get('filename', '')).strip()
            if filename:
                return Path(filename).name
        return "%s.json" % publication.publication_type.value

    def _write_publication_file(self, target: Path, publication: Publication) -> None:
        if publication.publication_type.value == 'skill_markdown':
            text = ''
            if isinstance(publication.content, dict):
                text = str(publication.content.get('text', '') or '')
            target.write_text(text, encoding='utf-8')
            return
        payload = publication.content if isinstance(publication.content, dict) else {'content': publication.content}
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def _build_cross_asset_refs(self, bundle: DistillBundle) -> list[dict[str, Any]]:
        if bundle.corpus is None or len(bundle.corpus.assets) < 2:
            return []

        asset_index = {item.asset_id: item for item in bundle.corpus.assets}
        evidence_index = self._build_evidence_index(bundle.evidence_nodes, bundle.evidence_units)
        refs: list[dict[str, Any]] = []

        skill_ref = self._reference_payload(
            reference_type='skill',
            reference_id=bundle.skill.skill_id,
            summary=bundle.skill.name,
            evidence_refs=bundle.skill.evidence_refs,
            asset_index=asset_index,
            evidence_index=evidence_index,
        )
        if skill_ref is not None:
            refs.append(skill_ref)

        for insight in bundle.insights:
            insight_ref = self._reference_payload(
                reference_type='insight',
                reference_id=insight.insight_id,
                summary=insight.summary,
                evidence_refs=insight.evidence_refs,
                asset_index=asset_index,
                evidence_index=evidence_index,
            )
            if insight_ref is not None:
                refs.append(insight_ref)

        return refs

    def _build_evidence_index(
        self,
        evidence_nodes: Sequence[EvidenceNode],
        evidence_units: Sequence[EvidenceUnit],
    ) -> dict[str, dict[str, Any]]:
        indexed: dict[str, dict[str, Any]] = {}
        for node in evidence_nodes:
            indexed[node.evidence_id] = {
                'evidence_id': node.evidence_id,
                'asset_id': node.asset_id,
                'modality': node.modality.value,
                'span_ref': node.span_ref,
                'content_type': node.content_type.value,
            }
        for unit in evidence_units:
            indexed.setdefault(
                unit.evidence_id,
                {
                    'evidence_id': unit.evidence_id,
                    'asset_id': unit.asset_id,
                    'modality': '',
                    'span_ref': unit.span_ref,
                    'content_type': unit.content_type.value,
                },
            )
        return indexed

    def _reference_payload(
        self,
        *,
        reference_type: str,
        reference_id: str,
        summary: str,
        evidence_refs: Sequence[str],
        asset_index: dict[str, CorpusAssetRef],
        evidence_index: dict[str, dict[str, Any]],
    ) -> dict[str, Any] | None:
        evidence_items: list[dict[str, Any]] = []
        asset_ids: list[str] = []
        modalities: list[str] = []
        roles: list[str] = []

        for evidence_id in unique_preserve_order(evidence_refs):
            normalized_evidence_id = evidence_id.split('@', 1)[0]
            record = evidence_index.get(normalized_evidence_id)
            if record is None:
                continue
            asset = asset_index.get(record['asset_id'])
            if asset is None:
                continue
            asset_ids.append(asset.asset_id)
            modalities.append(asset.modality.value)
            roles.append(asset.role)
            evidence_items.append(
                {
                    'evidence_ref': evidence_id,
                    'evidence_id': record['evidence_id'],
                    'asset_id': asset.asset_id,
                    'modality': asset.modality.value,
                    'role': asset.role,
                    'content_type': record['content_type'],
                    'span_ref': record['span_ref'],
                    'source_uri': asset.source_uri,
                }
            )

        unique_asset_ids = unique_preserve_order(asset_ids)
        if len(unique_asset_ids) < 2:
            return None

        return {
            'reference_type': reference_type,
            'reference_id': reference_id,
            'summary': summary.strip(),
            'asset_ids': unique_asset_ids,
            'modalities': unique_preserve_order(modalities),
            'roles': unique_preserve_order(roles),
            'evidence_refs': unique_preserve_order(item['evidence_id'] for item in evidence_items),
            'evidence': evidence_items,
        }
