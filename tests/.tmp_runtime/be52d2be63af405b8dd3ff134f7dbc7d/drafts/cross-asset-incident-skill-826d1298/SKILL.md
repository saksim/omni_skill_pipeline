# cross asset incident skill

## 判词
# Incident Runbook 1. Rebuild the timeline. 2. Merge duplicate alerts. Verify recovery with latency and error rate.

## 元信息
- skill_id: 826d1298-49b8-4189-b70f-1fbf6a0b0e40
- version: 0.1.0
- skill_type: procedure
- audience: self
- source_modality: text
- review_status: draft
- confidence: 0.75
- created_at: 2026-04-20T15:00:04Z

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
- 74205e37-9955-4b8b-b146-886aea6b8595@paragraph:0001
- 067a99c0-479b-4056-b70a-a44e9ae89b4f@timestamp:segment:0001
- 5b17b954-a3b3-4b1d-bf3f-3619258dd8eb@timestamp:segment:0002
- 4071fe1e-4870-4c8c-8d1f-7fa2d45e8b60@timestamp:segment:0003
- f0a0c44b-8809-495b-a948-cc067771df91@timestamp:segment:0004

## 标签
- incident_response
- text
- build_skill
- heuristic
