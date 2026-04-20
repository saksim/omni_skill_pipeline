# Incident Walkthrough

## 判词
1. Rebuild the incident timeline.

## 元信息
- skill_id: 2a9e1636-547b-4d0a-94d3-0f400bf5c3b2
- version: 0.1.0
- skill_type: decision
- audience: self
- source_modality: video
- review_status: draft
- confidence: 0.85
- created_at: 2026-04-20T14:15:04Z

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
- 0a5ea583-15ac-44a6-adac-0cb64463ea60@video:timestamp:0.00-3.00
- 3244fed3-1f17-4a34-917c-feb93b158bd9@video:timestamp:3.00-6.00
- 03d49fd0-8422-484e-927b-915258841fb5@video:timestamp:6.00-9.00
- 068e8f07-558f-4db7-87d1-3fb90a1b69c6@frame:0001@1.00s:ocr
- dc584b0d-d9a6-4112-af71-649036cfceb6@frame:0001@1.00s:scene
- 9f2af2a6-4dc1-45ae-95a1-723dcb6e67b8@frame:0002@2.00s:ocr
- 6bee5b6f-4d14-4db3-ba5c-5fb6dc5a5660@frame:0002@2.00s:scene

## 标签
- incident_response
- video
- build_skill
- heuristic
