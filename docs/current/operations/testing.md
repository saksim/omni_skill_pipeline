# Testing

## 判词

这个仓当前走的是 `unittest` 体系，不是 `pytest` 体系；测试判断要按现有链路验尸，不要拿错刑具。

## 本地环境对齐

PowerShell:

```powershell
py -3.11 -m venv .venv
. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

POSIX:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

## 全量回归

```bash
python scripts/run_ci.py
```

该入口会统一执行：

- `python -m coverage run --parallel-mode -m unittest discover -s tests -p 'test_*.py'`
- `python scripts/run_tp_tests.py --all --python <current-python>`
- `python -m coverage combine`
- `python -m coverage report --show-missing --fail-under <threshold>`
- `python -m coverage xml -o coverage.xml`

默认 coverage fail-under 为 `50`，可通过参数覆盖。

示例：提高阈值到 `65`

```bash
python scripts/run_ci.py --coverage-fail-under 65
```

示例：仅在本地快速验逻辑，临时关闭 coverage

```bash
python scripts/run_ci.py --no-coverage
```

## 容器烟测脚本

容器基线烟测（构建镜像 + 启动容器 + 轮询 `/healthz`）：

```bash
python scripts/run_container_smoke.py --image-tag omni-skill-pipeline:local --port 18000
```

只看执行计划，不真正调用 Docker：

```bash
python scripts/run_container_smoke.py --dry-run
```

Linux 统一验测时建议直接使用该脚本，作为 `LC-L1-18` 的容器回归入口。

## Dual-Write Benchmark Harness

`LC-L2-33` 引入 dual-write 基准脚本：

```bash
python scripts/benchmark_dual_write.py --iterations 20 --skip-postgres
python scripts/benchmark_dual_write.py --iterations 20 --postgres-dsn "$OMNI_TEST_POSTGRES_DSN"
```

- 第一个命令只测 file repository baseline。
- 第二个命令测 file + Postgres dual-write 时延。
- 默认报告落盘：`docs/current/status/baselines/e8-dual-write-benchmark-report.json`。

## 定向执行

查看当前已映射 Task Package:

```bash
python scripts/run_tp_tests.py --list
```

执行单个工单:

```bash
python scripts/run_tp_tests.py TP-E6-02 --python python
```

执行多个工单:

```bash
python scripts/run_tp_tests.py TP-E1-01 TP-E1-02 TP-E1-03 TP-E2-01 TP-E2-02 TP-E2-03 TP-E3-01 TP-E3-02 TP-E3-03 TP-E4-01 TP-E4-02 TP-E4-03 TP-E4-04 TP-E4-05 TP-E5-01 TP-E5-02 TP-E5-03 TP-E5-04 TP-E6-01 TP-E6-02 TP-E6-03 TP-E6-04 TP-E7-01 TP-E7-02 TP-E7-03 TP-E7-04 TP-E8-01 TP-E8-02 TP-E8-03 TP-E8-04 TP-E9-01 TP-E9-02 TP-E9-03 TP-E10-01 TP-E10-02 TP-E10-03 TP-E11-01 TP-E11-02 TP-E11-03 TP-E11-04 TP-E12-01 TP-E12-02 TP-E12-03 TP-E12-04 TP-E13-01 TP-E13-02 TP-E13-03 TP-E13-04 TP-E13-05 TP-E13-06 TP-E13-07 TP-E13-08 TP-E13-09 TP-E13-10 TP-E13-11 TP-E13-12 --python python3
```

## 当前覆盖重点

- `tests/test_mvp.py`: 覆盖 text / audio / image / video / tabular 主路径
- `tests/test_v2_schema_and_corpus.py`: 覆盖 corpus 组装、publication、quality、review artifacts
- `tests/test_quality_scoring.py`: 覆盖质量评分
- `tests/test_review_policy.py`: 覆盖 review threshold 与 reason codes
- `tests/test_dual_write_repository.py`: 覆盖 dual-write 主/从仓储行为与失败保护
- `tests/test_benchmark_dual_write.py`: 覆盖 dual-write benchmark 脚本烟测
- `tests/test_similarity_retrieval.py`: 覆盖检索抽象、inmemory baseline 排序、backend 选型占位行为
- `tests/test_lifecycle_decision_engine.py`: 覆盖 lifecycle `new/revise/merge/supersede/reject` 决策分流
- `tests/test_publication_builder.py`: 覆盖 checklist/decision_tree 输出与无 decision 场景 fallback
- `tests/test_publication_orchestrator_split.py`: 覆盖 goal_type 驱动的 publication type 选择
- `tests/test_api_app.py`: 覆盖 distill API 输入转换、错误映射与 TP-E10-02 的 V2 输出契约字段
- `tests/test_worker.py`: 覆盖 TP-E10-03 worker 新任务类型（review_queue/rebuild_publication/revise_skill）
- `tests/test_transformers_regression.py`: 覆盖 TP-E11-01 模型/转换器分支回归（skill_type、evidence 聚合、legacy atom bridge）
- `tests/test_doc_sync_check_script.py`: 覆盖 TP-E13-01 / TP-E13-02 / TP-E13-03 文档同步检查脚本（源码表面 + 迁移指南 + 发布切换标准 + LC-L1-19 Beta runbook 契约）
- `tests/test_linux_validation_suite_script.py`: 覆盖 TP-E13-04 Linux 统一验尸编排脚本（阶段筛选、命令打包、dry-run 计划落盘、container smoke / postgres_soak / postgres_ga / worker_ga / review_queue_ga / provider_ga / calibration_ga / roadmap_extension 参数透传）
- `tests/test_postgres_soak_validation_script.py`: 覆盖 TP-E13-05 Postgres 长稳验尸脚本（TP 回归编排、benchmark 参数、dsn fail-fast）
- `tests/test_worker_ga_validation_script.py`: 覆盖 TP-E13-06 worker GA 验证脚本（阶段筛选、dry-run 计划落盘）
- `tests/test_provider_ga_validation_script.py`: 覆盖 TP-E13-07 provider GA 验证脚本（retry/circuit-breaker/failure-budget/audit 计划编排）
- `tests/test_review_queue_ga_validation_script.py`: 覆盖 TP-E13-08 review queue GA 验证脚本（repository/service/api/feedback 阶段编排与筛选）
- `tests/test_calibration_ga_validation_script.py`: 覆盖 TP-E13-09 calibration GA 验证脚本（阈值契约、调参报告、manifest/report 参数透传）
- `tests/test_postgres_ga_validation_script.py`: 覆盖 TP-E13-10 Postgres GA 验证脚本（repository/dual-write/benchmark 阶段编排、dsn fail-fast、benchmark 参数透传）
- `tests/test_roadmap_extension_validation_script.py`: 覆盖 TP-E13-11 roadmap extension 验证脚本（LC-R-34~37 的 retrieval/lifecycle/publication/review queue surface 阶段编排与筛选）
- `tests/test_release_gate_validation_script.py`: 覆盖 TP-E13-12 发布门禁聚合脚本（beta/ga/roadmap 阶段筛选与 coverage/container/postgres/calibration 参数透传）
- `tests/test_tp_registry.py`: 覆盖 TP 注册表与 `skill-distillation-v2-work-orders.md` 的完整性对齐，防止新工单漏映射

## 当前缺口

- FastAPI/ASGI API 自动化测试已覆盖核心契约；仍缺真实 provider 故障注入与负载场景
- coverage fail-under 仍是保守阈值（`50`），后续应随质量基线提升
- 尚无生产级负载压测（当前仅有 dual-write benchmark smoke harness）
- 真实 provider failure-mode 覆盖仍偏薄

## 维护规则

每次新增 `TP-*` 工单时，至少同步完成三件事：

1. 在 `tests/` 落测试 case
2. 在 `scripts/run_tp_tests.py` 的 `TP_TEST_CASES` 中登记映射
3. 在本文件更新覆盖范围与新增工单说明（并确保 `tests/test_tp_registry.py` 对齐 work-orders）

## LC-R-37 Additions

- Added `TP-E9-03` for review queue operations surface.
- Added repository-level transition coverage in `tests/test_review_queue_repository.py`.
- Added service integration coverage in `tests/test_review_queue_integration.py`.
- Added API contract coverage in `tests/test_api_review_queue.py` for list/claim/close.
- Note: the previous API coverage gap statement is superseded for review queue scope; contract tests now exist in `tests/test_api_review_queue.py`.

## TP-E12-01 Additions

- Added structured trace fallback and chain fields in `src/omni_skill_pipeline/service.py`.
- Added per-job request/trace context propagation in `src/omni_skill_pipeline/worker.py`.
- Added `tests/test_trace_observability_tp_e12.py` for service/worker trace-chain coverage.
- Added `TP-E12-01` mapping in `scripts/run_tp_tests.py`.
- Batch example: `python scripts/run_tp_tests.py TP-E11-02 TP-E11-03 TP-E11-04 TP-E12-01 --python python`.

## TP-E12-02 Additions

- Added provider call audit counters/snapshots in `src/omni_skill_pipeline/providers/openai_provider.py`.
- Added adapter-level provider call metadata in `src/omni_skill_pipeline/adapters/audio.py`, `src/omni_skill_pipeline/adapters/image.py`, and `src/omni_skill_pipeline/adapters/video.py`.
- Added corpus-level provider footprint aggregation in `src/omni_skill_pipeline/service.py`.
- Added `tests/test_provider_audit_tp_e12.py` for provider audit and corpus footprint assertions.
- Added `TP-E12-02` mapping in `scripts/run_tp_tests.py`.
- Linux batch example: `python scripts/run_tp_tests.py TP-E12-01 TP-E12-02 --python python3`.

## TP-E12-03 Additions

- Added recursive redaction helpers in `src/omni_skill_pipeline/redaction.py` to sanitize sensitive keys and inline bearer/token-like values.
- Added request/adapter metadata sanitization in `src/omni_skill_pipeline/service.py` before persistence.
- Added repository-side defense-in-depth redaction in `src/omni_skill_pipeline/repository.py` before writing artifact files.
- Added `tests/test_security_redaction_tp_e12.py` for service payload redaction and file artifact persistence redaction assertions.
- Added `TP-E12-03` mapping in `scripts/run_tp_tests.py`.
- Linux batch example: `python scripts/run_tp_tests.py TP-E12-01 TP-E12-02 TP-E12-03 --python python3`.

## TP-E12-04 Additions

- Added explicit scratch cleanup status handling in `src/omni_skill_pipeline/adapters/video.py`; cleanup failures now record deferred recovery entries for prune jobs.
- Added intermediate keyframe candidate cleanup in `src/omni_skill_pipeline/providers/media.py` so only selected frames remain during processing.
- Added `tests/test_tmp_artifact_governance_tp_e12.py` to cover success cleanup and deferred cleanup-recovery behavior.
- Added `tests/test_media_provider.py::MediaProcessorTests.test_cleanup_unselected_frames_keeps_selected_only` for intermediate-frame lifecycle cleanup.
- Added `TP-E12-04` mapping in `scripts/run_tp_tests.py`.
- Linux batch example: `python scripts/run_tp_tests.py TP-E12-01 TP-E12-02 TP-E12-03 TP-E12-04 --python python3`.

## TP-E13-01 Additions

- Added `scripts/run_doc_sync_check.py` to verify README/CLI/API/worker/testing docs stay aligned with source surfaces.
- Extended `scripts/run_doc_sync_check.py` with `api_ops_contract_completeness` check for `docs/current/operations/api.md` (`LC-L1-16` auth/rate-limit/error/health contract).
- Extended `scripts/run_doc_sync_check.py` with `launch_beta_runbook_completeness` check for `docs/current/operations/runbooks/launch-beta.md` (`LC-L1-19` checklist contract).
- Added `tests/test_doc_sync_check_script.py` coverage for API ops-contract incomplete fail-path.
- Added `tests/test_doc_sync_check_script.py` coverage for launch-beta incomplete-contract fail-path.
- Added `TP-E13-01` mapping in `scripts/run_tp_tests.py`.
- Linux doc sync example: `python scripts/run_doc_sync_check.py --output docs/current/status/baselines/e13-doc-sync-check-report.json`.
- Linux batch example: `python scripts/run_tp_tests.py TP-E12-01 TP-E12-02 TP-E12-03 TP-E12-04 TP-E13-01 --python python3`.

## TP-E13-02 Additions

- Added `docs/current/architecture/v1-to-v2-migration-guide.md` with migration steps, rollback strategy, and risk register.
- Added `docs/current/operations/v1-to-v2-migration-runbook.md` with Linux execution and rollback sequence.
- Extended `scripts/run_doc_sync_check.py` with `migration_guide_completeness` check and migration doc path args.
- Extended `tests/test_doc_sync_check_script.py` with incomplete-migration-doc fail-path assertions.
- Added `TP-E13-02` mapping in `scripts/run_tp_tests.py`.
- Linux batch example: `python scripts/run_tp_tests.py TP-E13-01 TP-E13-02 --python python3`.

## TP-E13-03 Additions

- Added `docs/current/status/v2-release-switch-standard.md` with hard-gate rules and cutover/rollback criteria.
- Added `docs/history/status/2026-04-26-v2-release-switch-standard.md` as the first decision snapshot baseline.
- Extended `scripts/run_doc_sync_check.py` with `release_switch_standard_completeness` check and release status doc path args.
- Extended `tests/test_doc_sync_check_script.py` with release-switch incomplete-doc fail-path assertions.
- Added `TP-E13-03` mapping in `scripts/run_tp_tests.py`.
- Linux batch example: `python scripts/run_tp_tests.py TP-E13-01 TP-E13-02 TP-E13-03 --python python3`.

## TP-E13-04 Additions

- Added `scripts/run_linux_validation_suite.py` to orchestrate Linux unified validation stages (`ci`, `container_smoke`, `doc_sync`, `quality_regression`, `perf_cost_baseline`, `postgres_soak`).
- Added `tests/test_linux_validation_suite_script.py` for dry-run plan output, stage-filter behavior, and `container_smoke` option forwarding coverage.
- Added `TP-E13-04` mapping in `scripts/run_tp_tests.py`.
- Linux dry-run example: `python scripts/run_linux_validation_suite.py --python python3 --dry-run --output docs/current/status/baselines/e13-linux-validation-suite-plan.json`.
- Linux container-only dry-run example: `python scripts/run_linux_validation_suite.py --python python3 --stages container_smoke --container-image-tag omni-skill-pipeline:beta --dry-run --output -`.
- Linux execution example: `python scripts/run_linux_validation_suite.py --python python3`.

## TP-E13-05 Additions

- Added `scripts/run_postgres_soak_validation.py` to orchestrate Postgres soak command pack (`tp_postgres`, `review_queue`, `dual_write_benchmark`).
- Extended `scripts/run_linux_validation_suite.py` with `postgres_soak` stage so Linux full-pack can include Postgres long-run validation.
- Added `tests/test_postgres_soak_validation_script.py` for dry-run plan output, stage filtering, benchmark args, and DSN fail-fast behavior.
- Updated `tests/test_linux_validation_suite_script.py` for the new `postgres_soak` stage in default command pack and postgres option forwarding coverage.
- Added `TP-E13-05` mapping in `scripts/run_tp_tests.py`.
- Linux dry-run example: `python scripts/run_postgres_soak_validation.py --python python3 --dry-run --output docs/current/status/baselines/e13-postgres-soak-plan.json`.
- Linux execution example: `python scripts/run_postgres_soak_validation.py --python python3 --postgres-dsn "$OMNI_TEST_POSTGRES_DSN"`.

## TP-E13-06 Additions

- Added `scripts/run_worker_ga_validation.py` to orchestrate worker GA-hardening command pack (`worker_corpus`, `worker_retry`, `worker_idempotency`, `worker_claim_lock`, `worker_task_types`).
- Added `tests/test_worker_ga_validation_script.py` for dry-run plan output and stage-filter behavior.
- Extended `scripts/run_linux_validation_suite.py` with `worker_ga` stage so Linux full-pack can include worker GA hardening validation.
- Updated `tests/test_linux_validation_suite_script.py` with worker_ga stage forwarding coverage.
- Added `TP-E13-06` mapping in `scripts/run_tp_tests.py`.
- Linux dry-run example: `python scripts/run_worker_ga_validation.py --python python3 --dry-run --output docs/current/status/baselines/e13-worker-ga-validation-plan.json`.
- Linux stage-only dry-run example: `python scripts/run_worker_ga_validation.py --python python3 --stages worker_retry worker_claim_lock --dry-run --output -`.

## TP-E13-07 Additions

- Added `scripts/run_provider_ga_validation.py` to orchestrate provider GA-hardening command pack (`provider_retry`, `provider_circuit_breaker`, `provider_failure_budget`, `provider_config_contract`, `provider_call_audit`, `provider_footprint`).
- Added `tests/test_provider_ga_validation_script.py` for default dry-run plan output and stage-filter behavior.
- Extended `scripts/run_linux_validation_suite.py` with `provider_ga` stage so Linux full-pack can include provider GA hardening validation.
- Updated `tests/test_linux_validation_suite_script.py` with provider_ga stage forwarding coverage.
- Added `TP-E13-07` mapping in `scripts/run_tp_tests.py`.
- Linux dry-run example: `python scripts/run_provider_ga_validation.py --python python3 --dry-run --output docs/current/status/baselines/e13-provider-ga-validation-plan.json`.
- Linux stage-only dry-run example: `python scripts/run_provider_ga_validation.py --python python3 --stages provider_circuit_breaker provider_call_audit --dry-run --output -`.

## TP-E13-08 Additions

- Added `scripts/run_review_queue_ga_validation.py` to orchestrate review queue GA-hardening command pack (`review_queue_repository`, `review_queue_service`, `review_queue_api`, `review_feedback`, `review_feedback_consumer`).
- Added `tests/test_review_queue_ga_validation_script.py` for default dry-run plan output and stage-filter behavior.
- Extended `scripts/run_linux_validation_suite.py` with `review_queue_ga` stage so Linux full-pack can include review queue hardening validation.
- Updated `tests/test_linux_validation_suite_script.py` with review_queue_ga stage forwarding coverage.
- Added `TP-E13-08` mapping in `scripts/run_tp_tests.py`.
- Linux dry-run example: `python scripts/run_review_queue_ga_validation.py --python python3 --dry-run --output docs/current/status/baselines/e13-review-queue-ga-validation-plan.json`.
- Linux stage-only dry-run example: `python scripts/run_review_queue_ga_validation.py --python python3 --stages review_queue_api review_feedback_consumer --dry-run --output -`.

## TP-E13-09 Additions

- Added `scripts/run_calibration_ga_validation.py` to orchestrate calibration GA-hardening command pack (`calibration_contract`, `review_policy_contract`, `calibration_report`).
- Added `tests/test_calibration_ga_validation_script.py` for default dry-run plan output and calibration option-forwarding behavior.
- Extended `scripts/run_linux_validation_suite.py` with `calibration_ga` stage so Linux full-pack can include LC-L2-31 threshold calibration validation.
- Updated `tests/test_linux_validation_suite_script.py` with calibration_ga stage forwarding coverage.
- Added `TP-E13-09` mapping in `scripts/run_tp_tests.py`.
- Linux dry-run example: `python scripts/run_calibration_ga_validation.py --python python3 --dry-run --output docs/current/status/baselines/e13-calibration-ga-validation-plan.json`.
- Linux stage-only dry-run example: `python scripts/run_calibration_ga_validation.py --python python3 --stages calibration_report --manifest docs/current/status/baselines/e7-calibration-manifest.json --calibration-report-output docs/current/status/baselines/e7-calibration-report.json --margin 0.03 --dry-run --output -`.

## TP-E13-10 Additions

- Added `scripts/run_postgres_ga_validation.py` to orchestrate Postgres GA-hardening command pack (`postgres_repository_contract`, `postgres_repository_integration`, `dual_write_contract`, `dual_write_integration`, `dual_write_benchmark`).
- Added `tests/test_postgres_ga_validation_script.py` for default dry-run plan output, stage filtering, benchmark option-forwarding, and DSN fail-fast behavior.
- Extended `scripts/run_linux_validation_suite.py` with `postgres_ga` stage and forwarding for `postgres-dsn`, `postgres-ga-iterations`, `postgres-ga-output`, and benchmark output options.
- Updated `tests/test_linux_validation_suite_script.py` with postgres_ga stage forwarding coverage.
- Added `TP-E13-10` mapping in `scripts/run_tp_tests.py`.
- Linux dry-run example: `python scripts/run_postgres_ga_validation.py --python python3 --dry-run --output docs/current/status/baselines/e13-postgres-ga-validation-plan.json`.
- Linux stage-only dry-run example: `python scripts/run_postgres_ga_validation.py --python python3 --stages dual_write_contract dual_write_benchmark --postgres-dsn "$OMNI_TEST_POSTGRES_DSN" --benchmark-iterations 120 --benchmark-output docs/current/status/baselines/e13-postgres-ga-benchmark-report.json --dry-run --output -`.

## TP-E13-11 Additions

- Added `scripts/run_roadmap_extension_validation.py` to orchestrate LC-R-34~37 command pack (`retrieval_layer`, `lifecycle_engine`, `publication_expansion`, `review_queue_surface`).
- Added `tests/test_roadmap_extension_validation_script.py` for default dry-run plan output and stage-filter behavior.
- Extended `scripts/run_linux_validation_suite.py` with `roadmap_extension` stage and forwarding for `--roadmap-extension-output`.
- Updated `tests/test_linux_validation_suite_script.py` with roadmap_extension stage forwarding coverage.
- Added `TP-E13-11` mapping in `scripts/run_tp_tests.py`.
- Linux dry-run example: `python scripts/run_roadmap_extension_validation.py --python python3 --dry-run --output docs/current/status/baselines/e13-roadmap-extension-validation-plan.json`.
- Linux stage-only dry-run example: `python scripts/run_roadmap_extension_validation.py --python python3 --stages retrieval_layer review_queue_surface --dry-run --output -`.

## TP-E13-12 Additions

- Added `scripts/run_release_gate_validation.py` to orchestrate release gate command packs (`beta_gate`, `ga_gate`, `roadmap_gate`) by delegating to `scripts/run_linux_validation_suite.py`.
- Added `tests/test_release_gate_validation_script.py` for default dry-run plan output, beta-only stage forwarding, and ga-stage postgres/calibration option forwarding.
- Added `TP-E13-12` mapping in `scripts/run_tp_tests.py` and synced `tests/test_tp_registry.py` known-work-order assertions.
- Linux dry-run example: `python scripts/run_release_gate_validation.py --python python3 --dry-run --output docs/current/status/baselines/e13-release-gate-validation-plan.json`.
- Linux beta-only dry-run example: `python scripts/run_release_gate_validation.py --python python3 --stages beta_gate --coverage-fail-under 65 --container-image-tag omni-skill-pipeline:beta --dry-run --output -`.
