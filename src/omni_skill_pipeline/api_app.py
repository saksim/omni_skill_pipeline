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
    ConsoleViewsRequestSchema,
    CorpusDistillRequestSchema,
    DistillGoalSchema,
    GovernanceDeletionRequestSchema,
    GovernanceRetentionPolicyUpsertRequestSchema,
    GovernanceScopeRequestSchema,
    ImageDistillRequestSchema,
    ReviewQueueClaimRequestSchema,
    ReviewQueueCloseRequestSchema,
    ReviewQueueDecisionRequestSchema,
    TabularDistillRequestSchema,
    TextDistillRequestSchema,
    VideoDistillRequestSchema,
)
from omni_skill_pipeline import __version__
from omni_skill_pipeline.interfaces import ReviewQueueRepository
from omni_skill_pipeline.exceptions import (
    MediaProcessingError,
    ProviderExecutionError,
    ProviderUnavailableError,
)
from omni_skill_pipeline.models import (
    AudioDistillRequest,
    CorpusDistillRequest,
    DistillGoal,
    ImageDistillRequest,
    TabularDistillRequest,
    TextDistillRequest,
    VideoDistillRequest,
)
from omni_skill_pipeline.config import load_settings
from omni_skill_pipeline.logging_utils import configure_logging, reset_request_context, set_request_context
from omni_skill_pipeline.service import build_service
from omni_skill_pipeline.tenant_access import TenantAccessRegistry, TenantIdentity
from omni_skill_pipeline.governance import GovernanceLedger
from omni_skill_pipeline.platform_console import build_platform_console_views

try:
    from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
    from fastapi.exceptions import RequestValidationError
    from fastapi.responses import JSONResponse
    from fastapi.responses import PlainTextResponse
except ImportError:  # pragma: no cover
    Depends = None
    FastAPI = None
    Header = None
    HTTPException = Exception
    Query = None
    Request = object
    RequestValidationError = Exception
    JSONResponse = object
    PlainTextResponse = object

logger = logging.getLogger(__name__)

READINESS_REQUIRED_ROUTES = (
    '/healthz',
    '/v1/templates/skill',
    '/v1/review/queue',
    '/v1/review/queue/claim',
    '/v1/review/queue/{review_task_id}/close',
    '/v1/review/queue/{review_task_id}/decision',
    '/v1/distill/text',
    '/v1/distill/audio',
    '/v1/distill/image',
    '/v1/distill/tabular',
    '/v1/distill/video',
    '/v1/distill/corpus',
    '/v1/governance/report',
    '/v1/governance/retention-policy',
    '/v1/governance/deletion',
    '/v1/console/views',
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
    safe_message = str(message)
    return JSONResponse(
        status_code=status_code,
        headers=headers,
        content={
            'error': {
                'type': error_type,
                'code': code,
                'message': safe_message,
                'details': _json_safe(details),
            }
        },
    )


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, BaseException):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return str(value)


def _build_graph_metadata(payload: dict[str, Any]) -> dict[str, Any] | None:
    skill_graph = payload.get('skill_graph')
    if not isinstance(skill_graph, dict):
        return None

    def _count_list(key: str) -> int:
        value = skill_graph.get(key)
        return len(value) if isinstance(value, list) else 0

    return {
        'graph_id': str(skill_graph.get('graph_id') or ''),
        'name': str(skill_graph.get('name') or ''),
        'version': str(skill_graph.get('version') or ''),
        'review_status': str(skill_graph.get('review_status') or ''),
        'node_counts': {
            'steps': _count_list('steps'),
            'decisions': _count_list('decisions'),
            'verifications': _count_list('verifications'),
            'risks': _count_list('risks'),
            'examples': _count_list('examples'),
            'variables': _count_list('variables'),
            'edges': _count_list('edges'),
        },
    }


def _build_available_publications(payload: dict[str, Any]) -> list[dict[str, Any]]:
    publications = payload.get('publications')
    if not isinstance(publications, list):
        return []

    output: list[dict[str, Any]] = []
    for item in publications:
        if not isinstance(item, dict):
            continue
        publication_type = str(item.get('publication_type') or '').strip()
        if not publication_type:
            continue
        output.append(
            {
                'publication_type': publication_type,
                'path': item.get('path'),
                'publication_id': item.get('publication_id'),
            }
        )
    return output


def _resolve_review_status(payload: dict[str, Any]) -> str | None:
    review_task = payload.get('review_task')
    if isinstance(review_task, dict):
        status = str(review_task.get('status') or '').strip()
        if status:
            return status

    skill = payload.get('skill')
    if isinstance(skill, dict):
        status = str(skill.get('review_status') or '').strip()
        if status:
            return status

    skill_graph = payload.get('skill_graph')
    if isinstance(skill_graph, dict):
        status = str(skill_graph.get('review_status') or '').strip()
        if status:
            return status

    return None


def _resolve_lifecycle_decision(payload: dict[str, Any]) -> dict[str, Any] | None:
    lifecycle_decision = payload.get('lifecycle_decision')
    if isinstance(lifecycle_decision, dict):
        return lifecycle_decision

    adapter_metadata = payload.get('adapter_metadata')
    if not isinstance(adapter_metadata, dict):
        return None
    lifecycle_decision = adapter_metadata.get('lifecycle_decision')
    if isinstance(lifecycle_decision, dict):
        return lifecycle_decision
    return None


def _build_distill_response(bundle: Any) -> Any:
    if not hasattr(bundle, 'to_dict'):
        return bundle

    payload = bundle.to_dict()
    if not isinstance(payload, dict):
        return payload

    if 'skill_markdown' not in payload:
        return payload

    return {
        **payload,
        'graph_metadata': _build_graph_metadata(payload),
        'available_publications': _build_available_publications(payload),
        'review_status': _resolve_review_status(payload),
        'lifecycle_decision': _resolve_lifecycle_decision(payload),
    }


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


def _resolve_governance_ledger_dir(settings: Any) -> Path:
    configured = getattr(settings, 'governance_ledger_dir', None)
    if configured:
        return Path(configured).resolve()
    draft_dir = getattr(settings, 'draft_dir', None)
    if draft_dir:
        return (Path(draft_dir).resolve() / 'governance').resolve()
    repo_root = getattr(settings, 'repo_root', None)
    if repo_root:
        return (Path(repo_root).resolve() / 'skills' / 'drafts' / 'governance').resolve()
    return (Path.cwd() / 'skills' / 'drafts' / 'governance').resolve()


def create_app():
    if FastAPI is None:
        raise RuntimeError('FastAPI is not installed. Install with `pip install .[api]`.')

    configure_logging(service_name='api')
    app = FastAPI(title='Omni Skill Pipeline', version=__version__)
    settings = load_settings()
    expected_api_key = str(settings.api_key or '').strip()
    rate_limit_requests = int(getattr(settings, 'rate_limit_requests', 0) or 0)
    rate_limit_window_seconds = int(getattr(settings, 'rate_limit_window_seconds', 60) or 60)
    service = build_service()
    service_repository = getattr(service, 'repository', None)
    review_queue_repository = (
        service_repository
        if isinstance(service_repository, ReviewQueueRepository)
        else None
    )
    governance_ledger = GovernanceLedger(_resolve_governance_ledger_dir(settings))
    limiter = (
        InMemoryRateLimiter(
            max_requests=max(rate_limit_requests, 1),
            window_seconds=max(rate_limit_window_seconds, 1),
        )
        if rate_limit_requests > 0
        else None
    )
    tenant_registry = TenantAccessRegistry.from_settings(settings)

    def _require_api_key(
        x_api_key: str | None = Header(default=None, alias='X-API-Key'),
        authorization: str | None = Header(default=None, alias='Authorization'),
    ) -> None:
        provided = _extract_provided_api_key(x_api_key, authorization)
        if tenant_registry is not None:
            auth_result = tenant_registry.authenticate(provided)
            if auth_result.identity is None:
                status_code = 401 if auth_result.failure_code == 'missing_api_key' else 403
                raise HTTPException(status_code=status_code, detail=auth_result.message or 'Invalid API key.')
            return

        if not expected_api_key:
            return

        if not provided:
            raise HTTPException(status_code=401, detail='Missing API key.')
        if not hmac.compare_digest(provided, expected_api_key):
            raise HTTPException(status_code=403, detail='Invalid API key.')

    def _resolve_tenant_identity(
        *,
        x_api_key: str | None,
        authorization: str | None,
    ) -> TenantIdentity | None:
        if tenant_registry is None:
            return None
        provided = _extract_provided_api_key(x_api_key, authorization)
        auth_result = tenant_registry.authenticate(provided)
        return auth_result.identity

    def _tenant_scope_dict(scope_payload: Any) -> dict[str, str]:
        if scope_payload is None:
            return {}
        if hasattr(scope_payload, 'model_dump'):
            scope_payload = scope_payload.model_dump()
        if not isinstance(scope_payload, dict):
            return {}
        organization_id = str(scope_payload.get('organization_id', '')).strip()
        project_id = str(scope_payload.get('project_id', '')).strip()
        output: dict[str, str] = {}
        if organization_id:
            output['organization_id'] = organization_id
        if project_id:
            output['project_id'] = project_id
        return output

    def _tenant_scope_from_identity(identity: TenantIdentity | None) -> dict[str, str]:
        if identity is None:
            return {}
        return {
            'organization_id': identity.organization_id,
            'project_id': identity.project_id,
        }

    def _resolve_governance_scope(
        *,
        tenant_identity: TenantIdentity | None,
        requested_organization_id: str,
        requested_project_id: str,
    ) -> dict[str, str]:
        scope = _tenant_scope_from_identity(tenant_identity)
        organization_id = str(requested_organization_id or '').strip()
        project_id = str(requested_project_id or '').strip()
        if organization_id:
            scope['organization_id'] = organization_id
        if project_id:
            scope['project_id'] = project_id
        return {key: value for key, value in scope.items() if str(value).strip()}

    def _enforce_tenant_authorization(
        *,
        request: Request,
        action: str,
        x_api_key: str | None,
        authorization: str | None,
        requested_scope: dict[str, Any] | None,
    ) -> TenantIdentity | None:
        if tenant_registry is None:
            return None
        identity = _resolve_tenant_identity(x_api_key=x_api_key, authorization=authorization)
        if identity is None:
            raise HTTPException(status_code=403, detail='Invalid API key.')
        if not tenant_registry.authorize(identity=identity, action=action):
            raise HTTPException(status_code=403, detail='Tenant role is not authorized for this operation.')
        if not tenant_registry.validate_requested_scope(identity=identity, requested_scope=requested_scope):
            raise HTTPException(status_code=403, detail='Cross-tenant scope is not allowed.')
        allowed, retry_after = tenant_registry.enforce_quota(identity=identity, action=action)
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail='Tenant quota exceeded.',
                headers={'Retry-After': str(retry_after)},
            )
        request.state.tenant_identity = identity
        return identity

    def _inject_tenant_scope_metadata(
        *,
        payload_metadata: dict[str, Any] | None,
        tenant_identity: TenantIdentity | None,
        requested_scope: dict[str, Any] | None,
    ) -> dict[str, Any]:
        metadata = dict(payload_metadata or {})
        if tenant_identity is None:
            return metadata
        tenant_scope = tenant_identity.to_scope_dict()
        requested = _tenant_scope_dict(requested_scope)
        if requested:
            tenant_scope.update({
                'organization_id': requested.get('organization_id', tenant_scope.get('organization_id', '')),
                'project_id': requested.get('project_id', tenant_scope.get('project_id', '')),
            })
        metadata['tenant_scope'] = tenant_scope
        return metadata

    def _record_review_governance_event(
        *,
        event_type: str,
        status: str,
        review_task_id: str,
        tenant_identity: TenantIdentity | None,
        reason_codes: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        scope = _tenant_scope_from_identity(tenant_identity)
        governance_ledger.record_audit_event(
            {
                **scope,
                'event_type': event_type,
                'status': status,
                'review_task_id': str(review_task_id).strip(),
                'actor': tenant_identity.user_id if tenant_identity is not None else '',
                'api_key_id': tenant_identity.api_key_id if tenant_identity is not None else '',
                'metadata': {
                    **(metadata or {}),
                    'reason_codes': list(reason_codes or []),
                },
            }
        )

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

    def _require_review_queue_repository() -> ReviewQueueRepository:
        if review_queue_repository is None:
            raise HTTPException(status_code=503, detail='Review queue repository is not configured.')
        return review_queue_repository

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
            except Exception as exc:
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
                response = _error_response(
                    status_code=500,
                    error_type='runtime',
                    code='runtime_error',
                    message='Internal server error.',
                    details=str(exc),
                )
                response.headers['X-Request-ID'] = request_id
                response.headers['X-Trace-ID'] = trace_id
                return response

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

    @app.get('/v1/review/queue')
    def list_review_queue(
        request: Request,
        queue_status: str | None = Query(default='pending'),
        limit: int = Query(default=100, ge=1, le=1000),
        repository: ReviewQueueRepository = Depends(_require_review_queue_repository),
        x_api_key: str | None = Header(default=None, alias='X-API-Key'),
        authorization: str | None = Header(default=None, alias='Authorization'),
        _auth: None = Depends(_require_api_key),
        _rate_limit: None = Depends(_enforce_rate_limit),
    ):
        tenant_identity = _enforce_tenant_authorization(
            request=request,
            action='review.read',
            x_api_key=x_api_key,
            authorization=authorization,
            requested_scope=None,
        )
        tenant_scope = None if tenant_identity is None else {
            'organization_id': tenant_identity.organization_id,
            'project_id': tenant_identity.project_id,
        }
        return {
            'items': repository.list_review_queue(
                queue_status=queue_status,
                limit=limit,
                tenant_scope=tenant_scope,
            )
        }

    @app.post('/v1/review/queue/claim')
    def claim_review_queue_item(
        request: Request,
        payload: ReviewQueueClaimRequestSchema,
        repository: ReviewQueueRepository = Depends(_require_review_queue_repository),
        x_api_key: str | None = Header(default=None, alias='X-API-Key'),
        authorization: str | None = Header(default=None, alias='Authorization'),
        _auth: None = Depends(_require_api_key),
        _rate_limit: None = Depends(_enforce_rate_limit),
    ):
        tenant_identity = _enforce_tenant_authorization(
            request=request,
            action='review.write',
            x_api_key=x_api_key,
            authorization=authorization,
            requested_scope=_tenant_scope_dict(payload.tenant_scope),
        )
        tenant_scope = None if tenant_identity is None else {
            'organization_id': tenant_identity.organization_id,
            'project_id': tenant_identity.project_id,
        }
        claimed = repository.claim_review_task(
            review_task_id=payload.review_task_id,
            consumer=payload.consumer,
            tenant_scope=tenant_scope,
        )
        if claimed is None:
            raise HTTPException(status_code=404, detail='No review task available to claim.')
        _record_review_governance_event(
            event_type='review_claimed',
            status='success',
            review_task_id=str(claimed.get('review_task_id', '')),
            tenant_identity=tenant_identity,
            metadata={'consumer': payload.consumer},
        )
        return claimed

    @app.post('/v1/review/queue/{review_task_id}/close')
    def close_review_queue_item(
        request: Request,
        review_task_id: str,
        payload: ReviewQueueCloseRequestSchema,
        repository: ReviewQueueRepository = Depends(_require_review_queue_repository),
        x_api_key: str | None = Header(default=None, alias='X-API-Key'),
        authorization: str | None = Header(default=None, alias='Authorization'),
        _auth: None = Depends(_require_api_key),
        _rate_limit: None = Depends(_enforce_rate_limit),
    ):
        tenant_identity = _enforce_tenant_authorization(
            request=request,
            action='review.write',
            x_api_key=x_api_key,
            authorization=authorization,
            requested_scope=_tenant_scope_dict(payload.tenant_scope),
        )
        tenant_scope = None if tenant_identity is None else {
            'organization_id': tenant_identity.organization_id,
            'project_id': tenant_identity.project_id,
        }
        closed = repository.close_review_task(
            review_task_id,
            status=payload.status,
            closed_by=payload.closed_by,
            review_notes=payload.review_notes,
            decision=payload.decision,
            reason_codes=payload.reason_codes,
            reviewer_edits=payload.reviewer_edits,
            tenant_scope=tenant_scope,
        )
        if closed is None:
            raise HTTPException(status_code=404, detail='Review task not found: %s' % review_task_id.strip())
        _record_review_governance_event(
            event_type='review_closed',
            status='success',
            review_task_id=str(closed.get('review_task_id', '')).strip() or review_task_id.strip(),
            tenant_identity=tenant_identity,
            reason_codes=list(payload.reason_codes),
            metadata={
                'decision': str(closed.get('decision', '')).strip(),
                'final_status': str(closed.get('status', '')).strip(),
            },
        )
        decision_text = str(closed.get('decision', '')).strip().lower()
        if decision_text == 'approve':
            scope = _tenant_scope_from_identity(tenant_identity)
            governance_ledger.record_cost_entry(
                {
                    **scope,
                    'run_id': str(closed.get('review_task_id', '')).strip() or review_task_id.strip(),
                    'skill_id': str(closed.get('skill_id', '')).strip(),
                    'bundle_id': str(closed.get('skill_id', '')).strip(),
                    'event_kind': 'accepted_package',
                    'provider': 'review_queue',
                    'operation': 'review.approve',
                    'call_count': 1,
                    'failure_count': 0,
                    'estimated_cost_usd': 0.0,
                    'currency': 'USD',
                    'metadata': {
                        'source': 'review_queue_close',
                        'review_task_id': str(closed.get('review_task_id', '')).strip() or review_task_id.strip(),
                        'closed_by': str(closed.get('closed_by', '')).strip(),
                    },
                }
            )
        return closed

    @app.post('/v1/review/queue/{review_task_id}/decision')
    def update_review_queue_decision(
        request: Request,
        review_task_id: str,
        payload: ReviewQueueDecisionRequestSchema,
        repository: ReviewQueueRepository = Depends(_require_review_queue_repository),
        x_api_key: str | None = Header(default=None, alias='X-API-Key'),
        authorization: str | None = Header(default=None, alias='Authorization'),
        _auth: None = Depends(_require_api_key),
        _rate_limit: None = Depends(_enforce_rate_limit),
    ):
        tenant_identity = _enforce_tenant_authorization(
            request=request,
            action='review.write',
            x_api_key=x_api_key,
            authorization=authorization,
            requested_scope=_tenant_scope_dict(payload.tenant_scope),
        )
        tenant_scope = None if tenant_identity is None else {
            'organization_id': tenant_identity.organization_id,
            'project_id': tenant_identity.project_id,
        }
        update_fn = getattr(repository, 'update_review_task_decision', None)
        if update_fn is None:
            raise HTTPException(status_code=503, detail='Review queue decision operation is not configured.')
        closed = update_fn(
            review_task_id,
            decision=payload.decision,
            reviewer=payload.reviewer,
            reason_codes=payload.reason_codes,
            review_notes=payload.review_notes,
            reviewer_edits=payload.reviewer_edits,
            status=payload.status,
            tenant_scope=tenant_scope,
        )
        if closed is None:
            raise HTTPException(status_code=404, detail='Review task not found: %s' % review_task_id.strip())
        _record_review_governance_event(
            event_type='review_decision_applied',
            status='success',
            review_task_id=str(closed.get('review_task_id', '')).strip() or review_task_id.strip(),
            tenant_identity=tenant_identity,
            reason_codes=list(payload.reason_codes),
            metadata={
                'decision': payload.decision,
                'final_status': str(closed.get('status', '')).strip(),
            },
        )
        if payload.decision == 'approve':
            scope = _tenant_scope_from_identity(tenant_identity)
            governance_ledger.record_cost_entry(
                {
                    **scope,
                    'run_id': str(closed.get('review_task_id', '')).strip() or review_task_id.strip(),
                    'skill_id': str(closed.get('skill_id', '')).strip(),
                    'bundle_id': str(closed.get('skill_id', '')).strip(),
                    'event_kind': 'accepted_package',
                    'provider': 'review_queue',
                    'operation': 'review.approve',
                    'call_count': 1,
                    'failure_count': 0,
                    'estimated_cost_usd': 0.0,
                    'currency': 'USD',
                    'metadata': {
                        'source': 'review_queue_decision',
                        'review_task_id': str(closed.get('review_task_id', '')).strip() or review_task_id.strip(),
                        'closed_by': str(closed.get('closed_by', '')).strip(),
                    },
                }
            )
        return closed

    @app.post('/v1/distill/text')
    def distill_text(
        request: Request,
        payload: TextDistillRequestSchema,
        x_api_key: str | None = Header(default=None, alias='X-API-Key'),
        authorization: str | None = Header(default=None, alias='Authorization'),
        _auth: None = Depends(_require_api_key),
        _rate_limit: None = Depends(_enforce_rate_limit),
    ):
        tenant_identity = _enforce_tenant_authorization(
            request=request,
            action='distill.execute',
            x_api_key=x_api_key,
            authorization=authorization,
            requested_scope=_tenant_scope_dict(payload.tenant_scope),
        )
        request = TextDistillRequest(
            title=payload.title,
            content=payload.content,
            file_path=payload.file_path,
            goal=_goal_from_schema(payload.goal),
            metadata=_inject_tenant_scope_metadata(
                payload_metadata=payload.metadata,
                tenant_identity=tenant_identity,
                requested_scope=payload.tenant_scope,
            ),
        )
        return _build_distill_response(service.distill_text(request))

    @app.post('/v1/distill/audio')
    def distill_audio(
        request: Request,
        payload: AudioDistillRequestSchema,
        x_api_key: str | None = Header(default=None, alias='X-API-Key'),
        authorization: str | None = Header(default=None, alias='Authorization'),
        _auth: None = Depends(_require_api_key),
        _rate_limit: None = Depends(_enforce_rate_limit),
    ):
        tenant_identity = _enforce_tenant_authorization(
            request=request,
            action='distill.execute',
            x_api_key=x_api_key,
            authorization=authorization,
            requested_scope=_tenant_scope_dict(payload.tenant_scope),
        )
        request = AudioDistillRequest(
            title=payload.title,
            audio_path=payload.audio_path,
            transcript=payload.transcript,
            transcript_path=payload.transcript_path,
            language=payload.language,
            prompt=payload.prompt,
            goal=_goal_from_schema(payload.goal),
            metadata=_inject_tenant_scope_metadata(
                payload_metadata=payload.metadata,
                tenant_identity=tenant_identity,
                requested_scope=payload.tenant_scope,
            ),
        )
        return _build_distill_response(service.distill_audio(request))

    @app.post('/v1/distill/image')
    def distill_image(
        request: Request,
        payload: ImageDistillRequestSchema,
        x_api_key: str | None = Header(default=None, alias='X-API-Key'),
        authorization: str | None = Header(default=None, alias='Authorization'),
        _auth: None = Depends(_require_api_key),
        _rate_limit: None = Depends(_enforce_rate_limit),
    ):
        tenant_identity = _enforce_tenant_authorization(
            request=request,
            action='distill.execute',
            x_api_key=x_api_key,
            authorization=authorization,
            requested_scope=_tenant_scope_dict(payload.tenant_scope),
        )
        request = ImageDistillRequest(
            image_path=payload.image_path,
            title=payload.title,
            goal=_goal_from_schema(payload.goal),
            metadata=_inject_tenant_scope_metadata(
                payload_metadata=payload.metadata,
                tenant_identity=tenant_identity,
                requested_scope=payload.tenant_scope,
            ),
        )
        return _build_distill_response(service.distill_image(request))

    @app.post('/v1/distill/tabular')
    def distill_tabular(
        request: Request,
        payload: TabularDistillRequestSchema,
        x_api_key: str | None = Header(default=None, alias='X-API-Key'),
        authorization: str | None = Header(default=None, alias='Authorization'),
        _auth: None = Depends(_require_api_key),
        _rate_limit: None = Depends(_enforce_rate_limit),
    ):
        tenant_identity = _enforce_tenant_authorization(
            request=request,
            action='distill.execute',
            x_api_key=x_api_key,
            authorization=authorization,
            requested_scope=_tenant_scope_dict(payload.tenant_scope),
        )
        request = TabularDistillRequest(
            file_path=payload.file_path,
            title=payload.title,
            time_column=payload.time_column,
            value_columns=payload.value_columns,
            entity_columns=payload.entity_columns,
            max_series=payload.max_series,
            goal=_goal_from_schema(payload.goal),
            metadata=_inject_tenant_scope_metadata(
                payload_metadata=payload.metadata,
                tenant_identity=tenant_identity,
                requested_scope=payload.tenant_scope,
            ),
        )
        return _build_distill_response(service.distill_tabular(request))

    @app.post('/v1/distill/video')
    def distill_video(
        request: Request,
        payload: VideoDistillRequestSchema,
        x_api_key: str | None = Header(default=None, alias='X-API-Key'),
        authorization: str | None = Header(default=None, alias='Authorization'),
        _auth: None = Depends(_require_api_key),
        _rate_limit: None = Depends(_enforce_rate_limit),
    ):
        tenant_identity = _enforce_tenant_authorization(
            request=request,
            action='distill.execute',
            x_api_key=x_api_key,
            authorization=authorization,
            requested_scope=_tenant_scope_dict(payload.tenant_scope),
        )
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
            metadata=_inject_tenant_scope_metadata(
                payload_metadata=payload.metadata,
                tenant_identity=tenant_identity,
                requested_scope=payload.tenant_scope,
            ),
        )
        return _build_distill_response(service.distill_video(request))

    @app.post('/v1/distill/corpus')
    def distill_corpus(
        request: Request,
        payload: CorpusDistillRequestSchema,
        x_api_key: str | None = Header(default=None, alias='X-API-Key'),
        authorization: str | None = Header(default=None, alias='Authorization'),
        _auth: None = Depends(_require_api_key),
        _rate_limit: None = Depends(_enforce_rate_limit),
    ):
        tenant_identity = _enforce_tenant_authorization(
            request=request,
            action='distill.execute',
            x_api_key=x_api_key,
            authorization=authorization,
            requested_scope=_tenant_scope_dict(payload.tenant_scope),
        )
        payload_dict = payload.model_dump()
        payload_dict['metadata'] = _inject_tenant_scope_metadata(
            payload_metadata=payload.metadata,
            tenant_identity=tenant_identity,
            requested_scope=payload.tenant_scope,
        )
        request = CorpusDistillRequest.from_dict(payload_dict)
        return _build_distill_response(service.distill_corpus(request))

    @app.post('/v1/governance/report')
    def governance_report(
        request: Request,
        payload: GovernanceScopeRequestSchema,
        x_api_key: str | None = Header(default=None, alias='X-API-Key'),
        authorization: str | None = Header(default=None, alias='Authorization'),
        _auth: None = Depends(_require_api_key),
        _rate_limit: None = Depends(_enforce_rate_limit),
    ):
        tenant_identity = _enforce_tenant_authorization(
            request=request,
            action='review.read',
            x_api_key=x_api_key,
            authorization=authorization,
            requested_scope={
                'organization_id': payload.organization_id,
                'project_id': payload.project_id,
            },
        )
        scope = _resolve_governance_scope(
            tenant_identity=tenant_identity,
            requested_organization_id=payload.organization_id,
            requested_project_id=payload.project_id,
        )
        return governance_ledger.build_report(
            tenant_scope=scope,
            include_cost_entries=bool(payload.include_cost_entries),
            include_audit_events=bool(payload.include_audit_events),
            include_deletion_records=bool(payload.include_deletion_records),
            include_retention_policies=bool(payload.include_retention_policies),
            limit=int(payload.limit),
        )

    @app.post('/v1/governance/retention-policy')
    def governance_upsert_retention_policy(
        request: Request,
        payload: GovernanceRetentionPolicyUpsertRequestSchema,
        x_api_key: str | None = Header(default=None, alias='X-API-Key'),
        authorization: str | None = Header(default=None, alias='Authorization'),
        _auth: None = Depends(_require_api_key),
        _rate_limit: None = Depends(_enforce_rate_limit),
    ):
        tenant_identity = _enforce_tenant_authorization(
            request=request,
            action='review.write',
            x_api_key=x_api_key,
            authorization=authorization,
            requested_scope={
                'organization_id': payload.organization_id,
                'project_id': payload.project_id,
            },
        )
        scope = _resolve_governance_scope(
            tenant_identity=tenant_identity,
            requested_organization_id=payload.organization_id,
            requested_project_id=payload.project_id,
        )
        result = governance_ledger.upsert_retention_policy(
            {
                **payload.model_dump(),
                **scope,
                'updated_by': payload.updated_by or (
                    tenant_identity.user_id if tenant_identity is not None else 'governance-operator'
                ),
            }
        )
        return {'policy': result}

    @app.post('/v1/governance/deletion')
    def governance_record_deletion(
        request: Request,
        payload: GovernanceDeletionRequestSchema,
        x_api_key: str | None = Header(default=None, alias='X-API-Key'),
        authorization: str | None = Header(default=None, alias='Authorization'),
        _auth: None = Depends(_require_api_key),
        _rate_limit: None = Depends(_enforce_rate_limit),
    ):
        tenant_identity = _enforce_tenant_authorization(
            request=request,
            action='review.write',
            x_api_key=x_api_key,
            authorization=authorization,
            requested_scope={
                'organization_id': payload.organization_id,
                'project_id': payload.project_id,
            },
        )
        scope = _resolve_governance_scope(
            tenant_identity=tenant_identity,
            requested_organization_id=payload.organization_id,
            requested_project_id=payload.project_id,
        )
        result = governance_ledger.record_deletion_event(
            {
                **payload.model_dump(),
                **scope,
                'actor': payload.actor or (
                    tenant_identity.user_id if tenant_identity is not None else 'governance-operator'
                ),
                'api_key_id': payload.api_key_id or (
                    tenant_identity.api_key_id if tenant_identity is not None else ''
                ),
            }
        )
        return {'deletion_record': result}

    @app.post('/v1/console/views')
    def platform_console_views(
        request: Request,
        payload: ConsoleViewsRequestSchema,
        repository: ReviewQueueRepository = Depends(_require_review_queue_repository),
        x_api_key: str | None = Header(default=None, alias='X-API-Key'),
        authorization: str | None = Header(default=None, alias='Authorization'),
        _auth: None = Depends(_require_api_key),
        _rate_limit: None = Depends(_enforce_rate_limit),
    ):
        tenant_identity = _enforce_tenant_authorization(
            request=request,
            action='review.read',
            x_api_key=x_api_key,
            authorization=authorization,
            requested_scope={
                'organization_id': payload.organization_id,
                'project_id': payload.project_id,
            },
        )
        scope = _resolve_governance_scope(
            tenant_identity=tenant_identity,
            requested_organization_id=payload.organization_id,
            requested_project_id=payload.project_id,
        )
        review_queue_items = repository.list_review_queue(
            queue_status=payload.queue_status,
            limit=int(payload.limit),
            tenant_scope=scope,
        )
        return build_platform_console_views(
            repo_root=settings.repo_root,
            draft_dir=settings.draft_dir,
            governance_ledger=governance_ledger,
            tenant_scope=scope,
            review_queue_items=review_queue_items,
            limit=int(payload.limit),
        )

    return app


app = create_app() if FastAPI is not None else None
