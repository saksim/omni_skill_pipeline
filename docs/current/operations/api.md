# API

## Entry

- API app module: `apps/api/main.py`
- FastAPI assembly: `src/omni_skill_pipeline/api_app.py`

## Start

```bash
python -m uvicorn apps.api.main:app --reload
```

鍚姩鍚庡彲璁块棶锛?
- OpenAPI UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

## Container Baseline

鏋勫缓鏈€灏?API 闀滃儚锛?
```bash
docker build -t omni-skill-pipeline:local .
```

杩愯闀滃儚锛堟槧灏勫埌鏈満 `18000`锛夛細

```bash
docker run --rm -p 18000:8000 omni-skill-pipeline:local
```

鍚姩鍚庡叆鍙ｏ細

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

- `GET /healthz` 杩斿洖 readiness 缁撴灉锛屼笉璧扮粺涓€ `error` 鍖呰銆?- Ready response: `200` with `{"status":"ready","checks":[...]}`銆?- Degraded response: `503` with `{"status":"degraded","checks":[...]}`銆?- `checks[]` 瀛楁缁撴瀯锛?  - `name`: `template_path | draft_dir | app_assembly`
  - `ok`: `true | false`
  - `detail`: 鍙璇婃柇淇℃伅
  - `missing_routes`: 浠?`app_assembly` 澶辫触鏃惰繑鍥?- 褰撳墠妫€鏌ラ」锛?  - template path readability锛坄docs/current/contracts/SKILL.template.md`锛?  - draft directory availability锛坄skills/drafts/`锛?  - FastAPI required route assembly锛堟牳蹇冭矾鐢辨槸鍚﹀叏閮ㄨ閰嶏級

## Authentication

- 榛樿涓嶉壌鏉冦€?- 褰撶幆澧冨彉閲?`OMNI_API_KEY` 璁剧疆涓洪潪绌烘椂锛屾墍鏈?`POST /v1/distill/*` 涓?`POST /v1/governance/*` 绔偣鍚敤 API key 鏍￠獙銆?- `GET /healthz` 涓?`GET /v1/templates/skill` 涓嶅彈 `OMNI_API_KEY` 淇濇姢銆?- 鍙敤璇锋眰澶达細
  - `X-API-Key: <OMNI_API_KEY>`
  - `Authorization: Bearer <OMNI_API_KEY>`
- 閴存潈澶辫触琛屼负锛?  - 缂哄皯 key: `401`, `error.message = "Missing API key."`
  - key 涓嶅尮閰? `403`, `error.message = "Invalid API key."`

### Tenant Authz (GL-08)

- If tenant access config is enabled (OMNI_TENANT_ACCESS_JSON or OMNI_TENANT_ACCESS_FILE), distill and eview queue routes require tenant-scoped API keys.
- Role/action permissions are enforced (distill.execute, eview.read, eview.write).
- Cross-tenant scope requests are rejected.
- Revoked tenant API keys are rejected.
- Tenant quotas can return 429 with Retry-After.
## Rate Limiting

- 闄愭祦浣滅敤鍩燂細鎵€鏈?`POST /v1/distill/*` 绔偣銆?- 鏍囪瘑浼樺厛绾э細浼樺厛浣跨敤 `X-API-Key`/`Authorization` 涓殑 key锛涙棤 key 鏃跺洖閫€鍒板鎴风 IP銆?- 鍙傛暟鏉ユ簮锛?  - `OMNI_RATE_LIMIT_REQUESTS`锛氱獥鍙ｅ唴鏈€澶氳姹傛暟锛坄0` 涓哄叧闂級銆?  - `OMNI_RATE_LIMIT_WINDOW_SECONDS`锛氱獥鍙ｉ暱搴︼紙绉掞級銆?- 瓒呴檺鍝嶅簲锛歚429`锛屽苟鎼哄甫 `Retry-After` header銆?- 瓒呴檺閿欒浣擄細`error.type = "http"`锛宍error.code = "http_error"`锛宍error.message = "Rate limit exceeded."`銆?
## Error Contract

### Unified error envelope

闄?`/healthz` 澶栵紝API 寮傚父閮借繑鍥炵粺涓€ JSON锛?
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

| HTTP | `error.type` | `error.code` | 瑙﹀彂鏉′欢 |
| --- | --- | --- | --- |
| 400 | `validation` | `bad_request` | 涓氬姟灞?`ValueError` |
| 401 | `http` | `http_error` | 缂哄け API key |
| 403 | `http` | `http_error` | API key 涓嶅尮閰?|
| 422 | `validation` | `validation_error` | Pydantic 璇锋眰鏍￠獙澶辫触 |
| 429 | `http` | `http_error` | 瓒呭嚭闄愭祦绐楀彛 |
| 502 | `provider` | `provider_execution_error` | provider 鎵ц澶辫触 |
| 502 | `provider` | `media_processing_error` | 濯掍綋澶勭悊澶辫触 |
| 503 | `provider` | `provider_unavailable` | provider 涓嶅彲鐢?|
| 500 | `runtime` | `runtime_error` | 鏈崟鑾疯繍琛屾椂閿欒 |

### Details field contract

- `422`锛歚details` 涓烘暟缁勶紙Pydantic errors锛夈€?- `429`锛歚details = "Rate limit exceeded."`锛屽苟杩斿洖 `Retry-After` header銆?- 鍏朵粬閿欒锛歚details` 涓哄瓧绗︿覆鎴?`null`锛屽彇鍐充簬寮傚父鏉ユ簮銆?
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

For controlled external Beta operation, follow:

- `docs/current/operations/runbooks/controlled-external-beta-onboarding.md`

The runbook defines the official sequence:

1. manifest validation
2. distill (CLI/API)
3. review queue operation
4. export + usability validation
5. trial security gate
6. trial metrics collection
7. launch readiness decision check

## V2 Distill Response Summary (TP-E10-02)

鎵€鏈?`POST /v1/distill/*` 绔偣浠嶈繑鍥炲巻鍙?`bundle` 瀛楁锛堝 `skill_markdown`銆乣skill_graph`銆乣publications`锛夛紝鍚屾椂鏂板浠ヤ笅椤跺眰鎽樿瀛楁锛?
- `graph_metadata`
  - `graph_id`
  - `name`
  - `version`
  - `review_status`
  - `node_counts`锛坄steps/decisions/verifications/risks/examples/variables/edges`锛?- `available_publications`
  - 鍒楀嚭鍙敤鍙戝竷瑙嗗浘锛坄publication_type`銆乣path`銆乣publication_id`锛?- `review_status`
  - 浼樺厛鍙?`review_task.status`锛岀己澶辨椂鍥為€€ `skill.review_status`
- `lifecycle_decision`
  - 閫忎紶 `adapter_metadata.lifecycle_decision`锛堣嫢瀛樺湪锛?
鍏煎鎬ц姹傦細鏃ф帴鍙ｆ秷璐规柟浠嶅彲鐩存帴璇诲彇 `skill_markdown`锛屾棤闇€鏀归€犮€?
## Current Caveats

- distill API 宸插紑鏀?corpus 涓?V2 鎽樿瀛楁锛泈orker 宸叉敮鎸?`review_queue` / `rebuild_publication` / `revise_skill` 涓夌被浠诲姟銆?- 宸插惎鐢?structured logging锛屽寘鍚?request_id / trace_id 鍏宠仈瀛楁

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
  - Body:
    - `organization_id` (optional)
    - `project_id` (optional)
    - `include_cost` (optional, default `true`)
    - `include_audit` (optional, default `true`)
    - `include_deletions` (optional, default `true`)
    - `include_retention` (optional, default `true`)
  - Behavior: returns tenant/project scoped governance report from ledger records (`cost_entries`, `audit_events`, `deletion_records`, `retention_policies`).
- `POST /v1/governance/retention-policy`
  - Body: `organization_id`, `project_id` (optional), `policy_name`, `retention_days`, `enabled` (optional).
  - Behavior: upserts retention policy for the requested scope.
- `POST /v1/governance/deletion`
  - Body: `artifact_type`, `artifact_id`, `reason`, `requested_by`, `organization_id` (optional), `project_id` (optional).
  - Behavior: records deletion event and corresponding governance audit trail.

These endpoints follow the same API key and rate-limit middleware used by `/v1/distill/*`.
If repository does not implement `ReviewQueueRepository`, API returns `503`.

## Platform Console View (GL-10)

- `POST /v1/console/views`
  - Body:
    - `organization_id` (optional; if tenant auth is enabled, must match caller scope)
    - `project_id` (optional; if tenant auth is enabled, must match caller scope)
    - `queue_status`: `pending|consumed|closed|all` (default `pending`)
    - `limit`: `1..500` (default `50`)
  - Behavior:
    - Returns a single aggregated operator/reviewer surface with six view groups:
      - `trial_runs`
      - `review_queue`
      - `skill_registry`
      - `metrics`
      - `security_failures`
      - `cost`
    - Uses current baseline evidence files under `docs/current/status/baselines/` plus review queue/runtime and governance ledger.
    - Keeps tenant scope filtering aligned with GL-08 authz constraints.
  - Primary use:
    - one-call snapshot for operators to monitor trial state and launch blockers without manually reading raw artifact directories.

