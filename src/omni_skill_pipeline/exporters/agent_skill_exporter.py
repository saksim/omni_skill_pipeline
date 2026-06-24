from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from omni_skill_pipeline.models import (
    AgentSkillPackage,
    AgentSkillPackageFile,
    AgentSkillPackageReference,
    AgentSkillPackageSourceBundle,
    AgentSkillTarget,
    AgentSkillValidationStatus,
    ReviewStatus,
)
from omni_skill_pipeline.utils import slugify
from omni_skill_pipeline.validation import evaluate_trial_security
from omni_skill_pipeline.governance import GovernanceLedger


@dataclass(frozen=True, slots=True)
class ExportResult:
    target: AgentSkillTarget
    skill_path: Path
    package_path: Path


class AgentSkillExporter(object):
    _TARGET_LAYOUTS = {
        AgentSkillTarget.CODEX: Path('.codex') / 'skills',
        AgentSkillTarget.CLAUDE_CODE: Path('.claude') / 'skills',
        AgentSkillTarget.OPENCODE: Path('.opencode') / 'skill',
        AgentSkillTarget.PORTABLE: Path('skills') / 'portable',
    }

    def __init__(self, *, output_root: Path) -> None:
        self.output_root = Path(output_root).resolve()
        self._governance_root = self.output_root / '.governance'

    def export_from_bundle(
        self,
        *,
        bundle_path: Path,
        target: AgentSkillTarget,
    ) -> list[ExportResult]:
        payload = self._load_bundle_payload(bundle_path)
        bundle_dir = Path(bundle_path).resolve().parent
        skill_name = self._resolve_skill_name(payload, bundle_dir=bundle_dir)
        description = self._resolve_skill_description(payload)
        source_markdown = self._resolve_source_markdown_path(payload, bundle_dir=bundle_dir)
        source_references = source_markdown.parent / 'references'
        references_payload = self._load_references_payload(source_references)
        trial_security_report = evaluate_trial_security(
            skill_markdown=source_markdown.read_text(encoding='utf-8'),
            references=references_payload,
            request_payload=payload.get('request_payload') if isinstance(payload.get('request_payload'), dict) else {},
            review_context=self._resolve_review_context(payload),
        )
        if trial_security_report.status != 'pass':
            raise ValueError(
                'Trial security gate failed before export. failure_codes=%s'
                % ','.join(trial_security_report.failure_codes)
            )

        results: list[ExportResult] = []
        for target_item in self._resolve_targets(target):
            target_dir = self.output_root / self._TARGET_LAYOUTS[target_item] / skill_name
            target_dir.mkdir(parents=True, exist_ok=True)
            skill_output_path = target_dir / 'SKILL.md'
            shutil.copy2(source_markdown, skill_output_path)
            if source_references.is_dir():
                references_output = target_dir / 'references'
                if references_output.exists():
                    shutil.rmtree(references_output)
                shutil.copytree(source_references, references_output)
            package = self._build_package(
                payload=payload,
                bundle_path=Path(bundle_path).resolve(),
                target=target_item,
                package_name=skill_name,
                description=description,
                target_dir=target_dir,
            )
            package.validate()
            package_path = target_dir / 'agent_skill_package.json'
            package_path.write_text(package.to_json() + '\n', encoding='utf-8')
            self._record_export_governance(
                payload=payload,
                target=target_item,
                package=package,
                bundle_path=Path(bundle_path).resolve(),
                package_path=package_path,
            )
            results.append(
                ExportResult(
                    target=target_item,
                    skill_path=skill_output_path,
                    package_path=package_path,
                )
            )
        return results

    def _load_bundle_payload(self, bundle_path: Path) -> dict[str, Any]:
        path = Path(bundle_path).resolve()
        if not path.is_file():
            raise ValueError('Bundle file not found: %s' % path)
        payload = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(payload, dict):
            raise ValueError('Bundle payload must be a JSON object: %s' % path)
        return payload

    def _resolve_targets(self, target: AgentSkillTarget) -> list[AgentSkillTarget]:
        if target == AgentSkillTarget.ALL:
            return [
                AgentSkillTarget.CODEX,
                AgentSkillTarget.CLAUDE_CODE,
                AgentSkillTarget.OPENCODE,
                AgentSkillTarget.PORTABLE,
            ]
        return [target]

    def _resolve_skill_name(self, payload: dict[str, Any], *, bundle_dir: Path) -> str:
        skill_payload = payload.get('skill', {})
        if isinstance(skill_payload, dict):
            name = str(skill_payload.get('name', '')).strip()
            if name:
                return slugify(name)
        return slugify(bundle_dir.name)

    def _resolve_skill_description(self, payload: dict[str, Any]) -> str:
        skill_payload = payload.get('skill', {})
        if isinstance(skill_payload, dict):
            summary = str(skill_payload.get('summary', '')).strip()
            if summary:
                return summary
            goal = str(skill_payload.get('goal', '')).strip()
            if goal:
                return goal
        return 'Exported controlled-trial skill package.'

    def _resolve_source_markdown_path(self, payload: dict[str, Any], *, bundle_dir: Path) -> Path:
        artifacts = payload.get('artifacts', {})
        if not isinstance(artifacts, dict):
            artifacts = {}
        candidates = [
            artifacts.get('publication_skill_markdown', ''),
            artifacts.get('skill_markdown', ''),
        ]
        for raw_candidate in candidates:
            path_text = str(raw_candidate).strip()
            if not path_text:
                continue
            candidate = Path(path_text)
            if not candidate.is_absolute():
                candidate = (bundle_dir / candidate).resolve()
            if candidate.is_file():
                return candidate
        raise ValueError('Unable to resolve SKILL.md from bundle artifacts.')

    def _build_package(
        self,
        *,
        payload: dict[str, Any],
        bundle_path: Path,
        target: AgentSkillTarget,
        package_name: str,
        description: str,
        target_dir: Path,
    ) -> AgentSkillPackage:
        files = self._build_files(target_dir)
        references = self._build_references(payload)
        source_bundle = self._build_source_bundle(payload, bundle_path=bundle_path)
        review_status = self._resolve_review_status(payload)
        hashes = self._build_package_hashes(files)
        return AgentSkillPackage(
            package_name=package_name,
            description=description,
            target=target,
            files=files,
            references=references,
            validation_status=AgentSkillValidationStatus.PASSED,
            source_bundle=source_bundle,
            review_status=review_status,
            hashes=hashes,
            metadata={
                'target_layout': str(self._TARGET_LAYOUTS[target] / package_name).replace('\\', '/'),
                'export_bundle_path': str(bundle_path),
                'schema_version': 'agent_skill_package.v1',
                **self._build_review_metadata(payload, review_status=review_status),
            },
        )

    def _build_files(self, target_dir: Path) -> list[AgentSkillPackageFile]:
        files: list[AgentSkillPackageFile] = []
        for path in sorted(target_dir.rglob('*')):
            if not path.is_file():
                continue
            if path.name == 'agent_skill_package.json':
                continue
            relative = path.relative_to(target_dir).as_posix()
            media_type = self._resolve_media_type(path)
            files.append(
                AgentSkillPackageFile(
                    relative_path=relative,
                    category='primary' if relative == 'SKILL.md' else 'reference',
                    required=relative == 'SKILL.md',
                    media_type=media_type,
                    size_bytes=path.stat().st_size,
                    sha256=self._sha256_file(path),
                )
            )
        return files

    def _build_references(self, payload: dict[str, Any]) -> list[AgentSkillPackageReference]:
        evidence_units = payload.get('evidence_units', [])
        if not isinstance(evidence_units, list):
            return []
        source_uri_index = self._build_reference_source_uri_index(payload)

        refs: list[AgentSkillPackageReference] = []
        for item in evidence_units:
            if not isinstance(item, dict):
                continue
            evidence_id = str(item.get('evidence_id', '')).strip()
            if not evidence_id:
                continue
            span_ref = str(item.get('span_ref', '')).strip()
            title = 'Evidence %s' % evidence_id
            if span_ref:
                title = '%s (%s)' % (title, span_ref)
            source_uri = str(source_uri_index.get(evidence_id, '')).strip() or 'bundle://evidence'
            refs.append(
                AgentSkillPackageReference(
                    reference_id=evidence_id,
                    title=title,
                    source_uri=source_uri,
                    reference_type='evidence',
                    evidence_refs=[evidence_id],
                )
            )
        return refs

    def _build_reference_source_uri_index(self, payload: dict[str, Any]) -> dict[str, str]:
        default_source_uri = ''
        asset_payload = payload.get('asset', {})
        if isinstance(asset_payload, dict):
            default_source_uri = str(asset_payload.get('source_uri', '')).strip()

        index: dict[str, str] = {}
        corpus_assets = payload.get('corpus_assets', [])
        if isinstance(corpus_assets, list):
            corpus_asset_map: dict[str, str] = {}
            for item in corpus_assets:
                if not isinstance(item, dict):
                    continue
                asset_id = str(item.get('asset_id', '')).strip()
                if not asset_id:
                    continue
                source_uri = str(item.get('source_uri', '')).strip()
                if source_uri:
                    corpus_asset_map[asset_id] = source_uri
            evidence_units = payload.get('evidence_units', [])
            if isinstance(evidence_units, list):
                for unit in evidence_units:
                    if not isinstance(unit, dict):
                        continue
                    evidence_id = str(unit.get('evidence_id', '')).strip()
                    if not evidence_id:
                        continue
                    asset_id = str(unit.get('asset_id', '')).strip()
                    source_uri = corpus_asset_map.get(asset_id, '')
                    if source_uri:
                        index[evidence_id] = source_uri

        evidence_units = payload.get('evidence_units', [])
        if isinstance(evidence_units, list):
            for unit in evidence_units:
                if not isinstance(unit, dict):
                    continue
                evidence_id = str(unit.get('evidence_id', '')).strip()
                if not evidence_id or evidence_id in index:
                    continue
                if default_source_uri:
                    index[evidence_id] = default_source_uri
        return index

    def _build_source_bundle(self, payload: dict[str, Any], *, bundle_path: Path) -> AgentSkillPackageSourceBundle:
        skill_payload = payload.get('skill', {})
        graph_payload = payload.get('skill_graph', {})
        corpus_payload = payload.get('corpus', {})
        artifacts = payload.get('artifacts', {})
        return AgentSkillPackageSourceBundle(
            bundle_id=bundle_path.parent.name,
            graph_id=str(graph_payload.get('graph_id', '')).strip() if isinstance(graph_payload, dict) else '',
            skill_id=str(skill_payload.get('skill_id', '')).strip() if isinstance(skill_payload, dict) else '',
            corpus_id=str(corpus_payload.get('corpus_id', '')).strip() if isinstance(corpus_payload, dict) else '',
            artifact_manifest_path=(
                str(artifacts.get('publication_manifest', '')).strip() if isinstance(artifacts, dict) else ''
            ),
        )

    def _resolve_review_status(self, payload: dict[str, Any]) -> ReviewStatus:
        skill_status = self._coerce_review_status(
            self._read_nested_status(payload.get('skill'), key='review_status'),
            default=ReviewStatus.DRAFT,
        )
        if skill_status in {ReviewStatus.PUBLISHED, ReviewStatus.REJECTED}:
            return skill_status

        review_task_payload = self._resolve_review_task_payload(payload)
        task_status = self._coerce_review_status(
            self._read_nested_status(review_task_payload, key='status'),
            default=ReviewStatus.DRAFT,
        )
        if task_status in {ReviewStatus.PUBLISHED, ReviewStatus.REJECTED}:
            return task_status

        task_decision = str(review_task_payload.get('decision', '')).strip().lower()
        if task_decision in {'auto_publish', 'approve', 'approved'} and task_status == ReviewStatus.PUBLISHED:
            return ReviewStatus.PUBLISHED

        if skill_status == ReviewStatus.REVIEW_PENDING or task_status == ReviewStatus.REVIEW_PENDING:
            return ReviewStatus.REVIEW_PENDING
        return ReviewStatus.DRAFT

    def _read_nested_status(self, payload: Any, *, key: str) -> str:
        if not isinstance(payload, dict):
            return ''
        return str(payload.get(key, '')).strip().lower()

    def _coerce_review_status(self, raw: str, *, default: ReviewStatus) -> ReviewStatus:
        normalized = str(raw or '').strip().lower()
        if normalized in {'approved', 'approve'}:
            return ReviewStatus.PUBLISHED
        if normalized in {'review_required', 'needs_rework'}:
            return ReviewStatus.REVIEW_PENDING
        try:
            return ReviewStatus(normalized)
        except ValueError:
            return default

    def _resolve_review_task_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        review_task_payload = payload.get('review_task')
        if isinstance(review_task_payload, dict):
            return dict(review_task_payload)
        adapter_metadata = payload.get('adapter_metadata')
        if isinstance(adapter_metadata, dict):
            adapter_review_task = adapter_metadata.get('review_task')
            if isinstance(adapter_review_task, dict):
                return dict(adapter_review_task)
        return {}

    def _build_review_metadata(self, payload: dict[str, Any], *, review_status: ReviewStatus) -> dict[str, str]:
        review_task_payload = self._resolve_review_task_payload(payload)
        metadata: dict[str, str] = {'review_status_source': 'skill'}
        task_status = self._coerce_review_status(
            self._read_nested_status(review_task_payload, key='status'),
            default=ReviewStatus.DRAFT,
        )
        task_decision = str(review_task_payload.get('decision', '')).strip().lower()
        task_matches_final_status = task_status == review_status
        task_auto_published = review_status == ReviewStatus.PUBLISHED and task_decision in {
            'auto_publish',
            'approve',
            'approved',
        }
        if review_task_payload and (task_matches_final_status or task_auto_published):
            metadata['review_status_source'] = 'review_task'
        review_task_id = str(review_task_payload.get('review_task_id', '')).strip()
        if review_task_id:
            metadata['review_task_id'] = review_task_id
        decision = str(review_task_payload.get('decision', '')).strip()
        if decision:
            metadata['review_decision'] = decision
        return metadata

    def _resolve_legacy_review_status(self, payload: dict[str, Any]) -> ReviewStatus:
        skill_payload = payload.get('skill', {})
        if isinstance(skill_payload, dict):
            raw = str(skill_payload.get('review_status', '')).strip().lower()
            if raw:
                try:
                    return ReviewStatus(raw)
                except ValueError:
                    return ReviewStatus.DRAFT
        return ReviewStatus.DRAFT

    def _build_package_hashes(self, files: list[AgentSkillPackageFile]) -> dict[str, str]:
        skill_hash = ''
        digest_source: list[str] = []
        for item in files:
            digest_source.append('%s:%s' % (item.relative_path, item.sha256))
            if item.relative_path == 'SKILL.md':
                skill_hash = item.sha256
        digest_source.sort()
        package_digest = hashlib.sha256('\n'.join(digest_source).encode('utf-8')).hexdigest()
        return {
            'package_files_sha256': package_digest,
            'skill_markdown_sha256': skill_hash or package_digest,
        }

    def _resolve_media_type(self, path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix == '.md':
            return 'text/markdown'
        if suffix == '.json':
            return 'application/json'
        if suffix == '.txt':
            return 'text/plain'
        return 'application/octet-stream'

    def _sha256_file(self, path: Path) -> str:
        digest = hashlib.sha256()
        with path.open('rb') as handle:
            while True:
                chunk = handle.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
        return digest.hexdigest()

    def _load_references_payload(self, references_dir: Path) -> dict[str, str]:
        if not references_dir.is_dir():
            return {}
        output: dict[str, str] = {}
        for path in sorted(references_dir.rglob('*')):
            if not path.is_file():
                continue
            output[path.relative_to(references_dir).as_posix()] = path.read_text(encoding='utf-8')
        return output

    def _resolve_review_context(self, payload: dict[str, Any]) -> dict[str, Any]:
        adapter_metadata = payload.get('adapter_metadata')
        if not isinstance(adapter_metadata, dict):
            return {}
        reviewer_packet = adapter_metadata.get('reviewer_packet')
        if isinstance(reviewer_packet, dict):
            return reviewer_packet
        return {}

    def _record_export_governance(
        self,
        *,
        payload: dict[str, Any],
        target: AgentSkillTarget,
        package: AgentSkillPackage,
        bundle_path: Path,
        package_path: Path,
    ) -> None:
        governance_ledger = GovernanceLedger(self._governance_root)
        scope = self._resolve_tenant_scope(payload)
        review_task_payload = self._resolve_review_task_payload(payload)
        review_task_id = str(review_task_payload.get('review_task_id', '')).strip()
        skill_id = str(package.source_bundle.skill_id or '').strip()
        governance_ledger.record_audit_event(
            {
                **scope,
                'event_type': 'skill_exported',
                'status': 'success',
                'skill_id': skill_id,
                'review_task_id': review_task_id,
                'metadata': {
                    'target': target.value,
                    'package_id': package.package_id,
                    'bundle_path': str(bundle_path),
                    'package_path': str(package_path),
                },
            }
        )
        governance_ledger.record_cost_entry(
            {
                **scope,
                'run_id': review_task_id or skill_id or package.package_id,
                'skill_id': skill_id,
                'bundle_id': str(package.source_bundle.bundle_id or '').strip(),
                'event_kind': 'accepted_package' if package.review_status.value == 'published' else 'skill_export',
                'provider': 'exporter',
                'operation': 'export.%s' % target.value,
                'call_count': 1,
                'failure_count': 0,
                'estimated_cost_usd': 0.0,
                'currency': 'USD',
                'metadata': {
                    'package_id': package.package_id,
                    'package_path': str(package_path),
                },
            }
        )

    def _resolve_tenant_scope(self, payload: dict[str, Any]) -> dict[str, str]:
        adapter_metadata = payload.get('adapter_metadata')
        if not isinstance(adapter_metadata, dict):
            return {}
        tenant_scope = adapter_metadata.get('tenant_scope')
        if not isinstance(tenant_scope, dict):
            return {}
        organization_id = str(tenant_scope.get('organization_id', '')).strip()
        project_id = str(tenant_scope.get('project_id', '')).strip()
        output: dict[str, str] = {}
        if organization_id:
            output['organization_id'] = organization_id
        if project_id:
            output['project_id'] = project_id
        return output

    def _resolve_review_task_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        adapter_metadata = payload.get('adapter_metadata')
        if not isinstance(adapter_metadata, dict):
            return {}
        review_task_payload = adapter_metadata.get('review_task')
        if isinstance(review_task_payload, dict):
            return dict(review_task_payload)
        return {}
