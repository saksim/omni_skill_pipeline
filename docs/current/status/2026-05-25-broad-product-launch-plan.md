# Broad Product Launch Plan

> Date: 2026-05-25
> Scope: broad product launch architecture, gap-to-solution mapping, and GL task cards for controlled external Beta, single-team GA, and platformization.
> Current source of truth: `CURRENT_STATUS.md`, `2026-05-18-controlled-business-trial-iteration.md`, `2026-05-17-distillation-platform-strategy-assessment.md`.

## Verdict

The project should not restart as a generic platform rewrite. The correct path is to preserve the existing evidence-to-skill distillation core and add product launch layers around it.

Current state:

- Engineering release gate: strong. The latest recorded Linux release run reached `GO`.
- Controlled-trial construction: complete. `CBT-01` through `CBT-14` are complete.
- Product launch evidence: incomplete. The current controlled-trial evidence has only one complete loop and one modality, while the launch criteria require at least 10 loops across at least 4 modalities.

Therefore, the next program should be a new `GL-*` task group:

```text
CBT-* = controlled business trial capability construction
GL-*  = broad product launch construction
```

The first broad launch target is controlled external Beta. Single-team GA and multi-tenant SaaS must remain later stages.

## Launch Levels

### Level 1: Controlled External Beta

Target:

- 1-3 friendly users, teams, or workflows.
- Limited data classes and limited scenarios.
- Human review remains mandatory before publication.
- Operator-visible cost, latency, failure, review, and agent-smoke metrics.

Exit criteria:

- Latest release decision remains `GO`.
- At least 10 complete trial loops.
- At least 4 modalities represented.
- 0 unreviewed skills published.
- 0 critical secret or PII leaks.
- Agent smoke success rate at or above 80% for approved skills.
- Provider/runtime failure rate below agreed threshold.
- A final controlled-trial report recommends `EXPAND_BETA` or `GA_CANDIDATE`.

### Level 2: Single-Team GA Review

Target:

- One organization or one team can use the system as an ongoing production workflow.
- Postgres-first persistence is the default operating mode.
- Worker semantics are stable enough for long-running jobs.
- Review workflow is operational rather than artifact-only.
- Operations have deployment, rollback, backup, restore, and incident runbooks.

Exit criteria:

- Beta evidence meets the Level 1 criteria.
- Production-like soak shows stable worker/repository/review behavior.
- Review feedback can drive remediation or revision.
- Release gate remains strict and does not rely on relaxed flags, dry-run evidence, or skipped doc/security checks.

### Level 3: Platform Beta / SaaS Candidate

Target:

- Multiple organizations or projects can use the product without data, quota, or permission leakage.
- Tenant boundaries are enforced at every artifact, job, review task, skill package, and metric.
- Cost, quota, audit, data retention, and deletion workflows are product features.

Exit criteria:

- Tenant isolation tests pass.
- Role and API key authorization tests pass.
- Cost ledger and audit log are queryable by tenant/project.
- Data retention and deletion flows are documented and tested.
- Platform console or equivalent product surface supports day-to-day operation.

## Architecture Layers

Keep the existing distillation core as the center and add launch layers around it:

```text
L1 Input & Trial Control
L2 Distillation Core
L3 Review & Quality Loop
L4 Agent Skill Packaging
L5 Runtime Jobs & Persistence
L6 Security / Governance / Audit
L7 Product API / CLI / UI
L8 Launch Gate / Ops / Metrics
```

### L1 Input & Trial Control

Responsibility:

- Trial manifests.
- Allowed modalities, scenarios, sensitivity levels, owners, and publication targets.
- Real loop evidence collection.

Strengthening path:

- Move from fixture-only loops to real user/team loops.
- Expand from one mixed-corpus sample to at least 10 loops across 4 modalities.
- Reject trial inputs that do not declare owner, sensitivity, and review owner.

### L2 Distillation Core

Responsibility:

- Evidence extraction.
- Semantic atoms.
- Skill graph and skill document production.
- Publication views.

Strengthening path:

- Preserve the existing core as the semantic source of truth.
- Avoid broad rewrites unless trial evidence identifies recurring quality defects.
- Improve modality-specific extraction only when reviewer packets or metrics show concrete failure classes.

### L3 Review & Quality Loop

Responsibility:

- Review policy.
- Reviewer packet.
- Review task lifecycle.
- Feedback and remediation.
- Calibration between automated scores and human judgment.

Strengthening path:

- Turn artifact review into an operational review workflow.
- Make `approve`, `reject`, `needs_rework`, `supersede`, and `merge` structured actions.
- Convert reviewer feedback into remediation plans and quality regression cases.

### L4 Agent Skill Packaging

Responsibility:

- `AgentSkillPackage`.
- Portable `SKILL.md`.
- Target-specific exports for Codex, Claude Code, OpenCode, and portable packages.
- Usability validation and agent smoke recording.

Strengthening path:

- Keep long evidence in `references/`.
- Keep trigger descriptions precise and testable.
- Record agent smoke by target, skill, prompt, expected selection, observed selection, output, and failure code.

### L5 Runtime Jobs & Persistence

Responsibility:

- Worker job lifecycle.
- Idempotency, retry, locking, and dead-letter behavior.
- Postgres-first persistence.
- File artifacts as debug sidecars.

Strengthening path:

- Prefer one well-defined job runtime before introducing distributed orchestration.
- Ensure every job has a stable idempotency key.
- Ensure every job state transition is queryable and auditable.

### L6 Security / Governance / Audit

Responsibility:

- Trial security gate.
- Secret and PII detection.
- Sensitive data class policy.
- Audit logs.
- Data retention and deletion.
- Tenant data boundaries.

Strengthening path:

- Move from package-level validation to organization/project-level governance.
- Require policy decisions to be visible in reviewer packets and launch reports.
- Treat generated skills as executable or semi-executable assets requiring provenance and rollback evidence.

### L7 Product API / CLI / UI

Responsibility:

- Stable API and CLI contracts.
- Beta onboarding flow.
- Review queue product surface.
- Skill registry and metrics views.

Strengthening path:

- Make API/CLI usage repeatable without repository-internal knowledge.
- Add a minimal product console only after review packets and metrics prove the workflow shape.
- Prioritize operator workflows over marketing surfaces.

### L8 Launch Gate / Ops / Metrics

Responsibility:

- Machine-readable launch readiness.
- Release decision binding.
- Trial metrics.
- Operations runbooks.
- SLOs, alerts, rollback, backup, restore, and incident handling.

Strengthening path:

- Replace subjective launch judgment with `HOLD`, `READY_FOR_CONTROLLED_BETA`, `READY_FOR_GA_REVIEW`, and `READY_FOR_PLATFORM_BETA`.
- Refuse relaxed flags, dry-run evidence, stale evidence, skipped security checks, and skipped doc sync.
- Keep launch evidence fresh and tied to concrete artifacts.

## Gap-To-Solution Map

| Gap | Layer | Solution |
| --- | --- | --- |
| Only one real trial loop exists | L1, L8 | Build a trial evidence expansion program and require at least 10 loops across 4 modalities before Beta/GA discussion. |
| Launch readiness is still partly narrative | L8 | Add a broad launch readiness gate that reads release, trial, smoke, security, and docs evidence. |
| Review is still artifact-heavy | L3, L7 | Productize review task lifecycle with list, claim, approve, reject, needs-rework, close, and reason codes. |
| Feedback does not yet drive improvement | L3 | Add a feedback consumer that emits remediation plans and quality regression cases. |
| Agent smoke evidence is too small | L4, L8 | Expand agent smoke into a target/scenario matrix and feed pass rates into launch gates. |
| Worker and persistence need production semantics | L5 | Harden worker claim, retry, lock, idempotency, dead-letter, and Postgres-first repository behavior. |
| Customer-facing usage contract is thin | L7 | Publish Beta API/CLI/manifest/error/limit examples and onboarding runbooks. |
| Operations are not yet product-grade | L8 | Add deploy, rollback, backup, restore, alert, and incident workflows tied to validation scripts. |
| Multi-tenant SaaS is not ready | L6, L7 | Add organization, project, user, role, API key, tenant-bound artifact, and tenant-bound metric models before SaaS claims. |
| Cost is not governed as a product feature | L6, L8 | Add a cost ledger by run, skill, provider call, tenant, and accepted skill. |
| Data governance is not yet organization-grade | L6 | Add retention, deletion, sensitivity policy, audit log, and tenant boundary validation. |

## GL Task Cards

### GL-01 Launch Level Contract & Gate

- Status: Complete
- Goal: define broad launch levels and add a machine-readable readiness gate.
- Files:
  - `docs/current/status/2026-05-25-broad-product-launch-plan.md`
  - `scripts/run_launch_readiness_gate.py`
  - `tests/test_launch_readiness_gate_script.py`
  - `README.md`
  - `docs/INDEX.md`
  - `docs/current/status/CURRENT_STATUS.md`
- Work:
  - Define launch decisions: `HOLD`, `READY_FOR_CONTROLLED_BETA`, `READY_FOR_GA_REVIEW`, `READY_FOR_PLATFORM_BETA`.
  - Read release switch evidence, controlled trial metrics, agent smoke report, security gate evidence, and doc sync status.
  - Reject dry-run, relaxed, stale, missing, or skipped evidence.
  - Emit JSON and short Markdown summary.
- Acceptance:
  - Current repository evidence returns `HOLD` because trial loop and modality coverage are insufficient.
  - Fixture evidence with at least 10 loops and 4 modalities can reach `READY_FOR_CONTROLLED_BETA`.
  - Missing security or doc-sync evidence keeps the decision at `HOLD`.
- Evidence:
  - 2026-05-25: Added `scripts/run_launch_readiness_gate.py` with launch decisions `HOLD`, `READY_FOR_CONTROLLED_BETA`, `READY_FOR_GA_REVIEW`, and `READY_FOR_PLATFORM_BETA`.
  - 2026-05-25: Added `tests/test_launch_readiness_gate_script.py`; `python -m unittest tests.test_launch_readiness_gate_script` passed 5 tests covering current HOLD, ready fixture, missing security, missing doc-sync, and dry-run rejection.
  - 2026-05-25: `python scripts/run_launch_readiness_gate.py --output - --summary-output - --max-evidence-age-hours 0 --print-json` returned `HOLD` with the only blocking check `trial_loop_volume_and_modality_coverage` (`complete_loops=1/10`, `modalities=1/4`).

### GL-02 Trial Evidence Expansion

- Status: Complete
- Goal: expand controlled trial evidence from one fixture loop to launch-relevant coverage.
- Files:
  - `docs/current/status/baselines/controlled-trial/`
  - `docs/current/status/baselines/trial-manifests/`
  - `scripts/run_controlled_trial.py`
  - `scripts/run_trial_metrics_collector.py`
  - tests under `tests/`
- Work:
  - Add or collect at least 10 loop manifests across at least 4 modalities.
  - Ensure each loop records review outcome, edit distance, latency, provider/runtime failures, cost, security result, and agent smoke result.
  - Generate final controlled-trial report from real or explicitly labeled trial evidence.
- Acceptance:
  - Trial metrics pass `loop_volume_and_modality_coverage`.
  - GA discussion remains blocked if any critical safety condition fails.
- Evidence:
  - 2026-05-25: added GL-02 expansion fixture manifest `docs/current/status/baselines/trial-manifests/trial-sample-launch-expansion-fixture.example.json` with 10 loop samples across 6 modalities and explicit loop evidence labeling (`evidence_origin`, `launch_gate_eligible`, `launch_gate_ineligible_reason`).
  - 2026-05-25: updated trial metrics contracts in `src/omni_skill_pipeline/quality/trial_metrics.py` and `scripts/run_launch_readiness_gate.py` to separate total loop coverage from launch-gate-eligible real evidence coverage, preventing fixture/synthetic loops from being miscounted as controlled-Beta-ready evidence.
  - 2026-05-25: updated runner `scripts/run_controlled_trial.py` to persist loop evidence origin/eligibility fields into metrics manifests and run reports.
  - 2026-05-25: generated GL-02 baseline outputs under `docs/current/status/baselines/controlled-trial/`:
    - `controlled-trial-run-report.json` (`sample_count=10`, modalities=`text/audio/image/video/tabular/mixed_corpus`)
    - `trial-metrics-manifest.json`
    - `trial-metrics-report.json` (`complete_loop_count=10`, `complete_modalities=6`, `launch_gate_evidence.complete_loop_count=0`, `evidence_origin_counts.fixture=10`)
    - `trial-metrics-summary.md`
  - 2026-05-25: `python scripts/run_launch_readiness_gate.py --output - --summary-output - --max-evidence-age-hours 0 --print-json` kept decision `HOLD` with a single blocker `trial_loop_volume_and_modality_coverage`, now explicitly reported as lack of launch-gate-eligible real loops/modalities.
  - 2026-05-25: focused tests passed:
    - `python -m unittest tests.test_video_parser tests.test_trial_metrics_collector tests.test_trial_metrics_collector_script tests.test_launch_readiness_gate_script tests.test_controlled_trial_runner_script`
  - 2026-05-25: doc sync passed:
    - `python scripts/run_doc_sync_check.py --output -`

### GL-03 Beta Product Contract

- Status: Complete
- Goal: make controlled external Beta usable without repository-internal knowledge.
- Files:
  - `docs/current/operations/api.md`
  - `docs/current/operations/cli.md`
  - `docs/current/operations/env.md`
  - `docs/current/operations/runbooks/`
  - example payloads under `examples/`
- Work:
  - Document official API/CLI flows for manifest validation, distillation, review, export, validation, security gate, and metrics.
  - Include error contract, rate limits, auth, data restrictions, and cost visibility.
  - Add a friendly-customer onboarding checklist.
- Acceptance:
  - A beta operator can run one end-to-end loop using only the operations docs and examples.
- Evidence:
  - 2026-05-25: added controlled external Beta onboarding runbook `docs/current/operations/runbooks/controlled-external-beta-onboarding.md` defining the official GL-03 flow (`manifest validation -> distill -> review queue -> export -> validate -> security gate -> metrics -> launch readiness decision`).
  - 2026-05-25: added canonical GL-03 corpus payload example `examples/beta/corpus_payload.example.json` and linked it from API/CLI operation docs.
  - 2026-05-25: updated operation entrypoints to expose GL-03 contract and onboarding path:
    - `docs/current/operations/api.md`
    - `docs/current/operations/cli.md`
    - `docs/current/operations/env.md`
    - `docs/current/operations/OPERATIONS.md`
    - `docs/current/operations/runbooks/README.md`
  - 2026-05-25: verification passed:
    - `python scripts/run_doc_sync_check.py --output -`
    - `python scripts/run_launch_readiness_gate.py --output - --summary-output - --max-evidence-age-hours 0 --print-json` (decision remains `HOLD`; blocker remains trial launch-gate-eligible real loop/modality coverage).

### GL-04 Review Workflow Productization

- Status: Complete
- Goal: move review from artifact inspection to an operational workflow.
- Files:
  - `src/omni_skill_pipeline/review/`
  - `src/omni_skill_pipeline/repository.py`
  - `apps/api/` or `src/omni_skill_pipeline/api_app.py`
  - `docs/current/operations/`
  - tests under `tests/`
- Work:
  - Add list, claim, close, approve, reject, and needs-rework operations.
  - Persist reviewer, timestamps, decision, reason codes, and reviewer edits.
  - Keep reviewer packet as the detailed evidence surface.
- Acceptance:
  - Review tasks can be operated through API/CLI without manual artifact editing.
- Evidence:
  - 2026-05-25: extended review queue repository contract and persistence in `src/omni_skill_pipeline/interfaces.py` and `src/omni_skill_pipeline/repository.py` with structured decision operations (`approve`, `reject`, `needs_rework`) and reviewer metadata fields (`reason_codes`, `reviewer_edits`, `closed_by`, `closed_at`, `review_notes`).
  - 2026-05-25: expanded API review operation surface in `src/omni_skill_pipeline/api_schemas.py` and `src/omni_skill_pipeline/api_app.py`:
    - `POST /v1/review/queue/{review_task_id}/close` now accepts structured decision metadata.
    - added `POST /v1/review/queue/{review_task_id}/decision` for explicit `approve/reject/needs_rework` actions.
  - 2026-05-25: added CLI operational workflow in `src/omni_skill_pipeline/cli.py` via `review-queue` command (`list/claim/close/approve/reject/needs-rework`) so review lifecycle can be operated without manual artifact edits.
  - 2026-05-25: extended worker review queue runtime operations in `src/omni_skill_pipeline/worker.py` to support structured review actions and decision metadata payload persistence.
  - 2026-05-25: added focused tests:
    - `tests/test_api_schemas.py`
    - `tests/test_api_review_queue.py`
    - `tests/test_review_queue_repository.py`
    - `tests/test_worker.py`
    - `tests/test_cli.py`
  - 2026-05-25: operations docs updated:
    - `docs/current/operations/api.md`
    - `docs/current/operations/cli.md`
    - `docs/current/operations/worker.md`

### GL-05 Production Operations Baseline

- Status: Complete
- Goal: establish deployable and supportable production operations for single-team usage.
- Files:
  - `docs/current/operations/runbooks/`
  - `scripts/`
  - Docker/deploy files as needed
  - tests under `tests/`
- Work:
  - Define deploy, rollback, backup, restore, incident response, log inspection, and alert workflows.
  - Bind operations evidence to existing release gates.
  - Keep Linux validation mandatory for launch claims but allow CI/container evidence.
- Acceptance:
  - Operator can deploy, validate, roll back, and collect evidence using documented commands.
- Evidence:
  - 2026-05-25: production operations baseline runbook is in place at `docs/current/operations/runbooks/production-operations-baseline.md`, including deploy, validation, rollback, backup, restore, incident response, log inspection, alerting, and evidence collection workflows.
  - 2026-05-25: operations-readiness evidence runner `scripts/run_ops_readiness_evidence.py` plus focused checks/tests are in place (`tests/test_ops_readiness_evidence_script.py`, `tests/test_production_ops_runbook.py`, `tests/test_doc_sync_production_ops_runbook_check.py`).
  - 2026-05-25: focused verification passed:
    - `python -m unittest tests.test_production_ops_runbook tests.test_ops_readiness_evidence_script tests.test_doc_sync_production_ops_runbook_check`
    - `python scripts/run_doc_sync_check.py --output -`
  - 2026-05-25: baseline evidence artifacts were generated at canonical paths:
    - `docs/current/status/baselines/e13-release-gate-validation-plan.json` (release-gate plan)
    - `docs/current/status/baselines/e13-doc-sync-check-report.json` (doc-sync pass evidence)
    - `docs/current/status/baselines/operations-readiness-report.json` and `docs/current/status/baselines/operations-readiness-summary.md` (`overall_status=pass`, `fail_count=0`)
  - 2026-05-25: `python scripts/run_launch_readiness_gate.py --output - --summary-output - --max-evidence-age-hours 0 --print-json` now keeps `HOLD` with only one blocker: `trial_loop_volume_and_modality_coverage` (operations-readiness blockers cleared).

### GL-06 Persistence & Worker Hardening

- Status: Complete
- Goal: make long-running production workloads stable.
- Files:
  - `src/omni_skill_pipeline/worker.py`
  - `src/omni_skill_pipeline/persistence/`
  - `infra/sql/`
  - tests under `tests/`
- Work:
  - Make Postgres-first persistence the production mode.
  - Harden job claim, retry, lock, idempotency, and dead-letter behavior.
  - Preserve file artifacts as debug sidecars.
- Acceptance:
  - Duplicate jobs do not produce unsafe duplicate outputs.
  - Concurrent workers do not claim the same job.
  - Failed jobs are inspectable and recoverable.
- Evidence:
  - 2026-05-25: implemented repository mode controls for Postgres-first production operation in `src/omni_skill_pipeline/config.py` and `src/omni_skill_pipeline/service_factory.py`:
    - `OMNI_ARTIFACT_REPOSITORY_MODE=file|postgres|dual_write`
    - `OMNI_POSTGRES_REPOSITORY_DSN`
    - `OMNI_DUAL_WRITE_CONTINUE_ON_SECONDARY_ERROR`
    - `OMNI_DUAL_WRITE_SECONDARY_PREFIX`
  - 2026-05-25: wired `service_factory._build_artifact_repository(...)` so `postgres` mode uses `PostgresRepository`, and `dual_write` mode uses Postgres primary + file secondary debug sidecars via `DualWriteArtifactRepository`.
  - 2026-05-25: worker hardening acceptance evidence remains covered by focused worker tests for retry/claim/idempotency/failure inspection in `tests/test_worker.py` (duplicate suppression, concurrent claim safety, transient retry, and failed-job payload persistence under `jobs/failed`).
  - 2026-05-25: added focused configuration and composition tests:
    - `tests/test_service_factory_split.py` (file/postgres/dual_write repository mode selection and DSN guardrails)
    - `tests/test_openai_provider_config.py` (new artifact-repository env settings contract)
  - 2026-05-25: updated operator env contract docs for GL-06:
    - `.env.example`
    - `docs/current/operations/env.md`
  - 2026-05-25: focused verification passed:
    - `python -m unittest tests.test_service_factory_split tests.test_openai_provider_config tests.test_worker tests.test_dual_write_repository tests.test_postgres_repository`
    - `python scripts/run_doc_sync_check.py --output -`
  - 2026-05-25: launch gate verification:
    - `python scripts/run_launch_readiness_gate.py --output - --summary-output -` keeps decision `HOLD`; blocker remains only `trial_loop_volume_and_modality_coverage` (no new persistence/worker blocker introduced).

### GL-07 Quality Feedback Loop

- Status: Complete
- Goal: turn human feedback into measurable improvement.
- Files:
  - `src/omni_skill_pipeline/quality/`
  - `scripts/`
  - `docs/current/status/baselines/`
  - tests under `tests/`
- Work:
  - Convert review feedback into remediation plans.
  - Build quality regression cases from accepted/rejected loops.
  - Track calibration between automated quality scores and reviewer decisions.
- Acceptance:
  - Repeated quality defects become regression cases or remediation tasks.
- Evidence:
  - 2026-05-25: added quality feedback loop aggregation module `src/omni_skill_pipeline/quality/feedback_loop.py` to convert trial-loop `review_feedback` into executable remediation plans, repeated-defect regression cases, and calibration samples aligned to reviewer outcomes.
  - 2026-05-25: added runner `scripts/run_quality_feedback_loop.py` to emit:
    - `docs/current/status/baselines/quality-feedback-loop-report.json`
    - `docs/current/status/baselines/quality-feedback-loop-summary.md`
    - `docs/current/status/baselines/quality-feedback-loop-calibration-manifest.json`
  - 2026-05-25: baseline run over current GL-02 trial evidence generated `sample_count=10`, `remediation_plan_count=10`, `regression_case_count=0`, `calibration_sample_count=10` (no repeated defects yet under current thresholds; remediation plans still produced for every reviewed loop).
  - 2026-05-25: added focused tests:
    - `tests/test_quality_feedback_loop.py`
    - `tests/test_quality_feedback_loop_script.py`
    - and re-validated existing feedback/regression/calibration contracts:
      - `tests/test_review_feedback.py`
      - `tests/test_review_feedback_consumer.py`
      - `tests/test_quality_regression_script.py`
      - `tests/test_tune_review_policy.py`
      - `tests/test_calibration_ga_validation_script.py`
      - `tests/test_review_queue_ga_validation_script.py`
  - 2026-05-25: focused verification passed:
    - `python -m unittest tests.test_quality_feedback_loop tests.test_quality_feedback_loop_script tests.test_review_feedback tests.test_review_feedback_consumer tests.test_quality_regression_script tests.test_tune_review_policy tests.test_calibration_ga_validation_script tests.test_review_queue_ga_validation_script`
    - `python scripts/run_quality_feedback_loop.py --run-report docs/current/status/baselines/controlled-trial/controlled-trial-run-report.json --output docs/current/status/baselines/quality-feedback-loop-report.json --summary-output docs/current/status/baselines/quality-feedback-loop-summary.md --calibration-output docs/current/status/baselines/quality-feedback-loop-calibration-manifest.json`
    - `python scripts/run_doc_sync_check.py --output -`
    - `python scripts/run_launch_readiness_gate.py --output - --summary-output - --max-evidence-age-hours 0 --print-json` (decision remains `HOLD`; blocker remains `trial_loop_volume_and_modality_coverage` due launch-gate-eligible real loops/modalities 0/10 and 0/4).

### GL-08 Tenant / Authz / Quota Foundation

- Status: Complete
- Goal: prepare the system for platform Beta without claiming full SaaS.
- Files:
  - domain models under `src/omni_skill_pipeline/`
  - persistence schema under `infra/sql/`
  - API/auth modules
  - tests under `tests/`
- Work:
  - Add organization, project, user, role, membership, API key, and quota models.
  - Bind artifacts, jobs, review tasks, skill packages, and metrics to tenant/project scope.
  - Enforce role-based authorization on product-facing operations.
- Acceptance:
  - Cross-tenant reads and writes are rejected by tests.
  - API keys are scoped and revocable.
- Evidence:
  - 2026-05-26: added tenant domain models in `src/omni_skill_pipeline/models.py`:
    - `Organization`, `Project`, `TenantUser`, `Membership`, `TenantQuotaPolicy`, `TenantAPIKey`, and `MembershipRole`.
  - 2026-05-26: added tenant authz/quota registry `src/omni_skill_pipeline/tenant_access.py` and settings wiring in `src/omni_skill_pipeline/config.py` for:
    - `OMNI_TENANT_ACCESS_JSON`
    - `OMNI_TENANT_ACCESS_FILE`
  - 2026-05-26: bound tenant scope to distill/review flows:
    - API enforcement and metadata injection in `src/omni_skill_pipeline/api_app.py`
    - request/schema support in `src/omni_skill_pipeline/api_schemas.py`
    - service scope propagation in `src/omni_skill_pipeline/service.py`
    - review-queue tenant filtering in `src/omni_skill_pipeline/repository.py` and `src/omni_skill_pipeline/worker.py`.
  - 2026-05-26: persistence schema and Postgres binding updates:
    - `infra/sql/001_init.sql` adds `tenant_scopes` table.
    - `src/omni_skill_pipeline/persistence/postgres_repository.py` upserts tenant scope evidence from request/adapter metadata.
  - 2026-05-26: trial metrics contract now validates `tenant_scope` shape in `src/omni_skill_pipeline/quality/trial_metrics.py`.
  - 2026-05-26: acceptance-focused tests added/extended:
    - `tests/test_tenant_access.py` (authz, scope, quota, revoked key)
    - `tests/test_api_tenant_authz.py` (missing key, role restrictions, cross-tenant rejection, quota enforcement, revoked key rejection, tenant-scoped review queue list)
    - review-queue/worker compatibility updates in `tests/test_api_review_queue.py`, `tests/test_review_queue_repository.py`, `tests/test_worker.py`.
  - 2026-05-26: focused verification passed:
    - `python -m unittest tests.test_tenant_access tests.test_api_tenant_authz tests.test_api_auth tests.test_api_rate_limit tests.test_api_healthz tests.test_api_app tests.test_api_app_validation tests.test_api_review_queue tests.test_review_queue_repository tests.test_worker`
    - `python -m unittest tests.test_service_split_l2_28 tests.test_service_factory_split tests.test_service_repository_protocol tests.test_repository_contract tests.test_review_queue_repository tests.test_postgres_repository tests.test_api_schemas tests.test_trial_metrics_collector`
    - `python scripts/run_doc_sync_check.py --output -`
    - `python scripts/run_launch_readiness_gate.py --output - --summary-output - --print-json` (decision remains `HOLD`; blocker remains `trial_loop_volume_and_modality_coverage`).

### GL-09 Cost / Audit / Data Governance

- Status: Complete
- Goal: make cost and data governance explicit product capabilities.
- Files:
  - `src/omni_skill_pipeline/`
  - `infra/sql/`
  - `docs/current/operations/`
  - tests under `tests/`
- Work:
  - Add cost ledger entries for provider calls, runs, skills, and accepted packages.
  - Add audit events for review, export, security gate, deletion, and tenant-sensitive operations.
  - Add retention and deletion policy records.
- Acceptance:
  - A tenant/project cost and audit report can be generated without raw artifact inspection.
- Evidence:
  - 2026-05-26: added governance domain module `src/omni_skill_pipeline/governance.py` and wired it into runtime paths:
    - service wiring in `src/omni_skill_pipeline/service_factory.py` / `src/omni_skill_pipeline/service.py`
    - API wiring in `src/omni_skill_pipeline/api_app.py` / `src/omni_skill_pipeline/api_schemas.py`
    - exporter wiring in `src/omni_skill_pipeline/exporters/agent_skill_exporter.py`
    - settings contract in `src/omni_skill_pipeline/config.py` (`OMNI_GOVERNANCE_LEDGER_DIR`)
  - 2026-05-26: implemented GL-09 governance product operations:
    - API: `POST /v1/governance/report`, `POST /v1/governance/retention-policy`, `POST /v1/governance/deletion`
    - CLI: `governance-report`, `upsert-retention-policy`, `record-deletion`
    - runtime events: provider/run/skill/accepted-package cost records and audit events for review/export/deletion flows
  - 2026-05-26: added focused tests for cost/audit/retention/deletion and wiring:
    - `tests/test_governance.py`
    - `tests/test_api_governance.py`
    - `tests/test_cli_governance.py`
    - `tests/test_service_factory_split.py`
    - `tests/test_openai_provider_config.py`
    - `tests/test_api_schemas.py`
  - 2026-05-26: focused verification passed:
    - `python -m unittest tests.test_governance tests.test_api_governance tests.test_cli_governance tests.test_service_factory_split tests.test_openai_provider_config tests.test_api_schemas`
    - `python scripts/run_doc_sync_check.py --output -`
    - `python scripts/run_launch_readiness_gate.py --output - --summary-output -` (`decision=HOLD`, only blocker remains `trial_loop_volume_and_modality_coverage`).

### GL-10 Platform Console

- Status: Complete
- Goal: add the minimum product surface for operators and reviewers.
- Files:
  - `apps/`
  - `src/`
  - `docs/current/operations/`
  - tests under `tests/`
- Work:
  - Add views for trial runs, review queue, skill registry, metrics, security failures, and cost.
  - Keep the UI focused on operator workflows and repeated use.
  - Do not build a broad marketing surface.
- Acceptance:
  - Operators can monitor a trial, reviewers can finish review tasks, and owners can inspect accepted skills from one surface.
- Evidence:
  - 2026-05-26: added platform-console aggregation module `src/omni_skill_pipeline/platform_console.py` to assemble one-call operator/reviewer views for:
    - `trial_runs` (from controlled-trial run report)
    - `review_queue` (from repository runtime queue APIs)
    - `skill_registry` (from drafted bundle artifacts)
    - `metrics` (from trial metrics + broad launch readiness + operations readiness evidence)
    - `security_failures` (from trial security gate / launch readiness security checks)
    - `cost` (from governance ledger summary)
  - 2026-05-26: exposed API surface `POST /v1/console/views` in `src/omni_skill_pipeline/api_app.py` with:
    - tenant-scoped authz (`review.read`) and scope validation aligned with GL-08
    - shared API key/rate-limit middleware
    - queue-status and limit controls
  - 2026-05-26: added request schema `ConsoleViewsRequestSchema` in `src/omni_skill_pipeline/api_schemas.py` (`queue_status` + `limit` + scope fields) with normalization and validation contracts.
  - 2026-05-26: added focused tests:
    - `tests/test_api_platform_console.py` (aggregated six-view payload contract)
    - `tests/test_api_schemas.py` (console schema normalization/validation coverage)
    - `tests/test_api_healthz.py` updates for settings contract compatibility after GL-10 API assembly extension
  - 2026-05-26: updated operations API contract docs:
    - `docs/current/operations/api.md` includes `POST /v1/console/views` endpoint and payload semantics.
  - 2026-05-26: focused verification passed:
    - `python -m unittest tests.test_api_platform_console tests.test_api_schemas tests.test_api_healthz tests.test_api_tenant_authz tests.test_api_governance`
    - `python scripts/run_doc_sync_check.py --output -`
    - `python scripts/run_launch_readiness_gate.py --output - --summary-output -` (decision remains `HOLD`; blocker remains `trial_loop_volume_and_modality_coverage`).

### GL-11 Real Trial Evidence Traceability Contract

- Status: Complete
- Goal: make launch-gate-eligible real loops auditable with explicit source trace fields.
- Files:
  - `src/omni_skill_pipeline/quality/trial_metrics.py`
  - `scripts/run_launch_readiness_gate.py`
  - `scripts/run_controlled_trial.py`
  - `docs/current/status/baselines/trial-metrics/trial-metrics-manifest.template.json`
  - tests under `tests/`
- Work:
  - Add a strict real-evidence traceability contract for trial loops: `source_system`, `source_reference`, `collected_at_utc`.
  - Ensure trial metrics report and launch gate expose a dedicated check for missing real-evidence source trace.
  - Keep fixture/synthetic evidence explicitly non-launch-gate-eligible and reject unknown `evidence_origin` labels in trial runner.
- Acceptance:
  - Real loops missing source trace fields fail trial metrics critical condition.
  - Launch readiness gate remains `HOLD` when real-evidence traceability condition fails.
  - Current repository remains `HOLD` only on trial launch-gate-eligible volume/modality blocker when source-trace condition is satisfied.
- Evidence:
  - 2026-05-26: updated `src/omni_skill_pipeline/quality/trial_metrics.py`:
    - validates `evidence_origin` (`real`/`fixture`/`synthetic`) and launch-gate eligibility semantics.
    - validates real-loop source trace (`source_system`, `source_reference`, `collected_at_utc`).
    - emits `launch_gate_evidence.real_evidence_missing_source_trace_count`.
    - adds critical condition `real_evidence_source_trace_complete`.
  - 2026-05-26: updated `scripts/run_launch_readiness_gate.py`:
    - adds blocking check `trial_real_evidence_source_trace_complete` sourced from trial metrics.
  - 2026-05-26: updated `scripts/run_controlled_trial.py`:
    - enforces supported `evidence_origin` values.
    - preserves `evidence_origin`/`launch_gate_eligible` labels in loop metrics rows.
    - auto-populates source trace fields when `evidence_origin=real`.
  - 2026-05-26: updated metrics template `docs/current/status/baselines/trial-metrics/trial-metrics-manifest.template.json` with explicit real-loop source trace fields and explicit synthetic non-eligible loop labeling.
  - 2026-05-26: focused tests passed:
    - `python -m unittest tests.test_trial_metrics_collector tests.test_trial_metrics_collector_script tests.test_launch_readiness_gate_script tests.test_controlled_trial_runner_script`
    - includes new coverage for:
      - missing real-evidence source trace -> `real_evidence_source_trace_complete` fail
      - launch gate `trial_real_evidence_source_trace_complete` HOLD behavior
      - invalid `evidence_origin` in trial runner fails with actionable error
  - 2026-05-26: doc sync passed:
    - `python scripts/run_doc_sync_check.py --output -`
  - 2026-05-26: launch gate verification:
    - `python scripts/run_launch_readiness_gate.py --output - --summary-output - --print-json`
    - decision remains `HOLD`; only blocker remains `trial_loop_volume_and_modality_coverage` with source-trace check passing (`missing_source_trace_count=0`).


### GL-12 Real Trial Loop Collection Program

- Status: Complete
- Goal: establish an executable real-loop evidence collection program for launch-gate-ready controlled external Beta evidence.
- Files:
  - `scripts/run_real_trial_loop_collection.py`
  - `tests/test_real_trial_loop_collection_script.py`
  - `docs/current/operations/runbooks/real-trial-loop-collection.md`
  - `docs/current/status/baselines/real-trial-loop-collection/`
  - `docs/current/status/baselines/README.md`
- Work:
  - Collect and deduplicate loop metrics rows from one or more controlled-trial run reports.
  - Enforce launch-gate evidence semantics (`evidence_origin`, `launch_gate_eligible`, source trace for `real`).
  - Emit real-loop collection report, markdown summary, and a trial-metrics manifest that can be consumed by launch-readiness gate.
  - Keep fixture/synthetic loops explicitly non-launch-gate-eligible and preserve blocker visibility.
- Acceptance:
  - Collector fails on invalid evidence labeling (for example, non-real loop marked launch-gate-eligible).
  - Collector reports blockers when real-loop volume/modality thresholds or real source trace completeness are insufficient.
  - Current repository output remains `HOLD` unless launch-gate-eligible real loop and modality coverage are actually met.
- Evidence:
  - 2026-05-26: added `scripts/run_real_trial_loop_collection.py` with contracts for loop dedupe, evidence-origin enforcement, real source-trace checks, blocker computation, and trial-metrics manifest emission.
  - 2026-05-26: added focused tests `tests/test_real_trial_loop_collection_script.py` covering fixture-only incomplete state, threshold-ready state, missing real source trace blocker, and invalid launch-gate eligibility labeling.
  - 2026-05-26: added GL-12 operator runbook `docs/current/operations/runbooks/real-trial-loop-collection.md` and baseline template `docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-metrics-manifest.template.json`.
  - 2026-05-26: verification passed:
    - `python -m unittest tests.test_real_trial_loop_collection_script`
    - `python scripts/run_real_trial_loop_collection.py --run-report docs/current/status/baselines/controlled-trial/controlled-trial-run-report.json --output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-report.json --summary-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-summary.md --manifest-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-metrics-manifest.json`
    - `python scripts/run_doc_sync_check.py --output -`
    - `python scripts/run_launch_readiness_gate.py --output - --summary-output - --print-json` (decision remains `HOLD`; blocker remains `trial_loop_volume_and_modality_coverage`, with GL-12 collector status `COLLECTION_INCOMPLETE` and `real_eligible_complete=0`, `modalities=0`).

### GL-13 Real Trial Launch Evidence Bridge

- Status: Complete
- Goal: provide a one-command bridge from GL-12 collected real-loop evidence to launch-readiness gate inputs without relaxing any gate policy.
- Files:
  - `scripts/run_real_trial_launch_evidence.py`
  - `tests/test_real_trial_launch_evidence_script.py`
  - `docs/current/operations/runbooks/real-trial-loop-collection.md`
  - `docs/current/operations/runbooks/README.md`
  - `docs/current/status/baselines/README.md`
- Work:
  - Chain GL-12 loop collection, trial metrics report generation, and launch-readiness gate in one executable command.
  - Reuse existing strict contracts (`evidence_origin`, launch-gate eligibility semantics, real source trace requirements, no relaxed/dry-run gate claims).
  - Keep final decision owned by `scripts/run_launch_readiness_gate.py` and expose HOLD/READY results directly.
- Acceptance:
  - A run with threshold-ready real loops can emit `READY_FOR_CONTROLLED_BETA` through the same pipeline.
  - Fixture-only evidence remains `HOLD`.
  - Optional strict mode can fail on collection blockers and/or launch HOLD for CI-style enforcement.
- Evidence:
  - 2026-05-26: added bridge script `scripts/run_real_trial_launch_evidence.py` to execute:
    - `run_real_trial_loop_collection.py`
    - `run_trial_metrics_collector.py`
    - `run_launch_readiness_gate.py`
  - 2026-05-26: added focused tests `tests/test_real_trial_launch_evidence_script.py`:
    - threshold-ready real-loop input reaches `READY_FOR_CONTROLLED_BETA`
    - fixture-only input with `--fail-on-hold` exits non-zero and keeps launch decision `HOLD`
  - 2026-05-26: updated runbook/index docs for operator entry:
    - `docs/current/operations/runbooks/real-trial-loop-collection.md`
    - `docs/current/operations/runbooks/README.md`
    - `docs/current/status/baselines/README.md`
  - 2026-05-26: focused verification passed:
    - `python -m unittest tests.test_real_trial_launch_evidence_script tests.test_real_trial_loop_collection_script tests.test_trial_metrics_collector_script tests.test_launch_readiness_gate_script`
    - `python scripts/run_doc_sync_check.py --output -`
    - `python scripts/run_launch_readiness_gate.py --output - --summary-output - --print-json` (decision remains `HOLD`; blocker remains `trial_loop_volume_and_modality_coverage` until real launch-gate-eligible loop/modality thresholds are met).

### GL-14 Real Trial Reviewer Trace Contract

- Status: Complete
- Goal: ensure launch-gate-eligible real loops include auditable reviewer trace so controlled external Beta evidence cannot bypass review accountability.
- Files:
  - `scripts/run_real_trial_loop_collection.py`
  - `src/omni_skill_pipeline/quality/trial_metrics.py`
  - `scripts/run_launch_readiness_gate.py`
  - `scripts/run_controlled_trial.py`
  - tests under `tests/`
  - `docs/current/operations/runbooks/real-trial-loop-collection.md`
  - `docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-metrics-manifest.template.json`
- Work:
  - Add real-loop reviewer-trace contract fields: `review_task_id`, `reviewed_by`, `reviewed_at_utc`.
  - Extend GL-12 collector to compute and expose `real_evidence_missing_review_trace_count` and fail collection readiness when missing.
  - Extend trial metrics critical conditions with `real_evidence_review_trace_complete`.
  - Extend broad launch gate with blocking check `trial_real_evidence_review_trace_complete`.
  - Ensure controlled-trial runner emitted loop rows include reviewer trace fields for contract compatibility.
- Acceptance:
  - Real loops missing reviewer trace fail collector readiness (`COLLECTION_INCOMPLETE`) with explicit blocker.
  - Trial metrics mark `real_evidence_review_trace_complete` as failed for missing reviewer trace.
  - Launch readiness remains `HOLD` when reviewer trace evidence is incomplete.
- Evidence:
  - 2026-05-27: updated `scripts/run_real_trial_loop_collection.py` to enforce reviewer-trace completeness for real loops and emit:
    - blocker `real_loop_review_trace_incomplete`
    - metric `launch_gate_alignment.real_evidence_missing_review_trace_count`
  - 2026-05-27: updated `src/omni_skill_pipeline/quality/trial_metrics.py`:
    - metric `trial_metrics.launch_gate_evidence.real_evidence_missing_review_trace_count`
    - critical condition `real_evidence_review_trace_complete`
  - 2026-05-27: updated `scripts/run_launch_readiness_gate.py` with blocking check `trial_real_evidence_review_trace_complete`.
  - 2026-05-27: updated `scripts/run_controlled_trial.py` to include loop-level reviewer trace fields in emitted metrics rows.
  - 2026-05-27: added/updated focused tests:
    - `tests/test_real_trial_loop_collection_script.py`
    - `tests/test_trial_metrics_collector.py`
    - `tests/test_launch_readiness_gate_script.py`
    - `tests/test_real_trial_launch_evidence_script.py`
    - `tests/test_controlled_trial_runner_script.py`
  - 2026-05-27: doc/runbook template updates:
    - `docs/current/operations/runbooks/real-trial-loop-collection.md`
    - `docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-metrics-manifest.template.json`
  - 2026-05-27: verification passed:
    - `python -m unittest tests.test_real_trial_loop_collection_script tests.test_trial_metrics_collector tests.test_launch_readiness_gate_script tests.test_real_trial_launch_evidence_script tests.test_controlled_trial_runner_script`
    - `python scripts/run_doc_sync_check.py --output -`
    - `python scripts/run_launch_readiness_gate.py --output - --summary-output - --print-json` (decision remains `HOLD`; blocker remains launch-gate-eligible real loop/modality volume pending real external Beta evidence accumulation).

### GL-15 Real Loop Manifest Intake Bridge

- Status: Complete
- Goal: allow GL-13 launch evidence bridge to ingest explicit real-loop manifests directly, so controlled external Beta evidence can accumulate without depending on controlled-trial fixture run-report shape.
- Files:
  - `scripts/run_real_trial_loop_collection.py`
  - `scripts/run_real_trial_launch_evidence.py`
  - `tests/test_real_trial_loop_collection_script.py`
  - `tests/test_real_trial_launch_evidence_script.py`
- Work:
  - Extend GL-12 collector input contract with `--loop-manifest` (top-level `loops`) in addition to `--run-report`.
  - Keep strict contracts unchanged: `evidence_origin`, launch-gate eligibility semantics, real source trace, and real reviewer trace.
  - Extend GL-13 bridge to pass through one or more `--loop-manifest` inputs and run full metrics + launch-gate evaluation.
  - Preserve fallback behavior: if no loop-manifest/run-report is provided, use default controlled-trial run report baseline.
- Acceptance:
  - Collector can produce `READY_FOR_CONTROLLED_BETA_EVIDENCE` from threshold-ready real loop-manifest input.
  - Bridge can reach `READY_FOR_CONTROLLED_BETA` from threshold-ready real loop-manifest input.
  - Fixture-only/default baseline remains `HOLD`; no relaxed/dry-run bypass is introduced.
- Evidence:
  - 2026-05-27: updated `scripts/run_real_trial_loop_collection.py`:
    - added `--loop-manifest` input support and mixed-source dedupe (`run-report` + `loop-manifest`)
    - collection report now emits `source_loop_manifest_paths`, `input_loop_manifest_count`, and combined source counts.
  - 2026-05-27: updated `scripts/run_real_trial_launch_evidence.py`:
    - added `--loop-manifest` passthrough into GL-12 collection stage
    - input resolution now accepts either run-report or loop-manifest inputs (or both), preserving default fallback behavior.
  - 2026-05-27: added focused tests:
    - `tests/test_real_trial_loop_collection_script.py`:
      - `test_loop_manifest_input_can_drive_ready_status`
    - `tests/test_real_trial_launch_evidence_script.py`:
      - `test_pipeline_accepts_loop_manifest_input`
  - 2026-05-27: focused verification passed:
    - `python -m unittest tests.test_real_trial_loop_collection_script tests.test_real_trial_launch_evidence_script`
    - `python scripts/run_doc_sync_check.py --output -`
    - `python scripts/run_launch_readiness_gate.py --output - --summary-output - --print-json` (decision remains `HOLD`; blocker remains real launch-gate-eligible loop/modality volume in repository baseline evidence).

### GL-16 Controlled External Beta Evidence Pack Publication

- Status: Complete
- Goal: publish a machine-readable controlled external Beta evidence pack from the GL-13 bridge so launch-gate status, real-vs-fixture evidence classification, and blocker context can be handed to reviewers/operators without ad-hoc report stitching.
- Files:
  - `scripts/run_real_trial_launch_evidence.py`
  - `tests/test_real_trial_launch_evidence_script.py`
  - `docs/current/operations/runbooks/real-trial-loop-collection.md`
  - `docs/current/status/baselines/README.md`
  - `docs/current/status/2026-05-25-broad-product-launch-plan.md`
- Work:
  - Extend GL-13 bridge with `--evidence-pack-output` and emit `real_trial_launch_evidence_pack.v1`.
  - Evidence pack must summarize:
    - launch decision (`HOLD`/`READY_FOR_CONTROLLED_BETA`/...)
    - input evidence sources (`run-report` and `loop-manifest`)
    - explicit evidence classification (total loops/modalities vs launch-gate-eligible real loops/modalities)
    - source trace/reviewer trace missing counts and current blockers.
  - Keep policy strictness unchanged: no dry-run/relaxed bypass, no fixture-as-real promotion, no GA claim inflation.
- Acceptance:
  - GL-13 bridge writes evidence pack on both READY and HOLD paths.
  - Evidence pack clearly indicates whether controlled external Beta is ready while preserving real-vs-fixture separation.
  - Current repository baseline can publish the pack but still reports `HOLD` until real launch-gate-eligible loops reach threshold.
- Evidence:
  - 2026-05-27: updated `scripts/run_real_trial_launch_evidence.py`:
    - added `--evidence-pack-output` (default: `docs/current/status/baselines/real-trial-loop-collection/real-trial-launch-evidence-pack.json`)
    - emits `real_trial_launch_evidence_pack.v1` with launch decision, source inputs, evidence classification, safety summary, and gate blocker summary.
  - 2026-05-27: updated tests in `tests/test_real_trial_launch_evidence_script.py`:
    - READY path now asserts evidence-pack decision/classification fields.
    - HOLD path now asserts evidence-pack blocker visibility.
    - loop-manifest input path now asserts evidence-pack input source accounting.
  - 2026-05-27: baseline run published first GL-16 pack:
    - `docs/current/status/baselines/real-trial-loop-collection/real-trial-launch-evidence-pack.json`
    - decision remains `HOLD` because launch-gate-eligible real loop/modality coverage is still below threshold.

### GL-17 Real External Beta Loop Batch Intake

- Status: Complete
- Goal: make real controlled external Beta loop evidence accumulation operational by supporting batch manifest-directory intake and explicit launch-threshold gap tracking.
- Files:
  - `scripts/run_real_trial_loop_collection.py`
  - `scripts/run_real_trial_launch_evidence.py`
  - `tests/test_real_trial_loop_collection_script.py`
  - `tests/test_real_trial_launch_evidence_script.py`
  - `docs/current/operations/runbooks/real-trial-loop-collection.md`
  - `docs/current/status/baselines/README.md`
  - `docs/current/status/2026-05-25-broad-product-launch-plan.md`
- Work:
  - Extend GL-12 collector with batch manifest-directory intake:
    - `--loop-manifest-dir`
    - `--loop-manifest-pattern`
    - `--loop-manifest-recursive`
  - Extend GL-12 report contract with explicit threshold gap counters:
    - `missing_complete_loops_to_threshold`
    - `missing_modalities_to_threshold`
  - Extend GL-13 bridge to pass batch intake options through to GL-12 and expose batch-source accounting + threshold gaps in GL-16 evidence pack.
  - Keep strict evidence semantics unchanged: only `evidence_origin=real` with launch-gate eligibility and source/reviewer trace can count toward launch readiness.
- Acceptance:
  - Collector can reach `READY_FOR_CONTROLLED_BETA_EVIDENCE` from manifest-directory batch input when thresholds are met.
  - Bridge can reach `READY_FOR_CONTROLLED_BETA` from manifest-directory batch input when thresholds are met.
  - Evidence pack preserves real-vs-fixture classification and threshold gap visibility.
- Evidence:
  - 2026-05-27: updated `scripts/run_real_trial_loop_collection.py`:
    - added batch directory intake (`--loop-manifest-dir`, `--loop-manifest-pattern`, `--loop-manifest-recursive`)
    - report now emits `source_loop_manifest_dirs`, `input_loop_manifest_dir_count`
    - launch-gate alignment now emits `missing_complete_loops_to_threshold`, `missing_modalities_to_threshold`
  - 2026-05-27: updated `scripts/run_real_trial_launch_evidence.py`:
    - passes batch intake options through to GL-12 collection
    - validates `--loop-manifest-dir` existence
    - GL-16 evidence pack now includes manifest-dir source accounting and threshold gap counters
  - 2026-05-27: added focused tests:
    - `tests/test_real_trial_loop_collection_script.py`:
      - `test_loop_manifest_dir_input_can_drive_ready_status`
    - `tests/test_real_trial_launch_evidence_script.py`:
      - `test_pipeline_accepts_loop_manifest_dir_input`
  - 2026-05-27: focused verification passed:
    - `python -m unittest tests.test_real_trial_loop_collection_script tests.test_real_trial_launch_evidence_script`
    - `python scripts/run_doc_sync_check.py --output -`
    - `python scripts/run_launch_readiness_gate.py --output - --summary-output - --print-json` (decision remains `HOLD`; blocker remains `trial_loop_volume_and_modality_coverage` until launch-gate-eligible real loop/modality thresholds are met in baseline evidence).

### GL-18 Real Loop Batch Contract Tolerance

- Status: Complete
- Goal: make GL-17 directory batch intake robust for real external Beta evidence operations by tolerating non-loop-manifest JSON files by default while preserving a strict-fail mode for CI/policy enforcement.
- Files:
  - `scripts/run_real_trial_loop_collection.py`
  - `scripts/run_real_trial_launch_evidence.py`
  - `tests/test_real_trial_loop_collection_script.py`
  - `tests/test_real_trial_launch_evidence_script.py`
  - `docs/current/operations/runbooks/real-trial-loop-collection.md`
  - `docs/current/status/baselines/README.md`
- Work:
  - Add `--strict-loop-manifest-contract` to GL-12 collector:
    - default mode skips JSON files without top-level `loops` during `--loop-manifest-dir` ingestion.
    - strict mode fails fast on any non-loop-manifest JSON to enforce hard contracts.
  - Extend GL-12 collector report contract with:
    - `ingested_loop_manifest_count`
    - `skipped_non_loop_manifest_count`
    - `skipped_non_loop_manifest_paths`
  - Pass strict-contract mode through GL-13 bridge and expose the new ingest/skip accounting in GL-16 evidence pack `input_sources`.
  - Keep launch evidence semantics unchanged: no fixture-as-real promotion and no launch-gate bypass.
- Acceptance:
  - Batch intake succeeds when directory contains valid loop manifests plus unrelated JSON metadata files, with skipped files explicitly reported.
  - Strict mode fails with actionable error when non-loop-manifest JSON is present.
  - Launch decision output remains policy-bound by `run_launch_readiness_gate.py`.
- Evidence:
  - 2026-05-27: updated `scripts/run_real_trial_loop_collection.py`:
    - added `--strict-loop-manifest-contract`
    - default tolerant skip path for non-loop-manifest JSON
    - report/summary fields for ingest-vs-skip accounting
  - 2026-05-27: updated `scripts/run_real_trial_launch_evidence.py`:
    - added strict mode passthrough to GL-12 collection stage
    - GL-16 evidence pack now includes `ingested_loop_manifest_count`, `skipped_non_loop_manifest_count`, and `skipped_non_loop_manifest_paths`
  - 2026-05-27: added focused tests:
    - `tests/test_real_trial_loop_collection_script.py`:
      - `test_loop_manifest_dir_skips_non_manifest_json_by_default`
      - `test_strict_loop_manifest_contract_fails_on_non_manifest_json`
    - `tests/test_real_trial_launch_evidence_script.py`:
      - `test_pipeline_manifest_dir_skips_non_manifest_json_by_default`
      - `test_pipeline_strict_loop_manifest_contract_fails_on_non_manifest_json`
  - 2026-05-27: focused verification passed:
    - `python -m unittest tests.test_real_trial_loop_collection_script tests.test_real_trial_launch_evidence_script`
    - `python scripts/run_doc_sync_check.py --output -`
    - `python scripts/run_launch_readiness_gate.py --output - --summary-output - --print-json` (decision remains `HOLD`; blocker remains `trial_loop_volume_and_modality_coverage` pending launch-gate-eligible real loop/modality threshold.)

## Execution Rules For GL Work

- Execute `GL-*` in numeric order unless a later card is explicitly marked as independent.
- Each run should complete exactly one task card.
- Every behavior change needs focused tests.
- Every document contract change needs doc-sync validation.
- Do not claim GA from dry-run output, relaxed flags, skipped Postgres checks, skipped coverage, skipped security checks, or stale evidence.
- Any customer-facing status must distinguish controlled external Beta, GA review, and platform Beta.
- Platformization work must not weaken the existing controlled-trial review requirement.

## Recommended Next Step

Proceed with `GL-19` (or next newly-defined GL card) to continue collecting launch-gate-eligible real external Beta loops and close the remaining readiness threshold gap (`>=10` complete real loops, `>=4` modalities).

Reason:

- `GL-01` through `GL-18` are complete; the batch intake path now supports mixed JSON directories without brittle failure and still supports strict contract enforcement.
- The remaining blocker is still real launch-gate-eligible loop/modality volume in baseline evidence, not contract/tooling coverage.
