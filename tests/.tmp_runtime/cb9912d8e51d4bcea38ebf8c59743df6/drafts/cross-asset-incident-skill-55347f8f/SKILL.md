# cross asset incident skill

## 判词
Incident Runbook

## 元信息
- skill_id: 55347f8f-7d76-4f40-ad75-d1e1a031f300
- version: 0.1.0
- skill_type: procedure
- audience: self
- source_modality: text
- review_status: draft
- confidence: 0.79
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
- a9c48491-54ca-460b-95b8-ee64c21ce461@section:1
- f4450c9e-373b-4535-8e5b-590ff05400f9@section:1:paragraph:0001
- 29280eed-e913-4ce1-82a4-ec3a9246f848@timestamp:segment:0001
- fd64c421-29e6-49c7-a25c-f92181b15ab9@timestamp:segment:0002
- f0a9fb59-0bf1-4b9a-ab95-77da5225f647@timestamp:segment:0003
- 8492d97c-55b7-456d-93be-40db1c1f1bb9@timestamp:segment:0004

## 标签
- incident_response
- text
- build_skill
- heuristic
