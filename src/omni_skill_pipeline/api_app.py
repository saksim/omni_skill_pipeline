from __future__ import annotations

import collections
import hmac
import logging
import math
import threading
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

from omni_skill_pipeline.api_schemas import (
    AudioDistillRequestSchema,
    DistillGoalSchema,
    ImageDistillRequestSchema,
    TabularDistillRequestSchema,
    TextDistillRequestSchema,
    VideoDistillRequestSchema,
)
from omni_skill_pipeline.exceptions import (
    MediaProcessingError,
    ProviderExecutionError,
    ProviderUnavailableError,
)
from omni_skill_pipeline.models import (
    AudioDistillRequest,
    DistillGoal,
    ImageDistillRequest,
    TabularDistillRequest,
    TextDistillRequest,
    VideoDistillRequest,
)
from omni_skill_pipeline.config import load_settings
from omni_skill_pipeline.logging_utils import configure_logging, reset_request_context, set_request_context
from omni_skill_pipeline.service import build_service

try:
    from fastapi import Depends, FastAPI, Header, HTTPException, Request
    from fastapi.exceptions import RequestValidationError
    from fastapi.responses import JSONResponse
    from fastapi.responses import PlainTextResponse
except ImportError:  # pragma: no cover
    Depends = None
    FastAPI = None
    Header = None
    HTTPException = Exception
    Request = object
    RequestValidationError = Exception
    JSONResponse = object
    PlainTextResponse = object

logger = logging.getLogger(__name__)

READINESS_REQUIRED_ROUTES = (
    '/healthz',
    '/v1/templates/skill',
    '/v1/distill/text',
    '/v1/distill/audio',
    '/v1/distill/image',
    '/v1/distill/tabular',
    '/v1/distill/video',
)


def _goal_from_schema(payload: DistillGoalSchema) -> DistillGoal:
    return DistillGoal.from_dict(payload.model_dump())


def _extract_api_key_from_authorization_header(value: str | None) -> str:
    header = str(value or '').strip()
    if not header:
        return ''
    if header.lower().startswith('bearer '):
        return header[7:].strip()
    return header


def _extract_provided_api_key(
    x_api_key: str | None,
    authorization: str | None,
) -> str:
    provided = str(x_api_key or '').strip()
    if provided:
        return provided
    return _extract_api_key_from_authorization_header(authorization)


class InMemoryRateLimiter(object):
    def __init__(self, *, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._events: dict[str, collections.deque[float]] = {}
        self._lock = threading.Lock()

    def allow(self, key: str, now: float | None = None) -> tuple[bool, int]:
        now_ts = time.monotonic() if now is None else now
        cutoff = now_ts - float(self.window_seconds)

        with self._lock:
            events = self._events.get(key)
            if events is None:
                events = collections.deque()
                self._events[key] = events

            while events and events[0] <= cutoff:
                events.popleft()

            if len(events) >= self.max_requests:
                retry_after = max(1, int(math.ceil(events[0] + self.window_seconds - now_ts)))
                return False, retry_after

            events.append(now_ts)
            return True, 0


def _error_response(
    *,
    status_code: int,
    error_type: str,
    code: str,
    message: str,
    details: Any = None,
    headers: dict[str, str] | None = None,
):
    return JSONResponse(
        status_code=status_code,
        headers=headers,
        content={
            'error': {
                'type': error_type,
                'code': code,
                'message': message,
                'details': details,
            }
        },
    )


def _build_readiness_checks(app: Any, settings: Any) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    template_path_raw = getattr(settings, 'template_path', None)
    template_ok = False
    template_detail = 'template_path is not configured.'
    if template_path_raw is not None:
        template_path = Path(template_path_raw)
        if not template_path.is_file():
            template_detail = 'template file is missing: %s' % template_path
        else:
            try:
                with template_path.open('rb') as file_handle:
                    file_handle.read(1)
                template_ok = True
                template_detail = 'template file is readable.'
            except Exception as exc:
                template_detail = 'template file is unreadable: %s' % exc
    checks.append(
        {
            'name': 'template_path',
            'ok': template_ok,
            'detail': template_detail,
        }
    )

    draft_dir_raw = getattr(settings, 'draft_dir', None)
    draft_ok = False
    draft_detail = 'draft_dir is not configured.'
    if draft_dir_raw is not None:
        draft_dir = Path(draft_dir_raw)
        if not draft_dir.exists():
            draft_detail = 'draft directory is missing: %s' % draft_dir
        elif not draft_dir.is_dir():
            draft_detail = 'draft path is not a directory: %s' % draft_dir
        else:
            draft_ok = True
            draft_detail = 'draft directory is available.'
    checks.append(
        {
            'name': 'draft_dir',
            'ok': draft_ok,
            'detail': draft_detail,
        }
    )

    route_paths = {getattr(route, 'path', '') for route in getattr(app, 'routes', [])}
    missing_routes = [path for path in READINESS_REQUIRED_ROUTES if path not in route_paths]
    app_ok = not missing_routes
    if app_ok:
        app_detail = 'required routes are assembled.'
    else:
        app_detail = 'missing required routes: %s' % ','.join(missing_routes)
    checks.append(
        {
            'name': 'app_assembly',
            'ok': app_ok,
            'detail': app_detail,
            'missing_routes': missing_routes,
        }
    )
    return checks


def create_app():
    if FastAPI is None:
        raise RuntimeError('FastAPI is not installed. Install with `pip install .[api]`.')

    configure_logging(service_name='api')
    app = FastAPI(title='Omni Skill Pipeline', version='0.2.0')
    settings = load_settings()
    expected_api_key = str(settings.api_key or '').strip()
    rate_limit_requests = int(getattr(settings, 'rate_limit_requests', 0) or 0)
    rate_limit_window_seconds = int(getattr(settings, 'rate_limit_window_seconds', 60) or 60)
    service = build_service()
    limiter = (
        InMemoryRateLimiter(
            max_requests=max(rate_limit_requests, 1),
            window_seconds=max(rate_limit_window_seconds, 1),
        )
        if rate_limit_requests > 0
        else None
    )

    def _require_api_key(
        x_api_key: str | None = Header(default=None, alias='X-API-Key'),
        authorization: str | None = Header(default=None, alias='Authorization'),
    ) -> None:
        if not expected_api_key:
            return

        provided = _extract_provided_api_key(x_api_key, authorization)

        if not provided:
            raise HTTPException(status_code=401, detail='Missing API key.')
        if not hmac.compare_digest(provided, expected_api_key):
            raise HTTPException(status_code=403, detail='Invalid API key.')

    def _rate_limit_identity(
        request: Request,
        *,
        x_api_key: str | None,
        authorization: str | None,
    ) -> str:
        provided = _extract_provided_api_key(x_api_key, authorization)
        if provided:
            return 'key:%s' % provided
        client_host = getattr(getattr(request, 'client', None), 'host', None) or 'unknown'
        return 'ip:%s' % client_host

    def _enforce_rate_limit(
        request: Request,
        x_api_key: str | None = Header(default=None, alias='X-API-Key'),
        authorization: str | None = Header(default=None, alias='Authorization'),
    ) -> None:
        if limiter is None:
            return
        identity = _rate_limit_identity(
            request,
            x_api_key=x_api_key,
            authorization=authorization,
        )
        allowed, retry_after = limiter.allow(identity)
        if allowed:
            return
        raise HTTPException(
            status_code=429,
            detail='Rate limit exceeded.',
            headers={'Retry-After': str(retry_after)},
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_exception_handler(request, exc: RequestValidationError):
        return _error_response(
            status_code=422,
            error_type='validation',
            code='validation_error',
            message='Request validation failed.',
            details=exc.errors(),
        )

    @app.exception_handler(ProviderUnavailableError)
    async def provider_unavailable_exception_handler(request, exc: ProviderUnavailableError):
        return _error_response(
            status_code=503,
            error_type='provider',
            code='provider_unavailable',
            message=str(exc),
        )

    @app.exception_handler(ProviderExecutionError)
    async def provider_execution_exception_handler(request, exc: ProviderExecutionError):
        return _error_response(
            status_code=502,
            error_type='provider',
            code='provider_execution_error',
            message=str(exc),
        )

    @app.exception_handler(MediaProcessingError)
    async def media_processing_exception_handler(request, exc: MediaProcessingError):
        return _error_response(
            status_code=502,
            error_type='provider',
            code='media_processing_error',
            message=str(exc),
        )

    @app.exception_handler(ValueError)
    async def value_error_exception_handler(request, exc: ValueError):
        return _error_response(
            status_code=400,
            error_type='validation',
            code='bad_request',
            message=str(exc),
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc: HTTPException):
        detail = exc.detail if hasattr(exc, 'detail') else str(exc)
        return _error_response(
            status_code=exc.status_code,
            error_type='http',
            code='http_error',
            message=str(detail),
            details=detail,
            headers=dict(getattr(exc, 'headers', None) or {}),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request, exc: Exception):
        logger.exception('Unhandled runtime error during API request.', exc_info=exc)
        return _error_response(
            status_code=500,
            error_type='runtime',
            code='runtime_error',
            message='Internal server error.',
            details=str(exc),
        )

    @app.middleware('http')
    async def request_log_middleware(request: Request, call_next):
        request_id = str(request.headers.get('X-Request-ID', '')).strip() or str(uuid4())
        trace_id = str(request.headers.get('X-Trace-ID', '')).strip() or request_id
        request_token, trace_token = set_request_context(request_id=request_id, trace_id=trace_id)
        started_at = time.perf_counter()
        try:
            try:
                response = await call_next(request)
            except Exception:
                duration_ms = round((time.perf_counter() - started_at) * 1000.0, 3)
                logger.exception(
                    'API request failed.',
                    extra={
                        'event': 'api_request_failed',
                        'method': request.method,
                        'path': request.url.path,
                        'duration_ms': duration_ms,
                        'request_id': request_id,
                        'trace_id': trace_id,
                    },
                )
                raise

            duration_ms = round((time.perf_counter() - started_at) * 1000.0, 3)
            response.headers['X-Request-ID'] = request_id
            response.headers['X-Trace-ID'] = trace_id
            logger.info(
                'API request completed.',
                extra={
                    'event': 'api_request_completed',
                    'method': request.method,
                    'path': request.url.path,
                    'status_code': response.status_code,
                    'duration_ms': duration_ms,
                    'request_id': request_id,
                    'trace_id': trace_id,
                },
            )
            return response
        finally:
            reset_request_context(request_token=request_token, trace_token=trace_token)

    @app.get('/healthz')
    def healthz():
        checks = _build_readiness_checks(app=app, settings=settings)
        failed_checks = [item for item in checks if not item['ok']]
        payload = {
            'status': 'ready' if not failed_checks else 'degraded',
            'checks': checks,
        }
        if failed_checks:
            return JSONResponse(status_code=503, content=payload)
        return payload

    @app.get('/v1/templates/skill', response_class=PlainTextResponse)
    def get_template():
        return settings.template_path.read_text(encoding='utf-8')

    @app.post('/v1/distill/text')
    def distill_text(
        payload: TextDistillRequestSchema,
        _auth: None = Depends(_require_api_key),
        _rate_limit: None = Depends(_enforce_rate_limit),
    ):
        request = TextDistillRequest(
            title=payload.title,
            content=payload.content,
            file_path=payload.file_path,
            goal=_goal_from_schema(payload.goal),
        )
        return service.distill_text(request).to_dict()

    @app.post('/v1/distill/audio')
    def distill_audio(
        payload: AudioDistillRequestSchema,
        _auth: None = Depends(_require_api_key),
        _rate_limit: None = Depends(_enforce_rate_limit),
    ):
        request = AudioDistillRequest(
            title=payload.title,
            audio_path=payload.audio_path,
            transcript=payload.transcript,
            transcript_path=payload.transcript_path,
            language=payload.language,
            prompt=payload.prompt,
            goal=_goal_from_schema(payload.goal),
        )
        return service.distill_audio(request).to_dict()

    @app.post('/v1/distill/image')
    def distill_image(
        payload: ImageDistillRequestSchema,
        _auth: None = Depends(_require_api_key),
        _rate_limit: None = Depends(_enforce_rate_limit),
    ):
        request = ImageDistillRequest(
            image_path=payload.image_path,
            title=payload.title,
            goal=_goal_from_schema(payload.goal),
        )
        return service.distill_image(request).to_dict()

    @app.post('/v1/distill/tabular')
    def distill_tabular(
        payload: TabularDistillRequestSchema,
        _auth: None = Depends(_require_api_key),
        _rate_limit: None = Depends(_enforce_rate_limit),
    ):
        request = TabularDistillRequest(
            file_path=payload.file_path,
            title=payload.title,
            time_column=payload.time_column,
            value_columns=payload.value_columns,
            entity_columns=payload.entity_columns,
            max_series=payload.max_series,
            goal=_goal_from_schema(payload.goal),
        )
        return service.distill_tabular(request).to_dict()

    @app.post('/v1/distill/video')
    def distill_video(
        payload: VideoDistillRequestSchema,
        _auth: None = Depends(_require_api_key),
        _rate_limit: None = Depends(_enforce_rate_limit),
    ):
        request = VideoDistillRequest(
            video_path=payload.video_path,
            title=payload.title,
            transcript=payload.transcript,
            transcript_path=payload.transcript_path,
            language=payload.language,
            prompt=payload.prompt,
            keyframe_interval_seconds=payload.keyframe_interval_seconds,
            max_keyframes=payload.max_keyframes,
            scene_threshold=payload.scene_threshold,
            dedupe_distance=payload.dedupe_distance,
            goal=_goal_from_schema(payload.goal),
        )
        return service.distill_video(request).to_dict()

    return app


app = create_app() if FastAPI is not None else None
