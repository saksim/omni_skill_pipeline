# PostgreSQL Slow Query Review

## 判词
# PostgreSQL Slow Query Review

## 元信息
- skill_id: 6ca4ced9-71a8-4c4b-b7d3-a92f6929036d
- version: 0.1.0
- skill_type: procedure
- audience: self
- source_modality: text
- review_status: draft
- confidence: 0.95
- created_at: 2026-04-19T13:54:34Z

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
- 7c5dcb78-4bb8-4035-85af-d4b0b57b9dfd@paragraph:0001
- c2c211e5-0c3f-46aa-8f29-9a733a87e54b@paragraph:0002
- d6003682-aa57-47c0-8e5a-d9c47a3914b2@paragraph:0003
- 091dce6d-d676-45d0-b26e-4e9b8cee0b9d@paragraph:0004
- 51848cbe-782a-409f-aa66-6dc38e370820@paragraph:0005
- ef533090-62ab-4bdb-94af-6fd6186633e6@paragraph:0006
- ea1c71c4-18e5-4e23-8ce5-94421ea7efc5@paragraph:0007
- 34efa572-9bd8-4a3e-83a6-d75f64458858@paragraph:0008
- e2feaf12-5821-4911-82be-7e40402b8e09@paragraph:0009
- 96dd9984-f591-417c-a581-11e3488cbd54@paragraph:0010
- 233a0a20-86cd-4425-98c9-67db331aa6fa@paragraph:0011

## 标签
- database
- text
- build_skill
- heuristic
