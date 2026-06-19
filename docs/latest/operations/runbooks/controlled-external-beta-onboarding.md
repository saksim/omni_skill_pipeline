# Controlled External Beta Onboarding (GL-03)

## Goal

Use this runbook to execute one controlled external Beta loop without repository-internal knowledge.

This runbook does not declare GA. It is only for controlled external Beta pre-production operation.

## Scope

- Manifest validation
- Distillation via API or CLI
- Review queue operation
- Skill export and usability validation
- Trial security gate
- Trial metrics collection
- Launch readiness gate decision check

## Prerequisites

- Python 3.11 environment with `requirements-dev.txt` installed
- Optional provider credentials:
  - `OPENAI_API_KEY`
- API contract variables:
  - `OMNI_API_KEY` (if authentication enabled)
  - `OMNI_RATE_LIMIT_REQUESTS`
  - `OMNI_RATE_LIMIT_WINDOW_SECONDS`
- Controlled trial review defaults:
  - `OMNI_CONTROLLED_TRIAL_REVIEW_MODE=true`
  - `OMNI_CONTROLLED_TRIAL_REVIEW_REASON_CODE=controlled_trial_requires_review`

Reference docs:

- `docs/latest/operations/env.md`
- `docs/latest/operations/api.md`
- `docs/latest/operations/cli.md`

## Step 1: Validate Trial Manifest

Use one of the existing trial manifests or your own manifest using the CBT-02 contract.

```bash
python scripts/validate_manifest.py \
  --manifest docs/working/status/baselines/trial-manifests/trial-sample-mixed-corpus.example.json \
  --output -
```

Expected result: report status is pass.

## Step 2: Distill (CLI Path)

Option A: use `--asset` pairs.

```bash
python -m omni_skill_pipeline.cli distill-corpus \
  --name gl03-beta-loop \
  --asset text=examples/trial/text/slow-query-notes.md \
  --asset image=examples/trial/image/service-latency-dashboard.png \
  --asset audio=examples/trial/mixed/incident-review-transcript.md \
  --publication skill_markdown \
  --show-publications \
  --tag controlled-beta \
  --domain incident_response
```

Option B: use a JSON payload file.

```bash
python -m omni_skill_pipeline.cli distill-corpus \
  --payload-file examples/beta/corpus_payload.example.json \
  --publication skill_markdown \
  --show-publications
```

Record these fields from CLI output:

- `review_status`
- `decision`
- `review_task_id`
- `reason_codes`

## Step 3: Distill (API Path Alternative)

Start API:

```bash
python -m uvicorn apps.api.main:app --reload
```

Submit corpus payload:

```bash
curl -sS -X POST "http://127.0.0.1:8000/v1/distill/corpus" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${OMNI_API_KEY}" \
  --data-binary @examples/beta/corpus_payload.example.json
```

If API key is not enabled, remove `X-API-Key` header.

## Step 4: Operate Review Queue

List queue:

```bash
curl -sS "http://127.0.0.1:8000/v1/review/queue?queue_status=pending&limit=20"
```

Claim one task:

```bash
curl -sS -X POST "http://127.0.0.1:8000/v1/review/queue/claim" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${OMNI_API_KEY}" \
  -d "{\"consumer\":\"beta-reviewer\"}"
```

Close one task:

```bash
curl -sS -X POST "http://127.0.0.1:8000/v1/review/queue/<review_task_id>/close" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${OMNI_API_KEY}" \
  -d "{\"status\":\"published\",\"closed_by\":\"beta-reviewer\",\"review_notes\":\"approved for controlled beta\"}"
```

## Step 5: Export Skill Package

Use the generated `bundle.json` path from `skills/drafts/<skill-id>/bundle.json`.

```bash
python -m omni_skill_pipeline.cli export-skill \
  --bundle skills/drafts/<skill-id>/bundle.json \
  --target portable \
  --output-root .
```

Expected output includes:

- `target=portable`
- package path under `skills/portable/<skill-name>/`

## Step 6: Validate Package Usability

```bash
python -m omni_skill_pipeline.cli validate-skill \
  --package skills/portable/<skill-name> \
  --max-lines 500
```

Expected exit code:

- `0` pass
- `2` failure with `failure_codes`

## Step 7: Run Trial Security Gate Explicitly

`export-skill` already enforces this gate, but for audit evidence run it explicitly.

```bash
python scripts/trial_security.py \
  --bundle skills/drafts/<skill-id>/bundle.json \
  --output docs/working/status/baselines/controlled-trial/trial-security-gate-report.json
```

Expected exit code:

- `0` pass
- `2` fail

## Step 8: Collect Trial Metrics

```bash
python scripts/trial_metrics.py \
  --manifest docs/working/status/baselines/controlled-trial/trial-metrics-manifest.json \
  --output docs/working/status/baselines/controlled-trial/trial-metrics-report.json \
  --summary-output docs/working/status/baselines/controlled-trial/trial-metrics-summary.md \
  --print-summary
```

Cost visibility is read from the `cost_placeholder` section in metrics report.  
Until real provider billing integration is added, this is an operator-declared placeholder and must be treated as such.

## Step 9: Check Launch Readiness Decision

```bash
python scripts/launch_gate.py \
  --output - \
  --summary-output - \
  --max-evidence-age-hours 0 \
  --print-json
```

Allowed decision states:

- `HOLD`
- `READY_FOR_CONTROLLED_BETA`
- `READY_FOR_GA_REVIEW`
- `READY_FOR_PLATFORM_BETA`

Do not claim GA from dry-run, relaxed flags, or skipped evidence checks.

## Onboarding Checklist (Friendly Customer)

- Define owner, review owner, and approved data sensitivity for each trial manifest.
- Confirm no regulated data, credentials, or unsanitized customer PII in trial assets.
- Confirm `OMNI_CONTROLLED_TRIAL_REVIEW_MODE=true`.
- Run manifest validation and keep report output.
- Run at least one corpus distillation loop and capture `review_task_id`.
- Complete review queue close operation with reviewer identity and notes.
- Export package and run `validate-skill`.
- Record security gate report and trial metrics report.
- Run launch readiness gate and record the decision.
- Communicate status only as controlled external Beta readiness level.

## Incident / Escalation

- If `validate-skill` or trial security gate fails: stop publication, open remediation task, rerun from Step 5.
- If launch readiness gate returns `HOLD`: do not claim Beta-ready/GA-ready; resolve failed checks first.
- If provider/runtime failures spike: pause loop expansion and follow `docs/latest/operations/runbooks/launch-beta.md`.
