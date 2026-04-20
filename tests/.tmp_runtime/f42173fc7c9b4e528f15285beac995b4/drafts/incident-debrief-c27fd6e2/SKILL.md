# Incident Debrief

## 判词
1. Rebuild the incident timeline.

## 元信息
- skill_id: c27fd6e2-6f58-45b4-a3f6-608f09f499a3
- version: 0.1.0
- skill_type: decision
- audience: self
- source_modality: audio
- review_status: draft
- confidence: 0.72
- created_at: 2026-04-20T14:15:04Z

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
- 8ef994f9-14aa-40ab-a73d-195c0d30f704@timestamp:0.00-3.00
- 7112ebd8-fdf4-4a21-a258-80c9d0705dcf@timestamp:3.00-6.00
- 108dd866-7349-4a9a-9e9d-a73f3ab22309@timestamp:6.00-9.00

## 标签
- ops
- audio
- build_skill
- heuristic
