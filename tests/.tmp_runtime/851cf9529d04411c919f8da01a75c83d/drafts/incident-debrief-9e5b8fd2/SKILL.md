# Incident Debrief

## 判词
1. Rebuild the incident timeline.

## 元信息
- skill_id: 9e5b8fd2-a854-4271-b974-628eacd17d60
- version: 0.1.0
- skill_type: decision
- audience: self
- source_modality: audio
- review_status: draft
- confidence: 0.72
- created_at: 2026-04-20T16:21:33Z

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
- b499bec9-6d8b-4ab8-8749-ef9d8e78bd03@timestamp:0.00-3.00
- 5539fa43-b1db-4cab-a850-d3acf0f7f82f@timestamp:3.00-6.00
- 39e246b4-2ec6-4ee7-b4c9-7f59fe8cea3f@timestamp:6.00-9.00

## 标签
- ops
- audio
- build_skill
- heuristic
