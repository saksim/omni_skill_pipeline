# GPT5.5 后续迭代蓝图

日期：2026-06-20  
诊断依据：[项目能力与目标达成度评审 2026-06-20](../../reviews/2026-06-20-project-capability-review.md)  
施工入口：[GPT5.5 上线施工包](gpt55-launch-blueprint/README.md)

## 一句话结论

当前项目已经可以作为内部 dogfood 和受控内部玩具运行，但还不能声明外部 Beta、GA、SaaS 或生产上线。核心卡点不是代码执行能力不足，而是缺少可被发布闸门认可的真实业务闭环证据。

## 诊断基线

2026-06-20 追加决策：当前没有真实业务数据，因此上线口径选择内部 dogfood 或内部玩具。后续真实数据接入方式已经固化到 `docs/latest/operations/runbooks/real-data-intake-and-validation.md`，真实原始数据放在本地 `data/real-inputs/<batch-id>/`，仓库只提交脱敏 manifest 和验收证据。

以 2026-06-20 评估报告为准，当前状态如下：

| 领域 | 当前结论 | 关键证据 |
| --- | --- | --- |
| 内部 dogfood | 可用 | `READY_FOR_INTERNAL_DOGFOOD`，API smoke 为 `PASS` |
| 外部 Beta/GA | 不可声明 | `launch_gate.py` 判定 `HOLD` |
| 自动化测试 | 基线较稳 | 评估报告记录 `816 passed, 3 skipped` |
| 真实业务闭环 | P0 阻塞 | launch-gate-eligible real loops 为 `0/10` |
| 模态覆盖 | P0 阻塞 | launch-gate-eligible modalities 为 `0/4` |
| Docker 生产链路 | P1 阻塞 | container smoke 卡在 base image pull/build |
| 文档索引卫生 | P2 待清 | 历史路径残留需要归一 |
| 检索后端 | P2 待决 | pgvector/Qdrant 仍是占位或未来扩展 |

本轮未重新生成真实 launch gate 结果。当前执行环境的临时目录受限，`launch_gate.py` 在本会话中无法创建运行时临时文件，因此后续 GPT5.5 施工时必须在可写本地环境重新执行本文列出的验收命令。

## 范围锁定

本蓝图只定义后续施工方案，不直接补造真实业务证据，不修改 runtime 代码，不替代人工审核结论。

允许后续施工做的事：

- 收集并登记真实业务闭环证据。
- 运行现有 GL-12、GL-13、GL-31、GL-33、GL-63、GL-64 链路。
- 补齐 agent smoke、reviewer ops、trial metrics、launch gate 证据。
- 修复 Docker base image pull/build 导致的 container smoke 失败。
- 清理 live 文档索引里的历史路径残留。
- 在明确需要检索能力时补充 pgvector 或 Qdrant 的 ADR、实现和测试。

禁止后续施工绕过的事：

- 不得把 fixture、mock、template、placeholder 标记为 `launch_gate_eligible=true`。
- 不得将人工未审核产物标记为已审核。
- 不得以 Docker/K8s/Postgres/Vault/KMS 未完成为理由阻塞 P0 真实证据收集。
- 不得在没有证据的情况下改发布说明宣称外部 Beta、GA 或生产可用。

## 主从技能编排

| 阶段 | 主责 | 从责 | 产物 |
| --- | --- | --- | --- |
| 蓝图统筹 | top-engineering-orchestrator | top-engineering-router | 本蓝图和施工包 |
| 需求收敛 | top-product-strategist | top-qa | MVP、Non-goal、上线口径 |
| 架构边界 | top-architect | top-platform-architect-decision-framework | 卡点拆解、ADR 触发条件 |
| 真实证据闭环 | top-qa | top-python-dev | manifest、metrics、launch gate |
| 生产链路 | top-qa | devops, infrastructure | container smoke、release readiness |
| 检索扩展 | top-architect | top-middleware-evolutionary | pgvector/Qdrant 决策和落地 |

## 卡点总表

| 优先级 | 卡点 | 根因判断 | 解决策略 | 退出标准 |
| --- | --- | --- | --- | --- |
| P0 | 真实业务闭环 `0/10` | 现有 10 条闭环全部是 fixture，不可用于 launch gate | 按 GL-63 缺口填充 10 个真实 manifest，再跑 GL-13 和 launch gate | 至少 10 条 `evidence_origin=real`、`launch_gate_eligible=true`、`status=complete` |
| P0 | 模态覆盖 `0/4` | 真实证据未覆盖 text、audio、image、video | 先补 4 个目标模态，再补足总量 | 至少 4 个模态通过 launch gate |
| P1 | agent smoke 证据薄 | 目前多为内部样例，缺真实 agent 使用记录 | 对真实 skill 包运行 Codex、Claude Code、OpenCode smoke，失败也记录 | agent smoke 成功率达到阈值，失败原因可追踪 |
| P1 | reviewer ops 数据薄 | 审核结论、改动距离、返修数据不足 | 每条 real loop 绑定 review task、reviewer、review outcome、revision 和 edit distance | approval rate、median edit distance 通过 `trial_metrics.py` |
| P1 | Docker smoke fail | Docker CLI 和 daemon 可用，但 base image metadata 拉取失败 | 在线环境修复镜像拉取，离线环境预加载 base image 或使用内部镜像源 | `container_smoke.py` 为 `PASS` |
| P2 | 文档路径漂移 | 历史 `docs/current`、`docs/history` 路径残留在证据或索引中 | 将 live 文档指向 `latest/working/releases/archive`，历史证据只保留可追溯引用 | doc sync 和路径扫描无 live 漂移 |
| P2 | pgvector/Qdrant 占位 | 检索扩展未进入当前上线主路径 | 先冻结为 Future Track，需要时补 ADR、DDL、集成测试和召回指标 | 无占位能力对外宣称，启用前有测试和回滚 |

## 迭代路线

### S0 基线确认

目标：确认后续施工从同一张诊断图出发。

步骤：

1. 阅读本蓝图和 [施工包入口](gpt55-launch-blueprint/README.md)。
2. 阅读 2026-06-20 评估报告。
3. 执行只读基线命令，记录当前 `HOLD` 原因。
4. 不做任何功能扩展。

验收：

```powershell
python scripts\trial_metrics.py --manifest docs\working\status\baselines\controlled-trial\trial-metrics-manifest.json --print-summary --fail-on-ga-blocker
python scripts\launch_gate.py --output - --summary-output - --max-evidence-age-hours 0 --print-json
```

### S1 P0 真实闭环证据攻坚

目标：把 launch-gate-eligible real loops 从 `0/10` 拉到 `10/10`，且覆盖至少 4 个模态。

施工文档：[P0 真实业务闭环证据施工方案](gpt55-launch-blueprint/p0-real-loop-evidence.md)

验收：

- GL-64 preflight 为 `READY`。
- GL-13 生成新的 launch evidence pack。
- `launch_gate.py` 不再因为 `trial_loop_volume_and_modality_coverage` 阻塞。

### S2 P1 agent 与 reviewer 质量证据

目标：让真实闭环不仅数量达标，而且可证明被真实 agent 使用、被真实 reviewer 审核。

施工文档：[P1 Agent Smoke 与 Reviewer Ops 施工方案](gpt55-launch-blueprint/p1-agent-reviewer-quality.md)

验收：

- `agent_smoke.py` 记录覆盖真实 skill 包。
- reviewer approval、revision、edit distance 均进入 manifest。
- `trial_metrics.py --fail-on-ga-blocker` 不再因 reviewer 或 agent 质量阻塞。

### S3 Controlled Beta Gate Closure

目标：在不宣称生产可用的前提下，达到受控外部 Beta 的证据门槛。

步骤：

1. 合并 S1 和 S2 的真实 manifest。
2. 重新生成 trial metrics、launch evidence、launch gate 摘要。
3. 如果 launch gate 输出 `GO` 或等价的 Beta-ready 结论，再更新 release note。
4. 如果仍为 `HOLD`，只记录剩余 blocker，不改上线宣称。

验收命令：

```powershell
python -B scripts\gl13_launch_evidence.py --loop-manifest-dir docs\working\status\baselines\real-trial-loop-collection\manifests --strict-loop-manifest-contract --max-evidence-age-hours 0
python scripts\trial_metrics.py --manifest docs\working\status\baselines\real-trial-loop-collection\real-trial-loop-metrics-manifest.json --print-summary --fail-on-ga-blocker
python scripts\launch_gate.py --output - --summary-output - --max-evidence-age-hours 0 --print-json
```

### S4 生产链路补强

目标：把 Docker/container smoke 从当前 `FAIL` 修到 `PASS`。这条线服务于生产上线，不阻塞 S1 到 S3 的证据收集。

施工文档：[P1 Runtime 与生产链路施工方案](gpt55-launch-blueprint/p1-runtime-production-readiness.md)

验收：

- Docker image build 不再卡在 base image metadata。
- container health check 通过。
- Linux 发布脚本只在 Linux 运行机上验收。

### S5 文档与证据卫生

目标：确保人类工程师能根据中文文档直接操作，不再被历史路径和旧术语误导。

施工文档：[P2 文档索引与检索扩展施工方案](gpt55-launch-blueprint/p2-doc-index-and-retrieval.md)

验收：

- `docs/INDEX.md` 指向当前分层。
- live 文档不再把 `docs/current` 或 `docs/history` 当作当前路径。
- 历史证据中的旧路径保留时必须标明是 archive 或 historical evidence。

### S6 检索后端扩展

目标：只有在检索能力成为 Beta 或 GA 的真实需求时，才启动 pgvector/Qdrant 施工。

触发条件：

- 真实用户闭环中出现跨 skill 检索、相似案例召回或 review queue 检索需求。
- 现有文件系统或 JSON manifest 查询无法满足验收指标。

验收：

- 有 ADR。
- 有 DDL 或索引定义。
- 有 integration test。
- 有 recall 或 latency 指标。
- 有回滚方案。

## GPT5.5 交接指令

后续 GPT5.5 施工时，第一条消息可以直接使用：

```text
请以 docs/working/status/2026-06-20-gpt55-iteration-blueprint.md 为唯一诊断主线，以 docs/working/status/gpt55-launch-blueprint/*.md 为施工包。先执行 S0 基线确认，然后优先完成 P0 真实业务闭环证据施工。不得把 fixture、template、placeholder 或未审核产物标记为 launch_gate_eligible=true。每完成一个阶段，更新对应 summary，并用 launch_gate、trial_metrics、doc_sync 或 container_smoke 给出可复现验收结果。
```

## 风险与回滚

| 风险 | 处理方式 |
| --- | --- |
| 真实证据拿不到 | 保持内部 dogfood/内部玩具口径，不升级 Beta 宣称 |
| 人审记录缺失 | 该 loop 不进入 launch gate，补审后再入库 |
| agent smoke 失败 | 记录 failure code，不删除失败证据，按失败类别修复 |
| Docker 仍无法拉镜像 | 切到离线 base image 或内部镜像源，生产上线声明继续冻结 |
| 文档索引误导 | 优先修 live 索引，历史证据只做 archive 标记 |
| 检索后端引入复杂度 | 未触发真实需求前不落地中间件 |

## 完成定义

本蓝图后续落地完成，需要同时满足：

- 至少 10 条真实闭环通过 launch gate eligibility。
- 至少 4 个真实模态通过覆盖要求。
- reviewer ops 和 agent smoke 质量指标通过。
- 所有 release note 只声明已有证据支撑的能力。
- Docker/container smoke 如果仍未通过，必须明确标为生产链路未完成，不影响内部 dogfood 或证据型 controlled Beta 的边界。
- 文档索引、操作文档、施工包保持中文且可被人类工程师直接执行。
