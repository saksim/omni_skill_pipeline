# Skill Distillation V2

## 判词

当前 `LoadedAsset -> EvidenceUnit[] -> Insight[] -> SkillDocument` 主链已经证明多模态入口可统一，但它更像一次性蒸馏器，而不是可持续生长的知识操作系统。`SKILL.md` 不应继续承担中间语义层职责，V2 需要把核心抽象上移为可追溯、可合并、可再渲染的 `SkillGraph`。

## 1. 现状评估

### 1.1 已有优势

- 已形成稳定的统一入口：文本、音频、图片、视频、表格/时序数据都能归一进入主链。
- 现有模块边界清晰：`adapters / providers / pipeline / repository / render` 已具备继续演化的基础。
- `tabular/time-series` 已经验证了一件关键事实：typed evidence 比纯文本 evidence 更适合作为长期知识中间层。
- 产物已具备基础可追溯性：`asset.json / evidence.json / insights.json / skill.json / SKILL.md / bundle.json` 能帮助回看一次蒸馏的输入与输出。

### 1.2 核心病灶

#### 病灶一：`SKILL.md` 被定义得过早

当前主链在 `InsightExtractor` 之后直接生成 `SkillDocument`，导致系统默认假设所有输入最终都应该落成一份静态技能文档。这个假设对以下场景并不成立：

- 一段会议音频更适合先蒸成决策、分歧、待办，而不是直接变成 skill。
- 一段监控时序更适合先形成 guardrail、诊断假设、异常 episode，而不是 procedure。
- 一批截图或视频更适合先形成 UI state transition、scene cluster、关键 frame event，再判断是否足以组合 skill。

#### 病灶二：`EvidenceUnit` 语义密度不足

当前 `EvidenceUnit` 以 `content: str` 为核心，虽然能兼容所有模态，但损失了大量对后续蒸馏极其重要的结构：

- 图片缺 bbox、region hierarchy、layout role
- 视频缺时间范围、scene cluster、frame lineage、subtitle alignment
- 表格缺列级 lineage、聚合口径、统计方法
- 时序缺 observation window、sampling interval、change point、baseline spec
- 文档缺 section hierarchy、table/code block 引用、paragraph lineage

一旦这些结构在入口阶段被压成平面字符串，后续所有 skill 组合都只能在低保真语义上作业。

#### 病灶三：`SkillDocument` 更像发布模板，不像知识本体

当前 `SkillDocument` 强调对人类可读，但对机器继续演化不够友好，至少缺少：

- `step -> evidence` 精确映射
- `step -> step` 依赖与前后顺序关系
- 可参数化变量槽位
- 正例 / 反例 / failure mode
- 可执行验证或自动化检查入口
- 版本 lineage 与 supersede 关系
- 失效条件与复验窗口

#### 病灶四：缺少“新证据如何进入旧知识”的生命周期

V1 更像单次生成：给一批输入，产出一份 skill。它缺少以下关键判定：

- 新证据是应该生成新 skill，还是更新旧 skill
- 两份 skill 是重复、补充、冲突，还是上下位关系
- 某份 skill 是否因为 UI 演进、系统升级、指标口径变更而失效
- 哪些 skill 需要复验、哪些 skill 可以自动发布

#### 病灶五：评审闭环未落地

系统状态机文档里已经写到 `REVIEW_PENDING -> PUBLISHED | REJECTED`，但当前真实落地只到 `PERSISTED`。这会直接造成：

- 输出质量无法形成稳定阈值
- 噪声 evidence 会直接污染下游知识资产
- 无法积累评审反馈，模型与规则都难以迭代

## 2. V2 设计目标

### 2.1 功能目标

- 支持多资产联合蒸馏，而不是只接受单一 asset。
- 支持先蒸语义原子，再按目标渲染 skill/playbook/checklist/decision tree。
- 支持 `new / revise / merge / supersede / reject` 生命周期决策。
- 支持 review queue、质量评分、人工反馈回流。
- 支持后续接入 PostgreSQL + pgvector，而不改核心领域模型。

### 2.2 非功能目标

- 保持 modular monolith，不在 V2 初期拆微服务。
- 任何最终 skill 必须具备 evidence traceability。
- 允许不同模态使用专用 distiller，但中间语义层必须统一。
- 模型失败时可以退化为 heuristic 或 partial output，而不是整链失效。
- 后续可以对 skill、evidence、atom 做检索与增量更新。

### 2.3 明确不做

- V2 初期不做复杂在线协作编辑器。
- V2 初期不做分布式流式处理平台。
- V2 初期不强依赖图数据库；关系型 + JSONB 足够支撑前期演化。

## 3. 目标架构

### 3.1 总体主链

```text
Raw Asset / Asset Bundle
  -> Modality Parser
  -> EvidenceNode
  -> SemanticAtom
  -> SkillGraph
  -> Review / Quality Gate
  -> Renderers(SKILL.md / checklist / decision tree / playbook / embedding payload)
```

### 3.2 为什么要从 `EvidenceUnit` 升级到 `EvidenceNode`

`EvidenceNode` 仍然是统一证据层，但不再只保存纯文本，而是保存“证据 + 结构 + 定位 + lineage”。

推荐字段：

```json
{
  "evidence_id": "uuid",
  "asset_id": "uuid",
  "modality": "video",
  "content_type": "ocr",
  "span_ref": "frame:0012",
  "time_range": {"start_ms": 12000, "end_ms": 12300},
  "spatial_ref": {"x": 10, "y": 20, "w": 320, "h": 48},
  "structural_ref": {"section": "3.2", "row": 4, "column": "latency_p99"},
  "text_content": "Service degraded",
  "payload": {...},
  "parents": ["..."],
  "children": ["..."],
  "derived_from": ["..."],
  "confidence": 0.83,
  "tags": ["ocr", "region:title"]
}
```

最关键的不是字段多，而是保留每个模态后续继续推理所需的结构。

### 3.3 为什么要从 `Insight` 升级到 `SemanticAtom`

`Insight` 当前过于宽泛，很多本质不同的知识都被压进一层。V2 应改成 typed semantic atom。

建议最小集合：

- `ClaimAtom`: 可验证陈述
- `ProcedureAtom`: 单个操作动作
- `RuleAtom`: 条件-决策规则
- `VerificationAtom`: 校验动作或通过标准
- `AntiPatternAtom`: 明确不应做的动作
- `EntityAtom`: 人、系统、组件、指标、环境
- `EventAtom`: 某个发生过的操作、故障、变更、异常窗口
- `ExampleAtom`: 正例 / 反例 / 边界条件
- `MetricGuardrailAtom`: 指标阈值、趋势、预警条件
- `QuestionAtom`: 证据不足、需要人工确认的问题

它们的共同目标不是渲染人类文档，而是给后续 assembly 与 review 提供稳定的中间层。

### 3.4 `SkillGraph` 作为知识本体

`SkillGraph` 不直接面向人类，而是面向后续组装、检索、版本演化。

```text
SkillGraph
  - metadata
  - nodes
    - StepNode
    - DecisionNode
    - VerificationNode
    - ExampleNode
    - RiskNode
    - VariableNode
  - edges
    - depends_on
    - justified_by
    - verified_by
    - supersedes
    - conflicts_with
    - parameterizes
```

至少要支持以下能力：

- 精确追踪每个 step 由哪些 atom 和 evidence 支撑
- 表达 step 间依赖
- 表达 rule 与 verification 的绑定关系
- 表达旧版本 skill 被哪个新版本 supersede
- 表达变量化输入，例如环境、路径、组件、阈值

### 3.5 发布层只负责渲染视图

发布层应该是 renderer，而不是核心本体。V2 至少支持以下输出视图：

- `SKILL.md`: 人类可读的最终技能文档
- `skill.json`: 结构化技能视图
- `checklist.json`: 检查单视图
- `decision_tree.json`: 条件决策视图
- `playbook.json`: 长流程编排视图
- `embedding_document`: 供检索的精简语义视图

结论很简单：同一份 `SkillGraph` 可以有多个视图，但一个视图不应该成为唯一真相源。

## 4. 模态专用蒸馏策略

### 4.1 文档

V2 目标：

- section hierarchy
- code block / table / figure 单独成 node
- 标题、正文、注释、脚注分层
- 跨 section 的 procedure / rule / warning 抽取

建议流程：

```text
Document
  -> Document Structure Parser
  -> EvidenceNode(section/paragraph/table/code)
  -> ProcedureAtom / RuleAtom / ClaimAtom / ExampleAtom
  -> SkillGraph Assembly
```

### 4.2 音频

V2 不应再以 transcript 文本为唯一核心，而是补齐：

- diarization
- utterance act: question / decision / action item / objection / context
- unresolved issue
- speaker role

建议流程：

```text
Audio
  -> ASR + diarization
  -> utterance segmentation
  -> EventAtom / RuleAtom / QuestionAtom / ProcedureAtom
  -> SkillGraph Assembly or Decision Memo
```

### 4.3 图片

V2 重点不是“看图说话”，而是“识别布局与操作意义”：

- layout role: title / button / input / chart / legend / callout
- bbox hierarchy
- OCR block grouping
- diagram relation extraction
- UI state semantics

### 4.4 视频

V2 重点不是“抽几帧”，而是构建时间语义：

- transcript 与 frame 对齐
- scene cluster
- UI action timeline
- frame event
- subtitle / OCR / scene summary 汇合

建议新增概念：

- `SceneNode`
- `FrameEventNode`
- `TimelineSegment`
- `SubtitleTrack`

### 4.5 表格与时序

当前这一块已经是 V2 雏形，但还需要继续专业化：

- schema lineage
- metric formula / aggregation grain
- baseline spec
- change point
- seasonality / drift / anomaly type
- guardrail recommendation

结论：

- 时序数据默认优先蒸成 `MetricGuardrailAtom / EventAtom / ClaimAtom`
- 只有在 evidence 足以支持明确操作链时，才进一步组合成 procedure skill

## 5. 新的领域模型

### 5.1 领域对象

建议新增或替换如下：

```text
Corpus
  -> 一次蒸馏上下文，可含多个 Asset

Asset
  -> 原始输入资源

EvidenceNode
  -> 带结构、定位、lineage 的证据节点

SemanticAtom
  -> Typed 中间语义原子

SkillGraph
  -> 技能知识本体

ReviewTask
  -> 人工评审任务

Publication
  -> SkillGraph 的某种发布视图
```

### 5.2 `Corpus` 的意义

很多真实 skill 来自一个证据集合，而不是单文件：

- 设计文档 + 会议录音 + issue 评论
- 故障视频 + 仪表盘截图 + 时序指标
- SOP 文档 + 培训视频 + 屏幕录制

因此 V2 需要引入 `Corpus` 作为一轮蒸馏的上位容器：

- 一个 `Corpus` 可关联多个 `Asset`
- 一个 `Corpus` 可产出多份 `SkillGraph`
- 一个 `SkillGraph` 可引用多个 `Corpus` 版本

### 5.3 状态机

```text
RECEIVED
  -> PARSED
  -> NORMALIZED
  -> EVIDENCE_BUILT
  -> ATOMS_EXTRACTED
  -> ASSEMBLED
  -> SCORED
  -> REVIEW_PENDING
  -> APPROVED
  -> PUBLISHED
  -> SUPERSEDED | REJECTED | NEEDS_REWORK
```

相比 V1，新增的关键节点：

- `ATOMS_EXTRACTED`
- `ASSEMBLED`
- `SCORED`
- `NEEDS_REWORK`
- `SUPERSEDED`

## 6. 组装与路由策略

### 6.1 Distillation Router

V2 应新增显式路由器，根据以下信号选择 distiller：

- `goal_type`
- `domain`
- `audience`
- `modality mix`
- `evidence density`
- `quality budget`

输出：

- `ProcedureSkillDistiller`
- `DecisionTreeDistiller`
- `DiagnosticGuardrailDistiller`
- `PlaybookDistiller`
- `RejectLowSignalDistiller`

### 6.2 Assembly Policy

在 `SemanticAtom -> SkillGraph` 阶段，不要默认生成新 skill，而是先做判定：

- `new`: 不存在足够相似的旧 skill
- `revise`: 已有 skill 存在，且新证据只是补全或修订
- `merge`: 多个 skill 事实上是同一技能的重复分支
- `supersede`: 新 skill 取代旧 skill
- `reject`: 信号不足、噪声过大或证据冲突

### 6.3 相似性判定

V2 初期推荐混合策略：

- 结构相似：domain、skill_type、核心 entity、核心 trigger
- 语义相似：pgvector embedding
- 规则相似：decision rule overlap
- step 相似：procedure atom overlap

## 7. 质量关卡与评审

### 7.1 Quality Gate

每次蒸馏至少评分以下维度：

- `traceability_score`: step 是否可追到 atom 和 evidence
- `actionability_score`: 是否形成可执行动作
- `coverage_score`: 关键证据是否被纳入
- `consistency_score`: 是否存在冲突 statement
- `noise_score`: OCR/ASR/scene 噪声是否过高
- `novelty_score`: 与已有 skill 的增量价值

### 7.2 Review Queue

以下情况默认进入人工评审：

- `noise_score` 高
- `consistency_score` 低
- 多模态证据互相冲突
- 关键结论来自单个低置信 evidence
- 输出为 `supersede`
- audience 为 `junior` 且将进入发布态

### 7.3 反馈回流

review 结果不能只写备注，必须反哺为结构化信号：

- 原因分类：噪声、缺证据、步骤不可执行、规则不完整、版本过期
- 纠正动作：删 atom、补 atom、调整 assembly policy、提高 review 阈值

## 8. 存储设计

### 8.1 V2 存储原则

- PostgreSQL 是 system of record
- 文件系统或对象存储保存 raw asset 和大体积中间文件
- pgvector 支持 skill / atom / evidence 检索
- JSONB 保存 payload 与模态专用结构

### 8.2 建议表

- `corpora`
- `corpus_assets`
- `assets`
- `evidence_nodes`
- `semantic_atoms`
- `skill_graphs`
- `skill_graph_nodes`
- `skill_graph_edges`
- `publications`
- `review_tasks`
- `review_feedback`
- `lineage_links`

### 8.3 为什么不急着上图数据库

V2 初期的图关系规模和查询模式都还可预测：

- 按 skill 查 node / edge
- 按 evidence 查被哪些 skill 引用
- 按 atom 查相似 skill

这些查询用 PostgreSQL + JSONB + pgvector 足够支撑，复杂度远低于同时引入一套图数据库。

## 9. 模块演化建议

### 9.1 保留

- `adapters`
- `providers`
- `service`
- `render`

### 9.2 重构

- `pipeline.py`
  - 拆成 `atom_extractor.py`、`assembly.py`、`quality_gate.py`
- `models.py`
  - 新增 `Corpus`、`EvidenceNode`、`SemanticAtom`、`SkillGraph`
- `repository.py`
  - 增加 PG repository 接口与 file/object store 分离

### 9.3 新增建议模块

```text
src/omni_skill_pipeline/
  routing/
    distillation_router.py
  extraction/
    atom_extractor.py
    modality/
  assembly/
    skill_graph_builder.py
    publication_builder.py
  quality/
    scoring.py
    review_policy.py
  retrieval/
    similarity.py
  persistence/
    postgres_repository.py
    blob_store.py
```

## 10. 对现有代码的迁移原则

### 10.1 原则

- 保持外部 CLI / API 兼容
- 先扩展模型，再替换主链
- 先双写文件产物与新结构化产物，再切主存储
- 允许一段时间内 V1 renderer 渲染自 V2 graph

### 10.2 兼容策略

V2 过渡期建议：

- 保留 `SkillDocument`
- 增加 `SkillGraph`
- 由 `SkillGraphRenderer` 渲染出 `SkillDocument`
- 最终再把 `SkillDocument` 降级为 publication view

这样能避免一次性重写所有现有接口。

## 11. 关键架构决策

### ADR-001: 保持 Modular Monolith

原因：

- 当前项目仍在高速演化期
- 核心问题在知识模型，不在服务拆分
- 单体更利于快速重构与端到端验证

### ADR-002: PostgreSQL 作为首要持久层

原因：

- 事务、版本、review、lineage 更适合关系模型
- 可直接接 pgvector
- 运维复杂度低于多库组合

### ADR-003: `SkillGraph` 为真相源，`SKILL.md` 为发布视图

原因：

- 允许多视图渲染
- 允许增量更新
- 允许更稳定的评审与检索

### ADR-004: 引入 `Corpus`

原因：

- 多模态真实世界输入天然是多资产集合
- 单 asset 模型限制了知识组合能力

## 12. 成功标准

V2 至少要满足以下标准，才算真正替代 V1：

- 同一 `Corpus` 可由多资产联合蒸馏
- 最终 `step` 可追溯到 atom，再追溯到 evidence
- 新证据进入时，系统可以判断 `new / revise / merge / supersede / reject`
- Review queue 真正跑通
- 至少一种非 `SKILL.md` 输出视图落地
- 视频与时序的最终输出质量明显高于当前 V1

## 13. 给后续实现者的执行约束

面向后续用 `gpt-5.3-codex` 实施时，务必遵守：

- 先建模型与状态机，不要先改 prompt
- 先把 `EvidenceNode` 与 `SemanticAtom` 立住，再谈更多 provider
- 先打通 review 与 quality gate，再扩大自动发布
- 任何新增字段都要回答：它支撑的是业务问题、系统问题，还是技术问题
- 任何新产物都要回答：它是知识本体、派生产物，还是调试工件
