from __future__ import annotations

import contextvars
import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any

ENV_LOG_LEVEL = 'OMNI_LOG_LEVEL'
ENV_LOG_FORMAT = 'OMNI_LOG_FORMAT'
DEFAULT_LOG_LEVEL = 'INFO'
DEFAULT_LOG_FORMAT = 'json'

_DEFAULT_RECORD_FIELDS = set(logging.LogRecord('', logging.INFO, '', 0, '', (), None).__dict__.keys())
_DEFAULT_RECORD_FIELDS.update({'message', 'asctime'})

_request_id_context: contextvars.ContextVar[str] = contextvars.ContextVar('omni_request_id', default='')
_trace_id_context: contextvars.ContextVar[str] = contextvars.ContextVar('omni_trace_id', default='')


def _normalize_level(raw_level: str) -> int:
    text = str(raw_level or DEFAULT_LOG_LEVEL).strip().upper()
    return int(getattr(logging, text, logging.INFO))


def _coerce_json_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): _coerce_json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_coerce_json_value(item) for item in value]
    return str(value)


def set_request_context(request_id: str, trace_id: str) -> tuple[contextvars.Token[str], contextvars.Token[str]]:
    request_token = _request_id_context.set(str(request_id or '').strip())
    trace_token = _trace_id_context.set(str(trace_id or '').strip())
    return request_token, trace_token


def reset_request_context(*, request_token: contextvars.Token[str], trace_token: contextvars.Token[str]) -> None:
    _request_id_context.reset(request_token)
    _trace_id_context.reset(trace_token)


def get_request_context() -> tuple[str, str]:
    return _request_id_context.get(''), _trace_id_context.get('')


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        request_id, trace_id = get_request_context()
        if not getattr(record, 'request_id', ''):
            record.request_id = request_id
        if not getattr(record, 'trace_id', ''):
            record.trace_id = trace_id
        return True


class StructuredJsonFormatter(logging.Formatter):
    def __init__(self, *, service_name: str) -> None:
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            'timestamp': datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat().replace('+00:00', 'Z'),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'service': str(getattr(record, 'service', self.service_name)),
        }

        for key, value in record.__dict__.items():
            if key in _DEFAULT_RECORD_FIELDS or key.startswith('_'):
                continue
            payload[key] = _coerce_json_value(value)

        if record.exc_info:
            payload['exc_info'] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(
    *,
    service_name: str,
    level: str | None = None,
    log_format: str | None = None,
    stream = None,
    force: bool = False,
) -> None:
    resolved_level = _normalize_level(level or os.getenv(ENV_LOG_LEVEL, DEFAULT_LOG_LEVEL))
    resolved_format = str(log_format or os.getenv(ENV_LOG_FORMAT, DEFAULT_LOG_FORMAT)).strip().lower()
    output_stream = stream if stream is not None else sys.stdout

    signature = (service_name, resolved_level, resolved_format, id(output_stream))
    root_logger = logging.getLogger()
    existing_signature = getattr(root_logger, '_omni_logging_signature', None)
    if not force and existing_signature == signature:
        return

    handler = logging.StreamHandler(output_stream)
    handler.addFilter(RequestContextFilter())
    if resolved_format == 'json':
        handler.setFormatter(StructuredJsonFormatter(service_name=service_name))
    else:
        handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s'))

    root_logger.handlers = [handler]
    root_logger.setLevel(resolved_level)
    root_logger._omni_logging_signature = signature
