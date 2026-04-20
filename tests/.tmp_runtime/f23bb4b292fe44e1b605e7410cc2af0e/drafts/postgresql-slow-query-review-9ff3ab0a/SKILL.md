# PostgreSQL Slow Query Review

## 判词
# PostgreSQL Slow Query Review

## 元信息
- skill_id: 9ff3ab0a-d158-43c9-950c-8d772e9281f2
- version: 0.1.0
- skill_type: procedure
- audience: self
- source_modality: text
- review_status: draft
- confidence: 0.77
- created_at: 2026-04-20T14:15:04Z

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
- 6bb19512-5ce6-4448-b829-360b1105a12c@paragraph:0001
- 2d7574d2-d0f2-4e5c-bc5f-b7ca19732438@paragraph:0002
- 338a172d-c42d-4d8d-a713-0e8903e2408e@paragraph:0003

## 标签
- database
- text
- build_skill
- heuristic
