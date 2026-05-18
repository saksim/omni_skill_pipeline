# Evaluation Rubric

## 判词

E0 评估口径必须同时兼容自动比较与人工评审。否则后续 V2 改造只会陷入“感觉更好”，而不是“证据更强”。

## 1. 自动指标

### `traceability_rate`

定义：

```text
可追溯 step 数 / 全部 step 数
```

判定标准：

- step 至少能回指 1 个 atom
- atom 至少能回指 1 个 evidence node

### `evidence_coverage_rate`

定义：

```text
被 step / decision / verification 引用的关键 evidence 数 / 关键 evidence 总数
```

说明：

- 关键 evidence 由规则或人工标注决定
- 低噪声、强结论 evidence 应优先被覆盖

### `duplicate_skill_rate`

定义：

```text
被判定为重复技能的输出数 / 总输出数
```

目标：

- V2 上线后应持续下降

### `false_procedure_rate`

定义：

```text
本应是 analysis / guardrail / decision 输出，却被误组装成 procedure 的样本数 / 总样本数
```

当前重点关注：

- tabular/time-series
- image
- video

## 2. 半自动指标

### `noise_penalty`

0 到 5 分，越高越差：

- `0`: 无明显噪声
- `1`: 轻微错字，不影响理解
- `2`: 有局部脏 OCR / ASR，但可恢复
- `3`: 关键 step 已被噪声污染
- `4`: 主要输出不可直接使用
- `5`: 输出基本失真或误导

### `consistency_score`

0 到 5 分，越高越好：

- `0`: 自相矛盾
- `1`: 多处冲突
- `2`: 有明显不一致
- `3`: 基本一致，但仍有边界冲突
- `4`: 高度一致
- `5`: 结构与语义都一致

## 3. 人工评审指标

### `actionability_score`

0 到 5 分，越高越好：

- `0`: 完全不可执行
- `1`: 大部分是泛泛描述
- `2`: 少量动作可执行，但缺关键条件
- `3`: 基本可执行，但仍需资深工程师大量补全
- `4`: 可直接执行，仅需少量环境化调整
- `5`: 可直接复用，步骤、条件、验证都明确

### `reviewer_edit_distance`

建议计算方式：

- 统计 reviewer 在最终可接受版本中修改的 step 数
- 统计 reviewer 新增/删除的 decision / verification 项数
- 统计 reviewer 重写 summary 的比例

简化记录格式：

```text
step_edits=<n>, rule_edits=<n>, verification_edits=<n>, summary_rewritten=<true|false>
```

### `publication_fitness`

判断当前 publication 形态是否正确：

- `fit`: 输出类型正确
- `partial_fit`: 核心形态对，但混入杂质
- `misfit`: 输出类型错了

示例：

- 时序样本被生成为 `analysis`，可判 `fit`
- 时序样本被生成为 `procedure`，判 `misfit`

## 4. 基线评审模板

每次回归时，建议按如下模板记录：

```text
sample_id:
baseline_draft:
candidate_draft:
traceability_rate:
evidence_coverage_rate:
noise_penalty:
consistency_score:
actionability_score:
reviewer_edit_distance:
publication_fitness:
notes:
```

## 5. 阶段目标

### Phase 1-3

- 不要求 image/video 立即变好
- 重点观察 `traceability_rate` 与 `publication_fitness`

### Phase 4-7

- 要求 `noise_penalty` 下降
- 要求 `reviewer_edit_distance` 下降
- 要求 `false_procedure_rate` 明显下降

## 6. 当前基线结论

按 2026-04-20 的 E0 基线：

- `text`: `actionability_score` 高，`noise_penalty` 低
- `audio`: `actionability_score` 中高，`traceability_rate` 较好
- `tabular/time-series`: `evidence_coverage_rate` 高，但 `publication_fitness` 仅 `partial_fit`
- `image`: `noise_penalty` 高，`publication_fitness` 为 `misfit`
- `video`: `noise_penalty` 高，`publication_fitness` 为 `misfit`
