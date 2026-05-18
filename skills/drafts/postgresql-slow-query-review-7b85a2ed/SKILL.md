# PostgreSQL Slow Query Review

## 判词
# PostgreSQL Slow Query Review

## 元信息
- skill_id: 7b85a2ed-ceb0-449d-b4df-3de31bfa4ca5
- version: 0.1.0
- skill_type: procedure
- audience: self
- source_modality: text
- review_status: draft
- confidence: 0.95
- created_at: 2026-04-20T12:06:06Z

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
- 6cae9ba1-163e-498c-9da7-f48a25970f21@paragraph:0001
- 268be78c-ae37-404c-a034-eee8e51b989e@paragraph:0002
- eca307f4-03b7-4b19-98a4-005193a51f59@paragraph:0003
- c8151765-7814-4249-97c8-0123a37a57f8@paragraph:0004
- 02ede0a9-df09-4c8d-8492-a3b3cd9a92df@paragraph:0005
- b6524d0c-f80f-4acf-91ad-c3e2c203fb57@paragraph:0006
- 943263ef-7bef-4e6a-afaf-d3ec5c75b527@paragraph:0007
- 45459108-9ae6-476a-9189-974270edfcb1@paragraph:0008
- 9f91859e-c935-4faa-af4e-2753ec3d33e3@paragraph:0009
- 7b15af7d-bd94-4b12-a01a-dc6fd89ee0ad@paragraph:0010
- e251141a-4595-4797-b94d-9159f6e02ff0@paragraph:0011

## 标签
- database
- text
- build_skill
- heuristic
