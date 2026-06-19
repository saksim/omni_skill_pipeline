# API

## Entry

- API app module: `apps/api/main.py`
- FastAPI assembly: `src/omni_skill_pipeline/api_app.py`

## Start

```bash
python -m uvicorn apps.api.main:app --reload
```

After startup:

- OpenAPI UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

## Container Baseline

Build the minimal local API image:

```bash
docker build -t omni-skill-pipeline:local .
```

Run the image and map it to local port `18000`:

```bash
docker run --rm -p 18000:8000 omni-skill-pipeline:local
```

Container entry points:

- OpenAPI UI: `http://127.0.0.1:18000/docs`
- Health: `http://127.0.0.1:18000/healthz`

## Endpoints

- `GET /healthz`
- `GET /v1/templates/skill`
- `GET /v1/review/queue`
- `POST /v1/review/queue/claim`
- `POST /v1/review/queue/{review_task_id}/close`
- `POST /v1/review/queue/{review_task_id}/decision`
- `POST /v1/distill/text`
- `POST /v1/distill/audio`
- `POST /v1/distill/image`
- `POST /v1/distill/tabular`
- `POST /v1/distill/video`
- `POST /v1/distill/corpus`
- `POST /v1/governance/report`
- `POST /v1/governance/retention-policy`
- `POST /v1/governance/deletion`
- `POST /v1/console/views`

## Health / Readiness

- `GET /healthz` returns readiness directly and does not use the unified `error` envelope.
- Ready response: `200` with `{"status":"ready","checks":[...]}`.
- Degraded response: `503` with `{"status":"degraded","checks":[...]}`.
- `checks[]` fields:
  - `name`: `template_path | draft_dir | app_assembly`
  - `ok`: `true | false`
  - `detail`: readable diagnostic message
  - `missing_routes`: returned only when `app_assembly` fails
- Current checks:
  - template path readability (`docs/latest/contracts/SKILL.template.md`)
  - draft directory availability (`skills/drafts/`)
  - FastAPI required route assembly

## Authentication

- Authentication is disabled by default.
- When `OMNI_API_KEY` is set to a non-empty value, all `POST /v1/distill/*` and `POST /v1/governance/*` endpoints require API key validation.
- `GET /healthz` and `GET /v1/templates/skill` are not protected by `OMNI_API_KEY`.
- Accepted request headers:
  - `X-API-Key: <OMNI_API_KEY>`
  - `Authorization: Bearer <OMNI_API_KEY>`
- Authentication failures:
  - Missing key: `401`, `error.message = "Missing API key."`
  - Invalid key: `403`, `error.message = "Invalid API key."`

### Tenant Authz (GL-08)

- If tenant access config is enabled (`OMNI_TENANT_ACCESS_JSON` or `OMNI_TENANT_ACCESS_FILE`), distill and review queue routes require tenant-scoped API keys.
- Role/action permissions are enforced (`distill.execute`, `review.read`, `review.write`).
- Cross-tenant scope requests are rejected.
- Revoked tenant API keys are rejected.
- Tenant quotas can return `429` with `Retry-After`.

## Rate Limiting

- Rate limiting applies to all `POST /v1/distill/*` endpoints.
- Identity priority: use the key from `X-API-Key`/`Authorization` first; when absent, fall back to client IP.
- Parameters:
  - `OMNI_RATE_LIMIT_REQUESTS`: maximum requests per window (`0` disables rate limiting).
  - `OMNI_RATE_LIMIT_WINDOW_SECONDS`: window length in seconds.
- Exceeded limit response: `429` with `Retry-After` header.
- Error body: `error.type = "http"`, `error.code = "http_error"`, `error.message = "Rate limit exceeded."`

## Error Contract

### Unified Error Envelope

Except for `/healthz`, API exceptions return a unified JSON envelope:

```json
{
  "error": {
    "type": "validation | provider | http | runtime",
    "code": "stable_error_code",
    "message": "human readable message",
    "details": {}
  }
}
```

### Status / Code Matrix

| HTTP | `error.type` | `error.code` | Trigger |
| --- | --- | --- | --- |
| 400 | `validation` | `bad_request` | `ValueError` or malformed request |
| 401 | `http` | `http_error` | Missing API key |
| 403 | `http` | `http_error` | Invalid API key or rejected tenant scope |
| 422 | `validation` | `validation_error` | Pydantic validation error |
| 429 | `http` | `http_error` | Rate limit exceeded |
| 502 | `provider` | `provider_execution_error` | Provider execution failed |
| 502 | `provider` | `media_processing_error` | Media processing failed |
| 503 | `provider` | `provider_unavailable` | Provider unavailable |
| 500 | `runtime` | `runtime_error` | Unhandled runtime error |

### Details Field Contract

- `422`: `details` is an array of Pydantic errors.
- `429`: `details = "Rate limit exceeded."` and response includes `Retry-After`.
- Other errors: `details` is a string or `null`, depending on the exception source.

## Provider Timeout

- OpenAI provider requests use explicit timeout from `OMNI_OPENAI_TIMEOUT_SECONDS`.
- Default timeout is `60` seconds if env var is not set.

## Provider Retry / Backoff

- OpenAI transcription and responses requests use finite retry with exponential backoff.
- `OMNI_OPENAI_RETRY_MAX_ATTEMPTS` controls total attempts (default `3`).
- `OMNI_OPENAI_RETRY_BASE_DELAY_SECONDS` controls backoff base delay (default `0.5` seconds).
- Retry is only applied to transient failures (`429` or `5xx` style upstream errors).

## Provider Circuit Breaker / Failure Budget

- OpenAI provider tracks consecutive failures and rolling-window failures to prevent failure storms.
- Consecutive failure threshold: `OMNI_OPENAI_CIRCUIT_BREAKER_CONSECUTIVE_FAILURES` (default `3`).
- Failure budget window:
  - `OMNI_OPENAI_FAILURE_BUDGET_MAX_FAILURES` (default `6`)
  - `OMNI_OPENAI_FAILURE_BUDGET_WINDOW_SECONDS` (default `60`)
- Cooldown while circuit is open: `OMNI_OPENAI_CIRCUIT_BREAKER_COOLDOWN_SECONDS` (default `30`).
- When the circuit is open, provider calls fail fast with `ProviderExecutionError` and include `retry_after_seconds` plus the open reason.

## Payload Examples

### Text

```json
{
  "title": "PostgreSQL Slow Query Review",
  "file_path": "examples/text_note.md",
  "goal": {
    "domain": "database"
  }
}
```

### Audio

```json
{
  "transcript_path": "examples/audio_transcript.srt",
  "goal": {
    "domain": "ops"
  }
}
```

### Image

```json
{
  "image_path": "examples/demo_image.png",
  "goal": {
    "domain": "observability"
  }
}
```

### Tabular

```json
{
  "file_path": "examples/demo_timeseries.csv",
  "time_column": "timestamp",
  "value_columns": ["latency_ms", "error_rate"],
  "entity_columns": ["service"],
  "goal": {
    "domain": "incident_response"
  }
}
```

### Video

```json
{
  "video_path": "examples/demo_video.mp4",
  "max_keyframes": 6,
  "scene_threshold": 0.32,
  "dedupe_distance": 5,
  "goal": {
    "domain": "incident_response"
  }
}
```

### Corpus

```json
{
  "name": "gl03-controlled-beta-sample",
  "assets": [
    {
      "source_uri": "examples/trial/text/slow-query-notes.md",
      "modality": "text",
      "role": "primary"
    },
    {
      "source_uri": "examples/trial/image/service-latency-dashboard.png",
      "modality": "image",
      "role": "supporting"
    }
  ],
  "goal": {
    "goal_type": "build_skill",
    "audience": "ops",
    "rigor": "production",
    "granularity": "procedure",
    "domain": "incident_response"
  },
  "tags": ["controlled-beta", "gl03"],
  "metadata": {
    "review_owner": "beta-reviewer",
    "target_package_format": "portable",
    "expected_output_type": "runbook_skill"
  }
}
```

Canonical sample file: `examples/beta/corpus_payload.example.json`.

## Official GL-03 Flow

For controlled external Beta operation, follow `docs/latest/operations/runbooks/controlled-external-beta-onboarding.md`.

The runbook defines the official sequence:

1. manifest validation
2. distill (CLI/API)
3. review queue operation
4. export and usability validation
5. trial security gate
6. trial metrics collection
7. launch readiness decision check

## V2 Distill Response Summary (TP-E10-02)

All `POST /v1/distill/*` endpoints still return the legacy `bundle` field (`skill_markdown`, `skill_graph`, `publications`, and related artifacts). They also expose these top-level summary fields:

- `graph_metadata`
  - `graph_id`
  - `name`
  - `version`
  - `review_status`
  - `node_counts` (`steps`, `decisions`, `verifications`, `risks`, `examples`, `variables`, `edges`)
- `available_publications`
  - lists available publication views (`publication_type`, `path`, `publication_id`)
- `review_status`
  - prefers `review_task.status`; falls back to `skill.review_status` when the review task is absent
- `lifecycle_decision`
  - passes through `adapter_metadata.lifecycle_decision` when present

Compatibility requirement: legacy consumers can continue reading `skill_markdown` without changing their integration.

## Current Caveats

- distill API now exposes corpus and V2 summary fields.
- worker supports `review_queue`, `rebuild_publication`, and `revise_skill` task types.
- structured logging is enabled and includes `request_id` / `trace_id` correlation fields.

## Request / Trace Context

- Optional request headers:
  - `X-Request-ID`
  - `X-Trace-ID`
- If `X-Request-ID` is missing, API generates one.
- If `X-Trace-ID` is missing, API falls back to `X-Request-ID`.
- Response echoes both headers for downstream correlation.

## Structured Logging

- API, service, and worker logs include correlation fields:
  - `request_id`
  - `trace_id`
- API request completion event: `api_request_completed`.
- Service distillation events: `distill_start` / `distill_complete`.

## Review Queue Operations (LC-R-37)

- `GET /v1/review/queue`
  - Query: `queue_status` (`pending`/`consumed`/`closed`/`all`), `limit` (`1-1000`).
  - Response: `{"items": [...]}`.
- `POST /v1/review/queue/claim`
  - Body: `{"review_task_id"?: "...", "consumer"?: "review-consumer"}`.
  - Behavior: claim specific pending task if `review_task_id` is provided; otherwise claim oldest pending item.
  - `404` when no pending review task can be claimed.
- `POST /v1/review/queue/{review_task_id}/close`
  - Body: `{"status"?: "published", "closed_by"?: "review-operator", "review_notes"?: "...", "decision"?: "approve|reject|needs_rework", "reason_codes"?: ["..."], "reviewer_edits"?: {...}}`.
  - Behavior: move review task into `closed` queue bucket and persist closure metadata.
  - `404` when review task is not found.
- `POST /v1/review/queue/{review_task_id}/decision`
  - Body: `{"decision":"approve|reject|needs_rework", "reviewer"?: "review-operator", "reason_codes"?: ["..."], "review_notes"?: "...", "reviewer_edits"?: {...}, "status"?: "..."}`.
  - Behavior: structured decision action that closes the task with mapped status (`approve -> published`, `reject -> rejected`, `needs_rework -> needs_rework` unless `status` override is provided).
  - `404` when review task is not found.
  - `503` when repository runtime does not support structured decision operation.

## Governance Operations (GL-09)

- `POST /v1/governance/report`
  - Body: `organization_id` (optional), `project_id` (optional), `include_cost`, `include_audit`, `include_deletions`, `include_retention`.
  - Behavior: returns tenant/project scoped governance report from ledger records (`cost_entries`, `audit_events`, `deletion_records`, `retention_policies`).
- `POST /v1/governance/retention-policy`
  - Body: `organization_id`, `project_id` (optional), `policy_name`, `retention_days`, `enabled` (optional).
  - Behavior: upserts retention policy for the requested scope.
- `POST /v1/governance/deletion`
  - Body: `artifact_type`, `artifact_id`, `reason`, `requested_by`, `organization_id` (optional), `project_id` (optional).
  - Behavior: records deletion event and corresponding governance audit trail.

These endpoints follow the same API key and rate-limit middleware used by `/v1/distill/*`. If repository does not implement `ReviewQueueRepository`, API returns `503`.

## Platform Console View (GL-10)

- `POST /v1/console/views`
  - Body:
    - `organization_id` (optional; if tenant auth is enabled, must match caller scope)
    - `project_id` (optional; if tenant auth is enabled, must match caller scope)
    - `queue_status`: `pending|consumed|closed|all` (default `pending`)
    - `limit`: `1..500` (default `50`)
  - Behavior:
    - Returns a single aggregated operator/reviewer surface with six view groups: `trial_runs`, `review_queue`, `skill_registry`, `metrics`, `security_failures`, and `cost`.
    - Uses current baseline evidence files under `docs/working/status/baselines/` plus review queue/runtime and governance ledger.
    - Keeps tenant scope filtering aligned with GL-08 authz constraints.
  - Primary use: one-call snapshot for operators to monitor trial state and launch blockers without manually reading raw artifact directories.
