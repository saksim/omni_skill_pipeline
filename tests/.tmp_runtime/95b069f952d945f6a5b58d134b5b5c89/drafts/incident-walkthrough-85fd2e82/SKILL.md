# Incident Walkthrough

## 判词
1. Rebuild the incident timeline.

## 元信息
- skill_id: 85fd2e82-2687-4394-aaee-5e0c9135f82d
- version: 0.1.0
- skill_type: decision
- audience: self
- source_modality: video
- review_status: draft
- confidence: 0.85
- created_at: 2026-04-19T14:17:22Z

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
- ced8104b-9c7f-4c33-ae68-aa44bb2330f5@video:timestamp:0.00-3.00
- cfc1d77f-7865-4fc7-8c86-0ed8df1dd33b@video:timestamp:3.00-6.00
- c34db099-bf49-4828-bcf0-d509f32cd12a@video:timestamp:6.00-9.00
- fe37234b-c89f-489c-9ddb-6380daea543a@frame:0001:ocr
- 356f3df7-8add-44d0-99d4-3e3cadf537c5@frame:0001:scene
- 6508205c-2a7f-4a27-923c-b9cb57d5f6b3@frame:0002:ocr
- 90117d1a-252f-4cef-b747-eb266266f181@frame:0002:scene

## 标签
- incident_response
- video
- build_skill
- heuristic
