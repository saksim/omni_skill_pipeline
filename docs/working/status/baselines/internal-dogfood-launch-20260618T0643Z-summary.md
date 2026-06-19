# Internal Dogfood Launch Record

## Summary

| Field | Value |
| --- | --- |
| `release_id` | `internal-dogfood-20260618T0643Z` |
| `commit_sha` | `a4f0950` |
| `branch` | `dev` |
| `operator` | `Codex` |
| `started_at` | `2026-06-18T06:40:33Z` |
| `ended_at` | `2026-06-18T06:43:00Z` |
| `target_environment` | `local internal dogfood` |
| `decision` | `READY_FOR_INTERNAL_DOGFOOD` |
| `external_launch_gate` | `HOLD` |

## Scope Statement

This launch record is only for internal dogfood. It is not an external Beta, GA,
or SaaS launch claim. Fixture and simulated evidence may support internal
operator testing only when it remains clearly labelled as internal-only.

## Commands

### Dependency Check

```powershell
python -m coverage --version
```

Result:

```text
failed: No module named coverage.
```

Interpretation:

```text
The local Windows Python environment is missing the coverage package, so the
full CI coverage gate cannot pass locally in this environment. This is recorded
as an internal dogfood exemption, not as a CI pass.
```

### CI

```powershell
python scripts\ci.py --coverage-fail-under 50 --coverage-xml coverage.xml --keep-going
```

Result:

```text
failed: exit=1

Failures:
- coverage_erase failed because coverage is not installed.
- coverage unittest discovery failed because coverage is not installed.
- scripts/tp_tests.py failed on Windows with WinError 206: command line too long.
- coverage post-processing skipped because no coverage data files were created.
```

Interpretation:

```text
The CI workflow entrypoint has been fixed to scripts/ci.py. The remaining local
failure is environment/platform-specific and is not treated as external launch
evidence. This remains a follow-up item before any non-internal launch claim.
```

### Official Launch Gate

```powershell
python scripts\launch_gate.py --release-switch-report docs\working\status\baselines\e13-release-switch-decision-report.json --current-status-doc docs\working\status\CURRENT_STATUS.md --trial-metrics-report docs\working\status\baselines\controlled-trial\trial-metrics-report.json --controlled-trial-run-report docs\working\status\baselines\controlled-trial\controlled-trial-run-report.json --agent-smoke-report docs\working\status\baselines\controlled-trial\agent-smoke-report.json --doc-sync-report docs\working\status\baselines\e13-doc-sync-check-report.json --operations-readiness-report docs\working\status\baselines\operations-readiness-report.json --no-run-doc-sync --output - --summary-output - --max-evidence-age-hours 0 --print-json
```

Result:

```text
decision=HOLD
checks=15
pass=14
fail=1
blocking_checks=trial_loop_volume_and_modality_coverage
launch_gate_eligible_complete_loops=0/10
launch_gate_eligible_modalities=0/4
total_complete_loops=10
total_modalities=6
```

Allowed interpretation:

```text
The external launch gate remains HOLD because real launch-gate-eligible loop
and modality coverage is missing. This does not block internal dogfood, but it
does block controlled external Beta, GA, and SaaS claims.
```

### Internal Dogfood Gate

```powershell
python scripts\internal_launch_gate.py --ci-result exempted --ci-note "Local Windows CI baseline is not passing because coverage is not installed in this Python environment; GitHub workflow entrypoint is fixed to scripts/ci.py." --healthz-report docs\working\status\baselines\internal-dogfood-api-health-report.json --allow-degraded-health --output - --summary-output - --print-json
```

Result:

```text
decision=READY_FOR_INTERNAL_DOGFOOD
checks=9
pass=9
fail=0
blocking_checks=none
scope=internal_dogfood_only
external_launch_decision=HOLD
external_launch_claim=not_ready
fixture_sample_count=10
```

### API Health

Evidence file:

```text
docs/working/status/baselines/internal-dogfood-api-health-report.json
```

Result:

```text
status=degraded
http_status=503
internal_dogfood_only=true
failed_check=template_path
detail=template file is missing: docs/current/contracts/SKILL.template.md
```

Interpretation:

```text
This degraded health state is accepted only for internal dogfood with explicit
labelling. It is not acceptable external launch health evidence. The likely
runtime migration is to stop using the old docs/current template path and use
docs/latest/contracts/SKILL.template.md, but that code change is outside this
record's Patch Contract and requires explicit approval.
```

### Docker Smoke

```powershell
python scripts\container_smoke.py --dry-run
python scripts\container_smoke.py --image-tag omni-skill-pipeline:dogfood --port 18000
```

Result:

```text
not_run: Docker smoke was not executed in this local Windows verification pass.
```

## Known Risks

| Risk | Severity | Mitigation | Owner |
| --- | --- | --- | --- |
| External launch is still blocked by missing real loop evidence. | P0 for external launch | Keep `launch_gate.py` HOLD and collect real loop evidence before Beta/GA. | Product/Operator |
| Local CI does not pass in this environment. | P0 before external launch, exempted for internal dogfood | Install coverage and run CI on CI/Linux; fix Windows TP command length separately. | Engineering |
| API health is degraded due old `docs/current` template path. | P0 before external launch, accepted for internal dogfood only | Migrate runtime config/tests from `docs/current` to `docs/latest` after explicit scope approval. | Engineering |
| Internal readiness uses fixture evidence. | P0 before external launch | Keep all reports labelled `internal_dogfood_only=true`. | Operator |
| Docker smoke has not been executed. | P1 for internal launch hardening | Run on Docker-capable host. | DevOps |

## Failures

| Failure | Category | Blocking | Action | Owner |
| --- | --- | --- | --- | --- |
| `coverage` package missing locally. | dependency | no for internal dogfood; yes before external launch | Install dev dependencies and rerun CI. | Engineering |
| `scripts/tp_tests.py` hits WinError 206 on Windows. | platform/test | no for internal dogfood; yes before external launch | Use CI/Linux or split TP execution on Windows. | Engineering |
| `/healthz` degraded because template path points to `docs/current`. | runtime/doc-path | no for internal dogfood with explicit degraded allowance; yes before external launch | Approve and implement docs-current to docs-latest runtime migration. | Engineering |
| Official launch gate reports `trial_loop_volume_and_modality_coverage`. | product evidence | no for internal dogfood; yes before external launch | Collect 10 real loops across 4 modalities. | Product/Operator |

## Observation

| Window | Check | Result |
| --- | --- | --- |
| T+15m | `/healthz` | `degraded` recorded from internal health baseline |
| T+2h | errors/artifact growth/tmp growth | `not_run` |
| T+24h | internal user feedback | `not_run` |

## Rollback

Rollback triggered: no

```text
No live external launch was performed. Internal dogfood can be paused by
withholding use of this release record and keeping the official launch gate at
HOLD.
```

## Final Decision

```text
READY_FOR_INTERNAL_DOGFOOD
```

Decision notes:

```text
Proceed only as an internal dogfood/internal toy. Do not claim controlled
external Beta, GA, or SaaS readiness from this record.
```
