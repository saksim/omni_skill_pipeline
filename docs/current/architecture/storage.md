# Storage

## Core Data Objects

### Asset

- `asset_id`
- `modality`
- `source_uri`
- `metadata`

### EvidenceUnit

- `evidence_id`
- `asset_id`
- `span_ref`
- `content_type`
- `content`
- `speaker`
- `confidence`
- `tags`

### Insight

- `insight_id`
- `insight_type`
- `summary`
- `evidence_refs`
- `confidence`

### SkillDocument

- `skill_id`
- `name`
- `skill_type`
- `goal`
- `audience`
- `trigger`
- `inputs`
- `preconditions`
- `steps`
- `decision_rules`
- `anti_patterns`
- `verification`
- `evidence_refs`
- `confidence`
- `version`
- `summary`
- `tags`
- `source_modality`
- `review_status`
- `created_at`

## Relational Schema

DDL 已固化在 [001_init.sql](D:\download\gaming\new_program\data_helper\3_omni_skill_pipeline\infra\sql\001_init.sql)。

核心表：

- `ingest_jobs`
- `assets`
- `evidence_units`
- `insights`
- `skills`
- `skill_versions`
- `publications`
- `review_tasks`

## File Artifact Store

```text
skills/
  drafts/
    {slug}-{skill_id}/
      asset.json
      evidence.json
      insights.json
      skill.json
      SKILL.md
      bundle.json
  review_queue/
    pending/
      {review_task_id}.json
    consumed/
      {review_task_id}.json
```

## Storage Rules

- 当前主仓储是本地文件系统
- Repository 只负责工件落盘，不负责蒸馏推理
- `PostgresRepository` 位于 `src/omni_skill_pipeline/persistence/postgres_repository.py`，当前聚焦 skills/review/publications 的最小落库合同
- `DualWriteArtifactRepository` 位于 `src/omni_skill_pipeline/persistence/dual_write_repository.py`，用于 file + postgres 镜像写入与失败隔离
- Retrieval 抽象位于 `src/omni_skill_pipeline/retrieval/similarity.py`，当前默认 `inmemory`，并预留 `pgvector/qdrant` 占位 backend
- Review queue 最小合同支持 `pending` 查询与 `consume` 消费
- `docs/current/contracts/` 是 schema 与模板真相源
- Video 临时工坊位于 `.tmp_omni_media/`

## Future Direction

- PostgreSQL Repository 替换 File Repository
- Qdrant 混合检索
- Review Queue 真正落库
- 更细粒度的 evidence-to-step 引用关系
