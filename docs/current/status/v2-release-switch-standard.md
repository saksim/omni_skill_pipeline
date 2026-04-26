# V2 Release Switch Standard

## 1. Purpose

Define objective release gates for promoting V2 to the default mainline while preserving safe rollback.

## 2. Hard Gates

- `graph_is_source_of_truth`: all user-facing publications are rendered from `SkillGraph` metadata, not legacy-only compose paths.
- `review_queue_operational`: review queue list/claim/close flow is active, traceable, and auditable.
- `publication_view_count>=2`: markdown plus at least one structured publication (`checklist` or `decision_tree`) are both available.
- `postgres_repository_stable`: PostgreSQL repository write/read paths stay stable with rollback protection and no artifact corruption.
- `regression_beats_v1`: baseline regression metrics are not worse than V1 on required sample manifests.

## 3. Evidence Requirements

- Required TP references:
  - `TP-E9-03` (lineage link persistence and supersede audit chain)
  - `TP-E11-03` (quality regression harness and gated result)
- Required artifacts:
  - `docs/current/status/baselines/e13-doc-sync-check-report.json`
  - `docs/current/status/baselines/e11-quality-regression-manifest.json`
  - `docs/current/status/baselines/e11-perf-cost-baseline-manifest.json`
  - `docs/current/status/baselines/e13-postgres-soak-plan.json`
  - `docs/current/status/baselines/e13-postgres-soak-benchmark-report.json`

## 4. Cutover Decision

- Decision `GO`: all hard gates pass, evidence is complete, and release reviewer signs off.
- Decision `HOLD`: any hard gate fails or evidence is incomplete.
- Decision records must be written to history snapshot docs under `docs/history/status/`.

## 5. Rollback Trigger

- Any post-cutover regression where `traceability_rate` or `reviewer_edit_distance` violates baseline guardrail.
- Any sustained storage inconsistency or replay failure between publication artifacts and repository records.
- Any review queue processing break that removes audit traceability.

## 6. Command Pack

```bash
python scripts/run_tp_tests.py TP-E9-03 TP-E11-03 TP-E13-03 --python python3
python scripts/run_doc_sync_check.py --output docs/current/status/baselines/e13-doc-sync-check-report.json
python scripts/run_postgres_soak_validation.py --python python3 --postgres-dsn "$OMNI_TEST_POSTGRES_DSN"
```
