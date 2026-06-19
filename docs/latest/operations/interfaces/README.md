# Operation Interfaces

This document lists the current operational interfaces and where engineers
should look before running or changing them.

## CLI

Entry:

```bash
python -m omni_skill_pipeline.cli <command>
```

Primary commands:

- `show-template`
- `distill-text`
- `distill-audio`
- `distill-image`
- `distill-tabular`
- `distill-video`
- `distill-corpus`
- `export-skill`
- `validate-skill`
- `review-queue`
- `governance-report`
- `record-deletion`
- `upsert-retention-policy`

Manual: `docs/latest/operations/cli.md`.

## API

Entry:

```bash
python -m uvicorn apps.api.main:app --reload
```

Primary routes:

- `GET /healthz`
- `GET /v1/templates/skill`
- `POST /v1/distill/text`
- `POST /v1/distill/audio`
- `POST /v1/distill/image`
- `POST /v1/distill/tabular`
- `POST /v1/distill/video`
- `POST /v1/distill/corpus`
- review queue routes
- governance routes

Manual: `docs/latest/operations/api.md`.

## Worker

Entry:

```bash
python -m omni_skill_pipeline.worker
```

Use the worker for queued distillation/review/publication tasks when the
operator needs filesystem queue semantics instead of direct CLI/API calls.

Manual: `docs/latest/operations/worker.md`.

## Review Queue

CLI examples:

```bash
python -m omni_skill_pipeline.cli review-queue --action list --queue-status pending --limit 20
python -m omni_skill_pipeline.cli review-queue --action claim --consumer reviewer-1
python -m omni_skill_pipeline.cli review-queue --action approve --review-task-id <id> --reviewer reviewer-1
```

Encrypted queue files are supported when `OMNI_ARTIFACT_ENCRYPTION_MODE=fernet`
and the correct key is configured.

Manuals:

- `docs/latest/operations/cli.md`
- `docs/latest/operations/runbooks/artifact-encryption.md`

## Release Artifacts

Release workflow:

```text
.github/workflows/release.yml
```

Generated release pack:

- source archive
- wheel
- `coverage.xml`
- `release-manifest.json`
- `release-summary.md`
- `SHA256SUMS`

Consumer smoke:

```bash
python scripts/release_consumer_smoke.py --release-dir <release-dir> --expected-release-id <release-tag>
```

Manual: `docs/latest/operations/runbooks/github-release-workflow.md`.

## Gate Interfaces

- Internal dogfood gate:
  `python scripts/internal_launch_gate.py --output - --summary-output - --print-json`
- External launch gate:
  `python scripts/launch_gate.py --output - --summary-output - --print-json`
- Release switch:
  `python scripts/release_switch.py ...`
- Document sync:
  `python scripts/doc_sync.py --output -`

Internal dogfood readiness and external launch readiness are separate claims.
Do not use an internal `READY_FOR_INTERNAL_DOGFOOD` result as an external launch
approval.
