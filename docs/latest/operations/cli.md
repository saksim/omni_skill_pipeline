# CLI

## Entry

- CLI module: `src/omni_skill_pipeline/cli.py`
- Install dependencies first: `python -m pip install -r requirements-dev.txt`
- Invoke commands through: `python -m omni_skill_pipeline.cli ...`

If running directly from source tree without editable install, set `PYTHONPATH=src`.

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
  --payload-file examples/beta/corpus_payload.example.json
```

Official GL-03 sample payload:

- `examples/beta/corpus_payload.example.json`

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

### trial_security.py

```bash
python scripts/trial_security.py \
  --bundle skills/drafts/sample-skill-12345678/bundle.json \
  --output docs/working/status/baselines/controlled-trial/trial-security-gate-report.json
```

Exit code contract:

- `0`: trial security gate passed.
- `2`: trial security gate failed with explicit `failure_codes`.

### show-template

```bash
python -m omni_skill_pipeline.cli show-template
```

### review-queue

```bash
python -m omni_skill_pipeline.cli review-queue \
  --action list \
  --queue-status pending \
  --limit 20
```

```bash
python -m omni_skill_pipeline.cli review-queue \
  --action approve \
  --review-task-id <review-task-id> \
  --reviewer qa-lead \
  --reason-code SAFE \
  --review-notes "manual review passed" \
  --reviewer-edits-json '{"skill_markdown_patch":"none"}'
```

### governance-report

```bash
python -m omni_skill_pipeline.cli governance-report \
  --organization-id beta-org \
  --project-id ops-team \
  --include-cost-entries \
  --include-audit-events \
  --include-deletion-records \
  --limit 200
```

### record-deletion

```bash
python -m omni_skill_pipeline.cli record-deletion \
  --organization-id beta-org \
  --project-id ops-team \
  --resource-type skill_package \
  --resource-id pkg-20260526-001 \
  --actor governance-operator \
  --reason "customer offboarding data purge"
```

### upsert-retention-policy

```bash
python -m omni_skill_pipeline.cli upsert-retention-policy \
  --organization-id beta-org \
  --project-id ops-team \
  --policy-type artifact_retention \
  --retention-days 30 \
  --deletion-mode soft_delete \
  --updated-by governance-operator
```

## Notes

- `export-skill` exports an existing `bundle.json` to the selected target layout and writes `agent_skill_package.json`.
- `export-skill` enforces CBT-13 trial security gate before writing any target layout.
- `distill-corpus` prints `review_status`, `decision`, `review_task_id`, and `reason_codes` for review-queue routing.
- `review-queue` supports `list`, `claim`, `close`, `approve`, `reject`, and `needs-rework` operational actions.
- `review-queue approve|reject|needs-rework` persists reviewer, decision, reason codes, notes, and reviewer edits without manual artifact editing.
- `governance-report` returns scoped cost/audit/deletion/retention evidence for launch governance reviews.
- `record-deletion` appends tenant/project deletion records and matching audit trail evidence.
- `upsert-retention-policy` manages tenant/project retention policy records for governance checks.
- Use `--show-publications` to print `selected_publication` and `available_publications`.
- Default draft output root is controlled by `Settings.draft_dir` (currently `skills/drafts/`).
- Goal tuning is available via `--goal-type`, `--audience`, `--rigor`, `--granularity`, and `--domain`.
- `distill-corpus` supports both `--asset modality=source_uri` and `--payload-file` / `--payload-json`.
- Controlled external Beta onboarding flow: `docs/latest/operations/runbooks/controlled-external-beta-onboarding.md`.
