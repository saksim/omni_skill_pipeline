# Incident Debrief

## 判词
1. Rebuild the incident timeline.

## 元信息
- skill_id: 075cb6c6-2e57-4a92-b156-2e230df237be
- version: 0.1.0
- skill_type: decision
- audience: self
- source_modality: audio
- review_status: draft
- confidence: 0.72
- created_at: 2026-04-19T13:53:33Z

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
- 58dffd51-0675-45a2-9de9-8a51450361dc@timestamp:0.00-3.00
- 0e6aea9e-1a75-4de7-9f13-51f3aea21d00@timestamp:3.00-6.00
- 233ecbc2-fdb4-48d8-9e0a-9aa18c5d6420@timestamp:6.00-9.00

## 标签
- ops
- audio
- build_skill
- heuristic
