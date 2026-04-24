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

- 当前请求体仍使用 bare `dict`，尚未引入 Pydantic request models
- 当前无 auth / rate limiting / structured logging
- 请求处理异常当前多数会折叠为 `400`
