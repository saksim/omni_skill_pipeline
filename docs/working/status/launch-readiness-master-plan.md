# Launch Readiness Master Plan

> Date: 2026-04-24
> Scope: launch-target assessment, GLM5.1 comparison, feature inventory, gap decomposition, Codex task cards
> Sources: `src/`, `tests/`, `.github/workflows/ci.yml`, `docs/archive/assessments/glm-5.1-project-assessment.md`

> 2026-05-18 status update: this document is now a historical baseline. Many L1/L2 gaps listed below have since been closed by later TP-E13 work and the latest Linux release run reached `GO`. Use [CURRENT_STATUS.md](CURRENT_STATUS.md) and [2026-05-18-controlled-business-trial-iteration.md](2026-05-18-controlled-business-trial-iteration.md) as the current execution entry.

## 判词

项目当前不是“功能没做出来”，而是“核心蒸馏链已成、生产外壳未成”。  
如果目标是单机内网试运行，已经够用；如果目标是受控外部 Beta，上线前仍有一批明确的 P0 功能点要补；如果目标是正式 GA / 多实例生产，GLM5.1 点出的多数问题都成立，只是严重度要按上线阶段重新分层。

## 1. 上线目标定义

本计划把“上线”拆成三个层级，避免把首版上线和远期演进混成一锅。

### L0：内网试运行

- 单机或单目录部署
- 本地 file artifact store
- 手工 review
- 不承诺外部 API SLA

### L1：受控外部 Beta

- 对外暴露 API 或受控客户使用 CLI
- 有基本 auth、限流、错误合同、日志、健康检查
- 有最小发布/回滚/验收流程
- 仍可接受单节点部署和 file artifact store

### L2：正式 GA / 多实例生产

- 可扩展 worker / queue 语义
- repository abstraction 或正式持久层
- 更强的可观测性、发布门禁、运行规范
- review queue / feedback 流程真正闭环

### R：路线图扩展

- 检索、生命周期合并、Qdrant / pgvector、多视图发布、Review UI
- 这些不是首版上线阻断，但必须纳入任务台账

## 2. 对 GLM5.1 评估的裁决

| GLM5.1 结论 | 吾的裁决 | 依据 | 对上线影响 |
|---|---|---|---|
| `service.py` 过重 | 成立 | `DistillationService` 集中 orchestration / publication / review / factory wiring | L2 阻断，L1 高风险 |
| 缺 `ArtifactRepository` 抽象 | 成立 | `service.py` 直接依赖 `FileArtifactRepository` | L2 阻断，L1 可暂缓 |
| API 无 auth | 成立 | `api_app.py` 无认证依赖/中间件 | L1 阻断 |
| API 无 rate limiting | 成立 | 未见限流器、budget guard | L1 阻断 |
| 缺 structured logging / trace | 成立 | 未见 logging bootstrap / request_id / trace_id | L1 阻断 |
| temp file governance 缺失 | 部分成立 | 每次视频任务会清理 work dir，但 `.tmp_omni_media/` 根目录无 retention/prune | L1 需补最小治理 |
| `.env.example` 缺失 | 已修复 | 仓内已有 `.env.example` | 非阻断 |
| 测试覆盖太弱 | 部分成立 | 主链五模态与 corpus 路径有测试，但 API 层测试缺失 | L1 需补 API tests |
| 缺 API 文档 | 不成立 | FastAPI docs 存在，仓内已有 `docs/latest/operations/api.md` | 非阻断 |
| 评分完全 heuristic | 成立 | `quality/scoring.py` 与 `review_policy.py` 仍是 static heuristic | L2 问题，L1 可接受 |
| Review feedback 不可执行 | 成立 | feedback 仅落盘，不驱动后续流水线 | L2 问题 |
| V1/V2 终态不清 | 部分成立 | 路线图清楚，但 runtime 仍走兼容桥 | L2 问题 |
| 缺 coverage gate | 成立 | CI 无 fail-under | L1 建议补齐 |
| 缺 performance benchmark | 成立 | 无基准压测或 smoke benchmark | L2 问题 |

## 3. 功能点总览

### 统计

- 总功能点：`48`
- 已完成：`16`
- 部分完成：`3`
- 欠缺：`29`

### 按上线层级看

- L0 已具备：`16/16`
- L1 受控外部 Beta 仍需补：`16` 个功能点
  - 部分完成：`2`
  - 欠缺：`14`
- L2 正式 GA 仍需补：`12` 个功能点
  - 部分完成：`1`
  - 欠缺：`11`
- R 路线图扩展：`4` 个功能点，当前均未完成

### 状态标记

- `C` = 已完成
- `P` = 部分完成
- `M` = 欠缺

## 4. 全量功能矩阵

### 4.1 蒸馏核心与多模态能力

| ID | 功能点 | 状态 | 上线级别 | 证据 / 缺口 |
|---|---|---|---|---|
| F01 | Text single-asset distill engine | C | L0 | `TextAdapter` + `tests/test_mvp.py::test_text_distillation_creates_artifacts` |
| F02 | Audio single-asset distill engine | C | L0 | `AudioAdapter` + `tests/test_mvp.py::test_audio_distillation_uses_transcriber_when_transcript_missing` |
| F03 | Image single-asset distill engine | C | L0 | `ImageAdapter` + `tests/test_mvp.py::test_image_distillation_generates_ocr_and_scene_evidence` |
| F04 | Video single-asset distill engine | C | L0 | `VideoAdapter` + `tests/test_mvp.py::test_video_distillation_merges_audio_and_keyframe_evidence` |
| F05 | Tabular/time-series single-asset distill engine | C | L0 | `TabularAdapter` + `tests/test_mvp.py::test_tabular_distillation_emits_baseline_change_point_and_drift_evidence` |
| F06 | Corpus distill service path | C | L0 | `DistillationService.distill_corpus()` 已实现并有回归 |
| F07 | Corpus API surface | M | L1 | API 无 `/v1/distill/corpus` |
| F08 | Corpus CLI surface | M | L1 | CLI 无 `distill-corpus` 子命令 |
| F09 | Corpus worker surface | M | L2 | worker 不识别 `kind=corpus` |
| F10 | `file://` corpus asset normalization | C | L0 | `service.py::_resolve_source_uri()` |

### 4.2 Publication / Review / V2 语义链

| ID | 功能点 | 状态 | 上线级别 | 证据 / 缺口 |
|---|---|---|---|---|
| F11 | Publication builder + manifest 落盘 | C | L0 | `repository.py::_write_publications()` + corpus tests |
| F12 | Review task / review feedback / review policy 落盘 | C | L0 | `service.py` 与 `repository.py` 已写入相关 artifacts |
| F13 | Local file artifact repository | C | L0 | `FileArtifactRepository` 已承担 drafts 输出 |
| F14 | SkillGraph schema export / validation | C | L0 | `schema.py` + `tests/test_v2_schema_and_corpus.py` |
| F15 | Single-asset API entrypoints | C | L0 | `api_app.py` 已提供 text/audio/image/tabular/video |
| F16 | Typed request model validation | M | L1 | `api_app.py` 仍使用 bare `dict` |
| F17 | Typed / stable error contract | M | L1 | 现在大量异常统一折叠成 `HTTP 400` |
| F18 | API auth | M | L1 | 未见 API key / JWT / dependency |
| F19 | API rate limiting | M | L1 | 未见 limiter / budget guard |
| F20 | Provider timeout + retry/backoff | M | L1 | OpenAI provider 仅 `except Exception` 包装，无 timeout/retry 策略 |

### 4.3 运行、健康、可观测性

| ID | 功能点 | 状态 | 上线级别 | 证据 / 缺口 |
|---|---|---|---|---|
| F21 | Circuit breaker / failure budget guard | M | L2 | provider 层无熔断/预算 |
| F22 | Health / readiness checks | P | L1 | 仅有 `/healthz -> {"status":"ok"}`，不校验存储/模板/配置 |
| F23 | API automated tests | M | L1 | 未见 `TestClient` / `ASGITransport` / `AsyncClient` API 用例 |
| F24 | Local file-queue worker | P | L2 | `run_once()` 可跑，但只有单轮目录扫描语义 |
| F25 | Worker retry / idempotency | M | L2 | worker 无 retry policy，无重复作业防护 |
| F26 | Worker claim / lock semantics | M | L2 | 多 worker 并发安全语义未定义 |
| F27 | Temp scratch-root prune | M | L1 | `.tmp_omni_media/` 根目录缺 retention/prune |
| F28 | Structured logging | M | L1 | 无统一 logger / log schema |
| F29 | Request ID / trace ID propagation | M | L1 | 无 request-scoped context |
| F30 | Secrets bootstrap template | C | L0 | `.env.example` 已存在 |

### 4.4 运维合同、质量门禁与流程闭环

| ID | 功能点 | 状态 | 上线级别 | 证据 / 缺口 |
|---|---|---|---|---|
| F31 | Ops contract docs for auth / limits / errors | P | L1 | API docs有 endpoint/payload，但缺 auth、error、limit 合同 |
| F32 | Heuristic quality scoring | C | L0 | `quality/scoring.py` 已工作 |
| F33 | Threshold-based review policy | C | L0 | `quality/review_policy.py` 已工作 |
| F34 | Review feedback persistence | C | L0 | review feedback artifact 已落盘 |
| F35 | Executable feedback consumer | M | L2 | feedback 不驱动后续 pipeline |
| F36 | Review queue runtime workflow | M | L2 | 仅有 decision artifact，无真正 queue / assignee / close 流程 |
| F37 | Calibration dataset / threshold tuning | M | L2 | 评分阈值仍为 static defaults |
| F38 | `ArtifactRepository` abstraction | M | L2 | service 仍直接依赖 file repo |
| F39 | Service factory / orchestration split | M | L2 | `service.py` 同时持有 wiring + orchestration |
| F40 | PostgreSQL repository | M | L2 | 只有 SQL DDL，未见 runtime adapter |

### 4.5 发布门禁与交付

| ID | 功能点 | 状态 | 上线级别 | 证据 / 缺口 |
|---|---|---|---|---|
| F41 | Coverage gate | M | L1 | CI 无 fail-under / coverage report |
| F42 | Performance benchmark harness | M | L2 | 无 benchmark / load smoke |
| F43 | Container / deploy baseline | M | L1 | 无 Dockerfile / deploy manifest |
| F44 | Release runbook / checklist | M | L1 | 无正式上线手册 |

### 4.6 路线图扩展项

| ID | 功能点 | 状态 | 上线级别 | 证据 / 缺口 |
|---|---|---|---|---|
| F45 | Retrieval layer (`pgvector` / Qdrant) | M | R | 路线图有，runtime 未落地 |
| F46 | `revise / merge / supersede` lifecycle engine | M | R | 路线图有，runtime 未落地 |
| F47 | Multi-view publication expansion | M | R | 当前只稳定产出 markdown/json |
| F48 | Review UI / queue operations surface | M | R | 路线图有，runtime 未落地 |

## 5. 上线缺口结论

### 对外 Beta 前必须补齐的 16 个功能点

- F07 Corpus API surface
- F08 Corpus CLI surface
- F16 Typed request model validation
- F17 Typed / stable error contract
- F18 API auth
- F19 API rate limiting
- F20 Provider timeout + retry/backoff
- F22 Health / readiness checks
- F23 API automated tests
- F27 Temp scratch-root prune
- F28 Structured logging
- F29 Request ID / trace ID propagation
- F31 Ops contract docs for auth / limits / errors
- F41 Coverage gate
- F43 Container / deploy baseline
- F44 Release runbook / checklist

### 正式 GA 前建议补齐的 12 个功能点

- F09 Corpus worker surface
- F21 Circuit breaker / failure budget guard
- F24 Local file-queue worker hardening
- F25 Worker retry / idempotency
- F26 Worker claim / lock semantics
- F35 Executable feedback consumer
- F36 Review queue runtime workflow
- F37 Calibration dataset / threshold tuning
- F38 `ArtifactRepository` abstraction
- F39 Service factory / orchestration split
- F40 PostgreSQL repository
- F42 Performance benchmark harness

### 可后置但必须建账的路线图 4 点

- F45 Retrieval layer
- F46 Lifecycle revise/merge/supersede
- F47 Multi-view publication expansion
- F48 Review UI

## 6. 任务卡总索引

### L1 External Beta

- `LC-L1-01` 到 `LC-L1-19`

### L2 GA / Production Hardening

- `LC-L2-20` 到 `LC-L2-33`

### R Roadmap Extensions

- `LC-R-34` 到 `LC-R-37`

## 7. 细粒度任务卡

### LC-L1-01

- 关联功能点：F07
- 目标：新增 `/v1/distill/corpus` API 入口
- 文件：`src/omni_skill_pipeline/api_app.py`
- 完成标准：可接收 `CorpusDistillRequest` payload，返回 corpus bundle
- 验证：新增 API test，覆盖 2-asset corpus happy path

### LC-L1-02

- 关联功能点：F08
- 目标：新增 `distill-corpus` CLI 子命令
- 文件：`src/omni_skill_pipeline/cli.py`
- 完成标准：支持多 `--asset` 或 JSON payload 输入
- 验证：CLI smoke test + docs example

### LC-L1-03

- 关联功能点：F16
- 目标：新增 API request schema module
- 文件：`src/omni_skill_pipeline/api_schemas.py`
- 完成标准：为 text/audio/image/tabular/video/corpus 定义 Pydantic models
- 验证：schema import test + OpenAPI schema 检查

### LC-L1-04

- 关联功能点：F16
- 目标：用 Pydantic models 替换 bare `dict`
- 文件：`src/omni_skill_pipeline/api_app.py`
- 依赖：LC-L1-03
- 完成标准：所有 distill endpoint 不再接收 `payload: dict`
- 验证：invalid payload 返回 422 或明确 4xx

### LC-L1-05

- 关联功能点：F17
- 目标：建立统一异常映射与错误响应格式
- 文件：`src/omni_skill_pipeline/api_app.py`
- 完成标准：validation/provider/runtime error 有稳定 status code 与 JSON shape
- 验证：API error-path tests

### LC-L1-06

- 关联功能点：F18
- 目标：增加 API key 配置与校验依赖
- 文件：`src/omni_skill_pipeline/config.py`, `src/omni_skill_pipeline/api_app.py`, `.env.example`
- 完成标准：配置 `OMNI_API_KEY` 或同类变量后，distill endpoint 受保护
- 验证：无 key 401/403，有 key 通过

### LC-L1-07

- 关联功能点：F19
- 目标：增加最小限流策略
- 文件：`src/omni_skill_pipeline/api_app.py`
- 完成标准：按 IP 或 API key 限流，超限返回明确 429
- 验证：限流单测或 API integration test

### LC-L1-08

- 关联功能点：F20
- 目标：把 timeout 参数拉进 Settings
- 文件：`src/omni_skill_pipeline/config.py`, `src/omni_skill_pipeline/providers/openai_provider.py`
- 完成标准：OpenAI calls 不再依赖默认超时
- 验证：provider config unit test

### LC-L1-09

- 关联功能点：F20
- 目标：给 OpenAI provider 增加 retry/backoff wrapper
- 文件：`src/omni_skill_pipeline/providers/openai_provider.py`
- 依赖：LC-L1-08
- 完成标准：transcription / responses 请求具备有限重试与退避
- 验证：mock transient failure test

### LC-L1-10

- 关联功能点：F22
- 目标：升级 `/healthz` 为 readiness 检查
- 文件：`src/omni_skill_pipeline/api_app.py`
- 完成标准：至少校验 template path、draft dir、FastAPI app assembly
- 验证：ready / degraded path tests

### LC-L1-11

- 关联功能点：F23
- 目标：新增 API happy-path integration tests
- 文件：`tests/test_api_app.py`
- 完成标准：覆盖 text/audio/image/tabular/video endpoint
- 验证：加入 `scripts/ci.py` 回归

### LC-L1-12

- 关联功能点：F23
- 目标：新增 API validation / auth / error-path tests
- 文件：`tests/test_api_app.py`
- 依赖：`LC-L1-04`, `LC-L1-05`, `LC-L1-06`
- 完成标准：覆盖 bad payload、missing auth、provider failure
- 验证：CI 通过

### LC-L1-13

- 关联功能点：F27
- 目标：增加 scratch-root prune 工具与运维说明
- 文件：`scripts/`, `docs/latest/operations/worker.md`, `docs/latest/operations/env.md`
- 完成标准：可定期清理 `.tmp_omni_media/` 旧目录
- 验证：本地 smoke command

### LC-L1-14

- 关联功能点：F28
- 目标：新增统一 logging bootstrap
- 文件：`src/omni_skill_pipeline/logging_utils.py` 或同类模块
- 完成标准：API / service / worker 可输出结构化日志
- 验证：log smoke test

### LC-L1-15

- 关联功能点：F29
- 目标：增加 request_id / trace_id 传播
- 文件：`src/omni_skill_pipeline/api_app.py`, `src/omni_skill_pipeline/service.py`
- 依赖：LC-L1-14
- 完成标准：请求级上下文能进入关键日志事件
- 验证：API test 断言日志字段

### LC-L1-16

- 关联功能点：F31
- 目标：补 API 运维合同文档
- 文件：`docs/latest/operations/api.md`, `docs/latest/operations/env.md`
- 完成标准：写明 auth、error shape、rate limits、health endpoint 语义
- 验证：docs review

### LC-L1-17

- 关联功能点：F41
- 目标：新增 coverage report 与 fail-under gate
- 文件：`scripts/ci.py`, `.github/workflows/ci.yml`, `pyproject.toml` 或 coverage config
- 完成标准：CI 可输出 coverage，并设置最低阈值
- 验证：CI dry-run / local run

### LC-L1-18

- 关联功能点：F43
- 目标：提供最小容器化部署基线
- 文件：`Dockerfile`, 可选 `.dockerignore`
- 完成标准：能通过 `uvicorn apps.api.main:app` 启动服务镜像
- 验证：本地 build/run smoke

### LC-L1-19

- 关联功能点：F44
- 目标：新增外部 Beta 发布 runbook / checklist
- 文件：`docs/latest/operations/runbooks/launch-beta.md`
- 完成标准：含 deploy、rollback、验收、日志检查、临时目录清理
- 验证：docs review

### LC-L2-20

- 关联功能点：F09
- 目标：worker 支持 `kind=corpus`
- 文件：`src/omni_skill_pipeline/worker.py`
- 完成标准：worker 可消费 corpus job
- 验证：worker integration test

### LC-L2-21

- 关联功能点：`F24`, `F25`
- 目标：worker 增加 retry policy
- 文件：`src/omni_skill_pipeline/worker.py`
- 完成标准：transient failure 可重试，永久失败写 failed payload
- 验证：worker failure-mode test

### LC-L2-22

- 关联功能点：F25
- 目标：worker 增加幂等标识或重复作业防护
- 文件：`src/omni_skill_pipeline/worker.py`
- 完成标准：重复 job 不产生重复输出或具备安全覆盖策略
- 验证：duplicate job test

### LC-L2-23

- 关联功能点：F26
- 目标：定义并实现 worker claim / lock 语义
- 文件：`src/omni_skill_pipeline/worker.py`
- 完成标准：多 worker 不会同时消费同一 job
- 验证：concurrency simulation test

### LC-L2-24

- 关联功能点：F21
- 目标：provider 增加 circuit breaker / failure budget
- 文件：`src/omni_skill_pipeline/providers/openai_provider.py`
- 完成标准：连续失败后快速熔断并给出可观察错误
- 验证：mock failure storm test

### LC-L2-25

- 关联功能点：F38
- 目标：引入 `ArtifactRepository` Protocol
- 文件：`src/omni_skill_pipeline/interfaces.py`
- 完成标准：file repo 能声明性满足接口
- 验证：repository contract test

### LC-L2-26

- 关联功能点：F38
- 目标：让 `DistillationService` 依赖 repository protocol 而非 concrete class
- 文件：`src/omni_skill_pipeline/service.py`
- 依赖：LC-L2-25
- 完成标准：构造函数不再绑死 `FileArtifactRepository`
- 验证：service tests 通过

### LC-L2-27

- 关联功能点：F39
- 目标：抽离 service factory / composition root
- 文件：`src/omni_skill_pipeline/service.py`, 新建 `service_factory.py` 或同类模块
- 完成标准：`build_service()` 不再与核心 orchestration 混写
- 验证：import smoke + tests

### LC-L2-28

- 关联功能点：F39
- 目标：抽离 corpus orchestration / publication harmonization
- 文件：`src/omni_skill_pipeline/service.py`
- 完成标准：`service.py` 行数和职责明显收缩
- 验证：existing tests 通过

### LC-L2-29

- 关联功能点：F36
- 目标：实现最小 review queue 持久化合同
- 文件：`src/omni_skill_pipeline/`, `infra/sql/001_init.sql` 或新 schema
- 完成标准：`review_required` 不只落文件，还能被查询/消费
- 验证：integration test

### LC-L2-30

- 关联功能点：F35
- 目标：新增 review feedback consumer skeleton
- 文件：`src/omni_skill_pipeline/quality/` 或新模块
- 完成标准：feedback 至少能转换成下一步 remediation plan
- 验证：unit test

### LC-L2-31

- 关联功能点：F37
- 目标：建立 calibration dataset manifest 与调参脚本
- 文件：`docs/working/status/baselines/`, `scripts/`
- 完成标准：能基于样本比较 quality score 与 reviewer judgement
- 验证：script smoke run

### LC-L2-32

- 关联功能点：F40
- 目标：实现 PostgreSQL repository adapter
- 文件：`src/omni_skill_pipeline/persistence/postgres_repository.py`
- 完成标准：可写入 skills / review_tasks / publications 核心表
- 验证：repository integration test

### LC-L2-33

- 关联功能点：`F40`, `F42`
- 目标：增加 file + Postgres dual-write 测试与 benchmark harness
- 文件：`tests/`, `scripts/`
- 依赖：LC-L2-32
- 完成标准：dual-write 不破坏现有 file artifacts，并能测基础时延
- 验证：integration test + benchmark smoke

### LC-R-34

- 关联功能点：F45
- 目标：建立 retrieval abstraction 与 vector backend 选型基线
- 文件：`src/omni_skill_pipeline/retrieval/`, `docs/latest/architecture/`
- 完成标准：有统一检索接口与 backend decision doc
- 验证：unit smoke test

### LC-R-35

- 关联功能点：F46
- 目标：实现 `revise / merge / supersede` lifecycle decision engine
- 文件：`src/omni_skill_pipeline/`
- 完成标准：相近 skill 不再只新建，还可输出 lifecycle decision
- 验证：lifecycle tests

### LC-R-36

- 关联功能点：F47
- 目标：扩展 publication builder 输出 checklist / decision tree
- 文件：`src/omni_skill_pipeline/assembly/publication_builder.py`
- 完成标准：除 markdown/json 外至少再有一种 publication
- 验证：publication tests

### LC-R-37

- 关联功能点：F48
- 目标：建立 review queue operations surface
- 文件：`apps/`, `src/`, `docs/latest/operations/`
- 完成标准：review task 能被查看、认领、关闭
- 验证：integration test 或 UI smoke

## 8. 建议执行顺序

### 第一波：外部 Beta 阻断项

- LC-L1-03
- LC-L1-04
- LC-L1-05
- LC-L1-06
- LC-L1-07
- LC-L1-08
- LC-L1-09
- LC-L1-10
- LC-L1-11
- LC-L1-12
- LC-L1-14
- LC-L1-15
- LC-L1-17
- LC-L1-18
- LC-L1-19

### 第二波：把多资产能力打穿外部入口

- LC-L1-01
- LC-L1-02
- LC-L2-20

### 第三波：GA / 生产硬化

- LC-L2-21 到 LC-L2-33

### 第四波：路线图扩展

- LC-R-34 到 LC-R-37

## 9. 结论

GLM5.1 对“生产外壳未成”的判断大体正确；对“核心功能还很弱”的判断偏重。  
以 2026-04-24 的仓内实况看：

- 内网试运行：已可用
- 外部 Beta：还差一批明确的 API / 运维 / 发布门禁补全
- 正式 GA：还需补 repository abstraction、worker 语义、review queue、benchmark、持久层

后续 Codex 不需要再重新做大而化之的分析，直接按本卷的任务卡下刀即可。
