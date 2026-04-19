# audio transcript

## 判词
Rebuild the incident timeline before proposing a root cause.

## 元信息
- skill_id: afebf136-2840-43ae-a2f2-25b6b3d28508
- version: 0.1.0
- skill_type: procedure
- audience: self
- source_modality: audio
- review_status: draft
- confidence: 0.86
- created_at: 2026-04-19T13:54:34Z

## 目标
Distill ops material into a build_skill for self. Seed: Rebuild the incident timeline before proposing a root cause.

## 触发条件
- Use when you need to convert audio evidence into a reusable build_skill.

## 输入
- Audio source or transcript
- Distillation goal

## 前置条件
- Rebuild the incident timeline before proposing a root cause.

## 操作步骤
1. Rebuild the incident timeline before proposing a root cause.
Reason: Derived from normalized evidence and intended to preserve the original reasoning chain.
2. If multiple alerts point to the same dependency, merge them into one incident stream.
Reason: Derived from normalized evidence and intended to preserve the original reasoning chain.
3. Avoid changing configuration, code, and infrastructure in one mitigation step.
Reason: Derived from normalized evidence and intended to preserve the original reasoning chain.

## 决策规则
- If multiple alerts point to the same dependency, merge them into one incident stream.

## 反模式
- Avoid changing configuration, code, and infrastructure in one mitigation step.

## 验证方式
- Verify recovery with latency, saturation, and error rate instead of a single metric.

## 证据链
- 711d0dbe-9c41-4e95-9442-f4bc0a57c09c@timestamp:1.00-5.00
- ffbe737d-2ea7-4804-be4f-98b27d870223@timestamp:6.00-11.00
- dde0da3a-1a5c-4db0-a8f0-4adb20482b6a@timestamp:12.00-16.00
- 0a55a2d8-2fb1-4c96-b7d1-420455057cc3@timestamp:17.00-22.00

## 标签
- ops
- audio
- build_skill
- heuristic
