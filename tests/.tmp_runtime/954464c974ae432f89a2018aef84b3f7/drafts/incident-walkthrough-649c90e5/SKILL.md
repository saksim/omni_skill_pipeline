# Incident Walkthrough

## 判词
1. Rebuild the incident timeline.

## 元信息
- skill_id: 649c90e5-b3f9-4dc9-8963-7d9a892bebac
- version: 0.1.0
- skill_type: decision
- audience: self
- source_modality: video
- review_status: draft
- confidence: 0.85
- created_at: 2026-04-20T12:31:18Z

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
- 716049cd-9cd8-4c6b-a5c5-f566f60b765a@video:timestamp:0.00-3.00
- 2c4ead14-a8cd-4cdd-8b7e-5c917576d67a@video:timestamp:3.00-6.00
- 9546f28b-4d20-4dc8-9421-1c4e1fa7a213@video:timestamp:6.00-9.00
- b4a6edce-4808-4677-bcb6-1d4c4ce4d5fc@frame:0001@1.00s:ocr
- 9894030b-acaf-4863-b163-e5a93bca3474@frame:0001@1.00s:scene
- 266e339d-b916-40d6-910d-d59cab9b0702@frame:0002@2.00s:ocr
- 2a382944-2e7a-4c3a-bd41-3ad11ff93eb9@frame:0002@2.00s:scene

## 标签
- incident_response
- video
- build_skill
- heuristic
