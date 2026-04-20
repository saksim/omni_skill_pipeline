# Incident Debrief

## 判词
1. Rebuild the incident timeline.

## 元信息
- skill_id: e07c8e02-b620-4995-82bc-627cbed726d9
- version: 0.1.0
- skill_type: decision
- audience: self
- source_modality: audio
- review_status: draft
- confidence: 0.72
- created_at: 2026-04-20T12:08:19Z

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
- 1186a736-b152-4918-943e-ea20a21240b2@timestamp:0.00-3.00
- 117956ba-6bfe-45fe-a4c8-bfb245273bac@timestamp:3.00-6.00
- 4d48c0c2-1e48-4c16-b5e2-5548ecfb7d45@timestamp:6.00-9.00

## 标签
- ops
- audio
- build_skill
- heuristic
