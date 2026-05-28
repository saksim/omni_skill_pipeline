from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Sequence

from omni_skill_pipeline.interfaces import ArtifactRepository, ReviewQueueRepository
from omni_skill_pipeline.models import CorpusAssetRef, DistillBundle, EvidenceNode, EvidenceUnit, Publication, ReviewTask, new_id, utc_now_iso
from omni_skill_pipeline.redaction import redact_sensitive_data
from omni_skill_pipeline.utils import slugify, unique_preserve_order


class FileArtifactRepository(ArtifactRepository, ReviewQueueRepository):
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.review_queue_dir = self.base_dir / 'review_queue'
        self.review_queue_pending_dir = self.review_queue_dir / 'pending'
        self.review_queue_consumed_dir = self.review_queue_dir / 'consumed'
        self.review_queue_closed_dir = self.review_queue_dir / 'closed'

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
        if bundle.quality_scores:
            artifacts["quality_score"] = bundle_dir / "quality_score.json"
        review_task_payload = self._resolve_review_task_payload(bundle)
        if review_task_payload:
            artifacts["review_task"] = bundle_dir / "review_task.json"
        review_feedback_payload = self._resolve_review_feedback_payload(bundle)
        if review_feedback_payload:
            artifacts["review_feedback"] = bundle_dir / "review_feedback.json"
        reviewer_packet_payload = self._resolve_reviewer_packet_payload(bundle)
        if reviewer_packet_payload:
            artifacts["reviewer_packet"] = bundle_dir / "reviewer_packet.json"
        review_policy_payload = bundle.adapter_metadata.get("review_policy")
        if isinstance(review_policy_payload, dict) and review_policy_payload:
            artifacts["review_policy"] = bundle_dir / "review_policy.json"

        artifacts["asset"].write_text(
            json.dumps(redact_sensitive_data(bundle.asset.to_dict()), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        self._write_json_array(artifacts["evidence"], bundle.evidence_units)
        self._write_json_array(artifacts["insights"], bundle.insights)
        artifacts["skill"].write_text(
            json.dumps(redact_sensitive_data(bundle.skill.to_dict()), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        artifacts["skill_markdown"].write_text(str(redact_sensitive_data(bundle.skill_markdown)), encoding="utf-8")
        if bundle.corpus is not None:
            artifacts["corpus"].write_text(
                json.dumps(redact_sensitive_data(bundle.corpus.to_dict()), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            self._write_json_array(artifacts["corpus_assets"], bundle.corpus.assets)
        if bundle.evidence_nodes:
            self._write_json_array(artifacts["evidence_nodes"], bundle.evidence_nodes)
        if cross_asset_refs:
            self._write_json_array(artifacts["cross_asset_refs"], cross_asset_refs)
        if bundle.publications:
            publication_entries = self._write_publications(artifacts["publications_dir"], bundle.publications, artifacts)
            self._write_json_array(artifacts["publication_manifest"], publication_entries)
        if bundle.quality_scores:
            artifacts["quality_score"].write_text(
                json.dumps(redact_sensitive_data(bundle.quality_scores), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        if "review_task" in artifacts:
            artifacts["review_task"].write_text(
                json.dumps(redact_sensitive_data(review_task_payload), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        if "review_feedback" in artifacts:
            artifacts["review_feedback"].write_text(
                json.dumps(redact_sensitive_data(review_feedback_payload), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        if "reviewer_packet" in artifacts:
            artifacts["reviewer_packet"].write_text(
                json.dumps(redact_sensitive_data(reviewer_packet_payload), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        if "review_policy" in artifacts:
            artifacts["review_policy"].write_text(
                json.dumps(redact_sensitive_data(review_policy_payload), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        queue_item_path = self._enqueue_review_task(
            bundle=bundle,
            review_task_payload=review_task_payload,
            review_task_path=artifacts.get('review_task'),
            reviewer_packet_path=artifacts.get('reviewer_packet'),
            bundle_path=artifacts['bundle'],
        )
        if queue_item_path is not None:
            artifacts['review_queue_item'] = queue_item_path

        artifact_strings = {name: str(path) for name, path in artifacts.items()}
        bundle.artifacts = artifact_strings
        artifacts["bundle"].write_text(
            json.dumps(redact_sensitive_data(bundle.to_dict()), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return artifact_strings

    def list_review_queue(
        self,
        *,
        queue_status: str | None = 'pending',
        limit: int = 100,
        tenant_scope: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        if limit <= 0:
            return []
        entries: list[dict[str, Any]] = []
        normalized_scope = self._normalize_tenant_scope(tenant_scope)
        for item_path in self._iter_review_queue_files(queue_status):
            payload = self._read_queue_item(item_path)
            if payload is None:
                continue
            normalized_status = str(queue_status).strip().lower() if queue_status is not None else ''
            if normalized_status and normalized_status != 'all':
                payload_status = str(payload.get('queue_status', '')).strip().lower()
                if payload_status != normalized_status:
                    continue
            if not self._queue_item_matches_tenant_scope(payload, normalized_scope):
                continue
            entries.append(payload)
        entries.sort(key=lambda item: (str(item.get('enqueued_at', '')), str(item.get('review_task_id', ''))))
        return entries[:limit]

    def consume_review_task(
        self,
        *,
        consumer: str = 'review-consumer',
        tenant_scope: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        return self.claim_review_task(consumer=consumer, tenant_scope=tenant_scope)

    def claim_review_task(
        self,
        review_task_id: str | None = None,
        *,
        consumer: str = 'review-consumer',
        tenant_scope: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        target_review_task_id = str(review_task_id or '').strip()
        normalized_scope = self._normalize_tenant_scope(tenant_scope)
        queue_entry: dict[str, Any] | None = None
        if target_review_task_id:
            pending_path = self.review_queue_pending_dir / ('%s.json' % target_review_task_id)
            if not pending_path.exists():
                return None
            queue_entry = self._read_queue_item(pending_path)
            if queue_entry is None:
                return None
            if not self._queue_item_matches_tenant_scope(queue_entry, normalized_scope):
                return None
        else:
            queue_entry = next(
                iter(
                    self.list_review_queue(
                        queue_status='pending',
                        limit=1,
                        tenant_scope=normalized_scope,
                    )
                ),
                None,
            )
            if queue_entry is None:
                return None
            target_review_task_id = str(queue_entry.get('review_task_id', '')).strip()
            if not target_review_task_id:
                return None
            pending_path = self.review_queue_pending_dir / ('%s.json' % target_review_task_id)
            if not pending_path.exists():
                return None

        if queue_entry is None:
            queue_entry = self._read_queue_item(pending_path)
            if queue_entry is None:
                return None

        self._ensure_review_queue_dirs()
        consumed_path = self.review_queue_consumed_dir / pending_path.name
        consumed_payload = dict(queue_entry)
        claimed_at = utc_now_iso()
        consumed_payload['review_task_id'] = target_review_task_id
        consumed_payload['queue_status'] = 'consumed'
        consumed_payload['claimed_at'] = claimed_at
        consumed_payload['consumed_at'] = claimed_at
        consumed_payload['claimed_by'] = consumer.strip() or 'review-consumer'
        consumed_path.write_text(json.dumps(consumed_payload, ensure_ascii=False, indent=2) + "\n", encoding='utf-8')
        self._retire_queue_file(pending_path, consumed_payload)
        return consumed_payload

    def close_review_task(
        self,
        review_task_id: str,
        *,
        status: str = 'published',
        closed_by: str = 'review-operator',
        review_notes: str = '',
        decision: str | None = None,
        reason_codes: Sequence[str] | None = None,
        reviewer_edits: dict[str, Any] | None = None,
        tenant_scope: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        target_review_task_id = str(review_task_id).strip()
        if not target_review_task_id:
            return None

        self._ensure_review_queue_dirs()
        normalized_scope = self._normalize_tenant_scope(tenant_scope)
        source_path: Path | None = None
        for candidate in (
            self.review_queue_consumed_dir / ('%s.json' % target_review_task_id),
            self.review_queue_pending_dir / ('%s.json' % target_review_task_id),
            self.review_queue_closed_dir / ('%s.json' % target_review_task_id),
        ):
            if candidate.exists():
                source_path = candidate
                break
        if source_path is None:
            return None

        payload = self._read_queue_item(source_path)
        if payload is None:
            return None
        if not self._queue_item_matches_tenant_scope(payload, normalized_scope):
            return None

        closed_payload = dict(payload)
        closed_payload['review_task_id'] = target_review_task_id
        closed_payload['queue_status'] = 'closed'
        normalized_status = str(status).strip().lower()
        if normalized_status:
            closed_payload['status'] = normalized_status
        normalized_decision = self._normalize_close_decision(decision)
        if normalized_decision:
            closed_payload['decision'] = normalized_decision
        closed_payload['closed_by'] = closed_by.strip() or 'review-operator'
        closed_payload['closed_at'] = utc_now_iso()
        closed_payload['reason_codes'] = unique_preserve_order(
            self._normalize_reason_codes(reason_codes, fallback=closed_payload.get('reason_codes'))
        )
        closed_payload['reviewer_edits'] = self._normalize_reviewer_edits(
            reviewer_edits,
            fallback=closed_payload.get('reviewer_edits'),
        )
        if review_notes.strip():
            closed_payload['review_notes'] = review_notes.strip()
        else:
            closed_payload.setdefault('review_notes', '')

        closed_path = self.review_queue_closed_dir / ('%s.json' % target_review_task_id)
        closed_path.write_text(
            json.dumps(redact_sensitive_data(closed_payload), ensure_ascii=False, indent=2) + "\n",
            encoding='utf-8',
        )
        if source_path != closed_path:
            self._retire_queue_file(source_path, closed_payload)
        return closed_payload

    def update_review_task_decision(
        self,
        review_task_id: str,
        *,
        decision: str,
        reviewer: str = 'review-operator',
        reason_codes: Sequence[str] | None = None,
        review_notes: str = '',
        reviewer_edits: dict[str, Any] | None = None,
        status: str | None = None,
        tenant_scope: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        normalized_decision = self._normalize_close_decision(decision)
        if not normalized_decision:
            raise ValueError('review decision must be one of approve/reject/needs_rework.')
        if normalized_decision == 'approve':
            resolved_status = status or 'published'
        elif normalized_decision == 'reject':
            resolved_status = status or 'rejected'
        else:
            resolved_status = status or 'needs_rework'
        return self.close_review_task(
            review_task_id,
            status=resolved_status,
            closed_by=reviewer,
            review_notes=review_notes,
            decision=normalized_decision,
            reason_codes=reason_codes,
            reviewer_edits=reviewer_edits,
            tenant_scope=tenant_scope,
        )

    def _resolve_review_task_payload(self, bundle: DistillBundle) -> dict[str, Any]:
        payload = bundle.adapter_metadata.get('review_task')
        if isinstance(payload, dict):
            return dict(payload)
        if isinstance(bundle.review_task, ReviewTask):
            return bundle.review_task.to_dict()
        return {}

    def _resolve_review_feedback_payload(self, bundle: DistillBundle) -> dict[str, Any]:
        payload = bundle.adapter_metadata.get('review_feedback')
        if isinstance(payload, dict):
            return dict(payload)
        return {}

    def _resolve_reviewer_packet_payload(self, bundle: DistillBundle) -> dict[str, Any]:
        payload = bundle.adapter_metadata.get('reviewer_packet')
        if isinstance(payload, dict):
            return dict(payload)
        return {}

    def _enqueue_review_task(
        self,
        *,
        bundle: DistillBundle,
        review_task_payload: dict[str, Any],
        review_task_path: Path | None,
        reviewer_packet_path: Path | None,
        bundle_path: Path,
    ) -> Path | None:
        if not self._should_enqueue_review_task(review_task_payload):
            return None
        review_task_id = str(review_task_payload.get('review_task_id', '')).strip() or new_id()
        self._ensure_review_queue_dirs()
        pending_path = self.review_queue_pending_dir / ('%s.json' % review_task_id)
        consumed_path = self.review_queue_consumed_dir / pending_path.name
        closed_path = self.review_queue_closed_dir / pending_path.name
        if consumed_path.exists():
            self._remove_queue_file(consumed_path)
        if closed_path.exists():
            self._remove_queue_file(closed_path)

        queue_item = {
            'review_task_id': review_task_id,
            'skill_id': str(review_task_payload.get('skill_id', '')).strip() or bundle.skill.skill_id,
            'decision': str(review_task_payload.get('decision', '')).strip(),
            'status': str(review_task_payload.get('status', '')).strip(),
            'reason_codes': unique_preserve_order(review_task_payload.get('reason_codes', [])),
            'revision_suggestions': unique_preserve_order(review_task_payload.get('revision_suggestions', [])),
            'score_snapshot': dict(review_task_payload.get('score_snapshot', {}))
            if isinstance(review_task_payload.get('score_snapshot'), dict)
            else {},
            'thresholds': dict(review_task_payload.get('thresholds', {}))
            if isinstance(review_task_payload.get('thresholds'), dict)
            else {},
            'review_notes': str(review_task_payload.get('review_notes', '')).strip(),
            'queue_status': 'pending',
            'enqueued_at': utc_now_iso(),
            'organization_id': str(review_task_payload.get('organization_id', '')).strip(),
            'project_id': str(review_task_payload.get('project_id', '')).strip(),
            'review_task_path': str(review_task_path) if review_task_path is not None else '',
            'reviewer_packet_path': str(reviewer_packet_path) if reviewer_packet_path is not None else '',
            'bundle_path': str(bundle_path),
        }
        pending_path.write_text(
            json.dumps(redact_sensitive_data(queue_item), ensure_ascii=False, indent=2) + "\n",
            encoding='utf-8',
        )
        return pending_path

    def _should_enqueue_review_task(self, review_task_payload: dict[str, Any]) -> bool:
        if not review_task_payload:
            return False
        decision = str(review_task_payload.get('decision', '')).strip().lower()
        status = str(review_task_payload.get('status', '')).strip().lower()
        return decision == 'review_required' or status == 'review_pending'

    def _ensure_review_queue_dirs(self) -> None:
        self.review_queue_pending_dir.mkdir(parents=True, exist_ok=True)
        self.review_queue_consumed_dir.mkdir(parents=True, exist_ok=True)
        self.review_queue_closed_dir.mkdir(parents=True, exist_ok=True)

    def _remove_queue_file(self, path: Path) -> None:
        try:
            path.unlink(missing_ok=True)
        except PermissionError:
            try:
                os.remove(path)
            except PermissionError:
                return

    def _retire_queue_file(self, path: Path, payload: dict[str, Any]) -> None:
        if not path.exists():
            return
        try:
            path.write_text(
                json.dumps(redact_sensitive_data(payload), ensure_ascii=False, indent=2) + "\n",
                encoding='utf-8',
            )
        except OSError:
            pass
        self._remove_queue_file(path)

    def _iter_review_queue_files(self, queue_status: str | None) -> list[Path]:
        normalized = str(queue_status).strip().lower() if queue_status is not None else ''
        targets: list[Path] = []
        if not normalized or normalized == 'all':
            targets.extend([self.review_queue_pending_dir, self.review_queue_consumed_dir, self.review_queue_closed_dir])
        elif normalized == 'pending':
            targets.append(self.review_queue_pending_dir)
        elif normalized == 'consumed':
            targets.append(self.review_queue_consumed_dir)
        elif normalized == 'closed':
            targets.append(self.review_queue_closed_dir)
        else:
            return []

        paths: list[Path] = []
        for directory in targets:
            if not directory.exists():
                continue
            paths.extend(sorted(directory.glob('*.json')))
        return paths

    def _read_queue_item(self, item_path: Path) -> dict[str, Any] | None:
        try:
            payload = json.loads(item_path.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError):
            return None
        if not isinstance(payload, dict):
            return None
        payload = dict(payload)
        payload.setdefault('queue_status', item_path.parent.name)
        payload['reason_codes'] = unique_preserve_order(
            self._normalize_reason_codes(None, fallback=payload.get('reason_codes'))
        )
        payload['reviewer_edits'] = self._normalize_reviewer_edits(None, fallback=payload.get('reviewer_edits'))
        return payload

    def _normalize_close_decision(self, value: str | None) -> str:
        normalized = str(value or '').strip().lower()
        mapping = {
            'approve': 'approve',
            'approved': 'approve',
            'reject': 'reject',
            'rejected': 'reject',
            'needs_rework': 'needs_rework',
            'needs-rework': 'needs_rework',
            'needs rework': 'needs_rework',
        }
        return mapping.get(normalized, '')

    def _normalize_reason_codes(self, value: Sequence[str] | None, *, fallback: Any) -> list[str]:
        payload = value if value is not None else fallback
        if payload is None:
            return []
        if not isinstance(payload, Sequence) or isinstance(payload, (str, bytes)):
            return []
        normalized: list[str] = []
        for item in payload:
            code = str(item).strip()
            if code:
                normalized.append(code)
        return normalized

    def _normalize_reviewer_edits(self, value: dict[str, Any] | None, *, fallback: Any) -> dict[str, Any]:
        payload = value if value is not None else fallback
        if not isinstance(payload, dict):
            return {}
        normalized: dict[str, Any] = {}
        for key, item in payload.items():
            key_text = str(key).strip()
            if not key_text:
                continue
            normalized[key_text] = item
        return normalized

    def _normalize_tenant_scope(self, scope: dict[str, Any] | None) -> dict[str, str]:
        if not isinstance(scope, dict):
            return {}
        normalized: dict[str, str] = {}
        organization_id = str(scope.get('organization_id', '')).strip()
        project_id = str(scope.get('project_id', '')).strip()
        if organization_id:
            normalized['organization_id'] = organization_id
        if project_id:
            normalized['project_id'] = project_id
        return normalized

    def _queue_item_matches_tenant_scope(self, payload: dict[str, Any], scope: dict[str, str]) -> bool:
        if not scope:
            return True
        organization_id = str(payload.get('organization_id', '')).strip()
        project_id = str(payload.get('project_id', '')).strip()
        expected_organization_id = scope.get('organization_id', '')
        expected_project_id = scope.get('project_id', '')
        if expected_organization_id and organization_id != expected_organization_id:
            return False
        if expected_project_id and project_id != expected_project_id:
            return False
        return True

    def _write_json_array(self, target: Path, items: Sequence[Any]) -> None:
        payload = []
        for item in items:
            if hasattr(item, 'to_dict'):
                payload.append(redact_sensitive_data(item.to_dict()))
            else:
                payload.append(redact_sensitive_data(item))
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
                    'metadata': redact_sensitive_data(publication.metadata),
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
            references: dict[str, Any] = {}
            if isinstance(publication.content, dict):
                text = str(publication.content.get('text', '') or '')
                references_payload = publication.content.get('references')
                if isinstance(references_payload, dict):
                    references = references_payload
            target.write_text(str(redact_sensitive_data(text)), encoding='utf-8')
            self._write_publication_references(target.parent, references)
            return
        payload = publication.content if isinstance(publication.content, dict) else {'content': publication.content}
        payload = redact_sensitive_data(payload)
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def _write_publication_references(self, publications_dir: Path, references: dict[str, Any]) -> None:
        if not references:
            return
        for raw_relative_path, raw_content in references.items():
            relative_path = str(raw_relative_path).strip().replace('\\', '/')
            if not relative_path:
                continue
            normalized_parts = [part for part in relative_path.split('/') if part and part != '.']
            if not normalized_parts or any(part == '..' for part in normalized_parts):
                continue
            target = publications_dir
            for part in normalized_parts:
                target = target / part
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(str(redact_sensitive_data(raw_content)), encoding='utf-8')

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
