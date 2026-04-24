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
- `OMNI_TRANSCRIPTION_LANGUAGE`: 可选，ASR language hint

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
