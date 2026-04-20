# Incident Walkthrough

## 判词
1. Rebuild the incident timeline.

## 元信息
- skill_id: b059b281-bf28-4e29-baf2-e510f064219c
- version: 0.1.0
- skill_type: decision
- audience: self
- source_modality: video
- review_status: draft
- confidence: 0.85
- created_at: 2026-04-20T15:53:13Z

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
- 72bb8e74-a72d-43f1-8d26-b6fb50a23696@video:timestamp:0.00-3.00
- 67395052-5d5b-4a0b-b80a-c9515374bcce@video:timestamp:3.00-6.00
- 1cd8d153-e11d-4c30-95e2-f55cc27ec113@video:timestamp:6.00-9.00
- 402c4385-ebce-4fbb-b599-c7ad9f20f269@frame:0001@1.00s:ocr
- e196f7bc-7464-4218-b16e-f96a88959760@frame:0001@1.00s:scene
- db547def-9f45-4fb5-a036-2a9b00aa2267@frame:0002@2.00s:ocr
- fd735cec-2678-45ac-9c07-04e738965641@frame:0002@2.00s:scene

## 标签
- incident_response
- video
- build_skill
- heuristic
