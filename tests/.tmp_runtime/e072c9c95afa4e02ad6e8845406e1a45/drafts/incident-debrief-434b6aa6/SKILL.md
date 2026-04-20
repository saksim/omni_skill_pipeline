# Incident Debrief

## 判词
1. Rebuild the incident timeline.

## 元信息
- skill_id: 434b6aa6-bd94-40c0-8c86-cdb049f8f786
- version: 0.1.0
- skill_type: decision
- audience: self
- source_modality: audio
- review_status: draft
- confidence: 0.72
- created_at: 2026-04-20T15:23:46Z

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
- 278410e8-77bf-4be6-861c-1478d7936943@timestamp:0.00-3.00
- 57de53c8-ccfb-4ec4-a3f8-b585a4744130@timestamp:3.00-6.00
- c62d4246-2392-4aac-b787-8b223a91bad5@timestamp:6.00-9.00

## 标签
- ops
- audio
- build_skill
- heuristic
