from __future__ import annotations

import re
from typing import Any
from urllib.parse import parse_qsl, quote_plus, urlencode, urlsplit, urlunsplit

REDACTED_VALUE = '[REDACTED]'

_SENSITIVE_ASSIGNMENT_PATTERN = re.compile(
    r'(?i)\b(api[_-]?key|access[_-]?token|refresh[_-]?token|id[_-]?token|bearer[_-]?token|token|secret|credential|password)\b(\s*[:=]\s*)([^\s,;&]+)'
)
_BEARER_PATTERN = re.compile(r'(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{6,}')


def is_sensitive_key(key: Any) -> bool:
    normalized = ''.join(char.lower() if str(char).isalnum() else '_' for char in str(key))
    parts = [item for item in normalized.split('_') if item]
    if not parts:
        return False

    compact = ''.join(parts)
    if compact in {'apikey', 'accesstoken', 'refreshtoken', 'idtoken', 'bearertoken'}:
        return True
    if 'authorization' in parts:
        return True
    if 'secret' in parts or 'password' in parts or 'passwd' in parts:
        return True
    if 'credential' in parts or 'credentials' in parts:
        return True
    if len(parts) >= 2 and parts[-2:] in (
        ['api', 'key'],
        ['access', 'token'],
        ['refresh', 'token'],
        ['id', 'token'],
        ['bearer', 'token'],
    ):
        return True
    if parts[-1] == 'token' and len(parts) <= 2:
        return True
    return False


def redact_sensitive_data(value: Any, *, redacted_value: str = REDACTED_VALUE) -> Any:
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            key_str = str(key)
            if is_sensitive_key(key_str):
                sanitized[key_str] = redacted_value
                continue
            sanitized[key_str] = redact_sensitive_data(item, redacted_value=redacted_value)
        return sanitized
    if isinstance(value, list):
        return [redact_sensitive_data(item, redacted_value=redacted_value) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_sensitive_data(item, redacted_value=redacted_value) for item in value)
    if isinstance(value, str):
        sanitized = _redact_url(value, redacted_value=redacted_value)
        sanitized = _redact_inline_assignments(sanitized, redacted_value=redacted_value)
        sanitized = _BEARER_PATTERN.sub('Bearer %s' % redacted_value, sanitized)
        return sanitized
    return value


def _redact_inline_assignments(value: str, *, redacted_value: str) -> str:
    encoded_redacted_value = quote_plus(redacted_value)

    def _replace(match: re.Match[str]) -> str:
        if match.group(3) == encoded_redacted_value:
            return match.group(0)
        return '%s%s%s' % (match.group(1), match.group(2), redacted_value)

    return _SENSITIVE_ASSIGNMENT_PATTERN.sub(_replace, value)


def _redact_url(value: str, *, redacted_value: str) -> str:
    try:
        parsed = urlsplit(value)
    except ValueError:
        return value

    if not parsed.scheme:
        return value

    query_pairs = parse_qsl(parsed.query, keep_blank_values=True)
    query_changed = False
    sanitized_pairs: list[tuple[str, str]] = []
    for key, item in query_pairs:
        if is_sensitive_key(key):
            sanitized_pairs.append((key, redacted_value))
            query_changed = True
        else:
            sanitized_pairs.append((key, item))

    netloc = parsed.netloc
    netloc_changed = False
    if '@' in netloc:
        user_info, host = netloc.rsplit('@', 1)
        if user_info:
            netloc = '%s@%s' % (redacted_value, host)
            netloc_changed = True

    if not query_changed and not netloc_changed:
        return value

    sanitized_query = urlencode(sanitized_pairs, doseq=True)
    return urlunsplit((parsed.scheme, netloc, parsed.path, sanitized_query, parsed.fragment))
