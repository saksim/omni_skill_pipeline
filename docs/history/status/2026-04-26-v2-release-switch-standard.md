# 2026-04-26 V2 Release Switch Snapshot

## Decision Snapshot

- Decision: `HOLD`
- Scope: keep V1 compatibility default; continue V2 hardening before mainline cutover.
- Reviewer note: Linux unified regression run has not completed yet.

## Gate Checklist

- `graph_is_source_of_truth`: pass
- `review_queue_operational`: pass
- `publication_view_count>=2`: pass
- `postgres_repository_stable`: pending long-run soak verification
- `regression_beats_v1`: pending Linux full regression comparison

## Evidence Links

- Standard: `docs/current/status/v2-release-switch-standard.md`
- TP references: `TP-E9-03`, `TP-E11-03`
- Planned reports:
  - `docs/current/status/baselines/e13-doc-sync-check-report.json`
  - `docs/current/status/baselines/e11-quality-regression-manifest.json`
  - `docs/current/status/baselines/e11-perf-cost-baseline-manifest.json`
  - `docs/current/status/baselines/e13-postgres-soak-plan.json`
  - `docs/current/status/baselines/e13-postgres-soak-benchmark-report.json`

## Pending Risks

- Linux full-batch execution is still pending, so no final pass/fail seal can be issued.
- Postgres long-run soak for publication/review lineage has not been closed (runner ready: `scripts/run_postgres_soak_validation.py`).
- Production cutover rehearsal and rollback drill are not yet complete.
