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


#### TP-E13-12 Release gate 聚合脚本

- 目标：将 beta/ga/roadmap 三个 gate 的 Linux 验证入口聚合为单命令编排，统一 dry-run 计划与参数透传。
- 主要文件：
  - `scripts/run_release_gate_validation.py`
  - `tests/test_release_gate_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 支持阶段筛选（`beta_gate/ga_gate/roadmap_gate`）
  - 支持 coverage/container/postgres/calibration 参数透传到下游 Linux suite
  - 支持 dry-run 输出 `e13-release-gate-validation-plan.json` 与 nested suite 计划

#### TP-E13-13 Release switch 判定脚本

- 目标：将 release gate、TP 合同校验、doc-sync 与证据判定收敛成 Linux 单命令入口，输出 `GO/HOLD` 判定报告。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 支持阶段筛选（`release_gate/release_contract/doc_sync`）
  - 支持 `--decision-only` 直接基于已落盘报告输出判定
  - 支持输出 `e13-release-switch-decision-report.json`，并在 HOLD 时默认返回非零退出码

#### TP-E13-14 Release switch 证据闭环加固

- 目标：将 release switch 的判定门槛升级为必须包含 release-gate 顶层计划与 beta/ga/roadmap 子计划的完整证据包，避免缺包误判 `GO`。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - decision 评估纳入 `release-gate-output`、`beta-suite-output`、`ga-suite-output`、`roadmap-suite-output`
  - 证据包缺失或阶段不完整时，判定强制 `HOLD`
  - 完整证据包场景可稳定输出 `GO`

#### TP-E13-15 Release switch 证据时效门禁

- 目标：在 release switch 判定中加入 evidence freshness 守门，避免复用陈旧报告误判 `GO`。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 支持 `--max-evidence-age-hours`（默认开启 freshness 门禁）
  - evidence 文件超时效窗口时，判定强制 `HOLD`
  - 支持 `--max-evidence-age-hours 0` 显式关闭 freshness 门禁

#### TP-E13-16 Release switch 未来时间偏移门禁

- 目标：在 release switch 判定中加入 future timestamp skew 守门，防止证据文件时间被调到未来导致 freshness 绕过。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 支持 `--max-evidence-future-skew-hours`（默认开启 future-skew 门禁）
  - evidence 文件未来偏移超过阈值时，判定强制 `HOLD`
  - 支持 `--max-evidence-future-skew-hours 0` 显式关闭 future-skew 门禁

#### TP-E13-17 Release switch 证据批次一致性门禁

- 目标：在 release switch 判定中加入 evidence cohort skew 守门，避免混用跨批次报告导致 `GO` 误判。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 支持 `--max-evidence-cohort-skew-hours`（默认开启 cohort-skew 门禁）
  - evidence 文件时间跨度超过阈值时，判定强制 `HOLD`
  - 支持 `--max-evidence-cohort-skew-hours 0` 显式关闭 cohort-skew 门禁

#### TP-E13-18 Release switch 证据绑定一致性门禁

- 目标：在 release switch 判定中加入 release-gate 证据绑定守门，确保 `release-gate-output` 内部 beta/ga/roadmap stage 的 `--output` 指向与本次判定传入证据路径一致，避免混包误判 `GO`。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate stage `--output` 与 `--beta-suite-output/--ga-suite-output/--roadmap-suite-output` 一致性
  - 任一 stage 输出绑定错配时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-output-binding-check` 显式关闭绑定门禁

#### TP-E13-19 Release switch stage 合同一致性门禁

- 目标：在 release switch 判定中加入 release-gate stage 合同守门，确保 `beta_gate/ga_gate/roadmap_gate` 命令持续指向 `scripts/run_linux_validation_suite.py` 且 `--stages` 组合保持约定，防止“路径一致但执行计划漂移”误判 `GO`。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate stage 命令必须匹配 `scripts/run_linux_validation_suite.py + --stages` 合同
  - 任一 stage 命令或 `--stages` 漂移时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-stage-contract-check` 显式关闭 stage 合同门禁

#### TP-E13-20 Release switch 参数覆盖歧义门禁

- 目标：在 release switch 判定中加入 release-gate 参数覆盖歧义守门，确保 `beta_gate/ga_gate/roadmap_gate` 命令中的 `--stages` 与 `--output` 仅出现一次，防止重复参数覆盖绕过合同校验误判 `GO`。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate 各 stage 命令 `--stages/--output` 参数出现次数必须为 `1`
  - 任一 stage 存在重复参数覆盖歧义时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-option-override-check` 显式关闭参数覆盖门禁

#### TP-E13-21 Release switch 宽松开关绕过门禁

- 目标：在 release switch 判定中加入 release-gate 宽松开关守门，阻断通过 `--allow-regression/--no-coverage/--container-skip-build/--container-skip-run/--allow-secondary-failures` 等降级参数“带病放行”的 `GO` 误判。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate stage 命令不得包含宽松开关参数
  - 任一 stage 命中宽松开关时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-relaxed-flags-check` 显式关闭宽松开关门禁

#### TP-E13-22 Release switch dry-run 绕过门禁

- 目标：在 release switch 判定中加入 release-gate dry-run 守门，阻断通过 `--dry-run` 伪执行 stage 命令导致“证据看似完整但未真实执行”的 `GO` 误判。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate stage 命令不得包含 `--dry-run`
  - 任一 stage 命中 `--dry-run` 时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-dry-run-check` 显式关闭 dry-run 门禁

#### TP-E13-23 Release switch 脚本定位伪装门禁

- 目标：在 release switch 判定中加入 release-gate 脚本定位守门，确保 `beta_gate/ga_gate/roadmap_gate` 命令真正执行的是 `scripts/run_linux_validation_suite.py`，而不是“命令中仅携带同名 token”的伪装路径。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate stage 命令中第一个 script token 必须是 `scripts/run_linux_validation_suite.py`
  - 若预期脚本仅作为附带 token 出现（未实际执行）时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-script-position-check` 显式关闭脚本定位门禁

#### TP-E13-24 Release switch inline-exec 绕过门禁

- 目标：在 release switch 判定中加入 release-gate inline-dispatch 守门，阻断通过 `-c/-m/-` 让 python 在预期 linux-suite script token 前切换执行模式的绕过路径。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate stage 命令在 `scripts/run_linux_validation_suite.py` token 之前不得出现 `-c/-m/-`
  - 任一 stage 命中 inline-dispatch 绕过模式时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-inline-exec-check` 显式关闭 inline-dispatch 门禁

#### TP-E13-25 Release switch 脚本路径锚定门禁

- 目标：在 release switch 判定中加入 release-gate script anchor 守门，确保 stage 命令解析后的执行脚本必须锚定仓库内 canonical `scripts/run_linux_validation_suite.py`，阻断同名外部路径伪装绕过。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate stage 首个 script token 解析后的 canonical path 必须等于仓库内 `scripts/run_linux_validation_suite.py`
  - 任一 stage 命中同名外部路径伪装时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-script-anchor-check` 显式关闭 script-anchor 门禁

#### TP-E13-26 Release switch Python 绑定一致性门禁

- 目标：在 release switch 判定中加入 release-gate python-binding 守门，确保 stage 命令的 `--python` 与实际 launcher 前缀、以及 release-switch 输入值三方一致，阻断执行器覆盖或漂移导致的伪 `GO`。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate stage 命令 `--python` 仅出现一次，且值必须等于 release-switch 输入 `--python`
  - 默认校验 release-gate stage 命令脚本前 launcher token 串必须与 `--python` 值绑定一致
  - 任一 stage 命中 python-binding 漂移时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-python-binding-check` 显式关闭 python-binding 门禁

#### TP-E13-27 Release switch 覆盖率阈值绑定门禁

- 目标：在 release switch 判定中加入 release-gate coverage-floor 守门，确保 beta stage 的 `--coverage-fail-under` 既与 release-switch 输入绑定一致，也不低于最低发布阈值，阻断“降阈值放行”导致的伪 `GO`。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate` 命令 `--coverage-fail-under` 仅出现一次且为可解析浮点值
  - 默认校验该值必须等于 release-switch 输入 `--coverage-fail-under` 且不低于 `50`
  - 任一命中 coverage 阈值漂移或降级时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-coverage-floor-check` 显式关闭 coverage-floor 门禁

#### TP-E13-28 Release switch Python 优化旗标门禁

- 目标：在 release switch 判定中加入 release-gate python-optimization 守门，禁止 stage launcher 使用 `-O/-OO` 优化旗标，避免 assert 校验被跳过导致伪 `GO`。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `-O/-OO`
  - 任一 stage 命中 python 优化旗标时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-python-optimization-check` 显式关闭 python-optimization 门禁

#### TP-E13-29 Release switch Python 传递链优化旗标门禁

- 目标：在 release switch 判定中加入 release-gate `--python` 传递链 optimization 守门，禁止 stage `--python` 值携带 `-O/-OO`，避免下游执行链被隐式优化导致 assert 合同被绕过。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令 `--python` 仅出现一次且可解析
  - 默认校验 `--python` 传递值中不允许出现 `-O/-OO`
  - 任一 stage 命中 `--python` 传递优化旗标时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-python-option-optimization-check` 显式关闭该门禁

#### TP-E13-30 Release switch PYTHONOPTIMIZE 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `PYTHONOPTIMIZE` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 env 赋值绕过 assert 合同校验。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `PYTHONOPTIMIZE=*`
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `PYTHONOPTIMIZE=*`
  - 任一 stage 命中 `PYTHONOPTIMIZE` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-python-optimize-env-check` 显式关闭该门禁

#### TP-E13-31 Release switch Python 传递链 inline-exec 门禁

- 目标：在 release switch 判定中加入 release-gate `--python` 传递链 inline-dispatch 守门，禁止 stage `--python` 值携带 `-c/-m/-`，避免下游执行链切换成 inline 模式绕过脚本合同。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令 `--python` 仅出现一次且可解析
  - 默认校验 `--python` 传递值中不允许出现 `-c/-m/-`
  - 任一 stage 命中 `--python` 传递 inline-dispatch 旗标时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-python-option-inline-exec-check` 显式关闭该门禁

#### TP-E13-32 Release switch PYTHONPATH 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `PYTHONPATH` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 path 注入重定向模块解析，避免绕过预期 runtime 合同。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `PYTHONPATH=*`
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `PYTHONPATH=*`
  - 任一 stage 命中 `PYTHONPATH` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-python-path-env-check` 显式关闭该门禁

#### TP-E13-33 Release switch PYTHONHOME 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `PYTHONHOME` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 home 注入重定向解释器运行时根路径，避免绕过预期 runtime 合同。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `PYTHONHOME=*`
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `PYTHONHOME=*`
  - 任一 stage 命中 `PYTHONHOME` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-python-home-env-check` 显式关闭该门禁

#### TP-E13-34 Release switch PYTHONUSERBASE 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `PYTHONUSERBASE` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 user-base 注入重定向 user-site 包解析路径，避免绕过预期 runtime 合同。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `PYTHONUSERBASE=*`
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `PYTHONUSERBASE=*`
  - 任一 stage 命中 `PYTHONUSERBASE` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-python-user-base-env-check` 显式关闭该门禁

#### TP-E13-35 Release switch PYTHONBREAKPOINT 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `PYTHONBREAKPOINT` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 breakpoint hook 注入改变调试分发行为，避免绕过预期 runtime 合同。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `PYTHONBREAKPOINT=*`
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `PYTHONBREAKPOINT=*`
  - 任一 stage 命中 `PYTHONBREAKPOINT` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-python-breakpoint-env-check` 显式关闭该门禁

#### TP-E13-36 Release switch PYTHONSTARTUP 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `PYTHONSTARTUP` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 startup hook 注入启动脚本，避免绕过预期 runtime 合同。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `PYTHONSTARTUP=*`
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `PYTHONSTARTUP=*`
  - 任一 stage 命中 `PYTHONSTARTUP` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-python-startup-env-check` 显式关闭该门禁

#### TP-E13-37 Release switch PYTHONINSPECT 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `PYTHONINSPECT` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 inspect hook 切入交互模式，避免执行链漂移误判 `GO`。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `PYTHONINSPECT=*`
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `PYTHONINSPECT=*`
  - 任一 stage 命中 `PYTHONINSPECT` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-python-inspect-env-check` 显式关闭该门禁

#### TP-E13-38 Release switch PYTHONWARNINGS 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `PYTHONWARNINGS` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 warning filter 注入掩盖发布期间的告警契约漂移。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `PYTHONWARNINGS=*`
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `PYTHONWARNINGS=*`
  - 任一 stage 命中 `PYTHONWARNINGS` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-python-warnings-env-check` 显式关闭该门禁

#### TP-E13-39 Release switch 未登记 PYTHON* 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate 未登记 `PYTHON*` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过未纳入显式门禁名单的 `PYTHON*` 赋值漂移运行时契约。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现未知 `PYTHON*` 赋值（已登记门禁键除外）
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现未知 `PYTHON*` 赋值（已登记门禁键除外）
  - 任一 stage 命中未知 `PYTHON*` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-python-env-wildcard-check` 显式关闭该门禁

#### TP-E13-40 Release switch PATH 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `PATH` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 `PATH=*` 赋值重定向解释器解析路径，避免命中非预期 Python runtime 导致伪 `GO`。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `PATH=*`
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `PATH=*`
  - 任一 stage 命中 `PATH` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-path-env-check` 显式关闭该门禁

#### TP-E13-41 Release switch LD_PRELOAD 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `LD_PRELOAD` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 `LD_PRELOAD=*` 注入动态加载器 hook，避免运行时被旁路导致伪 `GO`。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `LD_PRELOAD=*`
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `LD_PRELOAD=*`
  - 任一 stage 命中 `LD_PRELOAD` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-ld-preload-env-check` 显式关闭该门禁

#### TP-E13-42 Release switch LD_LIBRARY_PATH 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `LD_LIBRARY_PATH` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 `LD_LIBRARY_PATH=*` 重定向动态链接器查找路径，避免运行时库解析漂移导致伪 `GO`。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `LD_LIBRARY_PATH=*`
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `LD_LIBRARY_PATH=*`
  - 任一 stage 命中 `LD_LIBRARY_PATH` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-ld-library-path-env-check` 显式关闭该门禁

#### TP-E13-43 Release switch LD_AUDIT 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `LD_AUDIT` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 `LD_AUDIT=*` 注入动态链接器审计 hook，避免运行时旁路导致伪 `GO`。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `LD_AUDIT=*`
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `LD_AUDIT=*`
  - 任一 stage 命中 `LD_AUDIT` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-ld-audit-env-check` 显式关闭该门禁

#### TP-E13-44 Release switch 未登记 LD_* 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate 未登记 `LD_*` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过未纳入显式门禁名单的 `LD_*` 赋值漂移动态链接器运行时契约。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现未知 `LD_*` 赋值（已登记门禁键除外）
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现未知 `LD_*` 赋值（已登记门禁键除外）
  - 任一 stage 命中未知 `LD_*` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-ld-env-wildcard-check` 显式关闭该门禁

#### TP-E13-45 Release switch GLIBC_TUNABLES 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `GLIBC_TUNABLES` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 `GLIBC_TUNABLES=*` 漂移 glibc 动态链接器 tunables 契约。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `GLIBC_TUNABLES=*`
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `GLIBC_TUNABLES=*`
  - 任一 stage 命中 `GLIBC_TUNABLES` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-glibc-tunables-env-check` 显式关闭该门禁

#### TP-E13-46 Release switch 未登记 GLIBC_* 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate 未登记 `GLIBC_*` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过未纳入显式门禁名单的 `GLIBC_*` 赋值漂移 glibc 运行时契约。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现未知 `GLIBC_*` 赋值（已登记门禁键除外）
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现未知 `GLIBC_*` 赋值（已登记门禁键除外）
  - 任一 stage 命中未知 `GLIBC_*` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-glibc-env-wildcard-check` 显式关闭该门禁

#### TP-E13-47 Release switch 未登记 MALLOC_* 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate 未登记 `MALLOC_*` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过未纳入显式门禁名单的 `MALLOC_*` 赋值漂移内存分配器运行时契约。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现未知 `MALLOC_*` 赋值（已登记门禁键除外）
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现未知 `MALLOC_*` 赋值（已登记门禁键除外）
  - 任一 stage 命中未知 `MALLOC_*` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-malloc-env-wildcard-check` 显式关闭该门禁

#### TP-E13-48 Release switch MALLOC_TRACE 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `MALLOC_TRACE` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 `MALLOC_TRACE=*` 注入分配器追踪输出与侧信道痕迹。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `MALLOC_TRACE=*`
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `MALLOC_TRACE=*`
  - 任一 stage 命中 `MALLOC_TRACE` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-malloc-trace-env-check` 显式关闭该门禁

#### TP-E13-49 Release switch MALLOC_CHECK_ 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `MALLOC_CHECK_` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 `MALLOC_CHECK_=*` 改写 glibc 分配器检查策略。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `MALLOC_CHECK_=*`
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `MALLOC_CHECK_=*`
  - 任一 stage 命中 `MALLOC_CHECK_` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-malloc-check-env-check` 显式关闭该门禁

#### TP-E13-50 Release switch MALLOC_PERTURB_ 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `MALLOC_PERTURB_` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 `MALLOC_PERTURB_=*` 注入内存扰动策略，避免运行时行为与基线判定出现漂移。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `MALLOC_PERTURB_=*`
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `MALLOC_PERTURB_=*`
  - 任一 stage 命中 `MALLOC_PERTURB_` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-malloc-perturb-env-check` 显式关闭该门禁

#### TP-E13-51 Release switch MALLOC_ARENA_MAX 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `MALLOC_ARENA_MAX` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 `MALLOC_ARENA_MAX=*` 改写 allocator arena 并发扩展策略，避免运行时资源行为与基线判定漂移。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `MALLOC_ARENA_MAX=*`
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `MALLOC_ARENA_MAX=*`
  - 任一 stage 命中 `MALLOC_ARENA_MAX` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-malloc-arena-max-env-check` 显式关闭该门禁

#### TP-E13-52 Release switch MALLOC_MMAP_THRESHOLD_ 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `MALLOC_MMAP_THRESHOLD_` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 `MALLOC_MMAP_THRESHOLD_=*` 改写 allocator mmap 阈值策略，避免运行时内存分配路径与基线判定漂移。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `MALLOC_MMAP_THRESHOLD_=*`
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `MALLOC_MMAP_THRESHOLD_=*`
  - 任一 stage 命中 `MALLOC_MMAP_THRESHOLD_` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-malloc-mmap-threshold-env-check` 显式关闭该门禁

#### TP-E13-53 Release switch MALLOC_MMAP_MAX_ 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `MALLOC_MMAP_MAX_` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 `MALLOC_MMAP_MAX_=*` 改写 allocator mmap 数量阈值策略，避免运行时分配形态与基线判定漂移。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `MALLOC_MMAP_MAX_=*`
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `MALLOC_MMAP_MAX_=*`
  - 任一 stage 命中 `MALLOC_MMAP_MAX_` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-malloc-mmap-max-env-check` 显式关闭该门禁

#### TP-E13-54 Release switch MALLOC_TOP_PAD_ 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `MALLOC_TOP_PAD_` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 `MALLOC_TOP_PAD_=*` 改写 allocator top chunk padding 策略，避免运行时堆增长行为与基线判定漂移。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `MALLOC_TOP_PAD_=*`
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `MALLOC_TOP_PAD_=*`
  - 任一 stage 命中 `MALLOC_TOP_PAD_` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-malloc-top-pad-env-check` 显式关闭该门禁

#### TP-E13-55 Release switch MALLOC_TRIM_THRESHOLD_ 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `MALLOC_TRIM_THRESHOLD_` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 `MALLOC_TRIM_THRESHOLD_=*` 改写 allocator trim threshold 策略，避免运行时内存回收行为与基线判定漂移。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `MALLOC_TRIM_THRESHOLD_=*`
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `MALLOC_TRIM_THRESHOLD_=*`
  - 任一 stage 命中 `MALLOC_TRIM_THRESHOLD_` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-malloc-trim-threshold-env-check` 显式关闭该门禁

#### TP-E13-56 Release switch MALLOC_ARENA_TEST 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `MALLOC_ARENA_TEST` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 `MALLOC_ARENA_TEST=*` 改写 allocator arena probing 策略，避免运行时 arena 扩展行为与基线判定漂移。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `MALLOC_ARENA_TEST=*`
  - 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `MALLOC_ARENA_TEST=*`
  - 任一 stage 命中 `MALLOC_ARENA_TEST` 赋值时，判定强制 `HOLD`
  - 支持 `--skip-release-gate-malloc-arena-test-env-check` 显式关闭该门禁

#### TP-E13-57 Release switch MALLOC_PER_THREAD 环境变量门禁

- 目标：在 release switch 判定中加入 release-gate `MALLOC_PER_THREAD` 环境变量守门，禁止 stage launcher 与 `--python` 传递链通过 `MALLOC_PER_THREAD=*` 改写 allocator per-thread arena pooling 策略，避免运行时线程内存分配行为与基线判定漂移。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 默认校验 release-gate `beta_gate/ga_gate/roadmap_gate` 命令在 linux-suite script token 前不允许出现 `MALLOC_PER_THREAD=*`
- 默认校验 stage `--python` 传递值解析后的 token 中不允许出现 `MALLOC_PER_THREAD=*`
- 任一 stage 命中 `MALLOC_PER_THREAD` 赋值时，判定强制 `HOLD`
- 支持 `--skip-release-gate-malloc-per-thread-env-check` 显式关闭该门禁

#### TP-E13-58 Release switch 决策 JSON 批量测算视图

- 目标：在保持现有 `decision/evidence_summary/gates` 兼容前提下，新增 `bulk_strategy_view` 结构化视图，避免每次新增 gate 都要求下游测算器改 schema，支持海量批处理的稳定解析。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 新增 `bulk_strategy_view`，包含固定骨架：`schema_version/decision/gate_count/pass_count/hold_count/gate_status_bitmap/gate_status_index/gate_rows/check_enablement/evidence_status_counts/evidence_freshness_counts`
  - `bulk_strategy_view` 中 gate 汇总与原始 `gates` 一致（计数、通过/阻断结果、门禁名映射）
  - `bulk_strategy_view` 同时适用于 `GO` 与 `HOLD` 决策样本
  - 保持旧字段不删除，避免破坏既有消费者

#### TP-E13-59 Release switch 批量测算域聚合签名

- 目标：在 `bulk_strategy_view` 上增加 domain 级聚合与签名字段，支持海量测算直接按域统计、按 hold 签名分桶，而无需二次遍历长 gate 明细。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - `bulk_strategy_view` 升级为 `schema_version=release_switch_bulk_strategy.v2`
  - 新增 `decision_code/hold_signature/pass_gate_indices/hold_gate_indices/gate_domain_index/domain_rollup`
  - `domain_rollup` 需给出每个 domain 的 `gate_count/pass_count/hold_count/pass_ratio`
  - `GO` 样本 `hold_signature` 固定为 `GO`；`HOLD` 样本 `hold_signature` 必须包含关键阻断 gate 名

#### TP-E13-60 Release switch 批量测算签名哈希固化

- 目标：在 `bulk_strategy_view` 上补齐固定宽度哈希签名字段，支撑海量聚合作业在不依赖长字符串索引的情况下完成分桶与去重，同时保持 `decision/gates/evidence_summary` 兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `hold_signature_sha256`
  - 决策 JSON 的 `bulk_strategy_view` 新增 `strategy_signature_sha256`
  - 两个签名字段均为 64 位十六进制字符串，且可由稳定规则重算
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-61 Release switch 批量测算域聚合哈希固化

- 目标：在 `bulk_strategy_view` 上补齐 domain 聚合轮廓的固定宽度签名字段，支撑海量策略作业按域聚合画像做快速索引与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `domain_rollup_sha256`
  - `domain_rollup_sha256` 必须由稳定 canonical payload 重算：`decision/domain_rollup/gate_domain_index`
  - `domain_rollup_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-62 Release switch 批量测算证据轮廓哈希固化

- 目标：在 `bulk_strategy_view` 上补齐 evidence 轮廓的固定宽度签名字段，支撑海量策略作业按证据状态画像快速分桶、去重与回放，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `evidence_profile_sha256`
  - `evidence_profile_sha256` 必须由稳定 canonical payload 重算：`decision/evidence_file_count/evidence_status_counts/evidence_freshness_counts`
  - `evidence_profile_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-63 Release switch 批量测算门阵索引哈希固化

- 目标：在 `bulk_strategy_view` 上补齐 gate 状态索引轮廓的固定宽度签名字段，支撑海量策略作业按门阵状态向量快速分桶、去重与回放，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `gate_status_index_sha256`
  - `gate_status_index_sha256` 必须由稳定 canonical payload 重算：`decision/gate_names/gate_status_bitmap/gate_status_index`
  - `gate_status_index_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-64 Release switch 批量测算组合轮廓哈希固化

- 目标：在 `bulk_strategy_view` 上补齐跨维度组合轮廓的固定宽度签名字段，把现有多维哈希收敛为单一主索引，支撑海量策略作业快速分桶、去重与回放，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `composite_profile_sha256`
  - `composite_profile_sha256` 必须由稳定 canonical payload 重算：`decision/hold_signature_sha256/strategy_signature_sha256/domain_rollup_sha256/evidence_profile_sha256/gate_status_index_sha256`
  - `composite_profile_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-65 Release switch 批量测算策略包络哈希固化

- 目标：在 `bulk_strategy_view` 上补齐策略包络级固定宽度签名字段，将决策码、门阵计数、证据计数与既有多维哈希绑定为统一索引，支撑跨批次快速对账、分桶与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `strategy_envelope_sha256`
  - `strategy_envelope_sha256` 必须由稳定 canonical payload 重算：`decision/decision_code/gate_count/pass_count/hold_count/evidence_file_count/hold_signature_sha256/strategy_signature_sha256/domain_rollup_sha256/evidence_profile_sha256/gate_status_index_sha256/composite_profile_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `strategy_envelope_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-66 Release switch 批量测算合同签名哈希固化

- 目标：在 `bulk_strategy_view` 上补齐合同级固定宽度签名字段，将 schema 版本、门阵域索引、门禁启停键与策略包络哈希绑定为统一合同签名，支撑跨批次合同漂移检测与快速对账，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `contract_signature_sha256`
  - `contract_signature_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/gate_names/gate_domain_index/check_enablement.enabled_keys/check_enablement.disabled_keys/strategy_envelope_sha256`
  - `contract_signature_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-67 Release switch 批量测算合同包络哈希固化

- 目标：在 `bulk_strategy_view` 上补齐合同包络级固定宽度签名字段，将合同签名与批次门阵/证据计数绑定为统一包络索引，支撑跨批次合同+姿态快速对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `contract_envelope_sha256`
  - `contract_envelope_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/gate_count/pass_count/hold_count/evidence_file_count/contract_signature_sha256/strategy_envelope_sha256/composite_profile_sha256`
  - `contract_envelope_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-68 Release switch 批量测算发布指纹哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布级固定宽度指纹字段，将合同签名、合同包络、姿态轮廓与门禁启停键绑定为统一发布指纹，支撑跨批次一键发布对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_fingerprint_sha256`
  - `release_fingerprint_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/gate_count/pass_count/hold_count/evidence_file_count/hold_signature_sha256/strategy_envelope_sha256/contract_signature_sha256/contract_envelope_sha256/composite_profile_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_fingerprint_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-69 Release switch 批量测算发布清单哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布清单级固定宽度哈希字段，将发布指纹与门阵状态、域索引、证据轮廓绑定为统一发布清单索引，支撑跨批次发布面快速回放、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_manifest_sha256`
  - `release_manifest_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/gate_names/gate_status_bitmap/gate_domain_index/domain_rollup_sha256/evidence_profile_sha256/release_fingerprint_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_manifest_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-70 Release switch 批量测算发布根签名哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布根级固定宽度哈希字段，将发布清单哈希与核心姿态签名绑定统一根索引，支撑跨批次快速对账、去重与回放，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_root_sha256`
  - `release_root_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/gate_count/pass_count/hold_count/evidence_file_count/hold_signature_sha256/strategy_signature_sha256/domain_rollup_sha256/evidence_profile_sha256/gate_status_index_sha256/composite_profile_sha256/strategy_envelope_sha256/contract_signature_sha256/contract_envelope_sha256/release_fingerprint_sha256/release_manifest_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_root_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-71 Release switch 批量测算发布见证哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布见证级固定宽度哈希字段，将发布根签名与发布清单、发布指纹及核心姿态索引绑定为统一见证键，支撑跨批次发布产物快速验签、对账与追踪，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_attestation_sha256`
  - `release_attestation_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/hold_signature_sha256/strategy_signature_sha256/gate_status_bitmap/gate_status_index_sha256/domain_rollup_sha256/evidence_profile_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_attestation_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-72 Release switch 批量测算发布裁决哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布裁决级固定宽度哈希字段，将发布见证、发布根、发布清单、发布指纹与合同姿态包络绑定为统一裁决键，支撑跨批次一键发布对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_verdict_sha256`
  - `release_verdict_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/strategy_envelope_sha256/contract_envelope_sha256/composite_profile_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_verdict_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-73 Release switch 批量测算发布谱系哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布谱系级固定宽度哈希字段，将发布裁决、发布见证、发布根签名、发布清单与核心姿态签名索引绑定为统一谱系键，支撑跨批次发布链路回放、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_lineage_sha256`
  - `release_lineage_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/hold_signature_sha256/strategy_signature_sha256/domain_rollup_sha256/evidence_profile_sha256/gate_status_index_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_lineage_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-74 Release switch 批量测算发布胶囊哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布胶囊级固定宽度哈希字段，将发布谱系签名与核心判定计数收敛为紧凑统一索引，支撑跨批次快速对账、分桶与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_capsule_sha256`
  - `release_capsule_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/gate_count/pass_count/hold_count/evidence_file_count/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_capsule_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-75 Release switch 批量测算发布锚点哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布锚点级固定宽度哈希字段，将发布胶囊签名与发布清单/发布指纹以及合同策略包络收敛为统一锚点索引，支撑跨批次极速对账、分桶与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_anchor_sha256`
  - `release_anchor_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_anchor_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-76 Release switch 批量测算发布信标哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布信标级固定宽度哈希字段，将发布锚点与门阵索引/组合轮廓及合同策略包络收敛为统一信标索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_beacon_sha256`
  - `release_beacon_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_beacon_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-77 Release switch 批量测算发布星图哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布星图级固定宽度哈希字段，将发布信标与谱系姿态签名收敛为统一星图索引，支撑跨批次极速路由、对账与回放，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_constellation_sha256`
  - `release_constellation_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_constellation_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-78 Release switch 批量测算发布星系哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布星系级固定宽度哈希字段，将发布星图与双签姿态收敛为统一星系索引，支撑跨批次极速路由、对账与回放，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_galaxy_sha256`
  - `release_galaxy_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_galaxy_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-79 Release switch 批量测算发布宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布宇宙级固定宽度哈希字段，将发布星系哈希与多维姿态签名收敛为统一宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_universe_sha256`
  - `release_universe_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_universe_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-80 Release switch 批量测算发布多元宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布多元宇宙级固定宽度哈希字段，将发布宇宙哈希与多维姿态签名收敛为统一多元宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_multiverse_sha256`
  - `release_multiverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_multiverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-81 Release switch 批量测算发布超宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布超宇宙级固定宽度哈希字段，将发布多元宇宙哈希与多维姿态签名收敛为统一超宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_omniverse_sha256`
  - `release_omniverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_omniverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-82 Release switch 批量测算发布极宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布极宇宙级固定宽度哈希字段，将发布超宇宙哈希与多维姿态签名收敛为统一极宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_hyperverse_sha256`
  - `release_hyperverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_hyperverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-83 Release switch 批量测算发布巨宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布巨宇宙级固定宽度哈希字段，将发布极宇宙哈希与多维姿态签名收敛为统一巨宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_megaverse_sha256`
  - `release_megaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_megaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-84 Release switch 批量测算发布十亿宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布十亿宇宙级固定宽度哈希字段，将发布巨宇宙哈希与多维姿态签名收敛为统一十亿宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_gigaverse_sha256`
  - `release_gigaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_gigaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-85 Release switch 批量测算发布万亿宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布万亿宇宙级固定宽度哈希字段，将发布十亿宇宙哈希与多维姿态签名收敛为统一万亿宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_teraverse_sha256`
  - `release_teraverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_teraverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-86 Release switch 批量测算发布千万亿宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布千万亿宇宙级固定宽度哈希字段，将发布万亿宇宙哈希与多维姿态签名收敛为统一千万亿宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_petaverse_sha256`
  - `release_petaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_petaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-87 Release switch 批量测算发布百京宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布百京宇宙级固定宽度哈希字段，将发布千万亿宇宙哈希与多维姿态签名收敛为统一百京宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_exaverse_sha256`
  - `release_exaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_exaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-88 Release switch 批量测算发布十垓宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布十垓宇宙级固定宽度哈希字段，将发布百京宇宙哈希与多维姿态签名收敛为统一十垓宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_zettaverse_sha256`
  - `release_zettaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_zettaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-89 Release switch 批量测算发布尧它宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布尧它宇宙级固定宽度哈希字段，将发布十垓宇宙哈希与多维姿态签名收敛为统一尧它宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_yottaverse_sha256`
  - `release_yottaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_yottaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-90 Release switch 批量测算发布罗纳宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布罗纳宇宙级固定宽度哈希字段，将发布秭宇宙哈希与多维姿态签名收敛为统一罗纳宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_ronnaverse_sha256`
  - `release_ronnaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_ronnaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-91 Release switch 批量测算发布昆塔宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布昆塔宇宙级固定宽度哈希字段，将发布罗纳宇宙哈希与多维姿态签名收敛为统一昆塔宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_quettaverse_sha256`
  - `release_quettaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_quettaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-92 Release switch 批量测算发布极巅宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布极巅宇宙级固定宽度哈希字段，将发布昆塔宇宙哈希与多维姿态签名收敛为统一极巅宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_apexverse_sha256`
  - `release_apexverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_apexverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-93 Release switch 批量测算发布终极宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布终极宇宙级固定宽度哈希字段，将发布极巅宇宙哈希与多维姿态签名收敛为统一终极宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_ultimaverse_sha256`
  - `release_ultimaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_ultimaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-94 Release switch 批量测算发布超越宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布超越宇宙级固定宽度哈希字段，将发布终极宇宙哈希与多维姿态签名收敛为统一超越宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_transcendaverse_sha256`
  - `release_transcendaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_transcendaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-95 Release switch 批量测算发布无限宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布无限宇宙级固定宽度哈希字段，将发布超越宇宙哈希与多维姿态签名收敛为统一无限宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_infinitaverse_sha256`
  - `release_infinitaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_infinitaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-96 Release switch 批量测算发布永恒宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布永恒宇宙级固定宽度哈希字段，将发布无限宇宙哈希与多维姿态签名收敛为统一永恒宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_eternaverse_sha256`
  - `release_eternaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_eternaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-97 Release switch 批量测算发布永序宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布永序宇宙级固定宽度哈希字段，将发布永恒宇宙哈希与多维姿态签名收敛为统一永序宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_timelessverse_sha256`
  - `release_timelessverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_timelessverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-98 Release switch 批量测算发布纪元宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布纪元宇宙级固定宽度哈希字段，将发布永序宇宙哈希与多维姿态签名收敛为统一纪元宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_aeonverse_sha256`
  - `release_aeonverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_aeonverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-99 Release switch 批量测算发布世代宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布世代宇宙级固定宽度哈希字段，将发布纪元宇宙哈希与多维姿态签名收敛为统一世代宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_epochverse_sha256`
  - `release_epochverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_epochverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-100 Release switch 批量测算发布元宇宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布元宇宇宙级固定宽度哈希字段，将发布世代宇宙哈希与多维姿态签名收敛为统一元宇宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_eraverse_sha256`
- `release_eraverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
- `release_eraverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
- 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-101 Release switch 批量测算发布超元宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布超元宇宙级固定宽度哈希字段，将发布元宇宇宙哈希与多维姿态签名收敛为统一超元宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_metaverse_sha256`
  - `release_metaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_metaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-102 Release switch 批量测算发布平行宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布平行宇宙级固定宽度哈希字段，将发布超元宇宙哈希与多维姿态签名收敛为统一平行宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_paraverse_sha256`
  - `release_paraverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_paraverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-103 Release switch 批量测算发布多维宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布多维宇宙级固定宽度哈希字段，将发布平行宇宙哈希与多维姿态签名收敛为统一多维宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_polyverse_sha256`
  - `release_polyverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_polyverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-104 Release switch 批量测算发布泛宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布泛宇宙级固定宽度哈希字段，将发布多维宇宙哈希与多维姿态签名收敛为统一泛宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_panverse_sha256`
  - `release_panverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_panverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-105 Release switch 批量测算发布全息宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布全息宇宙级固定宽度哈希字段，将发布泛宇宙哈希与多维姿态签名收敛为统一全息宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_holoverse_sha256`
  - `release_holoverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_holoverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-106 Release switch 批量测算发布新宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布新宇宙级固定宽度哈希字段，将发布全息宇宙哈希与多维姿态签名收敛为统一新宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_neoverse_sha256`
  - `release_neoverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_neoverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-107 Release switch 批量测算发布新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布新星宇宙级固定宽度哈希字段，将发布新宇宙哈希与多维姿态签名收敛为统一新星宇宙索引，支撑跨批次极速路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_novaverse_sha256`
  - `release_novaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_novaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-108 Release switch 批量测算发布超新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布超新星宇宙级固定宽度哈希字段，将发布新星宇宙哈希与前序发布签名收敛为统一超新星宇宙索引，支撑更高一层跨批次路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/CURRENT_STATUS.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_supernovaverse_sha256`
  - `release_supernovaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_supernovaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-109 Release switch 批量测算发布超极新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布超极新星宇宙级固定宽度哈希字段，将发布超新星宇宙哈希与前序发布签名收敛为统一超极新星宇宙索引，支撑更高一层跨批次路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/CURRENT_STATUS.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_hypernovaverse_sha256`
  - `release_hypernovaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_hypernovaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-110 Release switch 批量测算发布极耀新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布极耀新星宇宙级固定宽度哈希字段，将发布超极新星宇宙哈希与前序发布签名收敛为统一极耀新星宇宙索引，支撑更高一层跨批次路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/CURRENT_STATUS.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_ultranovaverse_sha256`
  - `release_ultranovaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_ultranovaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-111 Release switch 批量测算发布终耀新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布终耀新星宇宙级固定宽度哈希字段，将发布极耀新星宇宙哈希与前序发布签名收敛为统一终耀新星宇宙索引，支撑更高一层跨批次路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/CURRENT_STATUS.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_omeganovaverse_sha256`
  - `release_omeganovaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_omeganovaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-112 Release switch 批量测算发布始耀新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布始耀新星宇宙级固定宽度哈希字段，将发布终耀新星宇宙哈希与前序发布签名收敛为统一始耀新星宇宙索引，支撑更高一层跨批次路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/CURRENT_STATUS.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_alphanovaverse_sha256`
  - `release_alphanovaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_alphanovaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-113 Release switch 批量测算发布次耀新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布次耀新星宇宙级固定宽度哈希字段，将发布始耀新星宇宙哈希与前序发布签名收敛为统一次耀新星宇宙索引，支撑更高一层跨批次路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/CURRENT_STATUS.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_betanovaverse_sha256`
  - `release_betanovaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_betanovaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-114 Release switch 批量测算发布叁耀新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布叁耀新星宇宙级固定宽度哈希字段，将发布次耀新星宇宙哈希与前序发布签名收敛为统一叁耀新星宇宙索引，支撑更高一层跨批次路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/CURRENT_STATUS.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_gammanovaverse_sha256`
  - `release_gammanovaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_gammanovaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-115 Release switch 批量测算发布肆耀新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布肆耀新星宇宙级固定宽度哈希字段，将发布叁耀新星宇宙哈希与前序发布签名收敛为统一肆耀新星宇宙索引，支撑更高一层跨批次路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/CURRENT_STATUS.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_deltanovaverse_sha256`
  - `release_deltanovaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_gammanovaverse_sha256/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_deltanovaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-116 Release switch 批量测算发布伍耀新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布伍耀新星宇宙级固定宽度哈希字段，将发布肆耀新星宇宙哈希与前序发布签名收敛为统一伍耀新星宇宙索引，支撑更高一层跨批次路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/CURRENT_STATUS.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_epsilonnovaverse_sha256`
  - `release_epsilonnovaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_deltanovaverse_sha256/release_gammanovaverse_sha256/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_epsilonnovaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-117 Release switch 批量测算发布陆耀新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布陆耀新星宇宙级固定宽度哈希字段，将发布伍耀新星宇宙哈希与前序发布签名收敛为统一陆耀新星宇宙索引，支撑更高一层跨批次路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/CURRENT_STATUS.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_zetanovaverse_sha256`
  - `release_zetanovaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_epsilonnovaverse_sha256/release_deltanovaverse_sha256/release_gammanovaverse_sha256/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_zetanovaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-118 Release switch 批量测算发布柒耀新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布柒耀新星宇宙级固定宽度哈希字段，将发布陆耀新星宇宙哈希与前序发布签名收敛为统一柒耀新星宇宙索引，支撑更高一层跨批次路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/CURRENT_STATUS.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_etanovaverse_sha256`
  - `release_etanovaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_zetanovaverse_sha256/release_epsilonnovaverse_sha256/release_deltanovaverse_sha256/release_gammanovaverse_sha256/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_etanovaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-119 Release switch 批量测算发布捌耀新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布捌耀新星宇宙级固定宽度哈希字段，将发布柒耀新星宇宙哈希与前序发布签名收敛为统一捌耀新星宇宙索引，支撑更高一层跨批次路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/CURRENT_STATUS.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_thetanovaverse_sha256`
  - `release_thetanovaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_etanovaverse_sha256/release_zetanovaverse_sha256/release_epsilonnovaverse_sha256/release_deltanovaverse_sha256/release_gammanovaverse_sha256/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_thetanovaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-120 Release switch 批量测算发布玖耀新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布玖耀新星宇宙级固定宽度哈希字段，将发布捌耀新星宇宙哈希与前序发布签名收敛为统一玖耀新星宇宙索引，支撑更高一层跨批次路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/CURRENT_STATUS.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_iotanovaverse_sha256`
  - `release_iotanovaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_thetanovaverse_sha256/release_etanovaverse_sha256/release_zetanovaverse_sha256/release_epsilonnovaverse_sha256/release_deltanovaverse_sha256/release_gammanovaverse_sha256/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_iotanovaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-121 Release switch 批量测算发布拾耀新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布拾耀新星宇宙级固定宽度哈希字段，将发布玖耀新星宇宙哈希与前序发布签名收敛为统一拾耀新星宇宙索引，支撑更高一层跨批次路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/CURRENT_STATUS.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_kappanovaverse_sha256`
  - `release_kappanovaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_iotanovaverse_sha256/release_thetanovaverse_sha256/release_etanovaverse_sha256/release_zetanovaverse_sha256/release_epsilonnovaverse_sha256/release_deltanovaverse_sha256/release_gammanovaverse_sha256/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_kappanovaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-122 Release switch 批量测算发布拾壹耀新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布拾壹耀新星宇宙级固定宽度哈希字段，将发布拾耀新星宇宙哈希与前序发布签名收敛为统一拾壹耀新星宇宙索引，支撑更高一层跨批次路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/CURRENT_STATUS.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_lambdanovaverse_sha256`
  - `release_lambdanovaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_kappanovaverse_sha256/release_iotanovaverse_sha256/release_thetanovaverse_sha256/release_etanovaverse_sha256/release_zetanovaverse_sha256/release_epsilonnovaverse_sha256/release_deltanovaverse_sha256/release_gammanovaverse_sha256/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_lambdanovaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-123 Release switch 批量测算发布拾贰耀新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布拾贰耀新星宇宙级固定宽度哈希字段，将发布拾壹耀新星宇宙哈希与前序发布签名收敛为统一拾贰耀新星宇宙索引，支撑更高一层跨批次路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/CURRENT_STATUS.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_munovaverse_sha256`
  - `release_munovaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_lambdanovaverse_sha256/release_kappanovaverse_sha256/release_iotanovaverse_sha256/release_thetanovaverse_sha256/release_etanovaverse_sha256/release_zetanovaverse_sha256/release_epsilonnovaverse_sha256/release_deltanovaverse_sha256/release_gammanovaverse_sha256/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_munovaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-124 Release switch 批量测算发布拾叁耀新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布拾叁耀新星宇宙级固定宽度哈希字段，将发布拾贰耀新星宇宙哈希与前序发布签名收敛为统一拾叁耀新星宇宙索引，支撑更高一层跨批次路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/CURRENT_STATUS.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_nunovaverse_sha256`
  - `release_nunovaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_munovaverse_sha256/release_lambdanovaverse_sha256/release_kappanovaverse_sha256/release_iotanovaverse_sha256/release_thetanovaverse_sha256/release_etanovaverse_sha256/release_zetanovaverse_sha256/release_epsilonnovaverse_sha256/release_deltanovaverse_sha256/release_gammanovaverse_sha256/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_nunovaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-125 Release switch 批量测算发布拾肆耀新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布拾肆耀新星宇宙级固定宽度哈希字段，将发布拾叁耀新星宇宙哈希与前序发布签名收敛为统一拾肆耀新星宇宙索引，支撑更高一层跨批次路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/CURRENT_STATUS.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_xinovaverse_sha256`
  - `release_xinovaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_nunovaverse_sha256/release_munovaverse_sha256/release_lambdanovaverse_sha256/release_kappanovaverse_sha256/release_iotanovaverse_sha256/release_thetanovaverse_sha256/release_etanovaverse_sha256/release_zetanovaverse_sha256/release_epsilonnovaverse_sha256/release_deltanovaverse_sha256/release_gammanovaverse_sha256/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_xinovaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-126 Release switch 批量测算发布拾伍耀新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布拾伍耀新星宇宙级固定宽度哈希字段，将发布拾肆耀新星宇宙哈希与前序发布签名收敛为统一拾伍耀新星宇宙索引，支撑更高一层跨批次路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/CURRENT_STATUS.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_omicronovaverse_sha256`
  - `release_omicronovaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_xinovaverse_sha256/release_nunovaverse_sha256/release_munovaverse_sha256/release_lambdanovaverse_sha256/release_kappanovaverse_sha256/release_iotanovaverse_sha256/release_thetanovaverse_sha256/release_etanovaverse_sha256/release_zetanovaverse_sha256/release_epsilonnovaverse_sha256/release_deltanovaverse_sha256/release_gammanovaverse_sha256/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_omicronovaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-127 Release switch 批量测算发布拾陆耀新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布拾陆耀新星宇宙级固定宽度哈希字段，将发布拾伍耀新星宇宙哈希与前序发布签名收敛为统一拾陆耀新星宇宙索引，支撑更高一层跨批次路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/CURRENT_STATUS.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_pinovaverse_sha256`
  - `release_pinovaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_omicronovaverse_sha256/release_xinovaverse_sha256/release_nunovaverse_sha256/release_munovaverse_sha256/release_lambdanovaverse_sha256/release_kappanovaverse_sha256/release_iotanovaverse_sha256/release_thetanovaverse_sha256/release_etanovaverse_sha256/release_zetanovaverse_sha256/release_epsilonnovaverse_sha256/release_deltanovaverse_sha256/release_gammanovaverse_sha256/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_pinovaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-128 Release switch 批量测算发布拾柒耀新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布拾柒耀新星宇宙级固定宽度哈希字段，将发布拾陆耀新星宇宙哈希与前序发布签名收敛为统一拾柒耀新星宇宙索引，支撑更高一层跨批次路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/CURRENT_STATUS.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_rhonovaverse_sha256`
  - `release_rhonovaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_pinovaverse_sha256/release_omicronovaverse_sha256/release_xinovaverse_sha256/release_nunovaverse_sha256/release_munovaverse_sha256/release_lambdanovaverse_sha256/release_kappanovaverse_sha256/release_iotanovaverse_sha256/release_thetanovaverse_sha256/release_etanovaverse_sha256/release_zetanovaverse_sha256/release_epsilonnovaverse_sha256/release_deltanovaverse_sha256/release_gammanovaverse_sha256/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_rhonovaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-129 Release switch 批量测算发布拾捌耀新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布拾捌耀新星宇宙级固定宽度哈希字段，将发布拾柒耀新星宇宙哈希与前序发布签名收敛为统一拾捌耀新星宇宙索引，支撑更高一层跨批次路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/CURRENT_STATUS.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_sigmanovaverse_sha256`
  - `release_sigmanovaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_rhonovaverse_sha256/release_pinovaverse_sha256/release_omicronovaverse_sha256/release_xinovaverse_sha256/release_nunovaverse_sha256/release_munovaverse_sha256/release_lambdanovaverse_sha256/release_kappanovaverse_sha256/release_iotanovaverse_sha256/release_thetanovaverse_sha256/release_etanovaverse_sha256/release_zetanovaverse_sha256/release_epsilonnovaverse_sha256/release_deltanovaverse_sha256/release_gammanovaverse_sha256/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_sigmanovaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-130 Release switch 批量测算发布拾玖耀新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布拾玖耀新星宇宙级固定宽度哈希字段，将发布拾捌耀新星宇宙哈希与前序发布签名收敛为统一拾玖耀新星宇宙索引，支撑更高一层跨批次路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/CURRENT_STATUS.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_taunovaverse_sha256`
  - `release_taunovaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_sigmanovaverse_sha256/release_rhonovaverse_sha256/release_pinovaverse_sha256/release_omicronovaverse_sha256/release_xinovaverse_sha256/release_nunovaverse_sha256/release_munovaverse_sha256/release_lambdanovaverse_sha256/release_kappanovaverse_sha256/release_iotanovaverse_sha256/release_thetanovaverse_sha256/release_etanovaverse_sha256/release_zetanovaverse_sha256/release_epsilonnovaverse_sha256/release_deltanovaverse_sha256/release_gammanovaverse_sha256/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_taunovaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

#### TP-E13-131 Release switch 批量测算发布贰拾耀新星宇宙哈希固化

- 目标：在 `bulk_strategy_view` 上补齐发布贰拾耀新星宇宙级固定宽度哈希字段，将发布拾玖耀新星宇宙哈希与前序发布签名收敛为统一贰拾耀新星宇宙索引，支撑更高一层跨批次路由、对账与去重，同时保持既有判定字段兼容不变。
- 主要文件：
  - `scripts/run_release_switch_validation.py`
  - `tests/test_release_switch_validation_script.py`
  - `scripts/run_tp_tests.py`
  - `docs/current/operations/testing.md`
  - `docs/current/status/CURRENT_STATUS.md`
  - `docs/current/status/baselines/README.md`
- 验收：
  - 决策 JSON 的 `bulk_strategy_view` 新增 `release_upsilonnovaverse_sha256`
  - `release_upsilonnovaverse_sha256` 必须由稳定 canonical payload 重算：`schema_version/decision/decision_code/release_taunovaverse_sha256/release_sigmanovaverse_sha256/release_rhonovaverse_sha256/release_pinovaverse_sha256/release_omicronovaverse_sha256/release_xinovaverse_sha256/release_nunovaverse_sha256/release_munovaverse_sha256/release_lambdanovaverse_sha256/release_kappanovaverse_sha256/release_iotanovaverse_sha256/release_thetanovaverse_sha256/release_etanovaverse_sha256/release_zetanovaverse_sha256/release_epsilonnovaverse_sha256/release_deltanovaverse_sha256/release_gammanovaverse_sha256/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`
  - `release_upsilonnovaverse_sha256` 在 `GO/HOLD` 样本下均为 64 位十六进制字符串
  - 保持 `schema_version=release_switch_bulk_strategy.v2` 与既有字段兼容，不删除旧键

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
- 保持 provider 作为能力层，不吞业务规则

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
