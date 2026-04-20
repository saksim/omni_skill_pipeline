# audio transcript

## 判词
Rebuild the incident timeline before proposing a root cause.

## 元信息
- skill_id: 1267b0fb-4199-4448-b095-720e5a227178
- version: 0.1.0
- skill_type: procedure
- audience: self
- source_modality: audio
- review_status: draft
- confidence: 0.86
- created_at: 2026-04-20T12:06:08Z

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
- f30051c4-4326-4d5a-9fee-06ea6638accb@timestamp:1.00-5.00
- 0f7e3c32-371f-440e-b494-89cc8049aec2@timestamp:6.00-11.00
- b26b18e9-e517-4e39-83c4-2f217da7c197@timestamp:12.00-16.00
- 6328fb47-0c18-4932-81a9-bd5314b8a4e5@timestamp:17.00-22.00

## 标签
- ops
- audio
- build_skill
- heuristic
