# Retrieval Backend Decision Baseline

> Date: 2026-04-25  
> Task Card: `LC-R-34`  
> Scope: establish retrieval abstraction and backend selection baseline for similarity search

## Verdict

当前检索层先以 `inmemory` backend 作为默认 runtime baseline，接口已经统一到
`src/omni_skill_pipeline/retrieval/similarity.py`。`pgvector` 与 `qdrant` 先挂在同一接口下的 placeholder，
后续按数据规模与运维约束切换，不破坏调用方协议。

## Unified Interface

核心接口：

- `SimilarityBackend`
- `SimilarityRetriever`
- `SkillSearchDocument`
- `SimilarityQuery`
- `SimilarityResult`
- `build_similarity_backend()`

当前行为：

- `inmemory`: 可直接索引 + 检索（词面相似 + domain/tag boost）
- `pgvector`: placeholder，抛出 `BackendNotReadyError`
- `qdrant`: placeholder，抛出 `BackendNotReadyError`

## Backend Choice Matrix

| Option | Strength | Weakness | Recommended Use |
| --- | --- | --- | --- |
| `inmemory` | 零外部依赖、最快落地、单测稳定 | 不支持大规模向量检索、无持久化 | 当前开发与 smoke 基线 |
| `pgvector` | 复用 PostgreSQL 运维面、事务一致性好 | 索引/召回参数调优复杂、写入放大 | 已有 PG 且希望少系统依赖 |
| `qdrant` | 向量检索能力强、ANN 参数灵活 | 引入新基础设施、运维面扩大 | 检索吞吐/召回优先场景 |

## Switching Criteria

从 `inmemory` 切到向量 backend 的触发条件（满足任一）：

- skill corpus 超过 `10k` 且检索延迟/召回开始退化
- 需要跨 corpus 的近似语义召回与去重
- lifecycle decision (`revise/merge/supersede`) 对相似检索准确率有明确 SLO

## Next Cut

- `LC-R-35` 已于 2026-04-25 完成：lifecycle decision engine 可直接消费 `SimilarityRetriever` 输出
- `TP-E8-04`: 落地 pgvector 索引与向量写入路径
- `LC-R-34` 后续补丁：接入真实 embedding 生成链路（当前仅 baseline lexical scoring）
