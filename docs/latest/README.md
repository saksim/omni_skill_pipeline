# 最新文档

`docs/latest/` 是最新已发布手册层：这里的文档是今天应该使用的操作和参考材料。

当前发版候选内部版本：`v0.2.5-internal.2`。

本层用于：

- 描述当前系统的架构和数据流参考。
- 保存运行时或发布工具消费的 contracts、schemas 和 templates。
- 保存 API、CLI、worker、环境、测试和部署流程相关操作手册。
- 保存真实数据接入、质量门禁、GL-64 preflight 和 launch gate 的当前验收口径。

不要把迭代计划、生成证据或历史快照放在本层。

## 主要手册

- 操作入口：`operations/OPERATIONS.md`
- Runbook 入口：`operations/runbooks/README.md`
- GitHub Release 流程：`operations/runbooks/github-release-workflow.md`
- 真实数据接入：`operations/runbooks/real-data-intake-and-validation.md`
- Artifact 加密：`operations/runbooks/artifact-encryption.md`
- 环境变量：`operations/env.md`
- Strict launch gate：`operations/testing.md` 和 `operations/script-name-map.md`

## 边界

当前 latest 手册支持内部 dogfood 操作。外部 Beta、GA、SaaS、Docker/Postgres 生产验证、K8s、Vault/KMS、自动 key rotation 和 OCR hardening，都需要独立证据门禁通过后，才能被视为已完成 release claim。

当前外部 Beta 的主要阻塞不是功能手册缺失，而是缺少可被 `launch_gate.py` 承认的真实闭环证据。解除该阻塞需要 10 个脱敏 manifest 槽位、覆盖 `text/audio/image/video`，并且每条 loop 都有 source trace、expected/review/run evidence、quality gate 和 agent smoke 记录。
