# PostgreSQL Slow Query Review

## 判词
PostgreSQL Slow Query Review

## 元信息
- skill_id: 75a14e17-c361-48e0-a380-a598bb10e38f
- version: 0.1.0
- skill_type: procedure
- audience: self
- source_modality: text
- review_status: draft
- confidence: 0.77
- created_at: 2026-04-20T15:54:52Z

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
- 5e1e1a8d-1e5c-431f-aae2-b45b431a1b5e@section:1
- 309e2d09-198c-48ae-9ec0-7ddfc36f69dd@section:1:paragraph:0001
- 8c009254-ea26-4e3e-a0b8-cd8d52370a22@section:1:paragraph:0002

## 标签
- database
- text
- build_skill
- heuristic
