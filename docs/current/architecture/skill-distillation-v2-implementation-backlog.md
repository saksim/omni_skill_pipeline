# Skill Distillation V2 Implementation Backlog

## 判词

这不是讨论稿，而是面向后续 `gpt-5.3-codex` 直接施工的全量开发拆解台账。目标是把 V2 从概念图纸拆到可执行任务包，避免后续实现阶段继续在“定义问题”上耗血。

## 1. 文档用途

本文件用于回答五件事：

- V2 到底要开发哪些功能
- 这些功能属于哪个工作流与模块
- 应该按什么顺序做
- 每个任务包建议触达哪些文件
- 每个任务包完成后如何验收

本文件默认读者：

- 后续施工模型：`gpt-5.3-codex`
- 人类角色：资深研发 / 架构 owner / reviewer

## 2. 使用方式

推荐施工节奏：

1. 先从本文件选择一个 `Task Package`
2. 再核对 [skill-distillation-v2.md](D:\download\gaming\new_program\data_helper\3_omni_skill_pipeline\docs\current\architecture\skill-distillation-v2.md) 中的架构约束
3. 再核对 [skill-distillation-v2-roadmap.md](D:\download\gaming\new_program\data_helper\3_omni_skill_pipeline\docs\current\architecture\skill-distillation-v2-roadmap.md) 中的阶段边界
4. 每次只实现一个任务包或同一 Epic 下的紧邻任务包
5. 每完成一包，就补测试、跑回归、更新文档

严禁：

- 跳过领域模型，直接大改 prompt
- 跳过质量门禁，直接扩大自动发布
- 先上复杂基础设施，再补核心语义模型
- 把所有模态继续压成纯文本后再做二次抽取

## 3. 总体交付地图

```text
E0  基线与施工地基
E1  领域模型与兼容层
E2  Corpus 与多资产蒸馏
E3  EvidenceNode 证据归一层
E4  模态专用解析器与增强
E5  SemanticAtom 抽取层
E6  SkillGraph 组装与发布层
E7  Quality Gate 与 Review Queue
E8  PostgreSQL / pgvector 持久化
E9  检索、增量更新、supersede
E10 外部接口升级：CLI / API / Worker
E11 测试资产、评估、基准与回归
E12 可观测性、安全、运行治理
E13 文档、迁移、收口与发布
```

## 4. 依赖原则

关键依赖链：

```text
E0 -> E1 -> E3 -> E5 -> E6 -> E7 -> E8 -> E9 -> E10 -> E13
E2 依赖 E1
E4 依赖 E3
E11 全程并行，但每个 Epic 完成都要补
E12 建议从 E7 后开始持续补
```

并行原则：

- 同一时期允许并行的任务包必须没有文件写入冲突
- 需要改 `models.py`、`service.py`、`repository.py` 的任务尽量串行
- 测试与文档补齐可在主功能稳定后并行补齐

## 5. DoD

每个任务包完成的最低 Definition of Done：

- 代码已实现
- 类型/序列化/接口行为自洽
- 新增或更新测试
- 回归现有 CLI / API / 核心样本
- 更新相关文档
- 输出中没有未解释的临时结构或 TODO 占位

## 6. Epic 级拆解

## E0 基线与施工地基

### 目标

冻结 V1 行为，建立之后所有改造的对照基线。

### 范围

- 固定样本集
- 当前输出快照
- 质量评估维度
- 施工规则与任务模板

### Task Packages

#### TP-E0-01 建立 V1 基线样本集

- 目标：为文本、音频、图片、视频、表格/时序分别建立代表性样本。
- 触达目录：
  - `examples/`
  - `tests/fixtures/` 或新建专用样本目录
  - `docs/current/status/`
- 交付：
  - 样本清单
  - 每个样本的用途说明
  - 风险标签
- 验收：
  - 至少覆盖 5 类模态
  - 每类至少 2 到 3 个样本

#### TP-E0-02 固化当前 V1 输出快照

- 目标：对样本集跑出当前 `bundle.json / skill.json / SKILL.md`。
- 触达目录：
  - `skills/drafts/`
  - 新建 `docs/current/status/baselines/` 或等效目录
- 验收：
  - 每个样本都有可追溯输出
  - 后续可人工对比 edit distance

#### TP-E0-03 定义评估指标

- 目标：定义 V2 全链验收指标。
- 推荐指标：
  - `traceability_rate`
  - `actionability_score`
  - `noise_penalty`
  - `reviewer_edit_distance`
  - `duplicate_skill_rate`
  - `false_procedure_rate`
- 验收：
  - 指标定义写入 docs
  - 指标含公式或明确计算规则

## E1 领域模型与兼容层

### 目标

引入 V2 领域模型，但不破坏现有外部入口。

### 范围

- 新模型
- 新 enum
- compatibility transformer
- 序列化 contract

### 关键对象

- `Corpus`
- `CorpusAssetRef`
- `EvidenceNode`
- `SemanticAtom`
- `SkillGraph`
- `SkillGraphNode`
- `SkillGraphEdge`
- `Publication`
- `LifecycleDecision`

### Task Packages

#### TP-E1-01 新增 V2 基础枚举与 dataclass

- 目标：在现有模型层建立 V2 类型系统。
- 主要文件：
  - `src/omni_skill_pipeline/models.py`
- 新增建议：
  - `AtomType`
  - `GraphNodeType`
  - `GraphEdgeType`
  - `PublicationType`
  - `LifecycleDecisionType`
- 验收：
  - 所有新模型可 `to_dict()` / `to_json()`
  - 不破坏现有 `SkillDocument`

#### TP-E1-02 建立兼容转换器

- 目标：让 V2 模型可渲染回 V1 视图。
- 主要文件：
  - `src/omni_skill_pipeline/transformers.py`
  - `src/omni_skill_pipeline/render.py`
- 需要能力：
  - `EvidenceUnit -> EvidenceNode`
  - `SkillGraph -> SkillDocument`
- 验收：
  - 给定最小 `SkillGraph` 可以产出合法 `SkillDocument`

#### TP-E1-03 增加 schema v2 草案

- 目标：让结构化 contract 先行。
- 主要文件：
  - `src/omni_skill_pipeline/schema.py`
  - `docs/current/contracts/`
- 验收：
  - 至少有 `skill-graph.schema.json` 或等效结构
  - schema 与 dataclass 字段对齐

## E2 Corpus 与多资产蒸馏

### 目标

从“单 asset 蒸馏”升级为“多资产联合蒸馏”。

### 范围

- `Corpus` 创建
- asset bundle 输入
- corpus metadata
- 跨 asset 追溯

### Task Packages

#### TP-E2-01 建立 Corpus 请求模型

- 目标：支持一轮蒸馏绑定多个输入资源。
- 主要文件：
  - `src/omni_skill_pipeline/models.py`
  - `src/omni_skill_pipeline/interfaces.py`
- 能力：
  - `CorpusDistillRequest`
  - 多 asset metadata
  - goal 级配置
- 验收：
  - 能表达文档+音频+图片联合输入

#### TP-E2-02 Service 支持多资产 load

- 目标：让 service 可以消费多个 adapter 输出。
- 主要文件：
  - `src/omni_skill_pipeline/service.py`
- 验收：
  - 单资产路径保持兼容
  - 多资产路径可组装成一个 `Corpus`

#### TP-E2-03 统一 corpus artifact 输出

- 目标：将当前 bundle 扩展成 corpus 级 bundle。
- 主要文件：
  - `src/omni_skill_pipeline/repository.py`
- 验收：
  - 一次 corpus 蒸馏能保存资产清单与 cross-asset 引用

## E3 EvidenceNode 证据归一层

### 目标

替换 V1 平面 `EvidenceUnit` 的单薄结构，建立带定位、结构、lineage 的证据节点。

### 范围

- time range
- spatial ref
- structural ref
- payload
- parent/child lineage

### Task Packages

#### TP-E3-01 定义 EvidenceNode 数据结构

- 目标：补齐所有模态共用字段。
- 主要文件：
  - `src/omni_skill_pipeline/models.py`
- 字段建议：
  - `text_content`
  - `payload`
  - `time_range`
  - `spatial_ref`
  - `structural_ref`
  - `parents`
  - `children`
  - `derived_from`
- 验收：
  - 能覆盖文档、图片、视频、表格、时序五类定位需求

#### TP-E3-02 建立 EvidenceBuilder

- 目标：把各 adapter 的输出统一构造成 `EvidenceNode`。
- 主要文件：
  - 新建 `src/omni_skill_pipeline/extraction/evidence_builder.py`
- 验收：
  - 现有 adapter 输出可映射到 `EvidenceNode`

#### TP-E3-03 支持 evidence lineage

- 目标：表达 derived evidence。
- 例子：
  - 视频 OCR node 来自 frame node
  - 异常 event node 来自 timeseries metric node
- 验收：
  - 支持 parent/child/derived_from 基础链路

## E4 模态专用解析器与增强

### 目标

按模态补足 V2 真正需要的结构信号。

### 范围

- 文档结构
- 音频语义
- 图片布局
- 视频时间语义
- 表格/时序统计语义

### Task Packages

#### TP-E4-01 文档结构解析增强

- 目标：抽 section、table、code block、figure。
- 主要文件：
  - `src/omni_skill_pipeline/adapters/text.py`
  - 新建 `src/omni_skill_pipeline/extraction/modality/document_parser.py`
- 验收：
  - 文档证据不再只按 paragraph
  - section hierarchy 可追溯

#### TP-E4-02 音频增强：utterance act 与 speaker role

- 目标：从 transcript 升级到 decision/action/question 层。
- 主要文件：
  - `src/omni_skill_pipeline/adapters/audio.py`
  - 新建 `src/omni_skill_pipeline/extraction/modality/audio_parser.py`
- 验收：
  - 至少区分 `question / decision / action_item / context`

#### TP-E4-03 图片增强：layout / region / OCR grouping

- 目标：让图片不止输出 OCR 文本。
- 主要文件：
  - `src/omni_skill_pipeline/adapters/image.py`
  - 新建 `src/omni_skill_pipeline/extraction/modality/image_parser.py`
- 验收：
  - 至少支持 region 分组与 layout role

#### TP-E4-04 视频增强：scene timeline / frame event / subtitle alignment

- 目标：让视频证据具备时间结构。
- 主要文件：
  - `src/omni_skill_pipeline/adapters/video.py`
  - `src/omni_skill_pipeline/providers/media.py`
  - 新建 `src/omni_skill_pipeline/extraction/modality/video_parser.py`
- 验收：
  - 可输出 scene cluster
  - 可输出 frame-level event
  - transcript 与 frame 具备最小对齐

#### TP-E4-05 表格/时序增强：baseline / change point / drift

- 目标：让时序从 heuristic profile 升级到 guardrail-ready 语义。
- 主要文件：
  - `src/omni_skill_pipeline/adapters/tabular.py`
  - 新建 `src/omni_skill_pipeline/extraction/modality/timeseries_parser.py`
- 验收：
  - 至少增加 change point 与 baseline 概念
  - 能把异常区间明确成 `Event` 类证据

## E5 SemanticAtom 抽取层

### 目标

用 `SemanticAtom` 替代宽泛 `Insight`，建立统一语义原子层。

### 原子最小集合

- `ClaimAtom`
- `ProcedureAtom`
- `RuleAtom`
- `VerificationAtom`
- `AntiPatternAtom`
- `EntityAtom`
- `EventAtom`
- `ExampleAtom`
- `MetricGuardrailAtom`
- `QuestionAtom`

### Task Packages

#### TP-E5-01 新建 AtomExtractor 主接口

- 主要文件：
  - `src/omni_skill_pipeline/interfaces.py`
  - 新建 `src/omni_skill_pipeline/extraction/atom_extractor.py`
- 验收：
  - 可替代现有 `InsightExtractor`

#### TP-E5-02 实现 HeuristicAtomExtractor

- 目标：先用可解释规则起步。
- 主要文件：
  - 新建 `src/omni_skill_pipeline/extraction/heuristic_atom_extractor.py`
- 验收：
  - 基于 `EvidenceNode` 至少能产出 procedure/rule/verification/anti-pattern

#### TP-E5-03 模态专用 atom 策略

- 目标：不同模态走不同 atom 策略。
- 主要文件：
  - `src/omni_skill_pipeline/extraction/modality/*.py`
- 验收：
  - 视频优先产 `EventAtom`
  - 时序优先产 `MetricGuardrailAtom`
  - 音频优先产 `QuestionAtom / EventAtom`

#### TP-E5-04 LLM AtomExtractor 作为增强而非真相源

- 目标：在 heuristic 之后引入增强抽取。
- 主要文件：
  - `src/omni_skill_pipeline/providers/openai_provider.py`
  - 新建 `src/omni_skill_pipeline/extraction/llm_atom_extractor.py`
- 验收：
  - LLM 失败时不影响基础原子输出

## E6 SkillGraph 组装与发布层

### 目标

让 `SkillGraph` 成为真相源，`SKILL.md` 退化为发布视图。

### 范围

- graph node
- graph edge
- graph builder
- publication builder
- renderer

### Task Packages

#### TP-E6-01 定义 SkillGraph node/edge 模型

- 主要文件：
  - `src/omni_skill_pipeline/models.py`
- 最小 node：
  - `StepNode`
  - `DecisionNode`
  - `VerificationNode`
  - `RiskNode`
  - `ExampleNode`
  - `VariableNode`
- 最小 edge：
  - `depends_on`
  - `justified_by`
  - `verified_by`
  - `parameterizes`
  - `supersedes`
- 验收：
  - graph 可完整序列化

#### TP-E6-02 实现 SkillGraphBuilder

- 主要文件：
  - 新建 `src/omni_skill_pipeline/assembly/skill_graph_builder.py`
- 输入：
  - `Corpus`
  - `EvidenceNode[]`
  - `SemanticAtom[]`
- 输出：
  - `SkillGraph`
- 验收：
  - 可从最小 atom 集构图
  - step 可追到 atom/evidence

#### TP-E6-03 实现 PublicationBuilder

- 主要文件：
  - 新建 `src/omni_skill_pipeline/assembly/publication_builder.py`
- 发布视图：
  - `SKILL.md`
  - `skill.json`
  - `checklist.json`
  - `decision_tree.json`
- 验收：
  - 至少两个视图可输出

#### TP-E6-04 兼容 V1 renderer

- 主要文件：
  - `src/omni_skill_pipeline/render.py`
- 验收：
  - 现有外部接口仍可拿到 `skill_markdown`

## E7 Quality Gate 与 Review Queue

### 目标

让系统真正具备“不发布低质量技能”的能力。

### 范围

- scoring
- review policy
- review task
- feedback loop

### Task Packages

#### TP-E7-01 实现质量评分器

- 主要文件：
  - 新建 `src/omni_skill_pipeline/quality/scoring.py`
- 最低分项：
  - `traceability_score`
  - `actionability_score`
  - `coverage_score`
  - `consistency_score`
  - `noise_score`
  - `novelty_score`
- 验收：
  - 每次蒸馏都能生成评分结果

#### TP-E7-02 实现 ReviewPolicy

- 主要文件：
  - 新建 `src/omni_skill_pipeline/quality/review_policy.py`
- 输出：
  - `auto_publish`
  - `review_required`
  - `reject`
- 验收：
  - 有明确阈值与理由码

#### TP-E7-03 ReviewTask 结构化落地

- 主要文件：
  - `src/omni_skill_pipeline/models.py`
  - `src/omni_skill_pipeline/repository.py`
- 验收：
  - review 不是只有备注文本
  - 原因码与修正建议可保存

#### TP-E7-04 反馈回流

- 目标：review 能反哺 atom / graph / policy。
- 主要文件：
  - 新建 `src/omni_skill_pipeline/quality/feedback.py`
- 验收：
  - review feedback 可用于后续修订

## E8 PostgreSQL / pgvector 持久化

### 目标

从 file-based artifact store 升级为正式持久层。

### 范围

- SQL migrations
- PG repository
- dual-write
- vector search storage

### Task Packages

#### TP-E8-01 设计 SQL V2 初始表结构

- 主要文件：
  - `infra/sql/`
- 推荐表：
  - `corpora`
  - `corpus_assets`
  - `evidence_nodes`
  - `semantic_atoms`
  - `skill_graphs`
  - `skill_graph_nodes`
  - `skill_graph_edges`
  - `publications`
  - `review_tasks`
  - `lineage_links`
- 验收：
  - 能承载 corpus、graph、publication、review

#### TP-E8-02 实现 PostgresRepository

- 主要文件：
  - 新建 `src/omni_skill_pipeline/persistence/postgres_repository.py`
- 验收：
  - 可保存并重建 graph/publication

#### TP-E8-03 Dual-write 策略

- 主要文件：
  - `src/omni_skill_pipeline/service.py`
  - `src/omni_skill_pipeline/repository.py`
- 验收：
  - 文件产物与 PG 可同时写入

#### TP-E8-04 接 pgvector

- 目标：为 publication 与 atom 准备向量检索。
- 验收：
  - 至少支持存与查

## E9 检索、增量更新、supersede

### 目标

让新证据能进入旧知识，而不是无限复制新 skill。

### 范围

- similarity
- lifecycle decision
- revise / merge / supersede
- lineage

### Task Packages

#### TP-E9-01 相似技能检索

- 主要文件：
  - 新建 `src/omni_skill_pipeline/retrieval/similarity.py`
- 相似度来源：
  - embedding
  - domain/tag
  - graph overlap
  - step overlap
- 验收：
  - 能找出相近 skill

#### TP-E9-02 LifecycleDecisionEngine

- 主要文件：
  - 新建 `src/omni_skill_pipeline/assembly/lifecycle.py`
- 决策：
  - `new`
  - `revise`
  - `merge`
  - `supersede`
  - `reject`
- 验收：
  - 能给出明确决策与理由

#### TP-E9-03 实现 supersede / lineage link

- 主要文件：
  - `src/omni_skill_pipeline/models.py`
  - `src/omni_skill_pipeline/persistence/postgres_repository.py`
- 验收：
  - 新旧 skill 关系可追溯

## E10 外部接口升级：CLI / API / Worker

### 目标

在不破坏现有入口的前提下，让外部接口认识 V2。

### 范围

- corpus 输入
- graph 输出
- review 状态查询
- publication 选择

### Task Packages

#### TP-E10-01 CLI 支持 corpus distill

- 主要文件：
  - `src/omni_skill_pipeline/cli.py`
- 能力：
  - 多资产输入
  - 输出视图选择
  - review 状态展示
- 验收：
  - CLI 保留原命令并新增 corpus 模式

#### TP-E10-02 API 支持 V2 输出结构

- 主要文件：
  - `src/omni_skill_pipeline/api_app.py`
- 新增建议：
  - graph metadata
  - available publications
  - review status
  - lifecycle decision
- 验收：
  - 老接口仍可返回 `skill_markdown`

#### TP-E10-03 Worker 任务类型升级

- 主要文件：
  - `src/omni_skill_pipeline/worker.py`
  - `apps/worker/main.py`
- 验收：
  - 支持 review queue / rebuild publication / revise existing skill

## E11 测试资产、评估、基准与回归

### 目标

把“好坏”变成可以持续比较的东西。

### 范围

- unit tests
- integration tests
- golden samples
- regression dashboard

### Task Packages

#### TP-E11-01 模型与转换器测试

- 主要文件：
  - `tests/`
- 覆盖：
  - 新模型序列化
  - graph -> document
  - evidence -> atom -> graph

#### TP-E11-02 模态集成测试

- 覆盖：
  - document -> graph
  - audio -> atom
  - image -> layout/ocr
  - video -> scene timeline
  - timeseries -> guardrail

#### TP-E11-03 质量回归测试

- 目标：固定样本集，比较输出质量变化。
- 验收：
  - 至少能比较 traceability 与 reviewer edit distance

#### TP-E11-04 性能与成本基线

- 目标：避免 V2 语义增强导致成本失控。
- 验收：
  - 记录耗时、token、关键 provider 调用次数

## E12 可观测性、安全、运行治理

### 目标

让 V2 在工程上可运行、可诊断、可控。

### 范围

- structured logs
- metrics
- audit trail
- secret handling
- temp file hygiene

### Task Packages

#### TP-E12-01 结构化日志与 trace id

- 主要文件：
  - `src/omni_skill_pipeline/service.py`
  - `src/omni_skill_pipeline/worker.py`
- 验收：
  - 每轮蒸馏具备 trace id
  - 可追踪 asset -> graph -> publication

#### TP-E12-02 Provider 调用审计

- 目标：记录 ASR/OCR/LLM/Vision 调用摘要。
- 验收：
  - 能按 corpus 查看 provider footprint

#### TP-E12-03 安全与敏感信息控制

- 目标：保证日志与 artifacts 不泄漏密钥与敏感字段。
- 验收：
  - token、secret、credential 不落盘

#### TP-E12-04 临时工件治理

- 目标：整理 `.tmp_omni_media/` 与中间文件生命周期。
- 验收：
  - 有清理策略与失败回收策略

## E13 文档、迁移、收口与发布

### 目标

让 V2 最终能交接、能迁移、能发布。

### 范围

- docs
- migration plan
- V1 deprecation
- release notes

### Task Packages

#### TP-E13-01 文档持续同步

- 范围：
  - README
  - architecture
  - contracts
  - operations
  - status
- 验收：
  - 外部入口文档与代码一致

#### TP-E13-02 V1 -> V2 迁移指南

- 目标：告诉维护者何时走兼容层、何时切换主链。
- 验收：
  - 迁移步骤、回退策略、风险列表齐全

#### TP-E13-03 发布与切换标准

- 目标：定义什么时候可以宣布 V2 成为主链。
- 标准至少包括：
  - graph 为真相源
  - review queue 已落地
  - 至少两个 publication 可用
  - PG repository 稳定
  - 基线样本回归优于 V1

## 7. 按代码目录的开发清单

### `src/omni_skill_pipeline/models.py`

- 新增 V2 dataclass 与 enum
- 保留 `SkillDocument` 兼容
- 增加 graph / review / lifecycle 模型

### `src/omni_skill_pipeline/service.py`

- 支持 corpus
- 支持 dual-path: V1 / V2 shadow
- 接 quality gate / review policy / dual-write

### `src/omni_skill_pipeline/repository.py`

- 过渡期保留 file artifact
- 抽象 repository 接口
- 准备 PG repository 切换

### `src/omni_skill_pipeline/render.py`

- 支持 `SkillGraph -> SkillDocument -> SKILL.md`
- 支持新 publication renderer

### `src/omni_skill_pipeline/adapters/`

- 升级为输出结构化 evidence 所需字段
- 逐模态补强结构信息

### `src/omni_skill_pipeline/providers/`

- 新增 LLM atom extraction 支持
- 保持 provider 为能力层，不吞业务规则

### 新增目录建议

```text
src/omni_skill_pipeline/
  extraction/
  assembly/
  quality/
  retrieval/
  persistence/
  routing/
```

## 8. 推荐施工批次

推荐把所有工作拆成以下七批，而不是一次性大改：

### 批次 A

- `TP-E0-01`
- `TP-E0-02`
- `TP-E0-03`
- `TP-E1-01`
- `TP-E1-02`

### 批次 B

- `TP-E1-03`
- `TP-E3-01`
- `TP-E3-02`
- `TP-E3-03`

### 批次 C

- `TP-E4-01`
- `TP-E4-02`
- `TP-E4-03`
- `TP-E4-04`
- `TP-E4-05`

### 批次 D

- `TP-E5-01`
- `TP-E5-02`
- `TP-E5-03`
- `TP-E6-01`
- `TP-E6-02`

### 批次 E

- `TP-E6-03`
- `TP-E6-04`
- `TP-E7-01`
- `TP-E7-02`
- `TP-E7-03`
- `TP-E7-04`

### 批次 F

- `TP-E8-01`
- `TP-E8-02`
- `TP-E8-03`
- `TP-E8-04`
- `TP-E9-01`
- `TP-E9-02`
- `TP-E9-03`

### 批次 G

- `TP-E10-01`
- `TP-E10-02`
- `TP-E10-03`
- `TP-E11-*`
- `TP-E12-*`
- `TP-E13-*`

## 9. 交给 gpt-5.3-codex 的任务模板

后续每次可以用如下格式下发任务：

```text
你现在负责实现 Task Package: TP-EX-YY

必读文档：
- docs/current/architecture/skill-distillation-v2.md
- docs/current/architecture/skill-distillation-v2-roadmap.md
- docs/current/architecture/skill-distillation-v2-implementation-backlog.md

任务目标：
- <复制该任务包目标>

本次允许修改的文件：
- <列出文件>

必须完成：
- 代码实现
- 测试补齐
- 文档同步

验收标准：
- <复制该任务包验收标准>

禁止事项：
- 不要扩大范围到其他 Epic
- 不要破坏现有 CLI / API 兼容
- 不要引入未落地的新基础设施依赖
```

## 10. 当前最值得先做的五包

如果魔尊要最快进入施工态，最优先的是：

1. `TP-E0-01` 建立样本集
2. `TP-E1-01` 新增 V2 基础模型
3. `TP-E1-02` 建立兼容转换器
4. `TP-E3-01` 定义 `EvidenceNode`
5. `TP-E5-01` 建立 `AtomExtractor` 接口

做完这五包，V2 才真正拥有骨架；后面的 provider、review、存储、检索才不会继续搭在沙地上。
