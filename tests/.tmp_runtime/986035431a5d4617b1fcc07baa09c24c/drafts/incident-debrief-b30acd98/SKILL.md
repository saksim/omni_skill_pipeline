# Incident Debrief

## 判词
1. Rebuild the incident timeline.

## 元信息
- skill_id: b30acd98-fc20-43db-a1f3-9c44cf3e13a2
- version: 0.1.0
- skill_type: decision
- audience: self
- source_modality: audio
- review_status: draft
- confidence: 0.72
- created_at: 2026-04-20T13:01:53Z

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
- 84e79b07-7fc2-4521-952e-c1b2a1bd9b9d@timestamp:0.00-3.00
- 816b9bc1-d431-443c-9c29-34cd9b8e2e1a@timestamp:3.00-6.00
- 861aaeb6-c36d-4cf5-ad60-3efe82bca937@timestamp:6.00-9.00

## 标签
- ops
- audio
- build_skill
- heuristic
