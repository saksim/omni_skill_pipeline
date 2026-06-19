# Internal Dogfood Launch Docs

本目录存放“内部玩具上线 / Internal Dogfood Launch”的细则施工文档。

## 文档入口

- [主施工计划](../2026-06-18-internal-dogfood-launch-construction-plan.md)
- [P0 Workflow Fail Remediation](p0-workflow-fail-remediation.md)
- [Internal Dogfood Gate Spec](internal-dogfood-gate-spec.md)
- [Verification Runbook](verification-runbook.md)
- [Risk, Rollback, and Observation](risk-rollback-observation.md)
- [Launch Record Template](launch-record-template.md)

## 口径

内部 dogfood 不是外部 Beta，不是 GA，也不是 SaaS。

它只证明：

- 当前代码可被内部人员启动。
- CI 和基础 smoke 不存在硬失败。
- 生成能力可以被内部试用。
- 所有风险和限制都有记录。

它不证明：

- 存在真实业务闭环。
- 可以对外承诺稳定性。
- 可以跳过人工 review。
- 可以替代 `scripts/launch_gate.py` 的外部上线判断。
