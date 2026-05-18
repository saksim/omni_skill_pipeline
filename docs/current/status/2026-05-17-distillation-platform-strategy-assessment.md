# Distillation Platform Strategy Assessment

> Date: 2026-05-17  
> Scope: current capability boundary, field competitiveness, and next-stage evolution plan  
> Sources: `src/`, `tests/`, `docs/current/architecture/`, `docs/current/status/launch-readiness-master-plan.md`, public field references listed below

## 判词

项目不是“文件转 Markdown 工具”，也不应定位成又一个通用 LLM observability 平台。当前最准确的长期定位是：

> 从真实多模态证据中生成、评审、版本化、更新 Agent Skills 的技能蒸馏与治理层。

但短期战略必须收敛：不要先做“大而全蒸馏平台”，而要先做一个能快速把万物资料编译为 Codex / Claude Code / OpenCode 可直接使用的 `SKILL.md` 技能包的 **Skill Compiler**。

如果当前测试全部通过，项目已经具备受控 Beta / 内部生产试运行能力，并接近单团队可用的早期 GA。它的强项是多模态输入、知识本体、证据追踪、发布视图与生命周期雏形；短期短板不是“平台不够大”，而是最后一公里还没有把内部 `SkillDocument / SkillGraph` 稳定编译成 agent 原生可用的 skill package。

## 0. 战略修订：优先做 Skill Compiler

### 0.1 新的一阶段目标

一阶段目标不是建设完整知识治理平台，而是：

> 输入任意资料，快速生成可被 Codex、Claude Code、OpenCode 发现、加载、触发、执行的 `SKILL.md` 技能包。

目标链路：

```text
Text / Audio / Image / Video / Tabular / Corpus
  -> Lightweight Evidence
  -> SkillDocument / SkillGraph
  -> AgentSkillPackage
  -> SKILL.md + references/ + scripts/ + assets/
  -> .codex/skills / .claude/skills / .opencode/skill
  -> Agent immediately uses it
```

### 0.2 这个目标为什么更适合当前阶段

- 它直接服务主平台：蒸馏平台可以作为主平台的技能生产线，而不是独立 SaaS。
- 它避开正面竞争：OpenAI / Anthropic 会做通用 agent runtime 与通用 skill 机制，本项目做上游的资料蒸馏与技能编译。
- 它能快速验证价值：只要生成的 skill 能被 Codex / Claude Code / OpenCode 用起来，就能形成即时反馈。
- 它复用现有资产：当前已有多模态 adapter、`SkillDocument`、`SkillGraph`、publication builder、CLI/API/worker，不需要推倒重来。

### 0.3 当前差距

当前输出更像内部蒸馏报告，还不是稳定 agent skill package。主要差距：

- `SKILL.md` 缺少 agent skill 常用的 YAML frontmatter。
- `description` 还没有被设计成精准触发器。
- 主文档仍携带过多元信息与证据链，可能污染 agent 上下文。
- 缺少 portable package 结构：`SKILL.md`、`references/`、`scripts/`、`assets/`。
- 缺少目标导出器：Codex、Claude Code、OpenCode 的目录结构和兼容约束没有被显式建模。
- 缺少可用性校验：生成后是否能被触发、是否足够短、是否有 workflow / validation / failure modes。

### 0.4 最小可用 Skill 包标准

一份可用给 coding agent 的 `SKILL.md` 至少应具备：

```markdown
---
name: postgresql-slow-query-review
description: Review PostgreSQL slow queries before adding indexes. Use when the user asks to diagnose slow SQL, inspect EXPLAIN ANALYZE output, compare row estimates, or decide whether to add indexes.
---

# PostgreSQL Slow Query Review

## Workflow

1. Collect the query, runtime, database version, table sizes, indexes, and `EXPLAIN ANALYZE`.
2. Compare estimated rows with actual rows.
3. Identify whether the bottleneck is I/O, CPU, lock contention, poor join order, or stale statistics.
4. Propose one change at a time.

## Decision Rules

- If actual rows differ sharply from estimated rows, inspect statistics before adding indexes.
- If the query is I/O bound, check index coverage and buffer reads.
- If lock wait dominates, do not rewrite SQL first.

## Validation

- Compare latency before and after.
- Compare buffer hits, rows scanned, and plan shape.
- Confirm no write amplification from redundant indexes.

## Failure Modes

- Do not change query text and index strategy at the same time.
- Do not add overlapping indexes without checking write cost.
```

长证据、原文摘录、完整 transcript、OCR 噪声、样例输出应放入 `references/evidence.md` 或 `references/examples.md`，而不是塞进 `SKILL.md` 主体。

### 0.5 当前应后置的事项

以下事项仍有价值，但不应阻塞 Skill Compiler 一阶段：

- 完整 Review UI。
- 多租户与权限体系。
- 大规模 pgvector / qdrant 检索。
- 复杂 merge / supersede 生命周期。
- 完整 observability dashboard。
- 成熟的 Postgres-first 知识库产品形态。

一阶段只追求一个结果：生成出来的 skill 能被 agent 立刻用。

### 0.6 一阶段任务顺序

1. 新增 `AgentSkillPackage` 数据模型。
2. 新增 `PortableSkillRenderer`，从 `SkillDocument / SkillGraph` 渲染 agent 原生 `SKILL.md`。
3. 新增目标导出器：
   - `--target codex`
   - `--target claude-code`
   - `--target opencode`
   - `--target portable`
   - `--target all`
4. 输出目录：
   - `.codex/skills/<skill-name>/SKILL.md`
   - `.claude/skills/<skill-name>/SKILL.md`
   - `.opencode/skill/<skill-name>/SKILL.md`
   - `skills/portable/<skill-name>/SKILL.md`
5. 新增 skill 可用性检查：
   - frontmatter 存在且只包含必要字段。
   - `name` 短、稳定、目录名一致。
   - `description` 明确触发场景。
   - 主体短，默认不超过 500 行。
   - 包含 `Workflow`、`Decision Rules`、`Validation`、`Failure Modes`。
   - 长证据进入 `references/`。
   - 不泄露 secret / 本机绝对路径 / 私有 token。
   - 不自动执行危险命令。
6. CLI 增加：
   - `export-skill`
   - 或在现有 distill 命令上增加 `--export-agent-skill --target ...`
7. 对四类输入做最小模板：
   - image -> visual inspection skill
   - audio -> meeting decision skill
   - video -> SOP from video skill
   - tabular/time-series -> metric diagnostic skill
8. 用真实 Codex / Claude Code / OpenCode 做 smoke test：生成后能否触发并完成一个小任务。

## 1. 当前能力边界

### 1.1 已经具备的系统能力

当前代码已经从 V1 的单次生成器演进为 V2 语义链路：

```text
Raw Asset / Corpus
  -> Modality Adapter
  -> EvidenceNode
  -> SemanticAtom
  -> SkillGraph
  -> Quality / Review Policy
  -> Publication Views
  -> File / Postgres / Dual Write Repository
```

已落地能力：

- 多模态输入：text、audio、image、video、tabular/time-series。
- 多资产输入：`CorpusDistillRequest` 与 `/v1/distill/corpus`。
- 语义中间层：`Corpus`、`EvidenceNode`、`SemanticAtom`、`SkillGraph`、`Publication`。
- 发布视图：`SKILL.md`、`skill.json`、`checklist.json`、`decision_tree.json`。
- 质量门禁：traceability、actionability、coverage、consistency、noise、novelty heuristic scoring。
- Review 链路：review policy、review task、review feedback、file review queue、API list/claim/close。
- Worker 链路：本地 job claim、retry、idempotency、corpus/review/rebuild/revise job。
- 存储链路：file artifact repository、Postgres repository、dual-write repository。
- 检索与生命周期：in-memory similarity、`new / revise / merge / supersede / reject` 决策引擎。
- 生产外壳：API schema validation、auth、rate limiting、error contract、request/trace context、readiness check。

### 1.2 当前能承诺的上线层级

| 层级 | 判断 | 说明 |
| --- | --- | --- |
| L0 内网试运行 | 可承诺 | 主链、多模态输入、artifact 落盘、基础 review 已可用 |
| L1 受控外部 Beta | 可谨慎承诺 | API/worker/queue/发布门禁已有基础，仍需严格限制客户数量与使用场景 |
| L2 单团队早期 GA | 接近但需证据 | Postgres、worker、review queue 已有实现，但需要真实负载、真实样本与运行手册验证 |
| L3 多租户平台化 SaaS | 不应承诺 | 缺租户隔离、权限模型、配额体系、协作 UI、可观测性集成与成本治理 |

### 1.3 当前不应夸大的能力

- 质量评分仍是 heuristic，尚不能证明它能稳定预测人类 reviewer 的判断。
- `pgvector` / `qdrant` 仍是后续切换目标，当前真实可用检索主要是 in-memory lexical + structured hints。
- Review queue 是最小操作面，不是完整 SME 协作产品。
- Worker 是本地文件队列，不是 Celery / Kafka / Temporal 等分布式任务系统。
- 反馈能结构化落盘，但尚未形成“反馈自动改进抽取、组装、阈值”的学习闭环。
- 还没有足够公开 benchmark 证明自动蒸馏结果优于普通 LLM 总结或人工手写沉淀。

结论：工程骨架强，产品证据弱；平台形态已成，市场证明未成。

## 2. 领域竞争性判断

### 2.1 不是闭门造车

当前外部领域正在向三个方向收敛：

1. Agent / LLM observability and eval  
   OpenAI、LangSmith、Langfuse、Phoenix 等平台都在强化 tracing、datasets、experiments、human/LLM evaluation。
2. AI data development and governance  
   Snorkel、Scale、Databricks Mosaic AI 等平台强调数据开发、评估、标注、合成数据、RAG/agent 优化。
3. Agent Skills / reusable procedures  
   Anthropic Claude Skills 把 `SKILL.md`、脚本、资源目录作为可复用技能包，说明“技能资产化”正在成为真实生态方向。

这说明项目方向不是孤立想象。市场正在从“能不能调用模型”推进到“能不能持续评估、追踪、复现、治理 agent/skill 行为”。

### 2.2 竞争定位

本项目不适合直接对标 Langfuse、LangSmith、Phoenix、Weave 这类 observability 平台。它们在 trace ingestion、OpenTelemetry、UI、team workflow、experiment dashboard 上更成熟。

本项目更适合占据以下位置：

```text
Evidence Distillation and Skill Governance Layer

Upstream:
  documents / audio / video / screenshots / metrics / incidents / meetings

Core:
  evidence -> atoms -> skill graph -> review -> lifecycle -> publications

Downstream:
  Claude Skills / Codex Skills / internal agent playbooks / checklists / decision trees

Adjacent integrations:
  Langfuse / LangSmith / Phoenix / OpenAI Evals / internal BI
```

### 2.3 差异化优势

| 维度 | 本项目优势 | 竞争含义 |
| --- | --- | --- |
| 多模态证据归一 | text/audio/image/video/tabular/time-series 进入统一 evidence 层 | 比单一 trace/eval 平台更靠近真实知识来源 |
| 语义中间层 | `EvidenceNode`、`SemanticAtom`、`SkillGraph` | 不是只生成文档，而是保留可审计、可合并、可演化结构 |
| 多视图发布 | markdown/json/checklist/decision tree | 同一知识本体可以服务人类、agent、检索与评审 |
| 生命周期决策 | new/revise/merge/supersede/reject | 能避免 skill 库无序膨胀 |
| 质量与 review | scoring、policy、queue、feedback | 为受控发布与治理打基础 |

### 2.4 竞争弱点

| 弱点 | 影响 | 修复方向 |
| --- | --- | --- |
| 缺黄金评测集 | 难以证明质量优于普通 LLM 总结 | 建立每模态标准样本、人工 gold skill、edit distance 与复用率指标 |
| 检索未真正向量化 | lifecycle 判断召回能力有限 | 落地 pgvector / qdrant 与 embedding 写入 |
| 缺 SME 工作台 | review 仍像工程 artifact，不像产品流程 | 最小 Review UI：看证据、看 skill、批准/拒绝/打原因码 |
| 缺外部集成 | 容易被看成孤岛平台 | 输出 OpenTelemetry/OpenInference 或 Langfuse/Phoenix/LangSmith sink |
| 缺垂直场景证明 | 市场叙事抽象 | 先打穿一个高价值场景，例如故障复盘 -> runbook |

## 3. 未来强化路线

### 3.1 P0：黄金评测集与质量证明

目标：证明平台蒸馏出的 skill 可追溯、可执行、可复用，并且比普通 LLM 总结更稳定。

行动：

1. 每个模态准备 20-50 个真实样本。
2. 为每个样本制作人工 gold skill / checklist / decision tree。
3. 建立统一评分维度：
   - traceability
   - actionability
   - factual correctness
   - coverage
   - reviewer edit distance
   - downstream agent success rate
4. 在 `docs/current/status/baselines/` 建立固定 manifest。
5. 把质量回归纳入 release switch。

验收标准：

- 每次发布都能比较新旧输出。
- regression 不只看格式，也看质量维度。
- 至少一个垂直场景能证明自动蒸馏显著减少人工整理成本。

### 3.2 P1：评分系统从 heuristic 升级为校准系统

目标：让质量分能预测 reviewer 决策，而不是只作为静态规则。

行动：

1. 保留当前 `QualityScorer` 作为 deterministic baseline。
2. 增加 LLM-as-judge 评分，但必须保存 prompt、模型、输入、输出与裁决原因。
3. 将 review feedback 转成训练/调参信号。
4. 引入 calibration report，跟踪阈值命中率、误拒、误放、人工改动量。
5. 明确“不可自动发布”的硬规则：低证据、证据冲突、高噪声、涉及危险命令、涉及凭据或生产变更。

验收标准：

- review_required / reject / auto_publish 的预测与人工结论有可度量一致性。
- 阈值调整有证据，不靠直觉。

### 3.3 P1：真实语义检索与生命周期闭环

目标：让 skill 库进入可增长状态，避免重复、冲突、过期技能堆积。

行动：

1. 为 skill、atom、evidence 三层生成 embedding payload。
2. 优先落地 pgvector，除非检索规模或吞吐要求明确推动 qdrant。
3. lifecycle engine 消费真实向量召回结果。
4. 增加 lineage links：
   - supersedes
   - conflicts_with
   - derived_from
   - duplicates
   - complements
5. 建立 stale skill 检测：来源系统变化、指标口径变化、UI 变化、验证失败。

验收标准：

- 新证据进入时，系统能稳定输出 `new / revise / merge / supersede / reject`。
- 相似 skill 不再默认新建。
- 每个 supersede / merge 都有可审计理由。

### 3.4 P2：SME Review 工作台

目标：把 review queue 从工程文件操作升级成知识生产流程。

最小功能：

- 列表：待审、已认领、已关闭。
- 详情：原始证据、EvidenceNode、SemanticAtom、SkillGraph、发布视图。
- 操作：approve、reject、needs_rework、supersede、merge。
- 原因码：缺证据、不可执行、过期、冲突、噪声、敏感信息、危险操作。
- 反馈落盘：结构化写回 review feedback，用于 calibration。

验收标准：

- SME 不需要读 artifact 目录即可完成评审。
- 每个拒绝或返工都有结构化原因码。
- review feedback 能进入质量校准报表。

### 3.5 P2：外部观测平台集成

目标：不自研完整 observability，而是把蒸馏链路开放给成熟平台。

行动：

1. 每次 distillation 输出 trace/span：
   - parse
   - evidence build
   - atom extraction
   - graph assembly
   - quality scoring
   - review decision
   - publication
2. 支持至少一种导出：
   - OpenTelemetry / OpenInference
   - Langfuse sink
   - Phoenix sink
   - LangSmith-compatible run metadata
3. 把 provider footprint、token/cost、latency、error type 纳入 trace。

验收标准：

- 任意失败样本可在外部 trace UI 中复盘。
- 能按 domain、modality、provider、quality decision 聚合问题。

### 3.6 P2：安全与供应链治理

目标：把 skill 当作可执行/半可执行资产治理。

行动：

1. 扩展 schema validation。
2. 增加敏感信息扫描与脱敏回归。
3. 对 dangerous command、生产变更、凭据读取、网络外联等行为打风险标签。
4. 为 skill bundle 增加签名、hash、来源、review 状态、版本锁。
5. 建立 skill publish gate：未通过 review / high risk / low traceability 不可发布。

验收标准：

- 发布 skill 前能回答：来源是什么、谁审过、证据是什么、风险是什么、如何回滚。

## 4. 垂直场景优先级

不要先做“通用平台”叙事。下一阶段应选择一个垂直场景打穿质量闭环。

| 场景 | 输入 | 输出 | 推荐度 | 原因 |
| --- | --- | --- | --- | --- |
| 故障复盘 -> Runbook | incident doc、日志、监控截图、会议纪要 | diagnostic skill / checklist | 高 | 证据强、价值明确、可验证 |
| 数据库慢查询案例 -> DBA Skill | SQL、EXPLAIN、指标、修复记录 | procedure / decision tree | 高 | 项目已有 slow query draft 样本，适合建立基线 |
| 产品操作视频 -> SOP | screen recording、OCR、subtitle | checklist / procedure skill | 中 | 多模态优势明显，但 UI 变化会带来维护成本 |
| 会议/Issue -> 决策技能 | transcript、issue comments、PR notes | decision tree / playbook | 中 | 价值高，但事实校验和上下文补全难度较高 |
| 时序异常 -> Guardrail | metrics、events、thresholds | metric guardrail / alert playbook | 中 | 适合结构化 atom，但需要领域阈值校准 |

建议首选两个楔子：

1. 数据库慢查询案例 -> DBA Skill。
2. 故障复盘 -> Runbook。

这两个场景的共同点是 evidence 可审计、结果可验证、复用收益清晰。

## 5. 未来 90 天路线图

### 0-30 天：Agent Skill Compiler

- 建立 `AgentSkillPackage` 模型。
- 建立 `PortableSkillRenderer`。
- 生成带 YAML frontmatter 的 agent 原生 `SKILL.md`。
- 将长证据外置到 `references/evidence.md`。
- 支持 `codex / claude-code / opencode / portable / all` 导出目标。
- CLI 增加 `export-skill` 或 `--export-agent-skill`。
- 建立 skill 可用性检查器。
- 用 5 个真实样本完成端到端 smoke test。

验收标准：

- 生成的 skill 包能被目标 agent 目录发现。
- `description` 能触发正确使用。
- agent 使用 skill 后能完成一个小任务。
- 主 `SKILL.md` 不再携带冗长证据噪声。

### 31-60 天：四类最小蒸馏模板

- image -> visual inspection skill。
- audio -> meeting decision skill。
- video -> SOP from video skill。
- tabular/time-series -> metric diagnostic skill。
- 为每类模板建立 5-10 个样本。
- 对每类模板补齐 `Workflow / Decision Rules / Validation / Failure Modes`。

验收标准：

- 每类输入都能生成一个可用 agent skill。
- 每类 skill 至少通过一个真实 agent 使用案例。

### 61-90 天：主平台集成与轻量质量基线

- 将 Agent Skill Compiler 接入主平台。
- 建立 portable skill registry。
- 为已生成 skill 增加 hash、source、created_at、target、validation status。
- 建立最小质量基线：
  - skill 是否触发。
  - skill 是否完成任务。
  - 人工修改距离。
  - 是否泄露敏感信息。
- 只在真实需求出现后再推进 pgvector、Review UI、复杂 lifecycle。

验收标准：

- 主平台能一键从输入资料生成并安装 skill。
- 生成 skill 可在 Codex / Claude Code / OpenCode 至少一个目标中稳定使用。
- 每次生成都有可追溯 source 与 validation status。

## 5A. 中长期平台路线

### 0-30 天：质量基线

- 建立黄金评测集 v0。
- 每个模态至少 20 个样本。
- 产出人工 gold skill。
- 打通 quality regression report。
- 明确一个垂直场景作为主战场。

### 31-60 天：检索与生命周期

- 落地 embedding payload。
- 打通 pgvector 最小写入与召回。
- lifecycle engine 接真实召回。
- 为 merge/supersede/reject 建立审计报告。

### 61-90 天：Review 工作台与外部集成

- 上线最小 SME Review UI。
- 打通 review feedback -> calibration report。
- 输出 OpenTelemetry/OpenInference trace 或选定一个第三方 sink。
- 完成一个垂直场景的端到端案例报告。

## 6. 成功指标

### 产品指标

- `gold_skill_pass_rate`: 自动输出满足 gold rubric 的比例。
- `reviewer_edit_distance`: 人工修改距离，越低越好。
- `downstream_agent_success_rate`: agent 使用 skill 完成任务的成功率。
- `duplicate_skill_rate`: 新 skill 中被判定重复的比例，越低越好。
- `time_to_publish`: 从输入证据到可发布 skill 的时间。

### 工程指标

- `traceability_score_p50/p90`
- `quality_regression_fail_count`
- `review_queue_age_p95`
- `provider_error_rate`
- `distillation_latency_p95`
- `publication_success_rate`

### 治理指标

- 未审高风险 skill 发布数必须为 0。
- 含敏感信息的 artifact 发布数必须为 0。
- supersede / merge 决策必须 100% 有 lineage reason。

## 7. 外部参考

- [OpenAI Codex use cases](https://developers.openai.com/codex/use-cases): Codex 可将重复工作流保存为 skills。
- [Introducing the Codex app](https://openai.com/index/introducing-the-codex-app/): OpenAI 内部使用 Codex skills 沉淀代码库与工作流知识。
- [OpenAI Agent evals](https://platform.openai.com/docs/guides/agent-evals): agent tracing、trajectory grading、custom evals。
- [Claude Skills overview](https://claude.com/docs/skills/overview): `SKILL.md`、脚本与资源作为可复用技能包。
- [Claude Code Skills](https://code.claude.com/docs/en/skills): Claude Code 支持 `.claude/skills/<skill-name>/SKILL.md`。
- [OpenCode Agent Skills](https://opencode.ubitools.com/skills/): OpenCode 支持从 `.opencode/skill/`、`.claude/skills/` 等目录发现 `SKILL.md`。
- [Langfuse evaluation docs](https://langfuse.com/docs/evaluation/overview): datasets、experiments、LLM-as-a-judge 与 human evaluation。
- [LangSmith docs](https://docs.smith.langchain.com/): tracing、evaluation、datasets 与 observability。
- [Arize Phoenix docs](https://arize.com/docs/phoenix): AI observability、tracing、datasets、experiments 与 evals。

## 8. 结论

项目方向成立，且没有闭门造车。真正的战略风险不是“方向错”，而是过早建设大平台，导致迟迟不能生成可被真实 agent 使用的 skill。

下一阶段的核心命题应先从“平台还能加什么能力”切换为：

> 能否把任意输入资料快速编译成 Codex / Claude Code / OpenCode 可发现、可触发、可执行的 `SKILL.md` 技能包。

中长期命题才是：

> 能否在一个高价值垂直场景中，稳定把真实证据蒸馏成可追溯、可审核、可复用、可演化的 skill，并证明它比普通 LLM 总结和人工沉淀更快、更稳、更可治理。

短期主线是 **Skill Compiler**；中长期主线才是 **Skill Governance Platform**。
