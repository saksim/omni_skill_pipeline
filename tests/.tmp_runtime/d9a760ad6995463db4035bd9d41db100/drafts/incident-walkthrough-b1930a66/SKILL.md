# Incident Walkthrough

## 判词
1. Rebuild the incident timeline.

## 元信息
- skill_id: b1930a66-5574-4489-a95e-6ec6c426d57b
- version: 0.1.0
- skill_type: decision
- audience: self
- source_modality: video
- review_status: draft
- confidence: 0.85
- created_at: 2026-04-20T15:23:46Z

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
- ecd376fa-d054-477f-b597-967a63e4fc97@video:timestamp:0.00-3.00
- 98208856-c73a-43d4-9e11-78d9fc13d5d0@video:timestamp:3.00-6.00
- 08b4d9d6-4a01-4fd3-ab7b-8ffd9d45f78e@video:timestamp:6.00-9.00
- a1a58f4d-a32e-4975-b6fe-d281694e08d2@frame:0001@1.00s:ocr
- 0458a35c-5554-44f9-a6b4-922189fccfee@frame:0001@1.00s:scene
- b82b55ae-3a85-427f-9d5b-018d66d5ff8f@frame:0002@2.00s:ocr
- 0cf3adf1-fcac-4e6c-a953-1f9c2c2ba823@frame:0002@2.00s:scene

## 标签
- incident_response
- video
- build_skill
- heuristic
