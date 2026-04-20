# PostgreSQL Slow Query Review

## 判词
# PostgreSQL Slow Query Review

## 元信息
- skill_id: 3339f168-9ad9-439f-8386-24c67dde9cba
- version: 0.1.0
- skill_type: procedure
- audience: self
- source_modality: text
- review_status: draft
- confidence: 0.77
- created_at: 2026-04-20T15:00:05Z

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
- 0efcb9a5-ca6c-4036-8507-ce4e3a6d29ea@paragraph:0001
- b5e13fe4-6719-43fc-aecb-2a8180b1fce5@paragraph:0002
- 133189bf-d972-4f1a-8749-7a8fd94f12d2@paragraph:0003

## 标签
- database
- text
- build_skill
- heuristic
