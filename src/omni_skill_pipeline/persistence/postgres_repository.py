from __future__ import annotations

import json
from typing import Any, Callable, Protocol

from omni_skill_pipeline.interfaces import ArtifactRepository
from omni_skill_pipeline.models import (
    DistillBundle,
    Publication,
    ReviewDecision,
    ReviewStatus,
    ReviewTask,
    SkillLineageLink,
    new_id,
    utc_now_iso,
)


class CursorProtocol(Protocol):
    def execute(self, query: str, params: tuple[Any, ...] | None = None) -> Any:
        ...

    def close(self) -> None:
        ...


class ConnectionProtocol(Protocol):
    def cursor(self) -> CursorProtocol:
        ...

    def commit(self) -> None:
        ...

    def rollback(self) -> None:
        ...

    def close(self) -> None:
        ...


ConnectFn = Callable[[str], ConnectionProtocol]


def _default_connect(dsn: str) -> ConnectionProtocol:
    try:
        import psycopg  # type: ignore
    except ImportError as exc:  # pragma: no cover - integration environment dependent
        raise RuntimeError(
            'psycopg is required for PostgresRepository. Install with: pip install psycopg[binary]'
        ) from exc
    return psycopg.connect(dsn)  # type: ignore[no-any-return]


class PostgresRepository(ArtifactRepository):
    """LC-L2-32: PostgreSQL ArtifactRepository adapter."""

    def __init__(self, dsn: str, *, connect: ConnectFn | None = None) -> None:
        self.dsn = dsn.strip()
        if not self.dsn:
            raise ValueError('PostgresRepository requires non-empty dsn.')
        self._connect = connect or _default_connect

    def save_bundle(self, bundle: DistillBundle) -> dict[str, str]:
        review_task_payload = self._resolve_review_task_payload(bundle)
        publication_payloads = self._resolve_publications(bundle)
        lineage_link_payloads = self._resolve_lineage_links(bundle)

        connection = self._connect(self.dsn)
        cursor: CursorProtocol | None = None
        try:
            cursor = connection.cursor()
            self._upsert_skill(cursor, bundle)
            self._upsert_skill_version(cursor, bundle)
            self._upsert_tenant_scope(cursor, bundle)
            if review_task_payload:
                self._upsert_review_task(cursor, skill_id=bundle.skill.skill_id, payload=review_task_payload)
            for publication_payload in publication_payloads:
                self._upsert_publication(cursor, skill_id=bundle.skill.skill_id, payload=publication_payload)
            for lineage_payload in lineage_link_payloads:
                self._upsert_lineage_link(cursor, skill_id=bundle.skill.skill_id, payload=lineage_payload)
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            if cursor is not None:
                cursor.close()
            connection.close()

        artifacts = self._build_artifact_refs(
            bundle=bundle,
            review_task_payload=review_task_payload,
            publication_payloads=publication_payloads,
            lineage_link_payloads=lineage_link_payloads,
        )
        bundle.artifacts = artifacts
        return artifacts

    def _upsert_skill(self, cursor: CursorProtocol, bundle: DistillBundle) -> None:
        skill = bundle.skill
        cursor.execute(
            """
            INSERT INTO skills (
                skill_id,
                name,
                skill_type,
                goal,
                audience,
                source_modality,
                current_version,
                confidence,
                review_status,
                tags,
                created_at,
                updated_at
            ) VALUES (
                %s::uuid,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s::jsonb,
                %s::timestamptz,
                NOW()
            )
            ON CONFLICT (skill_id) DO UPDATE SET
                name = EXCLUDED.name,
                skill_type = EXCLUDED.skill_type,
                goal = EXCLUDED.goal,
                audience = EXCLUDED.audience,
                source_modality = EXCLUDED.source_modality,
                current_version = EXCLUDED.current_version,
                confidence = EXCLUDED.confidence,
                review_status = EXCLUDED.review_status,
                tags = EXCLUDED.tags,
                updated_at = NOW()
            """,
            (
                skill.skill_id,
                skill.name,
                self._enum_value(skill.skill_type),
                skill.goal,
                self._enum_value(skill.audience),
                self._enum_value(skill.source_modality),
                skill.version,
                float(skill.confidence),
                self._enum_value(skill.review_status),
                self._json_dumps(skill.tags),
                skill.created_at,
            ),
        )

    def _upsert_skill_version(self, cursor: CursorProtocol, bundle: DistillBundle) -> None:
        skill = bundle.skill
        cursor.execute(
            """
            INSERT INTO skill_versions (
                version_id,
                skill_id,
                version,
                skill_body,
                markdown_body,
                evidence_refs,
                created_at
            ) VALUES (
                %s::uuid,
                %s::uuid,
                %s,
                %s::jsonb,
                %s,
                %s::jsonb,
                %s::timestamptz
            )
            ON CONFLICT (skill_id, version) DO UPDATE SET
                skill_body = EXCLUDED.skill_body,
                markdown_body = EXCLUDED.markdown_body,
                evidence_refs = EXCLUDED.evidence_refs
            """,
            (
                new_id(),
                skill.skill_id,
                skill.version,
                self._json_dumps(skill.to_dict()),
                bundle.skill_markdown,
                self._json_dumps(skill.evidence_refs),
                skill.created_at,
            ),
        )

    def _upsert_tenant_scope(self, cursor: CursorProtocol, bundle: DistillBundle) -> None:
        tenant_scope = self._resolve_tenant_scope(bundle)
        if not tenant_scope:
            return
        cursor.execute(
            """
            INSERT INTO tenant_scopes (
                scope_id,
                skill_id,
                organization_id,
                project_id,
                user_id,
                role,
                api_key_id,
                source,
                metadata,
                created_at
            ) VALUES (
                %s::uuid,
                %s::uuid,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s::jsonb,
                %s::timestamptz
            )
            ON CONFLICT (skill_id) DO UPDATE SET
                organization_id = EXCLUDED.organization_id,
                project_id = EXCLUDED.project_id,
                user_id = EXCLUDED.user_id,
                role = EXCLUDED.role,
                api_key_id = EXCLUDED.api_key_id,
                source = EXCLUDED.source,
                metadata = EXCLUDED.metadata
            """,
            (
                new_id(),
                bundle.skill.skill_id,
                str(tenant_scope.get('organization_id', '')).strip(),
                str(tenant_scope.get('project_id', '')).strip(),
                str(tenant_scope.get('user_id', '')).strip() or None,
                str(tenant_scope.get('role', '')).strip() or None,
                str(tenant_scope.get('api_key_id', '')).strip() or None,
                str(tenant_scope.get('source', '')).strip() or 'request_metadata',
                self._json_dumps(tenant_scope.get('metadata', {})),
                utc_now_iso(),
            ),
        )

    def _upsert_review_task(self, cursor: CursorProtocol, *, skill_id: str, payload: dict[str, Any]) -> None:
        created_at = str(payload.get('created_at', '')).strip() or utc_now_iso()
        review_status = str(payload.get('status', '')).strip() or ReviewStatus.REVIEW_PENDING.value
        closed_at = str(payload.get('closed_at', '')).strip() or None
        if closed_at is None and review_status in {ReviewStatus.PUBLISHED.value, ReviewStatus.REJECTED.value}:
            closed_at = created_at

        cursor.execute(
            """
            INSERT INTO review_tasks (
                review_task_id,
                skill_id,
                decision,
                status,
                reason_codes,
                revision_suggestions,
                score_snapshot,
                thresholds,
                review_notes,
                queue_status,
                claimed_by,
                claimed_at,
                consumed_at,
                created_at,
                closed_at
            ) VALUES (
                %s::uuid,
                %s::uuid,
                %s,
                %s,
                %s::jsonb,
                %s::jsonb,
                %s::jsonb,
                %s::jsonb,
                %s,
                %s,
                %s,
                %s::timestamptz,
                %s::timestamptz,
                %s::timestamptz,
                %s::timestamptz
            )
            ON CONFLICT (review_task_id) DO UPDATE SET
                skill_id = EXCLUDED.skill_id,
                decision = EXCLUDED.decision,
                status = EXCLUDED.status,
                reason_codes = EXCLUDED.reason_codes,
                revision_suggestions = EXCLUDED.revision_suggestions,
                score_snapshot = EXCLUDED.score_snapshot,
                thresholds = EXCLUDED.thresholds,
                review_notes = EXCLUDED.review_notes,
                queue_status = EXCLUDED.queue_status,
                claimed_by = EXCLUDED.claimed_by,
                claimed_at = EXCLUDED.claimed_at,
                consumed_at = EXCLUDED.consumed_at,
                closed_at = EXCLUDED.closed_at
            """,
            (
                str(payload.get('review_task_id', '')).strip() or new_id(),
                skill_id,
                str(payload.get('decision', '')).strip() or ReviewDecision.REVIEW_REQUIRED.value,
                review_status,
                self._json_dumps(payload.get('reason_codes', [])),
                self._json_dumps(payload.get('revision_suggestions', [])),
                self._json_dumps(payload.get('score_snapshot', {})),
                self._json_dumps(payload.get('thresholds', {})),
                str(payload.get('review_notes', '')).strip(),
                self._resolve_queue_status(payload),
                str(payload.get('claimed_by', '')).strip() or None,
                str(payload.get('claimed_at', '')).strip() or None,
                str(payload.get('consumed_at', '')).strip() or None,
                created_at,
                closed_at,
            ),
        )

    def _upsert_publication(self, cursor: CursorProtocol, *, skill_id: str, payload: dict[str, Any]) -> None:
        cursor.execute(
            """
            INSERT INTO publications (
                publication_id,
                skill_id,
                publication_type,
                path,
                content,
                metadata,
                created_at,
                updated_at
            ) VALUES (
                %s::uuid,
                %s::uuid,
                %s,
                %s,
                %s::jsonb,
                %s::jsonb,
                %s::timestamptz,
                NOW()
            )
            ON CONFLICT (publication_id) DO UPDATE SET
                skill_id = EXCLUDED.skill_id,
                publication_type = EXCLUDED.publication_type,
                path = EXCLUDED.path,
                content = EXCLUDED.content,
                metadata = EXCLUDED.metadata,
                updated_at = NOW()
            """,
            (
                str(payload.get('publication_id', '')).strip() or new_id(),
                skill_id,
                str(payload.get('publication_type', '')).strip(),
                str(payload.get('path', '')).strip() or None,
                self._json_dumps(payload.get('content', {})),
                self._json_dumps(payload.get('metadata', {})),
                str(payload.get('created_at', '')).strip() or utc_now_iso(),
            ),
        )

    def _upsert_lineage_link(self, cursor: CursorProtocol, *, skill_id: str, payload: dict[str, Any]) -> None:
        related_skill_id = str(payload.get('related_skill_id', '')).strip()
        if not related_skill_id:
            return
        relation_type = str(payload.get('relation_type', '')).strip().lower() or 'related'
        cursor.execute(
            """
            INSERT INTO lineage_links (
                lineage_link_id,
                skill_id,
                related_skill_id,
                relation_type,
                confidence,
                reason,
                metadata,
                created_at,
                updated_at
            ) VALUES (
                %s::uuid,
                %s::uuid,
                %s,
                %s,
                %s,
                %s,
                %s::jsonb,
                %s::timestamptz,
                NOW()
            )
            ON CONFLICT (skill_id, related_skill_id, relation_type) DO UPDATE SET
                confidence = EXCLUDED.confidence,
                reason = EXCLUDED.reason,
                metadata = EXCLUDED.metadata,
                updated_at = NOW()
            """,
            (
                str(payload.get('lineage_link_id', '')).strip() or new_id(),
                skill_id,
                related_skill_id,
                relation_type,
                self._coerce_float(payload.get('confidence', 0.0)),
                str(payload.get('reason', '')).strip(),
                self._json_dumps(payload.get('metadata', {})),
                str(payload.get('created_at', '')).strip() or utc_now_iso(),
            ),
        )

    def _resolve_review_task_payload(self, bundle: DistillBundle) -> dict[str, Any]:
        if isinstance(bundle.review_task, ReviewTask):
            return bundle.review_task.to_dict()
        payload = bundle.adapter_metadata.get('review_task')
        if isinstance(payload, dict):
            return dict(payload)
        return {}

    def _resolve_lineage_links(self, bundle: DistillBundle) -> list[dict[str, Any]]:
        resolved: list[SkillLineageLink] = []
        skill_id = bundle.skill.skill_id
        lineage_links_payload = bundle.adapter_metadata.get('lineage_links')
        if isinstance(lineage_links_payload, list):
            for item in lineage_links_payload:
                link = self._coerce_lineage_link(item, default_skill_id=skill_id)
                if link is not None:
                    resolved.append(link)

        if not resolved:
            lifecycle_decision = bundle.adapter_metadata.get('lifecycle_decision')
            resolved.extend(
                SkillLineageLink.from_lifecycle_decision(skill_id=skill_id, lifecycle_decision=lifecycle_decision)
            )

        deduped: dict[tuple[str, str, str], SkillLineageLink] = {}
        for item in resolved:
            normalized_skill_id = str(item.skill_id).strip() or skill_id
            normalized_related = str(item.related_skill_id).strip()
            normalized_relation = str(item.relation_type).strip().lower() or 'related'
            if not normalized_related:
                continue
            deduped[(normalized_skill_id, normalized_related, normalized_relation)] = SkillLineageLink(
                skill_id=normalized_skill_id,
                related_skill_id=normalized_related,
                relation_type=normalized_relation,
                confidence=item.confidence,
                reason=item.reason,
                metadata=item.metadata if isinstance(item.metadata, dict) else {},
                created_at=item.created_at,
                lineage_link_id=item.lineage_link_id,
            )

        return [item.to_dict() for item in deduped.values()]

    def _resolve_publications(self, bundle: DistillBundle) -> list[dict[str, Any]]:
        if bundle.publications:
            return [self._coerce_publication(item) for item in bundle.publications]
        return [
            {
                'publication_id': new_id(),
                'publication_type': 'skill_markdown',
                'path': 'SKILL.md',
                'content': {'text': bundle.skill_markdown},
                'metadata': {'source': 'bundle.skill_markdown'},
                'created_at': utc_now_iso(),
            }
        ]

    def _coerce_publication(self, publication: Publication) -> dict[str, Any]:
        content = publication.content if isinstance(publication.content, dict) else {'content': publication.content}
        path = publication.path
        if not path:
            path = 'SKILL.md' if publication.publication_type.value == 'skill_markdown' else '%s.json' % publication.publication_type.value
        return {
            'publication_id': publication.publication_id,
            'publication_type': publication.publication_type.value,
            'path': path,
            'content': content,
            'metadata': publication.metadata if isinstance(publication.metadata, dict) else {},
            'created_at': publication.created_at,
        }

    def _coerce_lineage_link(self, payload: Any, *, default_skill_id: str) -> SkillLineageLink | None:
        if isinstance(payload, SkillLineageLink):
            return payload
        if hasattr(payload, 'to_dict'):
            payload = payload.to_dict()
        if not isinstance(payload, dict):
            return None

        related_skill_id = str(payload.get('related_skill_id', payload.get('related_graph_id', ''))).strip()
        if not related_skill_id:
            return None

        relation_type = str(payload.get('relation_type', payload.get('decision', ''))).strip().lower() or 'related'
        metadata_payload = payload.get('metadata')
        return SkillLineageLink(
            skill_id=str(payload.get('skill_id', '')).strip() or default_skill_id,
            related_skill_id=related_skill_id,
            relation_type=relation_type,
            confidence=self._coerce_float(payload.get('confidence', 0.0)),
            reason=str(payload.get('reason', '')).strip(),
            metadata=metadata_payload if isinstance(metadata_payload, dict) else {},
            created_at=str(payload.get('created_at', '')).strip() or utc_now_iso(),
            lineage_link_id=str(payload.get('lineage_link_id', '')).strip() or new_id(),
        )

    def _build_artifact_refs(
        self,
        *,
        bundle: DistillBundle,
        review_task_payload: dict[str, Any],
        publication_payloads: list[dict[str, Any]],
        lineage_link_payloads: list[dict[str, Any]],
    ) -> dict[str, str]:
        skill_id = bundle.skill.skill_id
        artifacts: dict[str, str] = {
            'skill': 'postgres://skills/%s' % skill_id,
            'skill_version': 'postgres://skill_versions/%s/%s' % (skill_id, bundle.skill.version),
        }
        if review_task_payload:
            review_task_id = str(review_task_payload.get('review_task_id', '')).strip() or 'latest'
            artifacts['review_task'] = 'postgres://review_tasks/%s' % review_task_id
        if publication_payloads:
            artifacts['publication_manifest'] = 'postgres://skills/%s/publications' % skill_id
            key_count: dict[str, int] = {}
            for payload in publication_payloads:
                publication_id = str(payload.get('publication_id', '')).strip() or new_id()
                publication_type = str(payload.get('publication_type', '')).strip() or 'unknown'
                key_base = 'publication_%s' % publication_type
                key_index = key_count.get(key_base, 0) + 1
                key_count[key_base] = key_index
                key = key_base if key_index == 1 else '%s_%s' % (key_base, key_index)
                artifacts[key] = 'postgres://publications/%s' % publication_id
        if lineage_link_payloads:
            artifacts['lineage_manifest'] = 'postgres://skills/%s/lineage_links' % skill_id
            key_count = {}
            for payload in lineage_link_payloads:
                lineage_link_id = str(payload.get('lineage_link_id', '')).strip() or new_id()
                relation_type = self._artifact_key_token(str(payload.get('relation_type', '')).strip() or 'related')
                key_base = 'lineage_%s' % relation_type
                key_index = key_count.get(key_base, 0) + 1
                key_count[key_base] = key_index
                key = key_base if key_index == 1 else '%s_%s' % (key_base, key_index)
                artifacts[key] = 'postgres://lineage_links/%s' % lineage_link_id
        return artifacts

    def _resolve_queue_status(self, payload: dict[str, Any]) -> str:
        queue_status = str(payload.get('queue_status', '')).strip().lower()
        if queue_status in {'pending', 'consumed', 'closed'}:
            return queue_status
        decision = str(payload.get('decision', '')).strip().lower()
        status = str(payload.get('status', '')).strip().lower()
        if decision == ReviewDecision.REVIEW_REQUIRED.value or status == ReviewStatus.REVIEW_PENDING.value:
            return 'pending'
        if status in {ReviewStatus.PUBLISHED.value, ReviewStatus.REJECTED.value}:
            return 'closed'
        return 'pending'

    def _resolve_tenant_scope(self, bundle: DistillBundle) -> dict[str, Any]:
        adapter_scope = bundle.adapter_metadata.get('tenant_scope')
        if isinstance(adapter_scope, dict):
            return dict(adapter_scope)
        request_scope = bundle.request_payload.get('metadata')
        if isinstance(request_scope, dict):
            nested = request_scope.get('tenant_scope')
            if isinstance(nested, dict):
                return dict(nested)
        return {}

    def _json_dumps(self, payload: Any) -> str:
        return json.dumps(payload, ensure_ascii=False, default=self._json_default)

    def _enum_value(self, value: Any) -> Any:
        if hasattr(value, 'value'):
            return value.value
        return value

    def _json_default(self, value: Any) -> Any:
        if hasattr(value, 'to_dict'):
            return value.to_dict()
        if hasattr(value, 'value'):
            return value.value
        return str(value)

    def _coerce_float(self, value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def _artifact_key_token(self, value: str) -> str:
        token = ''.join(char.lower() if char.isalnum() else '_' for char in value)
        compact = '_'.join(part for part in token.split('_') if part)
        return compact or 'unknown'
