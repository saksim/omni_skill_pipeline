# Worker

## Entry

- Worker module: `apps/worker/main.py`
- Worker implementation: `src/omni_skill_pipeline/worker.py`

## Queue Layout

```text
data/jobs/
  pending/
  completed/
  failed/
```

## Supported Job Kinds

- `text`
- `audio`
- `image`
- `tabular`
- `video`

## Job Payload Examples

### Text

```json
{
  "kind": "text",
  "file_path": "examples/text_note.md",
  "goal": {
    "domain": "database"
  }
}
```

### Audio

```json
{
  "kind": "audio",
  "audio_path": "examples/audio_transcript.srt",
  "goal": {
    "domain": "ops"
  }
}
```

### Tabular

```json
{
  "kind": "tabular",
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
  "kind": "video",
  "video_path": "examples/demo_video.mp4",
  "max_keyframes": 6,
  "scene_threshold": 0.32,
  "dedupe_distance": 5,
  "goal": {
    "domain": "incident_response"
  }
}
```

## Result Layout

- success -> `data/jobs/completed/`
- failure -> `data/jobs/failed/`
- generated artifacts -> `skills/drafts/{slug}-{skill_id}/`

## Scratch Root Prune

`video` and multimodal jobs may leave temporary artifacts under `.tmp_omni_media/`.
Use the prune utility to periodically remove stale entries:

```bash
python scripts/prune_tmp_media.py --dry-run
python scripts/prune_tmp_media.py --retention-hours 24
```

Recommended automation cadence: every 6-24 hours depending on media throughput.
The utility only deletes entries older than the configured retention threshold.

## Logging

Worker runtime now emits structured log events (JSON by default), including:
- `worker_init`
- `worker_scan_start` / `worker_scan_complete`
- `worker_job_start` / `worker_job_complete`

Configure logging behavior with `OMNI_LOG_LEVEL` and `OMNI_LOG_FORMAT`.
