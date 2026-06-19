# 文档索引

本项目文档按生命周期分层。判断该看哪份文档时，先看文档所在层级。

## 分层

- [latest/](latest/README.md)：最新已发布手册和当前操作参考。
- [working/](working/README.md)：当前迭代状态、计划、backlog、baseline 和证据。
- [releases/](releases/README.md)：changelog、发布说明、发布标准和带日期的发布决策快照。
- [archive/](archive/README.md)：历史评估、已替代状态快照和已完成能力归档。

## 最新手册（latest）

### 架构

- [架构总览](latest/architecture/ARCHITECTURE.md)
- [系统总览](latest/architecture/system-overview.md)
- [数据流](latest/architecture/data-flow.md)
- [存储](latest/architecture/storage.md)
- [Skill Distillation V2](latest/architecture/skill-distillation-v2.md)
- [Agent Skill Package 模型](latest/architecture/agent-skill-package-model.md)
- [Portable Skill Renderer](latest/architecture/portable-skill-renderer.md)
- [Lifecycle Decision Engine](latest/architecture/lifecycle-decision-engine.md)
- [Providers](latest/architecture/providers.md)
- [Review Queue 操作面](latest/architecture/review-queue-operations-surface.md)
- [Retrieval Backend 决策](latest/architecture/retrieval-backend-decision.md)
- [Publication Multi-View 基线](latest/architecture/publication-multi-view-baseline.md)
- [V1 到 V2 迁移指南](latest/architecture/v1-to-v2-migration-guide.md)

### 契约

- [Skill Schema](latest/contracts/skill.schema.json)
- [Skill Graph Schema](latest/contracts/skill-graph.schema.json)
- [Skill 模板](latest/contracts/SKILL.template.md)

### 操作

- [操作入口](latest/operations/OPERATIONS.md)
- [API](latest/operations/api.md)
- [CLI](latest/operations/cli.md)
- [环境变量](latest/operations/env.md)
- [Worker](latest/operations/worker.md)
- [测试](latest/operations/testing.md)
- [脚本命名映射](latest/operations/script-name-map.md)
- [Runbook 入口](latest/operations/runbooks/README.md)
- [操作环境](latest/operations/environments/README.md)
- [操作接口](latest/operations/interfaces/README.md)

## 当前迭代（working）

- [当前状态](working/status/CURRENT_STATUS.md)
- [上线 readiness 总计划](working/status/launch-readiness-master-plan.md)
- [蒸馏平台战略评估](working/status/2026-05-17-distillation-platform-strategy-assessment.md)
- [受控业务试运行迭代](working/status/2026-05-18-controlled-business-trial-iteration.md)
- [广义产品上线计划](working/status/2026-05-25-broad-product-launch-plan.md)
- [项目卡点评估 2026-06-18](working/status/2026-06-18-project-blocker-assessment.md)
- [内部 dogfood 上线施工计划 2026-06-18](working/status/2026-06-18-internal-dogfood-launch-construction-plan.md)
- [内部 dogfood 上线文档](working/status/internal-dogfood-launch/README.md)
- [内部 dogfood readiness 摘要](working/status/baselines/internal-dogfood-readiness-summary.md)
- [内部 dogfood API smoke 摘要](working/status/baselines/internal-dogfood-api-smoke-summary.md)
- [内部 dogfood container smoke 摘要](working/status/baselines/internal-dogfood-container-smoke-summary.md)
- [Real Trial Evidence Hygiene 20260618T0926Z](working/status/baselines/real-trial-evidence-hygiene-20260618T0926Z.md)
- [Real Trial GL62 Escalation 20260618T0935Z](working/status/baselines/real-trial-gl62-escalation-20260618T0935Z.md)
- [Real Trial GL63 Intake Workpack 20260619T0312Z](working/status/baselines/real-trial-gl63-intake-workpack-20260619T0312Z.md)
- [Real Trial GL64 Manifest Preflight 20260619T0322Z](working/status/baselines/real-trial-gl64-manifest-preflight-20260619T0322Z.md)
- [Skill Distillation V2 路线图](working/architecture/skill-distillation-v2-roadmap.md)
- [Skill Distillation V2 实施 backlog](working/architecture/skill-distillation-v2-implementation-backlog.md)
- [Skill Distillation V2 施工单](working/architecture/skill-distillation-v2-work-orders.md)
- [Baseline 包](working/status/baselines/README.md)
- [操作文档审计 2026-06-19](working/status/2026-06-19-operations-docs-audit.md)

## 发布（releases）

- [Changelog](releases/CHANGELOG.md)
- [发布说明](releases/notes/README.md)
- [v0.2.3-internal.1 发布说明](releases/notes/v0.2.3-internal.1.md)
- [v0.2.2-internal.1 发布说明](releases/notes/v0.2.2-internal.1.md)
- [v0.2.1-internal.1 发布说明](releases/notes/v0.2.1-internal.1.md)
- [v0.2.0-internal.1 发布说明](releases/notes/v0.2.0-internal.1.md)
- [V2 Release Switch 标准](releases/standards/v2-release-switch-standard.md)
- [2026-04-26 V2 Release Switch 快照](releases/status/2026-04-26-v2-release-switch-standard.md)

## 归档（archive）

- [已完成能力归档 2026-06-19](archive/status/2026-06-19-completed-capabilities-archive.md)
- [GLM-5.1 评估跳转](archive/assessments/glm-5.1-project-assessment.md)
- [GLM-5.1 原始评估归档](archive/assessments/2026-04-22-glm-5.1-project-assessment.md)
- [Pre-Launch Status 归档](archive/status/2026-04-24-current-status-pre-launch-master-plan.md)

## 规则

- 根目录只保留 [README.md](../README.md) 作为主入口。
- `docs/latest/` 是唯一应被视为“当前已发布手册”的层。
- `docs/working/` 可在迭代中变化，也可以包含生成证据。
- `docs/releases/` 记录发布决策和 changelog 历史。
- `docs/archive/` 仅用于可追溯性，不驱动当前操作。
