# audio transcript

## 判词
Rebuild the incident timeline before proposing a root cause.

## 元信息
- skill_id: 54f80baa-b8fb-4d2f-b2da-8a317dc5f9cb
- version: 0.1.0
- skill_type: procedure
- audience: self
- source_modality: audio
- review_status: draft
- confidence: 0.86
- created_at: 2026-04-19T13:52:07Z

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
- b8b17793-7216-4a53-a56f-a9f76d49a397@timestamp:1.00-5.00
- 7ed062ff-cf8a-40b5-8d8e-b4399146a2fb@timestamp:6.00-11.00
- 17fc270e-f331-4761-8dad-72b891d18af4@timestamp:12.00-16.00
- 795b0e75-5528-4e31-a366-319a4c13980c@timestamp:17.00-22.00

## 标签
- ops
- audio
- build_skill
- heuristic
