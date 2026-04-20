# Incident Walkthrough

## 判词
1. Rebuild the incident timeline.

## 元信息
- skill_id: 72af442f-0521-4e19-bce8-7c89d4dbe494
- version: 0.1.0
- skill_type: decision
- audience: self
- source_modality: video
- review_status: draft
- confidence: 0.85
- created_at: 2026-04-20T13:20:00Z

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
- 4e095582-69de-4958-a169-62724e2eb5c2@video:timestamp:0.00-3.00
- 991eda0e-4e2a-43fd-a7ff-3f7ea778229b@video:timestamp:3.00-6.00
- 5dc8a24c-a4de-4070-89b2-165375c8e5c7@video:timestamp:6.00-9.00
- 933ae18b-3719-41ab-9ff2-8ac9ad417c7c@frame:0001@1.00s:ocr
- ffb1002a-b7df-4a0f-a0d3-7104deaeb0e5@frame:0001@1.00s:scene
- 9d7c71a7-7a1e-41fa-8743-f3d3da1bd536@frame:0002@2.00s:ocr
- 47791196-69cb-4709-9edb-35c1ee4ec56a@frame:0002@2.00s:scene

## 标签
- incident_response
- video
- build_skill
- heuristic
