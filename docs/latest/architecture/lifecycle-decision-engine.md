# Lifecycle Decision Engine Baseline

> Date: 2026-04-25  
> Task Card: `LC-R-35`  
> Scope: lifecycle decision for `new/revise/merge/supersede/reject`

## Verdict

`LifecycleDecisionEngine` 已落地在 `src/omni_skill_pipeline/assembly/lifecycle.py`。  
引擎消费 similarity 检索结果与质量分，输出结构化 `LifecycleDecision`，避免“相近 skill 一律新建”。

## Runtime Contract

输入：

- `similarity_results`: 来自 retrieval 层的候选列表（按 `skill_id + score`）
- `quality_scores`（可选）:
  - `overall_score`
  - `noise_score`
  - `consistency_score`
  - `novelty_score`
- `evidence_conflict`（可选）: 明确证据冲突信号

输出：

- `LifecycleDecisionType.NEW`
- `LifecycleDecisionType.REVISE`
- `LifecycleDecisionType.MERGE`
- `LifecycleDecisionType.SUPERSEDE`
- `LifecycleDecisionType.REJECT`

## Default Policy

`LifecyclePolicyThresholds` 默认阈值：

- `revise_min_similarity = 0.78`
- `merge_min_similarity = 0.90`
- `supersede_min_similarity = 0.95`
- `supersede_min_overall = 0.80`
- `supersede_min_novelty = 0.65`
- `reject_max_overall = 0.40`
- `reject_min_noise = 0.90`
- `reject_max_consistency = 0.35`

优先级顺序：

1. `reject`（冲突/噪声/一致性/总体质量）
2. `supersede`（极高相似 + 质量达标 + 新颖度达标）
3. `merge`（多候选高相似）
4. `revise`（单候选高相似）
5. `new`（其余）

## Metadata

输出 metadata 包含：

- 阈值快照（`thresholds`）
- 质量分输入（`quality_scores`）
- Top 候选摘要（`top_candidates`）

该结构用于后续审计与策略调优。

## Verification

测试文件：

- `tests/test_lifecycle_decision_engine.py`

覆盖点：

- 无候选 -> `new`
- 单高相似 -> `revise`
- 多高相似 -> `merge`
- 近同构高质量 -> `supersede`
- 高噪声/冲突 -> `reject`
- 阈值覆写生效
