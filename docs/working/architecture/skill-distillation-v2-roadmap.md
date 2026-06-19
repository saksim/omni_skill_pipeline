# Skill Distillation V2 Roadmap

> 2026-05-18 status update: Phase 1 is complete. The latest Linux release run reached `GO`, and current execution has moved from core V2 model rollout to controlled business trial and Agent Skill Compiler validation. See [../status/CURRENT_STATUS.md](../status/CURRENT_STATUS.md) and [../status/2026-05-18-controlled-business-trial-iteration.md](../status/2026-05-18-controlled-business-trial-iteration.md).

## 判词

V2 不能一口吞天。正确路径不是推倒重来，而是沿着“模型先行、主链渐进替换、存储双写、评审闭环先落地”的顺序分阶段推进。

## 1. 实施总原则

- 先领域模型，后 provider 增强。
- 先结构化中间层，后 prompt 精修。
- 先双写与兼容，后主路径切换。
- 先质量门禁，后扩大自动发布比例。
- 每个阶段都必须有可回退边界。

## 2. 阶段总览

```text
Phase 0  对齐与基线
Phase 1  领域模型升级
Phase 2  原子抽取链路
Phase 3  SkillGraph 组装
Phase 4  质量门禁与 Review Queue
Phase 5  PostgreSQL + pgvector 持久化
Phase 6  检索、增量更新与 supersede
Phase 7  多视图发布与 V1 收口
```

## 3. Phase 0：对齐与基线

### 目标

- 冻结 V1 当前行为
- 明确迁移边界
- 建立验收样本集

### 具体动作

1. 选取代表性样本集：
   - 文档 3 份
   - 音频 3 份
   - 图片 3 份
   - 视频 3 份
   - 表格/时序 3 份
2. 为每份样本记录当前 V1 输出：
   - `bundle.json`
   - `skill.json`
   - `SKILL.md`
3. 建立评估维度：
   - traceability
   - actionability
   - noise tolerance
   - reviewer edit distance
4. 明确兼容约束：
   - CLI 不破
   - API 路由不破
   - 现有 file artifact 仍可继续生成

### 交付物

- 基线样本清单
- V1 质量评估表
- 兼容性约束文档

### 验收标准

- 任意后续改动都能与 Phase 0 基线做对比

## 4. Phase 1：领域模型升级

Status: Complete as of 2026-05-18. The implementation now has serializable V2 models, compatibility transforms, corpus/publication/review coverage, and release-contract evidence through the latest `GO` release run.

### 目标

- 在不打断 V1 外部接口的前提下，引入 V2 新模型

### 代码动作

1. 在 `models.py` 中新增：
   - `Corpus`
   - `EvidenceNode`
   - `SemanticAtom`
   - `SkillGraph`
   - `Publication`
2. 保留 `SkillDocument`
3. 建立转换器：
   - `EvidenceUnit -> EvidenceNode`
   - `SkillGraph -> SkillDocument`
4. 明确枚举类型：
   - `AtomType`
   - `GraphNodeType`
   - `LifecycleDecisionType`

### 推荐文件落点

```text
src/omni_skill_pipeline/models.py
src/omni_skill_pipeline/transformers.py
```

### 验收标准

- 新模型可序列化
- 不影响现有测试通过
- `SkillGraph -> SkillDocument` 最小转换可运行

### 风险

- 领域模型一开始设计得太细，会拖慢推进

### 控制策略

- 只实现最小闭环字段，预留 `payload` / `metadata`

## 5. Phase 2：原子抽取链路

### 目标

- 把 `InsightExtractor` 升级为 `AtomExtractor`

### 代码动作

1. 拆分 `pipeline.py`
   - `extraction/atom_extractor.py`
   - `extraction/modality/*.py`
2. 每种模态至少产出以下 atom：
   - 文档：`ClaimAtom / ProcedureAtom / RuleAtom`
   - 音频：`EventAtom / ProcedureAtom / QuestionAtom`
   - 图片：`ClaimAtom / EntityAtom / ProcedureAtom`
   - 视频：`EventAtom / ProcedureAtom / ClaimAtom`
   - 时序：`MetricGuardrailAtom / EventAtom / ClaimAtom`
3. 在过渡期保留：
   - `HeuristicInsightExtractor`
   - 新增 `HeuristicAtomExtractor`
4. 让 service 支持同时输出：
   - `insights`
   - `semantic_atoms`

### 验收标准

- 每种模态至少有 1 条端到端测试覆盖 atom 输出
- atom 数量与 evidence 数量之间存在合理比例，不是全部空壳

### 风险

- atom 设计过宽，退化为换皮 insight

### 控制策略

- 每个 atom 必须回答：它是否能独立支撑 assembly 决策

## 6. Phase 3：SkillGraph 组装

### 目标

- 从 `SemanticAtom[]` 组装 `SkillGraph`

### 代码动作

1. 新增：
   - `assembly/skill_graph_builder.py`
   - `assembly/publication_builder.py`
2. 明确 graph node：
   - `StepNode`
   - `DecisionNode`
   - `VerificationNode`
   - `RiskNode`
   - `VariableNode`
3. 明确 edge：
   - `depends_on`
   - `justified_by`
   - `verified_by`
   - `parameterizes`
4. 实现 `SkillGraphRenderer`
   - 输出兼容当前 `SkillDocument`
5. 让 `DistillationService` 支持两种路径：
   - V1: `evidence -> insight -> skill document`
   - V2 shadow: `evidence node -> semantic atom -> skill graph -> skill document`

### 验收标准

- V2 shadow path 可跑通
- 产出的 `SkillDocument` 与 V1 在格式上兼容
- `step -> atom -> evidence` 可追溯

### 风险

- graph 组装规则不稳定，导致结果震荡

### 控制策略

- 优先做 deterministic heuristic builder
- LLM 只做补充，不做唯一真相源

## 7. Phase 4：质量门禁与 Review Queue

### 目标

- 真正落地 `REVIEW_PENDING`

### 代码动作

1. 新增：
   - `quality/scoring.py`
   - `quality/review_policy.py`
2. 评分维度最小实现：
   - `traceability_score`
   - `actionability_score`
   - `consistency_score`
   - `noise_score`
3. 输出 review 决策：
   - `auto_publish`
   - `review_required`
   - `reject`
4. 为 review task 定义结构化原因码
5. CLI / API 增加查看评分与 review 状态能力

### 验收标准

- 每次蒸馏都有质量评分
- 部分样本会被自动打入 review queue
- review 状态能持久化

### 风险

- 评分规则太粗，全部进入 review

### 控制策略

- 初期阈值从宽，先追求可解释，再慢慢收紧

## 8. Phase 5：PostgreSQL + pgvector 持久化

### 目标

- 从 file artifact store 升级为正式持久层

### 代码动作

1. 设计并落地迁移 SQL：
   - `corpora`
   - `corpus_assets`
   - `evidence_nodes`
   - `semantic_atoms`
   - `skill_graphs`
   - `skill_graph_nodes`
   - `skill_graph_edges`
   - `publications`
   - `review_tasks`
2. 新增：
   - `persistence/postgres_repository.py`
3. 过渡期采用双写：
   - PostgreSQL
   - file artifact
4. 将 `bundle.json` 继续保留为调试工件，而不是唯一存储
5. 引入 pgvector 存储：
   - publication embedding
   - atom embedding

### 验收标准

- 任一 skill 可从 PostgreSQL 完整重建 publication
- file artifact 可作为旁路调试产物保留

### 风险

- 先切存储再切模型，导致 schema 快速失配

### 控制策略

- 必须在 Phase 1-4 稳定后再切持久层

## 9. Phase 6：检索、增量更新与 supersede

### 目标

- 让新证据进入旧知识，而不是不断复制 skill

### 代码动作

1. 新增检索模块：
   - `retrieval/similarity.py`
2. 支持混合相似度：
   - embedding
   - domain/tag
   - graph overlap
3. 实现生命周期判定：
   - `new`
   - `revise`
   - `merge`
   - `supersede`
   - `reject`
4. 为 `supersede` 建立 lineage link

### 验收标准

- 给相近样本输入时，系统能命中旧 skill
- 至少支持 `new` 与 `revise`
- `supersede` 有清晰审计链

## 10. Phase 7：多视图发布与 V1 收口

### 目标

- 让 `SKILL.md` 从真相源降级为视图

### 代码动作

1. 除 `SKILL.md` 外至少新增一种发布视图：
   - `decision_tree.json` 或 `checklist.json`
2. 统一 publication builder
3. 将外部 API 改为返回：
   - graph metadata
   - available publications
4. 将 V1 `HeuristicSkillComposer` 退居兼容路径

### 验收标准

- `SkillGraph` 成为唯一知识真相源
- `SKILL.md` 由 renderer 生成，不再直接 compose

## 11. 推荐任务拆分

面向 `gpt-5.3-codex` 实施时，建议按以下批次提交：

### 批次 A：模型与接口

- 新增模型
- 新增 enum
- 新增转换器
- 补测试

### 批次 B：AtomExtractor

- 拆 `pipeline.py`
- 加 atom 提取器
- 保留 V1 兼容

### 批次 C：SkillGraph Builder

- graph builder
- renderer
- shadow mode

### 批次 D：Quality Gate

- scoring
- review policy
- review task 持久化接口

### 批次 E：PostgreSQL Repository

- migrations
- repository
- dual-write

### 批次 F：Retrieval 与 lifecycle

- similarity
- revise/merge/supersede

### 批次 G：多视图发布

- checklist / decision tree
- API 返回结构更新

## 12. 每阶段测试要求

### 单元测试

- 模型序列化
- atom 抽取
- graph 组装
- score 计算
- lifecycle decision

### 集成测试

- 文档 -> graph -> publication
- 视频 -> graph -> review pending
- 时序 -> guardrail publication

### 回归测试

- 现有 CLI 子命令仍可用
- 现有 API 路由仍可用
- 现有 file artifact 仍会生成

## 13. 推荐验收样本

建议固定以下回归样本类型：

- 操作手册型 PDF
- 带明确 action item 的会议音频
- UI 截图
- 产品演示视频
- 监控指标 CSV

每次阶段推进后，都用同一组样本对比：

- reviewer edit distance 是否下降
- 可追溯率是否上升
- 误生成 procedure 的比例是否下降

## 14. 实施禁忌

- 不要先大改 prompt，后补模型
- 不要把所有模态继续压成纯文本再说
- 不要让 LLM 成为唯一组装器
- 不要在 review 闭环未落地前直接扩大自动发布
- 不要先引入过重的多服务部署复杂度

## 15. 第一批最值得立刻做的事

如果只允许先做一轮最小有效改造，优先顺序如下：

1. 新增 `EvidenceNode / SemanticAtom / SkillGraph`
2. 实现 `SkillGraph -> SkillDocument` 渲染兼容
3. 为视频与时序加专门 atom 抽取
4. 加 `traceability_score / noise_score`
5. 落 `review_required`

做到这五步，系统就从“一次性蒸馏器”跨进“可演化知识系统”的门槛。
