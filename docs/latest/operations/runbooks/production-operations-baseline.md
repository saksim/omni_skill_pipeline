# Production Operations Baseline

## Verdict

This runbook defines the GL-05 production operations baseline for single-team GA review preparation.
It is not a GA declaration. It is an evidence-producing operations workflow bound to strict release and launch gates.

## Scope

- Target: single-team production-like operation with strict release evidence.
- Applies to: deploy, validate, rollback, backup, restore, incident response, logs, alerts, and evidence collection.
- Gate policy: Linux validation remains mandatory for launch claims; CI/container evidence is accepted when Linux host access is limited.

## Preconditions

- Runtime image is buildable and launchable (`omni-skill-pipeline:beta` or equivalent pinned tag).
- Required secrets are managed outside image layers (`OPENAI_API_KEY`, optional `OMNI_API_KEY`).
- Baseline docs are present:
  - `docs/latest/operations/runbooks/github-release-workflow.md`
  - `docs/latest/operations/runbooks/docker-zero-to-release.md`
  - `docs/latest/operations/runbooks/launch-beta.md`
  - this document

## Publication Workflow

The GitHub Actions `Release` workflow is the publication layer:

- push to `main`: produces a release candidate artifact pack
- push a `v*` tag: publishes a GitHub Release
- manual `workflow_dispatch`: can publish a GitHub Release when `publish_github_release=true` and `release_tag` is supplied

The release pack contains source archive, Python wheel, coverage XML, manifest, summary, and checksums.

This is not a replacement for runtime validation. Use it to hand off an immutable build candidate, then run the deploy workflow below for container/API acceptance.

## Deploy Workflow

1. Build and smoke-check container image:

```bash
python scripts/container_smoke.py --image-tag omni-skill-pipeline:beta --port 18000
```

2. Start runtime service with explicit runtime env:

```bash
docker run --rm -d \
  --name omni-skill-beta \
  -p 8000:8000 \
  --env-file .env.runtime \
  -v omni_skill_drafts:/app/skills/drafts \
  -v omni_skill_published:/app/skills/published \
  -v omni_skill_tmp_media:/app/.tmp_omni_media \
  omni-skill-pipeline:beta
```

3. Verify live readiness:

```bash
curl -fsS http://127.0.0.1:8000/healthz
```

## Docker Readiness Workflow

Static Docker readiness verifies the runtime image contract, build-context hygiene, container smoke script, CI smoke evidence wiring, and operations docs:

```bash
python scripts/docker_readiness.py --print-json
```

Strict Docker readiness requires live non-dry-run evidence from `container_smoke.py`, including image build, image size, CLI smoke, container run, `/healthz`, logs, and cleanup, then explicit launch gate enforcement:

```bash
python scripts/container_smoke.py --image-tag omni-skill-pipeline:beta --port 18000
python scripts/docker_readiness.py --require-live-evidence --fail-on-blocked --print-json
python scripts/launch_gate.py --require-docker-readiness --docker-readiness-report docs/working/status/baselines/docker-readiness-report.json --print-json
```

Do not count `--dry-run`, `--skip-build`, or `--skip-run` container smoke output as Docker readiness evidence.

## Kubernetes Deploy Workflow

Kubernetes is a P2 productionization path and is not required for the internal dogfood release. The repository `k8s/` directory provides the minimum deployment, service, ingress, configmap, secret-reference, probe, and HPA baseline; runtime secrets must be provisioned outside the repository.

Static manifest readiness:

```bash
python scripts/k8s_readiness.py --print-json
```

Cluster validation requires real kubectl evidence:

```bash
kubectl apply --dry-run=server -f k8s/
kubectl rollout status deployment/omni-skill-pipeline -n omni-skill-pipeline
kubectl logs deployment/omni-skill-pipeline -n omni-skill-pipeline --tail=200
python scripts/k8s_readiness.py --require-cluster-evidence --fail-on-blocked --print-json
```

The strict `k8s_readiness.py` mode must not pass unless external cluster evidence records server dry-run, rollout, health probe, log inspection, and secret-reference validation.

## Validation Workflow

Run strict validation evidence before any launch claim:

```bash
python scripts/release_gate.py --python python3 --output docs/working/status/baselines/e13-release-gate-validation-plan.json
python scripts/doc_sync.py --output docs/working/status/baselines/e13-doc-sync-check-report.json
python scripts/ops_evidence.py --output docs/working/status/baselines/operations-readiness-report.json --summary-output docs/working/status/baselines/operations-readiness-summary.md
python scripts/docker_readiness.py --output docs/working/status/baselines/docker-readiness-report.json --summary-output docs/working/status/baselines/docker-readiness-summary.md
python scripts/k8s_readiness.py --output docs/working/status/baselines/k8s-readiness-report.json --summary-output docs/working/status/baselines/k8s-readiness-summary.md
python scripts/observability_readiness.py --output docs/working/status/baselines/observability-readiness-report.json --summary-output docs/working/status/baselines/observability-readiness-summary.md
python scripts/ci_evidence.py --evidence-dir docs/working/status/baselines/ci-matrix --fail-on-blocked --print-json
python scripts/launch_gate.py --require-ci-evidence --ci-evidence-report docs/working/status/baselines/ci-matrix/ci_evidence_report.json --output docs/working/status/baselines/broad-launch-readiness-report.json --summary-output docs/working/status/baselines/broad-launch-readiness-summary.md
```

Decision rules:

- If release gate or launch readiness is `HOLD`, stop launch expansion and remediate.
- The strict launch gate must read `docs/working/status/baselines/ci-matrix/ci_evidence_report.json` before CI-backed launch readiness can pass.
- Do not use dry-run, relaxed flags, or skipped checks for launch claims.

## Rollback Workflow

Trigger rollback if any of the following happens:

- `healthz` remains unavailable or degraded beyond allowed SLO.
- Core distill endpoints return sustained 5xx.
- Auth/rate-limit behavior drifts from contract.
- Release/launch gate evidence degrades to `HOLD`.

Rollback commands:

```bash
docker logs --tail 300 omni-skill-beta > rollback-omni-skill-beta.log
docker rm -f omni-skill-beta
docker run --rm -d --name omni-skill-beta -p 8000:8000 --env-file .env.runtime omni-skill-pipeline:stable
curl -fsS http://127.0.0.1:8000/healthz
```

## Backup Workflow

Back up mutable operation volumes before risky change windows:

```bash
mkdir -p backups
docker run --rm -v omni_skill_drafts:/from -v "${PWD}/backups:/to" alpine sh -c "tar -czf /to/omni_skill_drafts_$(date -u +%Y%m%dT%H%M%SZ).tar.gz -C /from ."
docker run --rm -v omni_skill_published:/from -v "${PWD}/backups:/to" alpine sh -c "tar -czf /to/omni_skill_published_$(date -u +%Y%m%dT%H%M%SZ).tar.gz -C /from ."
docker run --rm -v omni_skill_tmp_media:/from -v "${PWD}/backups:/to" alpine sh -c "tar -czf /to/omni_skill_tmp_media_$(date -u +%Y%m%dT%H%M%SZ).tar.gz -C /from ."
```

Minimum backup record:

- backup timestamp (UTC)
- volume name
- archive filename
- operator

## Restore Workflow

Restore a specific backup archive into an empty target volume:

```bash
docker run --rm -v omni_skill_published:/to -v "${PWD}/backups:/from" alpine sh -c "rm -rf /to/* && tar -xzf /from/<archive>.tar.gz -C /to"
```

Post-restore checks:

```bash
docker run --rm -v omni_skill_published:/to alpine sh -c "ls -la /to | head"
curl -fsS http://127.0.0.1:8000/healthz
```

## Incident Response Workflow

1. Detect and classify incident severity (`sev-1` to `sev-3`).
2. Stabilize service first (rollback or isolate noisy workflows).
3. Capture evidence:
   - `docker logs`
   - relevant gate outputs under `docs/working/status/baselines/`
   - impacted run/report ids
4. Open remediation owner + due time.
5. Re-run validation workflow after remediation.

## Log Inspection Workflow

Primary commands:

```bash
docker logs --tail 300 omni-skill-beta
docker logs omni-skill-beta | grep -E '"event":"(api_request_completed|distill_start|distill_complete)"'
docker logs omni-skill-beta | grep -E '"status_code":(4|5)[0-9]{2}'
```

Escalate if:

- repeated 5xx without recovery
- repeated provider unavailability
- repeated review queue persistence errors

## Alert Workflow

Minimum operator alerts for GL-05:

- availability alert: `healthz` probe failure
- error-rate alert: rolling 5xx ratio above threshold
- gate-drift alert: latest release/launch/ops readiness evidence switched to fail/HOLD

Alert handling sequence:

1. Acknowledge alert.
2. Run incident response workflow.
3. Record resolution with root cause and prevention action.

## Observability Evidence Workflow

Generate the static observability readiness report before strict production readiness review:

```bash
python scripts/observability_readiness.py --output docs/working/status/baselines/observability-readiness-report.json --summary-output docs/working/status/baselines/observability-readiness-summary.md
```

Strict production observability requires a live dashboard or evidence bundle, then launch gate enforcement:

```bash
python scripts/observability_readiness.py --require-live-evidence --fail-on-blocked --output docs/working/status/baselines/observability-readiness-report.json --summary-output docs/working/status/baselines/observability-readiness-summary.md
python scripts/launch_gate.py --require-observability-readiness --observability-readiness-report docs/working/status/baselines/observability-readiness-report.json --print-json
```

Minimum observability evidence fields:

- job duration
- job success/fail
- retry counts and retry rate
- modality success rate
- human review scores
- release artifact build pass/fail
- agent smoke pass/fail
- redaction/secret access failures

Static trial metrics, platform console fields, and release evidence contracts are not enough for strict production observability unless external dashboard evidence is attached.

## Evidence Collection Workflow

Generate and archive the minimum GL-05 evidence set:

```bash
python scripts/release_gate.py --python python3 --output docs/working/status/baselines/e13-release-gate-validation-plan.json
python scripts/launch_gate.py --output docs/working/status/baselines/broad-launch-readiness-report.json --summary-output docs/working/status/baselines/broad-launch-readiness-summary.md
python scripts/doc_sync.py --output docs/working/status/baselines/e13-doc-sync-check-report.json
python scripts/ops_evidence.py --output docs/working/status/baselines/operations-readiness-report.json --summary-output docs/working/status/baselines/operations-readiness-summary.md
python scripts/docker_readiness.py --output docs/working/status/baselines/docker-readiness-report.json --summary-output docs/working/status/baselines/docker-readiness-summary.md
python scripts/observability_readiness.py --output docs/working/status/baselines/observability-readiness-report.json --summary-output docs/working/status/baselines/observability-readiness-summary.md
```

Required artifacts:

- `docs/working/status/baselines/e13-release-gate-validation-plan.json`
- `docs/working/status/baselines/broad-launch-readiness-report.json`
- `docs/working/status/baselines/e13-doc-sync-check-report.json`
- `docs/working/status/baselines/operations-readiness-report.json`
- `docs/working/status/baselines/docker-readiness-report.json`
- `docs/working/status/baselines/observability-readiness-report.json`
- optional summary markdowns for human review

## Linux / CI Fallback

- Preferred: run on Linux host/container per `docker-zero-to-release.md`.
- If local environment cannot run full Linux validation, use CI/container-generated evidence and attach command logs.
- Never claim formal GA based only on fallback; fallback is acceptable for controlled Beta and GA review readiness evidence collection.
