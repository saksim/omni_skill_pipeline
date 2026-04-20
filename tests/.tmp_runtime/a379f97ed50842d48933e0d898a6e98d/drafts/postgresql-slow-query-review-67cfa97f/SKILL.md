# PostgreSQL Slow Query Review

## 判词
PostgreSQL Slow Query Review

## 元信息
- skill_id: 67cfa97f-1f7d-4012-896e-4ff65604b275
- version: 0.1.0
- skill_type: procedure
- audience: self
- source_modality: text
- review_status: draft
- confidence: 0.77
- created_at: 2026-04-20T15:53:13Z

## 目标
Distill database material into a build_skill for self. Seed: PostgreSQL Slow Query Review

## 触发条件
- Use when you need to convert text evidence into a reusable build_skill.

## 输入
- Source document
- Distillation goal

## 前置条件
- Confirm the source material matches the declared distillation goal.

## 操作步骤
1. Capture the top slow queries from pg_stat_statements.
Reason: Derived from normalized evidence and intended to preserve the original reasoning chain.
2. Compare execution plans before changing indexes.
Reason: Derived from normalized evidence and intended to preserve the original reasoning chain.

## 决策规则
- If the query is I/O bound, review the missing indexes first.

## 反模式
- Avoid adding overlapping indexes without measuring write amplification.

## 验证方式
- Verify the new plan with EXPLAIN ANALYZE and compare latency.

## 证据链
- 06f9bda2-e450-46d8-9f0e-442348141dff@section:1
- e2160afb-c26a-47bb-bf7e-30ecec40db8d@section:1:paragraph:0001
- 1f712aa6-036b-4cc8-950c-dbcfffbbea33@section:1:paragraph:0002

## 标签
- database
- text
- build_skill
- heuristic
