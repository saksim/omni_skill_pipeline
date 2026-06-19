# Internal Dogfood Launch Record 20260618T0656Z

## Summary

| Field | Value |
| --- | --- |
| release_id | 20260618T0656Z |
| commit_sha | 0c2aaf1 |
| branch | dev |
| operator | Codex |
| started_at | 2026-06-18T06:54:42Z |
| ended_at | 2026-06-18T06:56:00Z |
| target_environment | local TestClient / in-process API |
| decision | READY_FOR_INTERNAL_DOGFOOD |
| external_launch_gate | HOLD |

## Scope Statement

This record covers internal dogfood readiness only. It does not claim external beta, GA, SaaS readiness, or production launch readiness. The official launch gate remains the authority for external launch semantics.

## Change Summary

- Migrated runtime evidence defaults from `docs/current/status/baselines` to `docs/working/status/baselines`.
- Migrated published contract/manual defaults from `docs/current/contracts` to `docs/latest/contracts`.
- Migrated the release switch standard path from `docs/current/status` to `docs/releases/standards`.
- Revalidated `/healthz` as ready after the template path migration.
- Re-ran the internal dogfood readiness gate without degraded-health allowance.

## Evidence

| Evidence | Result | Notes |
| --- | --- | --- |
| API health baseline | PASS | `/healthz` returned 200 and `ready`; template path, draft directory, and app assembly checks passed. |
| Internal dogfood readiness gate | PASS | Evidence-backed run returned `READY_FOR_INTERNAL_DOGFOOD`; 9 pass, 0 fail. |
| Official launch gate | HOLD | 14 pass, 1 fail; failing check is `trial_loop_volume_and_modality_coverage`. |
| Ops evidence | PASS | 10 pass, 0 fail. |
| Doc sync | PASS | 13 pass, 0 fail. |
| Focused API/runbook tests | PASS | 76 tests passed. |
| Full local CI baseline | FAIL | `coverage` package unavailable and `scripts/tp_tests.py --all` hits Windows command length limit. |

## Invocation Note

The internal dogfood gate was evaluated with explicit CI evidence and the recorded health report:

```powershell
python scripts\internal_launch_gate.py --ci-result exempted --ci-note "Local Windows CI baseline is not passing: coverage package missing in this environment and scripts/tp_tests.py hits WinError 206 command-line length; GitHub workflow entrypoint is fixed to scripts/ci.py." --healthz-report docs\working\status\baselines\internal-dogfood-api-health-report.json --output docs\working\status\baselines\internal-dogfood-readiness-report.json --summary-output docs\working\status\baselines\internal-dogfood-readiness-summary.md --print-json
```

A default run without `--ci-result` correctly returns `HOLD` with `ci_baseline_passed`, because the gate does not invent CI status.

## Known Risks

| Risk | Level | Mitigation |
| --- | --- | --- |
| Docker smoke has not been run in this round. | P1 | Run the Docker zero-to-release smoke on a Docker-capable host. |
| Full local CI baseline still fails in this environment. | P1 | Install/enable `coverage` and split the TP test invocation to avoid Windows command length limits. |
| External launch evidence remains below launch threshold. | External blocker | Collect real eligible trial loops and modality coverage before claiming beta/GA. |

## Failures

- No blocking internal dogfood gate failure remains after the docs-layer path migration.
- External launch remains blocked by `trial_loop_volume_and_modality_coverage`.

## Observation

| Window | Status | Notes |
| --- | --- | --- |
| T+15m | PASS | API health is ready in local TestClient evidence. |
| T+2h | NOT_RUN | Not applicable to this local internal dogfood record. |
| T+24h | NOT_RUN | Not applicable to this local internal dogfood record. |

## Rollback

No rollback was required. If needed, revert the path migration and baseline updates as a single change set, then rerun the internal gate and official launch gate before reuse.

## Final Decision

`READY_FOR_INTERNAL_DOGFOOD` for internal toy/dogfood use only. The external launch decision remains `HOLD`.
