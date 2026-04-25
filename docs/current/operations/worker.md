# Worker

## Entry

- Worker module: `apps/worker/main.py`
- Worker implementation: `src/omni_skill_pipeline/worker.py`

## Queue Layout

```text
data/jobs/
  pending/
  inflight/
  completed/
  failed/
```

## Supported Job Kinds

- `text`
- `audio`
- `image`
- `tabular`
- `video`
- `corpus`

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

### Corpus

```json
{
  "kind": "corpus",
  "name": "beta-corpus",
  "assets": [
    {
      "source_uri": "file://examples/text_note.md",
      "modality": "text",
      "role": "primary"
    },
    {
      "source_uri": "file://examples/audio_transcript.srt",
      "modality": "audio",
      "role": "supporting"
    }
  ],
  "goal": {
    "domain": "operations"
  },
  "tags": ["beta", "ops"]
}
```

## Result Layout

- success -> `data/jobs/completed/`
- failure -> `data/jobs/failed/`
- generated artifacts -> `skills/drafts/{slug}-{skill_id}/`

## Retry Policy

- 默认每个作业最多尝试 `3` 次（包含首次执行）。
- 仅瞬时错误会重试：`ProviderExecutionError`、`MediaProcessingError`、`TimeoutError`、`ConnectionError`。
- 非瞬时错误（例如 payload 校验错误）直接失败，不重试。
- 失败落盘 (`data/jobs/failed/*.json`) 额外包含：
  - `attempts`
  - `transient`
  - `retry_exhausted`
  - `idempotency_key`

可通过 worker 参数覆盖默认策略：

```bash
python -m omni_skill_pipeline.worker \
  --jobs-root data/jobs \
  --max-attempts 3 \
  --retry-base-delay-seconds 0.5 \
  --retry-backoff-multiplier 2.0
```

## Idempotency / Duplicate Jobs

- Worker 会在处理前计算 `idempotency_key`，优先级如下：
  - payload 顶层 `idempotency_key`
  - payload `metadata.idempotency_key`
  - 无显式 key 时回退到 canonical payload 的 `sha256` 指纹
- 若该 key 已在 `completed/` 里出现，worker 会跳过二次执行，不再调用 distill service。
- 重复作业会从 `pending/` 清理，并写入审计记录到 `completed/{job_stem}.duplicate*.json`，记录字段包括：
  - `status=duplicate_skipped`
  - `idempotency_key`
  - `duplicate_of`（首个已完成作业文件名）

## Claim / Lock Semantics

- 每个 worker 在处理前会先对 `pending/*.json` 执行原子 claim：`pending -> inflight`。
- claim 成功的 worker 才会继续消费该 job；claim 失败代表已被其他 worker 抢占。
- 成功处理后，job 从 `inflight` 移入 `completed`；失败则写入 `failed` 并从 `inflight` 清理。
- 该语义确保多 worker 并发扫描同一队列时，同一 job 只会被单次消费。

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
- `worker_job_claimed` / `worker_job_claim_skipped`
- `worker_job_start` / `worker_job_complete`

Configure logging behavior with `OMNI_LOG_LEVEL` and `OMNI_LOG_FORMAT`.
