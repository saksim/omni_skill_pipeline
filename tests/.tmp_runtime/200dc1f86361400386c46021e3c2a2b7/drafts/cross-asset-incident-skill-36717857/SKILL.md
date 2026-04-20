# cross asset incident skill

## 判词
Incident Runbook

## 元信息
- skill_id: 36717857-70ed-4e87-a805-1f68355a462e
- version: 0.1.0
- skill_type: procedure
- audience: self
- source_modality: text
- review_status: draft
- confidence: 0.79
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
- a3c985ae-941f-49a0-a7b4-e831f8dcc74a@section:1
- bfa1e8c0-f691-45bf-82b2-efbb35a96e1c@section:1:paragraph:0001
- 669f87d3-4e77-4733-ab23-bac53daec437@timestamp:segment:0001
- 584e8500-0ea9-453d-927b-535a8f46cc1a@timestamp:segment:0002
- c25de681-ded9-4f88-b481-ffb34c7576dc@timestamp:segment:0003
- bf2f14cc-c106-4cc9-99d6-6484a2730b83@timestamp:segment:0004

## 标签
- incident_response
- text
- build_skill
- heuristic
