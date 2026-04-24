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

## Endpoints

- `GET /healthz`
- `GET /v1/templates/skill`
- `POST /v1/distill/text`
- `POST /v1/distill/audio`
- `POST /v1/distill/image`
- `POST /v1/distill/tabular`
- `POST /v1/distill/video`

## Health / Readiness

- `GET /healthz` returns structured readiness checks.
- Ready response: `200` with `{"status":"ready","checks":[...]}`.
- Degraded response: `503` with `{"status":"degraded","checks":[...]}`.
- Current checks include:
  - template path readability
  - draft directory availability
  - FastAPI required route assembly

## Authentication

- 默认不鉴权。
- 当环境变量 `OMNI_API_KEY` 设置为非空时，所有 `POST /v1/distill/*` 端点启用 API key 校验。
- 可用请求头：
  - `X-API-Key: <OMNI_API_KEY>`
  - `Authorization: Bearer <OMNI_API_KEY>`
- 鉴权失败行为：
  - 缺少 key: `401`
  - key 不匹配: `403`

## Rate Limiting

- 限流作用域：所有 `POST /v1/distill/*` 端点。
- 标识优先级：优先使用 `X-API-Key`/`Authorization` 中的 key；无 key 时回退到客户端 IP。
- 参数来源：
  - `OMNI_RATE_LIMIT_REQUESTS`：窗口内最多请求数（`0` 为关闭）。
  - `OMNI_RATE_LIMIT_WINDOW_SECONDS`：窗口长度（秒）。
- 超限响应：`429`，并携带 `Retry-After` header。

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
- 当前无 structured logging
- 已有结构化错误响应，但仍需补充更细粒度 error contract 与错误码稳定策略
