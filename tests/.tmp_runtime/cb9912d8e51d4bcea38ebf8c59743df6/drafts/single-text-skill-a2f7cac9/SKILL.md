# single text skill

## 判词
Incident Runbook

## 元信息
- skill_id: a2f7cac9-1211-4856-913e-62107d9d910f
- version: 0.1.0
- skill_type: procedure
- audience: self
- source_modality: text
- review_status: draft
- confidence: 0.63
- created_at: 2026-04-20T15:54:52Z

## 目标
Distill incident_response material into a build_skill for self. Seed: Incident Runbook

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
- a00455fd-54b0-4fec-80eb-26253717f61b@section:1
- ecbbb0d9-ae65-40f2-851d-473e1c07d4b2@section:1:paragraph:0001

## 标签
- incident_response
- text
- build_skill
- heuristic
