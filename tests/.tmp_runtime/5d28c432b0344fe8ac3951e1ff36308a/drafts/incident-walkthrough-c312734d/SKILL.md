# Incident Walkthrough

## 判词
1. Rebuild the incident timeline.

## 元信息
- skill_id: c312734d-bedf-4d22-b056-78a17ebdfdfb
- version: 0.1.0
- skill_type: decision
- audience: self
- source_modality: video
- review_status: draft
- confidence: 0.85
- created_at: 2026-04-20T15:45:17Z

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
- bae07b3c-d6f6-45fb-80f9-2d6c869047e8@video:timestamp:0.00-3.00
- c8c1550b-1e65-49cb-9e74-69de2f0c2599@video:timestamp:3.00-6.00
- 29b5eb21-8068-4fa4-8397-3e11774c0a50@video:timestamp:6.00-9.00
- 63ab1b55-b93c-4b95-8033-bac8d91f7f8e@frame:0001@1.00s:ocr
- d162428f-8e60-4f0e-9603-5657ce831647@frame:0001@1.00s:scene
- 8837ace6-895b-4069-ac68-044ccf52668f@frame:0002@2.00s:ocr
- fb1ae567-75f2-4cb7-b553-b50806c47715@frame:0002@2.00s:scene

## 标签
- incident_response
- video
- build_skill
- heuristic
