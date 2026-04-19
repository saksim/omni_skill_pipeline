# Incident Debrief

## 判词
1. Rebuild the incident timeline.

## 元信息
- skill_id: f2a0d2fc-90a4-490c-aace-d4ca71e55ded
- version: 0.1.0
- skill_type: decision
- audience: self
- source_modality: audio
- review_status: draft
- confidence: 0.72
- created_at: 2026-04-19T13:54:07Z

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
- 5ff52889-95fb-4560-a91e-633ae0cdb605@timestamp:0.00-3.00
- 9a182992-9304-4128-a810-f4f45d815cf7@timestamp:3.00-6.00
- 6baae87c-23f1-44c0-8513-71b9a0514a1b@timestamp:6.00-9.00

## 标签
- ops
- audio
- build_skill
- heuristic
