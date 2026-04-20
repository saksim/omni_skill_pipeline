# Incident Walkthrough

## 判词
1. Rebuild the incident timeline.

## 元信息
- skill_id: c3366744-3bf7-41e3-bba4-8b014bbda724
- version: 0.1.0
- skill_type: decision
- audience: self
- source_modality: video
- review_status: draft
- confidence: 0.85
- created_at: 2026-04-20T12:08:19Z

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
- d2ecc6b2-04e4-4498-aa91-a1f8d6831aef@video:timestamp:0.00-3.00
- f92b4e28-cc56-4c99-9e5b-bd67b5052d55@video:timestamp:3.00-6.00
- 44d38d04-bde5-4347-8b6b-819221762d12@video:timestamp:6.00-9.00
- 3d5c268b-6af3-48b4-94cd-126cd55f4fe3@frame:0001@1.00s:ocr
- 0d3e868d-d7f3-4ea6-b3b8-b3b3cb1c025d@frame:0001@1.00s:scene
- 76fa8244-0bad-487b-a196-158fac4e7676@frame:0002@2.00s:ocr
- ea158b44-21de-4351-8473-d4d4859dfef6@frame:0002@2.00s:scene

## 标签
- incident_response
- video
- build_skill
- heuristic
