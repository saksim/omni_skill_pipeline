# 环境变量

## 基线

运行时只需要干净的 Python 3.11 或 3.12 环境、可选媒体二进制工具，以及在启用 provider 时提供对应凭证。文档中不要硬编码绝对解释器路径。

## 运行时

- Python：`3.11` 或 `3.12`。`v0.2.x` 不声明支持 Python 3.13。
- 安装模式：优先使用隔离虚拟环境。
- Package root：`src/omni_skill_pipeline/`
- API 入口：`apps/api/main.py`
- Worker 入口：`apps/worker/main.py`
- CLI 入口：`src/omni_skill_pipeline/cli.py`

## 快速初始化

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

## OpenAI 变量

- `OPENAI_API_KEY`：启用 OpenAI provider 调用时必填。
- `OPENAI_BASE_URL`：可选兼容 endpoint 覆盖。
- `OMNI_OPENAI_LLM_MODEL`：LLM composer model，默认 `gpt-4.1`。
- `OMNI_OPENAI_VISION_MODEL`：vision model，默认 `gpt-4.1-mini`。
- `OMNI_OPENAI_TRANSCRIBE_MODEL`：ASR model，默认 `gpt-4o-transcribe`。
- `OMNI_OPENAI_TIMEOUT_SECONDS`：provider 请求超时时间，默认 `60` 秒。
- `OMNI_OPENAI_RETRY_MAX_ATTEMPTS`：总尝试次数，包含首次调用，默认 `3`。
- `OMNI_OPENAI_RETRY_BASE_DELAY_SECONDS`：retry backoff 基础延迟，默认 `0.5` 秒。
- `OMNI_OPENAI_CIRCUIT_BREAKER_CONSECUTIVE_FAILURES`：熔断连续失败阈值，默认 `3`。
- `OMNI_OPENAI_CIRCUIT_BREAKER_COOLDOWN_SECONDS`：熔断 cooldown，默认 `30` 秒。
- `OMNI_OPENAI_FAILURE_BUDGET_MAX_FAILURES`：滚动窗口内最大失败数，默认 `6`。
- `OMNI_OPENAI_FAILURE_BUDGET_WINDOW_SECONDS`：failure budget 窗口，默认 `60` 秒。
- `OMNI_TRANSCRIPTION_LANGUAGE`：可选 ASR language hint。

## API 变量

- `OMNI_API_KEY`：可选。设置后，`POST /v1/distill/*` 和 `POST /v1/governance/*` 需要 `X-API-Key` 或 `Authorization: Bearer <key>`。`GET /healthz` 和 `GET /v1/templates/skill` 仍不需要认证。
- `OMNI_RATE_LIMIT_REQUESTS`：每个窗口允许的请求数。`0` 表示禁用 rate limiting，默认 `0`。
- `OMNI_RATE_LIMIT_WINDOW_SECONDS`：rate limit 窗口长度，默认 `60` 秒。

## API 操作契约默认值

- `OMNI_API_KEY` 为空：distill 和 governance POST 路由不要求 API key auth。
- `OMNI_RATE_LIMIT_REQUESTS=0`：rate limiting 关闭。
- `OMNI_RATE_LIMIT_REQUESTS>0`：请求按 `OMNI_RATE_LIMIT_WINDOW_SECONDS` 控制的滑动窗口计数；超过限制返回 `429` 和 `Retry-After`。
- 统一 API error 见 `docs/latest/operations/api.md`。

## Tenant Access (GL-08)

- `OMNI_TENANT_ACCESS_JSON`：可选 inline tenant access-control JSON。
- `OMNI_TENANT_ACCESS_FILE`：可选 tenant access-control JSON 文件路径，当 `OMNI_TENANT_ACCESS_JSON` 为空时使用。
- 配置 tenant access 后，API 会对产品路由执行 tenant key authz/quota：
  - 缺 tenant key -> `401`
  - key 无效或 revoked -> `403`
  - cross-tenant scope -> `403`
  - tenant quota exceeded -> `429`，带 `Retry-After`

## Health / Readiness 输入

- `GET /healthz` 当前检查：
  - template path 可读性：`docs/latest/contracts/SKILL.template.md`
  - draft directory 可用性：`skills/drafts/`
  - 必要路由装配：`/healthz`、`/v1/templates/skill` 和五个 distill routes
- 当前版本没有单独的 `template_path` 或 `draft_dir` env override；它们从 repo root 推导。
- 任一检查失败时，`/healthz` 返回 `503`，并带 `status=degraded`。

## 媒体变量

- `OMNI_FFMPEG_BIN`：默认 `ffmpeg`。
- `OMNI_FFPROBE_BIN`：默认 `ffprobe`。
- `OMNI_TESSERACT_BIN`：默认 `tesseract`。
- `OMNI_TESSERACT_LANGUAGES`：默认 `eng+chi_sim`。

## 视频采样变量

- `OMNI_KEYFRAME_INTERVAL_SECONDS`：默认 `8`。
- `OMNI_MAX_KEYFRAMES`：默认 `6`。
- `OMNI_VIDEO_SCENE_THRESHOLD`：默认 `0.32`。
- `OMNI_VIDEO_FRAME_DEDUPE_DISTANCE`：默认 `5`。

## 行为变量

- `OMNI_PREFER_LLM_COMPOSER`：默认 `true`。
- `OMNI_CONTROLLED_TRIAL_REVIEW_MODE`：默认 `false`。设为 `true` 后，所有 distilled result 都会强制进入 `review_required`，避免 auto-publish。
- `OMNI_CONTROLLED_TRIAL_REVIEW_REASON_CODE`：默认 `controlled_trial_requires_review`；用于持久化 controlled-trial review enforcement 的 reason code。
- `OMNI_PORTABLE_SKILL_MARKDOWN_LINE_LIMIT`：默认 `220`，最小 `21`；控制 portable `SKILL.md` body 最大长度，长证据会移动到 `publications/references/`。

## 说明

- `.env.example` 列出基线可配置变量。
- `docs/latest/contracts/` 是 templates 和 schemas 的来源。
- `scripts/export_schema.py` 会导出 schema 到 `docs/latest/contracts/skill.schema.json`。
- 临时视频/媒体文件写入 `.tmp_omni_media/`；单个任务会清理自身临时 workspace，但 root 仍应定期 prune。

## Postgres 集成测试变量

- `OMNI_TEST_POSTGRES_DSN`：供 `tests/test_postgres_repository_integration.py`、`tests/test_dual_write_repository_integration.py` 和 `scripts/bench_dual_write.py` 使用的 Postgres DSN。

## GL-06 Artifact Repository Mode

- `OMNI_ARTIFACT_REPOSITORY_MODE`：`file` 默认、`postgres` 或 `dual_write`。
- `OMNI_POSTGRES_REPOSITORY_DSN`：当 mode 为 `postgres` 或 `dual_write` 时必填。
- `OMNI_DUAL_WRITE_CONTINUE_ON_SECONDARY_ERROR`：仅 `dual_write` mode 生效，默认 `true`。
- `OMNI_DUAL_WRITE_SECONDARY_PREFIX`：仅 `dual_write` mode 生效，默认 `secondary_`。

模式语义：

- `file`：只使用 file artifact repository，路径为 `skills/drafts/*`。
- `postgres`：Postgres-first repository。
- `dual_write`：Postgres 作为 primary，file artifact 作为 secondary debug sidecar，用于诊断和 replay。

## GL-06A 本地 Artifact 加密

- `OMNI_ARTIFACT_ENCRYPTION_MODE`：默认空/off。设为 `fernet` 后加密 file-backed artifact。
- `OMNI_ARTIFACT_ENCRYPTION_KEY`：当 encryption mode 为 `fernet` 时必填，必须是 Fernet key。
- `OMNI_ARTIFACT_ENCRYPTION_KEY_ID`：可选 key identifier，会写入 encrypted envelope，默认 `default`。
- 操作手册：`docs/latest/operations/runbooks/artifact-encryption.md`。

生成本地 key：

```bash
python -c "from omni_skill_pipeline.artifact_crypto import generate_fernet_key; print(generate_fernet_key())"
```

不要提交生成的 key。请把 key 放在本地 secret store、CI secret 或密码管理器中。后续读取加密 artifact 时需要同一个 key。

范围：

- 作用于本地 `FileArtifactRepository` artifact 和 review queue 文件。
- 加密关闭时，旧 plaintext artifact 仍可读。
- 读取加密 review queue entry 需要配置同一个 key。
- 不提供 Vault/KMS 集成或自动 key rotation。

## Scratch Root Prune 变量

- `OMNI_TMP_MEDIA_ROOT`：临时媒体 artifact root，默认 `.tmp_omni_media`。
- `OMNI_TMP_MEDIA_RETENTION_HOURS`：prune 保留窗口，默认 `24` 小时。

## Scratch Root Prune 命令

```bash
python scripts/prune_tmp.py --dry-run
python scripts/prune_tmp.py --retention-hours 24
```

## 日志变量

- `OMNI_LOG_LEVEL`：API/service/worker 全局日志级别，默认 `INFO`。
- `OMNI_LOG_FORMAT`：`json` 或 `plain`，默认 `json`。

## GL-03 推荐 Beta 默认值

用于 controlled external Beta onboarding：

- 设置 `OMNI_CONTROLLED_TRIAL_REVIEW_MODE=true`。
- 保持 `OMNI_CONTROLLED_TRIAL_REVIEW_REASON_CODE=controlled_trial_requires_review`。
- 面向 partner 的 API 环境应配置 `OMNI_API_KEY`。
- 为安全性设置非零 rate limit：
  - `OMNI_RATE_LIMIT_REQUESTS=60`
  - `OMNI_RATE_LIMIT_WINDOW_SECONDS=60`
