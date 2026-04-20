# Incident Walkthrough

## 判词
1. Rebuild the incident timeline.

## 元信息
- skill_id: b6396d5c-85c8-42f1-b030-005b2ff2cb01
- version: 0.1.0
- skill_type: decision
- audience: self
- source_modality: video
- review_status: draft
- confidence: 0.85
- created_at: 2026-04-20T16:21:33Z

## 目标
Distill incident_response material into a build_skill for self. Seed: 1. Rebuild the incident timeline.

## 触发条件
- Use when you need to convert video evidence into a reusable build_skill.

## 输入
- Video source
- Distillation goal
- Keyframe/OCR evidence

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
- 49ee4cc6-6166-40b1-8908-39194a373507@video:timestamp:0.00-3.00
- 9596d2dd-7746-4fd8-83da-153f0d7ff244@video:timestamp:3.00-6.00
- 4ed41117-19b6-44be-af42-394cbfed9d1c@video:timestamp:6.00-9.00
- c08b1c5d-e103-4cd5-a8df-4daf1e879f40@frame:0001@1.00s:ocr
- 2f968922-9ca1-447a-99b9-e3e4a9c34daa@frame:0001@1.00s:scene
- 3c8a6ff7-f582-4a70-87cd-8e25d60e4553@frame:0002@2.00s:ocr
- aad61dff-e8fd-4264-ba35-dc71b468af96@frame:0002@2.00s:scene

## 标签
- incident_response
- video
- build_skill
- heuristic
