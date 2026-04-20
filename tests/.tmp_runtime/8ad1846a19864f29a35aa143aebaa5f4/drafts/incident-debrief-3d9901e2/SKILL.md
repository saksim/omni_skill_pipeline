# Incident Debrief

## 判词
1. Rebuild the incident timeline.

## 元信息
- skill_id: 3d9901e2-fe63-4123-90b7-9af761d8f19f
- version: 0.1.0
- skill_type: decision
- audience: self
- source_modality: audio
- review_status: draft
- confidence: 0.72
- created_at: 2026-04-20T14:13:38Z

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
- a13d6701-1e6e-4fb6-a63f-7386b6d3203a@timestamp:0.00-3.00
- d7494332-14c8-4eac-9c26-c664c7e62846@timestamp:3.00-6.00
- 315d38d7-5671-4486-9713-70adbf238733@timestamp:6.00-9.00

## 标签
- ops
- audio
- build_skill
- heuristic
