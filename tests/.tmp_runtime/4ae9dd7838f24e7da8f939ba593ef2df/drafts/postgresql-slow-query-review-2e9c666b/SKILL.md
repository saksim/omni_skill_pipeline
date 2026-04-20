# PostgreSQL Slow Query Review

## 判词
# PostgreSQL Slow Query Review

## 元信息
- skill_id: 2e9c666b-7298-45ba-9ab0-d0e128bcaf9e
- version: 0.1.0
- skill_type: procedure
- audience: self
- source_modality: text
- review_status: draft
- confidence: 0.77
- created_at: 2026-04-20T14:13:38Z

## 目标
Distill database material into a build_skill for self. Seed: # PostgreSQL Slow Query Review

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
- d93fd792-8d98-4afa-ad36-e87b2d62ceb1@paragraph:0001
- 87184581-2e0c-44ef-92a5-c2e7f5df5c39@paragraph:0002
- 001bddeb-7cb2-40ec-82bd-fe44921a27b1@paragraph:0003

## 标签
- database
- text
- build_skill
- heuristic
