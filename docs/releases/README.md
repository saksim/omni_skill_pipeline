# 发布文档

`docs/releases/` 是发布层：记录本次发了什么、做了什么决策，以及发布遵循哪个标准。

本层用于：

- 变更日志条目和发布说明。
- GitHub Release 使用的人类可读发布说明，位于 [notes/](notes/README.md)。
- Release switch 标准和 gate 定义。
- 带日期的发布决策快照。

长期维护的操作手册应放在 `docs/latest/`；已替代的历史上下文应移入 `docs/archive/`。

跨多个 release 汇总的已完成能力，应在相关 release 真正发布后归档到 `docs/archive/status/`。当前记录：`docs/archive/status/2026-06-19-completed-capabilities-archive.md`。

当前发版候选：`v0.2.5-internal.2`。本轮 release 重点是在没有真实业务数据时收敛为内部 dogfood 口径，并补齐后续真实数据接入、验收和归档文档。
