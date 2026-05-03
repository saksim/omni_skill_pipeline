from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / 'scripts' / 'run_release_switch_validation.py'


def _plan_payload(
    stage_names: list[str],
    *,
    include_command: bool = True,
    stage_output_paths: dict[str, Path] | None = None,
    stage_commands: dict[str, list[str]] | None = None,
) -> dict[str, object]:
    stages: list[dict[str, object]] = []
    for stage_name in stage_names:
        stage_payload: dict[str, object] = {'name': stage_name}
        if include_command:
            command: list[str]
            if stage_commands and stage_name in stage_commands:
                command = list(stage_commands[stage_name])
            else:
                command = ['python3', '-m', 'unittest', stage_name]
                output_path = (stage_output_paths or {}).get(stage_name)
                if output_path is not None:
                    command.extend(['--output', str(output_path.resolve())])
            stage_payload['command'] = command
        stages.append(stage_payload)
    return {
        'stage_count': len(stages),
        'stages': stages,
    }


def _release_gate_stage_contract_commands(
    *,
    beta_output: Path,
    ga_output: Path,
    roadmap_output: Path,
    coverage_fail_under: float = 50.0,
) -> dict[str, list[str]]:
    return {
        'beta_gate': [
            'python3',
            'scripts/run_linux_validation_suite.py',
            '--python',
            'python3',
            '--stages',
            'ci',
            'container_smoke',
            'doc_sync',
            'quality_regression',
            'perf_cost_baseline',
            '--coverage-fail-under',
            str(float(coverage_fail_under)),
            '--output',
            str(beta_output.resolve()),
        ],
        'ga_gate': [
            'python3',
            'scripts/run_linux_validation_suite.py',
            '--python',
            'python3',
            '--stages',
            'postgres_soak',
            'postgres_ga',
            'worker_ga',
            'review_queue_ga',
            'provider_ga',
            'calibration_ga',
            '--output',
            str(ga_output.resolve()),
        ],
        'roadmap_gate': [
            'python3',
            'scripts/run_linux_validation_suite.py',
            '--python',
            'python3',
            '--stages',
            'roadmap_extension',
            '--output',
            str(roadmap_output.resolve()),
        ],
    }


def _expected_bulk_strategy_signature_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'decision': str(bulk_view.get('decision') or ''),
        'gate_status_bitmap': list(bulk_view.get('gate_status_bitmap') or []),
        'pass_gate_indices': list(bulk_view.get('pass_gate_indices') or []),
        'hold_gate_indices': list(bulk_view.get('hold_gate_indices') or []),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_domain_rollup_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'decision': str(bulk_view.get('decision') or ''),
        'domain_rollup': dict(bulk_view.get('domain_rollup') or {}),
        'gate_domain_index': dict(bulk_view.get('gate_domain_index') or {}),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_evidence_profile_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'decision': str(bulk_view.get('decision') or ''),
        'evidence_file_count': int(bulk_view.get('evidence_file_count') or 0),
        'evidence_status_counts': dict(bulk_view.get('evidence_status_counts') or {}),
        'evidence_freshness_counts': dict(bulk_view.get('evidence_freshness_counts') or {}),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_gate_status_index_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'decision': str(bulk_view.get('decision') or ''),
        'gate_names': list(bulk_view.get('gate_names') or []),
        'gate_status_bitmap': list(bulk_view.get('gate_status_bitmap') or []),
        'gate_status_index': dict(bulk_view.get('gate_status_index') or {}),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_composite_profile_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'decision': str(bulk_view.get('decision') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_strategy_envelope_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'gate_count': int(bulk_view.get('gate_count') or 0),
        'pass_count': int(bulk_view.get('pass_count') or 0),
        'hold_count': int(bulk_view.get('hold_count') or 0),
        'evidence_file_count': int(bulk_view.get('evidence_file_count') or 0),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_contract_signature_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'gate_names': list(bulk_view.get('gate_names') or []),
        'gate_domain_index': dict(bulk_view.get('gate_domain_index') or {}),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_contract_envelope_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'gate_count': int(bulk_view.get('gate_count') or 0),
        'pass_count': int(bulk_view.get('pass_count') or 0),
        'hold_count': int(bulk_view.get('hold_count') or 0),
        'evidence_file_count': int(bulk_view.get('evidence_file_count') or 0),
        'contract_signature_sha256': str(bulk_view.get('contract_signature_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_fingerprint_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'gate_count': int(bulk_view.get('gate_count') or 0),
        'pass_count': int(bulk_view.get('pass_count') or 0),
        'hold_count': int(bulk_view.get('hold_count') or 0),
        'evidence_file_count': int(bulk_view.get('evidence_file_count') or 0),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'contract_signature_sha256': str(bulk_view.get('contract_signature_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_manifest_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'gate_names': list(bulk_view.get('gate_names') or []),
        'gate_status_bitmap': list(bulk_view.get('gate_status_bitmap') or []),
        'gate_domain_index': dict(bulk_view.get('gate_domain_index') or {}),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_root_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'gate_count': int(bulk_view.get('gate_count') or 0),
        'pass_count': int(bulk_view.get('pass_count') or 0),
        'hold_count': int(bulk_view.get('hold_count') or 0),
        'evidence_file_count': int(bulk_view.get('evidence_file_count') or 0),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'contract_signature_sha256': str(bulk_view.get('contract_signature_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_attestation_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'gate_status_bitmap': list(bulk_view.get('gate_status_bitmap') or []),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_verdict_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_lineage_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_capsule_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'gate_count': int(bulk_view.get('gate_count') or 0),
        'pass_count': int(bulk_view.get('pass_count') or 0),
        'hold_count': int(bulk_view.get('hold_count') or 0),
        'evidence_file_count': int(bulk_view.get('evidence_file_count') or 0),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_anchor_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_beacon_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_constellation_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_galaxy_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_universe_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_multiverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_omniverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_multiverse_sha256': str(bulk_view.get('release_multiverse_sha256') or ''),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_hyperverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_omniverse_sha256': str(bulk_view.get('release_omniverse_sha256') or ''),
        'release_multiverse_sha256': str(bulk_view.get('release_multiverse_sha256') or ''),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_megaverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_hyperverse_sha256': str(bulk_view.get('release_hyperverse_sha256') or ''),
        'release_omniverse_sha256': str(bulk_view.get('release_omniverse_sha256') or ''),
        'release_multiverse_sha256': str(bulk_view.get('release_multiverse_sha256') or ''),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_gigaverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_megaverse_sha256': str(bulk_view.get('release_megaverse_sha256') or ''),
        'release_hyperverse_sha256': str(bulk_view.get('release_hyperverse_sha256') or ''),
        'release_omniverse_sha256': str(bulk_view.get('release_omniverse_sha256') or ''),
        'release_multiverse_sha256': str(bulk_view.get('release_multiverse_sha256') or ''),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_teraverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_gigaverse_sha256': str(bulk_view.get('release_gigaverse_sha256') or ''),
        'release_megaverse_sha256': str(bulk_view.get('release_megaverse_sha256') or ''),
        'release_hyperverse_sha256': str(bulk_view.get('release_hyperverse_sha256') or ''),
        'release_omniverse_sha256': str(bulk_view.get('release_omniverse_sha256') or ''),
        'release_multiverse_sha256': str(bulk_view.get('release_multiverse_sha256') or ''),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_petaverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_teraverse_sha256': str(bulk_view.get('release_teraverse_sha256') or ''),
        'release_gigaverse_sha256': str(bulk_view.get('release_gigaverse_sha256') or ''),
        'release_megaverse_sha256': str(bulk_view.get('release_megaverse_sha256') or ''),
        'release_hyperverse_sha256': str(bulk_view.get('release_hyperverse_sha256') or ''),
        'release_omniverse_sha256': str(bulk_view.get('release_omniverse_sha256') or ''),
        'release_multiverse_sha256': str(bulk_view.get('release_multiverse_sha256') or ''),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_exaverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_petaverse_sha256': str(bulk_view.get('release_petaverse_sha256') or ''),
        'release_teraverse_sha256': str(bulk_view.get('release_teraverse_sha256') or ''),
        'release_gigaverse_sha256': str(bulk_view.get('release_gigaverse_sha256') or ''),
        'release_megaverse_sha256': str(bulk_view.get('release_megaverse_sha256') or ''),
        'release_hyperverse_sha256': str(bulk_view.get('release_hyperverse_sha256') or ''),
        'release_omniverse_sha256': str(bulk_view.get('release_omniverse_sha256') or ''),
        'release_multiverse_sha256': str(bulk_view.get('release_multiverse_sha256') or ''),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_zettaverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_exaverse_sha256': str(bulk_view.get('release_exaverse_sha256') or ''),
        'release_petaverse_sha256': str(bulk_view.get('release_petaverse_sha256') or ''),
        'release_teraverse_sha256': str(bulk_view.get('release_teraverse_sha256') or ''),
        'release_gigaverse_sha256': str(bulk_view.get('release_gigaverse_sha256') or ''),
        'release_megaverse_sha256': str(bulk_view.get('release_megaverse_sha256') or ''),
        'release_hyperverse_sha256': str(bulk_view.get('release_hyperverse_sha256') or ''),
        'release_omniverse_sha256': str(bulk_view.get('release_omniverse_sha256') or ''),
        'release_multiverse_sha256': str(bulk_view.get('release_multiverse_sha256') or ''),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_yottaverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_zettaverse_sha256': str(bulk_view.get('release_zettaverse_sha256') or ''),
        'release_exaverse_sha256': str(bulk_view.get('release_exaverse_sha256') or ''),
        'release_petaverse_sha256': str(bulk_view.get('release_petaverse_sha256') or ''),
        'release_teraverse_sha256': str(bulk_view.get('release_teraverse_sha256') or ''),
        'release_gigaverse_sha256': str(bulk_view.get('release_gigaverse_sha256') or ''),
        'release_megaverse_sha256': str(bulk_view.get('release_megaverse_sha256') or ''),
        'release_hyperverse_sha256': str(bulk_view.get('release_hyperverse_sha256') or ''),
        'release_omniverse_sha256': str(bulk_view.get('release_omniverse_sha256') or ''),
        'release_multiverse_sha256': str(bulk_view.get('release_multiverse_sha256') or ''),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_ronnaverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_yottaverse_sha256': str(bulk_view.get('release_yottaverse_sha256') or ''),
        'release_zettaverse_sha256': str(bulk_view.get('release_zettaverse_sha256') or ''),
        'release_exaverse_sha256': str(bulk_view.get('release_exaverse_sha256') or ''),
        'release_petaverse_sha256': str(bulk_view.get('release_petaverse_sha256') or ''),
        'release_teraverse_sha256': str(bulk_view.get('release_teraverse_sha256') or ''),
        'release_gigaverse_sha256': str(bulk_view.get('release_gigaverse_sha256') or ''),
        'release_megaverse_sha256': str(bulk_view.get('release_megaverse_sha256') or ''),
        'release_hyperverse_sha256': str(bulk_view.get('release_hyperverse_sha256') or ''),
        'release_omniverse_sha256': str(bulk_view.get('release_omniverse_sha256') or ''),
        'release_multiverse_sha256': str(bulk_view.get('release_multiverse_sha256') or ''),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_quettaverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_ronnaverse_sha256': str(bulk_view.get('release_ronnaverse_sha256') or ''),
        'release_yottaverse_sha256': str(bulk_view.get('release_yottaverse_sha256') or ''),
        'release_zettaverse_sha256': str(bulk_view.get('release_zettaverse_sha256') or ''),
        'release_exaverse_sha256': str(bulk_view.get('release_exaverse_sha256') or ''),
        'release_petaverse_sha256': str(bulk_view.get('release_petaverse_sha256') or ''),
        'release_teraverse_sha256': str(bulk_view.get('release_teraverse_sha256') or ''),
        'release_gigaverse_sha256': str(bulk_view.get('release_gigaverse_sha256') or ''),
        'release_megaverse_sha256': str(bulk_view.get('release_megaverse_sha256') or ''),
        'release_hyperverse_sha256': str(bulk_view.get('release_hyperverse_sha256') or ''),
        'release_omniverse_sha256': str(bulk_view.get('release_omniverse_sha256') or ''),
        'release_multiverse_sha256': str(bulk_view.get('release_multiverse_sha256') or ''),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_apexverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_quettaverse_sha256': str(bulk_view.get('release_quettaverse_sha256') or ''),
        'release_ronnaverse_sha256': str(bulk_view.get('release_ronnaverse_sha256') or ''),
        'release_yottaverse_sha256': str(bulk_view.get('release_yottaverse_sha256') or ''),
        'release_zettaverse_sha256': str(bulk_view.get('release_zettaverse_sha256') or ''),
        'release_exaverse_sha256': str(bulk_view.get('release_exaverse_sha256') or ''),
        'release_petaverse_sha256': str(bulk_view.get('release_petaverse_sha256') or ''),
        'release_teraverse_sha256': str(bulk_view.get('release_teraverse_sha256') or ''),
        'release_gigaverse_sha256': str(bulk_view.get('release_gigaverse_sha256') or ''),
        'release_megaverse_sha256': str(bulk_view.get('release_megaverse_sha256') or ''),
        'release_hyperverse_sha256': str(bulk_view.get('release_hyperverse_sha256') or ''),
        'release_omniverse_sha256': str(bulk_view.get('release_omniverse_sha256') or ''),
        'release_multiverse_sha256': str(bulk_view.get('release_multiverse_sha256') or ''),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_ultimaverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_apexverse_sha256': str(bulk_view.get('release_apexverse_sha256') or ''),
        'release_quettaverse_sha256': str(bulk_view.get('release_quettaverse_sha256') or ''),
        'release_ronnaverse_sha256': str(bulk_view.get('release_ronnaverse_sha256') or ''),
        'release_yottaverse_sha256': str(bulk_view.get('release_yottaverse_sha256') or ''),
        'release_zettaverse_sha256': str(bulk_view.get('release_zettaverse_sha256') or ''),
        'release_exaverse_sha256': str(bulk_view.get('release_exaverse_sha256') or ''),
        'release_petaverse_sha256': str(bulk_view.get('release_petaverse_sha256') or ''),
        'release_teraverse_sha256': str(bulk_view.get('release_teraverse_sha256') or ''),
        'release_gigaverse_sha256': str(bulk_view.get('release_gigaverse_sha256') or ''),
        'release_megaverse_sha256': str(bulk_view.get('release_megaverse_sha256') or ''),
        'release_hyperverse_sha256': str(bulk_view.get('release_hyperverse_sha256') or ''),
        'release_omniverse_sha256': str(bulk_view.get('release_omniverse_sha256') or ''),
        'release_multiverse_sha256': str(bulk_view.get('release_multiverse_sha256') or ''),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_transcendaverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_ultimaverse_sha256': str(bulk_view.get('release_ultimaverse_sha256') or ''),
        'release_apexverse_sha256': str(bulk_view.get('release_apexverse_sha256') or ''),
        'release_quettaverse_sha256': str(bulk_view.get('release_quettaverse_sha256') or ''),
        'release_ronnaverse_sha256': str(bulk_view.get('release_ronnaverse_sha256') or ''),
        'release_yottaverse_sha256': str(bulk_view.get('release_yottaverse_sha256') or ''),
        'release_zettaverse_sha256': str(bulk_view.get('release_zettaverse_sha256') or ''),
        'release_exaverse_sha256': str(bulk_view.get('release_exaverse_sha256') or ''),
        'release_petaverse_sha256': str(bulk_view.get('release_petaverse_sha256') or ''),
        'release_teraverse_sha256': str(bulk_view.get('release_teraverse_sha256') or ''),
        'release_gigaverse_sha256': str(bulk_view.get('release_gigaverse_sha256') or ''),
        'release_megaverse_sha256': str(bulk_view.get('release_megaverse_sha256') or ''),
        'release_hyperverse_sha256': str(bulk_view.get('release_hyperverse_sha256') or ''),
        'release_omniverse_sha256': str(bulk_view.get('release_omniverse_sha256') or ''),
        'release_multiverse_sha256': str(bulk_view.get('release_multiverse_sha256') or ''),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_infinitaverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_transcendaverse_sha256': str(bulk_view.get('release_transcendaverse_sha256') or ''),
        'release_ultimaverse_sha256': str(bulk_view.get('release_ultimaverse_sha256') or ''),
        'release_apexverse_sha256': str(bulk_view.get('release_apexverse_sha256') or ''),
        'release_quettaverse_sha256': str(bulk_view.get('release_quettaverse_sha256') or ''),
        'release_ronnaverse_sha256': str(bulk_view.get('release_ronnaverse_sha256') or ''),
        'release_yottaverse_sha256': str(bulk_view.get('release_yottaverse_sha256') or ''),
        'release_zettaverse_sha256': str(bulk_view.get('release_zettaverse_sha256') or ''),
        'release_exaverse_sha256': str(bulk_view.get('release_exaverse_sha256') or ''),
        'release_petaverse_sha256': str(bulk_view.get('release_petaverse_sha256') or ''),
        'release_teraverse_sha256': str(bulk_view.get('release_teraverse_sha256') or ''),
        'release_gigaverse_sha256': str(bulk_view.get('release_gigaverse_sha256') or ''),
        'release_megaverse_sha256': str(bulk_view.get('release_megaverse_sha256') or ''),
        'release_hyperverse_sha256': str(bulk_view.get('release_hyperverse_sha256') or ''),
        'release_omniverse_sha256': str(bulk_view.get('release_omniverse_sha256') or ''),
        'release_multiverse_sha256': str(bulk_view.get('release_multiverse_sha256') or ''),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_eternaverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_infinitaverse_sha256': str(bulk_view.get('release_infinitaverse_sha256') or ''),
        'release_transcendaverse_sha256': str(bulk_view.get('release_transcendaverse_sha256') or ''),
        'release_ultimaverse_sha256': str(bulk_view.get('release_ultimaverse_sha256') or ''),
        'release_apexverse_sha256': str(bulk_view.get('release_apexverse_sha256') or ''),
        'release_quettaverse_sha256': str(bulk_view.get('release_quettaverse_sha256') or ''),
        'release_ronnaverse_sha256': str(bulk_view.get('release_ronnaverse_sha256') or ''),
        'release_yottaverse_sha256': str(bulk_view.get('release_yottaverse_sha256') or ''),
        'release_zettaverse_sha256': str(bulk_view.get('release_zettaverse_sha256') or ''),
        'release_exaverse_sha256': str(bulk_view.get('release_exaverse_sha256') or ''),
        'release_petaverse_sha256': str(bulk_view.get('release_petaverse_sha256') or ''),
        'release_teraverse_sha256': str(bulk_view.get('release_teraverse_sha256') or ''),
        'release_gigaverse_sha256': str(bulk_view.get('release_gigaverse_sha256') or ''),
        'release_megaverse_sha256': str(bulk_view.get('release_megaverse_sha256') or ''),
        'release_hyperverse_sha256': str(bulk_view.get('release_hyperverse_sha256') or ''),
        'release_omniverse_sha256': str(bulk_view.get('release_omniverse_sha256') or ''),
        'release_multiverse_sha256': str(bulk_view.get('release_multiverse_sha256') or ''),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_timelessverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_eternaverse_sha256': str(bulk_view.get('release_eternaverse_sha256') or ''),
        'release_infinitaverse_sha256': str(bulk_view.get('release_infinitaverse_sha256') or ''),
        'release_transcendaverse_sha256': str(bulk_view.get('release_transcendaverse_sha256') or ''),
        'release_ultimaverse_sha256': str(bulk_view.get('release_ultimaverse_sha256') or ''),
        'release_apexverse_sha256': str(bulk_view.get('release_apexverse_sha256') or ''),
        'release_quettaverse_sha256': str(bulk_view.get('release_quettaverse_sha256') or ''),
        'release_ronnaverse_sha256': str(bulk_view.get('release_ronnaverse_sha256') or ''),
        'release_yottaverse_sha256': str(bulk_view.get('release_yottaverse_sha256') or ''),
        'release_zettaverse_sha256': str(bulk_view.get('release_zettaverse_sha256') or ''),
        'release_exaverse_sha256': str(bulk_view.get('release_exaverse_sha256') or ''),
        'release_petaverse_sha256': str(bulk_view.get('release_petaverse_sha256') or ''),
        'release_teraverse_sha256': str(bulk_view.get('release_teraverse_sha256') or ''),
        'release_gigaverse_sha256': str(bulk_view.get('release_gigaverse_sha256') or ''),
        'release_megaverse_sha256': str(bulk_view.get('release_megaverse_sha256') or ''),
        'release_hyperverse_sha256': str(bulk_view.get('release_hyperverse_sha256') or ''),
        'release_omniverse_sha256': str(bulk_view.get('release_omniverse_sha256') or ''),
        'release_multiverse_sha256': str(bulk_view.get('release_multiverse_sha256') or ''),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_aeonverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_timelessverse_sha256': str(bulk_view.get('release_timelessverse_sha256') or ''),
        'release_eternaverse_sha256': str(bulk_view.get('release_eternaverse_sha256') or ''),
        'release_infinitaverse_sha256': str(bulk_view.get('release_infinitaverse_sha256') or ''),
        'release_transcendaverse_sha256': str(bulk_view.get('release_transcendaverse_sha256') or ''),
        'release_ultimaverse_sha256': str(bulk_view.get('release_ultimaverse_sha256') or ''),
        'release_apexverse_sha256': str(bulk_view.get('release_apexverse_sha256') or ''),
        'release_quettaverse_sha256': str(bulk_view.get('release_quettaverse_sha256') or ''),
        'release_ronnaverse_sha256': str(bulk_view.get('release_ronnaverse_sha256') or ''),
        'release_yottaverse_sha256': str(bulk_view.get('release_yottaverse_sha256') or ''),
        'release_zettaverse_sha256': str(bulk_view.get('release_zettaverse_sha256') or ''),
        'release_exaverse_sha256': str(bulk_view.get('release_exaverse_sha256') or ''),
        'release_petaverse_sha256': str(bulk_view.get('release_petaverse_sha256') or ''),
        'release_teraverse_sha256': str(bulk_view.get('release_teraverse_sha256') or ''),
        'release_gigaverse_sha256': str(bulk_view.get('release_gigaverse_sha256') or ''),
        'release_megaverse_sha256': str(bulk_view.get('release_megaverse_sha256') or ''),
        'release_hyperverse_sha256': str(bulk_view.get('release_hyperverse_sha256') or ''),
        'release_omniverse_sha256': str(bulk_view.get('release_omniverse_sha256') or ''),
        'release_multiverse_sha256': str(bulk_view.get('release_multiverse_sha256') or ''),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_epochverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_aeonverse_sha256': str(bulk_view.get('release_aeonverse_sha256') or ''),
        'release_timelessverse_sha256': str(bulk_view.get('release_timelessverse_sha256') or ''),
        'release_eternaverse_sha256': str(bulk_view.get('release_eternaverse_sha256') or ''),
        'release_infinitaverse_sha256': str(bulk_view.get('release_infinitaverse_sha256') or ''),
        'release_transcendaverse_sha256': str(bulk_view.get('release_transcendaverse_sha256') or ''),
        'release_ultimaverse_sha256': str(bulk_view.get('release_ultimaverse_sha256') or ''),
        'release_apexverse_sha256': str(bulk_view.get('release_apexverse_sha256') or ''),
        'release_quettaverse_sha256': str(bulk_view.get('release_quettaverse_sha256') or ''),
        'release_ronnaverse_sha256': str(bulk_view.get('release_ronnaverse_sha256') or ''),
        'release_yottaverse_sha256': str(bulk_view.get('release_yottaverse_sha256') or ''),
        'release_zettaverse_sha256': str(bulk_view.get('release_zettaverse_sha256') or ''),
        'release_exaverse_sha256': str(bulk_view.get('release_exaverse_sha256') or ''),
        'release_petaverse_sha256': str(bulk_view.get('release_petaverse_sha256') or ''),
        'release_teraverse_sha256': str(bulk_view.get('release_teraverse_sha256') or ''),
        'release_gigaverse_sha256': str(bulk_view.get('release_gigaverse_sha256') or ''),
        'release_megaverse_sha256': str(bulk_view.get('release_megaverse_sha256') or ''),
        'release_hyperverse_sha256': str(bulk_view.get('release_hyperverse_sha256') or ''),
        'release_omniverse_sha256': str(bulk_view.get('release_omniverse_sha256') or ''),
        'release_multiverse_sha256': str(bulk_view.get('release_multiverse_sha256') or ''),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_eraverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_epochverse_sha256': str(bulk_view.get('release_epochverse_sha256') or ''),
        'release_aeonverse_sha256': str(bulk_view.get('release_aeonverse_sha256') or ''),
        'release_timelessverse_sha256': str(bulk_view.get('release_timelessverse_sha256') or ''),
        'release_eternaverse_sha256': str(bulk_view.get('release_eternaverse_sha256') or ''),
        'release_infinitaverse_sha256': str(bulk_view.get('release_infinitaverse_sha256') or ''),
        'release_transcendaverse_sha256': str(bulk_view.get('release_transcendaverse_sha256') or ''),
        'release_ultimaverse_sha256': str(bulk_view.get('release_ultimaverse_sha256') or ''),
        'release_apexverse_sha256': str(bulk_view.get('release_apexverse_sha256') or ''),
        'release_quettaverse_sha256': str(bulk_view.get('release_quettaverse_sha256') or ''),
        'release_ronnaverse_sha256': str(bulk_view.get('release_ronnaverse_sha256') or ''),
        'release_yottaverse_sha256': str(bulk_view.get('release_yottaverse_sha256') or ''),
        'release_zettaverse_sha256': str(bulk_view.get('release_zettaverse_sha256') or ''),
        'release_exaverse_sha256': str(bulk_view.get('release_exaverse_sha256') or ''),
        'release_petaverse_sha256': str(bulk_view.get('release_petaverse_sha256') or ''),
        'release_teraverse_sha256': str(bulk_view.get('release_teraverse_sha256') or ''),
        'release_gigaverse_sha256': str(bulk_view.get('release_gigaverse_sha256') or ''),
        'release_megaverse_sha256': str(bulk_view.get('release_megaverse_sha256') or ''),
        'release_hyperverse_sha256': str(bulk_view.get('release_hyperverse_sha256') or ''),
        'release_omniverse_sha256': str(bulk_view.get('release_omniverse_sha256') or ''),
        'release_multiverse_sha256': str(bulk_view.get('release_multiverse_sha256') or ''),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_metaverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_eraverse_sha256': str(bulk_view.get('release_eraverse_sha256') or ''),
        'release_epochverse_sha256': str(bulk_view.get('release_epochverse_sha256') or ''),
        'release_aeonverse_sha256': str(bulk_view.get('release_aeonverse_sha256') or ''),
        'release_timelessverse_sha256': str(bulk_view.get('release_timelessverse_sha256') or ''),
        'release_eternaverse_sha256': str(bulk_view.get('release_eternaverse_sha256') or ''),
        'release_infinitaverse_sha256': str(bulk_view.get('release_infinitaverse_sha256') or ''),
        'release_transcendaverse_sha256': str(bulk_view.get('release_transcendaverse_sha256') or ''),
        'release_ultimaverse_sha256': str(bulk_view.get('release_ultimaverse_sha256') or ''),
        'release_apexverse_sha256': str(bulk_view.get('release_apexverse_sha256') or ''),
        'release_quettaverse_sha256': str(bulk_view.get('release_quettaverse_sha256') or ''),
        'release_ronnaverse_sha256': str(bulk_view.get('release_ronnaverse_sha256') or ''),
        'release_yottaverse_sha256': str(bulk_view.get('release_yottaverse_sha256') or ''),
        'release_zettaverse_sha256': str(bulk_view.get('release_zettaverse_sha256') or ''),
        'release_exaverse_sha256': str(bulk_view.get('release_exaverse_sha256') or ''),
        'release_petaverse_sha256': str(bulk_view.get('release_petaverse_sha256') or ''),
        'release_teraverse_sha256': str(bulk_view.get('release_teraverse_sha256') or ''),
        'release_gigaverse_sha256': str(bulk_view.get('release_gigaverse_sha256') or ''),
        'release_megaverse_sha256': str(bulk_view.get('release_megaverse_sha256') or ''),
        'release_hyperverse_sha256': str(bulk_view.get('release_hyperverse_sha256') or ''),
        'release_omniverse_sha256': str(bulk_view.get('release_omniverse_sha256') or ''),
        'release_multiverse_sha256': str(bulk_view.get('release_multiverse_sha256') or ''),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_paraverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_metaverse_sha256': str(bulk_view.get('release_metaverse_sha256') or ''),
        'release_eraverse_sha256': str(bulk_view.get('release_eraverse_sha256') or ''),
        'release_epochverse_sha256': str(bulk_view.get('release_epochverse_sha256') or ''),
        'release_aeonverse_sha256': str(bulk_view.get('release_aeonverse_sha256') or ''),
        'release_timelessverse_sha256': str(bulk_view.get('release_timelessverse_sha256') or ''),
        'release_eternaverse_sha256': str(bulk_view.get('release_eternaverse_sha256') or ''),
        'release_infinitaverse_sha256': str(bulk_view.get('release_infinitaverse_sha256') or ''),
        'release_transcendaverse_sha256': str(bulk_view.get('release_transcendaverse_sha256') or ''),
        'release_ultimaverse_sha256': str(bulk_view.get('release_ultimaverse_sha256') or ''),
        'release_apexverse_sha256': str(bulk_view.get('release_apexverse_sha256') or ''),
        'release_quettaverse_sha256': str(bulk_view.get('release_quettaverse_sha256') or ''),
        'release_ronnaverse_sha256': str(bulk_view.get('release_ronnaverse_sha256') or ''),
        'release_yottaverse_sha256': str(bulk_view.get('release_yottaverse_sha256') or ''),
        'release_zettaverse_sha256': str(bulk_view.get('release_zettaverse_sha256') or ''),
        'release_exaverse_sha256': str(bulk_view.get('release_exaverse_sha256') or ''),
        'release_petaverse_sha256': str(bulk_view.get('release_petaverse_sha256') or ''),
        'release_teraverse_sha256': str(bulk_view.get('release_teraverse_sha256') or ''),
        'release_gigaverse_sha256': str(bulk_view.get('release_gigaverse_sha256') or ''),
        'release_megaverse_sha256': str(bulk_view.get('release_megaverse_sha256') or ''),
        'release_hyperverse_sha256': str(bulk_view.get('release_hyperverse_sha256') or ''),
        'release_omniverse_sha256': str(bulk_view.get('release_omniverse_sha256') or ''),
        'release_multiverse_sha256': str(bulk_view.get('release_multiverse_sha256') or ''),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_polyverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_paraverse_sha256': str(bulk_view.get('release_paraverse_sha256') or ''),
        'release_metaverse_sha256': str(bulk_view.get('release_metaverse_sha256') or ''),
        'release_eraverse_sha256': str(bulk_view.get('release_eraverse_sha256') or ''),
        'release_epochverse_sha256': str(bulk_view.get('release_epochverse_sha256') or ''),
        'release_aeonverse_sha256': str(bulk_view.get('release_aeonverse_sha256') or ''),
        'release_timelessverse_sha256': str(bulk_view.get('release_timelessverse_sha256') or ''),
        'release_eternaverse_sha256': str(bulk_view.get('release_eternaverse_sha256') or ''),
        'release_infinitaverse_sha256': str(bulk_view.get('release_infinitaverse_sha256') or ''),
        'release_transcendaverse_sha256': str(bulk_view.get('release_transcendaverse_sha256') or ''),
        'release_ultimaverse_sha256': str(bulk_view.get('release_ultimaverse_sha256') or ''),
        'release_apexverse_sha256': str(bulk_view.get('release_apexverse_sha256') or ''),
        'release_quettaverse_sha256': str(bulk_view.get('release_quettaverse_sha256') or ''),
        'release_ronnaverse_sha256': str(bulk_view.get('release_ronnaverse_sha256') or ''),
        'release_yottaverse_sha256': str(bulk_view.get('release_yottaverse_sha256') or ''),
        'release_zettaverse_sha256': str(bulk_view.get('release_zettaverse_sha256') or ''),
        'release_exaverse_sha256': str(bulk_view.get('release_exaverse_sha256') or ''),
        'release_petaverse_sha256': str(bulk_view.get('release_petaverse_sha256') or ''),
        'release_teraverse_sha256': str(bulk_view.get('release_teraverse_sha256') or ''),
        'release_gigaverse_sha256': str(bulk_view.get('release_gigaverse_sha256') or ''),
        'release_megaverse_sha256': str(bulk_view.get('release_megaverse_sha256') or ''),
        'release_hyperverse_sha256': str(bulk_view.get('release_hyperverse_sha256') or ''),
        'release_omniverse_sha256': str(bulk_view.get('release_omniverse_sha256') or ''),
        'release_multiverse_sha256': str(bulk_view.get('release_multiverse_sha256') or ''),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_panverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_polyverse_sha256': str(bulk_view.get('release_polyverse_sha256') or ''),
        'release_paraverse_sha256': str(bulk_view.get('release_paraverse_sha256') or ''),
        'release_metaverse_sha256': str(bulk_view.get('release_metaverse_sha256') or ''),
        'release_eraverse_sha256': str(bulk_view.get('release_eraverse_sha256') or ''),
        'release_epochverse_sha256': str(bulk_view.get('release_epochverse_sha256') or ''),
        'release_aeonverse_sha256': str(bulk_view.get('release_aeonverse_sha256') or ''),
        'release_timelessverse_sha256': str(bulk_view.get('release_timelessverse_sha256') or ''),
        'release_eternaverse_sha256': str(bulk_view.get('release_eternaverse_sha256') or ''),
        'release_infinitaverse_sha256': str(bulk_view.get('release_infinitaverse_sha256') or ''),
        'release_transcendaverse_sha256': str(bulk_view.get('release_transcendaverse_sha256') or ''),
        'release_ultimaverse_sha256': str(bulk_view.get('release_ultimaverse_sha256') or ''),
        'release_apexverse_sha256': str(bulk_view.get('release_apexverse_sha256') or ''),
        'release_quettaverse_sha256': str(bulk_view.get('release_quettaverse_sha256') or ''),
        'release_ronnaverse_sha256': str(bulk_view.get('release_ronnaverse_sha256') or ''),
        'release_yottaverse_sha256': str(bulk_view.get('release_yottaverse_sha256') or ''),
        'release_zettaverse_sha256': str(bulk_view.get('release_zettaverse_sha256') or ''),
        'release_exaverse_sha256': str(bulk_view.get('release_exaverse_sha256') or ''),
        'release_petaverse_sha256': str(bulk_view.get('release_petaverse_sha256') or ''),
        'release_teraverse_sha256': str(bulk_view.get('release_teraverse_sha256') or ''),
        'release_gigaverse_sha256': str(bulk_view.get('release_gigaverse_sha256') or ''),
        'release_megaverse_sha256': str(bulk_view.get('release_megaverse_sha256') or ''),
        'release_hyperverse_sha256': str(bulk_view.get('release_hyperverse_sha256') or ''),
        'release_omniverse_sha256': str(bulk_view.get('release_omniverse_sha256') or ''),
        'release_multiverse_sha256': str(bulk_view.get('release_multiverse_sha256') or ''),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_holoverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_panverse_sha256': str(bulk_view.get('release_panverse_sha256') or ''),
        'release_polyverse_sha256': str(bulk_view.get('release_polyverse_sha256') or ''),
        'release_paraverse_sha256': str(bulk_view.get('release_paraverse_sha256') or ''),
        'release_metaverse_sha256': str(bulk_view.get('release_metaverse_sha256') or ''),
        'release_eraverse_sha256': str(bulk_view.get('release_eraverse_sha256') or ''),
        'release_epochverse_sha256': str(bulk_view.get('release_epochverse_sha256') or ''),
        'release_aeonverse_sha256': str(bulk_view.get('release_aeonverse_sha256') or ''),
        'release_timelessverse_sha256': str(bulk_view.get('release_timelessverse_sha256') or ''),
        'release_eternaverse_sha256': str(bulk_view.get('release_eternaverse_sha256') or ''),
        'release_infinitaverse_sha256': str(bulk_view.get('release_infinitaverse_sha256') or ''),
        'release_transcendaverse_sha256': str(bulk_view.get('release_transcendaverse_sha256') or ''),
        'release_ultimaverse_sha256': str(bulk_view.get('release_ultimaverse_sha256') or ''),
        'release_apexverse_sha256': str(bulk_view.get('release_apexverse_sha256') or ''),
        'release_quettaverse_sha256': str(bulk_view.get('release_quettaverse_sha256') or ''),
        'release_ronnaverse_sha256': str(bulk_view.get('release_ronnaverse_sha256') or ''),
        'release_yottaverse_sha256': str(bulk_view.get('release_yottaverse_sha256') or ''),
        'release_zettaverse_sha256': str(bulk_view.get('release_zettaverse_sha256') or ''),
        'release_exaverse_sha256': str(bulk_view.get('release_exaverse_sha256') or ''),
        'release_petaverse_sha256': str(bulk_view.get('release_petaverse_sha256') or ''),
        'release_teraverse_sha256': str(bulk_view.get('release_teraverse_sha256') or ''),
        'release_gigaverse_sha256': str(bulk_view.get('release_gigaverse_sha256') or ''),
        'release_megaverse_sha256': str(bulk_view.get('release_megaverse_sha256') or ''),
        'release_hyperverse_sha256': str(bulk_view.get('release_hyperverse_sha256') or ''),
        'release_omniverse_sha256': str(bulk_view.get('release_omniverse_sha256') or ''),
        'release_multiverse_sha256': str(bulk_view.get('release_multiverse_sha256') or ''),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_neoverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_holoverse_sha256': str(bulk_view.get('release_holoverse_sha256') or ''),
        'release_panverse_sha256': str(bulk_view.get('release_panverse_sha256') or ''),
        'release_polyverse_sha256': str(bulk_view.get('release_polyverse_sha256') or ''),
        'release_paraverse_sha256': str(bulk_view.get('release_paraverse_sha256') or ''),
        'release_metaverse_sha256': str(bulk_view.get('release_metaverse_sha256') or ''),
        'release_eraverse_sha256': str(bulk_view.get('release_eraverse_sha256') or ''),
        'release_epochverse_sha256': str(bulk_view.get('release_epochverse_sha256') or ''),
        'release_aeonverse_sha256': str(bulk_view.get('release_aeonverse_sha256') or ''),
        'release_timelessverse_sha256': str(bulk_view.get('release_timelessverse_sha256') or ''),
        'release_eternaverse_sha256': str(bulk_view.get('release_eternaverse_sha256') or ''),
        'release_infinitaverse_sha256': str(bulk_view.get('release_infinitaverse_sha256') or ''),
        'release_transcendaverse_sha256': str(bulk_view.get('release_transcendaverse_sha256') or ''),
        'release_ultimaverse_sha256': str(bulk_view.get('release_ultimaverse_sha256') or ''),
        'release_apexverse_sha256': str(bulk_view.get('release_apexverse_sha256') or ''),
        'release_quettaverse_sha256': str(bulk_view.get('release_quettaverse_sha256') or ''),
        'release_ronnaverse_sha256': str(bulk_view.get('release_ronnaverse_sha256') or ''),
        'release_yottaverse_sha256': str(bulk_view.get('release_yottaverse_sha256') or ''),
        'release_zettaverse_sha256': str(bulk_view.get('release_zettaverse_sha256') or ''),
        'release_exaverse_sha256': str(bulk_view.get('release_exaverse_sha256') or ''),
        'release_petaverse_sha256': str(bulk_view.get('release_petaverse_sha256') or ''),
        'release_teraverse_sha256': str(bulk_view.get('release_teraverse_sha256') or ''),
        'release_gigaverse_sha256': str(bulk_view.get('release_gigaverse_sha256') or ''),
        'release_megaverse_sha256': str(bulk_view.get('release_megaverse_sha256') or ''),
        'release_hyperverse_sha256': str(bulk_view.get('release_hyperverse_sha256') or ''),
        'release_omniverse_sha256': str(bulk_view.get('release_omniverse_sha256') or ''),
        'release_multiverse_sha256': str(bulk_view.get('release_multiverse_sha256') or ''),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_novaverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_neoverse_sha256': str(bulk_view.get('release_neoverse_sha256') or ''),
        'release_holoverse_sha256': str(bulk_view.get('release_holoverse_sha256') or ''),
        'release_panverse_sha256': str(bulk_view.get('release_panverse_sha256') or ''),
        'release_polyverse_sha256': str(bulk_view.get('release_polyverse_sha256') or ''),
        'release_paraverse_sha256': str(bulk_view.get('release_paraverse_sha256') or ''),
        'release_metaverse_sha256': str(bulk_view.get('release_metaverse_sha256') or ''),
        'release_eraverse_sha256': str(bulk_view.get('release_eraverse_sha256') or ''),
        'release_epochverse_sha256': str(bulk_view.get('release_epochverse_sha256') or ''),
        'release_aeonverse_sha256': str(bulk_view.get('release_aeonverse_sha256') or ''),
        'release_timelessverse_sha256': str(bulk_view.get('release_timelessverse_sha256') or ''),
        'release_eternaverse_sha256': str(bulk_view.get('release_eternaverse_sha256') or ''),
        'release_infinitaverse_sha256': str(bulk_view.get('release_infinitaverse_sha256') or ''),
        'release_transcendaverse_sha256': str(bulk_view.get('release_transcendaverse_sha256') or ''),
        'release_ultimaverse_sha256': str(bulk_view.get('release_ultimaverse_sha256') or ''),
        'release_apexverse_sha256': str(bulk_view.get('release_apexverse_sha256') or ''),
        'release_quettaverse_sha256': str(bulk_view.get('release_quettaverse_sha256') or ''),
        'release_ronnaverse_sha256': str(bulk_view.get('release_ronnaverse_sha256') or ''),
        'release_yottaverse_sha256': str(bulk_view.get('release_yottaverse_sha256') or ''),
        'release_zettaverse_sha256': str(bulk_view.get('release_zettaverse_sha256') or ''),
        'release_exaverse_sha256': str(bulk_view.get('release_exaverse_sha256') or ''),
        'release_petaverse_sha256': str(bulk_view.get('release_petaverse_sha256') or ''),
        'release_teraverse_sha256': str(bulk_view.get('release_teraverse_sha256') or ''),
        'release_gigaverse_sha256': str(bulk_view.get('release_gigaverse_sha256') or ''),
        'release_megaverse_sha256': str(bulk_view.get('release_megaverse_sha256') or ''),
        'release_hyperverse_sha256': str(bulk_view.get('release_hyperverse_sha256') or ''),
        'release_omniverse_sha256': str(bulk_view.get('release_omniverse_sha256') or ''),
        'release_multiverse_sha256': str(bulk_view.get('release_multiverse_sha256') or ''),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_supernovaverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_novaverse_sha256': str(bulk_view.get('release_novaverse_sha256') or ''),
        'release_neoverse_sha256': str(bulk_view.get('release_neoverse_sha256') or ''),
        'release_holoverse_sha256': str(bulk_view.get('release_holoverse_sha256') or ''),
        'release_panverse_sha256': str(bulk_view.get('release_panverse_sha256') or ''),
        'release_polyverse_sha256': str(bulk_view.get('release_polyverse_sha256') or ''),
        'release_paraverse_sha256': str(bulk_view.get('release_paraverse_sha256') or ''),
        'release_metaverse_sha256': str(bulk_view.get('release_metaverse_sha256') or ''),
        'release_eraverse_sha256': str(bulk_view.get('release_eraverse_sha256') or ''),
        'release_epochverse_sha256': str(bulk_view.get('release_epochverse_sha256') or ''),
        'release_aeonverse_sha256': str(bulk_view.get('release_aeonverse_sha256') or ''),
        'release_timelessverse_sha256': str(bulk_view.get('release_timelessverse_sha256') or ''),
        'release_eternaverse_sha256': str(bulk_view.get('release_eternaverse_sha256') or ''),
        'release_infinitaverse_sha256': str(bulk_view.get('release_infinitaverse_sha256') or ''),
        'release_transcendaverse_sha256': str(bulk_view.get('release_transcendaverse_sha256') or ''),
        'release_ultimaverse_sha256': str(bulk_view.get('release_ultimaverse_sha256') or ''),
        'release_apexverse_sha256': str(bulk_view.get('release_apexverse_sha256') or ''),
        'release_quettaverse_sha256': str(bulk_view.get('release_quettaverse_sha256') or ''),
        'release_ronnaverse_sha256': str(bulk_view.get('release_ronnaverse_sha256') or ''),
        'release_yottaverse_sha256': str(bulk_view.get('release_yottaverse_sha256') or ''),
        'release_zettaverse_sha256': str(bulk_view.get('release_zettaverse_sha256') or ''),
        'release_exaverse_sha256': str(bulk_view.get('release_exaverse_sha256') or ''),
        'release_petaverse_sha256': str(bulk_view.get('release_petaverse_sha256') or ''),
        'release_teraverse_sha256': str(bulk_view.get('release_teraverse_sha256') or ''),
        'release_gigaverse_sha256': str(bulk_view.get('release_gigaverse_sha256') or ''),
        'release_megaverse_sha256': str(bulk_view.get('release_megaverse_sha256') or ''),
        'release_hyperverse_sha256': str(bulk_view.get('release_hyperverse_sha256') or ''),
        'release_omniverse_sha256': str(bulk_view.get('release_omniverse_sha256') or ''),
        'release_multiverse_sha256': str(bulk_view.get('release_multiverse_sha256') or ''),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_hypernovaverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_supernovaverse_sha256': str(bulk_view.get('release_supernovaverse_sha256') or ''),
        'release_novaverse_sha256': str(bulk_view.get('release_novaverse_sha256') or ''),
        'release_neoverse_sha256': str(bulk_view.get('release_neoverse_sha256') or ''),
        'release_holoverse_sha256': str(bulk_view.get('release_holoverse_sha256') or ''),
        'release_panverse_sha256': str(bulk_view.get('release_panverse_sha256') or ''),
        'release_polyverse_sha256': str(bulk_view.get('release_polyverse_sha256') or ''),
        'release_paraverse_sha256': str(bulk_view.get('release_paraverse_sha256') or ''),
        'release_metaverse_sha256': str(bulk_view.get('release_metaverse_sha256') or ''),
        'release_eraverse_sha256': str(bulk_view.get('release_eraverse_sha256') or ''),
        'release_epochverse_sha256': str(bulk_view.get('release_epochverse_sha256') or ''),
        'release_aeonverse_sha256': str(bulk_view.get('release_aeonverse_sha256') or ''),
        'release_timelessverse_sha256': str(bulk_view.get('release_timelessverse_sha256') or ''),
        'release_eternaverse_sha256': str(bulk_view.get('release_eternaverse_sha256') or ''),
        'release_infinitaverse_sha256': str(bulk_view.get('release_infinitaverse_sha256') or ''),
        'release_transcendaverse_sha256': str(bulk_view.get('release_transcendaverse_sha256') or ''),
        'release_ultimaverse_sha256': str(bulk_view.get('release_ultimaverse_sha256') or ''),
        'release_apexverse_sha256': str(bulk_view.get('release_apexverse_sha256') or ''),
        'release_quettaverse_sha256': str(bulk_view.get('release_quettaverse_sha256') or ''),
        'release_ronnaverse_sha256': str(bulk_view.get('release_ronnaverse_sha256') or ''),
        'release_yottaverse_sha256': str(bulk_view.get('release_yottaverse_sha256') or ''),
        'release_zettaverse_sha256': str(bulk_view.get('release_zettaverse_sha256') or ''),
        'release_exaverse_sha256': str(bulk_view.get('release_exaverse_sha256') or ''),
        'release_petaverse_sha256': str(bulk_view.get('release_petaverse_sha256') or ''),
        'release_teraverse_sha256': str(bulk_view.get('release_teraverse_sha256') or ''),
        'release_gigaverse_sha256': str(bulk_view.get('release_gigaverse_sha256') or ''),
        'release_megaverse_sha256': str(bulk_view.get('release_megaverse_sha256') or ''),
        'release_hyperverse_sha256': str(bulk_view.get('release_hyperverse_sha256') or ''),
        'release_omniverse_sha256': str(bulk_view.get('release_omniverse_sha256') or ''),
        'release_multiverse_sha256': str(bulk_view.get('release_multiverse_sha256') or ''),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_ultranovaverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_hypernovaverse_sha256': str(bulk_view.get('release_hypernovaverse_sha256') or ''),
        'release_supernovaverse_sha256': str(bulk_view.get('release_supernovaverse_sha256') or ''),
        'release_novaverse_sha256': str(bulk_view.get('release_novaverse_sha256') or ''),
        'release_neoverse_sha256': str(bulk_view.get('release_neoverse_sha256') or ''),
        'release_holoverse_sha256': str(bulk_view.get('release_holoverse_sha256') or ''),
        'release_panverse_sha256': str(bulk_view.get('release_panverse_sha256') or ''),
        'release_polyverse_sha256': str(bulk_view.get('release_polyverse_sha256') or ''),
        'release_paraverse_sha256': str(bulk_view.get('release_paraverse_sha256') or ''),
        'release_metaverse_sha256': str(bulk_view.get('release_metaverse_sha256') or ''),
        'release_eraverse_sha256': str(bulk_view.get('release_eraverse_sha256') or ''),
        'release_epochverse_sha256': str(bulk_view.get('release_epochverse_sha256') or ''),
        'release_aeonverse_sha256': str(bulk_view.get('release_aeonverse_sha256') or ''),
        'release_timelessverse_sha256': str(bulk_view.get('release_timelessverse_sha256') or ''),
        'release_eternaverse_sha256': str(bulk_view.get('release_eternaverse_sha256') or ''),
        'release_infinitaverse_sha256': str(bulk_view.get('release_infinitaverse_sha256') or ''),
        'release_transcendaverse_sha256': str(bulk_view.get('release_transcendaverse_sha256') or ''),
        'release_ultimaverse_sha256': str(bulk_view.get('release_ultimaverse_sha256') or ''),
        'release_apexverse_sha256': str(bulk_view.get('release_apexverse_sha256') or ''),
        'release_quettaverse_sha256': str(bulk_view.get('release_quettaverse_sha256') or ''),
        'release_ronnaverse_sha256': str(bulk_view.get('release_ronnaverse_sha256') or ''),
        'release_yottaverse_sha256': str(bulk_view.get('release_yottaverse_sha256') or ''),
        'release_zettaverse_sha256': str(bulk_view.get('release_zettaverse_sha256') or ''),
        'release_exaverse_sha256': str(bulk_view.get('release_exaverse_sha256') or ''),
        'release_petaverse_sha256': str(bulk_view.get('release_petaverse_sha256') or ''),
        'release_teraverse_sha256': str(bulk_view.get('release_teraverse_sha256') or ''),
        'release_gigaverse_sha256': str(bulk_view.get('release_gigaverse_sha256') or ''),
        'release_megaverse_sha256': str(bulk_view.get('release_megaverse_sha256') or ''),
        'release_hyperverse_sha256': str(bulk_view.get('release_hyperverse_sha256') or ''),
        'release_omniverse_sha256': str(bulk_view.get('release_omniverse_sha256') or ''),
        'release_multiverse_sha256': str(bulk_view.get('release_multiverse_sha256') or ''),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_omeganovaverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_ultranovaverse_sha256': str(bulk_view.get('release_ultranovaverse_sha256') or ''),
        'release_hypernovaverse_sha256': str(bulk_view.get('release_hypernovaverse_sha256') or ''),
        'release_supernovaverse_sha256': str(bulk_view.get('release_supernovaverse_sha256') or ''),
        'release_novaverse_sha256': str(bulk_view.get('release_novaverse_sha256') or ''),
        'release_neoverse_sha256': str(bulk_view.get('release_neoverse_sha256') or ''),
        'release_holoverse_sha256': str(bulk_view.get('release_holoverse_sha256') or ''),
        'release_panverse_sha256': str(bulk_view.get('release_panverse_sha256') or ''),
        'release_polyverse_sha256': str(bulk_view.get('release_polyverse_sha256') or ''),
        'release_paraverse_sha256': str(bulk_view.get('release_paraverse_sha256') or ''),
        'release_metaverse_sha256': str(bulk_view.get('release_metaverse_sha256') or ''),
        'release_eraverse_sha256': str(bulk_view.get('release_eraverse_sha256') or ''),
        'release_epochverse_sha256': str(bulk_view.get('release_epochverse_sha256') or ''),
        'release_aeonverse_sha256': str(bulk_view.get('release_aeonverse_sha256') or ''),
        'release_timelessverse_sha256': str(bulk_view.get('release_timelessverse_sha256') or ''),
        'release_eternaverse_sha256': str(bulk_view.get('release_eternaverse_sha256') or ''),
        'release_infinitaverse_sha256': str(bulk_view.get('release_infinitaverse_sha256') or ''),
        'release_transcendaverse_sha256': str(bulk_view.get('release_transcendaverse_sha256') or ''),
        'release_ultimaverse_sha256': str(bulk_view.get('release_ultimaverse_sha256') or ''),
        'release_apexverse_sha256': str(bulk_view.get('release_apexverse_sha256') or ''),
        'release_quettaverse_sha256': str(bulk_view.get('release_quettaverse_sha256') or ''),
        'release_ronnaverse_sha256': str(bulk_view.get('release_ronnaverse_sha256') or ''),
        'release_yottaverse_sha256': str(bulk_view.get('release_yottaverse_sha256') or ''),
        'release_zettaverse_sha256': str(bulk_view.get('release_zettaverse_sha256') or ''),
        'release_exaverse_sha256': str(bulk_view.get('release_exaverse_sha256') or ''),
        'release_petaverse_sha256': str(bulk_view.get('release_petaverse_sha256') or ''),
        'release_teraverse_sha256': str(bulk_view.get('release_teraverse_sha256') or ''),
        'release_gigaverse_sha256': str(bulk_view.get('release_gigaverse_sha256') or ''),
        'release_megaverse_sha256': str(bulk_view.get('release_megaverse_sha256') or ''),
        'release_hyperverse_sha256': str(bulk_view.get('release_hyperverse_sha256') or ''),
        'release_omniverse_sha256': str(bulk_view.get('release_omniverse_sha256') or ''),
        'release_multiverse_sha256': str(bulk_view.get('release_multiverse_sha256') or ''),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_alphanovaverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_omeganovaverse_sha256': str(bulk_view.get('release_omeganovaverse_sha256') or ''),
        'release_ultranovaverse_sha256': str(bulk_view.get('release_ultranovaverse_sha256') or ''),
        'release_hypernovaverse_sha256': str(bulk_view.get('release_hypernovaverse_sha256') or ''),
        'release_supernovaverse_sha256': str(bulk_view.get('release_supernovaverse_sha256') or ''),
        'release_novaverse_sha256': str(bulk_view.get('release_novaverse_sha256') or ''),
        'release_neoverse_sha256': str(bulk_view.get('release_neoverse_sha256') or ''),
        'release_holoverse_sha256': str(bulk_view.get('release_holoverse_sha256') or ''),
        'release_panverse_sha256': str(bulk_view.get('release_panverse_sha256') or ''),
        'release_polyverse_sha256': str(bulk_view.get('release_polyverse_sha256') or ''),
        'release_paraverse_sha256': str(bulk_view.get('release_paraverse_sha256') or ''),
        'release_metaverse_sha256': str(bulk_view.get('release_metaverse_sha256') or ''),
        'release_eraverse_sha256': str(bulk_view.get('release_eraverse_sha256') or ''),
        'release_epochverse_sha256': str(bulk_view.get('release_epochverse_sha256') or ''),
        'release_aeonverse_sha256': str(bulk_view.get('release_aeonverse_sha256') or ''),
        'release_timelessverse_sha256': str(bulk_view.get('release_timelessverse_sha256') or ''),
        'release_eternaverse_sha256': str(bulk_view.get('release_eternaverse_sha256') or ''),
        'release_infinitaverse_sha256': str(bulk_view.get('release_infinitaverse_sha256') or ''),
        'release_transcendaverse_sha256': str(bulk_view.get('release_transcendaverse_sha256') or ''),
        'release_ultimaverse_sha256': str(bulk_view.get('release_ultimaverse_sha256') or ''),
        'release_apexverse_sha256': str(bulk_view.get('release_apexverse_sha256') or ''),
        'release_quettaverse_sha256': str(bulk_view.get('release_quettaverse_sha256') or ''),
        'release_ronnaverse_sha256': str(bulk_view.get('release_ronnaverse_sha256') or ''),
        'release_yottaverse_sha256': str(bulk_view.get('release_yottaverse_sha256') or ''),
        'release_zettaverse_sha256': str(bulk_view.get('release_zettaverse_sha256') or ''),
        'release_exaverse_sha256': str(bulk_view.get('release_exaverse_sha256') or ''),
        'release_petaverse_sha256': str(bulk_view.get('release_petaverse_sha256') or ''),
        'release_teraverse_sha256': str(bulk_view.get('release_teraverse_sha256') or ''),
        'release_gigaverse_sha256': str(bulk_view.get('release_gigaverse_sha256') or ''),
        'release_megaverse_sha256': str(bulk_view.get('release_megaverse_sha256') or ''),
        'release_hyperverse_sha256': str(bulk_view.get('release_hyperverse_sha256') or ''),
        'release_omniverse_sha256': str(bulk_view.get('release_omniverse_sha256') or ''),
        'release_multiverse_sha256': str(bulk_view.get('release_multiverse_sha256') or ''),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_betanovaverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_alphanovaverse_sha256': str(bulk_view.get('release_alphanovaverse_sha256') or ''),
        'release_omeganovaverse_sha256': str(bulk_view.get('release_omeganovaverse_sha256') or ''),
        'release_ultranovaverse_sha256': str(bulk_view.get('release_ultranovaverse_sha256') or ''),
        'release_hypernovaverse_sha256': str(bulk_view.get('release_hypernovaverse_sha256') or ''),
        'release_supernovaverse_sha256': str(bulk_view.get('release_supernovaverse_sha256') or ''),
        'release_novaverse_sha256': str(bulk_view.get('release_novaverse_sha256') or ''),
        'release_neoverse_sha256': str(bulk_view.get('release_neoverse_sha256') or ''),
        'release_holoverse_sha256': str(bulk_view.get('release_holoverse_sha256') or ''),
        'release_panverse_sha256': str(bulk_view.get('release_panverse_sha256') or ''),
        'release_polyverse_sha256': str(bulk_view.get('release_polyverse_sha256') or ''),
        'release_paraverse_sha256': str(bulk_view.get('release_paraverse_sha256') or ''),
        'release_metaverse_sha256': str(bulk_view.get('release_metaverse_sha256') or ''),
        'release_eraverse_sha256': str(bulk_view.get('release_eraverse_sha256') or ''),
        'release_epochverse_sha256': str(bulk_view.get('release_epochverse_sha256') or ''),
        'release_aeonverse_sha256': str(bulk_view.get('release_aeonverse_sha256') or ''),
        'release_timelessverse_sha256': str(bulk_view.get('release_timelessverse_sha256') or ''),
        'release_eternaverse_sha256': str(bulk_view.get('release_eternaverse_sha256') or ''),
        'release_infinitaverse_sha256': str(bulk_view.get('release_infinitaverse_sha256') or ''),
        'release_transcendaverse_sha256': str(bulk_view.get('release_transcendaverse_sha256') or ''),
        'release_ultimaverse_sha256': str(bulk_view.get('release_ultimaverse_sha256') or ''),
        'release_apexverse_sha256': str(bulk_view.get('release_apexverse_sha256') or ''),
        'release_quettaverse_sha256': str(bulk_view.get('release_quettaverse_sha256') or ''),
        'release_ronnaverse_sha256': str(bulk_view.get('release_ronnaverse_sha256') or ''),
        'release_yottaverse_sha256': str(bulk_view.get('release_yottaverse_sha256') or ''),
        'release_zettaverse_sha256': str(bulk_view.get('release_zettaverse_sha256') or ''),
        'release_exaverse_sha256': str(bulk_view.get('release_exaverse_sha256') or ''),
        'release_petaverse_sha256': str(bulk_view.get('release_petaverse_sha256') or ''),
        'release_teraverse_sha256': str(bulk_view.get('release_teraverse_sha256') or ''),
        'release_gigaverse_sha256': str(bulk_view.get('release_gigaverse_sha256') or ''),
        'release_megaverse_sha256': str(bulk_view.get('release_megaverse_sha256') or ''),
        'release_hyperverse_sha256': str(bulk_view.get('release_hyperverse_sha256') or ''),
        'release_omniverse_sha256': str(bulk_view.get('release_omniverse_sha256') or ''),
        'release_multiverse_sha256': str(bulk_view.get('release_multiverse_sha256') or ''),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_gammanovaverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_betanovaverse_sha256': str(bulk_view.get('release_betanovaverse_sha256') or ''),
        'release_alphanovaverse_sha256': str(bulk_view.get('release_alphanovaverse_sha256') or ''),
        'release_omeganovaverse_sha256': str(bulk_view.get('release_omeganovaverse_sha256') or ''),
        'release_ultranovaverse_sha256': str(bulk_view.get('release_ultranovaverse_sha256') or ''),
        'release_hypernovaverse_sha256': str(bulk_view.get('release_hypernovaverse_sha256') or ''),
        'release_supernovaverse_sha256': str(bulk_view.get('release_supernovaverse_sha256') or ''),
        'release_novaverse_sha256': str(bulk_view.get('release_novaverse_sha256') or ''),
        'release_neoverse_sha256': str(bulk_view.get('release_neoverse_sha256') or ''),
        'release_holoverse_sha256': str(bulk_view.get('release_holoverse_sha256') or ''),
        'release_panverse_sha256': str(bulk_view.get('release_panverse_sha256') or ''),
        'release_polyverse_sha256': str(bulk_view.get('release_polyverse_sha256') or ''),
        'release_paraverse_sha256': str(bulk_view.get('release_paraverse_sha256') or ''),
        'release_metaverse_sha256': str(bulk_view.get('release_metaverse_sha256') or ''),
        'release_eraverse_sha256': str(bulk_view.get('release_eraverse_sha256') or ''),
        'release_epochverse_sha256': str(bulk_view.get('release_epochverse_sha256') or ''),
        'release_aeonverse_sha256': str(bulk_view.get('release_aeonverse_sha256') or ''),
        'release_timelessverse_sha256': str(bulk_view.get('release_timelessverse_sha256') or ''),
        'release_eternaverse_sha256': str(bulk_view.get('release_eternaverse_sha256') or ''),
        'release_infinitaverse_sha256': str(bulk_view.get('release_infinitaverse_sha256') or ''),
        'release_transcendaverse_sha256': str(bulk_view.get('release_transcendaverse_sha256') or ''),
        'release_ultimaverse_sha256': str(bulk_view.get('release_ultimaverse_sha256') or ''),
        'release_apexverse_sha256': str(bulk_view.get('release_apexverse_sha256') or ''),
        'release_quettaverse_sha256': str(bulk_view.get('release_quettaverse_sha256') or ''),
        'release_ronnaverse_sha256': str(bulk_view.get('release_ronnaverse_sha256') or ''),
        'release_yottaverse_sha256': str(bulk_view.get('release_yottaverse_sha256') or ''),
        'release_zettaverse_sha256': str(bulk_view.get('release_zettaverse_sha256') or ''),
        'release_exaverse_sha256': str(bulk_view.get('release_exaverse_sha256') or ''),
        'release_petaverse_sha256': str(bulk_view.get('release_petaverse_sha256') or ''),
        'release_teraverse_sha256': str(bulk_view.get('release_teraverse_sha256') or ''),
        'release_gigaverse_sha256': str(bulk_view.get('release_gigaverse_sha256') or ''),
        'release_megaverse_sha256': str(bulk_view.get('release_megaverse_sha256') or ''),
        'release_hyperverse_sha256': str(bulk_view.get('release_hyperverse_sha256') or ''),
        'release_omniverse_sha256': str(bulk_view.get('release_omniverse_sha256') or ''),
        'release_multiverse_sha256': str(bulk_view.get('release_multiverse_sha256') or ''),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_deltanovaverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_gammanovaverse_sha256': str(bulk_view.get('release_gammanovaverse_sha256') or ''),
        'release_betanovaverse_sha256': str(bulk_view.get('release_betanovaverse_sha256') or ''),
        'release_alphanovaverse_sha256': str(bulk_view.get('release_alphanovaverse_sha256') or ''),
        'release_omeganovaverse_sha256': str(bulk_view.get('release_omeganovaverse_sha256') or ''),
        'release_ultranovaverse_sha256': str(bulk_view.get('release_ultranovaverse_sha256') or ''),
        'release_hypernovaverse_sha256': str(bulk_view.get('release_hypernovaverse_sha256') or ''),
        'release_supernovaverse_sha256': str(bulk_view.get('release_supernovaverse_sha256') or ''),
        'release_novaverse_sha256': str(bulk_view.get('release_novaverse_sha256') or ''),
        'release_neoverse_sha256': str(bulk_view.get('release_neoverse_sha256') or ''),
        'release_holoverse_sha256': str(bulk_view.get('release_holoverse_sha256') or ''),
        'release_panverse_sha256': str(bulk_view.get('release_panverse_sha256') or ''),
        'release_polyverse_sha256': str(bulk_view.get('release_polyverse_sha256') or ''),
        'release_paraverse_sha256': str(bulk_view.get('release_paraverse_sha256') or ''),
        'release_metaverse_sha256': str(bulk_view.get('release_metaverse_sha256') or ''),
        'release_eraverse_sha256': str(bulk_view.get('release_eraverse_sha256') or ''),
        'release_epochverse_sha256': str(bulk_view.get('release_epochverse_sha256') or ''),
        'release_aeonverse_sha256': str(bulk_view.get('release_aeonverse_sha256') or ''),
        'release_timelessverse_sha256': str(bulk_view.get('release_timelessverse_sha256') or ''),
        'release_eternaverse_sha256': str(bulk_view.get('release_eternaverse_sha256') or ''),
        'release_infinitaverse_sha256': str(bulk_view.get('release_infinitaverse_sha256') or ''),
        'release_transcendaverse_sha256': str(bulk_view.get('release_transcendaverse_sha256') or ''),
        'release_ultimaverse_sha256': str(bulk_view.get('release_ultimaverse_sha256') or ''),
        'release_apexverse_sha256': str(bulk_view.get('release_apexverse_sha256') or ''),
        'release_quettaverse_sha256': str(bulk_view.get('release_quettaverse_sha256') or ''),
        'release_ronnaverse_sha256': str(bulk_view.get('release_ronnaverse_sha256') or ''),
        'release_yottaverse_sha256': str(bulk_view.get('release_yottaverse_sha256') or ''),
        'release_zettaverse_sha256': str(bulk_view.get('release_zettaverse_sha256') or ''),
        'release_exaverse_sha256': str(bulk_view.get('release_exaverse_sha256') or ''),
        'release_petaverse_sha256': str(bulk_view.get('release_petaverse_sha256') or ''),
        'release_teraverse_sha256': str(bulk_view.get('release_teraverse_sha256') or ''),
        'release_gigaverse_sha256': str(bulk_view.get('release_gigaverse_sha256') or ''),
        'release_megaverse_sha256': str(bulk_view.get('release_megaverse_sha256') or ''),
        'release_hyperverse_sha256': str(bulk_view.get('release_hyperverse_sha256') or ''),
        'release_omniverse_sha256': str(bulk_view.get('release_omniverse_sha256') or ''),
        'release_multiverse_sha256': str(bulk_view.get('release_multiverse_sha256') or ''),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_epsilonnovaverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_deltanovaverse_sha256': str(bulk_view.get('release_deltanovaverse_sha256') or ''),
        'release_gammanovaverse_sha256': str(bulk_view.get('release_gammanovaverse_sha256') or ''),
        'release_betanovaverse_sha256': str(bulk_view.get('release_betanovaverse_sha256') or ''),
        'release_alphanovaverse_sha256': str(bulk_view.get('release_alphanovaverse_sha256') or ''),
        'release_omeganovaverse_sha256': str(bulk_view.get('release_omeganovaverse_sha256') or ''),
        'release_ultranovaverse_sha256': str(bulk_view.get('release_ultranovaverse_sha256') or ''),
        'release_hypernovaverse_sha256': str(bulk_view.get('release_hypernovaverse_sha256') or ''),
        'release_supernovaverse_sha256': str(bulk_view.get('release_supernovaverse_sha256') or ''),
        'release_novaverse_sha256': str(bulk_view.get('release_novaverse_sha256') or ''),
        'release_neoverse_sha256': str(bulk_view.get('release_neoverse_sha256') or ''),
        'release_holoverse_sha256': str(bulk_view.get('release_holoverse_sha256') or ''),
        'release_panverse_sha256': str(bulk_view.get('release_panverse_sha256') or ''),
        'release_polyverse_sha256': str(bulk_view.get('release_polyverse_sha256') or ''),
        'release_paraverse_sha256': str(bulk_view.get('release_paraverse_sha256') or ''),
        'release_metaverse_sha256': str(bulk_view.get('release_metaverse_sha256') or ''),
        'release_eraverse_sha256': str(bulk_view.get('release_eraverse_sha256') or ''),
        'release_epochverse_sha256': str(bulk_view.get('release_epochverse_sha256') or ''),
        'release_aeonverse_sha256': str(bulk_view.get('release_aeonverse_sha256') or ''),
        'release_timelessverse_sha256': str(bulk_view.get('release_timelessverse_sha256') or ''),
        'release_eternaverse_sha256': str(bulk_view.get('release_eternaverse_sha256') or ''),
        'release_infinitaverse_sha256': str(bulk_view.get('release_infinitaverse_sha256') or ''),
        'release_transcendaverse_sha256': str(bulk_view.get('release_transcendaverse_sha256') or ''),
        'release_ultimaverse_sha256': str(bulk_view.get('release_ultimaverse_sha256') or ''),
        'release_apexverse_sha256': str(bulk_view.get('release_apexverse_sha256') or ''),
        'release_quettaverse_sha256': str(bulk_view.get('release_quettaverse_sha256') or ''),
        'release_ronnaverse_sha256': str(bulk_view.get('release_ronnaverse_sha256') or ''),
        'release_yottaverse_sha256': str(bulk_view.get('release_yottaverse_sha256') or ''),
        'release_zettaverse_sha256': str(bulk_view.get('release_zettaverse_sha256') or ''),
        'release_exaverse_sha256': str(bulk_view.get('release_exaverse_sha256') or ''),
        'release_petaverse_sha256': str(bulk_view.get('release_petaverse_sha256') or ''),
        'release_teraverse_sha256': str(bulk_view.get('release_teraverse_sha256') or ''),
        'release_gigaverse_sha256': str(bulk_view.get('release_gigaverse_sha256') or ''),
        'release_megaverse_sha256': str(bulk_view.get('release_megaverse_sha256') or ''),
        'release_hyperverse_sha256': str(bulk_view.get('release_hyperverse_sha256') or ''),
        'release_omniverse_sha256': str(bulk_view.get('release_omniverse_sha256') or ''),
        'release_multiverse_sha256': str(bulk_view.get('release_multiverse_sha256') or ''),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_zetanovaverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_epsilonnovaverse_sha256': str(bulk_view.get('release_epsilonnovaverse_sha256') or ''),
        'release_deltanovaverse_sha256': str(bulk_view.get('release_deltanovaverse_sha256') or ''),
        'release_gammanovaverse_sha256': str(bulk_view.get('release_gammanovaverse_sha256') or ''),
        'release_betanovaverse_sha256': str(bulk_view.get('release_betanovaverse_sha256') or ''),
        'release_alphanovaverse_sha256': str(bulk_view.get('release_alphanovaverse_sha256') or ''),
        'release_omeganovaverse_sha256': str(bulk_view.get('release_omeganovaverse_sha256') or ''),
        'release_ultranovaverse_sha256': str(bulk_view.get('release_ultranovaverse_sha256') or ''),
        'release_hypernovaverse_sha256': str(bulk_view.get('release_hypernovaverse_sha256') or ''),
        'release_supernovaverse_sha256': str(bulk_view.get('release_supernovaverse_sha256') or ''),
        'release_novaverse_sha256': str(bulk_view.get('release_novaverse_sha256') or ''),
        'release_neoverse_sha256': str(bulk_view.get('release_neoverse_sha256') or ''),
        'release_holoverse_sha256': str(bulk_view.get('release_holoverse_sha256') or ''),
        'release_panverse_sha256': str(bulk_view.get('release_panverse_sha256') or ''),
        'release_polyverse_sha256': str(bulk_view.get('release_polyverse_sha256') or ''),
        'release_paraverse_sha256': str(bulk_view.get('release_paraverse_sha256') or ''),
        'release_metaverse_sha256': str(bulk_view.get('release_metaverse_sha256') or ''),
        'release_eraverse_sha256': str(bulk_view.get('release_eraverse_sha256') or ''),
        'release_epochverse_sha256': str(bulk_view.get('release_epochverse_sha256') or ''),
        'release_aeonverse_sha256': str(bulk_view.get('release_aeonverse_sha256') or ''),
        'release_timelessverse_sha256': str(bulk_view.get('release_timelessverse_sha256') or ''),
        'release_eternaverse_sha256': str(bulk_view.get('release_eternaverse_sha256') or ''),
        'release_infinitaverse_sha256': str(bulk_view.get('release_infinitaverse_sha256') or ''),
        'release_transcendaverse_sha256': str(bulk_view.get('release_transcendaverse_sha256') or ''),
        'release_ultimaverse_sha256': str(bulk_view.get('release_ultimaverse_sha256') or ''),
        'release_apexverse_sha256': str(bulk_view.get('release_apexverse_sha256') or ''),
        'release_quettaverse_sha256': str(bulk_view.get('release_quettaverse_sha256') or ''),
        'release_ronnaverse_sha256': str(bulk_view.get('release_ronnaverse_sha256') or ''),
        'release_yottaverse_sha256': str(bulk_view.get('release_yottaverse_sha256') or ''),
        'release_zettaverse_sha256': str(bulk_view.get('release_zettaverse_sha256') or ''),
        'release_exaverse_sha256': str(bulk_view.get('release_exaverse_sha256') or ''),
        'release_petaverse_sha256': str(bulk_view.get('release_petaverse_sha256') or ''),
        'release_teraverse_sha256': str(bulk_view.get('release_teraverse_sha256') or ''),
        'release_gigaverse_sha256': str(bulk_view.get('release_gigaverse_sha256') or ''),
        'release_megaverse_sha256': str(bulk_view.get('release_megaverse_sha256') or ''),
        'release_hyperverse_sha256': str(bulk_view.get('release_hyperverse_sha256') or ''),
        'release_omniverse_sha256': str(bulk_view.get('release_omniverse_sha256') or ''),
        'release_multiverse_sha256': str(bulk_view.get('release_multiverse_sha256') or ''),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_etanovaverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_zetanovaverse_sha256': str(bulk_view.get('release_zetanovaverse_sha256') or ''),
        'release_epsilonnovaverse_sha256': str(bulk_view.get('release_epsilonnovaverse_sha256') or ''),
        'release_deltanovaverse_sha256': str(bulk_view.get('release_deltanovaverse_sha256') or ''),
        'release_gammanovaverse_sha256': str(bulk_view.get('release_gammanovaverse_sha256') or ''),
        'release_betanovaverse_sha256': str(bulk_view.get('release_betanovaverse_sha256') or ''),
        'release_alphanovaverse_sha256': str(bulk_view.get('release_alphanovaverse_sha256') or ''),
        'release_omeganovaverse_sha256': str(bulk_view.get('release_omeganovaverse_sha256') or ''),
        'release_ultranovaverse_sha256': str(bulk_view.get('release_ultranovaverse_sha256') or ''),
        'release_hypernovaverse_sha256': str(bulk_view.get('release_hypernovaverse_sha256') or ''),
        'release_supernovaverse_sha256': str(bulk_view.get('release_supernovaverse_sha256') or ''),
        'release_novaverse_sha256': str(bulk_view.get('release_novaverse_sha256') or ''),
        'release_neoverse_sha256': str(bulk_view.get('release_neoverse_sha256') or ''),
        'release_holoverse_sha256': str(bulk_view.get('release_holoverse_sha256') or ''),
        'release_panverse_sha256': str(bulk_view.get('release_panverse_sha256') or ''),
        'release_polyverse_sha256': str(bulk_view.get('release_polyverse_sha256') or ''),
        'release_paraverse_sha256': str(bulk_view.get('release_paraverse_sha256') or ''),
        'release_metaverse_sha256': str(bulk_view.get('release_metaverse_sha256') or ''),
        'release_eraverse_sha256': str(bulk_view.get('release_eraverse_sha256') or ''),
        'release_epochverse_sha256': str(bulk_view.get('release_epochverse_sha256') or ''),
        'release_aeonverse_sha256': str(bulk_view.get('release_aeonverse_sha256') or ''),
        'release_timelessverse_sha256': str(bulk_view.get('release_timelessverse_sha256') or ''),
        'release_eternaverse_sha256': str(bulk_view.get('release_eternaverse_sha256') or ''),
        'release_infinitaverse_sha256': str(bulk_view.get('release_infinitaverse_sha256') or ''),
        'release_transcendaverse_sha256': str(bulk_view.get('release_transcendaverse_sha256') or ''),
        'release_ultimaverse_sha256': str(bulk_view.get('release_ultimaverse_sha256') or ''),
        'release_apexverse_sha256': str(bulk_view.get('release_apexverse_sha256') or ''),
        'release_quettaverse_sha256': str(bulk_view.get('release_quettaverse_sha256') or ''),
        'release_ronnaverse_sha256': str(bulk_view.get('release_ronnaverse_sha256') or ''),
        'release_yottaverse_sha256': str(bulk_view.get('release_yottaverse_sha256') or ''),
        'release_zettaverse_sha256': str(bulk_view.get('release_zettaverse_sha256') or ''),
        'release_exaverse_sha256': str(bulk_view.get('release_exaverse_sha256') or ''),
        'release_petaverse_sha256': str(bulk_view.get('release_petaverse_sha256') or ''),
        'release_teraverse_sha256': str(bulk_view.get('release_teraverse_sha256') or ''),
        'release_gigaverse_sha256': str(bulk_view.get('release_gigaverse_sha256') or ''),
        'release_megaverse_sha256': str(bulk_view.get('release_megaverse_sha256') or ''),
        'release_hyperverse_sha256': str(bulk_view.get('release_hyperverse_sha256') or ''),
        'release_omniverse_sha256': str(bulk_view.get('release_omniverse_sha256') or ''),
        'release_multiverse_sha256': str(bulk_view.get('release_multiverse_sha256') or ''),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_thetanovaverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_etanovaverse_sha256': str(bulk_view.get('release_etanovaverse_sha256') or ''),
        'release_zetanovaverse_sha256': str(bulk_view.get('release_zetanovaverse_sha256') or ''),
        'release_epsilonnovaverse_sha256': str(bulk_view.get('release_epsilonnovaverse_sha256') or ''),
        'release_deltanovaverse_sha256': str(bulk_view.get('release_deltanovaverse_sha256') or ''),
        'release_gammanovaverse_sha256': str(bulk_view.get('release_gammanovaverse_sha256') or ''),
        'release_betanovaverse_sha256': str(bulk_view.get('release_betanovaverse_sha256') or ''),
        'release_alphanovaverse_sha256': str(bulk_view.get('release_alphanovaverse_sha256') or ''),
        'release_omeganovaverse_sha256': str(bulk_view.get('release_omeganovaverse_sha256') or ''),
        'release_ultranovaverse_sha256': str(bulk_view.get('release_ultranovaverse_sha256') or ''),
        'release_hypernovaverse_sha256': str(bulk_view.get('release_hypernovaverse_sha256') or ''),
        'release_supernovaverse_sha256': str(bulk_view.get('release_supernovaverse_sha256') or ''),
        'release_novaverse_sha256': str(bulk_view.get('release_novaverse_sha256') or ''),
        'release_neoverse_sha256': str(bulk_view.get('release_neoverse_sha256') or ''),
        'release_holoverse_sha256': str(bulk_view.get('release_holoverse_sha256') or ''),
        'release_panverse_sha256': str(bulk_view.get('release_panverse_sha256') or ''),
        'release_polyverse_sha256': str(bulk_view.get('release_polyverse_sha256') or ''),
        'release_paraverse_sha256': str(bulk_view.get('release_paraverse_sha256') or ''),
        'release_metaverse_sha256': str(bulk_view.get('release_metaverse_sha256') or ''),
        'release_eraverse_sha256': str(bulk_view.get('release_eraverse_sha256') or ''),
        'release_epochverse_sha256': str(bulk_view.get('release_epochverse_sha256') or ''),
        'release_aeonverse_sha256': str(bulk_view.get('release_aeonverse_sha256') or ''),
        'release_timelessverse_sha256': str(bulk_view.get('release_timelessverse_sha256') or ''),
        'release_eternaverse_sha256': str(bulk_view.get('release_eternaverse_sha256') or ''),
        'release_infinitaverse_sha256': str(bulk_view.get('release_infinitaverse_sha256') or ''),
        'release_transcendaverse_sha256': str(bulk_view.get('release_transcendaverse_sha256') or ''),
        'release_ultimaverse_sha256': str(bulk_view.get('release_ultimaverse_sha256') or ''),
        'release_apexverse_sha256': str(bulk_view.get('release_apexverse_sha256') or ''),
        'release_quettaverse_sha256': str(bulk_view.get('release_quettaverse_sha256') or ''),
        'release_ronnaverse_sha256': str(bulk_view.get('release_ronnaverse_sha256') or ''),
        'release_yottaverse_sha256': str(bulk_view.get('release_yottaverse_sha256') or ''),
        'release_zettaverse_sha256': str(bulk_view.get('release_zettaverse_sha256') or ''),
        'release_exaverse_sha256': str(bulk_view.get('release_exaverse_sha256') or ''),
        'release_petaverse_sha256': str(bulk_view.get('release_petaverse_sha256') or ''),
        'release_teraverse_sha256': str(bulk_view.get('release_teraverse_sha256') or ''),
        'release_gigaverse_sha256': str(bulk_view.get('release_gigaverse_sha256') or ''),
        'release_megaverse_sha256': str(bulk_view.get('release_megaverse_sha256') or ''),
        'release_hyperverse_sha256': str(bulk_view.get('release_hyperverse_sha256') or ''),
        'release_omniverse_sha256': str(bulk_view.get('release_omniverse_sha256') or ''),
        'release_multiverse_sha256': str(bulk_view.get('release_multiverse_sha256') or ''),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_iotanovaverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_thetanovaverse_sha256': str(bulk_view.get('release_thetanovaverse_sha256') or ''),
        'release_etanovaverse_sha256': str(bulk_view.get('release_etanovaverse_sha256') or ''),
        'release_zetanovaverse_sha256': str(bulk_view.get('release_zetanovaverse_sha256') or ''),
        'release_epsilonnovaverse_sha256': str(bulk_view.get('release_epsilonnovaverse_sha256') or ''),
        'release_deltanovaverse_sha256': str(bulk_view.get('release_deltanovaverse_sha256') or ''),
        'release_gammanovaverse_sha256': str(bulk_view.get('release_gammanovaverse_sha256') or ''),
        'release_betanovaverse_sha256': str(bulk_view.get('release_betanovaverse_sha256') or ''),
        'release_alphanovaverse_sha256': str(bulk_view.get('release_alphanovaverse_sha256') or ''),
        'release_omeganovaverse_sha256': str(bulk_view.get('release_omeganovaverse_sha256') or ''),
        'release_ultranovaverse_sha256': str(bulk_view.get('release_ultranovaverse_sha256') or ''),
        'release_hypernovaverse_sha256': str(bulk_view.get('release_hypernovaverse_sha256') or ''),
        'release_supernovaverse_sha256': str(bulk_view.get('release_supernovaverse_sha256') or ''),
        'release_novaverse_sha256': str(bulk_view.get('release_novaverse_sha256') or ''),
        'release_neoverse_sha256': str(bulk_view.get('release_neoverse_sha256') or ''),
        'release_holoverse_sha256': str(bulk_view.get('release_holoverse_sha256') or ''),
        'release_panverse_sha256': str(bulk_view.get('release_panverse_sha256') or ''),
        'release_polyverse_sha256': str(bulk_view.get('release_polyverse_sha256') or ''),
        'release_paraverse_sha256': str(bulk_view.get('release_paraverse_sha256') or ''),
        'release_metaverse_sha256': str(bulk_view.get('release_metaverse_sha256') or ''),
        'release_eraverse_sha256': str(bulk_view.get('release_eraverse_sha256') or ''),
        'release_epochverse_sha256': str(bulk_view.get('release_epochverse_sha256') or ''),
        'release_aeonverse_sha256': str(bulk_view.get('release_aeonverse_sha256') or ''),
        'release_timelessverse_sha256': str(bulk_view.get('release_timelessverse_sha256') or ''),
        'release_eternaverse_sha256': str(bulk_view.get('release_eternaverse_sha256') or ''),
        'release_infinitaverse_sha256': str(bulk_view.get('release_infinitaverse_sha256') or ''),
        'release_transcendaverse_sha256': str(bulk_view.get('release_transcendaverse_sha256') or ''),
        'release_ultimaverse_sha256': str(bulk_view.get('release_ultimaverse_sha256') or ''),
        'release_apexverse_sha256': str(bulk_view.get('release_apexverse_sha256') or ''),
        'release_quettaverse_sha256': str(bulk_view.get('release_quettaverse_sha256') or ''),
        'release_ronnaverse_sha256': str(bulk_view.get('release_ronnaverse_sha256') or ''),
        'release_yottaverse_sha256': str(bulk_view.get('release_yottaverse_sha256') or ''),
        'release_zettaverse_sha256': str(bulk_view.get('release_zettaverse_sha256') or ''),
        'release_exaverse_sha256': str(bulk_view.get('release_exaverse_sha256') or ''),
        'release_petaverse_sha256': str(bulk_view.get('release_petaverse_sha256') or ''),
        'release_teraverse_sha256': str(bulk_view.get('release_teraverse_sha256') or ''),
        'release_gigaverse_sha256': str(bulk_view.get('release_gigaverse_sha256') or ''),
        'release_megaverse_sha256': str(bulk_view.get('release_megaverse_sha256') or ''),
        'release_hyperverse_sha256': str(bulk_view.get('release_hyperverse_sha256') or ''),
        'release_omniverse_sha256': str(bulk_view.get('release_omniverse_sha256') or ''),
        'release_multiverse_sha256': str(bulk_view.get('release_multiverse_sha256') or ''),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_kappanovaverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_iotanovaverse_sha256': str(bulk_view.get('release_iotanovaverse_sha256') or ''),
        'release_thetanovaverse_sha256': str(bulk_view.get('release_thetanovaverse_sha256') or ''),
        'release_etanovaverse_sha256': str(bulk_view.get('release_etanovaverse_sha256') or ''),
        'release_zetanovaverse_sha256': str(bulk_view.get('release_zetanovaverse_sha256') or ''),
        'release_epsilonnovaverse_sha256': str(bulk_view.get('release_epsilonnovaverse_sha256') or ''),
        'release_deltanovaverse_sha256': str(bulk_view.get('release_deltanovaverse_sha256') or ''),
        'release_gammanovaverse_sha256': str(bulk_view.get('release_gammanovaverse_sha256') or ''),
        'release_betanovaverse_sha256': str(bulk_view.get('release_betanovaverse_sha256') or ''),
        'release_alphanovaverse_sha256': str(bulk_view.get('release_alphanovaverse_sha256') or ''),
        'release_omeganovaverse_sha256': str(bulk_view.get('release_omeganovaverse_sha256') or ''),
        'release_ultranovaverse_sha256': str(bulk_view.get('release_ultranovaverse_sha256') or ''),
        'release_hypernovaverse_sha256': str(bulk_view.get('release_hypernovaverse_sha256') or ''),
        'release_supernovaverse_sha256': str(bulk_view.get('release_supernovaverse_sha256') or ''),
        'release_novaverse_sha256': str(bulk_view.get('release_novaverse_sha256') or ''),
        'release_neoverse_sha256': str(bulk_view.get('release_neoverse_sha256') or ''),
        'release_holoverse_sha256': str(bulk_view.get('release_holoverse_sha256') or ''),
        'release_panverse_sha256': str(bulk_view.get('release_panverse_sha256') or ''),
        'release_polyverse_sha256': str(bulk_view.get('release_polyverse_sha256') or ''),
        'release_paraverse_sha256': str(bulk_view.get('release_paraverse_sha256') or ''),
        'release_metaverse_sha256': str(bulk_view.get('release_metaverse_sha256') or ''),
        'release_eraverse_sha256': str(bulk_view.get('release_eraverse_sha256') or ''),
        'release_epochverse_sha256': str(bulk_view.get('release_epochverse_sha256') or ''),
        'release_aeonverse_sha256': str(bulk_view.get('release_aeonverse_sha256') or ''),
        'release_timelessverse_sha256': str(bulk_view.get('release_timelessverse_sha256') or ''),
        'release_eternaverse_sha256': str(bulk_view.get('release_eternaverse_sha256') or ''),
        'release_infinitaverse_sha256': str(bulk_view.get('release_infinitaverse_sha256') or ''),
        'release_transcendaverse_sha256': str(bulk_view.get('release_transcendaverse_sha256') or ''),
        'release_ultimaverse_sha256': str(bulk_view.get('release_ultimaverse_sha256') or ''),
        'release_apexverse_sha256': str(bulk_view.get('release_apexverse_sha256') or ''),
        'release_quettaverse_sha256': str(bulk_view.get('release_quettaverse_sha256') or ''),
        'release_ronnaverse_sha256': str(bulk_view.get('release_ronnaverse_sha256') or ''),
        'release_yottaverse_sha256': str(bulk_view.get('release_yottaverse_sha256') or ''),
        'release_zettaverse_sha256': str(bulk_view.get('release_zettaverse_sha256') or ''),
        'release_exaverse_sha256': str(bulk_view.get('release_exaverse_sha256') or ''),
        'release_petaverse_sha256': str(bulk_view.get('release_petaverse_sha256') or ''),
        'release_teraverse_sha256': str(bulk_view.get('release_teraverse_sha256') or ''),
        'release_gigaverse_sha256': str(bulk_view.get('release_gigaverse_sha256') or ''),
        'release_megaverse_sha256': str(bulk_view.get('release_megaverse_sha256') or ''),
        'release_hyperverse_sha256': str(bulk_view.get('release_hyperverse_sha256') or ''),
        'release_omniverse_sha256': str(bulk_view.get('release_omniverse_sha256') or ''),
        'release_multiverse_sha256': str(bulk_view.get('release_multiverse_sha256') or ''),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_lambdanovaverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_kappanovaverse_sha256': str(bulk_view.get('release_kappanovaverse_sha256') or ''),
        'release_iotanovaverse_sha256': str(bulk_view.get('release_iotanovaverse_sha256') or ''),
        'release_thetanovaverse_sha256': str(bulk_view.get('release_thetanovaverse_sha256') or ''),
        'release_etanovaverse_sha256': str(bulk_view.get('release_etanovaverse_sha256') or ''),
        'release_zetanovaverse_sha256': str(bulk_view.get('release_zetanovaverse_sha256') or ''),
        'release_epsilonnovaverse_sha256': str(bulk_view.get('release_epsilonnovaverse_sha256') or ''),
        'release_deltanovaverse_sha256': str(bulk_view.get('release_deltanovaverse_sha256') or ''),
        'release_gammanovaverse_sha256': str(bulk_view.get('release_gammanovaverse_sha256') or ''),
        'release_betanovaverse_sha256': str(bulk_view.get('release_betanovaverse_sha256') or ''),
        'release_alphanovaverse_sha256': str(bulk_view.get('release_alphanovaverse_sha256') or ''),
        'release_omeganovaverse_sha256': str(bulk_view.get('release_omeganovaverse_sha256') or ''),
        'release_ultranovaverse_sha256': str(bulk_view.get('release_ultranovaverse_sha256') or ''),
        'release_hypernovaverse_sha256': str(bulk_view.get('release_hypernovaverse_sha256') or ''),
        'release_supernovaverse_sha256': str(bulk_view.get('release_supernovaverse_sha256') or ''),
        'release_novaverse_sha256': str(bulk_view.get('release_novaverse_sha256') or ''),
        'release_neoverse_sha256': str(bulk_view.get('release_neoverse_sha256') or ''),
        'release_holoverse_sha256': str(bulk_view.get('release_holoverse_sha256') or ''),
        'release_panverse_sha256': str(bulk_view.get('release_panverse_sha256') or ''),
        'release_polyverse_sha256': str(bulk_view.get('release_polyverse_sha256') or ''),
        'release_paraverse_sha256': str(bulk_view.get('release_paraverse_sha256') or ''),
        'release_metaverse_sha256': str(bulk_view.get('release_metaverse_sha256') or ''),
        'release_eraverse_sha256': str(bulk_view.get('release_eraverse_sha256') or ''),
        'release_epochverse_sha256': str(bulk_view.get('release_epochverse_sha256') or ''),
        'release_aeonverse_sha256': str(bulk_view.get('release_aeonverse_sha256') or ''),
        'release_timelessverse_sha256': str(bulk_view.get('release_timelessverse_sha256') or ''),
        'release_eternaverse_sha256': str(bulk_view.get('release_eternaverse_sha256') or ''),
        'release_infinitaverse_sha256': str(bulk_view.get('release_infinitaverse_sha256') or ''),
        'release_transcendaverse_sha256': str(bulk_view.get('release_transcendaverse_sha256') or ''),
        'release_ultimaverse_sha256': str(bulk_view.get('release_ultimaverse_sha256') or ''),
        'release_apexverse_sha256': str(bulk_view.get('release_apexverse_sha256') or ''),
        'release_quettaverse_sha256': str(bulk_view.get('release_quettaverse_sha256') or ''),
        'release_ronnaverse_sha256': str(bulk_view.get('release_ronnaverse_sha256') or ''),
        'release_yottaverse_sha256': str(bulk_view.get('release_yottaverse_sha256') or ''),
        'release_zettaverse_sha256': str(bulk_view.get('release_zettaverse_sha256') or ''),
        'release_exaverse_sha256': str(bulk_view.get('release_exaverse_sha256') or ''),
        'release_petaverse_sha256': str(bulk_view.get('release_petaverse_sha256') or ''),
        'release_teraverse_sha256': str(bulk_view.get('release_teraverse_sha256') or ''),
        'release_gigaverse_sha256': str(bulk_view.get('release_gigaverse_sha256') or ''),
        'release_megaverse_sha256': str(bulk_view.get('release_megaverse_sha256') or ''),
        'release_hyperverse_sha256': str(bulk_view.get('release_hyperverse_sha256') or ''),
        'release_omniverse_sha256': str(bulk_view.get('release_omniverse_sha256') or ''),
        'release_multiverse_sha256': str(bulk_view.get('release_multiverse_sha256') or ''),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_munovaverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_lambdanovaverse_sha256': str(bulk_view.get('release_lambdanovaverse_sha256') or ''),
        'release_kappanovaverse_sha256': str(bulk_view.get('release_kappanovaverse_sha256') or ''),
        'release_iotanovaverse_sha256': str(bulk_view.get('release_iotanovaverse_sha256') or ''),
        'release_thetanovaverse_sha256': str(bulk_view.get('release_thetanovaverse_sha256') or ''),
        'release_etanovaverse_sha256': str(bulk_view.get('release_etanovaverse_sha256') or ''),
        'release_zetanovaverse_sha256': str(bulk_view.get('release_zetanovaverse_sha256') or ''),
        'release_epsilonnovaverse_sha256': str(bulk_view.get('release_epsilonnovaverse_sha256') or ''),
        'release_deltanovaverse_sha256': str(bulk_view.get('release_deltanovaverse_sha256') or ''),
        'release_gammanovaverse_sha256': str(bulk_view.get('release_gammanovaverse_sha256') or ''),
        'release_betanovaverse_sha256': str(bulk_view.get('release_betanovaverse_sha256') or ''),
        'release_alphanovaverse_sha256': str(bulk_view.get('release_alphanovaverse_sha256') or ''),
        'release_omeganovaverse_sha256': str(bulk_view.get('release_omeganovaverse_sha256') or ''),
        'release_ultranovaverse_sha256': str(bulk_view.get('release_ultranovaverse_sha256') or ''),
        'release_hypernovaverse_sha256': str(bulk_view.get('release_hypernovaverse_sha256') or ''),
        'release_supernovaverse_sha256': str(bulk_view.get('release_supernovaverse_sha256') or ''),
        'release_novaverse_sha256': str(bulk_view.get('release_novaverse_sha256') or ''),
        'release_neoverse_sha256': str(bulk_view.get('release_neoverse_sha256') or ''),
        'release_holoverse_sha256': str(bulk_view.get('release_holoverse_sha256') or ''),
        'release_panverse_sha256': str(bulk_view.get('release_panverse_sha256') or ''),
        'release_polyverse_sha256': str(bulk_view.get('release_polyverse_sha256') or ''),
        'release_paraverse_sha256': str(bulk_view.get('release_paraverse_sha256') or ''),
        'release_metaverse_sha256': str(bulk_view.get('release_metaverse_sha256') or ''),
        'release_eraverse_sha256': str(bulk_view.get('release_eraverse_sha256') or ''),
        'release_epochverse_sha256': str(bulk_view.get('release_epochverse_sha256') or ''),
        'release_aeonverse_sha256': str(bulk_view.get('release_aeonverse_sha256') or ''),
        'release_timelessverse_sha256': str(bulk_view.get('release_timelessverse_sha256') or ''),
        'release_eternaverse_sha256': str(bulk_view.get('release_eternaverse_sha256') or ''),
        'release_infinitaverse_sha256': str(bulk_view.get('release_infinitaverse_sha256') or ''),
        'release_transcendaverse_sha256': str(bulk_view.get('release_transcendaverse_sha256') or ''),
        'release_ultimaverse_sha256': str(bulk_view.get('release_ultimaverse_sha256') or ''),
        'release_apexverse_sha256': str(bulk_view.get('release_apexverse_sha256') or ''),
        'release_quettaverse_sha256': str(bulk_view.get('release_quettaverse_sha256') or ''),
        'release_ronnaverse_sha256': str(bulk_view.get('release_ronnaverse_sha256') or ''),
        'release_yottaverse_sha256': str(bulk_view.get('release_yottaverse_sha256') or ''),
        'release_zettaverse_sha256': str(bulk_view.get('release_zettaverse_sha256') or ''),
        'release_exaverse_sha256': str(bulk_view.get('release_exaverse_sha256') or ''),
        'release_petaverse_sha256': str(bulk_view.get('release_petaverse_sha256') or ''),
        'release_teraverse_sha256': str(bulk_view.get('release_teraverse_sha256') or ''),
        'release_gigaverse_sha256': str(bulk_view.get('release_gigaverse_sha256') or ''),
        'release_megaverse_sha256': str(bulk_view.get('release_megaverse_sha256') or ''),
        'release_hyperverse_sha256': str(bulk_view.get('release_hyperverse_sha256') or ''),
        'release_omniverse_sha256': str(bulk_view.get('release_omniverse_sha256') or ''),
        'release_multiverse_sha256': str(bulk_view.get('release_multiverse_sha256') or ''),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_nunovaverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_munovaverse_sha256': str(bulk_view.get('release_munovaverse_sha256') or ''),
        'release_lambdanovaverse_sha256': str(bulk_view.get('release_lambdanovaverse_sha256') or ''),
        'release_kappanovaverse_sha256': str(bulk_view.get('release_kappanovaverse_sha256') or ''),
        'release_iotanovaverse_sha256': str(bulk_view.get('release_iotanovaverse_sha256') or ''),
        'release_thetanovaverse_sha256': str(bulk_view.get('release_thetanovaverse_sha256') or ''),
        'release_etanovaverse_sha256': str(bulk_view.get('release_etanovaverse_sha256') or ''),
        'release_zetanovaverse_sha256': str(bulk_view.get('release_zetanovaverse_sha256') or ''),
        'release_epsilonnovaverse_sha256': str(bulk_view.get('release_epsilonnovaverse_sha256') or ''),
        'release_deltanovaverse_sha256': str(bulk_view.get('release_deltanovaverse_sha256') or ''),
        'release_gammanovaverse_sha256': str(bulk_view.get('release_gammanovaverse_sha256') or ''),
        'release_betanovaverse_sha256': str(bulk_view.get('release_betanovaverse_sha256') or ''),
        'release_alphanovaverse_sha256': str(bulk_view.get('release_alphanovaverse_sha256') or ''),
        'release_omeganovaverse_sha256': str(bulk_view.get('release_omeganovaverse_sha256') or ''),
        'release_ultranovaverse_sha256': str(bulk_view.get('release_ultranovaverse_sha256') or ''),
        'release_hypernovaverse_sha256': str(bulk_view.get('release_hypernovaverse_sha256') or ''),
        'release_supernovaverse_sha256': str(bulk_view.get('release_supernovaverse_sha256') or ''),
        'release_novaverse_sha256': str(bulk_view.get('release_novaverse_sha256') or ''),
        'release_neoverse_sha256': str(bulk_view.get('release_neoverse_sha256') or ''),
        'release_holoverse_sha256': str(bulk_view.get('release_holoverse_sha256') or ''),
        'release_panverse_sha256': str(bulk_view.get('release_panverse_sha256') or ''),
        'release_polyverse_sha256': str(bulk_view.get('release_polyverse_sha256') or ''),
        'release_paraverse_sha256': str(bulk_view.get('release_paraverse_sha256') or ''),
        'release_metaverse_sha256': str(bulk_view.get('release_metaverse_sha256') or ''),
        'release_eraverse_sha256': str(bulk_view.get('release_eraverse_sha256') or ''),
        'release_epochverse_sha256': str(bulk_view.get('release_epochverse_sha256') or ''),
        'release_aeonverse_sha256': str(bulk_view.get('release_aeonverse_sha256') or ''),
        'release_timelessverse_sha256': str(bulk_view.get('release_timelessverse_sha256') or ''),
        'release_eternaverse_sha256': str(bulk_view.get('release_eternaverse_sha256') or ''),
        'release_infinitaverse_sha256': str(bulk_view.get('release_infinitaverse_sha256') or ''),
        'release_transcendaverse_sha256': str(bulk_view.get('release_transcendaverse_sha256') or ''),
        'release_ultimaverse_sha256': str(bulk_view.get('release_ultimaverse_sha256') or ''),
        'release_apexverse_sha256': str(bulk_view.get('release_apexverse_sha256') or ''),
        'release_quettaverse_sha256': str(bulk_view.get('release_quettaverse_sha256') or ''),
        'release_ronnaverse_sha256': str(bulk_view.get('release_ronnaverse_sha256') or ''),
        'release_yottaverse_sha256': str(bulk_view.get('release_yottaverse_sha256') or ''),
        'release_zettaverse_sha256': str(bulk_view.get('release_zettaverse_sha256') or ''),
        'release_exaverse_sha256': str(bulk_view.get('release_exaverse_sha256') or ''),
        'release_petaverse_sha256': str(bulk_view.get('release_petaverse_sha256') or ''),
        'release_teraverse_sha256': str(bulk_view.get('release_teraverse_sha256') or ''),
        'release_gigaverse_sha256': str(bulk_view.get('release_gigaverse_sha256') or ''),
        'release_megaverse_sha256': str(bulk_view.get('release_megaverse_sha256') or ''),
        'release_hyperverse_sha256': str(bulk_view.get('release_hyperverse_sha256') or ''),
        'release_omniverse_sha256': str(bulk_view.get('release_omniverse_sha256') or ''),
        'release_multiverse_sha256': str(bulk_view.get('release_multiverse_sha256') or ''),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _expected_bulk_release_xinovaverse_sha256(bulk_view: dict[str, object]) -> str:
    payload = {
        'schema_version': str(bulk_view.get('schema_version') or ''),
        'decision': str(bulk_view.get('decision') or ''),
        'decision_code': int(bulk_view.get('decision_code') or 0),
        'release_nunovaverse_sha256': str(bulk_view.get('release_nunovaverse_sha256') or ''),
        'release_munovaverse_sha256': str(bulk_view.get('release_munovaverse_sha256') or ''),
        'release_lambdanovaverse_sha256': str(bulk_view.get('release_lambdanovaverse_sha256') or ''),
        'release_kappanovaverse_sha256': str(bulk_view.get('release_kappanovaverse_sha256') or ''),
        'release_iotanovaverse_sha256': str(bulk_view.get('release_iotanovaverse_sha256') or ''),
        'release_thetanovaverse_sha256': str(bulk_view.get('release_thetanovaverse_sha256') or ''),
        'release_etanovaverse_sha256': str(bulk_view.get('release_etanovaverse_sha256') or ''),
        'release_zetanovaverse_sha256': str(bulk_view.get('release_zetanovaverse_sha256') or ''),
        'release_epsilonnovaverse_sha256': str(bulk_view.get('release_epsilonnovaverse_sha256') or ''),
        'release_deltanovaverse_sha256': str(bulk_view.get('release_deltanovaverse_sha256') or ''),
        'release_gammanovaverse_sha256': str(bulk_view.get('release_gammanovaverse_sha256') or ''),
        'release_betanovaverse_sha256': str(bulk_view.get('release_betanovaverse_sha256') or ''),
        'release_alphanovaverse_sha256': str(bulk_view.get('release_alphanovaverse_sha256') or ''),
        'release_omeganovaverse_sha256': str(bulk_view.get('release_omeganovaverse_sha256') or ''),
        'release_ultranovaverse_sha256': str(bulk_view.get('release_ultranovaverse_sha256') or ''),
        'release_hypernovaverse_sha256': str(bulk_view.get('release_hypernovaverse_sha256') or ''),
        'release_supernovaverse_sha256': str(bulk_view.get('release_supernovaverse_sha256') or ''),
        'release_novaverse_sha256': str(bulk_view.get('release_novaverse_sha256') or ''),
        'release_neoverse_sha256': str(bulk_view.get('release_neoverse_sha256') or ''),
        'release_holoverse_sha256': str(bulk_view.get('release_holoverse_sha256') or ''),
        'release_panverse_sha256': str(bulk_view.get('release_panverse_sha256') or ''),
        'release_polyverse_sha256': str(bulk_view.get('release_polyverse_sha256') or ''),
        'release_paraverse_sha256': str(bulk_view.get('release_paraverse_sha256') or ''),
        'release_metaverse_sha256': str(bulk_view.get('release_metaverse_sha256') or ''),
        'release_eraverse_sha256': str(bulk_view.get('release_eraverse_sha256') or ''),
        'release_epochverse_sha256': str(bulk_view.get('release_epochverse_sha256') or ''),
        'release_aeonverse_sha256': str(bulk_view.get('release_aeonverse_sha256') or ''),
        'release_timelessverse_sha256': str(bulk_view.get('release_timelessverse_sha256') or ''),
        'release_eternaverse_sha256': str(bulk_view.get('release_eternaverse_sha256') or ''),
        'release_infinitaverse_sha256': str(bulk_view.get('release_infinitaverse_sha256') or ''),
        'release_transcendaverse_sha256': str(bulk_view.get('release_transcendaverse_sha256') or ''),
        'release_ultimaverse_sha256': str(bulk_view.get('release_ultimaverse_sha256') or ''),
        'release_apexverse_sha256': str(bulk_view.get('release_apexverse_sha256') or ''),
        'release_quettaverse_sha256': str(bulk_view.get('release_quettaverse_sha256') or ''),
        'release_ronnaverse_sha256': str(bulk_view.get('release_ronnaverse_sha256') or ''),
        'release_yottaverse_sha256': str(bulk_view.get('release_yottaverse_sha256') or ''),
        'release_zettaverse_sha256': str(bulk_view.get('release_zettaverse_sha256') or ''),
        'release_exaverse_sha256': str(bulk_view.get('release_exaverse_sha256') or ''),
        'release_petaverse_sha256': str(bulk_view.get('release_petaverse_sha256') or ''),
        'release_teraverse_sha256': str(bulk_view.get('release_teraverse_sha256') or ''),
        'release_gigaverse_sha256': str(bulk_view.get('release_gigaverse_sha256') or ''),
        'release_megaverse_sha256': str(bulk_view.get('release_megaverse_sha256') or ''),
        'release_hyperverse_sha256': str(bulk_view.get('release_hyperverse_sha256') or ''),
        'release_omniverse_sha256': str(bulk_view.get('release_omniverse_sha256') or ''),
        'release_multiverse_sha256': str(bulk_view.get('release_multiverse_sha256') or ''),
        'release_universe_sha256': str(bulk_view.get('release_universe_sha256') or ''),
        'release_galaxy_sha256': str(bulk_view.get('release_galaxy_sha256') or ''),
        'release_constellation_sha256': str(bulk_view.get('release_constellation_sha256') or ''),
        'release_beacon_sha256': str(bulk_view.get('release_beacon_sha256') or ''),
        'release_anchor_sha256': str(bulk_view.get('release_anchor_sha256') or ''),
        'release_capsule_sha256': str(bulk_view.get('release_capsule_sha256') or ''),
        'release_lineage_sha256': str(bulk_view.get('release_lineage_sha256') or ''),
        'release_verdict_sha256': str(bulk_view.get('release_verdict_sha256') or ''),
        'release_attestation_sha256': str(bulk_view.get('release_attestation_sha256') or ''),
        'release_root_sha256': str(bulk_view.get('release_root_sha256') or ''),
        'release_manifest_sha256': str(bulk_view.get('release_manifest_sha256') or ''),
        'release_fingerprint_sha256': str(bulk_view.get('release_fingerprint_sha256') or ''),
        'contract_envelope_sha256': str(bulk_view.get('contract_envelope_sha256') or ''),
        'strategy_envelope_sha256': str(bulk_view.get('strategy_envelope_sha256') or ''),
        'gate_status_index_sha256': str(bulk_view.get('gate_status_index_sha256') or ''),
        'composite_profile_sha256': str(bulk_view.get('composite_profile_sha256') or ''),
        'domain_rollup_sha256': str(bulk_view.get('domain_rollup_sha256') or ''),
        'evidence_profile_sha256': str(bulk_view.get('evidence_profile_sha256') or ''),
        'hold_signature_sha256': str(bulk_view.get('hold_signature_sha256') or ''),
        'strategy_signature_sha256': str(bulk_view.get('strategy_signature_sha256') or ''),
        'enabled_checks': list((bulk_view.get('check_enablement') or {}).get('enabled_keys') or []),
        'disabled_checks': list((bulk_view.get('check_enablement') or {}).get('disabled_keys') or []),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _write_go_decision_evidence_bundle(tmp_path: Path) -> dict[str, Path]:
    doc_sync_path = tmp_path / 'e13-doc-sync-check-report.json'
    quality_path = tmp_path / 'e11-quality-regression-report.json'
    perf_path = tmp_path / 'e11-perf-cost-baseline-report.json'
    postgres_soak_path = tmp_path / 'e13-postgres-soak-benchmark-report.json'
    beta_suite_path = tmp_path / 'e13-release-gate-beta-suite-plan.json'
    ga_suite_path = tmp_path / 'e13-release-gate-ga-suite-plan.json'
    roadmap_suite_path = tmp_path / 'e13-release-gate-roadmap-suite-plan.json'
    release_gate_path = tmp_path / 'e13-release-gate-validation-plan.json'
    standard_path = tmp_path / 'v2-release-switch-standard.md'
    decision_path = tmp_path / 'release-switch-decision.json'

    doc_sync_path.write_text(
        json.dumps(
            {
                'status': 'pass',
                'failed_count': 0,
                'checks': [
                    {'name': 'release_switch_standard_completeness', 'status': 'pass'},
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + '\n',
        encoding='utf-8',
    )
    quality_path.write_text(
        json.dumps({'regressed_count': 0}, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8',
    )
    perf_path.write_text(
        json.dumps({'regressed_count': 0}, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8',
    )
    postgres_soak_path.write_text(
        json.dumps(
            {
                'run_postgres': True,
                'runs': {
                    'dual_write': {
                        'summary': {'count': 4},
                    }
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + '\n',
        encoding='utf-8',
    )
    beta_suite_path.write_text(
        json.dumps(
            _plan_payload(
                [
                    'ci',
                    'container_smoke',
                    'doc_sync',
                    'quality_regression',
                    'perf_cost_baseline',
                ]
            ),
            ensure_ascii=False,
            indent=2,
        )
        + '\n',
        encoding='utf-8',
    )
    ga_suite_path.write_text(
        json.dumps(
            _plan_payload(
                [
                    'postgres_soak',
                    'postgres_ga',
                    'worker_ga',
                    'provider_ga',
                    'calibration_ga',
                    'review_queue_ga',
                ]
            ),
            ensure_ascii=False,
            indent=2,
        )
        + '\n',
        encoding='utf-8',
    )
    roadmap_suite_path.write_text(
        json.dumps(
            _plan_payload(['roadmap_extension']),
            ensure_ascii=False,
            indent=2,
        )
        + '\n',
        encoding='utf-8',
    )
    release_gate_path.write_text(
        json.dumps(
            _plan_payload(
                ['beta_gate', 'ga_gate', 'roadmap_gate'],
                stage_output_paths={
                    'beta_gate': beta_suite_path,
                    'ga_gate': ga_suite_path,
                    'roadmap_gate': roadmap_suite_path,
                },
                stage_commands=_release_gate_stage_contract_commands(
                    beta_output=beta_suite_path,
                    ga_output=ga_suite_path,
                    roadmap_output=roadmap_suite_path,
                ),
            ),
            ensure_ascii=False,
            indent=2,
        )
        + '\n',
        encoding='utf-8',
    )
    standard_path.write_text(
        '\n'.join(
            [
                '# V2 Release Switch Standard',
                '- graph_is_source_of_truth',
                '- review_queue_operational',
                '- publication_view_count>=2',
                '- postgres_repository_stable',
                '- regression_beats_v1',
            ]
        )
        + '\n',
        encoding='utf-8',
    )

    return {
        'doc_sync_path': doc_sync_path,
        'quality_path': quality_path,
        'perf_path': perf_path,
        'postgres_soak_path': postgres_soak_path,
        'beta_suite_path': beta_suite_path,
        'ga_suite_path': ga_suite_path,
        'roadmap_suite_path': roadmap_suite_path,
        'release_gate_path': release_gate_path,
        'standard_path': standard_path,
        'decision_path': decision_path,
    }


class ReleaseSwitchValidationScriptTests(unittest.TestCase):
    def test_script_dry_run_emits_default_release_switch_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            output_path = tmp_path / 'release-switch-plan.json'
            decision_path = tmp_path / 'release-switch-decision.json'
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--python',
                    'python3',
                    '--dry-run',
                    '--output',
                    str(output_path),
                    '--decision-output',
                    str(decision_path),
                    '--doc-sync-report',
                    str(tmp_path / 'doc-sync-report.json'),
                    '--quality-report',
                    str(tmp_path / 'quality-report.json'),
                    '--perf-report',
                    str(tmp_path / 'perf-report.json'),
                    '--postgres-soak-benchmark-report',
                    str(tmp_path / 'postgres-soak-benchmark-report.json'),
                    '--ga-suite-output',
                    str(tmp_path / 'release-gate-ga-suite-plan.json'),
                    '--release-standard-doc',
                    str(tmp_path / 'v2-release-switch-standard.md'),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Selected stages: release_gate, release_contract, doc_sync', completed.stdout)
            self.assertIn('scripts/run_release_gate_validation.py', completed.stdout)
            self.assertIn('scripts/run_tp_tests.py TP-E9-03 TP-E11-03 TP-E13-03', completed.stdout)
            self.assertIn('scripts/run_doc_sync_check.py', completed.stdout)

            plan = json.loads(output_path.read_text(encoding='utf-8'))
            self.assertEqual(plan.get('stage_count'), 3)
            self.assertEqual(
                [item.get('name') for item in plan.get('stages', [])],
                ['release_gate', 'release_contract', 'doc_sync'],
            )

            decision = json.loads(decision_path.read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            self.assertGreaterEqual(int(decision.get('hold_count', 0)), 1)
            missing = decision.get('missing_or_invalid_evidence', [])
            self.assertTrue(missing)

    def test_script_respects_stage_selection_and_option_forwarding(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                '--python',
                'python3',
                '--stages',
                'release_gate',
                '--coverage-fail-under',
                '72.5',
                '--no-coverage',
                '--allow-regression',
                '--container-image-tag',
                'omni-skill-pipeline:rc',
                '--container-name',
                'omni-release-switch',
                '--container-host',
                '0.0.0.0',
                '--container-port',
                '19090',
                '--container-timeout-seconds',
                '41',
                '--container-interval-seconds',
                '2',
                '--container-skip-build',
                '--postgres-dsn',
                'postgresql://validator',
                '--postgres-soak-iterations',
                '88',
                '--postgres-ga-iterations',
                '99',
                '--allow-secondary-failures',
                '--calibration-margin',
                '0.06',
                '--dry-run',
                '--output',
                '-',
                '--decision-output',
                '-',
            ],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn('Selected stages: release_gate', completed.stdout)
        self.assertIn('--coverage-fail-under 72.5', completed.stdout)
        self.assertIn('--no-coverage', completed.stdout)
        self.assertIn('--allow-regression', completed.stdout)
        self.assertIn('--container-image-tag omni-skill-pipeline:rc', completed.stdout)
        self.assertIn('--container-name omni-release-switch', completed.stdout)
        self.assertIn('--container-host 0.0.0.0', completed.stdout)
        self.assertIn('--container-port 19090', completed.stdout)
        self.assertIn('--container-timeout-seconds 41.0', completed.stdout)
        self.assertIn('--container-interval-seconds 2.0', completed.stdout)
        self.assertIn('--container-skip-build', completed.stdout)
        self.assertIn('--postgres-dsn postgresql://validator', completed.stdout)
        self.assertIn('--postgres-soak-iterations 88', completed.stdout)
        self.assertIn('--postgres-ga-iterations 99', completed.stdout)
        self.assertIn('--allow-secondary-failures', completed.stdout)
        self.assertIn('--calibration-margin 0.06', completed.stdout)
        self.assertNotIn('scripts/run_tp_tests.py', completed.stdout)
        self.assertNotIn('scripts/run_doc_sync_check.py --output', completed.stdout)

    def test_script_decision_only_can_emit_go_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            doc_sync_path = tmp_path / 'e13-doc-sync-check-report.json'
            quality_path = tmp_path / 'e11-quality-regression-report.json'
            perf_path = tmp_path / 'e11-perf-cost-baseline-report.json'
            postgres_soak_path = tmp_path / 'e13-postgres-soak-benchmark-report.json'
            beta_suite_path = tmp_path / 'e13-release-gate-beta-suite-plan.json'
            ga_suite_path = tmp_path / 'e13-release-gate-ga-suite-plan.json'
            roadmap_suite_path = tmp_path / 'e13-release-gate-roadmap-suite-plan.json'
            release_gate_path = tmp_path / 'e13-release-gate-validation-plan.json'
            standard_path = tmp_path / 'v2-release-switch-standard.md'
            decision_path = tmp_path / 'release-switch-decision.json'

            doc_sync_path.write_text(
                json.dumps(
                    {
                        'status': 'pass',
                        'failed_count': 0,
                        'checks': [
                            {'name': 'release_switch_standard_completeness', 'status': 'pass'},
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + '\n',
                encoding='utf-8',
            )
            quality_path.write_text(
                json.dumps({'regressed_count': 0}, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            perf_path.write_text(
                json.dumps({'regressed_count': 0}, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            postgres_soak_path.write_text(
                json.dumps(
                    {
                        'run_postgres': True,
                        'runs': {
                            'dual_write': {
                                'summary': {'count': 4},
                            }
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + '\n',
                encoding='utf-8',
            )
            beta_suite_path.write_text(
                json.dumps(
                    _plan_payload(
                        [
                            'ci',
                            'container_smoke',
                            'doc_sync',
                            'quality_regression',
                            'perf_cost_baseline',
                        ]
                    ),
                    ensure_ascii=False,
                    indent=2,
                )
                + '\n',
                encoding='utf-8',
            )
            ga_suite_path.write_text(
                json.dumps(
                    _plan_payload(
                        [
                            'postgres_soak',
                            'postgres_ga',
                            'worker_ga',
                            'provider_ga',
                            'calibration_ga',
                            'review_queue_ga',
                        ]
                    ),
                    ensure_ascii=False,
                    indent=2,
                )
                + '\n',
                encoding='utf-8',
            )
            roadmap_suite_path.write_text(
                json.dumps(
                    _plan_payload(['roadmap_extension']),
                    ensure_ascii=False,
                    indent=2,
                )
                + '\n',
                encoding='utf-8',
            )
            release_gate_path.write_text(
                json.dumps(
                    _plan_payload(
                        ['beta_gate', 'ga_gate', 'roadmap_gate'],
                        stage_output_paths={
                            'beta_gate': beta_suite_path,
                            'ga_gate': ga_suite_path,
                            'roadmap_gate': roadmap_suite_path,
                        },
                        stage_commands=_release_gate_stage_contract_commands(
                            beta_output=beta_suite_path,
                            ga_output=ga_suite_path,
                            roadmap_output=roadmap_suite_path,
                        ),
                    ),
                    ensure_ascii=False,
                    indent=2,
                )
                + '\n',
                encoding='utf-8',
            )
            standard_path.write_text(
                '\n'.join(
                    [
                        '# V2 Release Switch Standard',
                        '- graph_is_source_of_truth',
                        '- review_queue_operational',
                        '- publication_view_count>=2',
                        '- postgres_repository_stable',
                        '- regression_beats_v1',
                    ]
                )
                + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(doc_sync_path),
                    '--quality-report',
                    str(quality_path),
                    '--perf-report',
                    str(perf_path),
                    '--postgres-soak-benchmark-report',
                    str(postgres_soak_path),
                    '--beta-suite-output',
                    str(beta_suite_path),
                    '--ga-suite-output',
                    str(ga_suite_path),
                    '--roadmap-suite-output',
                    str(roadmap_suite_path),
                    '--release-gate-output',
                    str(release_gate_path),
                    '--release-standard-doc',
                    str(standard_path),
                    '--decision-output',
                    str(decision_path),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(decision_path.read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            self.assertEqual(decision.get('hold_count'), 0)
            self.assertEqual(decision.get('pass_count'), 46)
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_stage_pack_complete'))
            self.assertTrue(summary.get('release_gate_output_binding_pass'))
            self.assertTrue(summary.get('release_gate_stage_contract_pass'))
            self.assertTrue(summary.get('release_gate_script_position_pass'))
            self.assertTrue(summary.get('release_gate_python_binding_pass'))
            self.assertTrue(summary.get('release_gate_python_optimization_pass'))
            self.assertTrue(summary.get('release_gate_python_option_optimization_pass'))
            self.assertTrue(summary.get('release_gate_python_optimize_env_pass'))
            self.assertTrue(summary.get('release_gate_python_path_env_pass'))
            self.assertTrue(summary.get('release_gate_python_home_env_pass'))
            self.assertTrue(summary.get('release_gate_python_user_base_env_pass'))
            self.assertTrue(summary.get('release_gate_python_breakpoint_env_pass'))
            self.assertTrue(summary.get('release_gate_python_startup_env_pass'))
            self.assertTrue(summary.get('release_gate_python_inspect_env_pass'))
            self.assertTrue(summary.get('release_gate_python_warnings_env_pass'))
            self.assertTrue(summary.get('release_gate_python_env_wildcard_pass'))
            self.assertTrue(summary.get('release_gate_path_env_pass'))
            self.assertTrue(summary.get('release_gate_ld_preload_env_pass'))
            self.assertTrue(summary.get('release_gate_ld_library_path_env_pass'))
            self.assertTrue(summary.get('release_gate_ld_audit_env_pass'))
            self.assertTrue(summary.get('release_gate_ld_env_wildcard_pass'))
            self.assertTrue(summary.get('release_gate_glibc_tunables_env_pass'))
            self.assertTrue(summary.get('release_gate_glibc_env_wildcard_pass'))
            self.assertTrue(summary.get('release_gate_malloc_check_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_trace_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_perturb_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_arena_max_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_mmap_max_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_mmap_threshold_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_top_pad_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_trim_threshold_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_arena_test_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_per_thread_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_env_wildcard_pass'))
            self.assertTrue(summary.get('release_gate_python_option_inline_exec_pass'))
            self.assertTrue(summary.get('release_gate_coverage_floor_pass'))
            self.assertTrue(summary.get('release_gate_inline_exec_pass'))
            self.assertTrue(summary.get('release_gate_option_override_pass'))
            self.assertTrue(summary.get('release_gate_dry_run_pass'))
            self.assertTrue(summary.get('release_gate_relaxed_flags_pass'))
            self.assertTrue(summary.get('beta_suite_stage_pack_complete'))
            self.assertTrue(summary.get('ga_suite_stage_pack_complete'))
            self.assertTrue(summary.get('roadmap_suite_stage_pack_complete'))
            self.assertTrue(summary.get('evidence_cohort_skew_gate_pass'))

    def test_script_decision_only_emits_bulk_strategy_view_for_go_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(bulk_view.get('schema_version'), 'release_switch_bulk_strategy.v2')
            self.assertEqual(bulk_view.get('decision'), 'GO')
            self.assertEqual(bulk_view.get('gate_count'), decision.get('gate_count'))
            self.assertEqual(bulk_view.get('pass_count'), decision.get('pass_count'))
            self.assertEqual(bulk_view.get('hold_count'), decision.get('hold_count'))
            self.assertEqual(len(bulk_view.get('gate_rows', [])), int(decision.get('gate_count', 0)))
            self.assertEqual(len(bulk_view.get('gate_status_bitmap', [])), int(decision.get('gate_count', 0)))
            self.assertEqual(
                bulk_view.get('gate_status_index', {}).get('release_gate_malloc_per_thread_env'),
                1,
            )
            check_enablement = bulk_view.get('check_enablement', {})
            self.assertEqual(
                int(check_enablement.get('enabled_count', 0)),
                len(check_enablement.get('enabled_keys', [])),
            )
            self.assertEqual(
                int(check_enablement.get('disabled_count', 0)),
                len(check_enablement.get('disabled_keys', [])),
            )

    def test_script_decision_only_emits_bulk_strategy_view_for_hold_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(bulk_view.get('schema_version'), 'release_switch_bulk_strategy.v2')
            self.assertEqual(bulk_view.get('decision'), 'HOLD')
            self.assertGreaterEqual(int(bulk_view.get('hold_count', 0)), 1)
            self.assertEqual(
                bulk_view.get('gate_status_index', {}).get('release_gate_malloc_per_thread_env'),
                0,
            )
            self.assertIn(
                'release_gate_malloc_per_thread_env',
                bulk_view.get('hold_gate_names', []),
            )

    def test_script_decision_only_emits_bulk_strategy_domain_rollup_for_go_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(bulk_view.get('decision_code'), 1)
            self.assertEqual(bulk_view.get('hold_signature'), 'GO')
            domain_rollup = bulk_view.get('domain_rollup', {})
            self.assertIn('release_gate', domain_rollup)
            self.assertGreaterEqual(int(domain_rollup['release_gate'].get('gate_count', 0)), 1)
            self.assertEqual(int(domain_rollup['release_gate'].get('hold_count', 0)), 0)
            self.assertEqual(
                int(domain_rollup['release_gate'].get('pass_count', 0)),
                int(domain_rollup['release_gate'].get('gate_count', 0)),
            )
            self.assertEqual(len(bulk_view.get('hold_gate_indices', [])), 0)

    def test_script_decision_only_emits_bulk_strategy_domain_rollup_for_hold_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(bulk_view.get('decision_code'), 0)
            self.assertIn('release_gate_malloc_per_thread_env', str(bulk_view.get('hold_signature', '')))
            domain_rollup = bulk_view.get('domain_rollup', {})
            self.assertIn('release_gate', domain_rollup)
            self.assertGreaterEqual(int(domain_rollup['release_gate'].get('hold_count', 0)), 1)
            hold_indices = bulk_view.get('hold_gate_indices', [])
            self.assertGreaterEqual(len(hold_indices), 1)
            gate_rows = bulk_view.get('gate_rows', [])
            per_thread_row = next(
                (
                    row
                    for row in gate_rows
                    if row.get('name') == 'release_gate_malloc_per_thread_env'
                ),
                None,
            )
            self.assertIsNotNone(per_thread_row)
            self.assertIn(int(per_thread_row.get('idx')), hold_indices)

    def test_script_decision_only_emits_bulk_strategy_signature_hash_for_go_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            bulk_view = decision.get('bulk_strategy_view', {})
            hold_signature = str(bulk_view.get('hold_signature') or '')
            self.assertEqual(hold_signature, 'GO')
            self.assertEqual(
                bulk_view.get('hold_signature_sha256'),
                hashlib.sha256(hold_signature.encode('utf-8')).hexdigest(),
            )
            self.assertEqual(
                bulk_view.get('strategy_signature_sha256'),
                _expected_bulk_strategy_signature_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('hold_signature_sha256') or '')), 64)
            self.assertEqual(len(str(bulk_view.get('strategy_signature_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_signature_hash_for_hold_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            bulk_view = decision.get('bulk_strategy_view', {})
            hold_signature = str(bulk_view.get('hold_signature') or '')
            self.assertIn('release_gate_malloc_per_thread_env', hold_signature)
            self.assertEqual(
                bulk_view.get('hold_signature_sha256'),
                hashlib.sha256(hold_signature.encode('utf-8')).hexdigest(),
            )
            self.assertEqual(
                bulk_view.get('strategy_signature_sha256'),
                _expected_bulk_strategy_signature_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('hold_signature_sha256') or '')), 64)
            self.assertEqual(len(str(bulk_view.get('strategy_signature_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_domain_rollup_hash_for_go_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('domain_rollup_sha256'),
                _expected_bulk_domain_rollup_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('domain_rollup_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_domain_rollup_hash_for_hold_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('domain_rollup_sha256'),
                _expected_bulk_domain_rollup_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('domain_rollup_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_evidence_profile_hash_for_go_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('evidence_profile_sha256'),
                _expected_bulk_evidence_profile_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('evidence_profile_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_evidence_profile_hash_for_hold_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('evidence_profile_sha256'),
                _expected_bulk_evidence_profile_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('evidence_profile_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_gate_status_index_hash_for_go_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('gate_status_index_sha256'),
                _expected_bulk_gate_status_index_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('gate_status_index_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_gate_status_index_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('gate_status_index_sha256'),
                _expected_bulk_gate_status_index_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('gate_status_index_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_composite_profile_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('composite_profile_sha256'),
                _expected_bulk_composite_profile_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('composite_profile_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_composite_profile_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('composite_profile_sha256'),
                _expected_bulk_composite_profile_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('composite_profile_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_envelope_hash_for_go_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('strategy_envelope_sha256'),
                _expected_bulk_strategy_envelope_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('strategy_envelope_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_envelope_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('strategy_envelope_sha256'),
                _expected_bulk_strategy_envelope_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('strategy_envelope_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_contract_signature_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('contract_signature_sha256'),
                _expected_bulk_contract_signature_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('contract_signature_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_contract_signature_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('contract_signature_sha256'),
                _expected_bulk_contract_signature_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('contract_signature_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_contract_envelope_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('contract_envelope_sha256'),
                _expected_bulk_contract_envelope_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('contract_envelope_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_contract_envelope_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('contract_envelope_sha256'),
                _expected_bulk_contract_envelope_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('contract_envelope_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_fingerprint_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_fingerprint_sha256'),
                _expected_bulk_release_fingerprint_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_fingerprint_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_fingerprint_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_fingerprint_sha256'),
                _expected_bulk_release_fingerprint_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_fingerprint_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_manifest_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_manifest_sha256'),
                _expected_bulk_release_manifest_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_manifest_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_manifest_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_manifest_sha256'),
                _expected_bulk_release_manifest_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_manifest_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_root_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_root_sha256'),
                _expected_bulk_release_root_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_root_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_root_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_root_sha256'),
                _expected_bulk_release_root_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_root_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_attestation_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_attestation_sha256'),
                _expected_bulk_release_attestation_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_attestation_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_attestation_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_attestation_sha256'),
                _expected_bulk_release_attestation_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_attestation_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_verdict_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_verdict_sha256'),
                _expected_bulk_release_verdict_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_verdict_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_verdict_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_verdict_sha256'),
                _expected_bulk_release_verdict_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_verdict_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_lineage_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_lineage_sha256'),
                _expected_bulk_release_lineage_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_lineage_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_lineage_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_lineage_sha256'),
                _expected_bulk_release_lineage_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_lineage_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_capsule_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_capsule_sha256'),
                _expected_bulk_release_capsule_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_capsule_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_capsule_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_capsule_sha256'),
                _expected_bulk_release_capsule_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_capsule_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_anchor_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_anchor_sha256'),
                _expected_bulk_release_anchor_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_anchor_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_anchor_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_anchor_sha256'),
                _expected_bulk_release_anchor_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_anchor_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_beacon_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_beacon_sha256'),
                _expected_bulk_release_beacon_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_beacon_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_beacon_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_beacon_sha256'),
                _expected_bulk_release_beacon_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_beacon_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_constellation_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_constellation_sha256'),
                _expected_bulk_release_constellation_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_constellation_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_constellation_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_constellation_sha256'),
                _expected_bulk_release_constellation_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_constellation_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_galaxy_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_galaxy_sha256'),
                _expected_bulk_release_galaxy_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_galaxy_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_galaxy_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_galaxy_sha256'),
                _expected_bulk_release_galaxy_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_galaxy_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_universe_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_universe_sha256'),
                _expected_bulk_release_universe_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_universe_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_universe_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_universe_sha256'),
                _expected_bulk_release_universe_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_universe_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_multiverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_multiverse_sha256'),
                _expected_bulk_release_multiverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_multiverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_multiverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_multiverse_sha256'),
                _expected_bulk_release_multiverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_multiverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_omniverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_omniverse_sha256'),
                _expected_bulk_release_omniverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_omniverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_omniverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_omniverse_sha256'),
                _expected_bulk_release_omniverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_omniverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_hyperverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_hyperverse_sha256'),
                _expected_bulk_release_hyperverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_hyperverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_hyperverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_hyperverse_sha256'),
                _expected_bulk_release_hyperverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_hyperverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_megaverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_megaverse_sha256'),
                _expected_bulk_release_megaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_megaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_megaverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_megaverse_sha256'),
                _expected_bulk_release_megaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_megaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_gigaverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_gigaverse_sha256'),
                _expected_bulk_release_gigaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_gigaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_gigaverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_gigaverse_sha256'),
                _expected_bulk_release_gigaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_gigaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_teraverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_teraverse_sha256'),
                _expected_bulk_release_teraverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_teraverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_teraverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_teraverse_sha256'),
                _expected_bulk_release_teraverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_teraverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_petaverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_petaverse_sha256'),
                _expected_bulk_release_petaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_petaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_petaverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_petaverse_sha256'),
                _expected_bulk_release_petaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_petaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_exaverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_exaverse_sha256'),
                _expected_bulk_release_exaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_exaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_exaverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_exaverse_sha256'),
                _expected_bulk_release_exaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_exaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_zettaverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_zettaverse_sha256'),
                _expected_bulk_release_zettaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_zettaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_zettaverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_zettaverse_sha256'),
                _expected_bulk_release_zettaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_zettaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_yottaverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_yottaverse_sha256'),
                _expected_bulk_release_yottaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_yottaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_yottaverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_yottaverse_sha256'),
                _expected_bulk_release_yottaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_yottaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_ronnaverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_ronnaverse_sha256'),
                _expected_bulk_release_ronnaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_ronnaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_ronnaverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_ronnaverse_sha256'),
                _expected_bulk_release_ronnaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_ronnaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_quettaverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_quettaverse_sha256'),
                _expected_bulk_release_quettaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_quettaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_quettaverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_quettaverse_sha256'),
                _expected_bulk_release_quettaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_quettaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_apexverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_apexverse_sha256'),
                _expected_bulk_release_apexverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_apexverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_apexverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_apexverse_sha256'),
                _expected_bulk_release_apexverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_apexverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_ultimaverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_ultimaverse_sha256'),
                _expected_bulk_release_ultimaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_ultimaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_ultimaverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_ultimaverse_sha256'),
                _expected_bulk_release_ultimaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_ultimaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_transcendaverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_transcendaverse_sha256'),
                _expected_bulk_release_transcendaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_transcendaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_transcendaverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_transcendaverse_sha256'),
                _expected_bulk_release_transcendaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_transcendaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_infinitaverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_infinitaverse_sha256'),
                _expected_bulk_release_infinitaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_infinitaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_infinitaverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_infinitaverse_sha256'),
                _expected_bulk_release_infinitaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_infinitaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_eternaverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_eternaverse_sha256'),
                _expected_bulk_release_eternaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_eternaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_eternaverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_eternaverse_sha256'),
                _expected_bulk_release_eternaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_eternaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_timelessverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_timelessverse_sha256'),
                _expected_bulk_release_timelessverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_timelessverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_timelessverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_timelessverse_sha256'),
                _expected_bulk_release_timelessverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_timelessverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_aeonverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_aeonverse_sha256'),
                _expected_bulk_release_aeonverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_aeonverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_aeonverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_aeonverse_sha256'),
                _expected_bulk_release_aeonverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_aeonverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_epochverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_epochverse_sha256'),
                _expected_bulk_release_epochverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_epochverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_epochverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_epochverse_sha256'),
                _expected_bulk_release_epochverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_epochverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_eraverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_eraverse_sha256'),
                _expected_bulk_release_eraverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_eraverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_eraverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_eraverse_sha256'),
                _expected_bulk_release_eraverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_eraverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_metaverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_metaverse_sha256'),
                _expected_bulk_release_metaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_metaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_metaverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_metaverse_sha256'),
                _expected_bulk_release_metaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_metaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_paraverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_paraverse_sha256'),
                _expected_bulk_release_paraverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_paraverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_paraverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_paraverse_sha256'),
                _expected_bulk_release_paraverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_paraverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_polyverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_polyverse_sha256'),
                _expected_bulk_release_polyverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_polyverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_polyverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_polyverse_sha256'),
                _expected_bulk_release_polyverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_polyverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_panverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_panverse_sha256'),
                _expected_bulk_release_panverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_panverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_holoverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_holoverse_sha256'),
                _expected_bulk_release_holoverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_holoverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_holoverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_holoverse_sha256'),
                _expected_bulk_release_holoverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_holoverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_neoverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_neoverse_sha256'),
                _expected_bulk_release_neoverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_neoverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_neoverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_neoverse_sha256'),
                _expected_bulk_release_neoverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_neoverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_novaverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_novaverse_sha256'),
                _expected_bulk_release_novaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_novaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_novaverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_novaverse_sha256'),
                _expected_bulk_release_novaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_novaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_supernovaverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_supernovaverse_sha256'),
                _expected_bulk_release_supernovaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_supernovaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_supernovaverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_supernovaverse_sha256'),
                _expected_bulk_release_supernovaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_supernovaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_hypernovaverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_hypernovaverse_sha256'),
                _expected_bulk_release_hypernovaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_hypernovaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_hypernovaverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_hypernovaverse_sha256'),
                _expected_bulk_release_hypernovaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_hypernovaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_ultranovaverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_ultranovaverse_sha256'),
                _expected_bulk_release_ultranovaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_ultranovaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_ultranovaverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_ultranovaverse_sha256'),
                _expected_bulk_release_ultranovaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_ultranovaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_omeganovaverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_omeganovaverse_sha256'),
                _expected_bulk_release_omeganovaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_omeganovaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_omeganovaverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_omeganovaverse_sha256'),
                _expected_bulk_release_omeganovaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_omeganovaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_alphanovaverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_alphanovaverse_sha256'),
                _expected_bulk_release_alphanovaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_alphanovaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_alphanovaverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_alphanovaverse_sha256'),
                _expected_bulk_release_alphanovaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_alphanovaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_betanovaverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_betanovaverse_sha256'),
                _expected_bulk_release_betanovaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_betanovaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_betanovaverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_betanovaverse_sha256'),
                _expected_bulk_release_betanovaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_betanovaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_gammanovaverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_gammanovaverse_sha256'),
                _expected_bulk_release_gammanovaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_gammanovaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_gammanovaverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_gammanovaverse_sha256'),
                _expected_bulk_release_gammanovaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_gammanovaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_deltanovaverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_deltanovaverse_sha256'),
                _expected_bulk_release_deltanovaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_deltanovaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_deltanovaverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_deltanovaverse_sha256'),
                _expected_bulk_release_deltanovaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_deltanovaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_epsilonnovaverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_epsilonnovaverse_sha256'),
                _expected_bulk_release_epsilonnovaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_epsilonnovaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_epsilonnovaverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_epsilonnovaverse_sha256'),
                _expected_bulk_release_epsilonnovaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_epsilonnovaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_zetanovaverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_zetanovaverse_sha256'),
                _expected_bulk_release_zetanovaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_zetanovaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_zetanovaverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_zetanovaverse_sha256'),
                _expected_bulk_release_zetanovaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_zetanovaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_etanovaverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_etanovaverse_sha256'),
                _expected_bulk_release_etanovaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_etanovaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_etanovaverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_etanovaverse_sha256'),
                _expected_bulk_release_etanovaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_etanovaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_thetanovaverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_thetanovaverse_sha256'),
                _expected_bulk_release_thetanovaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_thetanovaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_thetanovaverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_thetanovaverse_sha256'),
                _expected_bulk_release_thetanovaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_thetanovaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_iotanovaverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_iotanovaverse_sha256'),
                _expected_bulk_release_iotanovaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_iotanovaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_iotanovaverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_iotanovaverse_sha256'),
                _expected_bulk_release_iotanovaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_iotanovaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_kappanovaverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_kappanovaverse_sha256'),
                _expected_bulk_release_kappanovaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_kappanovaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_kappanovaverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_kappanovaverse_sha256'),
                _expected_bulk_release_kappanovaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_kappanovaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_lambdanovaverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_lambdanovaverse_sha256'),
                _expected_bulk_release_lambdanovaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_lambdanovaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_lambdanovaverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_lambdanovaverse_sha256'),
                _expected_bulk_release_lambdanovaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_lambdanovaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_munovaverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_munovaverse_sha256'),
                _expected_bulk_release_munovaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_munovaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_munovaverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_munovaverse_sha256'),
                _expected_bulk_release_munovaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_munovaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_nunovaverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_nunovaverse_sha256'),
                _expected_bulk_release_nunovaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_nunovaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_nunovaverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_nunovaverse_sha256'),
                _expected_bulk_release_nunovaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_nunovaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_xinovaverse_hash_for_go_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    sys.executable,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_xinovaverse_sha256'),
                _expected_bulk_release_xinovaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_xinovaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_xinovaverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_xinovaverse_sha256'),
                _expected_bulk_release_xinovaverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_xinovaverse_sha256') or '')), 64)

    def test_script_decision_only_emits_bulk_strategy_release_panverse_hash_for_hold_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            bulk_view = decision.get('bulk_strategy_view', {})
            self.assertEqual(
                bulk_view.get('release_panverse_sha256'),
                _expected_bulk_release_panverse_sha256(bulk_view),
            )
            self.assertEqual(len(str(bulk_view.get('release_panverse_sha256') or '')), 64)

    def test_script_decision_only_holds_when_release_gate_pack_evidence_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            doc_sync_path = tmp_path / 'e13-doc-sync-check-report.json'
            quality_path = tmp_path / 'e11-quality-regression-report.json'
            perf_path = tmp_path / 'e11-perf-cost-baseline-report.json'
            postgres_soak_path = tmp_path / 'e13-postgres-soak-benchmark-report.json'
            beta_suite_path = tmp_path / 'e13-release-gate-beta-suite-plan.json'
            ga_suite_path = tmp_path / 'e13-release-gate-ga-suite-plan.json'
            roadmap_suite_path = tmp_path / 'e13-release-gate-roadmap-suite-plan.json'
            release_gate_path = tmp_path / 'missing-release-gate-plan.json'
            standard_path = tmp_path / 'v2-release-switch-standard.md'
            decision_path = tmp_path / 'release-switch-decision.json'

            doc_sync_path.write_text(
                json.dumps(
                    {
                        'status': 'pass',
                        'failed_count': 0,
                        'checks': [
                            {'name': 'release_switch_standard_completeness', 'status': 'pass'},
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + '\n',
                encoding='utf-8',
            )
            quality_path.write_text(
                json.dumps({'regressed_count': 0}, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            perf_path.write_text(
                json.dumps({'regressed_count': 0}, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            postgres_soak_path.write_text(
                json.dumps(
                    {
                        'run_postgres': True,
                        'runs': {
                            'dual_write': {
                                'summary': {'count': 4},
                            }
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + '\n',
                encoding='utf-8',
            )
            beta_suite_path.write_text(
                json.dumps(
                    _plan_payload(
                        [
                            'ci',
                            'container_smoke',
                            'doc_sync',
                            'quality_regression',
                            'perf_cost_baseline',
                        ]
                    ),
                    ensure_ascii=False,
                    indent=2,
                )
                + '\n',
                encoding='utf-8',
            )
            ga_suite_path.write_text(
                json.dumps(
                    _plan_payload(
                        [
                            'postgres_soak',
                            'postgres_ga',
                            'worker_ga',
                            'review_queue_ga',
                            'provider_ga',
                            'calibration_ga',
                        ]
                    ),
                    ensure_ascii=False,
                    indent=2,
                )
                + '\n',
                encoding='utf-8',
            )
            roadmap_suite_path.write_text(
                json.dumps(
                    _plan_payload(['roadmap_extension']),
                    ensure_ascii=False,
                    indent=2,
                )
                + '\n',
                encoding='utf-8',
            )
            standard_path.write_text(
                '\n'.join(
                    [
                        '# V2 Release Switch Standard',
                        '- graph_is_source_of_truth',
                        '- review_queue_operational',
                        '- publication_view_count>=2',
                        '- postgres_repository_stable',
                        '- regression_beats_v1',
                    ]
                )
                + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(doc_sync_path),
                    '--quality-report',
                    str(quality_path),
                    '--perf-report',
                    str(perf_path),
                    '--postgres-soak-benchmark-report',
                    str(postgres_soak_path),
                    '--beta-suite-output',
                    str(beta_suite_path),
                    '--ga-suite-output',
                    str(ga_suite_path),
                    '--roadmap-suite-output',
                    str(roadmap_suite_path),
                    '--release-gate-output',
                    str(release_gate_path),
                    '--release-standard-doc',
                    str(standard_path),
                    '--decision-output',
                    str(decision_path),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(decision_path.read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_stage_pack_complete'))
            missing_paths = {item.get('path') for item in decision.get('missing_or_invalid_evidence', [])}
            self.assertIn(str(release_gate_path.resolve()), missing_paths)

    def test_script_decision_only_holds_when_release_gate_pack_stage_commands_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            doc_sync_path = tmp_path / 'e13-doc-sync-check-report.json'
            quality_path = tmp_path / 'e11-quality-regression-report.json'
            perf_path = tmp_path / 'e11-perf-cost-baseline-report.json'
            postgres_soak_path = tmp_path / 'e13-postgres-soak-benchmark-report.json'
            beta_suite_path = tmp_path / 'e13-release-gate-beta-suite-plan.json'
            ga_suite_path = tmp_path / 'e13-release-gate-ga-suite-plan.json'
            roadmap_suite_path = tmp_path / 'e13-release-gate-roadmap-suite-plan.json'
            release_gate_path = tmp_path / 'e13-release-gate-validation-plan.json'
            standard_path = tmp_path / 'v2-release-switch-standard.md'
            decision_path = tmp_path / 'release-switch-decision.json'

            doc_sync_path.write_text(
                json.dumps(
                    {
                        'status': 'pass',
                        'failed_count': 0,
                        'checks': [
                            {'name': 'release_switch_standard_completeness', 'status': 'pass'},
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + '\n',
                encoding='utf-8',
            )
            quality_path.write_text(
                json.dumps({'regressed_count': 0}, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            perf_path.write_text(
                json.dumps({'regressed_count': 0}, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            postgres_soak_path.write_text(
                json.dumps(
                    {
                        'run_postgres': True,
                        'runs': {
                            'dual_write': {
                                'summary': {'count': 3},
                            }
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + '\n',
                encoding='utf-8',
            )
            beta_suite_path.write_text(
                json.dumps(
                    _plan_payload(
                        [
                            'ci',
                            'container_smoke',
                            'doc_sync',
                            'quality_regression',
                            'perf_cost_baseline',
                        ]
                    ),
                    ensure_ascii=False,
                    indent=2,
                )
                + '\n',
                encoding='utf-8',
            )
            ga_suite_path.write_text(
                json.dumps(
                    _plan_payload(
                        [
                            'postgres_soak',
                            'postgres_ga',
                            'worker_ga',
                            'review_queue_ga',
                            'provider_ga',
                            'calibration_ga',
                        ]
                    ),
                    ensure_ascii=False,
                    indent=2,
                )
                + '\n',
                encoding='utf-8',
            )
            roadmap_suite_path.write_text(
                json.dumps(
                    _plan_payload(['roadmap_extension']),
                    ensure_ascii=False,
                    indent=2,
                )
                + '\n',
                encoding='utf-8',
            )
            release_gate_path.write_text(
                json.dumps(
                    _plan_payload(
                        ['beta_gate', 'ga_gate', 'roadmap_gate'],
                        include_command=False,
                    ),
                    ensure_ascii=False,
                    indent=2,
                )
                + '\n',
                encoding='utf-8',
            )
            standard_path.write_text(
                '\n'.join(
                    [
                        '# V2 Release Switch Standard',
                        '- graph_is_source_of_truth',
                        '- review_queue_operational',
                        '- publication_view_count>=2',
                        '- postgres_repository_stable',
                        '- regression_beats_v1',
                    ]
                )
                + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(doc_sync_path),
                    '--quality-report',
                    str(quality_path),
                    '--perf-report',
                    str(perf_path),
                    '--postgres-soak-benchmark-report',
                    str(postgres_soak_path),
                    '--beta-suite-output',
                    str(beta_suite_path),
                    '--ga-suite-output',
                    str(ga_suite_path),
                    '--roadmap-suite-output',
                    str(roadmap_suite_path),
                    '--release-gate-output',
                    str(release_gate_path),
                    '--release-standard-doc',
                    str(standard_path),
                    '--decision-output',
                    str(decision_path),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(decision_path.read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_stage_pack_executable'))
            self.assertFalse(summary.get('release_gate_evidence_pack_complete'))
            missing_paths = {item.get('path') for item in decision.get('missing_or_invalid_evidence', [])}
            self.assertNotIn(str(release_gate_path.resolve()), missing_paths)

    def test_script_decision_only_holds_when_evidence_files_are_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            stale_timestamp = time.time() - (6 * 3600)
            os.utime(bundle['quality_path'], (stale_timestamp, stale_timestamp))

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--max-evidence-age-hours',
                    '1',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('freshness_check_enabled'))
            self.assertFalse(summary.get('evidence_freshness_gate_pass'))
            stale_files = set(summary.get('stale_evidence_files', []))
            self.assertIn(str(bundle['quality_path'].resolve()), stale_files)
            freshness_gate = next(
                (item for item in decision.get('gates', []) if item.get('name') == 'evidence_freshness'),
                None,
            )
            self.assertIsNotNone(freshness_gate)
            self.assertEqual(freshness_gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_evidence_freshness_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            stale_timestamp = time.time() - (6 * 3600)
            os.utime(bundle['quality_path'], (stale_timestamp, stale_timestamp))

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--max-evidence-age-hours',
                    '0',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('freshness_check_enabled'))
            self.assertTrue(summary.get('evidence_freshness_gate_pass'))

    def test_script_decision_only_holds_when_evidence_files_are_future_skewed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            future_timestamp = time.time() + (6 * 3600)
            os.utime(bundle['quality_path'], (future_timestamp, future_timestamp))

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--max-evidence-future-skew-hours',
                    '1',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('future_skew_check_enabled'))
            self.assertFalse(summary.get('evidence_freshness_gate_pass'))
            future_files = set(summary.get('future_evidence_files', []))
            self.assertIn(str(bundle['quality_path'].resolve()), future_files)
            freshness_gate = next(
                (item for item in decision.get('gates', []) if item.get('name') == 'evidence_freshness'),
                None,
            )
            self.assertIsNotNone(freshness_gate)
            self.assertEqual(freshness_gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_future_skew_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            future_timestamp = time.time() + (6 * 3600)
            os.utime(bundle['quality_path'], (future_timestamp, future_timestamp))

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--max-evidence-future-skew-hours',
                    '0',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('future_skew_check_enabled'))
            self.assertTrue(summary.get('evidence_freshness_gate_pass'))

    def test_script_decision_only_holds_when_evidence_cohort_age_spread_is_too_large(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            stale_but_not_expired_timestamp = time.time() - (20 * 3600)
            os.utime(bundle['quality_path'], (stale_but_not_expired_timestamp, stale_but_not_expired_timestamp))

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--max-evidence-age-hours',
                    '24',
                    '--max-evidence-cohort-skew-hours',
                    '1',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('cohort_skew_check_enabled'))
            self.assertFalse(summary.get('evidence_cohort_skew_gate_pass'))
            self.assertIsNotNone(summary.get('evidence_cohort_age_spread_hours'))
            self.assertGreater(float(summary.get('evidence_cohort_age_spread_hours', 0.0)), 1.0)
            violation_files = set(summary.get('cohort_skew_violation_files', []))
            self.assertIn(str(bundle['quality_path'].resolve()), violation_files)
            cohort_gate = next(
                (item for item in decision.get('gates', []) if item.get('name') == 'evidence_cohort_skew'),
                None,
            )
            self.assertIsNotNone(cohort_gate)
            self.assertEqual(cohort_gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_evidence_cohort_skew_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            stale_but_not_expired_timestamp = time.time() - (20 * 3600)
            os.utime(bundle['quality_path'], (stale_but_not_expired_timestamp, stale_but_not_expired_timestamp))

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--max-evidence-age-hours',
                    '24',
                    '--max-evidence-cohort-skew-hours',
                    '0',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('cohort_skew_check_enabled'))
            self.assertTrue(summary.get('evidence_cohort_skew_gate_pass'))

    def test_script_decision_only_holds_when_release_gate_stage_outputs_do_not_match_evidence_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            wrong_beta_output = tmp_path / 'wrong-beta-suite-plan.json'

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                if stage.get('name') != 'beta_gate':
                    continue
                stage['command'] = [
                    'python3',
                    'scripts/run_linux_validation_suite.py',
                    '--python',
                    'python3',
                    '--stages',
                    'ci',
                    'container_smoke',
                    'doc_sync',
                    'quality_regression',
                    'perf_cost_baseline',
                    '--output',
                    str(wrong_beta_output.resolve()),
                ]
                break
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_binding_check_enabled'))
            self.assertFalse(summary.get('release_gate_output_binding_pass'))
            self.assertGreaterEqual(int(summary.get('release_gate_binding_mismatch_count', 0)), 1)
            mismatches = summary.get('release_gate_binding_mismatches', [])
            self.assertTrue(any(item.get('stage') == 'beta_gate' for item in mismatches))
            binding_gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_evidence_binding'
                ),
                None,
            )
            self.assertIsNotNone(binding_gate)
            self.assertEqual(binding_gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_output_binding_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            wrong_beta_output = tmp_path / 'wrong-beta-suite-plan.json'

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                if stage.get('name') != 'beta_gate':
                    continue
                stage['command'] = [
                    'python3',
                    'scripts/run_linux_validation_suite.py',
                    '--python',
                    'python3',
                    '--stages',
                    'ci',
                    'container_smoke',
                    'doc_sync',
                    'quality_regression',
                    'perf_cost_baseline',
                    '--output',
                    str(wrong_beta_output.resolve()),
                ]
                break
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--skip-release-gate-output-binding-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_binding_check_enabled'))
            self.assertTrue(summary.get('release_gate_output_binding_pass'))
            self.assertEqual(int(summary.get('release_gate_binding_mismatch_count', 0)), 0)
            self.assertTrue(summary.get('release_gate_stage_contract_pass'))
            binding_gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_evidence_binding'
                ),
                None,
            )
            self.assertIsNotNone(binding_gate)
            self.assertEqual(binding_gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_contract_mismatches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                if stage.get('name') != 'beta_gate':
                    continue
                stage['command'] = [
                    'python3',
                    'scripts/run_linux_validation_suite.py',
                    '--python',
                    'python3',
                    '--stages',
                    'ci',
                    '--output',
                    str(bundle['beta_suite_path'].resolve()),
                ]
                break
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_stage_contract_check_enabled'))
            self.assertFalse(summary.get('release_gate_stage_contract_pass'))
            self.assertGreaterEqual(int(summary.get('release_gate_stage_contract_mismatch_count', 0)), 1)
            mismatches = summary.get('release_gate_stage_contract_mismatches', [])
            self.assertTrue(any(item.get('check') == '--stages' for item in mismatches))
            stage_contract_gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_stage_contract'
                ),
                None,
            )
            self.assertIsNotNone(stage_contract_gate)
            self.assertEqual(stage_contract_gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_stage_contract_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                if stage.get('name') != 'beta_gate':
                    continue
                stage['command'] = [
                    'python3',
                    'scripts/run_linux_validation_suite.py',
                    '--python',
                    'python3',
                    '--stages',
                    'ci',
                    '--output',
                    str(bundle['beta_suite_path'].resolve()),
                ]
                break
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--skip-release-gate-stage-contract-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_stage_contract_check_enabled'))
            self.assertTrue(summary.get('release_gate_stage_contract_pass'))
            self.assertEqual(int(summary.get('release_gate_stage_contract_mismatch_count', 0)), 0)
            stage_contract_gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_stage_contract'
                ),
                None,
            )
            self.assertIsNotNone(stage_contract_gate)
            self.assertEqual(stage_contract_gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_script_position_is_decoy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                if stage.get('name') != 'beta_gate':
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    break
                stage['command'] = [
                    'python3',
                    'scripts/run_release_gate_validation.py',
                    'scripts/run_linux_validation_suite.py',
                    *command[2:],
                ]
                break
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_stage_contract_pass'))
            self.assertTrue(summary.get('release_gate_script_position_check_enabled'))
            self.assertFalse(summary.get('release_gate_script_position_pass'))
            self.assertGreaterEqual(int(summary.get('release_gate_script_position_mismatch_count', 0)), 1)
            mismatches = summary.get('release_gate_script_position_mismatches', [])
            self.assertTrue(any(item.get('check') == 'script-position' for item in mismatches))
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_script_position'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_script_position_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                if stage.get('name') != 'beta_gate':
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    break
                stage['command'] = [
                    'python3',
                    'scripts/run_release_gate_validation.py',
                    'scripts/run_linux_validation_suite.py',
                    *command[2:],
                ]
                break
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--skip-release-gate-script-position-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_script_position_check_enabled'))
            self.assertTrue(summary.get('release_gate_script_position_pass'))
            self.assertEqual(int(summary.get('release_gate_script_position_mismatch_count', 0)), 0)
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_script_position'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_script_path_is_not_repo_canonical(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            decoy_script = str(
                (tmp_path / 'decoy' / 'scripts' / 'run_linux_validation_suite.py').resolve()
            )
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                if stage.get('name') != 'beta_gate':
                    continue
                command = stage.get('command')
                if not isinstance(command, list) or len(command) < 2:
                    break
                command[1] = decoy_script
                break
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_stage_contract_pass'))
            self.assertTrue(summary.get('release_gate_script_position_pass'))
            self.assertTrue(summary.get('release_gate_script_anchor_check_enabled'))
            self.assertFalse(summary.get('release_gate_script_anchor_pass'))
            self.assertGreaterEqual(int(summary.get('release_gate_script_anchor_mismatch_count', 0)), 1)
            mismatches = summary.get('release_gate_script_anchor_mismatches', [])
            self.assertTrue(
                any(
                    item.get('stage') == 'beta_gate' and item.get('check') == 'script-anchor'
                    for item in mismatches
                )
            )
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_script_anchor'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_script_anchor_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            decoy_script = str(
                (tmp_path / 'decoy' / 'scripts' / 'run_linux_validation_suite.py').resolve()
            )
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                if stage.get('name') != 'beta_gate':
                    continue
                command = stage.get('command')
                if not isinstance(command, list) or len(command) < 2:
                    break
                command[1] = decoy_script
                break
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--skip-release-gate-script-anchor-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_script_anchor_check_enabled'))
            self.assertTrue(summary.get('release_gate_script_anchor_pass'))
            self.assertEqual(int(summary.get('release_gate_script_anchor_mismatch_count', 0)), 0)
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_script_anchor'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_python_binding_mismatches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                if stage.get('name') != 'beta_gate':
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    break
                python_option_index = command.index('--python')
                command[python_option_index + 1] = 'python3.11'
                break
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_stage_contract_pass'))
            self.assertTrue(summary.get('release_gate_script_anchor_pass'))
            self.assertTrue(summary.get('release_gate_python_binding_check_enabled'))
            self.assertFalse(summary.get('release_gate_python_binding_pass'))
            self.assertGreaterEqual(int(summary.get('release_gate_python_binding_mismatch_count', 0)), 1)
            mismatches = summary.get('release_gate_python_binding_mismatches', [])
            self.assertTrue(any(item.get('check') == '--python-value' for item in mismatches))
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_python_binding'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_python_binding_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                if stage.get('name') != 'beta_gate':
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    break
                python_option_index = command.index('--python')
                command[python_option_index + 1] = 'python3.11'
                break
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--skip-release-gate-python-binding-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_python_binding_check_enabled'))
            self.assertTrue(summary.get('release_gate_python_binding_pass'))
            self.assertEqual(int(summary.get('release_gate_python_binding_mismatch_count', 0)), 0)
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_python_binding'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_uses_python_optimization_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list) or not command:
                    continue
                command.insert(1, '-O')
                python_option_index = command.index('--python')
                command[python_option_index + 1] = 'python3 -O'
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    'python3 -O',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_python_binding_pass'))
            self.assertTrue(summary.get('release_gate_python_optimization_check_enabled'))
            self.assertFalse(summary.get('release_gate_python_optimization_pass'))
            self.assertGreaterEqual(int(summary.get('release_gate_python_optimization_mismatch_count', 0)), 1)
            mismatches = summary.get('release_gate_python_optimization_mismatches', [])
            self.assertTrue(any(item.get('option') in ('-O', '-OO', '-O*') for item in mismatches))
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_python_optimization'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_python_optimization_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list) or not command:
                    continue
                command.insert(1, '-O')
                python_option_index = command.index('--python')
                command[python_option_index + 1] = 'python3 -O'
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    'python3 -O',
                    '--skip-release-gate-python-optimization-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_python_optimization_check_enabled'))
            self.assertTrue(summary.get('release_gate_python_optimization_pass'))
            self.assertEqual(int(summary.get('release_gate_python_optimization_mismatch_count', 0)), 0)
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_python_optimization'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_python_option_uses_optimization_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                python_option_index = command.index('--python')
                command[python_option_index + 1] = 'python3 -O'
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--skip-release-gate-python-binding-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_python_binding_check_enabled'))
            self.assertTrue(summary.get('release_gate_python_optimization_pass'))
            self.assertTrue(summary.get('release_gate_python_option_optimization_check_enabled'))
            self.assertFalse(summary.get('release_gate_python_option_optimization_pass'))
            self.assertGreaterEqual(int(summary.get('release_gate_python_option_optimization_mismatch_count', 0)), 1)
            mismatches = summary.get('release_gate_python_option_optimization_mismatches', [])
            self.assertTrue(any(item.get('option') in ('-O', '-OO', '-O*') for item in mismatches))
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_python_option_optimization'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_python_option_optimization_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                python_option_index = command.index('--python')
                command[python_option_index + 1] = 'python3 -O'
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--skip-release-gate-python-binding-check',
                    '--skip-release-gate-python-option-optimization-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_python_binding_check_enabled'))
            self.assertFalse(summary.get('release_gate_python_option_optimization_check_enabled'))
            self.assertTrue(summary.get('release_gate_python_option_optimization_pass'))
            self.assertEqual(int(summary.get('release_gate_python_option_optimization_mismatch_count', 0)), 0)
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_python_option_optimization'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_uses_python_optimize_env_assignment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env PYTHONOPTIMIZE=2 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'PYTHONOPTIMIZE=2', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_python_binding_pass'))
            self.assertTrue(summary.get('release_gate_python_optimize_env_check_enabled'))
            self.assertFalse(summary.get('release_gate_python_optimize_env_pass'))
            self.assertGreaterEqual(int(summary.get('release_gate_python_optimize_env_mismatch_count', 0)), 1)
            mismatches = summary.get('release_gate_python_optimize_env_mismatches', [])
            self.assertTrue(any('PYTHONOPTIMIZE=' in str(item.get('actual')) for item in mismatches))
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_python_optimize_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_python_optimize_env_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env PYTHONOPTIMIZE=2 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'PYTHONOPTIMIZE=2', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--skip-release-gate-python-optimize-env-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_python_optimize_env_check_enabled'))
            self.assertTrue(summary.get('release_gate_python_optimize_env_pass'))
            self.assertEqual(int(summary.get('release_gate_python_optimize_env_mismatch_count', 0)), 0)
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_python_optimize_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_uses_python_path_env_assignment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env PYTHONPATH=/tmp/rogue python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'PYTHONPATH=/tmp/rogue', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_python_binding_pass'))
            self.assertTrue(summary.get('release_gate_python_path_env_check_enabled'))
            self.assertFalse(summary.get('release_gate_python_path_env_pass'))
            self.assertGreaterEqual(int(summary.get('release_gate_python_path_env_mismatch_count', 0)), 1)
            mismatches = summary.get('release_gate_python_path_env_mismatches', [])
            self.assertTrue(any('PYTHONPATH=' in str(item.get('actual')) for item in mismatches))
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_python_path_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_python_path_env_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env PYTHONPATH=/tmp/rogue python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'PYTHONPATH=/tmp/rogue', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--skip-release-gate-python-path-env-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_python_path_env_check_enabled'))
            self.assertTrue(summary.get('release_gate_python_path_env_pass'))
            self.assertEqual(int(summary.get('release_gate_python_path_env_mismatch_count', 0)), 0)
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_python_path_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_uses_python_home_env_assignment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env PYTHONHOME=/tmp/rogue-home python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'PYTHONHOME=/tmp/rogue-home', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_python_binding_pass'))
            self.assertTrue(summary.get('release_gate_python_home_env_check_enabled'))
            self.assertFalse(summary.get('release_gate_python_home_env_pass'))
            self.assertGreaterEqual(int(summary.get('release_gate_python_home_env_mismatch_count', 0)), 1)
            mismatches = summary.get('release_gate_python_home_env_mismatches', [])
            self.assertTrue(any('PYTHONHOME=' in str(item.get('actual')) for item in mismatches))
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_python_home_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_python_home_env_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env PYTHONHOME=/tmp/rogue-home python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'PYTHONHOME=/tmp/rogue-home', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--skip-release-gate-python-home-env-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_python_home_env_check_enabled'))
            self.assertTrue(summary.get('release_gate_python_home_env_pass'))
            self.assertEqual(int(summary.get('release_gate_python_home_env_mismatch_count', 0)), 0)
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_python_home_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_uses_python_user_base_env_assignment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env PYTHONUSERBASE=/tmp/rogue-userbase python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'PYTHONUSERBASE=/tmp/rogue-userbase', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_python_binding_pass'))
            self.assertTrue(summary.get('release_gate_python_user_base_env_check_enabled'))
            self.assertFalse(summary.get('release_gate_python_user_base_env_pass'))
            self.assertGreaterEqual(int(summary.get('release_gate_python_user_base_env_mismatch_count', 0)), 1)
            mismatches = summary.get('release_gate_python_user_base_env_mismatches', [])
            self.assertTrue(any('PYTHONUSERBASE=' in str(item.get('actual')) for item in mismatches))
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_python_user_base_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_python_user_base_env_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env PYTHONUSERBASE=/tmp/rogue-userbase python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'PYTHONUSERBASE=/tmp/rogue-userbase', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--skip-release-gate-python-user-base-env-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_python_user_base_env_check_enabled'))
            self.assertTrue(summary.get('release_gate_python_user_base_env_pass'))
            self.assertEqual(int(summary.get('release_gate_python_user_base_env_mismatch_count', 0)), 0)
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_python_user_base_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_uses_python_breakpoint_env_assignment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env PYTHONBREAKPOINT=evil.hook python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'PYTHONBREAKPOINT=evil.hook', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_python_binding_pass'))
            self.assertTrue(summary.get('release_gate_python_breakpoint_env_check_enabled'))
            self.assertFalse(summary.get('release_gate_python_breakpoint_env_pass'))
            self.assertGreaterEqual(int(summary.get('release_gate_python_breakpoint_env_mismatch_count', 0)), 1)
            mismatches = summary.get('release_gate_python_breakpoint_env_mismatches', [])
            self.assertTrue(any('PYTHONBREAKPOINT=' in str(item.get('actual')) for item in mismatches))
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_python_breakpoint_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_python_breakpoint_env_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env PYTHONBREAKPOINT=evil.hook python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'PYTHONBREAKPOINT=evil.hook', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--skip-release-gate-python-breakpoint-env-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_python_breakpoint_env_check_enabled'))
            self.assertTrue(summary.get('release_gate_python_breakpoint_env_pass'))
            self.assertEqual(int(summary.get('release_gate_python_breakpoint_env_mismatch_count', 0)), 0)
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_python_breakpoint_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_uses_python_startup_env_assignment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env PYTHONSTARTUP=/tmp/evil-startup.py python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'PYTHONSTARTUP=/tmp/evil-startup.py', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_python_binding_pass'))
            self.assertTrue(summary.get('release_gate_python_startup_env_check_enabled'))
            self.assertFalse(summary.get('release_gate_python_startup_env_pass'))
            self.assertGreaterEqual(int(summary.get('release_gate_python_startup_env_mismatch_count', 0)), 1)
            mismatches = summary.get('release_gate_python_startup_env_mismatches', [])
            self.assertTrue(any('PYTHONSTARTUP=' in str(item.get('actual')) for item in mismatches))
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_python_startup_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_python_startup_env_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env PYTHONSTARTUP=/tmp/evil-startup.py python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'PYTHONSTARTUP=/tmp/evil-startup.py', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--skip-release-gate-python-startup-env-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_python_startup_env_check_enabled'))
            self.assertTrue(summary.get('release_gate_python_startup_env_pass'))
            self.assertEqual(int(summary.get('release_gate_python_startup_env_mismatch_count', 0)), 0)
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_python_startup_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_uses_python_inspect_env_assignment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env PYTHONINSPECT=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'PYTHONINSPECT=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_python_binding_pass'))
            self.assertTrue(summary.get('release_gate_python_inspect_env_check_enabled'))
            self.assertFalse(summary.get('release_gate_python_inspect_env_pass'))
            self.assertGreaterEqual(int(summary.get('release_gate_python_inspect_env_mismatch_count', 0)), 1)
            mismatches = summary.get('release_gate_python_inspect_env_mismatches', [])
            self.assertTrue(any('PYTHONINSPECT=' in str(item.get('actual')) for item in mismatches))
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_python_inspect_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_python_inspect_env_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env PYTHONINSPECT=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'PYTHONINSPECT=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--skip-release-gate-python-inspect-env-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_python_inspect_env_check_enabled'))
            self.assertTrue(summary.get('release_gate_python_inspect_env_pass'))
            self.assertEqual(int(summary.get('release_gate_python_inspect_env_mismatch_count', 0)), 0)
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_python_inspect_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_uses_python_warnings_env_assignment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env PYTHONWARNINGS=ignore python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'PYTHONWARNINGS=ignore', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_python_binding_pass'))
            self.assertTrue(summary.get('release_gate_python_warnings_env_check_enabled'))
            self.assertFalse(summary.get('release_gate_python_warnings_env_pass'))
            self.assertGreaterEqual(int(summary.get('release_gate_python_warnings_env_mismatch_count', 0)), 1)
            mismatches = summary.get('release_gate_python_warnings_env_mismatches', [])
            self.assertTrue(any('PYTHONWARNINGS=' in str(item.get('actual')) for item in mismatches))
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_python_warnings_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_python_warnings_env_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env PYTHONWARNINGS=ignore python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'PYTHONWARNINGS=ignore', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--skip-release-gate-python-warnings-env-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_python_warnings_env_check_enabled'))
            self.assertTrue(summary.get('release_gate_python_warnings_env_pass'))
            self.assertEqual(int(summary.get('release_gate_python_warnings_env_mismatch_count', 0)), 0)
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_python_warnings_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_uses_unknown_python_env_assignment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env PYTHONUNBUFFERED=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'PYTHONUNBUFFERED=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_python_binding_pass'))
            self.assertTrue(summary.get('release_gate_python_warnings_env_pass'))
            self.assertTrue(summary.get('release_gate_python_env_wildcard_check_enabled'))
            self.assertFalse(summary.get('release_gate_python_env_wildcard_pass'))
            self.assertGreaterEqual(int(summary.get('release_gate_python_env_wildcard_mismatch_count', 0)), 1)
            mismatches = summary.get('release_gate_python_env_wildcard_mismatches', [])
            self.assertTrue(any('PYTHONUNBUFFERED=' in str(item.get('actual')) for item in mismatches))
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_python_env_wildcard'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_python_env_wildcard_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env PYTHONUNBUFFERED=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'PYTHONUNBUFFERED=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--skip-release-gate-python-env-wildcard-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_python_env_wildcard_check_enabled'))
            self.assertTrue(summary.get('release_gate_python_env_wildcard_pass'))
            self.assertEqual(int(summary.get('release_gate_python_env_wildcard_mismatch_count', 0)), 0)
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_python_env_wildcard'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_uses_path_env_assignment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env PATH=/tmp/rogue python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'PATH=/tmp/rogue', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_python_binding_pass'))
            self.assertTrue(summary.get('release_gate_python_env_wildcard_pass'))
            self.assertTrue(summary.get('release_gate_path_env_check_enabled'))
            self.assertFalse(summary.get('release_gate_path_env_pass'))
            self.assertGreaterEqual(int(summary.get('release_gate_path_env_mismatch_count', 0)), 1)
            mismatches = summary.get('release_gate_path_env_mismatches', [])
            self.assertTrue(any('PATH=' in str(item.get('actual')) for item in mismatches))
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_path_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_path_env_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env PATH=/tmp/rogue python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'PATH=/tmp/rogue', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--skip-release-gate-path-env-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_path_env_check_enabled'))
            self.assertTrue(summary.get('release_gate_path_env_pass'))
            self.assertEqual(int(summary.get('release_gate_path_env_mismatch_count', 0)), 0)
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_path_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_uses_ld_preload_env_assignment(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env LD_PRELOAD=/tmp/evil.so python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'LD_PRELOAD=/tmp/evil.so', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_python_binding_pass'))
            self.assertTrue(summary.get('release_gate_path_env_pass'))
            self.assertTrue(summary.get('release_gate_ld_preload_env_check_enabled'))
            self.assertFalse(summary.get('release_gate_ld_preload_env_pass'))
            self.assertGreaterEqual(int(summary.get('release_gate_ld_preload_env_mismatch_count', 0)), 1)
            mismatches = summary.get('release_gate_ld_preload_env_mismatches', [])
            self.assertTrue(any('LD_PRELOAD=' in str(item.get('actual')) for item in mismatches))
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_ld_preload_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_ld_preload_env_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env LD_PRELOAD=/tmp/evil.so python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'LD_PRELOAD=/tmp/evil.so', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--skip-release-gate-ld-preload-env-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_ld_preload_env_check_enabled'))
            self.assertTrue(summary.get('release_gate_ld_preload_env_pass'))
            self.assertEqual(int(summary.get('release_gate_ld_preload_env_mismatch_count', 0)), 0)
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_ld_preload_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_uses_ld_library_path_env_assignment(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env LD_LIBRARY_PATH=/tmp/evil-lib python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'LD_LIBRARY_PATH=/tmp/evil-lib', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_python_binding_pass'))
            self.assertTrue(summary.get('release_gate_ld_preload_env_pass'))
            self.assertTrue(summary.get('release_gate_ld_library_path_env_check_enabled'))
            self.assertFalse(summary.get('release_gate_ld_library_path_env_pass'))
            self.assertGreaterEqual(
                int(summary.get('release_gate_ld_library_path_env_mismatch_count', 0)),
                1,
            )
            mismatches = summary.get('release_gate_ld_library_path_env_mismatches', [])
            self.assertTrue(
                any('LD_LIBRARY_PATH=' in str(item.get('actual')) for item in mismatches)
            )
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_ld_library_path_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_ld_library_path_env_gate(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env LD_LIBRARY_PATH=/tmp/evil-lib python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'LD_LIBRARY_PATH=/tmp/evil-lib', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--skip-release-gate-ld-library-path-env-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_ld_library_path_env_check_enabled'))
            self.assertTrue(summary.get('release_gate_ld_library_path_env_pass'))
            self.assertEqual(
                int(summary.get('release_gate_ld_library_path_env_mismatch_count', 0)),
                0,
            )
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_ld_library_path_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_uses_ld_audit_env_assignment(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env LD_AUDIT=/tmp/evil.audit.so python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'LD_AUDIT=/tmp/evil.audit.so', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_ld_library_path_env_pass'))
            self.assertTrue(summary.get('release_gate_ld_audit_env_check_enabled'))
            self.assertFalse(summary.get('release_gate_ld_audit_env_pass'))
            self.assertGreaterEqual(int(summary.get('release_gate_ld_audit_env_mismatch_count', 0)), 1)
            mismatches = summary.get('release_gate_ld_audit_env_mismatches', [])
            self.assertTrue(any('LD_AUDIT=' in str(item.get('actual')) for item in mismatches))
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_ld_audit_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_ld_audit_env_gate(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env LD_AUDIT=/tmp/evil.audit.so python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'LD_AUDIT=/tmp/evil.audit.so', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--skip-release-gate-ld-audit-env-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_ld_audit_env_check_enabled'))
            self.assertTrue(summary.get('release_gate_ld_audit_env_pass'))
            self.assertEqual(int(summary.get('release_gate_ld_audit_env_mismatch_count', 0)), 0)
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_ld_audit_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_uses_unknown_ld_env_assignment(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env LD_DEBUG=files python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'LD_DEBUG=files', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_ld_audit_env_pass'))
            self.assertTrue(summary.get('release_gate_ld_env_wildcard_check_enabled'))
            self.assertFalse(summary.get('release_gate_ld_env_wildcard_pass'))
            self.assertGreaterEqual(int(summary.get('release_gate_ld_env_wildcard_mismatch_count', 0)), 1)
            mismatches = summary.get('release_gate_ld_env_wildcard_mismatches', [])
            self.assertTrue(any('LD_DEBUG=' in str(item.get('actual')) for item in mismatches))
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_ld_env_wildcard'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_ld_env_wildcard_gate(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env LD_DEBUG=files python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'LD_DEBUG=files', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--skip-release-gate-ld-env-wildcard-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_ld_env_wildcard_check_enabled'))
            self.assertTrue(summary.get('release_gate_ld_env_wildcard_pass'))
            self.assertEqual(int(summary.get('release_gate_ld_env_wildcard_mismatch_count', 0)), 0)
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_ld_env_wildcard'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_uses_glibc_tunables_env_assignment(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env GLIBC_TUNABLES=glibc.malloc.check=3 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'GLIBC_TUNABLES=glibc.malloc.check=3', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_ld_env_wildcard_pass'))
            self.assertTrue(summary.get('release_gate_glibc_tunables_env_check_enabled'))
            self.assertFalse(summary.get('release_gate_glibc_tunables_env_pass'))
            self.assertGreaterEqual(
                int(summary.get('release_gate_glibc_tunables_env_mismatch_count', 0)),
                1,
            )
            mismatches = summary.get('release_gate_glibc_tunables_env_mismatches', [])
            self.assertTrue(
                any('GLIBC_TUNABLES=' in str(item.get('actual')) for item in mismatches)
            )
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_glibc_tunables_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_glibc_tunables_env_gate(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env GLIBC_TUNABLES=glibc.malloc.check=3 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'GLIBC_TUNABLES=glibc.malloc.check=3', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--skip-release-gate-glibc-tunables-env-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_glibc_tunables_env_check_enabled'))
            self.assertTrue(summary.get('release_gate_glibc_tunables_env_pass'))
            self.assertEqual(int(summary.get('release_gate_glibc_tunables_env_mismatch_count', 0)), 0)
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_glibc_tunables_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_uses_unknown_glibc_env_assignment(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env GLIBC_MEMUSAGE=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'GLIBC_MEMUSAGE=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_glibc_tunables_env_pass'))
            self.assertTrue(summary.get('release_gate_glibc_env_wildcard_check_enabled'))
            self.assertFalse(summary.get('release_gate_glibc_env_wildcard_pass'))
            self.assertGreaterEqual(
                int(summary.get('release_gate_glibc_env_wildcard_mismatch_count', 0)),
                1,
            )
            mismatches = summary.get('release_gate_glibc_env_wildcard_mismatches', [])
            self.assertTrue(
                any('GLIBC_MEMUSAGE=' in str(item.get('actual')) for item in mismatches)
            )
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_glibc_env_wildcard'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_glibc_env_wildcard_gate(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env GLIBC_MEMUSAGE=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'GLIBC_MEMUSAGE=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--skip-release-gate-glibc-env-wildcard-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_glibc_env_wildcard_check_enabled'))
            self.assertTrue(summary.get('release_gate_glibc_env_wildcard_pass'))
            self.assertEqual(int(summary.get('release_gate_glibc_env_wildcard_mismatch_count', 0)), 0)
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_glibc_env_wildcard'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_uses_unknown_malloc_env_assignment(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_SHADOW_POLICY=strict python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_SHADOW_POLICY=strict', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_glibc_env_wildcard_pass'))
            self.assertTrue(summary.get('release_gate_malloc_check_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_trace_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_perturb_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_env_wildcard_check_enabled'))
            self.assertFalse(summary.get('release_gate_malloc_env_wildcard_pass'))
            self.assertGreaterEqual(
                int(summary.get('release_gate_malloc_env_wildcard_mismatch_count', 0)),
                1,
            )
            mismatches = summary.get('release_gate_malloc_env_wildcard_mismatches', [])
            self.assertTrue(
                any('MALLOC_SHADOW_POLICY=' in str(item.get('actual')) for item in mismatches)
            )
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_malloc_env_wildcard'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_malloc_env_wildcard_gate(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_SHADOW_POLICY=strict python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_SHADOW_POLICY=strict', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--skip-release-gate-malloc-env-wildcard-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_malloc_env_wildcard_check_enabled'))
            self.assertTrue(summary.get('release_gate_malloc_env_wildcard_pass'))
            self.assertEqual(int(summary.get('release_gate_malloc_env_wildcard_mismatch_count', 0)), 0)
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_malloc_env_wildcard'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_uses_malloc_trace_env_assignment(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_TRACE=/tmp/mtrace.log python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_TRACE=/tmp/mtrace.log', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_malloc_env_wildcard_pass'))
            self.assertTrue(summary.get('release_gate_malloc_check_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_perturb_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_trace_env_check_enabled'))
            self.assertFalse(summary.get('release_gate_malloc_trace_env_pass'))
            self.assertGreaterEqual(
                int(summary.get('release_gate_malloc_trace_env_mismatch_count', 0)),
                1,
            )
            mismatches = summary.get('release_gate_malloc_trace_env_mismatches', [])
            self.assertTrue(
                any('MALLOC_TRACE=' in str(item.get('actual')) for item in mismatches)
            )
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_malloc_trace_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_malloc_trace_env_gate(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_TRACE=/tmp/mtrace.log python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_TRACE=/tmp/mtrace.log', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--skip-release-gate-malloc-trace-env-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_malloc_trace_env_check_enabled'))
            self.assertTrue(summary.get('release_gate_malloc_trace_env_pass'))
            self.assertEqual(int(summary.get('release_gate_malloc_trace_env_mismatch_count', 0)), 0)
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_malloc_trace_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_uses_malloc_check_env_assignment(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_CHECK_=3 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_CHECK_=3', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_malloc_env_wildcard_pass'))
            self.assertTrue(summary.get('release_gate_malloc_trace_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_perturb_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_check_env_check_enabled'))
            self.assertFalse(summary.get('release_gate_malloc_check_env_pass'))
            self.assertGreaterEqual(
                int(summary.get('release_gate_malloc_check_env_mismatch_count', 0)),
                1,
            )
            mismatches = summary.get('release_gate_malloc_check_env_mismatches', [])
            self.assertTrue(
                any('MALLOC_CHECK_=' in str(item.get('actual')) for item in mismatches)
            )
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_malloc_check_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_malloc_check_env_gate(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_CHECK_=3 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_CHECK_=3', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--skip-release-gate-malloc-check-env-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_malloc_check_env_check_enabled'))
            self.assertTrue(summary.get('release_gate_malloc_check_env_pass'))
            self.assertEqual(int(summary.get('release_gate_malloc_check_env_mismatch_count', 0)), 0)
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_malloc_check_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_uses_malloc_perturb_env_assignment(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PERTURB_=153 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PERTURB_=153', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_malloc_env_wildcard_pass'))
            self.assertTrue(summary.get('release_gate_malloc_trace_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_check_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_perturb_env_check_enabled'))
            self.assertFalse(summary.get('release_gate_malloc_perturb_env_pass'))
            self.assertGreaterEqual(
                int(summary.get('release_gate_malloc_perturb_env_mismatch_count', 0)),
                1,
            )
            mismatches = summary.get('release_gate_malloc_perturb_env_mismatches', [])
            self.assertTrue(
                any('MALLOC_PERTURB_=' in str(item.get('actual')) for item in mismatches)
            )
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_malloc_perturb_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_malloc_perturb_env_gate(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PERTURB_=153 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PERTURB_=153', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--skip-release-gate-malloc-perturb-env-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_malloc_perturb_env_check_enabled'))
            self.assertTrue(summary.get('release_gate_malloc_perturb_env_pass'))
            self.assertEqual(int(summary.get('release_gate_malloc_perturb_env_mismatch_count', 0)), 0)
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_malloc_perturb_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_uses_malloc_arena_max_env_assignment(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_ARENA_MAX=8 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_ARENA_MAX=8', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_malloc_env_wildcard_pass'))
            self.assertTrue(summary.get('release_gate_malloc_trace_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_check_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_perturb_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_arena_max_env_check_enabled'))
            self.assertFalse(summary.get('release_gate_malloc_arena_max_env_pass'))
            self.assertGreaterEqual(
                int(summary.get('release_gate_malloc_arena_max_env_mismatch_count', 0)),
                1,
            )
            mismatches = summary.get('release_gate_malloc_arena_max_env_mismatches', [])
            self.assertTrue(
                any('MALLOC_ARENA_MAX=' in str(item.get('actual')) for item in mismatches)
            )
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_malloc_arena_max_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_malloc_arena_max_env_gate(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_ARENA_MAX=8 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_ARENA_MAX=8', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--skip-release-gate-malloc-arena-max-env-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_malloc_arena_max_env_check_enabled'))
            self.assertTrue(summary.get('release_gate_malloc_arena_max_env_pass'))
            self.assertEqual(
                int(summary.get('release_gate_malloc_arena_max_env_mismatch_count', 0)),
                0,
            )
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_malloc_arena_max_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_uses_malloc_mmap_threshold_env_assignment(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_MMAP_THRESHOLD_=16384 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_MMAP_THRESHOLD_=16384', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_malloc_env_wildcard_pass'))
            self.assertTrue(summary.get('release_gate_malloc_trace_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_check_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_perturb_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_arena_max_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_mmap_max_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_mmap_threshold_env_check_enabled'))
            self.assertFalse(summary.get('release_gate_malloc_mmap_threshold_env_pass'))
            self.assertGreaterEqual(
                int(summary.get('release_gate_malloc_mmap_threshold_env_mismatch_count', 0)),
                1,
            )
            mismatches = summary.get('release_gate_malloc_mmap_threshold_env_mismatches', [])
            self.assertTrue(
                any('MALLOC_MMAP_THRESHOLD_=' in str(item.get('actual')) for item in mismatches)
            )
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_malloc_mmap_threshold_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_malloc_mmap_threshold_env_gate(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_MMAP_THRESHOLD_=16384 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_MMAP_THRESHOLD_=16384', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--skip-release-gate-malloc-mmap-threshold-env-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_malloc_mmap_threshold_env_check_enabled'))
            self.assertTrue(summary.get('release_gate_malloc_mmap_threshold_env_pass'))
            self.assertEqual(
                int(summary.get('release_gate_malloc_mmap_threshold_env_mismatch_count', 0)),
                0,
            )
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_malloc_mmap_threshold_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_uses_malloc_mmap_max_env_assignment(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_MMAP_MAX_=256 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_MMAP_MAX_=256', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_malloc_env_wildcard_pass'))
            self.assertTrue(summary.get('release_gate_malloc_trace_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_check_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_perturb_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_arena_max_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_mmap_threshold_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_mmap_max_env_check_enabled'))
            self.assertFalse(summary.get('release_gate_malloc_mmap_max_env_pass'))
            self.assertGreaterEqual(
                int(summary.get('release_gate_malloc_mmap_max_env_mismatch_count', 0)),
                1,
            )
            mismatches = summary.get('release_gate_malloc_mmap_max_env_mismatches', [])
            self.assertTrue(
                any('MALLOC_MMAP_MAX_=' in str(item.get('actual')) for item in mismatches)
            )
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_malloc_mmap_max_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_malloc_mmap_max_env_gate(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_MMAP_MAX_=256 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_MMAP_MAX_=256', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--skip-release-gate-malloc-mmap-max-env-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_malloc_mmap_max_env_check_enabled'))
            self.assertTrue(summary.get('release_gate_malloc_mmap_max_env_pass'))
            self.assertEqual(
                int(summary.get('release_gate_malloc_mmap_max_env_mismatch_count', 0)),
                0,
            )
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_malloc_mmap_max_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_uses_malloc_top_pad_env_assignment(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_TOP_PAD_=131072 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_TOP_PAD_=131072', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_malloc_env_wildcard_pass'))
            self.assertTrue(summary.get('release_gate_malloc_trace_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_check_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_perturb_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_arena_max_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_mmap_threshold_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_mmap_max_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_top_pad_env_check_enabled'))
            self.assertFalse(summary.get('release_gate_malloc_top_pad_env_pass'))
            self.assertGreaterEqual(
                int(summary.get('release_gate_malloc_top_pad_env_mismatch_count', 0)),
                1,
            )
            mismatches = summary.get('release_gate_malloc_top_pad_env_mismatches', [])
            self.assertTrue(
                any('MALLOC_TOP_PAD_=' in str(item.get('actual')) for item in mismatches)
            )
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_malloc_top_pad_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_malloc_top_pad_env_gate(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_TOP_PAD_=131072 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_TOP_PAD_=131072', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--skip-release-gate-malloc-top-pad-env-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_malloc_top_pad_env_check_enabled'))
            self.assertTrue(summary.get('release_gate_malloc_top_pad_env_pass'))
            self.assertEqual(
                int(summary.get('release_gate_malloc_top_pad_env_mismatch_count', 0)),
                0,
            )
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_malloc_top_pad_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_uses_malloc_trim_threshold_env_assignment(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_TRIM_THRESHOLD_=262144 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_TRIM_THRESHOLD_=262144', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_malloc_env_wildcard_pass'))
            self.assertTrue(summary.get('release_gate_malloc_trace_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_check_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_perturb_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_arena_max_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_mmap_threshold_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_mmap_max_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_top_pad_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_trim_threshold_env_check_enabled'))
            self.assertFalse(summary.get('release_gate_malloc_trim_threshold_env_pass'))
            self.assertGreaterEqual(
                int(summary.get('release_gate_malloc_trim_threshold_env_mismatch_count', 0)),
                1,
            )
            mismatches = summary.get('release_gate_malloc_trim_threshold_env_mismatches', [])
            self.assertTrue(
                any('MALLOC_TRIM_THRESHOLD_=' in str(item.get('actual')) for item in mismatches)
            )
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_malloc_trim_threshold_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_malloc_trim_threshold_env_gate(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_TRIM_THRESHOLD_=262144 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_TRIM_THRESHOLD_=262144', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--skip-release-gate-malloc-trim-threshold-env-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_malloc_trim_threshold_env_check_enabled'))
            self.assertTrue(summary.get('release_gate_malloc_trim_threshold_env_pass'))
            self.assertEqual(
                int(summary.get('release_gate_malloc_trim_threshold_env_mismatch_count', 0)),
                0,
            )
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_malloc_trim_threshold_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_uses_malloc_arena_test_env_assignment(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_ARENA_TEST=16 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_ARENA_TEST=16', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_malloc_env_wildcard_pass'))
            self.assertTrue(summary.get('release_gate_malloc_trace_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_check_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_perturb_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_arena_max_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_mmap_threshold_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_mmap_max_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_top_pad_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_trim_threshold_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_arena_test_env_check_enabled'))
            self.assertFalse(summary.get('release_gate_malloc_arena_test_env_pass'))
            self.assertGreaterEqual(
                int(summary.get('release_gate_malloc_arena_test_env_mismatch_count', 0)),
                1,
            )
            mismatches = summary.get('release_gate_malloc_arena_test_env_mismatches', [])
            self.assertTrue(
                any('MALLOC_ARENA_TEST=' in str(item.get('actual')) for item in mismatches)
            )
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_malloc_arena_test_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_malloc_arena_test_env_gate(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_ARENA_TEST=16 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_ARENA_TEST=16', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--skip-release-gate-malloc-arena-test-env-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_malloc_arena_test_env_check_enabled'))
            self.assertTrue(summary.get('release_gate_malloc_arena_test_env_pass'))
            self.assertEqual(
                int(summary.get('release_gate_malloc_arena_test_env_mismatch_count', 0)),
                0,
            )
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_malloc_arena_test_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_uses_malloc_per_thread_env_assignment(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_malloc_env_wildcard_pass'))
            self.assertTrue(summary.get('release_gate_malloc_trace_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_check_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_perturb_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_arena_max_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_mmap_threshold_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_mmap_max_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_top_pad_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_trim_threshold_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_arena_test_env_pass'))
            self.assertTrue(summary.get('release_gate_malloc_per_thread_env_check_enabled'))
            self.assertFalse(summary.get('release_gate_malloc_per_thread_env_pass'))
            self.assertGreaterEqual(
                int(summary.get('release_gate_malloc_per_thread_env_mismatch_count', 0)),
                1,
            )
            mismatches = summary.get('release_gate_malloc_per_thread_env_mismatches', [])
            self.assertTrue(
                any('MALLOC_PER_THREAD=' in str(item.get('actual')) for item in mismatches)
            )
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_malloc_per_thread_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_malloc_per_thread_env_gate(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            malicious_python = 'env MALLOC_PER_THREAD=1 python3'
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                command[:1] = ['env', 'MALLOC_PER_THREAD=1', command[0]]
                python_option_index = command.index('--python')
                command[python_option_index + 1] = malicious_python
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    malicious_python,
                    '--skip-release-gate-malloc-per-thread-env-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_malloc_per_thread_env_check_enabled'))
            self.assertTrue(summary.get('release_gate_malloc_per_thread_env_pass'))
            self.assertEqual(
                int(summary.get('release_gate_malloc_per_thread_env_mismatch_count', 0)),
                0,
            )
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_malloc_per_thread_env'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_python_option_uses_inline_exec_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                python_option_index = command.index('--python')
                command[python_option_index + 1] = 'python3 -m site'
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--skip-release-gate-python-binding-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_python_binding_check_enabled'))
            self.assertTrue(summary.get('release_gate_python_option_inline_exec_check_enabled'))
            self.assertFalse(summary.get('release_gate_python_option_inline_exec_pass'))
            self.assertGreaterEqual(int(summary.get('release_gate_python_option_inline_exec_mismatch_count', 0)), 1)
            mismatches = summary.get('release_gate_python_option_inline_exec_mismatches', [])
            self.assertTrue(any(item.get('option') in ('-c', '-m', '-') for item in mismatches))
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_python_option_inline_exec'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_python_option_inline_exec_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    continue
                python_option_index = command.index('--python')
                command[python_option_index + 1] = 'python3 -m site'
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--skip-release-gate-python-binding-check',
                    '--skip-release-gate-python-option-inline-exec-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_python_binding_check_enabled'))
            self.assertFalse(summary.get('release_gate_python_option_inline_exec_check_enabled'))
            self.assertTrue(summary.get('release_gate_python_option_inline_exec_pass'))
            self.assertEqual(int(summary.get('release_gate_python_option_inline_exec_mismatch_count', 0)), 0)
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_python_option_inline_exec'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_coverage_floor_is_downgraded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                if stage.get('name') != 'beta_gate':
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    break
                coverage_option_index = command.index('--coverage-fail-under')
                command[coverage_option_index + 1] = '0'
                break
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_coverage_floor_check_enabled'))
            self.assertFalse(summary.get('release_gate_coverage_floor_pass'))
            self.assertGreaterEqual(int(summary.get('release_gate_coverage_floor_mismatch_count', 0)), 1)
            mismatches = summary.get('release_gate_coverage_floor_mismatches', [])
            self.assertTrue(
                any(
                    item.get('check')
                    in ('--coverage-fail-under-floor', '--coverage-fail-under-binding')
                    for item in mismatches
                )
            )
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_coverage_floor'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_coverage_floor_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                if stage.get('name') != 'beta_gate':
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    break
                coverage_option_index = command.index('--coverage-fail-under')
                command[coverage_option_index + 1] = '0'
                break
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--skip-release-gate-coverage-floor-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_coverage_floor_check_enabled'))
            self.assertTrue(summary.get('release_gate_coverage_floor_pass'))
            self.assertEqual(int(summary.get('release_gate_coverage_floor_mismatch_count', 0)), 0)
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_coverage_floor'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_uses_inline_exec_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                if stage.get('name') != 'beta_gate':
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    break
                stage['command'] = [
                    command[0],
                    '-c',
                    'print("decoy-runner")',
                    *command[1:],
                ]
                break
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_stage_contract_pass'))
            self.assertTrue(summary.get('release_gate_script_position_pass'))
            self.assertTrue(summary.get('release_gate_inline_exec_check_enabled'))
            self.assertFalse(summary.get('release_gate_inline_exec_pass'))
            self.assertGreaterEqual(int(summary.get('release_gate_inline_exec_mismatch_count', 0)), 1)
            mismatches = summary.get('release_gate_inline_exec_mismatches', [])
            self.assertTrue(any(item.get('option') == '-c' for item in mismatches))
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_inline_exec'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_inline_exec_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                if stage.get('name') != 'beta_gate':
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    break
                stage['command'] = [
                    command[0],
                    '-c',
                    'print("decoy-runner")',
                    *command[1:],
                ]
                break
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--skip-release-gate-inline-exec-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_inline_exec_check_enabled'))
            self.assertTrue(summary.get('release_gate_inline_exec_pass'))
            self.assertEqual(int(summary.get('release_gate_inline_exec_mismatch_count', 0)), 0)
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_inline_exec'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_options_are_ambiguous(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                if stage.get('name') != 'beta_gate':
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    break
                output_index = command.index('--output')
                command[output_index:output_index] = ['--stages', 'ci']
                break
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_stage_contract_pass'))
            self.assertTrue(summary.get('release_gate_output_binding_pass'))
            self.assertTrue(summary.get('release_gate_option_override_check_enabled'))
            self.assertFalse(summary.get('release_gate_option_override_pass'))
            self.assertGreaterEqual(int(summary.get('release_gate_option_override_mismatch_count', 0)), 1)
            mismatches = summary.get('release_gate_option_override_mismatches', [])
            self.assertTrue(any(item.get('check') == '--stages-occurrence' for item in mismatches))
            option_override_gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_option_override'
                ),
                None,
            )
            self.assertIsNotNone(option_override_gate)
            self.assertEqual(option_override_gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_option_override_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                if stage.get('name') != 'beta_gate':
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    break
                output_index = command.index('--output')
                command[output_index:output_index] = ['--stages', 'ci']
                break
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--skip-release-gate-option-override-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_option_override_check_enabled'))
            self.assertTrue(summary.get('release_gate_option_override_pass'))
            self.assertEqual(int(summary.get('release_gate_option_override_mismatch_count', 0)), 0)
            option_override_gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_option_override'
                ),
                None,
            )
            self.assertIsNotNone(option_override_gate)
            self.assertEqual(option_override_gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_uses_dry_run_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                if stage.get('name') != 'beta_gate':
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    break
                command.append('--dry-run')
                break
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_stage_contract_pass'))
            self.assertTrue(summary.get('release_gate_option_override_pass'))
            self.assertTrue(summary.get('release_gate_dry_run_check_enabled'))
            self.assertFalse(summary.get('release_gate_dry_run_pass'))
            self.assertGreaterEqual(int(summary.get('release_gate_dry_run_mismatch_count', 0)), 1)
            mismatches = summary.get('release_gate_dry_run_mismatches', [])
            self.assertTrue(any(item.get('option') == '--dry-run' for item in mismatches))
            dry_run_gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_dry_run'
                ),
                None,
            )
            self.assertIsNotNone(dry_run_gate)
            self.assertEqual(dry_run_gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_dry_run_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                if stage.get('name') != 'beta_gate':
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    break
                command.append('--dry-run')
                break
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--skip-release-gate-dry-run-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_dry_run_check_enabled'))
            self.assertTrue(summary.get('release_gate_dry_run_pass'))
            self.assertEqual(int(summary.get('release_gate_dry_run_mismatch_count', 0)), 0)
            dry_run_gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_dry_run'
                ),
                None,
            )
            self.assertIsNotNone(dry_run_gate)
            self.assertEqual(dry_run_gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_uses_relaxed_flags(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                if stage.get('name') != 'beta_gate':
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    break
                command.append('--allow-regression')
                break
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_relaxed_flags_check_enabled'))
            self.assertFalse(summary.get('release_gate_relaxed_flags_pass'))
            self.assertGreaterEqual(int(summary.get('release_gate_relaxed_flags_mismatch_count', 0)), 1)
            mismatches = summary.get('release_gate_relaxed_flags_mismatches', [])
            self.assertTrue(any(item.get('option') == '--allow-regression' for item in mismatches))
            relaxed_gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_relaxed_flags'
                ),
                None,
            )
            self.assertIsNotNone(relaxed_gate)
            self.assertEqual(relaxed_gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_relaxed_flags_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                if stage.get('name') != 'beta_gate':
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    break
                command.append('--allow-regression')
                break
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--skip-release-gate-relaxed-flags-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_relaxed_flags_check_enabled'))
            self.assertTrue(summary.get('release_gate_relaxed_flags_pass'))
            self.assertEqual(int(summary.get('release_gate_relaxed_flags_mismatch_count', 0)), 0)
            relaxed_gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_relaxed_flags'
                ),
                None,
            )
            self.assertIsNotNone(relaxed_gate)
            self.assertEqual(relaxed_gate.get('status'), 'pass')

    def test_script_decision_only_hold_is_nonzero_unless_allow_hold(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            decision_path = tmp_path / 'release-switch-decision.json'

            hold_completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(tmp_path / 'missing-doc-sync.json'),
                    '--quality-report',
                    str(tmp_path / 'missing-quality.json'),
                    '--perf-report',
                    str(tmp_path / 'missing-perf.json'),
                    '--postgres-soak-benchmark-report',
                    str(tmp_path / 'missing-postgres.json'),
                    '--ga-suite-output',
                    str(tmp_path / 'missing-ga-suite.json'),
                    '--release-standard-doc',
                    str(tmp_path / 'missing-standard.md'),
                    '--decision-output',
                    str(decision_path),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(hold_completed.returncode, 1, hold_completed.stderr)
            self.assertIn('Release switch decision=HOLD', hold_completed.stdout)

            allow_hold_completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--allow-hold',
                    '--doc-sync-report',
                    str(tmp_path / 'missing-doc-sync.json'),
                    '--quality-report',
                    str(tmp_path / 'missing-quality.json'),
                    '--perf-report',
                    str(tmp_path / 'missing-perf.json'),
                    '--postgres-soak-benchmark-report',
                    str(tmp_path / 'missing-postgres.json'),
                    '--ga-suite-output',
                    str(tmp_path / 'missing-ga-suite.json'),
                    '--release-standard-doc',
                    str(tmp_path / 'missing-standard.md'),
                    '--decision-output',
                    str(decision_path),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(allow_hold_completed.returncode, 0, allow_hold_completed.stderr)
            self.assertIn('Release switch decision=HOLD', allow_hold_completed.stdout)


if __name__ == '__main__':
    unittest.main()
