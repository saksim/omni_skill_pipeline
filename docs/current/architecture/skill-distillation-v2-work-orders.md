# Skill Distillation V2 Work Orders

## 判词

本文件把 `E1` 及之后的全部开发工作压成可直接下发给 `gpt-5.3-codex` 的施工任务单。若 [skill-distillation-v2-implementation-backlog.md](D:\download\gaming\new_program\data_helper\3_omni_skill_pipeline\docs\current\architecture\skill-distillation-v2-implementation-backlog.md) 是总台账，此文件就是逐包开斩的作战排程。

## 1. 施工总规则

- 一次只执行一个工单，或同一批次中明确无写冲突的少量工单。
- 若工单触达 `models.py`、`service.py`、`repository.py`，默认串行。
- 每个工单都必须带测试与文档同步。
- 未完成前置工单，不得跳级施工。
- 工单名称沿用 backlog 中的 `TP-*` 编号，避免后续混乱。

## 2. 工单通用模板

每次下发给 `gpt-5.3-codex` 时，统一使用：

```text
你现在负责实现工单：TP-EX-YY

必读文档：
- docs/current/architecture/skill-distillation-v2.md
- docs/current/architecture/skill-distillation-v2-roadmap.md
- docs/current/architecture/skill-distillation-v2-implementation-backlog.md
- docs/current/architecture/skill-distillation-v2-work-orders.md

本次目标：
- <复制工单目标>

主要文件：
- <复制主要文件>

必须完成：
- 代码实现
- 测试补齐
- 文档同步

验收标准：
- <复制本工单验收>

禁止事项：
- 不要扩大到未列出的 Epic
- 不要破坏现有 CLI / API 兼容
- 不要私自引入新的重型基础设施
```

## 3. 推荐执行顺序

```text
Batch A: E1
Batch B: E2 + E3
Batch C: E4
Batch D: E5 + E6(前半)
Batch E: E6(后半) + E7
Batch F: E8 + E9
Batch G: E10 + E11 + E12 + E13
```

## 4. Work Orders

## Batch A

| 工单 | Epic | 目标 | 主要文件 | 前置 | 测试 | 验收 |
| --- | --- | --- | --- | --- | --- | --- |
| `TP-E1-01` | E1 | 新增 V2 基础枚举与 dataclass | `src/omni_skill_pipeline/models.py` | E0 | 新模型序列化测试 | `Corpus/EvidenceNode/SemanticAtom/SkillGraph` 等可 `to_dict()/to_json()`，且不破坏 `SkillDocument` |
| `TP-E1-02` | E1 | 建立兼容转换器 | `src/omni_skill_pipeline/transformers.py`, `src/omni_skill_pipeline/render.py` | `TP-E1-01` | graph/document 转换测试 | `EvidenceUnit -> EvidenceNode` 与 `SkillGraph -> SkillDocument` 最小闭环可跑 |
| `TP-E1-03` | E1 | 增加 schema v2 草案 | `src/omni_skill_pipeline/schema.py`, `docs/current/contracts/` | `TP-E1-01` | schema 校验测试 | 至少落一份 `skill-graph` 结构 contract，并与 dataclass 字段对齐 |

## Batch B

| 工单 | Epic | 目标 | 主要文件 | 前置 | 测试 | 验收 |
| --- | --- | --- | --- | --- | --- | --- |
| `TP-E2-01` | E2 | 建立 `CorpusDistillRequest` 与多资产请求模型 | `src/omni_skill_pipeline/models.py`, `src/omni_skill_pipeline/interfaces.py` | `TP-E1-01` | request 构造测试 | 单个请求可表达多资产联合蒸馏 |
| `TP-E2-02` | E2 | Service 支持多资产 load | `src/omni_skill_pipeline/service.py` | `TP-E2-01` | service 集成测试 | 单资产路径兼容，多资产路径可组装 `Corpus` |
| `TP-E2-03` | E2 | 统一 corpus artifact 输出 | `src/omni_skill_pipeline/repository.py` | `TP-E2-02` | repository 输出测试 | 一次 corpus 蒸馏能保存资产清单与 cross-asset 引用 |
| `TP-E3-01` | E3 | 定义 `EvidenceNode` 完整结构 | `src/omni_skill_pipeline/models.py` | `TP-E1-01` | model 测试 | 支持 `time_range/spatial_ref/structural_ref/payload/lineage` |
| `TP-E3-02` | E3 | 建立 `EvidenceBuilder` | `src/omni_skill_pipeline/extraction/evidence_builder.py` | `TP-E3-01` | evidence builder 测试 | 现有 adapter 输出可映射成 `EvidenceNode` |
| `TP-E3-03` | E3 | 支持 evidence lineage | `src/omni_skill_pipeline/models.py`, `src/omni_skill_pipeline/extraction/evidence_builder.py` | `TP-E3-02` | lineage 测试 | parent/child/derived_from 基础链路成立 |

## Batch C

| 工单 | Epic | 目标 | 主要文件 | 前置 | 测试 | 验收 |
| --- | --- | --- | --- | --- | --- | --- |
| `TP-E4-01` | E4 | 文档结构解析增强 | `src/omni_skill_pipeline/adapters/text.py`, `src/omni_skill_pipeline/extraction/modality/document_parser.py` | `TP-E3-02` | 文档结构测试 | 支持 section/table/code/figure 级 evidence |
| `TP-E4-02` | E4 | 音频增强：utterance act 与 speaker role | `src/omni_skill_pipeline/adapters/audio.py`, `src/omni_skill_pipeline/extraction/modality/audio_parser.py` | `TP-E3-02` | 音频语义测试 | 至少区分 `question/decision/action_item/context` |
| `TP-E4-03` | E4 | 图片增强：layout / region / OCR grouping | `src/omni_skill_pipeline/adapters/image.py`, `src/omni_skill_pipeline/extraction/modality/image_parser.py` | `TP-E3-02` | 图片布局测试 | 输出不再只剩平面 OCR 文本 |
| `TP-E4-04` | E4 | 视频增强：scene timeline / frame event / subtitle alignment | `src/omni_skill_pipeline/adapters/video.py`, `src/omni_skill_pipeline/providers/media.py`, `src/omni_skill_pipeline/extraction/modality/video_parser.py` | `TP-E3-02` | 视频解析测试 | 可输出 scene cluster、frame event、最小 transcript-frame 对齐 |
| `TP-E4-05` | E4 | 表格/时序增强：baseline / change point / drift | `src/omni_skill_pipeline/adapters/tabular.py`, `src/omni_skill_pipeline/extraction/modality/timeseries_parser.py` | `TP-E3-02` | 时序解析测试 | 至少引入 baseline、change point、异常区间 event |

## Batch D

| 工单 | Epic | 目标 | 主要文件 | 前置 | 测试 | 验收 |
| --- | --- | --- | --- | --- | --- | --- |
| `TP-E5-01` | E5 | 新建 `AtomExtractor` 主接口 | `src/omni_skill_pipeline/interfaces.py`, `src/omni_skill_pipeline/extraction/atom_extractor.py` | `TP-E3-02` | 接口与冒烟测试 | 可替代现有 `InsightExtractor` 接口位 |
| `TP-E5-02` | E5 | 实现 `HeuristicAtomExtractor` | `src/omni_skill_pipeline/extraction/heuristic_atom_extractor.py` | `TP-E5-01` | heuristic atom 测试 | 基于 `EvidenceNode` 能稳定产出 procedure/rule/verification/anti-pattern |
| `TP-E5-03` | E5 | 建立模态专用 atom 策略 | `src/omni_skill_pipeline/extraction/modality/*.py` | `TP-E5-02`, `TP-E4-*` | 各模态 atom 测试 | 视频优先 event，时序优先 guardrail，音频优先 question/event |
| `TP-E5-04` | E5 | LLM AtomExtractor 增强 | `src/omni_skill_pipeline/providers/openai_provider.py`, `src/omni_skill_pipeline/extraction/llm_atom_extractor.py` | `TP-E5-02` | fallback 测试 | LLM 失败不影响基础 atom 输出 |
| `TP-E6-01` | E6 | 定义 `SkillGraph` node/edge 模型 | `src/omni_skill_pipeline/models.py` | `TP-E1-01`, `TP-E5-01` | graph model 测试 | graph 结构完整可序列化 |
| `TP-E6-02` | E6 | 实现 `SkillGraphBuilder` | `src/omni_skill_pipeline/assembly/skill_graph_builder.py` | `TP-E6-01`, `TP-E5-03` | graph builder 测试 | step 可追到 atom，再追到 evidence |

## Batch E

| 工单 | Epic | 目标 | 主要文件 | 前置 | 测试 | 验收 |
| --- | --- | --- | --- | --- | --- | --- |
| `TP-E6-03` | E6 | 实现 `PublicationBuilder` | `src/omni_skill_pipeline/assembly/publication_builder.py` | `TP-E6-02` | publication 输出测试 | 至少输出 `SKILL.md` 与另一种结构化 publication |
| `TP-E6-04` | E6 | 兼容 V1 renderer | `src/omni_skill_pipeline/render.py` | `TP-E6-03` | markdown 回归测试 | 现有外部接口仍能拿到 `skill_markdown` |
| `TP-E7-01` | E7 | 实现质量评分器 | `src/omni_skill_pipeline/quality/scoring.py` | `TP-E6-02` | score 测试 | 每次蒸馏生成 `traceability/actionability/coverage/consistency/noise/novelty` 评分 |
| `TP-E7-02` | E7 | 实现 `ReviewPolicy` | `src/omni_skill_pipeline/quality/review_policy.py` | `TP-E7-01` | policy 测试 | 输出 `auto_publish/review_required/reject` 且附理由码 |
| `TP-E7-03` | E7 | `ReviewTask` 结构化落地 | `src/omni_skill_pipeline/models.py`, `src/omni_skill_pipeline/repository.py` | `TP-E7-02` | review task 测试 | review 不再只是一段备注文本 |
| `TP-E7-04` | E7 | review feedback 回流 | `src/omni_skill_pipeline/quality/feedback.py` | `TP-E7-03` | feedback 测试 | feedback 可进入后续修订链路 |

## Batch F

| 工单 | Epic | 目标 | 主要文件 | 前置 | 测试 | 验收 |
| --- | --- | --- | --- | --- | --- | --- |
| `TP-E8-01` | E8 | 设计 SQL V2 初始表结构 | `infra/sql/` | `TP-E6-02`, `TP-E7-03` | migration 校验 | schema 能承载 corpus/evidence/atom/graph/publication/review |
| `TP-E8-02` | E8 | 实现 `PostgresRepository` | `src/omni_skill_pipeline/persistence/postgres_repository.py` | `TP-E8-01` | repository 集成测试 | graph/publication 可持久化与重建 |
| `TP-E8-03` | E8 | Dual-write 策略 | `src/omni_skill_pipeline/service.py`, `src/omni_skill_pipeline/repository.py` | `TP-E8-02` | dual-write 测试 | 文件产物与 PG 可同时写入 |
| `TP-E8-04` | E8 | 接 pgvector | `src/omni_skill_pipeline/persistence/postgres_repository.py`, `infra/sql/` | `TP-E8-02` | vector 存取测试 | publication 与 atom 向量可存可查 |
| `TP-E9-01` | E9 | 相似技能检索 | `src/omni_skill_pipeline/retrieval/similarity.py` | `TP-E8-04` | similarity 测试 | 能找出相近 skill |
| `TP-E9-02` | E9 | `LifecycleDecisionEngine` | `src/omni_skill_pipeline/assembly/lifecycle.py` | `TP-E9-01`, `TP-E7-02` | lifecycle 测试 | 能输出 `new/revise/merge/supersede/reject` |
| `TP-E9-03` | E9 | 实现 supersede / lineage link | `src/omni_skill_pipeline/models.py`, `src/omni_skill_pipeline/persistence/postgres_repository.py` | `TP-E9-02` | lineage 测试 | 新旧 skill 关系可审计追溯 |

## Batch G

| 工单 | Epic | 目标 | 主要文件 | 前置 | 测试 | 验收 |
| --- | --- | --- | --- | --- | --- | --- |
| `TP-E10-01` | E10 | CLI 支持 corpus distill 与 publication 选择 | `src/omni_skill_pipeline/cli.py` | `TP-E6-03`, `TP-E8-03` | CLI 回归测试 | 保留旧命令并新增 corpus 模式 |
| `TP-E10-02` | E10 | API 支持 V2 输出结构 | `src/omni_skill_pipeline/api_app.py` | `TP-E6-03`, `TP-E7-03` | API 集成测试 | 返回 graph metadata、available publications、review status，旧接口仍兼容 |
| `TP-E10-03` | E10 | Worker 任务类型升级 | `src/omni_skill_pipeline/worker.py`, `apps/worker/main.py` | `TP-E10-02` | worker 任务测试 | 支持 review queue / rebuild publication / revise existing skill |
| `TP-E11-01` | E11 | 模型与转换器测试补齐 | `tests/` | `TP-E1-02`, `TP-E6-02` | 单元测试 | graph/document/evidence/atom 转换有回归覆盖 |
| `TP-E11-02` | E11 | 模态集成测试补齐 | `tests/` | `TP-E4-*`, `TP-E5-*` | 集成测试 | document/audio/image/video/timeseries 均有端到端验证 |
| `TP-E11-03` | E11 | 质量回归测试 | `tests/`, `docs/current/status/baselines/` | `TP-E7-01` | 基线回归脚本 | 能对比 `traceability` 与 `reviewer_edit_distance` |
| `TP-E11-04` | E11 | 性能与成本基线 | `tests/`, `docs/current/status/baselines/` | `TP-E8-03` | perf/成本记录 | 记录耗时、token、provider 调用次数 |
| `TP-E12-01` | E12 | 结构化日志与 trace id | `src/omni_skill_pipeline/service.py`, `src/omni_skill_pipeline/worker.py` | `TP-E7-01` | logging 测试 | 一次蒸馏可追踪 asset -> graph -> publication |
| `TP-E12-02` | E12 | provider 调用审计 | `src/omni_skill_pipeline/service.py`, `src/omni_skill_pipeline/providers/` | `TP-E12-01` | audit 测试 | 能按 corpus 查看 provider footprint |
| `TP-E12-03` | E12 | 安全与敏感信息控制 | `src/omni_skill_pipeline/service.py`, `src/omni_skill_pipeline/repository.py` | `TP-E12-01` | redaction 测试 | token/secret/credential 不落盘 |
| `TP-E12-04` | E12 | 临时工件治理 | `src/omni_skill_pipeline/adapters/video.py`, `src/omni_skill_pipeline/providers/media.py` | `TP-E12-01` | temp cleanup 测试 | `.tmp_omni_media/` 有清理与失败回收策略 |
| `TP-E13-01` | E13 | 文档持续同步 | `README.md`, `docs/` | 全程 | doc sync 检查 | 对外文档与代码一致 |
| `TP-E13-02` | E13 | V1 -> V2 迁移指南 | `docs/current/architecture/`, `docs/current/operations/` | `TP-E8-03`, `TP-E10-02` | 文档审阅 | 迁移步骤、回退策略、风险齐全 |
| `TP-E13-03` | E13 | 发布与切换标准 | `docs/current/status/`, `docs/history/` | `TP-E9-03`, `TP-E11-03` | 发布审查 | 明确何时 V2 可成为主链 |
| `TP-E13-04` | E13 | Linux 统一验尸编排脚本 | `scripts/run_linux_validation_suite.py`, `tests/test_linux_validation_suite_script.py`, `docs/current/operations/testing.md` | `TP-E11-03`, `TP-E11-04`, `TP-E13-03` | 脚本 smoke 测试 | Linux 可一条命令串起 CI/doc-sync/quality/perf 基线验收 |
| `TP-E13-05` | E13 | Postgres 长稳验尸脚本 | `scripts/run_postgres_soak_validation.py`, `tests/test_postgres_soak_validation_script.py`, `scripts/run_linux_validation_suite.py`, `docs/current/operations/testing.md` | `TP-E13-04` | 脚本 smoke 测试 | Linux 可一条命令打包 TP-E8/E9 + review queue + dual-write benchmark 的 Postgres 长稳验收 |

## 5. 近战优先级

魔尊若要最快开工，直接按以下顺序下发：

1. `TP-E1-01`
2. `TP-E1-02`
3. `TP-E3-01`
4. `TP-E5-01`
5. `TP-E6-01`

这是最小骨架五连斩。若连这五刀都未落下，后续 provider、review、PG、检索全都会继续搭在旧 V1 的薄骨上。
