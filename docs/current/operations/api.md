# API

## Entry

- API app module: `apps/api/main.py`
- FastAPI assembly: `src/omni_skill_pipeline/api_app.py`

## Start

```bash
python -m uvicorn apps.api.main:app --reload
```

启动后可访问：

- OpenAPI UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

## Container Baseline

构建最小 API 镜像：

```bash
docker build -t omni-skill-pipeline:local .
```

运行镜像（映射到本机 `18000`）：

```bash
docker run --rm -p 18000:8000 omni-skill-pipeline:local
```

启动后入口：

- OpenAPI UI: `http://127.0.0.1:18000/docs`
- Health: `http://127.0.0.1:18000/healthz`

## Endpoints

- `GET /healthz`
- `GET /v1/templates/skill`
- `GET /v1/review/queue`
- `POST /v1/review/queue/claim`
- `POST /v1/review/queue/{review_task_id}/close`
- `POST /v1/distill/text`
- `POST /v1/distill/audio`
- `POST /v1/distill/image`
- `POST /v1/distill/tabular`
- `POST /v1/distill/video`
- `POST /v1/distill/corpus`

## Health / Readiness

- `GET /healthz` 返回 readiness 结果，不走统一 `error` 包装。
- Ready response: `200` with `{"status":"ready","checks":[...]}`。
- Degraded response: `503` with `{"status":"degraded","checks":[...]}`。
- `checks[]` 字段结构：
  - `name`: `template_path | draft_dir | app_assembly`
  - `ok`: `true | false`
  - `detail`: 可读诊断信息
  - `missing_routes`: 仅 `app_assembly` 失败时返回
- 当前检查项：
  - template path readability（`docs/current/contracts/SKILL.template.md`）
  - draft directory availability（`skills/drafts/`）
  - FastAPI required route assembly（核心路由是否全部装配）

## Authentication

- 默认不鉴权。
- 当环境变量 `OMNI_API_KEY` 设置为非空时，所有 `POST /v1/distill/*` 端点启用 API key 校验。
- `GET /healthz` 与 `GET /v1/templates/skill` 不受 `OMNI_API_KEY` 保护。
- 可用请求头：
  - `X-API-Key: <OMNI_API_KEY>`
  - `Authorization: Bearer <OMNI_API_KEY>`
- 鉴权失败行为：
  - 缺少 key: `401`, `error.message = "Missing API key."`
  - key 不匹配: `403`, `error.message = "Invalid API key."`

## Rate Limiting

- 限流作用域：所有 `POST /v1/distill/*` 端点。
- 标识优先级：优先使用 `X-API-Key`/`Authorization` 中的 key；无 key 时回退到客户端 IP。
- 参数来源：
  - `OMNI_RATE_LIMIT_REQUESTS`：窗口内最多请求数（`0` 为关闭）。
  - `OMNI_RATE_LIMIT_WINDOW_SECONDS`：窗口长度（秒）。
- 超限响应：`429`，并携带 `Retry-After` header。
- 超限错误体：`error.type = "http"`，`error.code = "http_error"`，`error.message = "Rate limit exceeded."`。

## Error Contract

### Unified error envelope

除 `/healthz` 外，API 异常都返回统一 JSON：

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

### Status / code matrix

| HTTP | `error.type` | `error.code` | 触发条件 |
| --- | --- | --- | --- |
| 400 | `validation` | `bad_request` | 业务层 `ValueError` |
| 401 | `http` | `http_error` | 缺失 API key |
| 403 | `http` | `http_error` | API key 不匹配 |
| 422 | `validation` | `validation_error` | Pydantic 请求校验失败 |
| 429 | `http` | `http_error` | 超出限流窗口 |
| 502 | `provider` | `provider_execution_error` | provider 执行失败 |
| 502 | `provider` | `media_processing_error` | 媒体处理失败 |
| 503 | `provider` | `provider_unavailable` | provider 不可用 |
| 500 | `runtime` | `runtime_error` | 未捕获运行时错误 |

### Details field contract

- `422`：`details` 为数组（Pydantic errors）。
- `429`：`details = "Rate limit exceeded."`，并返回 `Retry-After` header。
- 其他错误：`details` 为字符串或 `null`，取决于异常来源。

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

## V2 Distill Response Summary (TP-E10-02)

所有 `POST /v1/distill/*` 端点仍返回历史 `bundle` 字段（如 `skill_markdown`、`skill_graph`、`publications`），同时新增以下顶层摘要字段：

- `graph_metadata`
  - `graph_id`
  - `name`
  - `version`
  - `review_status`
  - `node_counts`（`steps/decisions/verifications/risks/examples/variables/edges`）
- `available_publications`
  - 列出可用发布视图（`publication_type`、`path`、`publication_id`）
- `review_status`
  - 优先取 `review_task.status`，缺失时回退 `skill.review_status`
- `lifecycle_decision`
  - 透传 `adapter_metadata.lifecycle_decision`（若存在）

兼容性要求：旧接口消费方仍可直接读取 `skill_markdown`，无需改造。

## Current Caveats

- distill API 已开放 corpus 与 V2 摘要字段；worker 任务类型升级仍待 `TP-E10-03`
- 已启用 structured logging，包含 request_id / trace_id 关联字段

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
  - Behavior: claim specific pending task if `review_task_id` provided; otherwise claim oldest pending item.
  - `404` when no pending review task can be claimed.
- `POST /v1/review/queue/{review_task_id}/close`
  - Body: `{"status"?: "published", "closed_by"?: "review-operator", "review_notes"?: "..."}`.
  - Behavior: move review task into `closed` queue bucket and persist closure metadata.
  - `404` when review task is not found.

These endpoints follow the same API key and rate-limit middleware used by `/v1/distill/*`.
If repository does not implement `ReviewQueueRepository`, API returns `503`.
