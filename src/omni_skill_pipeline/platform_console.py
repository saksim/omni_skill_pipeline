from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from omni_skill_pipeline.governance import GovernanceLedger
from omni_skill_pipeline.models import utc_now_iso


def build_platform_console_views(
    *,
    repo_root: Path,
    draft_dir: Path,
    governance_ledger: GovernanceLedger,
    tenant_scope: dict[str, str] | None,
    review_queue_items: list[dict[str, Any]],
    limit: int,
) -> dict[str, Any]:
    resolved_scope = _normalize_scope(tenant_scope)
    resolved_limit = max(1, int(limit))

    trial_run_path = (
        repo_root
        / 'docs'
        / 'working'
        / 'status'
        / 'baselines'
        / 'controlled-trial'
        / 'controlled-trial-run-report.json'
    )
    trial_metrics_path = (
        repo_root
        / 'docs'
        / 'working'
        / 'status'
        / 'baselines'
        / 'controlled-trial'
        / 'trial-metrics-report.json'
    )
    launch_readiness_path = (
        repo_root
        / 'docs'
        / 'working'
        / 'status'
        / 'baselines'
        / 'broad-launch-readiness-report.json'
    )
    operations_readiness_path = (
        repo_root
        / 'docs'
        / 'working'
        / 'status'
        / 'baselines'
        / 'operations-readiness-report.json'
    )
    agent_smoke_path = (
        repo_root
        / 'docs'
        / 'working'
        / 'status'
        / 'baselines'
        / 'controlled-trial'
        / 'agent-smoke-report.json'
    )
    release_artifacts_path = repo_root / 'docs' / 'working' / 'status' / 'baselines' / 'release_artifacts.json'
    release_consumer_smoke_path = (
        repo_root / 'docs' / 'working' / 'status' / 'baselines' / 'release_consumer_smoke.json'
    )

    trial_run_payload = _read_json_object(trial_run_path)
    trial_metrics_payload = _read_json_object(trial_metrics_path)
    launch_readiness_payload = _read_json_object(launch_readiness_path)
    operations_readiness_payload = _read_json_object(operations_readiness_path)
    agent_smoke_payload = _read_json_object(agent_smoke_path)
    release_artifacts_payload = _read_json_object(release_artifacts_path)
    release_consumer_smoke_payload = _read_json_object(release_consumer_smoke_path)

    filtered_queue = [_trim_review_queue_item(item) for item in review_queue_items][:resolved_limit]
    skill_registry = _build_skill_registry(
        draft_dir=draft_dir,
        tenant_scope=resolved_scope,
        limit=resolved_limit,
    )
    security_failures = _build_security_failures(
        trial_run_payload=trial_run_payload,
        launch_readiness_payload=launch_readiness_payload,
        limit=resolved_limit,
    )
    governance_report = governance_ledger.build_report(
        tenant_scope=resolved_scope,
        include_cost_entries=False,
        include_audit_events=False,
        include_deletion_records=False,
        include_retention_policies=False,
        limit=resolved_limit,
    )

    return {
        'schema_version': 'platform_console_views.v1',
        'generated_at_utc': utc_now_iso(),
        'tenant_scope': resolved_scope,
        'views': {
            'trial_runs': _build_trial_runs_view(
                trial_run_payload=trial_run_payload,
                limit=resolved_limit,
            ),
            'review_queue': {
                'status': 'available',
                'item_count': len(filtered_queue),
                'items': filtered_queue,
            },
            'skill_registry': skill_registry,
            'metrics': _build_metrics_view(
                trial_metrics_payload=trial_metrics_payload,
                launch_readiness_payload=launch_readiness_payload,
                operations_readiness_payload=operations_readiness_payload,
                agent_smoke_payload=agent_smoke_payload,
                release_artifacts_payload=release_artifacts_payload,
                release_consumer_smoke_payload=release_consumer_smoke_payload,
            ),
            'security_failures': security_failures,
            'cost': {
                'status': 'available',
                'cost_summary': governance_report.get('cost_summary', {}),
                'audit_summary': governance_report.get('audit_summary', {}),
                'deletion_summary': governance_report.get('deletion_summary', {}),
                'retention_policy_summary': governance_report.get('retention_policy_summary', {}),
            },
        },
        'evidence_paths': {
            'trial_run_report': str(trial_run_path),
            'trial_metrics_report': str(trial_metrics_path),
            'launch_readiness_report': str(launch_readiness_path),
            'operations_readiness_report': str(operations_readiness_path),
            'agent_smoke_report': str(agent_smoke_path),
            'release_artifacts_report': str(release_artifacts_path),
            'release_consumer_smoke_report': str(release_consumer_smoke_path),
            'draft_dir': str(draft_dir),
            'governance_ledger_root': str(governance_ledger.paths.root),
        },
    }


def _normalize_scope(scope: dict[str, str] | None) -> dict[str, str]:
    payload = scope if isinstance(scope, dict) else {}
    organization_id = str(payload.get('organization_id', '')).strip()
    project_id = str(payload.get('project_id', '')).strip()
    output: dict[str, str] = {}
    if organization_id:
        output['organization_id'] = organization_id
    if project_id:
        output['project_id'] = project_id
    return output


def _read_json_object(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    return payload


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _to_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _to_float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _build_trial_runs_view(*, trial_run_payload: dict[str, Any], limit: int) -> dict[str, Any]:
    if not trial_run_payload:
        return {
            'status': 'missing',
            'sample_count': 0,
            'run_id': '',
            'generated_at_utc': '',
            'samples': [],
        }

    samples_payload = trial_run_payload.get('samples')
    samples = samples_payload if isinstance(samples_payload, list) else []
    rows: list[dict[str, Any]] = []
    for item in samples[:limit]:
        if not isinstance(item, dict):
            continue
        loop_metrics = item.get('loop_metrics')
        loop_metrics = loop_metrics if isinstance(loop_metrics, dict) else {}
        trial_security_gate = item.get('trial_security_gate_report')
        trial_security_gate = trial_security_gate if isinstance(trial_security_gate, dict) else {}
        rows.append(
            {
                'sample_id': str(item.get('sample_id', '')).strip(),
                'modality': str(item.get('modality', '')).strip(),
                'target': str(item.get('target', '')).strip(),
                'status': str(loop_metrics.get('status', '')).strip(),
                'review_outcome': str(loop_metrics.get('review_outcome', '')).strip(),
                'agent_smoke_result': str(loop_metrics.get('agent_smoke_result', '')).strip(),
                'launch_gate_eligible': bool(loop_metrics.get('launch_gate_eligible', False)),
                'evidence_origin': str(loop_metrics.get('evidence_origin', '')).strip(),
                'security_gate_status': str(trial_security_gate.get('status', '')).strip() or 'unknown',
            }
        )

    return {
        'status': 'available',
        'run_id': str(trial_run_payload.get('run_id', '')).strip(),
        'generated_at_utc': str(trial_run_payload.get('generated_at_utc', '')).strip(),
        'sample_count': int(trial_run_payload.get('sample_count', len(samples)) or len(samples)),
        'metrics_status': str(trial_run_payload.get('metrics_status', '')).strip(),
        'ga_discussion_blocked': bool(trial_run_payload.get('ga_discussion_blocked', False)),
        'samples': rows,
    }


def _trim_review_queue_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        'review_task_id': str(item.get('review_task_id', '')).strip(),
        'skill_id': str(item.get('skill_id', '')).strip(),
        'queue_status': str(item.get('queue_status', '')).strip(),
        'status': str(item.get('status', '')).strip(),
        'decision': str(item.get('decision', '')).strip(),
        'organization_id': str(item.get('organization_id', '')).strip(),
        'project_id': str(item.get('project_id', '')).strip(),
        'claimed_by': str(item.get('claimed_by', '')).strip(),
        'claimed_at': str(item.get('claimed_at', '')).strip(),
        'closed_by': str(item.get('closed_by', '')).strip(),
        'closed_at': str(item.get('closed_at', '')).strip(),
    }


def _build_skill_registry(
    *,
    draft_dir: Path,
    tenant_scope: dict[str, str],
    limit: int,
) -> dict[str, Any]:
    if not draft_dir.exists() or not draft_dir.is_dir():
        return {'status': 'missing', 'item_count': 0, 'skills': []}

    candidates = sorted(
        draft_dir.rglob('bundle.json'),
        key=lambda path: path.stat().st_mtime if path.exists() else 0.0,
        reverse=True,
    )

    skills: list[dict[str, Any]] = []
    for path in candidates:
        payload = _read_json_object(path)
        if not payload:
            continue
        row = _build_skill_registry_row(bundle_payload=payload, bundle_path=path)
        if row is None:
            continue
        if not _skill_matches_scope(row, tenant_scope):
            continue
        skills.append(row)
        if len(skills) >= limit:
            break

    return {
        'status': 'available',
        'item_count': len(skills),
        'skills': skills,
    }


def _build_skill_registry_row(*, bundle_payload: dict[str, Any], bundle_path: Path) -> dict[str, Any] | None:
    skill_payload = bundle_payload.get('skill')
    if not isinstance(skill_payload, dict):
        return None

    review_task_payload = bundle_payload.get('review_task')
    if not isinstance(review_task_payload, dict):
        review_task_payload = {}
    adapter_metadata = bundle_payload.get('adapter_metadata')
    if not isinstance(adapter_metadata, dict):
        adapter_metadata = {}
    metadata_scope = adapter_metadata.get('tenant_scope')
    metadata_scope = metadata_scope if isinstance(metadata_scope, dict) else {}

    organization_id = str(review_task_payload.get('organization_id', '')).strip() or str(
        metadata_scope.get('organization_id', '')
    ).strip()
    project_id = str(review_task_payload.get('project_id', '')).strip() or str(
        metadata_scope.get('project_id', '')
    ).strip()
    review_status = str(review_task_payload.get('status', '')).strip() or str(
        skill_payload.get('review_status', '')
    ).strip()
    decision = str(review_task_payload.get('decision', '')).strip()

    return {
        'skill_id': str(skill_payload.get('skill_id', '')).strip(),
        'name': str(skill_payload.get('name', '')).strip(),
        'review_status': review_status,
        'review_decision': decision,
        'organization_id': organization_id,
        'project_id': project_id,
        'bundle_path': str(bundle_path),
        'updated_at_epoch': bundle_path.stat().st_mtime if bundle_path.exists() else 0.0,
    }


def _skill_matches_scope(row: dict[str, Any], scope: dict[str, str]) -> bool:
    if not scope:
        return True
    org_scope = scope.get('organization_id', '')
    project_scope = scope.get('project_id', '')
    row_org = str(row.get('organization_id', '')).strip()
    row_project = str(row.get('project_id', '')).strip()
    if org_scope:
        if not row_org or row_org != org_scope:
            return False
    if project_scope:
        if not row_project or row_project != project_scope:
            return False
    return True


def _build_metrics_view(
    *,
    trial_metrics_payload: dict[str, Any],
    launch_readiness_payload: dict[str, Any],
    operations_readiness_payload: dict[str, Any],
    agent_smoke_payload: dict[str, Any],
    release_artifacts_payload: dict[str, Any],
    release_consumer_smoke_payload: dict[str, Any],
) -> dict[str, Any]:
    trial_metrics = _as_dict(trial_metrics_payload.get('trial_metrics'))
    latency = _as_dict(trial_metrics.get('latency_ms'))
    provider_runtime = _as_dict(trial_metrics.get('provider_runtime'))
    review_quality = _as_dict(trial_metrics.get('review_quality'))
    reviewer_edit_distance = _as_dict(trial_metrics.get('reviewer_edit_distance_pct'))
    safety = _as_dict(trial_metrics.get('safety'))
    complete_loop_count = _to_int(trial_metrics.get('complete_loop_count'))
    loop_count = _to_int(trial_metrics.get('loop_count'))
    launch_summary = launch_readiness_payload.get('summary')
    launch_summary = launch_summary if isinstance(launch_summary, dict) else {}
    complete_modalities = _as_list(trial_metrics.get('complete_modalities'))

    return {
        'status': 'available',
        'trial_metrics': {
            'overall_status': str(trial_metrics_payload.get('overall_status', '')).strip(),
            'ga_discussion_blocked': bool(trial_metrics_payload.get('ga_discussion_blocked', False)),
            'complete_loop_count': complete_loop_count,
            'complete_modalities': complete_modalities,
            'job_runtime': {
                'loop_count': loop_count,
                'success_count': complete_loop_count,
                'failure_count': max(0, loop_count - complete_loop_count) if loop_count else 0,
                'average_duration_ms': _to_float(latency.get('average')),
                'duration_sample_count': _to_int(latency.get('samples')),
                'provider_failure_rate': _to_float(provider_runtime.get('provider_failure_rate')),
                'retry_count_total': _to_int(provider_runtime.get('retry_count_total')),
                'retry_count_average_per_loop': _to_float(provider_runtime.get('retry_count_average_per_loop')),
            },
            'modality_success': {
                'success_rate': (complete_loop_count / loop_count) if loop_count else 0.0,
                'complete_modality_count': len(complete_modalities),
                'complete_modalities': complete_modalities,
            },
            'human_review_scores': {
                'review_outcome_counts': _as_dict(trial_metrics.get('review_outcome_counts')),
                'median_reviewer_edit_distance_pct': _to_float(reviewer_edit_distance.get('median')),
                'reviewer_edit_distance_samples': _to_int(reviewer_edit_distance.get('samples')),
                'review_evaluable_count': _to_int(review_quality.get('review_evaluable_count')),
                'approval_rate_after_one_revision': _to_float(
                    review_quality.get('approval_rate_after_one_revision')
                ),
            },
            'agent_smoke': _build_agent_smoke_observability(
                agent_smoke_payload=agent_smoke_payload,
                review_quality=review_quality,
            ),
            'redaction_secret_failures': {
                'critical_secret_or_pii_leak_count': _to_int(safety.get('critical_secret_or_pii_leak_count')),
                'unreviewed_published_count': _to_int(safety.get('unreviewed_published_count')),
                'high_severity_incident_count': _to_int(safety.get('high_severity_incident_count')),
                'launch_security_failed_checks': _security_failed_check_ids(launch_readiness_payload),
            },
            'launch_gate_eligible_complete_loop_count': _to_int(
                ((trial_metrics.get('launch_gate_evidence') or {}).get('complete_loop_count', 0))
                if isinstance(trial_metrics.get('launch_gate_evidence'), dict)
                else 0
            ),
            'launch_gate_eligible_complete_modalities': _as_list(
                ((trial_metrics.get('launch_gate_evidence') or {}).get('complete_modalities', []))
                if isinstance(trial_metrics.get('launch_gate_evidence'), dict)
                and isinstance((trial_metrics.get('launch_gate_evidence') or {}).get('complete_modalities', []), list)
                else []
            ),
        },
        'launch_readiness': {
            'decision': str(launch_readiness_payload.get('decision', '')).strip(),
            'fail_count': int(launch_readiness_payload.get('fail_count', 0) or 0),
            'failed_checks': list(launch_readiness_payload.get('failed_checks', []))
            if isinstance(launch_readiness_payload.get('failed_checks', []), list)
            else [],
            'summary': launch_summary,
        },
        'operations_readiness': {
            'overall_status': str(operations_readiness_payload.get('overall_status', '')).strip(),
            'fail_count': _to_int(operations_readiness_payload.get('fail_count')),
            'failed_checks': _as_list(operations_readiness_payload.get('failed_checks')),
        },
        'release_artifact_evidence': _build_release_artifact_observability(
            release_artifacts_payload=release_artifacts_payload,
            release_consumer_smoke_payload=release_consumer_smoke_payload,
        ),
    }


def _build_agent_smoke_observability(
    *,
    agent_smoke_payload: dict[str, Any],
    review_quality: dict[str, Any],
) -> dict[str, Any]:
    records = [item for item in _as_list(agent_smoke_payload.get('records')) if isinstance(item, dict)]
    status_counts: dict[str, int] = {'passed': 0, 'failed': 0, 'not_run': 0}
    for item in records:
        raw = str(item.get('metrics_agent_smoke_result') or item.get('status') or '').strip().lower()
        if raw in {'passed', 'pass', 'agent_smoke_passed'}:
            status_counts['passed'] += 1
        elif raw in {'failed', 'fail', 'agent_smoke_failed'}:
            status_counts['failed'] += 1
        elif raw == 'not_run':
            status_counts['not_run'] += 1
        else:
            status_counts.setdefault(raw or 'unknown', 0)
            status_counts[raw or 'unknown'] += 1
    return {
        'success_rate': _to_float(review_quality.get('agent_smoke_success_rate')),
        'record_count': len(records),
        'status_counts': status_counts,
    }


def _build_release_artifact_observability(
    *,
    release_artifacts_payload: dict[str, Any],
    release_consumer_smoke_payload: dict[str, Any],
) -> dict[str, Any]:
    artifacts = _as_list(release_artifacts_payload.get('artifacts'))
    release_artifacts_present = bool(release_artifacts_payload)
    release_artifacts_ok = (
        release_artifacts_payload.get('schema_version') == 'omni.release_artifacts.v1'
        and bool(str(release_artifacts_payload.get('release_id', '')).strip())
        and bool(artifacts)
    )
    consumer_present = bool(release_consumer_smoke_payload)
    consumer_ok = (
        release_consumer_smoke_payload.get('schema_version') == 'release_consumer_smoke.v1'
        and str(release_consumer_smoke_payload.get('decision', '')).strip().upper() == 'PASS'
    )
    return {
        'release_artifacts_status': 'pass'
        if release_artifacts_ok
        else ('missing' if not release_artifacts_present else 'fail'),
        'release_consumer_smoke_status': 'pass' if consumer_ok else ('missing' if not consumer_present else 'fail'),
        'artifact_count': len(artifacts),
        'release_id': str(release_artifacts_payload.get('release_id', '')).strip(),
        'consumer_decision': str(release_consumer_smoke_payload.get('decision', '')).strip(),
    }


def _security_failed_check_ids(launch_readiness_payload: dict[str, Any]) -> list[str]:
    failed: list[str] = []
    for check in _as_list(launch_readiness_payload.get('checks')):
        if not isinstance(check, dict) or check.get('status') != 'fail':
            continue
        check_id = str(check.get('id', '')).strip()
        lowered = check_id.lower()
        if any(marker in lowered for marker in ('security', 'secret', 'pii', 'redaction')):
            failed.append(check_id)
    return failed


def _build_security_failures(
    *,
    trial_run_payload: dict[str, Any],
    launch_readiness_payload: dict[str, Any],
    limit: int,
) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    samples = trial_run_payload.get('samples')
    if isinstance(samples, list):
        for item in samples:
            if not isinstance(item, dict):
                continue
            gate_payload = item.get('trial_security_gate_report')
            gate_payload = gate_payload if isinstance(gate_payload, dict) else {}
            status = str(gate_payload.get('status', '')).strip().lower()
            if status == 'pass':
                continue
            failures.append(
                {
                    'source': 'trial_security_gate',
                    'sample_id': str(item.get('sample_id', '')).strip(),
                    'status': str(gate_payload.get('status', '')).strip() or 'unknown',
                    'failure_codes': list(gate_payload.get('failure_codes', []))
                    if isinstance(gate_payload.get('failure_codes', []), list)
                    else [],
                }
            )

    checks = launch_readiness_payload.get('checks')
    if isinstance(checks, list):
        for check in checks:
            if not isinstance(check, dict):
                continue
            check_id = str(check.get('id', '')).strip()
            if check.get('status') != 'fail':
                continue
            if 'security' not in check_id and 'secret' not in check_id and 'pii' not in check_id:
                continue
            failures.append(
                {
                    'source': 'launch_readiness',
                    'check_id': check_id,
                    'status': str(check.get('status', '')).strip(),
                    'details': check.get('details', ''),
                }
            )

    return {
        'status': 'available',
        'failure_count': len(failures),
        'failures': failures[:limit],
    }
