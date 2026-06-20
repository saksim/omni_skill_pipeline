# 最新文档

`docs/latest/` 是最新已发布手册层：这里的文档是今天应该使用的操作和参考材料。

当前发版候选内部版本：`v0.2.5-internal.2`。

本层用于：

- 描述当前系统的架构和数据流参考。
- 保存运行时或发布工具消费的 contracts、schemas 和 templates。
- 保存 API、CLI、worker、环境、测试和部署流程相关操作手册。

不要把迭代计划、生成证据或历史快照放在本层。

## 主要手册

- 操作入口：`operations/OPERATIONS.md`
- Runbook 入口：`operations/runbooks/README.md`
- GitHub Release 流程：`operations/runbooks/github-release-workflow.md`
- 真实数据接入：`operations/runbooks/real-data-intake-and-validation.md`
- Artifact 加密：`operations/runbooks/artifact-encryption.md`
- 环境变量：`operations/env.md`

## 边界

当前 latest 手册支持内部 dogfood 操作。外部 Beta、GA、SaaS、Docker/Postgres 生产验证、K8s、Vault/KMS、自动 key rotation 和 OCR hardening，都需要独立证据门禁通过后，才能被视为已完成 release claim。
