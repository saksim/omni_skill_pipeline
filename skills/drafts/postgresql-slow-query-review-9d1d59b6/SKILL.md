# PostgreSQL Slow Query Review

## 判词
# PostgreSQL Slow Query Review

## 元信息
- skill_id: 9d1d59b6-ae5f-4570-9864-fb1c6b86f8cd
- version: 0.1.0
- skill_type: procedure
- audience: self
- source_modality: text
- review_status: draft
- confidence: 0.95
- created_at: 2026-04-19T13:02:09Z

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
- 2c13daad-4b7b-472d-b392-e56f92660bb7@paragraph:0001
- ad5df780-f101-4de3-9a8d-331d79c5f39a@paragraph:0002
- e99975e5-1457-4958-b760-e422e24620c3@paragraph:0003
- 89649571-0e2e-4773-a42a-787c61a71e8b@paragraph:0004
- 117420a9-9b19-4189-8664-e711c03b7207@paragraph:0005
- eb4db591-cc97-4e2d-b994-1bf78250830b@paragraph:0006
- 616e1a80-bfa1-416c-929a-bdd0c5752dfc@paragraph:0007
- 4634db72-def8-414f-9a5d-e0f691060336@paragraph:0008
- a9457bf8-9364-42d4-ab82-2db14fcc36e8@paragraph:0009
- b031dbc7-63dc-4d16-8de4-19a5286774b7@paragraph:0010
- f7b9f626-437d-4cf9-b470-e4660a0dcc1d@paragraph:0011

## 标签
- database
- text
- build_skill
