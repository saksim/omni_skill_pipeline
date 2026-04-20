# Incident Walkthrough

## 判词
1. Rebuild the incident timeline.

## 元信息
- skill_id: e204f9ce-d7e7-4577-9fb4-6712a9543957
- version: 0.1.0
- skill_type: decision
- audience: self
- source_modality: video
- review_status: draft
- confidence: 0.85
- created_at: 2026-04-20T15:00:05Z

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
- 16fc7fa8-f934-4fe5-89fb-cd6359b1a73e@video:timestamp:0.00-3.00
- 997269a2-84c3-4ba0-b05a-60ffa818f45b@video:timestamp:3.00-6.00
- 4ce96bc6-46c7-4eaf-a546-1c87151cc3e3@video:timestamp:6.00-9.00
- 789e568a-2e9f-49ae-87ca-078621d666f9@frame:0001@1.00s:ocr
- bc4cc11c-ff6d-440d-86f2-bf7ced91b4cf@frame:0001@1.00s:scene
- e5aa5885-3725-47b7-9df4-0afedbb49f24@frame:0002@2.00s:ocr
- 6630bf98-4375-4e5d-8890-cacd39229c58@frame:0002@2.00s:scene

## 标签
- incident_response
- video
- build_skill
- heuristic
