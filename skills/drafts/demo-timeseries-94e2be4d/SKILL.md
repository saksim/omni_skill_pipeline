# demo timeseries

## 判词
Table schema summary Rows: 12 Columns: 5 1. Confirm row count and dtype assumptions before interpreting the table. 2. Normalize time zones, units, and duplicated keys before aggregation. If a column mixes numeric and string forms, clean it before trend analysis. Verify the busine

## 元信息
- skill_id: 94e2be4d-852a-45d5-bbed-2bba55922176
- version: 0.1.0
- skill_type: analysis
- audience: self
- source_modality: tabular
- review_status: draft
- confidence: 0.95
- created_at: 2026-04-20T12:06:08Z

## 目标
Distill incident_response material into a build_skill for self. Seed: Table schema summary Rows: 12 Columns: 5 1. Confirm row count and dtype assumptions before interpreting the table. 2. No

## 触发条件
- Use when you need to convert tabular evidence into a reusable build_skill.

## 输入
- Structured table or time-series dataset
- Distillation goal

## 前置条件
- If a column mixes numeric and string forms, clean it before trend analysis.
- If one entity dominates the sample, review entity bias before reading the global average.
- If latency_ms shows a long tail, inspect outliers before computing a baseline.
- If error_rate shows a long tail, inspect outliers before computing a baseline.
- If rps shows a long tail, inspect outliers before computing a baseline.

## 操作步骤
1. Confirm row count and dtype assumptions before interpreting the table.
Reason: Derived from normalized evidence and intended to preserve the original reasoning chain.
2. Normalize time zones, units, and duplicated keys before aggregation.
Reason: Derived from normalized evidence and intended to preserve the original reasoning chain.
3. timestamp :: str
Reason: Derived from normalized evidence and intended to preserve the original reasoning chain.
4. service :: str
Reason: Derived from normalized evidence and intended to preserve the original reasoning chain.
5. latency_ms :: int64
Reason: Derived from normalized evidence and intended to preserve the original reasoning chain.
6. error_rate :: float64
Reason: Derived from normalized evidence and intended to preserve the original reasoning chain.
7. rps :: int64
Reason: Derived from normalized evidence and intended to preserve the original reasoning chain.
8. Inspect the highest-missing columns before trusting downstream trends.
Reason: Derived from normalized evidence and intended to preserve the original reasoning chain.

## 决策规则
- If missingness jumps after a date boundary, inspect upstream ingestion or schema drift.
- If anomalies cluster near a timestamp boundary, inspect deploys, ingest gaps, or backfills first.
- If latency_ms deviates more than the rolling baseline, inspect deploys, schema changes, or data loss first.
- If error_rate deviates more than the rolling baseline, inspect deploys, schema changes, or data loss first.

## 反模式
- None

## 验证方式
- Verify the business grain of one row before building any skill from this table.
- Verify whether null means unavailable, zero, or not applicable in the source system.
- Verify extreme rows against source records and unit assumptions.
- Verify each anomaly against raw rows immediately before and after the flagged timestamp.
- Verify each flagged point against neighboring rows and source records.

## 证据链
- fb97c437-4f62-4b22-a06a-4b6c1d13f938@table:schema:0001
- 5a971037-119e-4a74-a00f-d6bf3ba52ea7@table:missingness:0001
- daa9d6fc-dcf1-4cd3-b80f-bea2d7a3dc9b@table:entities:0001
- 000c705d-c769-47fa-85bf-b42a3e47cc83@table:numeric:0001
- aa423517-1ae1-4de5-82d0-3bc9834dc4c1@table:numeric:0002
- 67794919-af9e-4b34-aa26-05a5d3b97fca@table:numeric:0003
- 2e32dcf1-e95b-4171-9745-4ea75eb602f1@timeseries:overview:0001
- f235e26d-2922-4159-8634-79e23d46c683@timeseries:metric:0001
- 93e756a5-8259-42eb-a687-d6afd1d37564@timeseries:metric:0002

## 标签
- incident_response
- tabular
- build_skill
- heuristic
