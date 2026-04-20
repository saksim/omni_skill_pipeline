# cross asset incident skill

## 判词
# Incident Runbook 1. Rebuild the timeline. 2. Merge duplicate alerts. Verify recovery with latency and error rate.

## 元信息
- skill_id: 26b3558c-4457-434c-b12a-e272aca3914d
- version: 0.1.0
- skill_type: procedure
- audience: self
- source_modality: text
- review_status: draft
- confidence: 0.75
- created_at: 2026-04-20T15:23:46Z

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
- 3b4a0b96-db72-448d-949e-cb558448e4ff@paragraph:0001
- 24d109a9-a769-4fe7-9f4c-9d44eb16f581@timestamp:segment:0001
- 32dd9e14-89f8-4794-8b72-07f53e8e409c@timestamp:segment:0002
- 5e65f859-584d-4319-8012-0b7889a78dba@timestamp:segment:0003
- 5261ec3c-e0cb-41ea-8918-f854975ce6fe@timestamp:segment:0004

## 标签
- incident_response
- text
- build_skill
- heuristic
