# Current Status

## 判词

项目已从“路线图与骨架阶段”推进到“可扩展的多模态蒸馏内核”，但在对外暴露前仍卡在 API 加固、可观测性、repository abstraction 这三道关口。

## 当前已落地

### 文档与入口

- 根入口已收束到 `README.md`
- 当前文档按 `architecture / contracts / status / operations` 分域整理
- API、CLI、Environment、Testing 已各自拆出独立运行文档

### Python 工程骨架

- 主包：`src/omni_skill_pipeline/`
- API 入口：`apps/api/main.py`
- Worker 入口：`apps/worker/main.py`
- 协议层：`interfaces.py`
- 核心模块：`service.py`、`repository.py`、`render.py`、`schema.py`

### 多模态主链

- Text：统一进入 `EvidenceUnit`
- Audio：支持 transcript、transcript sidecar、OpenAI ASR
- Image：支持 OCR 与 scene summary
- Video：支持 audio 抽取、keyframe、OCR、scene summary、时间语义增强
- Tabular / Time-series：支持 `TABLE / METRIC / EVENT` evidence

### V2 语义层

- 已落地 `Corpus`、`EvidenceNode`、`SemanticAtom`、`SkillGraph`
- 已落地 `SkillGraph -> SkillDocument -> SKILL.md` 兼容路径
- 已落地 `Publication`、quality scoring、review policy、review task、review feedback 持久化
- 已落地 `load_corpus()` 与 `distill_corpus()`

### 测试与 CI

- CI 统一走 `python scripts/ci.py`
- `test_mvp.py` 已覆盖 text / audio / image / video / tabular 主链
- `test_v2_schema_and_corpus.py` 已覆盖 corpus 组装、publication、quality、review artifacts
- `test_quality_scoring.py` / `test_review_policy.py` 覆盖质量门禁逻辑

## 本轮确认

- API 文档存在于 `docs/current/operations/api.md`
- Environment 文档存在于 `docs/current/operations/env.md`
- FastAPI app 已存在，但请求体仍是 bare `dict`，尚未引入 Pydantic request models
- API 层仍无 auth / rate limit / structured logging
- 视频任务会清理每次运行产生的临时工作目录，但共享 `.tmp_omni_media/` 根目录仍无 retention/prune 策略
- README 与运行文档已改为可移植命令，不再绑定单机解释器路径

## 当前待解

- 尚未引入 `ArtifactRepository` Protocol，`service.py` 仍直接依赖 `FileArtifactRepository`
- 尚未接入 PostgreSQL Repository
- 尚未接入 Qdrant 检索
- 尚未建立 Review UI / Review Queue 实体流转
- 尚未补 API 层自动化测试
- 尚未建立 coverage gate 与 performance benchmark
- 尚未补 structured logging / trace ID

## 下一刀建议

1. 先抽出 `ArtifactRepository` Protocol，降低 E8 迁移阻力
2. 再补 API request models、auth、rate limiting
3. 再补 structured logging / trace context
4. 最后补 FastAPI/ASGI 测试与 coverage gate
