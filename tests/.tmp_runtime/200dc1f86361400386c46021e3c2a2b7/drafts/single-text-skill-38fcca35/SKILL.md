# single text skill

## 判词
Incident Runbook

## 元信息
- skill_id: 38fcca35-2968-4298-bfbd-f9873f8997ec
- version: 0.1.0
- skill_type: procedure
- audience: self
- source_modality: text
- review_status: draft
- confidence: 0.63
- created_at: 2026-04-20T16:21:46Z

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
- be88c33e-69d3-4b25-a1a6-393c1eca8480@section:1
- 0aed693e-f5c2-4e95-a97f-ac1e603f85cd@section:1:paragraph:0001

## 标签
- incident_response
- text
- build_skill
- heuristic
