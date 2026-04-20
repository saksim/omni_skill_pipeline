# cross asset incident skill

## 判词
# Incident Runbook 1. Rebuild the timeline. 2. Merge duplicate alerts. Verify recovery with latency and error rate.

## 元信息
- skill_id: 8105cac0-6cf9-4ab0-a69c-ed3a4f26e4b1
- version: 0.1.0
- skill_type: procedure
- audience: self
- source_modality: text
- review_status: draft
- confidence: 0.75
- created_at: 2026-04-20T14:58:37Z

## 目标
Distill incident_response material into a build_skill for self. Seed: # Incident Runbook 1. Rebuild the timeline. 2. Merge duplicate alerts. Verify recovery with latency and error rate.

## 触发条件
- Use when you need to convert text evidence into a reusable build_skill.

## 输入
- Source document
- Distillation goal

## 前置条件
- Confirm the source material matches the declared distillation goal.

## 操作步骤
1. Rebuild the timeline.
Reason: Derived from normalized evidence and intended to preserve the original reasoning chain.
2. Merge duplicate alerts.
Reason: Derived from normalized evidence and intended to preserve the original reasoning chain.

## 决策规则
- None

## 反模式
- None

## 验证方式
- Verify recovery with latency and error rate.

## 证据链
- 898e1452-3a83-4678-9d39-cdc415128887@paragraph:0001
- 6c03cb60-77b0-4bda-be1e-54b667d08b3c@timestamp:segment:0001
- ef90e094-8f0f-4711-b4fa-9375799b9dab@timestamp:segment:0002
- f74a1d44-0d2a-4f68-872d-30013fe0f6e1@timestamp:segment:0003
- 5e3a2394-4440-49ee-b506-05976b89ebf8@timestamp:segment:0004

## 标签
- incident_response
- text
- build_skill
- heuristic
