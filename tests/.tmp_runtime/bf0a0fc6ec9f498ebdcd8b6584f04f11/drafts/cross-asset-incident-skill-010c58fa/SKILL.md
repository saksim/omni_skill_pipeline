# cross asset incident skill

## 判词
# Incident Runbook 1. Rebuild the timeline. 2. Merge duplicate alerts. Verify recovery with latency and error rate.

## 元信息
- skill_id: 010c58fa-e7d9-4eb2-bb8d-4c7c7191cf8b
- version: 0.1.0
- skill_type: procedure
- audience: self
- source_modality: text
- review_status: draft
- confidence: 0.75
- created_at: 2026-04-20T14:13:01Z

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
- 92370345-7c72-4417-aeb1-2d878c52077d@paragraph:0001
- 1f566a8d-d24b-4894-98cc-69cbfee0cd13@timestamp:segment:0001
- 89d87216-c49e-4e57-bd3b-3f58c5a72f1b@timestamp:segment:0002
- 61cd7687-40b0-48b9-91fd-91f06eed7f64@timestamp:segment:0003
- 95bf9ea3-c874-4121-8b09-1de6bcb68227@timestamp:segment:0004

## 标签
- incident_response
- text
- build_skill
- heuristic
