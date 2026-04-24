# Environment

## 判词

运行前只需要一个干净的 Python 3.11 环境、可选 media binaries 和按需配置的 OpenAI credentials；不要把解释器绝对路径写死在文档里。

## Runtime

- Python: `3.11+`
- 安装方式：优先使用 isolated virtual environment
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

- `OPENAI_API_KEY`: 启用 OpenAI provider 所需
- `OPENAI_BASE_URL`: 可选，自定义兼容端点
- `OMNI_OPENAI_LLM_MODEL`: LLM composer model，默认 `gpt-4.1`
- `OMNI_OPENAI_VISION_MODEL`: Vision model，默认 `gpt-4.1-mini`
- `OMNI_OPENAI_TRANSCRIBE_MODEL`: ASR model，默认 `gpt-4o-transcribe`
- `OMNI_OPENAI_TIMEOUT_SECONDS`: OpenAI provider request timeout in seconds，默认 `60`
- `OMNI_OPENAI_RETRY_MAX_ATTEMPTS`: OpenAI provider 总尝试次数（含首次调用），默认 `3`
- `OMNI_OPENAI_RETRY_BASE_DELAY_SECONDS`: OpenAI provider 退避基数秒数，默认 `0.5`（指数退避）
- `OMNI_TRANSCRIPTION_LANGUAGE`: 可选，ASR language hint

## API Variables

- `OMNI_API_KEY`: 可选。设置后仅 `POST /v1/distill/*` 端点强制校验 `X-API-Key` 或 `Authorization: Bearer <key>`；`GET /healthz` 与 `GET /v1/templates/skill` 保持免鉴权。
- `OMNI_RATE_LIMIT_REQUESTS`: 每个窗口允许请求数。`0` 表示关闭限流，默认 `0`。
- `OMNI_RATE_LIMIT_WINDOW_SECONDS`: 限流窗口秒数，默认 `60`。

## API Ops Contract Defaults

- `OMNI_API_KEY` 为空：distill 接口不鉴权。
- `OMNI_RATE_LIMIT_REQUESTS=0`：限流关闭。
- `OMNI_RATE_LIMIT_REQUESTS>0`：按 `OMNI_RATE_LIMIT_WINDOW_SECONDS` 形成滑动窗口，超限返回 `429` 与 `Retry-After` header。
- 统一错误体见 `docs/current/operations/api.md` 的 `Error Contract`。

## Health / Readiness Inputs

- `GET /healthz` 当前检查三项：
  - template path readability（`docs/current/contracts/SKILL.template.md`）
  - draft directory availability（`skills/drafts/`）
  - required route assembly（`/healthz`、`/v1/templates/skill`、五个 distill 路由）
- 当前版本未提供独立 env 覆盖 `template_path`/`draft_dir`；它们由 repo root 派生。
- 当任一检查失败时，`/healthz` 返回 `503` 与 `status=degraded`。

## Media Variables

- `OMNI_FFMPEG_BIN`: 默认 `ffmpeg`
- `OMNI_FFPROBE_BIN`: 默认 `ffprobe`
- `OMNI_TESSERACT_BIN`: 默认 `tesseract`
- `OMNI_TESSERACT_LANGUAGES`: 默认 `eng+chi_sim`

## Video Sampling Variables

- `OMNI_KEYFRAME_INTERVAL_SECONDS`: 默认 `8`
- `OMNI_MAX_KEYFRAMES`: 默认 `6`
- `OMNI_VIDEO_SCENE_THRESHOLD`: 默认 `0.32`
- `OMNI_VIDEO_FRAME_DEDUPE_DISTANCE`: 默认 `5`

## Behavior Variable

- `OMNI_PREFER_LLM_COMPOSER`: 默认 `true`

## Notes

- `.env.example` 列出了当前可配置变量的基线模板。
- `docs/current/contracts/` 是模板与 schema 的真相源。
- `scripts/export_skill_schema.py` 会导出到 `docs/current/contracts/skill.schema.json`。
- 视频临时文件会落到 `.tmp_omni_media/`；每次任务的临时工作目录会被清理，但根目录仍建议定期 prune。

## Scratch Root Prune Variables

- `OMNI_TMP_MEDIA_ROOT`: scratch-root path for temporary media artifacts (default: `.tmp_omni_media`).
- `OMNI_TMP_MEDIA_RETENTION_HOURS`: retention window in hours for prune jobs (default: `24`).

## Scratch Root Prune Command

```bash
python scripts/prune_tmp_media.py --dry-run
python scripts/prune_tmp_media.py --retention-hours 24
```

## Logging Variables

- `OMNI_LOG_LEVEL`: global runtime log level for API/service/worker (default: `INFO`).
- `OMNI_LOG_FORMAT`: `json` or `plain` (default: `json`).
