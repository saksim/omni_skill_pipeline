# cross asset incident skill

## 判词
Incident Runbook

## 元信息
- skill_id: ad9fcc5d-d1cc-4c10-88c8-482033d03ab9
- version: 0.1.0
- skill_type: procedure
- audience: self
- source_modality: text
- review_status: draft
- confidence: 0.79
- created_at: 2026-04-20T15:45:17Z

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
- 2d4555fe-b997-487c-9558-8ddd8b2c3bba@section:1
- 797e6628-a25e-42f6-948e-fd7ff9e998cd@section:1:paragraph:0001
- bfc6eeb8-92ba-4c05-86a9-352eb450e99f@timestamp:segment:0001
- 84e705d2-2404-4443-86fa-cf2df0d911e3@timestamp:segment:0002
- 7fe4d07f-36ab-4649-a8ca-b39a5a86c071@timestamp:segment:0003
- 6d6c2036-41d2-4c8f-9084-c67b67667721@timestamp:segment:0004

## 标签
- incident_response
- text
- build_skill
- heuristic
