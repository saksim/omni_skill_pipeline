# Environment

## Baseline

Runtime only needs a clean Python 3.11 environment, optional media binaries, and provider credentials when those providers are enabled. Do not hard-code absolute interpreter paths in documentation.

## Runtime

- Python: `3.11+`
- Install mode: prefer an isolated virtual environment.
- Package root: `src/omni_skill_pipeline/`
- API entry: `apps/api/main.py`
- Worker entry: `apps/worker/main.py`
- CLI entry: `src/omni_skill_pipeline/cli.py`

## Quick Bootstrap

PowerShell:

```powershell
py -3.11 -m venv .venv
. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

POSIX:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

## OpenAI Variables

- `OPENAI_API_KEY`: required when OpenAI provider calls are enabled.
- `OPENAI_BASE_URL`: optional compatible endpoint override.
- `OMNI_OPENAI_LLM_MODEL`: LLM composer model, default `gpt-4.1`.
- `OMNI_OPENAI_VISION_MODEL`: vision model, default `gpt-4.1-mini`.
- `OMNI_OPENAI_TRANSCRIBE_MODEL`: ASR model, default `gpt-4o-transcribe`.
- `OMNI_OPENAI_TIMEOUT_SECONDS`: provider request timeout in seconds, default `60`.
- `OMNI_OPENAI_RETRY_MAX_ATTEMPTS`: total attempts including the first call, default `3`.
- `OMNI_OPENAI_RETRY_BASE_DELAY_SECONDS`: retry backoff base delay in seconds, default `0.5`.
- `OMNI_OPENAI_CIRCUIT_BREAKER_CONSECUTIVE_FAILURES`: consecutive failure threshold, default `3`.
- `OMNI_OPENAI_CIRCUIT_BREAKER_COOLDOWN_SECONDS`: circuit breaker cooldown in seconds, default `30`.
- `OMNI_OPENAI_FAILURE_BUDGET_MAX_FAILURES`: max failures inside the rolling budget window, default `6`.
- `OMNI_OPENAI_FAILURE_BUDGET_WINDOW_SECONDS`: failure budget window in seconds, default `60`.
- `OMNI_TRANSCRIPTION_LANGUAGE`: optional ASR language hint.

## API Variables

- `OMNI_API_KEY`: optional. When set, `POST /v1/distill/*` and `POST /v1/governance/*` require `X-API-Key` or `Authorization: Bearer <key>`. `GET /healthz` and `GET /v1/templates/skill` remain unauthenticated.
- `OMNI_RATE_LIMIT_REQUESTS`: allowed requests per window. `0` disables rate limiting, default `0`.
- `OMNI_RATE_LIMIT_WINDOW_SECONDS`: rate limit window length in seconds, default `60`.

## API Ops Contract Defaults

- `OMNI_API_KEY` empty: distill and governance POST routes do not require API key auth.
- `OMNI_RATE_LIMIT_REQUESTS=0`: rate limiting is disabled.
- `OMNI_RATE_LIMIT_REQUESTS>0`: requests are counted in a sliding window controlled by `OMNI_RATE_LIMIT_WINDOW_SECONDS`; over-limit responses return `429` and `Retry-After`.
- Unified API errors are documented in `docs/latest/operations/api.md`.

## Tenant Access (GL-08)

- `OMNI_TENANT_ACCESS_JSON`: optional inline tenant access-control JSON payload.
- `OMNI_TENANT_ACCESS_FILE`: optional path to tenant access-control JSON file, used when `OMNI_TENANT_ACCESS_JSON` is empty.
- When tenant access is configured, API enforces tenant key authz/quota on product routes:
  - missing tenant key -> `401`
  - invalid or revoked key -> `403`
  - cross-tenant scope -> `403`
  - tenant quota exceeded -> `429` with `Retry-After`

## Health / Readiness Inputs

- `GET /healthz` currently checks:
  - template path readability (`docs/latest/contracts/SKILL.template.md`)
  - draft directory availability (`skills/drafts/`)
  - required route assembly (`/healthz`, `/v1/templates/skill`, and the five distill routes)
- The current version does not provide separate env overrides for `template_path` or `draft_dir`; they are derived from repo root.
- When any check fails, `/healthz` returns `503` with `status=degraded`.

## Media Variables

- `OMNI_FFMPEG_BIN`: default `ffmpeg`.
- `OMNI_FFPROBE_BIN`: default `ffprobe`.
- `OMNI_TESSERACT_BIN`: default `tesseract`.
- `OMNI_TESSERACT_LANGUAGES`: default `eng+chi_sim`.

## Video Sampling Variables

- `OMNI_KEYFRAME_INTERVAL_SECONDS`: default `8`.
- `OMNI_MAX_KEYFRAMES`: default `6`.
- `OMNI_VIDEO_SCENE_THRESHOLD`: default `0.32`.
- `OMNI_VIDEO_FRAME_DEDUPE_DISTANCE`: default `5`.

## Behavior Variables

- `OMNI_PREFER_LLM_COMPOSER`: default `true`.
- `OMNI_CONTROLLED_TRIAL_REVIEW_MODE`: default `false`. Set to `true` to force all distilled results to `review_required` and prevent auto-publish.
- `OMNI_CONTROLLED_TRIAL_REVIEW_REASON_CODE`: default `controlled_trial_requires_review`; persisted reason code for controlled-trial review enforcement.
- `OMNI_PORTABLE_SKILL_MARKDOWN_LINE_LIMIT`: default `220`, minimum `21`; controls the maximum body length for portable `SKILL.md`, with long evidence moved into `publications/references/`.

## Notes

- `.env.example` lists the baseline configurable variables.
- `docs/latest/contracts/` is the source of truth for templates and schemas.
- `scripts/export_schema.py` exports the schema to `docs/latest/contracts/skill.schema.json`.
- Temporary video/media files are written under `.tmp_omni_media/`; each task cleans its temporary workspace, but the root should still be pruned periodically.

## Postgres Integration Test Variable

- `OMNI_TEST_POSTGRES_DSN`: Postgres DSN used by `tests/test_postgres_repository_integration.py`, `tests/test_dual_write_repository_integration.py`, and `scripts/bench_dual_write.py`.

## GL-06 Artifact Repository Mode

- `OMNI_ARTIFACT_REPOSITORY_MODE`: `file` (default), `postgres`, or `dual_write`.
- `OMNI_POSTGRES_REPOSITORY_DSN`: required when mode is `postgres` or `dual_write`.
- `OMNI_DUAL_WRITE_CONTINUE_ON_SECONDARY_ERROR`: active in `dual_write` mode, default `true`.
- `OMNI_DUAL_WRITE_SECONDARY_PREFIX`: active in `dual_write` mode, default `secondary_`.

Mode semantics:

- `file`: file artifact repository only (`skills/drafts/*`).
- `postgres`: Postgres-first repository.
- `dual_write`: Postgres as primary and file artifacts as secondary debug sidecar for diagnostics and replay.

## GL-06A Local Artifact Encryption

- `OMNI_ARTIFACT_ENCRYPTION_MODE`: empty/off by default. Set to `fernet` to encrypt file-backed artifacts.
- `OMNI_ARTIFACT_ENCRYPTION_KEY`: required when encryption mode is `fernet`; must be a Fernet key.
- `OMNI_ARTIFACT_ENCRYPTION_KEY_ID`: optional key identifier stored in encrypted envelopes, default `default`.

Generate a local key:

```bash
python -c "from omni_skill_pipeline.artifact_crypto import generate_fernet_key; print(generate_fernet_key())"
```

Scope:

- Applies to the local `FileArtifactRepository` artifacts and review queue files.
- Keeps old plaintext artifacts readable when encryption is disabled.
- Requires the same configured key to read encrypted review queue entries.
- Does not provide Vault/KMS integration or automated key rotation.

## Scratch Root Prune Variables

- `OMNI_TMP_MEDIA_ROOT`: scratch-root path for temporary media artifacts, default `.tmp_omni_media`.
- `OMNI_TMP_MEDIA_RETENTION_HOURS`: retention window in hours for prune jobs, default `24`.

## Scratch Root Prune Command

```bash
python scripts/prune_tmp.py --dry-run
python scripts/prune_tmp.py --retention-hours 24
```

## Logging Variables

- `OMNI_LOG_LEVEL`: global runtime log level for API/service/worker, default `INFO`.
- `OMNI_LOG_FORMAT`: `json` or `plain`, default `json`.

## GL-03 Recommended Beta Defaults

For controlled external Beta onboarding:

- Set `OMNI_CONTROLLED_TRIAL_REVIEW_MODE=true`.
- Keep `OMNI_CONTROLLED_TRIAL_REVIEW_REASON_CODE=controlled_trial_requires_review`.
- Configure `OMNI_API_KEY` for partner-facing API environments.
- Set a non-zero rate limit for safety:
  - `OMNI_RATE_LIMIT_REQUESTS=60`
  - `OMNI_RATE_LIMIT_WINDOW_SECONDS=60`
