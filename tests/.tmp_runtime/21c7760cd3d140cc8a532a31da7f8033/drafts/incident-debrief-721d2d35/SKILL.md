# Incident Debrief

## 判词
1. Rebuild the incident timeline.

## 元信息
- skill_id: 721d2d35-8781-487a-a27a-2424a2e3742d
- version: 0.1.0
- skill_type: decision
- audience: self
- source_modality: audio
- review_status: draft
- confidence: 0.72
- created_at: 2026-04-20T13:20:00Z

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
- 4c3cb3bf-4795-4084-94de-661491600cea@timestamp:0.00-3.00
- ca81d71f-2992-4524-9ba6-135aa0f4ac46@timestamp:3.00-6.00
- 1d4fc782-6b8b-4af8-acee-8eaf920110a0@timestamp:6.00-9.00

## 标签
- ops
- audio
- build_skill
- heuristic
