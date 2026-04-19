# PostgreSQL Slow Query Review

## 判词
# PostgreSQL Slow Query Review

## 元信息
- skill_id: f278a745-2970-40d6-b0c7-aa12cf985ee6
- version: 0.1.0
- skill_type: procedure
- audience: self
- source_modality: text
- review_status: draft
- confidence: 0.95
- created_at: 2026-04-19T13:52:06Z

## 目标
Distill database material into a build_skill for self. Seed: # PostgreSQL Slow Query Review

## 触发条件
- Use when you need to convert text evidence into a reusable build_skill.

## 输入
- Source document
- Distillation goal

## 前置条件
- This note captures a repeatable way to review slow SQL queries before blindly adding indexes.
- If the query is I/O bound, review index coverage before rewriting business logic.

## 操作步骤
1. Capture the worst queries from `pg_stat_statements`.
Reason: Derived from normalized evidence and intended to preserve the original reasoning chain.
2. Run `EXPLAIN ANALYZE` and compare the actual plan with the expected access path.
Reason: Derived from normalized evidence and intended to preserve the original reasoning chain.
3. Measure whether the bottleneck is I/O, CPU, or lock contention.
Reason: Derived from normalized evidence and intended to preserve the original reasoning chain.

## 决策规则
- If row estimates diverge sharply from actual rows, inspect stale statistics.

## 反模式
- Avoid adding overlapping indexes without calculating write amplification.
- Do not change the query text and the index strategy at the same time.

## 验证方式
- Verify the fix by comparing latency, buffer hits, and row estimates before and after the change.

## 证据链
- d047d775-16b8-41e1-b979-661e099d322f@paragraph:0001
- 8a83dc35-21cc-4dbf-a598-882734c7f97f@paragraph:0002
- 51f1518c-63d2-42ce-bca9-aeb3d344c4f9@paragraph:0003
- f14e142d-926a-416d-89ad-bfc5381a6902@paragraph:0004
- d22440bb-f41a-40eb-9dd0-7f8e4cbd25eb@paragraph:0005
- 1143b789-9c10-444a-afd0-ff63f9c5a457@paragraph:0006
- 0dfc3974-c132-46bb-b1c0-a4035fa753ce@paragraph:0007
- 9b03d248-6297-4308-81c2-f05bdf56c09d@paragraph:0008
- a0183ba7-1e09-46f2-8720-a8d985045ba4@paragraph:0009
- ee5cc3ac-262b-47a1-8c48-581f9aab76ff@paragraph:0010
- 46f4be3b-31b7-4047-bd83-b8f367d5fd93@paragraph:0011

## 标签
- database
- text
- build_skill
- heuristic
