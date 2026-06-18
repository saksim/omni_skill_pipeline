from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from omni_skill_pipeline.models import new_id, utc_now_iso


def _as_text(value: Any) -> str:
    return str(value or '').strip()


def _as_non_negative_int(value: Any) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _as_non_negative_float(value: Any) -> float:
    try:
        return max(0.0, float(value))
    except (TypeError, ValueError):
        return 0.0


def _as_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return list(value)
    if isinstance(value, tuple):
        return list(value)
    return []


@dataclass(frozen=True, slots=True)
class GovernancePaths:
    root: Path
    cost_ledger: Path
    audit_log: Path
    deletion_log: Path
    retention_policies: Path


class GovernanceLedger(object):
    def __init__(self, root: Path) -> None:
        root_path = Path(root).resolve()
        self.paths = GovernancePaths(
            root=root_path,
            cost_ledger=root_path / 'cost-ledger.jsonl',
            audit_log=root_path / 'audit-log.jsonl',
            deletion_log=root_path / 'deletion-log.jsonl',
            retention_policies=root_path / 'retention-policies.json',
        )
        self.paths.root.mkdir(parents=True, exist_ok=True)

    def record_cost_entry(self, payload: dict[str, Any]) -> dict[str, Any]:
        normalized = self._normalize_cost_entry(payload)
        self._append_jsonl(self.paths.cost_ledger, normalized)
        return normalized

    def record_audit_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        normalized = self._normalize_audit_event(payload)
        self._append_jsonl(self.paths.audit_log, normalized)
        return normalized

    def record_deletion_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        normalized = self._normalize_deletion_event(payload)
        self._append_jsonl(self.paths.deletion_log, normalized)
        self.record_audit_event(
            {
                'event_type': 'deletion_recorded',
                'status': normalized.get('status', 'recorded'),
                'organization_id': normalized.get('organization_id', ''),
                'project_id': normalized.get('project_id', ''),
                'actor': normalized.get('actor', ''),
                'api_key_id': normalized.get('api_key_id', ''),
                'skill_id': normalized.get('skill_id', ''),
                'metadata': {
                    'deletion_record_id': normalized.get('deletion_record_id', ''),
                    'deletion_mode': normalized.get('deletion_mode', ''),
                    'resource_type': normalized.get('resource_type', ''),
                    'resource_id': normalized.get('resource_id', ''),
                    'reason': normalized.get('reason', ''),
                },
            }
        )
        return normalized

    def upsert_retention_policy(self, payload: dict[str, Any]) -> dict[str, Any]:
        normalized = self._normalize_retention_policy(payload)
        policies = self._read_retention_policies()
        policy_id = normalized['policy_id']
        replaced = False
        output: list[dict[str, Any]] = []
        for item in policies:
            if _as_text(item.get('policy_id', '')) == policy_id:
                output.append(normalized)
                replaced = True
            else:
                output.append(item)
        if not replaced:
            output.append(normalized)
        self._write_json(self.paths.retention_policies, output)
        self.record_audit_event(
            {
                'event_type': 'retention_policy_upserted',
                'status': 'success',
                'organization_id': normalized.get('organization_id', ''),
                'project_id': normalized.get('project_id', ''),
                'actor': normalized.get('updated_by', ''),
                'metadata': {
                    'policy_id': normalized.get('policy_id', ''),
                    'policy_type': normalized.get('policy_type', ''),
                    'retention_days': normalized.get('retention_days', 0),
                },
            }
        )
        return normalized

    def list_retention_policies(self, *, tenant_scope: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        scope = self._normalize_scope(tenant_scope)
        policies = self._read_retention_policies()
        return [item for item in policies if self._matches_scope(item, scope)]

    def build_report(
        self,
        *,
        tenant_scope: dict[str, Any] | None = None,
        include_cost_entries: bool = False,
        include_audit_events: bool = False,
        include_deletion_records: bool = False,
        include_retention_policies: bool = True,
        limit: int = 200,
    ) -> dict[str, Any]:
        scope = self._normalize_scope(tenant_scope)
        record_limit = max(1, int(limit))

        all_cost_entries = [item for item in self._read_jsonl(self.paths.cost_ledger) if self._matches_scope(item, scope)]
        all_audit_events = [item for item in self._read_jsonl(self.paths.audit_log) if self._matches_scope(item, scope)]
        all_deletion_records = [
            item for item in self._read_jsonl(self.paths.deletion_log) if self._matches_scope(item, scope)
        ]
        all_policies = self.list_retention_policies(tenant_scope=scope)

        by_event_kind: dict[str, int] = {}
        by_provider: dict[str, int] = {}
        total_estimated_cost_usd = 0.0
        accepted_package_count = 0
        for item in all_cost_entries:
            event_kind = _as_text(item.get('event_kind', '')) or 'unknown'
            provider = _as_text(item.get('provider', '')) or 'unknown'
            by_event_kind[event_kind] = by_event_kind.get(event_kind, 0) + 1
            by_provider[provider] = by_provider.get(provider, 0) + 1
            total_estimated_cost_usd += _as_non_negative_float(item.get('estimated_cost_usd', 0.0))
            if event_kind == 'accepted_package':
                accepted_package_count += 1

        by_audit_event_type: dict[str, int] = {}
        by_audit_status: dict[str, int] = {}
        for item in all_audit_events:
            event_type = _as_text(item.get('event_type', '')) or 'unknown'
            status = _as_text(item.get('status', '')) or 'unknown'
            by_audit_event_type[event_type] = by_audit_event_type.get(event_type, 0) + 1
            by_audit_status[status] = by_audit_status.get(status, 0) + 1

        soft_delete_count = 0
        hard_delete_count = 0
        for item in all_deletion_records:
            mode = _as_text(item.get('deletion_mode', '')).lower()
            if mode == 'hard_delete':
                hard_delete_count += 1
            else:
                soft_delete_count += 1

        return {
            'schema_version': 'governance_report.v1',
            'generated_at_utc': utc_now_iso(),
            'tenant_scope': scope,
            'cost_summary': {
                'entry_count': len(all_cost_entries),
                'total_estimated_cost_usd': round(total_estimated_cost_usd, 6),
                'accepted_package_count': accepted_package_count,
                'by_event_kind': by_event_kind,
                'by_provider': by_provider,
            },
            'audit_summary': {
                'event_count': len(all_audit_events),
                'by_event_type': by_audit_event_type,
                'by_status': by_audit_status,
            },
            'deletion_summary': {
                'record_count': len(all_deletion_records),
                'soft_delete_count': soft_delete_count,
                'hard_delete_count': hard_delete_count,
            },
            'retention_policy_summary': {
                'policy_count': len(all_policies),
            },
            'cost_entries': all_cost_entries[:record_limit] if include_cost_entries else [],
            'audit_events': all_audit_events[:record_limit] if include_audit_events else [],
            'deletion_records': all_deletion_records[:record_limit] if include_deletion_records else [],
            'retention_policies': all_policies[:record_limit] if include_retention_policies else [],
        }

    def _normalize_scope(self, scope: dict[str, Any] | None) -> dict[str, str]:
        scope_payload = scope if isinstance(scope, dict) else {}
        organization_id = _as_text(scope_payload.get('organization_id', ''))
        project_id = _as_text(scope_payload.get('project_id', ''))
        normalized: dict[str, str] = {}
        if organization_id:
            normalized['organization_id'] = organization_id
        if project_id:
            normalized['project_id'] = project_id
        return normalized

    def _matches_scope(self, payload: dict[str, Any], scope: dict[str, str]) -> bool:
        if not scope:
            return True
        expected_org = _as_text(scope.get('organization_id', ''))
        expected_project = _as_text(scope.get('project_id', ''))
        organization_id = _as_text(payload.get('organization_id', ''))
        project_id = _as_text(payload.get('project_id', ''))
        if expected_org and organization_id != expected_org:
            return False
        if expected_project and project_id != expected_project:
            return False
        return True

    def _normalize_cost_entry(self, payload: dict[str, Any]) -> dict[str, Any]:
        metadata = _as_dict(payload.get('metadata', {}))
        return {
            'cost_entry_id': _as_text(payload.get('cost_entry_id', '')) or new_id(),
            'recorded_at_utc': _as_text(payload.get('recorded_at_utc', '')) or utc_now_iso(),
            'organization_id': _as_text(payload.get('organization_id', '')),
            'project_id': _as_text(payload.get('project_id', '')),
            'run_id': _as_text(payload.get('run_id', '')),
            'skill_id': _as_text(payload.get('skill_id', '')),
            'bundle_id': _as_text(payload.get('bundle_id', '')),
            'event_kind': _as_text(payload.get('event_kind', '')) or 'unspecified',
            'provider': _as_text(payload.get('provider', '')),
            'operation': _as_text(payload.get('operation', '')),
            'call_count': _as_non_negative_int(payload.get('call_count', 0)),
            'failure_count': _as_non_negative_int(payload.get('failure_count', 0)),
            'estimated_cost_usd': _as_non_negative_float(payload.get('estimated_cost_usd', 0.0)),
            'currency': _as_text(payload.get('currency', '')) or 'USD',
            'metadata': metadata,
        }

    def _normalize_audit_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        metadata = _as_dict(payload.get('metadata', {}))
        return {
            'audit_event_id': _as_text(payload.get('audit_event_id', '')) or new_id(),
            'recorded_at_utc': _as_text(payload.get('recorded_at_utc', '')) or utc_now_iso(),
            'event_type': _as_text(payload.get('event_type', '')) or 'unspecified',
            'status': _as_text(payload.get('status', '')) or 'success',
            'actor': _as_text(payload.get('actor', '')),
            'organization_id': _as_text(payload.get('organization_id', '')),
            'project_id': _as_text(payload.get('project_id', '')),
            'api_key_id': _as_text(payload.get('api_key_id', '')),
            'skill_id': _as_text(payload.get('skill_id', '')),
            'review_task_id': _as_text(payload.get('review_task_id', '')),
            'metadata': metadata,
        }

    def _normalize_deletion_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        metadata = _as_dict(payload.get('metadata', {}))
        return {
            'deletion_record_id': _as_text(payload.get('deletion_record_id', '')) or new_id(),
            'recorded_at_utc': _as_text(payload.get('recorded_at_utc', '')) or utc_now_iso(),
            'organization_id': _as_text(payload.get('organization_id', '')),
            'project_id': _as_text(payload.get('project_id', '')),
            'resource_type': _as_text(payload.get('resource_type', '')) or 'artifact',
            'resource_id': _as_text(payload.get('resource_id', '')),
            'resource_path': _as_text(payload.get('resource_path', '')),
            'deletion_mode': _as_text(payload.get('deletion_mode', '')) or 'soft_delete',
            'status': _as_text(payload.get('status', '')) or 'recorded',
            'actor': _as_text(payload.get('actor', '')),
            'api_key_id': _as_text(payload.get('api_key_id', '')),
            'skill_id': _as_text(payload.get('skill_id', '')),
            'reason': _as_text(payload.get('reason', '')),
            'metadata': metadata,
        }

    def _normalize_retention_policy(self, payload: dict[str, Any]) -> dict[str, Any]:
        organization_id = _as_text(payload.get('organization_id', ''))
        project_id = _as_text(payload.get('project_id', ''))
        policy_type = _as_text(payload.get('policy_type', '')) or 'artifact_retention'
        default_policy_id = '%s:%s:%s' % (
            organization_id or 'global',
            project_id or 'global',
            policy_type,
        )
        metadata = _as_dict(payload.get('metadata', {}))
        return {
            'policy_id': _as_text(payload.get('policy_id', '')) or default_policy_id,
            'updated_at_utc': _as_text(payload.get('updated_at_utc', '')) or utc_now_iso(),
            'updated_by': _as_text(payload.get('updated_by', '')),
            'organization_id': organization_id,
            'project_id': project_id,
            'policy_type': policy_type,
            'retention_days': _as_non_negative_int(payload.get('retention_days', 0)),
            'deletion_mode': _as_text(payload.get('deletion_mode', '')) or 'soft_delete',
            'delete_requires_review_approval': bool(payload.get('delete_requires_review_approval', True)),
            'enabled': bool(payload.get('enabled', True)),
            'metadata': metadata,
        }

    def _read_retention_policies(self) -> list[dict[str, Any]]:
        if not self.paths.retention_policies.is_file():
            return []
        try:
            payload = json.loads(self.paths.retention_policies.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError):
            return []
        if not isinstance(payload, list):
            return []
        output: list[dict[str, Any]] = []
        for item in payload:
            if isinstance(item, dict):
                output.append(dict(item))
        return output

    def _read_jsonl(self, path: Path) -> list[dict[str, Any]]:
        if not path.is_file():
            return []
        output: list[dict[str, Any]] = []
        try:
            lines = path.read_text(encoding='utf-8').splitlines()
        except OSError:
            return []
        for raw in lines:
            text = raw.strip()
            if not text:
                continue
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                output.append(payload)
        return output

    def _append_jsonl(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('a', encoding='utf-8') as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + '\n')

    def _write_json(self, path: Path, payload: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
