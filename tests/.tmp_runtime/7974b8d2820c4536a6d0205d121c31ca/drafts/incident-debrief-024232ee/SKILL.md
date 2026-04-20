# Incident Debrief

## 判词
1. Rebuild the incident timeline.

## 元信息
- skill_id: 024232ee-63c7-45f6-b589-f2a09211c224
- version: 0.1.0
- skill_type: decision
- audience: self
- source_modality: audio
- review_status: draft
- confidence: 0.72
- created_at: 2026-04-20T15:54:52Z

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
- 7788e46f-6299-4c16-896f-dcabcfd8d582@timestamp:0.00-3.00
- e2b1d4a1-b265-44d8-953d-31865ab8e576@timestamp:3.00-6.00
- 6161cccf-eaae-4893-bee7-913212684a2b@timestamp:6.00-9.00

## 标签
- ops
- audio
- build_skill
- heuristic
