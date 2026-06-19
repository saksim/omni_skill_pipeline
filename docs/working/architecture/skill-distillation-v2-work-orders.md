# Skill Distillation V2 Work Orders

## 判词

本文件把 `E1` 及之后的全部开发工作压成可直接下发给 `gpt-5.3-codex` 的施工任务单。若 [skill-distillation-v2-implementation-backlog.md](skill-distillation-v2-implementation-backlog.md) 是总台账，此文件就是逐包开斩的作战排程。

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
- docs/latest/architecture/skill-distillation-v2.md
- docs/working/architecture/skill-distillation-v2-roadmap.md
- docs/working/architecture/skill-distillation-v2-implementation-backlog.md
- docs/working/architecture/skill-distillation-v2-work-orders.md

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
| `TP-E1-03` | E1 | 增加 schema v2 草案 | `src/omni_skill_pipeline/schema.py`, `docs/latest/contracts/` | `TP-E1-01` | schema 校验测试 | 至少落一份 `skill-graph` 结构 contract，并与 dataclass 字段对齐 |

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
| `TP-E11-03` | E11 | 质量回归测试 | `tests/`, `docs/working/status/baselines/` | `TP-E7-01` | 基线回归脚本 | 能对比 `traceability` 与 `reviewer_edit_distance` |
| `TP-E11-04` | E11 | 性能与成本基线 | `tests/`, `docs/working/status/baselines/` | `TP-E8-03` | perf/成本记录 | 记录耗时、token、provider 调用次数 |
| `TP-E12-01` | E12 | 结构化日志与 trace id | `src/omni_skill_pipeline/service.py`, `src/omni_skill_pipeline/worker.py` | `TP-E7-01` | logging 测试 | 一次蒸馏可追踪 asset -> graph -> publication |
| `TP-E12-02` | E12 | provider 调用审计 | `src/omni_skill_pipeline/service.py`, `src/omni_skill_pipeline/providers/` | `TP-E12-01` | audit 测试 | 能按 corpus 查看 provider footprint |
| `TP-E12-03` | E12 | 安全与敏感信息控制 | `src/omni_skill_pipeline/service.py`, `src/omni_skill_pipeline/repository.py` | `TP-E12-01` | redaction 测试 | token/secret/credential 不落盘 |
| `TP-E12-04` | E12 | 临时工件治理 | `src/omni_skill_pipeline/adapters/video.py`, `src/omni_skill_pipeline/providers/media.py` | `TP-E12-01` | temp cleanup 测试 | `.tmp_omni_media/` 有清理与失败回收策略 |
| `TP-E13-01` | E13 | 文档持续同步 | `README.md`, `docs/` | 全程 | doc sync 检查 | 对外文档与代码一致 |
| `TP-E13-02` | E13 | V1 -> V2 迁移指南 | `docs/latest/architecture/`, `docs/latest/operations/` | `TP-E8-03`, `TP-E10-02` | 文档审阅 | 迁移步骤、回退策略、风险齐全 |
| `TP-E13-03` | E13 | 发布与切换标准 | `docs/working/status/`, `docs/archive/` | `TP-E9-03`, `TP-E11-03` | 发布审查 | 明确何时 V2 可成为主链 |
| `TP-E13-04` | E13 | Linux validation suite | `scripts/linux_validate.py`, `tests/test_linux_validation_suite_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-03` | script smoke tests | Linux orchestrates CI, container smoke, doc sync, quality, perf, and Postgres validation stages |
| `TP-E13-05` | E13 | Postgres soak validation | `scripts/pg_soak.py`, `tests/test_postgres_soak_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-04` | script smoke tests | Linux orchestrates TP regression, review queue, and dual-write benchmark soak stages |
| `TP-E13-06` | E13 | Worker GA validation | `scripts/worker_ga.py`, `tests/test_worker_ga_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-04` | script smoke tests | Linux validates worker corpus, retry, idempotency, claim-lock, and task-type hardening |
| `TP-E13-07` | E13 | Provider GA validation | `scripts/provider_ga.py`, `tests/test_provider_ga_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-04` | script smoke tests | Linux validates provider retry, circuit breaker, failure budget, config, audit, and footprint hardening |
| `TP-E13-08` | E13 | Review queue GA validation | `scripts/ga_review_queue.py`, `tests/test_review_queue_ga_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-04` | script smoke tests | Linux validates review queue repository, service, API, feedback, and consumer hardening |
| `TP-E13-09` | E13 | Calibration GA validation | `scripts/ga_calibration.py`, `tests/test_calibration_ga_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-04` | script smoke tests | Linux validates calibration contract, review policy contract, and calibration report stages |
| `TP-E13-10` | E13 | Postgres GA validation | `scripts/pg_ga.py`, `tests/test_postgres_ga_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-05` | script smoke tests | Linux validates Postgres repository, dual-write contract, integration, and benchmark stages |
| `TP-E13-11` | E13 | Roadmap extension validation | `scripts/roadmap_ext.py`, `tests/test_roadmap_extension_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-04` | script smoke tests | Linux validates retrieval, lifecycle, publication, and review queue surface roadmap extensions |

## 5. 近战优先级

魔尊若要最快开工，直接按以下顺序下发：

1. `TP-E1-01`
2. `TP-E1-02`
3. `TP-E3-01`
4. `TP-E5-01`
5. `TP-E6-01`

这是最小骨架五连斩。若连这五刀都未落下，后续 provider、review、PG、检索全都会继续搭在旧 V1 的薄骨上。
| `TP-E13-12` | E13 | Release gate 聚合脚本 | `scripts/release_gate.py`, `tests/test_release_gate_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-11` | 脚本 smoke 测试 | Linux 可一条命令执行 beta/ga/roadmap gate 编排，并透传 coverage/container/postgres/calibration 参数 |
| `TP-E13-13` | E13 | Release switch 判定脚本 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-12` | 脚本 smoke 测试 | Linux 可一条命令执行 release-gate + TP 合同 + doc-sync 并输出 `GO/HOLD` 判定 JSON |
| `TP-E13-14` | E13 | Release switch 证据闭环加固 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-13` | 脚本 smoke 测试 | Linux 判定必须校验 release-gate/beta/ga/roadmap 证据包完整性，缺一即 HOLD |
| `TP-E13-15` | E13 | Release switch 证据时效门禁 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-14` | 脚本 smoke 测试 | Linux 判定默认要求证据文件在 freshness 窗口内，过期即 HOLD，支持 `--max-evidence-age-hours 0` 关闭门禁 |
| `TP-E13-16` | E13 | Release switch 未来时间偏移门禁 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-15` | 脚本 smoke 测试 | Linux 判定默认要求证据文件未来偏移不超过阈值，超限即 HOLD，支持 `--max-evidence-future-skew-hours 0` 关闭门禁 |
| `TP-E13-17` | E13 | Release switch 证据批次一致性门禁 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-16` | 脚本 smoke 测试 | Linux 判定默认要求证据文件时间分布落在同一批次窗口，超出 cohort skew 阈值即 HOLD，支持 `--max-evidence-cohort-skew-hours 0` 关闭门禁 |
| `TP-E13-18` | E13 | Release switch 证据绑定一致性门禁 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-17` | 脚本 smoke 测试 | Linux 判定默认要求 release-gate/beta/ga/roadmap 的证据绑定一致，错配即 HOLD |
| `TP-E13-19` | E13 | Release switch stage 合同一致性门禁 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-18` | 脚本 smoke 测试 | Linux 判定默认要求 release-gate stage 命令持续符合 linux-suite 合同 |
| `TP-E13-20` | E13 | Release switch 参数覆盖歧义门禁 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-19` | 脚本 smoke 测试 | Linux 判定默认要求关键参数不重复出现，重复即 HOLD |
| `TP-E13-21` | E13 | Release switch 宽松开关绕过门禁 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-20` | 脚本 smoke 测试 | Linux 判定默认阻断 `--allow-regression/--no-coverage` 等宽松开关 |
| `TP-E13-22` | E13 | Release switch dry-run 绕过门禁 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-21` | 脚本 smoke 测试 | Linux 判定默认阻断 release-gate stage 命令里的 `--dry-run` |
| `TP-E13-23` | E13 | Release switch 脚本定位伪装门禁 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-22` | 脚本 smoke 测试 | Linux 判定默认要求 stage 首个 script token 正确指向 linux validation suite |
| `TP-E13-24` | E13 | Release switch inline-exec 绕过门禁 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-23` | 脚本 smoke 测试 | Linux 判定默认阻断 `-c/-m/-` inline dispatch 绕过 |
| `TP-E13-25` | E13 | Release switch 脚本路径锚定门禁 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-24` | 脚本 smoke 测试 | Linux 判定默认要求脚本解析路径锚定仓库内 canonical suite |
| `TP-E13-26` | E13 | Release switch Python 绑定一致性门禁 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-25` | 脚本 smoke 测试 | Linux 判定默认要求 `--python` 与实际 launcher 严格绑定一致 |
| `TP-E13-27` | E13 | Release switch 覆盖率阈值绑定门禁 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-26` | 脚本 smoke 测试 | Linux 判定默认要求 coverage floor 绑定且不低于 50 |
| `TP-E13-28` | E13 | Release switch Python 优化旗标门禁 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-27` | 脚本 smoke 测试 | Linux 判定默认阻断 launcher 侧 `-O/-OO` |
| `TP-E13-29` | E13 | Release switch Python 传递链优化旗标门禁 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-28` | 脚本 smoke 测试 | Linux 判定默认阻断 `--python` 传递值中的 `-O/-OO` |
| `TP-E13-30` | E13 | Release switch PYTHONOPTIMIZE 环境变量门禁 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-29` | 脚本 smoke 测试 | Linux 判定默认阻断 `PYTHONOPTIMIZE=*` |
| `TP-E13-31` | E13 | Release switch Python 传递链 inline-exec 门禁 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-30` | 脚本 smoke 测试 | Linux 判定默认阻断 `--python` 传递链中的 inline dispatch |
| `TP-E13-32` | E13 | Release switch PYTHONPATH 环境变量门禁 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-31` | 脚本 smoke 测试 | Linux 判定默认阻断 `PYTHONPATH=*` |
| `TP-E13-33` | E13 | Release switch PYTHONHOME 环境变量门禁 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-32` | 脚本 smoke 测试 | Linux 判定默认阻断 `PYTHONHOME=*` |
| `TP-E13-34` | E13 | Release switch PYTHONUSERBASE 环境变量门禁 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-33` | 脚本 smoke 测试 | Linux 判定默认阻断 `PYTHONUSERBASE=*` |
| `TP-E13-35` | E13 | Release switch PYTHONBREAKPOINT 环境变量门禁 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-34` | 脚本 smoke 测试 | Linux 判定默认阻断 `PYTHONBREAKPOINT=*` |
| `TP-E13-36` | E13 | Release switch PYTHONSTARTUP 环境变量门禁 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-35` | 脚本 smoke 测试 | Linux 判定默认阻断 `PYTHONSTARTUP=*` |
| `TP-E13-37` | E13 | Release switch PYTHONINSPECT 环境变量门禁 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-36` | 脚本 smoke 测试 | Linux 判定默认阻断 `PYTHONINSPECT=*` |
| `TP-E13-38` | E13 | Release switch PYTHONWARNINGS 环境变量门禁 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-37` | 脚本 smoke 测试 | Linux 判定默认阻断 `PYTHONWARNINGS=*` |
| `TP-E13-39` | E13 | Release switch 未登记 PYTHON* 环境变量门禁 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-38` | 脚本 smoke 测试 | Linux 判定默认阻断未知 `PYTHON*` 环境变量 |
| `TP-E13-40` | E13 | Release switch PATH 环境变量门禁 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-39` | 脚本 smoke 测试 | Linux 判定默认阻断 `PATH=*` 注入 |
| `TP-E13-41` | E13 | Release switch LD_PRELOAD 环境变量门禁 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-40` | 脚本 smoke 测试 | Linux 判定默认阻断 `LD_PRELOAD=*` |
| `TP-E13-42` | E13 | Release switch LD_LIBRARY_PATH 环境变量门禁 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-41` | 脚本 smoke 测试 | Linux 判定默认阻断 `LD_LIBRARY_PATH=*` |
| `TP-E13-43` | E13 | Release switch LD_AUDIT 环境变量门禁 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-42` | 脚本 smoke 测试 | Linux 判定默认阻断 `LD_AUDIT=*` |
| `TP-E13-44` | E13 | Release switch 未登记 LD_* 环境变量门禁 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-43` | 脚本 smoke 测试 | Linux 判定默认阻断未知 `LD_*` 环境变量 |
| `TP-E13-45` | E13 | Release switch GLIBC_TUNABLES 环境变量门禁 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-44` | 脚本 smoke 测试 | Linux 判定默认阻断 `GLIBC_TUNABLES=*` |
| `TP-E13-46` | E13 | Release switch 未登记 GLIBC_* 环境变量门禁 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-45` | 脚本 smoke 测试 | Linux 判定默认阻断未知 `GLIBC_*` 环境变量 |
| `TP-E13-47` | E13 | Release switch 未登记 MALLOC_* 环境变量门禁 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-46` | 脚本 smoke 测试 | Linux 判定默认阻断未知 `MALLOC_*` 环境变量 |
| `TP-E13-48` | E13 | Release switch MALLOC_TRACE 环境变量门禁 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-47` | 脚本 smoke 测试 | Linux 判定默认阻断 `MALLOC_TRACE=*` |
| `TP-E13-49` | E13 | Release switch MALLOC_CHECK_ 环境变量门禁 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-48` | 脚本 smoke 测试 | Linux 判定默认阻断 `MALLOC_CHECK_=*` |
| `TP-E13-50` | E13 | Release switch MALLOC_PERTURB_ 环境变量门禁 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-49` | 脚本 smoke 测试 | Linux 判定默认阻断 `MALLOC_PERTURB_=*` |
| `TP-E13-51` | E13 | Release switch MALLOC_ARENA_MAX 环境变量门禁 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-50` | 脚本 smoke 测试 | Linux 判定默认阻断 `MALLOC_ARENA_MAX=*` |
| `TP-E13-52` | E13 | Release switch MALLOC_MMAP_THRESHOLD_ 环境变量门禁 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-51` | 脚本 smoke 测试 | Linux 判定默认阻断 `MALLOC_MMAP_THRESHOLD_=*` |
| `TP-E13-53` | E13 | Release switch MALLOC_MMAP_MAX_ 环境变量门禁 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-52` | 脚本 smoke 测试 | Linux 判定默认阻断 `MALLOC_MMAP_MAX_=*` |
| `TP-E13-54` | E13 | Release switch MALLOC_TOP_PAD_ 环境变量门禁 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-53` | 脚本 smoke 测试 | Linux 判定默认阻断 `MALLOC_TOP_PAD_=*` |
| `TP-E13-55` | E13 | Release switch MALLOC_TRIM_THRESHOLD_ 环境变量门禁 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-54` | 脚本 smoke 测试 | Linux 判定默认阻断 `MALLOC_TRIM_THRESHOLD_=*` |
| `TP-E13-56` | E13 | Release switch MALLOC_ARENA_TEST 环境变量门禁 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-55` | 脚本 smoke 测试 | Linux 判定默认阻断 `MALLOC_ARENA_TEST=*` |
| `TP-E13-57` | E13 | Release switch MALLOC_PER_THREAD 环境变量门禁 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-56` | 脚本 smoke 测试 | Linux 判定默认阻断 `MALLOC_PER_THREAD=*` |
| `TP-E13-58` | E13 | Release switch 决策 JSON 批量测算视图 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-57` | 脚本 smoke 测试 | Linux 判定输出 `bulk_strategy_view` 固定骨架，兼容既有消费者 |
| `TP-E13-59` | E13 | Release switch 批量测算域聚合签名 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-58` | 脚本 smoke 测试 | Linux 判定输出 domain rollup、hold signature 与 gate index 向量 |
| `TP-E13-60` | E13 | Release switch 批量测算签名哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-59` | 脚本 smoke 测试 | Linux 判定输出 `hold_signature_sha256/strategy_signature_sha256` 固定宽度签名 |
| `TP-E13-61` | E13 | Release switch 批量测算域聚合哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-60` | 脚本 smoke 测试 | Linux 判定输出 `domain_rollup_sha256` 固定宽度签名 |
| `TP-E13-62` | E13 | Release switch 批量测算证据轮廓哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-61` | 脚本 smoke 测试 | Linux 判定输出 `evidence_profile_sha256` 固定宽度签名 |
| `TP-E13-63` | E13 | Release switch 批量测算门阵索引哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-62` | 脚本 smoke 测试 | Linux 判定输出 `gate_status_index_sha256` 固定宽度签名 |
| `TP-E13-64` | E13 | Release switch 批量测算组合轮廓哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-63` | 脚本 smoke 测试 | Linux 判定输出 `composite_profile_sha256`，支持高并发分桶去重与回放 |
| `TP-E13-65` | E13 | Release switch 批量测算策略包络哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-64` | 脚本 smoke 测试 | Linux 判定输出 `strategy_envelope_sha256`，支持跨批次快速对账与去重 |
| `TP-E13-66` | E13 | Release switch 批量测算合同签名哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-65` | 脚本 smoke 测试 | Linux 判定输出 `contract_signature_sha256`，支持合同漂移检测与对账 |
| `TP-E13-67` | E13 | Release switch 批量测算合同包络哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-66` | 脚本 smoke 测试 | Linux 判定输出 `contract_envelope_sha256`，支持合同+姿态对账与去重 |
| `TP-E13-68` | E13 | Release switch 批量测算发布指纹哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-67` | 脚本 smoke 测试 | Linux 判定输出 `release_fingerprint_sha256`，支持一键发布对账与去重 |
| `TP-E13-69` | E13 | Release switch 批量测算发布清单哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-68` | 脚本 smoke 测试 | Linux 判定输出 `release_manifest_sha256`，支持发布面回放对账与去重 |
| `TP-E13-70` | E13 | Release switch 批量测算发布根签名哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-69` | 脚本 smoke 测试 | Linux 判定输出 `release_root_sha256`，支持快速对账、去重与回放 |
| `TP-E13-71` | E13 | Release switch 批量测算发布见证哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-70` | 脚本 smoke 测试 | Linux 判定输出 `release_attestation_sha256`，支持验签、对账与追踪 |
| `TP-E13-72` | E13 | Release switch 批量测算发布裁决哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-71` | 脚本 smoke 测试 | Linux 判定输出 `release_verdict_sha256`，支持一键对账与去重 |
| `TP-E13-73` | E13 | Release switch 批量测算发布谱系哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-72` | 脚本 smoke 测试 | Linux 判定输出 `release_lineage_sha256`，支持链路回放、对账与去重 |
| `TP-E13-74` | E13 | Release switch 批量测算发布胶囊哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-73` | 脚本 smoke 测试 | Linux 判定输出 `release_capsule_sha256`，支持快速对账、分桶与去重 |
| `TP-E13-75` | E13 | Release switch 批量测算发布锚点哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-74` | 脚本 smoke 测试 | Linux 判定输出 `release_anchor_sha256`，支持极速对账、分桶与去重 |
| `TP-E13-76` | E13 | Release switch 批量测算发布信标哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-75` | 脚本 smoke 测试 | Linux 判定输出 `release_beacon_sha256`，支持极速路由、对账与去重 |
| `TP-E13-77` | E13 | Release switch 批量测算发布星图哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-76` | 脚本 smoke 测试 | Linux 判定输出 `release_constellation_sha256`，支持极速路由、对账与回放 |
| `TP-E13-78` | E13 | Release switch 批量测算发布星系哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-77` | 脚本 smoke 测试 | Linux 判定输出 `release_galaxy_sha256`，支持极速路由、对账与回放 |
| `TP-E13-79` | E13 | Release switch 批量测算发布宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-78` | 脚本 smoke 测试 | Linux 判定输出 `release_universe_sha256`，支持极速路由、对账与去重 |
| `TP-E13-80` | E13 | Release switch 批量测算发布多元宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-79` | 脚本 smoke 测试 | Linux 判定输出 `release_multiverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-81` | E13 | Release switch 批量测算发布超宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-80` | 脚本 smoke 测试 | Linux 判定输出 `release_omniverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-82` | E13 | Release switch 批量测算发布极宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-81` | 脚本 smoke 测试 | Linux 判定输出 `release_hyperverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-83` | E13 | Release switch 批量测算发布巨宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-82` | 脚本 smoke 测试 | Linux 判定输出 `release_megaverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-84` | E13 | Release switch 批量测算发布十亿宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-83` | 脚本 smoke 测试 | Linux 判定输出 `release_gigaverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-85` | E13 | Release switch 批量测算发布万亿宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-84` | 脚本 smoke 测试 | Linux 判定输出 `release_teraverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-86` | E13 | Release switch 批量测算发布千万亿宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-85` | 脚本 smoke 测试 | Linux 判定输出 `release_petaverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-87` | E13 | Release switch 批量测算发布百京宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-86` | 脚本 smoke 测试 | Linux 判定输出 `release_exaverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-88` | E13 | Release switch 批量测算发布十垓宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-87` | 脚本 smoke 测试 | Linux 判定输出 `release_zettaverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-89` | E13 | Release switch 批量测算发布秭宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-88` | 脚本 smoke 测试 | Linux 判定输出 `release_yottaverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-90` | E13 | Release switch 批量测算发布罗纳宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-89` | 脚本 smoke 测试 | Linux 判定输出 `release_ronnaverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-91` | E13 | Release switch 批量测算发布昆塔宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-90` | 脚本 smoke 测试 | Linux 判定输出 `release_quettaverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-92` | E13 | Release switch 批量测算发布极巅宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-91` | 脚本 smoke 测试 | Linux 判定输出 `release_apexverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-93` | E13 | Release switch 批量测算发布终极宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-92` | 脚本 smoke 测试 | Linux 判定输出 `release_ultimaverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-94` | E13 | Release switch 批量测算发布超越宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-93` | 脚本 smoke 测试 | Linux 判定输出 `release_transcendaverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-95` | E13 | Release switch 批量测算发布无限宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-94` | 脚本 smoke 测试 | Linux 判定输出 `release_infinitaverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-96` | E13 | Release switch 批量测算发布永恒宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-95` | 脚本 smoke 测试 | Linux 判定输出 `release_eternaverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-97` | E13 | Release switch 批量测算发布永序宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-96` | 脚本 smoke 测试 | Linux 判定输出 `release_timelessverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-98` | E13 | Release switch 批量测算发布纪元宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-97` | 脚本 smoke 测试 | Linux 判定输出 `release_aeonverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-99` | E13 | Release switch 批量测算发布世代宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-98` | 脚本 smoke 测试 | Linux 判定输出 `release_epochverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-100` | E13 | Release switch 批量测算发布元宇宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-99` | 脚本 smoke 测试 | Linux 判定输出 `release_eraverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-101` | E13 | Release switch 批量测算发布超元宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-100` | 脚本 smoke 测试 | Linux 判定输出 `release_metaverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-102` | E13 | Release switch 批量测算发布平行宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-101` | 脚本 smoke 测试 | Linux 判定输出 `release_paraverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-103` | E13 | Release switch 批量测算发布多维宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-102` | 脚本 smoke 测试 | Linux 判定输出 `release_polyverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-104` | E13 | Release switch 批量测算发布泛宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-103` | 脚本 smoke 测试 | Linux 判定输出 `release_panverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-105` | E13 | Release switch 批量测算发布全息宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-104` | 脚本 smoke 测试 | Linux 判定输出 `release_holoverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-106` | E13 | Release switch 批量测算发布新宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-105` | 脚本 smoke 测试 | Linux 判定输出 `release_neoverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-107` | E13 | Release switch 批量测算发布新星宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-106` | 脚本 smoke 测试 | Linux 判定输出 `release_novaverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-108` | E13 | Release switch 批量测算发布超新星宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-107` | 脚本 smoke 测试 | Linux 判定输出 `release_supernovaverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-109` | E13 | Release switch 批量测算发布超极新星宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-108` | 脚本 smoke 测试 | Linux 判定输出 `release_hypernovaverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-110` | E13 | Release switch 批量测算发布极耀新星宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-109` | 脚本 smoke 测试 | Linux 判定输出 `release_ultranovaverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-111` | E13 | Release switch 批量测算发布终耀新星宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-110` | 脚本 smoke 测试 | Linux 判定输出 `release_omeganovaverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-112` | E13 | Release switch 批量测算发布始耀新星宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-111` | 脚本 smoke 测试 | Linux 判定输出 `release_alphanovaverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-113` | E13 | Release switch 批量测算发布次耀新星宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-112` | 脚本 smoke 测试 | Linux 判定输出 `release_betanovaverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-114` | E13 | Release switch 批量测算发布叁耀新星宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-113` | 脚本 smoke 测试 | Linux 判定输出 `release_gammanovaverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-115` | E13 | Release switch 批量测算发布肆耀新星宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switchValidation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-114` | 脚本 smoke 测试 | Linux 判定输出 `release_deltanovaverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-116` | E13 | Release switch 批量测算发布伍耀新星宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-115` | 脚本 smoke 测试 | Linux 判定输出 `release_epsilonnovaverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-117` | E13 | Release switch 批量测算发布陆耀新星宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-116` | 脚本 smoke 测试 | Linux 判定输出 `release_zetanovaverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-118` | E13 | Release switch 批量测算发布柒耀新星宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-117` | 脚本 smoke 测试 | Linux 判定输出 `release_etanovaverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-119` | E13 | Release switch 批量测算发布捌耀新星宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-118` | 脚本 smoke 测试 | Linux 判定输出 `release_thetanovaverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-120` | E13 | Release switch 批量测算发布玖耀新星宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-119` | 脚本 smoke 测试 | Linux 判定输出 `release_iotanovaverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-121` | E13 | Release switch 批量测算发布拾耀新星宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-120` | 脚本 smoke 测试 | Linux 判定输出 `release_kappanovaverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-122` | E13 | Release switch 批量测算发布拾壹耀新星宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-121` | 脚本 smoke 测试 | Linux 判定输出 `release_lambdanovaverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-123` | E13 | Release switch 批量测算发布拾贰耀新星宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-122` | 脚本 smoke 测试 | Linux 判定输出 `release_munovaverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-124` | E13 | Release switch 批量测算发布拾叁耀新星宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-123` | 脚本 smoke 测试 | Linux 判定输出 `release_nunovaverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-125` | E13 | Release switch 批量测算发布拾肆耀新星宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-124` | 脚本 smoke 测试 | Linux 判定输出 `release_xinovaverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-126` | E13 | Release switch 批量测算发布拾伍耀新星宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-125` | 脚本 smoke 测试 | Linux 判定输出 `release_omicronovaverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-127` | E13 | Release switch 批量测算发布拾陆耀新星宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-126` | 脚本 smoke 测试 | Linux 判定输出 `release_pinovaverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-128` | E13 | Release switch 批量测算发布拾柒耀新星宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-127` | 脚本 smoke 测试 | Linux 判定输出 `release_rhonovaverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-129` | E13 | Release switch 批量测算发布拾捌耀新星宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-128` | 脚本 smoke 测试 | Linux 判定输出 `release_sigmanovaverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-130` | E13 | Release switch 批量测算发布拾玖耀新星宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-129` | 脚本 smoke 测试 | Linux 判定输出 `release_taunovaverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-131` | E13 | Release switch 批量测算发布贰拾耀新星宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-130` | 脚本 smoke 测试 | Linux 判定输出 `release_upsilonnovaverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-132` | E13 | Release switch 批量测算发布贰拾壹耀新星宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-131` | 脚本 smoke 测试 | Linux 判定输出 `release_phinovaverse_sha256`，支持极速路由、对账与去重 |
| `TP-E13-133` | E13 | Release switch 批量测算发布贰拾贰耀新星宇宙哈希固化 | `scripts/release_switch.py`, `tests/test_release_switch_validation_script.py`, `scripts/tp_tests.py`, `docs/latest/operations/testing.md` | `TP-E13-132` | 脚本 smoke 测试 | Linux 判定输出 `release_chinovaverse_sha256`，支持极速路由、对账与去重 |

## 5. 近战优先级

魔尊若要最快开工，直接按以下顺序下发：

1. `TP-E1-01`
2. `TP-E1-02`
3. `TP-E3-01`
4. `TP-E5-01`
5. `TP-E6-01`

这是最小骨架五连斩。若连这五刀都未落下，后续 provider、review、PG、检索全都会继续搭在旧 V1 的薄骨上。
