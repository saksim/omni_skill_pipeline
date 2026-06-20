# 项目能力与目标达成度评审

> 日期：2026-06-20  
> 范围：基于 README、docs/latest、docs/working/status、代码实现、launch gate、coverage 与 pytest 结果，对当前项目“能做到什么程度”和“宣称目标达成情况”进行评审。  
> 结论类型：工程/产品 readiness 评审，不替代后续真实业务试运行证据。

## 一句话结论

当前项目已经能作为“内部 dogfood / 受控试运行级 Agent Skill Compiler”使用：多模态输入、V2 语义层、CLI/API/Worker、review queue、发布包、质量门禁和回归测试都比较完整；但还不能诚实宣称“外部 Beta / GA / 多租户 SaaS / 生产部署就绪”。核心缺口不是代码跑不起来，而是真实业务闭环证据不足。

## 当前验证结果

| 验证项 | 结果 | 评审解读 |
| --- | --- | --- |
| `python scripts\launch_gate.py --output - --summary-output - --max-evidence-age-hours 0 --print-json` | `HOLD`，16 项检查 15 过 1 失败 | 产品上线 readiness 未达标，唯一阻断项是 `trial_loop_volume_and_modality_coverage` |
| launch-gate-eligible real complete loops | `0/10` | 没有达到受控外部 Beta 所需真实闭环数量 |
| launch-gate-eligible real modalities | `0/4` | 没有达到受控外部 Beta 所需真实模态覆盖 |
| 完整 pytest | `816 passed, 3 skipped, 1 warning, 2 subtests passed` | 工程回归状态强 |
| coverage.xml | line coverage `81.18%`，branch coverage `61.37%` | 代码覆盖率有基础，但外部 provider/media 边界仍需真实环境验证 |
| internal dogfood readiness | `READY_FOR_INTERNAL_DOGFOOD` | 内部 dogfood 可宣称 |
| internal dogfood API smoke | `PASS` | 内部 API 路径可用 |
| container smoke baseline | `FAIL`，失败在 Docker base image pull/build | Docker/生产部署链路不能作为已完成承诺 |

## 目标达成度总表

| 宣称/目标 | 当前做到程度 | 已做到的证据 | 没做到/限制 | 结论 |
| --- | ---: | --- | --- | --- |
| 把文本、音频、图像、视频、表格和混合语料蒸馏成 `SKILL.md`、`skill.json`、`SkillGraph`、publication manifest、agent skill package | 高 | README 主目标明确；代码有 adapters、`SkillGraph`、publication、exporter；完整 pytest 通过 | 输出质量仍依赖 review；真实业务样本不足 | 可以作为内部 Agent Skill Compiler |
| 多模态入口 | 高 | 文档和代码均覆盖 text/audio/image/video/tabular | 音频、图像、视频依赖 OpenAI、Tesseract、FFmpeg；外部环境稳定性未完全证明 | 工程可用，生产依赖需再验证 |
| V2 语义层：`Corpus`、`EvidenceNode`、`SemanticAtom`、`SkillGraph`、`Publication` | 中高 | `models.py` 与 service 主链已落地 | V2 文档承认状态机真实落地只到 `PERSISTED`，不是完整 `PUBLISHED/REJECTED` 生命周期 | 语义层已成型，生命周期未完全闭环 |
| CLI/API/Worker 三入口 | 高 | CLI/API/Worker 均有入口和测试；代表性测试与完整测试通过 | 没有完整产品 UI；worker 是本地任务消费形态 | 内部操作可用 |
| Review queue / reviewer packet / review policy | 中高 | 支持 list/claim/close/decision；review policy 有阈值；reviewer packet 有实现 | 真实 reviewer 使用、edit distance、修订后 approval rate 仍缺真实证据 | 流程有了，产品化证明不足 |
| 内部 dogfood | 高 | internal readiness 为 `READY_FOR_INTERNAL_DOGFOOD`；API smoke `PASS` | 只能代表内部，不是外部 Beta/GA/SaaS | 可以宣称内部 dogfood ready |
| 外部受控 Beta | 低 | release switch、doc sync、ops readiness 多数通过 | launch gate 仍 `HOLD`；真实闭环 `0/10`、真实模态 `0/4` | 不能宣称外部 Beta ready |
| 单团队 GA / 持续生产工作流 | 低 | 有 release、测试、ops runbook 基础 | 缺真实负载、真实样本、长期质量/成本/故障率、agent 使用成功率证据 | 不能宣称 GA |
| 多租户 SaaS / 平台化 | 低 | 有 tenant/governance/cost/retention/deletion 的早期表面能力 | 缺真实 tenant isolation、role/API 授权、quota、cost ledger、operator console 验证 | 不能宣称 SaaS |
| Postgres / dual-write | 中 | `PostgresRepository`、`DualWriteArtifactRepository` 存在；环境变量支持 `postgres`/`dual_write` | 默认仍是 file repository；需要 DSN；不等于生产数据库体系完成 | 有基础实现，不是默认生产形态 |
| pgvector / Qdrant 检索 | 很低 | 有统一接口 | 文档和代码明确是 placeholder，会抛 `BackendNotReadyError` | 不能宣称向量检索已落地 |
| Docker / 生产部署链路 | 低 | 有 Dockerfile、runbook、container smoke 脚本 | container smoke 基线为 `FAIL`；README 也说 Docker/K8s/Vault/KMS 不属当前完成边界 | 不能宣称生产部署 ready |
| Agent-native 真实使用 | 偏低 | agent smoke 记录 `1/1 passed` | 样本太少；真实 target-agent 重复使用没有被证明 | 包格式可用，真实使用证据薄 |
| 文档/证据治理 | 中 | 文档已分层为 latest/working/releases/archive | 仍有旧 `docs/current`/`docs/history` 引用、缺失 release-switch report 路径等证据卫生问题 | 可内部用，对外口径需清理 |

## 可以宣称与不能宣称

| 可以诚实宣称 | 不该宣称 |
| --- | --- |
| 这是一个内部 dogfood 可用的多模态 Agent Skill Compiler | 外部 Beta 已 ready |
| 工程回归状态强，完整 pytest 当前通过 | GA / 生产工作流已验证 |
| 支持把多模态材料转成可审核、可追溯的 skill 工件 | 多租户 SaaS 已就绪 |
| review queue、质量评分、发布包和治理账本已有基础实现 | 全自动技能发布器已可靠 |
| Postgres/dual-write 有适配基础 | pgvector/Qdrant、Docker/K8s/Vault/KMS 生产链路已完成 |

## 主要卡点

| 卡点 | 严重度 | 影响 | 建议动作 |
| --- | --- | --- | --- |
| 真实业务闭环证据不足 | P0 | 阻断外部受控 Beta | 收集至少 10 个真实完整闭环，覆盖至少 4 种模态 |
| 真实 agent 使用证据太薄 | P1 | 无法证明 agent-native package 在真实工作流中稳定有用 | 扩大 target-agent smoke 样本，记录成功率、失败原因和人工修订 |
| Review 流程缺真实 reviewer 运营数据 | P1 | 无法证明质量门禁能稳定转化为发布质量 | 记录 reviewer decision、edit distance、一轮修订后 approval rate |
| Docker/生产化链路未完成 | P1 | 不能作为生产部署承诺 | 修复 container smoke，补 Docker/K8s/Vault/KMS/key rotation 证据 |
| 文档证据索引有历史路径残留 | P2 | 增加 GO/HOLD 解读成本 | 清理旧 `docs/current`/`docs/history` 引用，统一到 current docs 分层 |
| pgvector/Qdrant 仍是 placeholder | P2 | 不能支持生产级向量检索宣称 | 在需要检索扩展时单独推进 DDL、索引、写入和召回验证 |

## 后续建议

| 优先级 | 建议 | 验收方式 |
| --- | --- | --- |
| P0 | 冻结广义功能扩张，优先补真实 launch-gate-eligible 业务闭环 | `launch_gate.py` 达到 `READY_FOR_CONTROLLED_BETA` |
| P0 | 每个真实输入必须包含 source trace 和 human review trace | trial metrics 中 missing trace 为 0，且 real loop count 达标 |
| P1 | 扩大 agent smoke 样本，覆盖 Codex / Claude Code / OpenCode 目标场景 | agent smoke success rate 达到阈值，失败样本有分类 |
| P1 | 将 reviewer feedback 转成 calibration / remediation 证据 | reviewer edit distance、approval rate、reason codes 可统计 |
| P1 | 修复 container smoke 与生产依赖文档 | container smoke `PASS`，生产 runbook 与实际命令一致 |
| P2 | 清理历史路径和证据索引漂移 | doc sync 和 operations readiness 不再引用不存在的旧路径 |

## 评审边界

本报告认可当前项目继续推进，不建议推倒重写。正确短期定位是 Agent Skill Compiler 的受控试运行；如果短期拿不到真实用户或真实业务输入，应降级为内部 dogfood 系统，停止按外部 launch-track software 推进。若未来目标是 SaaS，应在受控外部 Beta 证据达标后，再单独进入平台化轨道。

## 本次评审过程中的注意事项

完整 pytest 会触发若干 `docs/working/status/baselines/real-trial-loop-collection/` 下 generated timestamp 与临时路径类基线差异。评审时未回滚这些文件，因为评审开始前工作区已存在改动，不能确认哪些变更属于用户已有工作。
