# Environment

## Runtime

- Python interpreter: `D:\code_environment\anaconda_all_css\py311\python.exe`
- Package root: `src/omni_skill_pipeline/`
- API entry: `apps/api/main.py`
- Worker entry: `apps/worker/main.py`
- CLI entry: `src/omni_skill_pipeline/cli.py`

## OpenAI Variables

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OMNI_OPENAI_LLM_MODEL`
- `OMNI_OPENAI_VISION_MODEL`
- `OMNI_OPENAI_TRANSCRIBE_MODEL`
- `OMNI_TRANSCRIPTION_LANGUAGE`

## Media Variables

- `OMNI_FFMPEG_BIN`
- `OMNI_FFPROBE_BIN`
- `OMNI_TESSERACT_BIN`
- `OMNI_TESSERACT_LANGUAGES`

## Video Sampling Variables

- `OMNI_KEYFRAME_INTERVAL_SECONDS`
- `OMNI_MAX_KEYFRAMES`
- `OMNI_VIDEO_SCENE_THRESHOLD`
- `OMNI_VIDEO_FRAME_DEDUPE_DISTANCE`

## Composer Variable

- `OMNI_PREFER_LLM_COMPOSER`

## Notes

- `docs/current/contracts/` is the source of truth for template and schema files.
- `scripts/export_skill_schema.py` exports into `docs/current/contracts/skill.schema.json`.
- Video temporary files are staged under `.tmp_omni_media/`.