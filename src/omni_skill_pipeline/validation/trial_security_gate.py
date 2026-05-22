from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

from omni_skill_pipeline.redaction import is_sensitive_key

FAILURE_CODE_SECRET_LEAK = 'TRIAL_SECRET_LEAK'
FAILURE_CODE_PRIVATE_LOCAL_ABSOLUTE_PATH = 'TRIAL_PRIVATE_LOCAL_ABSOLUTE_PATH'
FAILURE_CODE_DANGEROUS_PRODUCTION_COMMAND = 'TRIAL_DANGEROUS_PRODUCTION_COMMAND'
FAILURE_CODE_UNAPPROVED_SENSITIVE_DATA_CLASS = 'TRIAL_UNAPPROVED_SENSITIVE_DATA_CLASS'

_REDACTED_MARKERS = {'[REDACTED]', '<redacted>', '***'}
_TOKEN_LIKE_SECRET_PATTERN = re.compile(r'(?i)\b(?:sk|rk|pk|ghp|glpat|xoxb|xoxp|pat)-[A-Za-z0-9_\-]{8,}\b')
_BEARER_TOKEN_PATTERN = re.compile(r'(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{6,}\b')
_WINDOWS_ABSOLUTE_PATH_PATTERN = re.compile(r'(?i)\b[A-Z]:\\[^\s"\']+')
_POSIX_ABSOLUTE_PATH_PATTERN = re.compile(r'(?<!\w)/(?:Users|home|root|etc|var|opt|srv|tmp|private|mnt)/[^\s"\']+')
_FILE_URI_PATTERN = re.compile(r'(?i)\bfile://[^\s"\']+')

_DANGEROUS_COMMAND_MARKERS = (
    'rm -rf /',
    'sudo rm -rf',
    'terraform destroy',
    'kubectl delete namespace',
    'kubectl delete pod',
    'drop database',
    'drop table',
    'truncate table',
    'shutdown -h',
    'reboot',
    'mkfs.',
    'dd if=',
)

_SENSITIVITY_KEYS = {
    'sensitivity',
    'sensitivity_level',
    'sensitivity_class',
    'security_class',
    'data_class',
    'data_classification',
    'classification',
    'data_sensitivity',
    'sensitive_class',
}

_BLOCKED_SENSITIVE_CLASSES = {
    'restricted',
    'regulated',
    'payment',
    'payment_data',
    'production_credentials',
    'credentials',
    'secret',
    'secrets',
    'pii',
    'customer_pii',
    'phi',
    'hipaa',
    'pci',
    'legal',
    'medical',
    'financial',
    'customer_confidential',
}


@dataclass(frozen=True, slots=True)
class TrialSecurityIssue:
    code: str
    message: str
    severity: str = 'high'
    context: str = ''

    def to_dict(self) -> dict[str, str]:
        return {
            'code': self.code,
            'message': self.message,
            'severity': self.severity,
            'context': self.context,
        }


@dataclass(frozen=True, slots=True)
class TrialSecurityReport:
    status: str
    issues: list[TrialSecurityIssue] = field(default_factory=list)

    @property
    def failure_codes(self) -> list[str]:
        return [item.code for item in self.issues]

    @property
    def risk_labels(self) -> list[dict[str, str]]:
        labels: list[dict[str, str]] = []
        seen: set[str] = set()
        for issue in self.issues:
            risk_code = _risk_label_for_code(issue.code)
            if risk_code in seen:
                continue
            seen.add(risk_code)
            labels.append(
                {
                    'code': risk_code,
                    'severity': issue.severity,
                    'source': 'trial_security_gate',
                }
            )
        return labels

    def to_dict(self) -> dict[str, Any]:
        return {
            'status': self.status,
            'failure_code_count': len(self.failure_codes),
            'failure_codes': self.failure_codes,
            'issues': [item.to_dict() for item in self.issues],
            'risk_labels': self.risk_labels,
        }


def evaluate_trial_security(
    *,
    skill_markdown: str,
    references: Mapping[str, str] | None = None,
    package_metadata: Mapping[str, Any] | None = None,
    request_payload: Mapping[str, Any] | None = None,
    review_context: Mapping[str, Any] | None = None,
    allowed_sensitivity_levels: set[str] | None = None,
    approved_sensitive_classes: set[str] | None = None,
) -> TrialSecurityReport:
    references_payload = dict(references or {})
    package_payload = dict(package_metadata or {})
    request_context_payload = dict(request_payload or {})
    review_context_payload = dict(review_context or {})
    allowed_sensitivity = {
        _normalize_sensitive_value(item)
        for item in (allowed_sensitivity_levels or {'public', 'internal', 'confidential'})
        if _normalize_sensitive_value(item)
    }
    approved_sensitive = {
        _normalize_sensitive_value(item)
        for item in (approved_sensitive_classes or set())
        if _normalize_sensitive_value(item)
    }

    issues: list[TrialSecurityIssue] = []
    seen: set[tuple[str, str]] = set()

    _collect_secret_leaks(
        issues,
        seen,
        payload=skill_markdown,
        context='skill_markdown',
    )
    _collect_dangerous_command_markers(
        issues,
        seen,
        payload=skill_markdown,
        context='skill_markdown',
    )
    _collect_private_local_absolute_path_leaks(
        issues,
        seen,
        payload=skill_markdown,
        context='skill_markdown',
    )

    for relative_path, content in references_payload.items():
        context = 'reference:%s' % str(relative_path).replace('\\', '/')
        _collect_secret_leaks(
            issues,
            seen,
            payload=str(content),
            context=context,
        )
        _collect_dangerous_command_markers(
            issues,
            seen,
            payload=str(content),
            context=context,
        )
        _collect_private_local_absolute_path_leaks(
            issues,
            seen,
            payload=str(content),
            context=context,
        )

    _collect_secret_leaks(
        issues,
        seen,
        payload=package_payload,
        context='package_metadata',
    )
    _collect_private_local_absolute_path_leaks(
        issues,
        seen,
        payload=package_payload,
        context='package_metadata',
    )
    _collect_secret_leaks(
        issues,
        seen,
        payload=request_context_payload,
        context='request_payload',
    )
    _collect_secret_leaks(
        issues,
        seen,
        payload=review_context_payload,
        context='review_context',
    )
    _collect_unapproved_sensitive_data_classes(
        issues,
        seen,
        payload=request_context_payload,
        context='request_payload',
        allowed_sensitivity_levels=allowed_sensitivity,
        approved_sensitive_classes=approved_sensitive,
    )
    _collect_unapproved_sensitive_data_classes(
        issues,
        seen,
        payload=package_payload,
        context='package_metadata',
        allowed_sensitivity_levels=allowed_sensitivity,
        approved_sensitive_classes=approved_sensitive,
    )
    _collect_unapproved_sensitive_data_classes(
        issues,
        seen,
        payload=review_context_payload,
        context='review_context',
        allowed_sensitivity_levels=allowed_sensitivity,
        approved_sensitive_classes=approved_sensitive,
    )

    status = 'pass' if not issues else 'fail'
    return TrialSecurityReport(status=status, issues=issues)


def collect_trial_security_risk_labels(
    *,
    skill_markdown: str,
    request_payload: Mapping[str, Any] | None = None,
    package_metadata: Mapping[str, Any] | None = None,
    references: Mapping[str, str] | None = None,
    review_context: Mapping[str, Any] | None = None,
    allowed_sensitivity_levels: set[str] | None = None,
    approved_sensitive_classes: set[str] | None = None,
) -> list[dict[str, str]]:
    report = evaluate_trial_security(
        skill_markdown=skill_markdown,
        request_payload=request_payload,
        package_metadata=package_metadata,
        references=references,
        review_context=review_context,
        allowed_sensitivity_levels=allowed_sensitivity_levels,
        approved_sensitive_classes=approved_sensitive_classes,
    )
    return report.risk_labels


def evaluate_trial_security_from_bundle(
    *,
    bundle_path: Path,
    allowed_sensitivity_levels: set[str] | None = None,
    approved_sensitive_classes: set[str] | None = None,
) -> TrialSecurityReport:
    bundle_file = Path(bundle_path).resolve()
    payload = json.loads(bundle_file.read_text(encoding='utf-8'))
    if not isinstance(payload, dict):
        raise ValueError('Bundle payload must be a JSON object: %s' % bundle_file)

    source_markdown = _resolve_bundle_skill_markdown_path(payload=payload, bundle_path=bundle_file)
    references_dir = source_markdown.parent / 'references'
    references = _load_reference_texts(references_dir)
    review_context = {}
    adapter_metadata = payload.get('adapter_metadata')
    if isinstance(adapter_metadata, dict):
        reviewer_packet = adapter_metadata.get('reviewer_packet')
        if isinstance(reviewer_packet, dict):
            review_context = reviewer_packet
    return evaluate_trial_security(
        skill_markdown=source_markdown.read_text(encoding='utf-8'),
        references=references,
        request_payload=payload.get('request_payload') if isinstance(payload.get('request_payload'), dict) else {},
        review_context=review_context,
        allowed_sensitivity_levels=allowed_sensitivity_levels,
        approved_sensitive_classes=approved_sensitive_classes,
    )


def _resolve_bundle_skill_markdown_path(*, payload: dict[str, Any], bundle_path: Path) -> Path:
    bundle_dir = bundle_path.parent
    artifacts = payload.get('artifacts')
    if not isinstance(artifacts, dict):
        artifacts = {}
    for key in ('publication_skill_markdown', 'skill_markdown'):
        value = str(artifacts.get(key, '')).strip()
        if not value:
            continue
        candidate = Path(value)
        if not candidate.is_absolute():
            candidate = (bundle_dir / candidate).resolve()
        if candidate.is_file():
            return candidate
    raise ValueError('Unable to resolve SKILL.md from bundle artifacts: %s' % bundle_path)


def _load_reference_texts(references_dir: Path) -> dict[str, str]:
    if not references_dir.is_dir():
        return {}
    output: dict[str, str] = {}
    for path in sorted(references_dir.rglob('*')):
        if not path.is_file():
            continue
        relative = path.relative_to(references_dir).as_posix()
        output[relative] = path.read_text(encoding='utf-8')
    return output


def _collect_secret_leaks(
    issues: list[TrialSecurityIssue],
    seen: set[tuple[str, str]],
    *,
    payload: Any,
    context: str,
) -> None:
    for key_name, path, value in _iter_string_entries(payload, path=context):
        if key_name and is_sensitive_key(key_name) and value.strip() and value not in _REDACTED_MARKERS:
            _append_issue(
                issues,
                seen,
                TrialSecurityIssue(
                    code=FAILURE_CODE_SECRET_LEAK,
                    message='Unredacted sensitive key/value detected at %s.' % path,
                    severity='high',
                    context=context,
                ),
            )
            continue

        direct = _TOKEN_LIKE_SECRET_PATTERN.search(value)
        if direct is not None:
            _append_issue(
                issues,
                seen,
                TrialSecurityIssue(
                    code=FAILURE_CODE_SECRET_LEAK,
                    message='Token-like secret detected at %s: %s' % (path, direct.group(0)),
                    severity='high',
                    context=context,
                ),
            )
            continue
        bearer = _BEARER_TOKEN_PATTERN.search(value)
        if bearer is not None and '[redacted]' not in value.lower():
            _append_issue(
                issues,
                seen,
                TrialSecurityIssue(
                    code=FAILURE_CODE_SECRET_LEAK,
                    message='Unredacted Bearer token detected at %s.' % path,
                    severity='high',
                    context=context,
                ),
            )


def _collect_private_local_absolute_path_leaks(
    issues: list[TrialSecurityIssue],
    seen: set[tuple[str, str]],
    *,
    payload: Any,
    context: str,
) -> None:
    for _, path, value in _iter_string_entries(payload, path=context):
        local_path = _extract_private_local_path(value)
        if not local_path:
            continue
        _append_issue(
            issues,
            seen,
            TrialSecurityIssue(
                code=FAILURE_CODE_PRIVATE_LOCAL_ABSOLUTE_PATH,
                message='Private local absolute path detected at %s: %s' % (path, local_path),
                severity='high',
                context=context,
            ),
        )


def _collect_dangerous_command_markers(
    issues: list[TrialSecurityIssue],
    seen: set[tuple[str, str]],
    *,
    payload: Any,
    context: str,
) -> None:
    for _, path, value in _iter_string_entries(payload, path=context):
        lowered = value.lower()
        for marker in _DANGEROUS_COMMAND_MARKERS:
            if marker not in lowered:
                continue
            _append_issue(
                issues,
                seen,
                TrialSecurityIssue(
                    code=FAILURE_CODE_DANGEROUS_PRODUCTION_COMMAND,
                    message='Dangerous production command marker detected at %s: %s' % (path, marker),
                    severity='high',
                    context=context,
                ),
            )
            break


def _collect_unapproved_sensitive_data_classes(
    issues: list[TrialSecurityIssue],
    seen: set[tuple[str, str]],
    *,
    payload: Any,
    context: str,
    allowed_sensitivity_levels: set[str],
    approved_sensitive_classes: set[str],
) -> None:
    for key_name, path, value in _iter_string_entries(payload, path=context):
        if not key_name:
            continue
        normalized_key = _normalize_sensitive_value(key_name)
        if normalized_key not in _SENSITIVITY_KEYS:
            continue
        normalized_value = _normalize_sensitive_value(value)
        if not normalized_value:
            continue
        if normalized_value in approved_sensitive_classes:
            continue
        if normalized_value in allowed_sensitivity_levels:
            continue
        if normalized_value in _BLOCKED_SENSITIVE_CLASSES or normalized_key == 'sensitivity':
            _append_issue(
                issues,
                seen,
                TrialSecurityIssue(
                    code=FAILURE_CODE_UNAPPROVED_SENSITIVE_DATA_CLASS,
                    message='Unapproved sensitive data class at %s: %s' % (path, normalized_value),
                    severity='high',
                    context=context,
                ),
            )


def _append_issue(
    issues: list[TrialSecurityIssue],
    seen: set[tuple[str, str]],
    issue: TrialSecurityIssue,
) -> None:
    key = (issue.code, issue.message)
    if key in seen:
        return
    seen.add(key)
    issues.append(issue)


def _iter_string_entries(value: Any, *, path: str, key_name: str = '') -> list[tuple[str, str, str]]:
    entries: list[tuple[str, str, str]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            item_key = str(key)
            item_path = '%s.%s' % (path, item_key)
            entries.extend(_iter_string_entries(item, path=item_path, key_name=item_key))
        return entries
    if isinstance(value, list):
        for index, item in enumerate(value):
            item_path = '%s[%s]' % (path, index)
            entries.extend(_iter_string_entries(item, path=item_path, key_name=key_name))
        return entries
    if isinstance(value, tuple):
        for index, item in enumerate(value):
            item_path = '%s[%s]' % (path, index)
            entries.extend(_iter_string_entries(item, path=item_path, key_name=key_name))
        return entries
    if isinstance(value, str):
        entries.append((key_name, path, value))
    return entries


def _extract_private_local_path(value: str) -> str:
    text = str(value or '').strip()
    if not text:
        return ''

    parsed = urlparse(text)
    scheme = parsed.scheme.lower()
    if scheme in {'http', 'https'}:
        return ''
    if scheme == 'file':
        return text
    if scheme:
        return ''

    windows_match = _WINDOWS_ABSOLUTE_PATH_PATTERN.search(text)
    if windows_match is not None:
        return windows_match.group(0)

    posix_match = _POSIX_ABSOLUTE_PATH_PATTERN.search(text)
    if posix_match is not None:
        return posix_match.group(0)

    file_match = _FILE_URI_PATTERN.search(text)
    if file_match is not None:
        return file_match.group(0)
    return ''


def _normalize_sensitive_value(value: Any) -> str:
    return str(value or '').strip().lower().replace('-', '_').replace(' ', '_')


def _risk_label_for_code(code: str) -> str:
    if code == FAILURE_CODE_SECRET_LEAK:
        return 'trial_security_secret_leak_detected'
    if code == FAILURE_CODE_PRIVATE_LOCAL_ABSOLUTE_PATH:
        return 'trial_security_private_local_absolute_path'
    if code == FAILURE_CODE_DANGEROUS_PRODUCTION_COMMAND:
        return 'trial_security_dangerous_production_command'
    if code == FAILURE_CODE_UNAPPROVED_SENSITIVE_DATA_CLASS:
        return 'trial_security_unapproved_sensitive_data_class'
    return 'trial_security_issue'
