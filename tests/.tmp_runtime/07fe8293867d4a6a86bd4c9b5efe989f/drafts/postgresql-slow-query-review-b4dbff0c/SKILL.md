# PostgreSQL Slow Query Review

## 判词
PostgreSQL Slow Query Review

## 元信息
- skill_id: b4dbff0c-841b-45e4-9d00-d5f8fba0b6cd
- version: 0.1.0
- skill_type: procedure
- audience: self
- source_modality: text
- review_status: draft
- confidence: 0.77
- created_at: 2026-04-20T15:45:17Z

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
- b22aa88b-2507-49e4-b032-e8af28cb9dfc@section:1
- a2dd12d7-c135-48e0-83ae-2f4124722a46@section:1:paragraph:0001
- 1f9af28e-0d04-4038-9f6f-aa713753dbd2@section:1:paragraph:0002

## 标签
- database
- text
- build_skill
- heuristic
