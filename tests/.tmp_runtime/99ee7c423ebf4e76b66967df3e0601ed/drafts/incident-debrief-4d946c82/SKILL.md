# Incident Debrief

## 判词
1. Rebuild the incident timeline.

## 元信息
- skill_id: 4d946c82-9edd-4c40-883e-77df9daaa333
- version: 0.1.0
- skill_type: decision
- audience: self
- source_modality: audio
- review_status: draft
- confidence: 0.72
- created_at: 2026-04-20T15:53:13Z

## 目标
Distill ops material into a build_skill for self. Seed: 1. Rebuild the incident timeline.

## 触发条件
- Use when you need to convert audio evidence into a reusable build_skill.

## 输入
- Audio source or transcript
- Distillation goal

## 前置条件
- Confirm the source material matches the declared distillation goal.

## 操作步骤
1. Rebuild the incident timeline.
Reason: Derived from normalized evidence and intended to preserve the original reasoning chain.

## 决策规则
- If alerts duplicate, merge them into one incident stream.

## 反模式
- None

## 验证方式
- Verify recovery with error rate and latency.

## 证据链
- 5b6d528c-bf43-4abc-8037-98d9ee101183@timestamp:0.00-3.00
- b052af40-9b33-4522-b6d0-892902224164@timestamp:3.00-6.00
- 6ee3dfd9-be9d-432e-a835-d456df553d98@timestamp:6.00-9.00

## 标签
- ops
- audio
- build_skill
- heuristic
