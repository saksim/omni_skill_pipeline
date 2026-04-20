# PostgreSQL Slow Query Review

## 判词
PostgreSQL Slow Query Review

## 元信息
- skill_id: a3e80d4c-1f1a-4bd4-91ae-1b8d9d5dde0c
- version: 0.1.0
- skill_type: procedure
- audience: self
- source_modality: text
- review_status: draft
- confidence: 0.77
- created_at: 2026-04-20T16:21:33Z

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
- 1a70c6c6-9463-4246-addd-978d93b9634a@section:1
- 56d618e1-1a2e-4c81-9bc2-800624ee877d@section:1:paragraph:0001
- 75ff662f-27fe-4ca5-a73c-eb33e3d9457e@section:1:paragraph:0002

## 标签
- database
- text
- build_skill
- heuristic
