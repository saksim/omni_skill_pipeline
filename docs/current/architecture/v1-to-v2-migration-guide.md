# V1 -> V2 Migration Guide

## 判词

V2 切换必须在兼容层可回退的前提下推进。先守住 `TP-E8-03` 双写一致性，再确认 `TP-E10-02` 输出契约，最后切默认读取路径。

## 1. 迁移范围与前置条件

- 迁移范围：`distill_corpus` 输出结构、publication 读取路径、review 状态展示。
- 不在本轮范围：历史 artifact 重写、离线批量回灌。
- 前置条件：
  - `TP-E8-03` 已验证 file + postgres dual-write 一致性。
  - `TP-E10-02` 已验证 API V2 摘要字段兼容输出。
  - `TP-E13-01` 文档同步脚本可稳定通过。

## 2. 兼容层决策（何时保留 V1）

- 保留 V1 兼容层：
  - 外部消费者仍依赖 `skill_markdown` 或 legacy bundle 字段。
  - 生产环境尚未完成 V2 contract 回归。
- 切到 V2 主链：
  - 下游已消费 `graph_metadata / available_publications / review_status`。
  - runbook 回退路径已演练且可在变更窗口内完成。

## 3. 迁移步骤

1. 冻结窗口：锁定切换窗口，禁止并发 schema 变更。
2. 验证双写：执行 `TP-E8-03` 对应回归，确认 primary/secondary artifact 均可读取。
3. 验证 API 契约：执行 `TP-E10-02` 回归，确认 V2 摘要字段存在且 legacy 字段仍在。
4. 切默认读取：优先读 `publication_*` 与 graph metadata，legacy 字段改为 fallback。
5. 变更确认：检查最近批次 request 的 review/publish 状态是否连续、可追踪。

## 4. 回退策略

- 触发条件：
  - publication 读取失败率升高或字段缺失导致消费失败。
  - review_status 与 review_task 状态不一致。
- 回退动作：
  - 将默认读取切回 V1 兼容渲染层。
  - 保持 dual-write，不删除 V2 artifact。
  - 记录故障样本并冻结新增切换尝试。
- 回退验证：
  - 重新执行 `TP-E8-03` 与 `TP-E10-02`，确认回退后链路恢复。

## 5. 风险清单

- 契约漂移：文档与实际输出字段不一致，导致调用方误读。
- 兼容失效：legacy fallback 未覆盖边缘场景。
- 状态错位：review queue 与 publication 状态不同步。
- 运营误切：窗口外切换导致数据观测断裂。

## 6. 验收信号

- 连续两个批次输出同时满足：V2 摘要字段完整 + legacy fallback 可用。
- 回退演练可在目标窗口内完成且不丢失 artifact 引用。
