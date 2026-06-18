# Docs Index

The documentation tree is split by lifecycle stage. Use the layer name as the first routing decision.

## Layers

- [latest/](latest/README.md): latest published manuals and current operating references.
- [working/](working/README.md): active iteration status, plans, backlogs, baselines, and evidence.
- [releases/](releases/README.md): changelog, release standards, and dated release decision snapshots.
- [archive/](archive/README.md): historical assessments and superseded status snapshots.

## Latest

### Architecture

- [Architecture](latest/architecture/ARCHITECTURE.md)
- [System Overview](latest/architecture/system-overview.md)
- [Data Flow](latest/architecture/data-flow.md)
- [Storage](latest/architecture/storage.md)
- [Skill Distillation V2](latest/architecture/skill-distillation-v2.md)
- [Agent Skill Package Model](latest/architecture/agent-skill-package-model.md)
- [Portable Skill Renderer](latest/architecture/portable-skill-renderer.md)
- [Lifecycle Decision Engine](latest/architecture/lifecycle-decision-engine.md)
- [Providers](latest/architecture/providers.md)
- [Review Queue Operations Surface](latest/architecture/review-queue-operations-surface.md)
- [Retrieval Backend Decision](latest/architecture/retrieval-backend-decision.md)
- [Publication Multi-View Baseline](latest/architecture/publication-multi-view-baseline.md)
- [V1 to V2 Migration Guide](latest/architecture/v1-to-v2-migration-guide.md)

### Contracts

- [Skill Schema](latest/contracts/skill.schema.json)
- [Skill Graph Schema](latest/contracts/skill-graph.schema.json)
- [Skill Template](latest/contracts/SKILL.template.md)

### Operations

- [Operations](latest/operations/OPERATIONS.md)
- [API](latest/operations/api.md)
- [CLI](latest/operations/cli.md)
- [Environment](latest/operations/env.md)
- [Worker](latest/operations/worker.md)
- [Testing](latest/operations/testing.md)
- [Script Name Map](latest/operations/script-name-map.md)
- [Runbooks](latest/operations/runbooks/README.md)

## Working

- [Current Status](working/status/CURRENT_STATUS.md)
- [Launch Readiness Master Plan](working/status/launch-readiness-master-plan.md)
- [Distillation Platform Strategy Assessment](working/status/2026-05-17-distillation-platform-strategy-assessment.md)
- [Controlled Business Trial Iteration](working/status/2026-05-18-controlled-business-trial-iteration.md)
- [Broad Product Launch Plan](working/status/2026-05-25-broad-product-launch-plan.md)
- [项目卡点评估（2026-06-18）](working/status/2026-06-18-project-blocker-assessment.md)
- [内部玩具上线施工计划（2026-06-18）](working/status/2026-06-18-internal-dogfood-launch-construction-plan.md)
- [Internal Dogfood Launch Docs](working/status/internal-dogfood-launch/README.md)
- [Internal Dogfood Readiness Report](working/status/baselines/internal-dogfood-readiness-report.json)
- [Internal Dogfood Readiness Summary](working/status/baselines/internal-dogfood-readiness-summary.md)
- [Internal Dogfood API Health Report](working/status/baselines/internal-dogfood-api-health-report.json)
- [Internal Dogfood Launch Record 20260618T0643Z](working/status/baselines/internal-dogfood-launch-20260618T0643Z-summary.md)
- [Internal Dogfood Launch Record 20260618T0656Z](working/status/baselines/internal-dogfood-launch-20260618T0656Z-summary.md)
- [Skill Distillation V2 Roadmap](working/architecture/skill-distillation-v2-roadmap.md)
- [Skill Distillation V2 Implementation Backlog](working/architecture/skill-distillation-v2-implementation-backlog.md)
- [Skill Distillation V2 Work Orders](working/architecture/skill-distillation-v2-work-orders.md)
- [Baseline Pack](working/status/baselines/README.md)

## Releases

- [Changelog](releases/CHANGELOG.md)
- [V2 Release Switch Standard](releases/standards/v2-release-switch-standard.md)
- [2026-04-26 V2 Release Switch Snapshot](releases/status/2026-04-26-v2-release-switch-standard.md)

## Archive

- [GLM-5.1 Assessment Redirect](archive/assessments/glm-5.1-project-assessment.md)
- [Archived GLM-5.1 Assessment](archive/assessments/2026-04-22-glm-5.1-project-assessment.md)
- [Archived Pre-Launch Status](archive/status/2026-04-24-current-status-pre-launch-master-plan.md)

## Rules

- Root directory keeps only [README.md](../README.md) as the primary entry document.
- `docs/latest/` is the only layer that should be treated as the current published manual.
- `docs/working/` may change during an iteration and may contain generated evidence.
- `docs/releases/` records release decisions and changelog history.
- `docs/archive/` is retained for traceability and should not drive current operation.
