# Incident Walkthrough

## 判词
1. Rebuild the incident timeline.

## 元信息
- skill_id: 7f3e4018-7570-4d7f-9cb3-19be69c6159d
- version: 0.1.0
- skill_type: decision
- audience: self
- source_modality: video
- review_status: draft
- confidence: 0.85
- created_at: 2026-04-19T13:54:07Z

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
- 1aac8ad0-5af8-4afc-b856-cdb656129cdd@video:timestamp:0.00-3.00
- e331aaaa-6ab6-4d9b-a92d-1af19c2b93d5@video:timestamp:3.00-6.00
- 26f76d6d-4e00-4ae3-ba00-5361037b2e40@video:timestamp:6.00-9.00
- 88ec3372-e648-42ca-8737-1fb5708f9a64@frame:0001:ocr
- a6f72173-d138-441d-8854-c8133aa24bd7@frame:0001:scene
- 31d7fed1-b328-4c38-aa66-cec6af81f8aa@frame:0002:ocr
- f17548d0-a433-4b56-ba67-e70e04963c0e@frame:0002:scene

## 标签
- incident_response
- video
- build_skill
- heuristic
