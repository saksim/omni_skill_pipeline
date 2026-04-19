# audio transcript

## 判词
Rebuild the incident timeline before proposing a root cause.

## 元信息
- skill_id: 7db18457-cdf0-4e07-b654-ed607a1ea8a9
- version: 0.1.0
- skill_type: decision
- audience: self
- source_modality: audio
- review_status: draft
- confidence: 0.90
- created_at: 2026-04-19T13:02:09Z

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
- db3d0845-fb82-4366-aa5f-8cbef1492eb1@timestamp:00:00:01,000-00:00:05,000
- 3e1f418d-cc46-417a-852b-f64fb3425c9c@timestamp:00:00:06,000-00:00:11,000
- 1d7d64dc-59cc-4c95-8096-42e26f264a80@timestamp:00:00:12,000-00:00:16,000
- 55008c57-6f93-4195-ade7-5d9684a5800b@timestamp:00:00:17,000-00:00:22,000

## 标签
- ops
- audio
- build_skill
