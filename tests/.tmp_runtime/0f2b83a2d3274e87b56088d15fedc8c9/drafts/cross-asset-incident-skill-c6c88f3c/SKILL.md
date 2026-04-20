# cross asset incident skill

## 判词
# Incident Runbook 1. Rebuild the timeline. 2. Merge duplicate alerts. Verify recovery with latency and error rate.

## 元信息
- skill_id: c6c88f3c-4cae-4d2a-b2eb-1f8025d514ad
- version: 0.1.0
- skill_type: procedure
- audience: self
- source_modality: text
- review_status: draft
- confidence: 0.75
- created_at: 2026-04-20T14:15:04Z

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
- 88e9e048-ba57-4029-96d9-3c6169838bc9@paragraph:0001
- 5b0b8f6e-2aba-41cd-8102-5d786422b1e7@timestamp:segment:0001
- 882bafe1-c4b9-4eb8-b1b0-b1da5bd2a8a2@timestamp:segment:0002
- 1564cda0-bc02-434a-8ac1-aba7c5c62a35@timestamp:segment:0003
- 51039baa-9bf1-4720-8995-52101d361dfb@timestamp:segment:0004

## 标签
- incident_response
- text
- build_skill
- heuristic
