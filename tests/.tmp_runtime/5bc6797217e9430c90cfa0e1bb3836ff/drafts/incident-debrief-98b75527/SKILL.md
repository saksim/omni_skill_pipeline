# Incident Debrief

## 判词
1. Rebuild the incident timeline.

## 元信息
- skill_id: 98b75527-4317-44d0-aa00-43df811ce672
- version: 0.1.0
- skill_type: decision
- audience: self
- source_modality: audio
- review_status: draft
- confidence: 0.72
- created_at: 2026-04-20T12:31:18Z

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
- c860bbaf-556b-460b-9368-51914e9fb228@timestamp:0.00-3.00
- 9f31c898-fff0-460e-b6f9-a85d516a5aee@timestamp:3.00-6.00
- a2ffb79a-90e5-430d-9ac2-416f2d64b36a@timestamp:6.00-9.00

## 标签
- ops
- audio
- build_skill
- heuristic
