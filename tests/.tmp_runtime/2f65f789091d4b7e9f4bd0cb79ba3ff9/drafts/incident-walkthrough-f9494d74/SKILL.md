# Incident Walkthrough

## 判词
1. Rebuild the incident timeline.

## 元信息
- skill_id: f9494d74-7c0b-4ec2-9c90-2adc13d103b9
- version: 0.1.0
- skill_type: decision
- audience: self
- source_modality: video
- review_status: draft
- confidence: 0.85
- created_at: 2026-04-20T13:01:53Z

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
- 8cc06123-5904-4152-b712-7e98e1653dcd@video:timestamp:0.00-3.00
- c8545170-fd8c-4728-883b-b917e2f6f40a@video:timestamp:3.00-6.00
- 1a5892fa-46db-4ce2-9e38-40e5ada4c87a@video:timestamp:6.00-9.00
- d48adc95-3be6-41a1-81c7-677c0e2678f7@frame:0001@1.00s:ocr
- 9e3db9e8-bb16-4dca-87e7-24216d27a35b@frame:0001@1.00s:scene
- 06ad4ca7-9bdb-4ac6-85c7-569e2f9ab5e5@frame:0002@2.00s:ocr
- 4eabb635-3af1-48d6-a4b8-63447732c4e1@frame:0002@2.00s:scene

## 标签
- incident_response
- video
- build_skill
- heuristic
