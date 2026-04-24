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
- `POST /v1/distill/text`
- `POST /v1/distill/audio`
- `POST /v1/distill/image`
- `POST /v1/distill/tabular`
- `POST /v1/distill/video`

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

## Current Caveats

- 当前仅覆盖单资产 distill 端点，`/v1/distill/corpus` 尚未开放
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

