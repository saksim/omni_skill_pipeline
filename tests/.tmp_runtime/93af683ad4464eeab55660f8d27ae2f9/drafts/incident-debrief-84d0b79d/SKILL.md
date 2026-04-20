# Incident Debrief

## 判词
1. Rebuild the incident timeline.

## 元信息
- skill_id: 84d0b79d-ac10-4cb4-bfda-a64af802b988
- version: 0.1.0
- skill_type: decision
- audience: self
- source_modality: audio
- review_status: draft
- confidence: 0.72
- created_at: 2026-04-20T15:00:05Z

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
- 7e5376d5-dd95-4172-b87b-f8694bb11b78@timestamp:0.00-3.00
- 653b8b18-76ed-4cf8-a1b4-db5740acc171@timestamp:3.00-6.00
- d41be1a0-4ab2-4247-9dfb-d500da2b7707@timestamp:6.00-9.00

## 标签
- ops
- audio
- build_skill
- heuristic
