# Incident Debrief

## 判词
1. Rebuild the incident timeline.

## 元信息
- skill_id: 94a1674f-3df5-4f69-afa0-8c686d6b2cad
- version: 0.1.0
- skill_type: decision
- audience: self
- source_modality: audio
- review_status: draft
- confidence: 0.72
- created_at: 2026-04-19T13:52:06Z

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
- 2532d4e8-423b-40dd-8610-82a4d20e0987@timestamp:0.00-3.00
- 438e6bc0-7947-47c7-ad4a-072bcd5c8137@timestamp:3.00-6.00
- 791503a9-df6f-4fb9-b1d1-8687f8b7a875@timestamp:6.00-9.00

## 标签
- ops
- audio
- build_skill
- heuristic
