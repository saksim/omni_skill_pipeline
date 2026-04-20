# PostgreSQL Slow Query Review

## 判词
# PostgreSQL Slow Query Review

## 元信息
- skill_id: 1d98b721-e64f-47ae-9ed2-96435760d2e9
- version: 0.1.0
- skill_type: procedure
- audience: self
- source_modality: text
- review_status: draft
- confidence: 0.77
- created_at: 2026-04-20T15:23:46Z

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
- 6f57b312-a925-4007-9cc9-e10e447902b4@paragraph:0001
- e728db83-9752-41e5-a1c0-32f4c1df1253@paragraph:0002
- 538d76bc-0c0b-4d22-b4db-2bd6055a8ce9@paragraph:0003

## 标签
- database
- text
- build_skill
- heuristic
