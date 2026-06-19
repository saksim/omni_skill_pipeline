# 内部 Dogfood 上线文档

本目录保存内部 dogfood 上线轨道的 working-level 施工与验证文档。

当前操作手册请使用 `docs/latest/operations/`。只有需要追溯历史施工计划、gate 细则、上线记录模板或内部 dogfood 决策背后的风险说明时，才使用本目录。

## 文档

- [施工计划](../2026-06-18-internal-dogfood-launch-construction-plan.md)
- [P0 Workflow Fail Remediation](p0-workflow-fail-remediation.md)
- [Internal Dogfood Gate Spec](internal-dogfood-gate-spec.md)
- [验证 Runbook](verification-runbook.md)
- [Risk, Rollback, and Observation](risk-rollback-observation.md)
- [Launch Record Template](launch-record-template.md)

## 边界

内部 dogfood 不是外部 Beta、GA 或 SaaS。

它证明：

- 内部操作人员可以启动当前代码。
- CI 和基础 smoke 对内部路径不存在阻断性失败。
- 生成的 skill 可以被内部 review 和使用。
- 限制与 rollback 点已经记录。

它不证明：

- 真实外部业务闭环覆盖。
- 生产 uptime 或公开可靠性。
- 可以安全跳过人工 review 自动发布。
- 可以替代 `scripts/launch_gate.py` 的外部上线判断。
