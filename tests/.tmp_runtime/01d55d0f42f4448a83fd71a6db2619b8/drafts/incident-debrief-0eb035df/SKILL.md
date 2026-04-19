# Incident Debrief

## 判词
1. Rebuild the incident timeline.

## 元信息
- skill_id: 0eb035df-69cb-41e7-964c-f3d77bdd04e8
- version: 0.1.0
- skill_type: decision
- audience: self
- source_modality: audio
- review_status: draft
- confidence: 0.72
- created_at: 2026-04-19T14:17:22Z

## 目标
Distill ops material into a build_skill for self. Seed: 1. Rebuild the incident timeline.

## 触发条件
- Use when you need to convert audio evidence into a reusable build_skill.

## 输入
- Audio source or transcript
- Distillation goal

## 前置条件
- Confirm the source material matches the declared distillation goal.

## 操作步骤
1. Rebuild the incident timeline.
Reason: Derived from normalized evidence and intended to preserve the original reasoning chain.

## 决策规则
- If alerts duplicate, merge them into one incident stream.

## 反模式
- None

## 验证方式
- Verify recovery with error rate and latency.

## 证据链
- b06884a2-8be1-40c2-b662-df846d5c9081@timestamp:0.00-3.00
- 5a011704-f839-45ec-9121-8962f7d3d4ad@timestamp:3.00-6.00
- 35fff96a-5f64-41cf-8108-55819e2c03b1@timestamp:6.00-9.00

## 标签
- ops
- audio
- build_skill
- heuristic
