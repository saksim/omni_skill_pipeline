# CLI

## Entry

- CLI module: `src/omni_skill_pipeline/cli.py`
- 推荐前置：先执行 `python -m pip install -r requirements-dev.txt`
- 运行方式：安装后直接使用 `python -m omni_skill_pipeline.cli ...`

如果你选择不安装 editable package，而是直接从源码树运行，再显式设置 `PYTHONPATH=src`。

## Base Pattern

```bash
python -m omni_skill_pipeline.cli <command> ...
```

PowerShell source-tree fallback:

```powershell
$env:PYTHONPATH = "src"
python -m omni_skill_pipeline.cli <command> ...
```

## Commands

### distill-text

```bash
python -m omni_skill_pipeline.cli distill-text \
  --file examples/text_note.md \
  --domain database
```

### distill-audio

```bash
python -m omni_skill_pipeline.cli distill-audio \
  --transcript-path examples/audio_transcript.srt \
  --domain ops
```

### distill-image

```bash
python -m omni_skill_pipeline.cli distill-image \
  --image-path examples/demo_image.png \
  --domain observability
```

### distill-tabular

```bash
python -m omni_skill_pipeline.cli distill-tabular \
  --file examples/demo_timeseries.csv \
  --time-column timestamp \
  --value-column latency_ms \
  --value-column error_rate \
  --entity-column service \
  --domain incident_response
```

### distill-video

```bash
python -m omni_skill_pipeline.cli distill-video \
  --video-path examples/demo_video.mp4 \
  --domain incident_response \
  --max-keyframes 6 \
  --scene-threshold 0.32 \
  --dedupe-distance 5
```

### distill-corpus (multi `--asset`)

```bash
python -m omni_skill_pipeline.cli distill-corpus \
  --name beta-corpus \
  --asset text=examples/text_note.md \
  --asset audio=examples/audio_transcript.srt \
  --publication skill_json \
  --show-publications \
  --tag beta \
  --tag ops \
  --domain operations
```

### distill-corpus (JSON payload)

```bash
python -m omni_skill_pipeline.cli distill-corpus \
  --payload-file examples/corpus_payload.json
```

### export-skill

```bash
python -m omni_skill_pipeline.cli export-skill \
  --bundle skills/drafts/sample-skill-12345678/bundle.json \
  --target codex \
  --output-root .
```

Supported targets:

- `codex` -> `.codex/skills/<skill-name>/SKILL.md`
- `claude-code` -> `.claude/skills/<skill-name>/SKILL.md`
- `opencode` -> `.opencode/skill/<skill-name>/SKILL.md`
- `portable` -> `skills/portable/<skill-name>/SKILL.md`
- `all` -> export every target above in one command

### validate-skill

```bash
python -m omni_skill_pipeline.cli validate-skill \
  --package skills/portable/sample-skill \
  --max-lines 500
```

Exit code contract:

- `0`: package passed usability/safety validation.
- `2`: package failed with explicit `failure_codes` and issue lines.

### run_trial_security_gate.py

```bash
python scripts/run_trial_security_gate.py \
  --bundle skills/drafts/sample-skill-12345678/bundle.json \
  --output docs/current/status/baselines/controlled-trial/trial-security-gate-report.json
```

Exit code contract:

- `0`: trial security gate passed.
- `2`: trial security gate failed with explicit `failure_codes`.

### show-template

```bash
python -m omni_skill_pipeline.cli show-template
```

## Notes

- `export-skill` exports an existing `bundle.json` to the selected target layout and writes `agent_skill_package.json`.
- `export-skill` now enforces CBT-13 trial security gate before writing any target layout.
- `distill-corpus` 默认打印所选 publication 路径（默认 `skill_markdown`，可通过 `--publication` 选择）。
- `distill-corpus` 会打印 `review_status`、`decision`、`review_task_id` 与 `reason_codes`，便于接 review queue。
- 使用 `--show-publications` 可额外打印 `selected_publication` 与 `available_publications`。
- 默认输出目录由 `Settings.draft_dir` 决定，当前默认指向 `skills/drafts/`。
- 目标与受众可通过 `--goal-type`、`--audience`、`--rigor`、`--granularity`、`--domain` 调整。
- `distill-corpus` 支持两种输入：
  - 多次 `--asset`（格式：`modality=source_uri`）
  - `--payload-file` 或 `--payload-json`（完整 `CorpusDistillRequest` JSON）
