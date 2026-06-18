# 项目卡点评估

> 日期：2026-06-18  
> 范围：基于当前蓝图、状态、运行、合约与基线证据文档，对项目整体卡点进行评估。  
> 定位：本文记录本轮讨论形成的评估结论，不替代 release switch、launch gate 或受控试运行证据报告。

## 总结论

本项目当前主要不是卡在“核心能不能跑”。

当前真实状态是：

- 工程发布就绪度：对受控试运行而言基本是 `GO`。
- 产品上线就绪度：仍然是 `HOLD`。
- 正确产品姿态：继续按 **Agent Skill Compiler** 做受控试运行。
- 错误产品姿态：现在不应宣称广义外部 Beta、单团队 GA 或多租户 SaaS 就绪。

主卡点是证据，不是架构：

> 项目需要足够的真实、launch-gate-eligible 业务闭环，才可以从受控试运行推进到受控外部 Beta。

## 当前机器判定

2026-06-18 复核命令：

```powershell
python scripts\launch_gate.py --output - --summary-output - --max-evidence-age-hours 0 --print-json
```

观察结果：

- Decision：`HOLD`
- Checks：`15`
- Passed：`14`
- Failed：`1`
- Blocking check：`trial_loop_volume_and_modality_coverage`
- Total complete loops：`10`
- Total modalities：`6`
- Launch-gate-eligible real complete loops：`0/10`
- Launch-gate-eligible real modalities：`0/4`

解释：

- fixture/simulated loop 对工程验证有价值。
- 它们不足以作为受控外部 Beta 的产品证据。
- 当前 gate 正确地区分了“有测试证据”和“有真实用户/业务证据”。

## 证据来源

主要当前状态来源：

- [CURRENT_STATUS.md](CURRENT_STATUS.md)
- [2026-05-17-distillation-platform-strategy-assessment.md](2026-05-17-distillation-platform-strategy-assessment.md)
- [2026-05-18-controlled-business-trial-iteration.md](2026-05-18-controlled-business-trial-iteration.md)
- [2026-05-25-broad-product-launch-plan.md](2026-05-25-broad-product-launch-plan.md)
- [baselines/broad-launch-readiness-summary.md](baselines/broad-launch-readiness-summary.md)
- [baselines/real-trial-loop-collection/real-trial-loop-collection-summary.md](baselines/real-trial-loop-collection/real-trial-loop-collection-summary.md)
- [baselines/real-trial-loop-collection/real-trial-launch-evidence-pack.json](baselines/real-trial-loop-collection/real-trial-launch-evidence-pack.json)
- [baselines/controlled-trial/controlled-trial-run-report.json](baselines/controlled-trial/controlled-trial-run-report.json)
- [../architecture/agent-skill-package-model.md](../architecture/agent-skill-package-model.md)
- [../architecture/portable-skill-renderer.md](../architecture/portable-skill-renderer.md)

## 已经较强的部分

以下内容不应再作为受控试运行的主要阻断项：

- V2 Phase 1 模型与发布基础。
- release switch 与发布证据检查。
- 文档同步检查。
- CLI/API/worker 三类入口。
- review queue 基础能力。
- file repository、Postgres repository 与 dual-write 基础能力。
- provider fallback 姿态。
- portable skill rendering 基线。
- agent skill package model 基线。
- cost、audit、tenant、retention、deletion 的早期平台层表面能力。

这些能力支撑“受控使用”，但不能自动证明“产品可上线”。

## 主要卡点

### 1. 真实试运行覆盖不足

这是决定性卡点。

launch criteria 至少要求：

- `10` 个真实完整闭环。
- 覆盖 `4` 种模态。
- 人工 review trace。
- source trace。
- 0 个未审核发布。
- 0 个 critical secret/PII 泄露。
- agent smoke 达到成功率阈值。
- 成本、延迟、provider failure、reviewer edit distance 等指标可记录。

当前 launch-gate-eligible 真实证据是：

- `0/10` real complete loops。
- `0/4` real modalities。

因此产品上线 readiness 继续是 `HOLD`。

### 2. GO/HOLD 语义容易误读

文档里同时出现 `GO` 和 `HOLD`，因为它们属于不同 gate：

- `GO`：工程发布 / release switch 证据。
- `HOLD`：广义产品上线 readiness。

正确解读是：

> 核心链路足够支撑受控业务试运行，但产品证据还不足以支撑广义外部上线。

任何客户口径或计划口径都必须把这两个 gate 分开。

### 3. 产品定位必须收窄

短期最强产品楔子是 **Agent Skill Compiler**：

> 将真实材料编译成 Codex / Claude Code / OpenCode 风格的 `SKILL.md` 包，使其可发现、可触发、可 review、可被 agent 使用。

当前不应把项目定位为：

- 通用 LLM observability 平台。
- 大而全知识治理平台。
- 多租户 SaaS 平台。
- 全自动技能发布器。

这些可以是后续阶段，但不是当前 proof target。

### 4. Agent-native skill 的真实使用证据仍薄

架构已经包含 `AgentSkillPackage` 和 `PortableSkillRenderer`，并且设计上把长证据放入 `references/`。

剩余风险：

- agent smoke evidence 规模太小。
- 生成技能还需要更多真实 target-agent 验证。
- trigger description、主 `SKILL.md` 简洁性、references、review status、failure modes 都需要在真实工作流里验证。

包格式已经存在；重复真实使用还没有被证明。

### 5. Review 流程已有操作面，但还没有产品化证明

review queue 已支持 list/claim/close 与 approve/reject/needs-rework。

剩余风险：

- reviewer feedback 还需要转化为 calibration 与 remediation 证据。
- reviewer edit distance 需要在真实材料上测量。
- 一轮修订后的 approval rate 需要被证明。
- reviewer packet 需要真实 reviewer 使用，而不是只靠 fixture bundle。

人工 review 仍然必须保留为强制默认。

### 6. 平台化 / SaaS 承诺仍然过早

项目现在已经有早期 tenant、quota、governance、cost、audit、retention、deletion 表面能力。

这不等于多租户 SaaS 就绪。

在宣称 SaaS 前，需要真实验证：

- artifact、job、review task、publication、metric、cost record 的 tenant isolation。
- role 与 API authorization。
- 真实使用下的 quota 行为。
- 按 run、skill、provider call、tenant、accepted package 计量的 cost ledger。
- audit、retention、deletion 行为。
- operator console 或等价的日常运营流。

这些应留到受控外部 Beta 证据达标之后。

### 7. 文档复杂度本身已经成为产品风险

当前实际文档树仍是：

- `docs/current/`
- `docs/history/`

团队讨论过的目标分层是：

- `docs/latest/`：最新已发布使用手册层。
- `docs/working/`：当前迭代层。
- `docs/releases/`：发布层。
- `docs/archive/`：归档层。

本评估支持这个拆分。

原因：

- 当前 docs 混合了当前事实、历史 baseline、发布证据、长任务日志和产品上线计划。
- 这会放大 `GO`/`HOLD` 的理解成本。
- 也会让“唯一真实下一步”变得不清晰。

文档结构迁移应作为单独的文档重组任务处理，不应和本评估混在一起。

## 对受控试运行而言不是阻断项的内容

以下内容不应阻断受控试运行继续推进：

- 没有完整 SaaS console。
- 没有 Qdrant 或生产向量检索。
- 没有分布式 worker 基础设施。
- 没有全自动发布。
- 没有广义公开 benchmark。

这些是真实产品/平台缺口，但不是下一步受控试运行证明的前置条件。

## 建议下一步

冻结广义功能扩张，优先补真实证据。

执行一次真实受控试运行证据冲刺：

1. 收集至少 `10` 个真实完整闭环。
2. 覆盖至少 `4` 种模态，优先 `text`、`audio`、`image`、`video`。
3. 每个真实输入必须有 source trace。
4. 每个输出必须有 human review trace。
5. 所有生成 skill 在批准前保持 `REVIEW_REQUIRED`。
6. 对批准后的 package 执行 target-agent smoke。
7. 记录 cost、latency、provider failure、reviewer decision、reviewer edit distance、incident/security counts。
8. 重新运行 `scripts/launch_gate.py`。

只有当 launch gate 到达 `READY_FOR_CONTROLLED_BETA` 后，才应讨论外部 Beta 扩张。

## 讨论立场

如果团队短期能获得真实受控试运行闭环，本项目值得继续。

如果拿不到真实用户或真实业务输入，项目应明确降级为内部 Agent Skill Compiler / dogfooding 系统，停止以 launch-track software 的方式推进。

如果目标是 SaaS，应在受控外部 Beta 证据达标后，再单独进入平台化轨道。

## 决策摘要

建议决策：

- 继续：是。
- 推倒重写：否。
- 现在扩张平台功能：否。
- 现在推外部 Beta：否。
- 现在推 SaaS：否。
- 立即重点：为 Agent Skill Compiler 受控试运行补真实证据。
