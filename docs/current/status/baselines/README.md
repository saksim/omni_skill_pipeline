# E0 Baseline Pack

## 判词

此目录用于固化 V2 改造前的 E0 基线。目标不是保存“好看”的输出，而是保存“可对照、可复验、可审判”的当前事实。

## 包含内容

- [e0-sample-inventory.md](D:\download\gaming\new_program\data_helper\3_omni_skill_pipeline\docs\current\status\baselines\e0-sample-inventory.md)
  - 样本清单、用途、已知缺口
- [e0-baseline-2026-04-20.md](D:\download\gaming\new_program\data_helper\3_omni_skill_pipeline\docs\current\status\baselines\e0-baseline-2026-04-20.md)
  - 2026-04-20 实际重放结果、观察与结论
- [evaluation-rubric.md](D:\download\gaming\new_program\data_helper\3_omni_skill_pipeline\docs\current\status\baselines\evaluation-rubric.md)
  - 后续 V2 所有阶段共用的评估口径
- [e0-baseline-manifest.json](D:\download\gaming\new_program\data_helper\3_omni_skill_pipeline\docs\current\status\baselines\e0-baseline-manifest.json)
  - 机器可读的样本与基线草稿映射
- `e8-dual-write-benchmark-report.json`（由 `scripts/benchmark_dual_write.py` 生成）
  - file-only 与 file+postgres dual-write 的基础时延报告

## 用法

每次推进 V2 任一阶段时，都应执行以下动作：

1. 选取对应样本集
2. 重放当前实现
3. 按 `evaluation-rubric.md` 评分
4. 与 E0 基线对比
5. 记录是变强、持平，还是退化

## 注意

- E0 基线允许包含低质量输出，因为它的职责是反映真相，不是粉饰问题。
- 当前图片与视频基线故意保留了明显 OCR 噪声，它们正是 V2 必须优先斩断的病灶。

## TP-E11-03 Quality Regression

- Baseline manifest: `docs/current/status/baselines/e11-quality-regression-manifest.json`
- Runner script: `scripts/run_quality_regression.py`
- Linux example:
  - `python scripts/run_quality_regression.py --manifest docs/current/status/baselines/e11-quality-regression-manifest.json --output docs/current/status/baselines/e11-quality-regression-report.json`

## TP-E11-04 Perf-Cost Baseline

- Baseline manifest: `docs/current/status/baselines/e11-perf-cost-baseline-manifest.json`
- Runner script: `scripts/run_perf_cost_baseline.py`
- Linux example:
  - `python scripts/run_perf_cost_baseline.py --manifest docs/current/status/baselines/e11-perf-cost-baseline-manifest.json --output docs/current/status/baselines/e11-perf-cost-baseline-report.json --fail-on-regression`

## TP-E13-01 Doc Sync Check

- Output report: `docs/current/status/baselines/e13-doc-sync-check-report.json`
- Runner script: `scripts/run_doc_sync_check.py`
- Scope docs:
  - `docs/current/operations/api.md` (`LC-L1-16`)
  - `docs/current/operations/runbooks/launch-beta.md` (`LC-L1-19`)
- Validation checks:
  - `api_ops_contract_completeness`
  - `launch_beta_runbook_completeness`
- Linux example:
  - `python scripts/run_doc_sync_check.py --output docs/current/status/baselines/e13-doc-sync-check-report.json`

## TP-E13-02 Migration Guide Contract

- Scope docs:
  - `docs/current/architecture/v1-to-v2-migration-guide.md`
  - `docs/current/operations/v1-to-v2-migration-runbook.md`
- Validation check: `migration_guide_completeness` in `scripts/run_doc_sync_check.py`
- Linux example:
  - `python scripts/run_tp_tests.py TP-E13-02 --python python3`
  - `python scripts/run_doc_sync_check.py --output docs/current/status/baselines/e13-doc-sync-check-report.json`

## TP-E13-03 Release Switch Standard Contract

- Scope docs:
  - `docs/current/status/v2-release-switch-standard.md`
  - `docs/history/status/2026-04-26-v2-release-switch-standard.md`
- Validation check: `release_switch_standard_completeness` in `scripts/run_doc_sync_check.py`
- Linux example:
  - `python scripts/run_tp_tests.py TP-E13-03 --python python3`
  - `python scripts/run_doc_sync_check.py --output docs/current/status/baselines/e13-doc-sync-check-report.json`

## TP-E13-04 Linux Validation Suite

- Plan report: `docs/current/status/baselines/e13-linux-validation-suite-plan.json`
- Runner script: `scripts/run_linux_validation_suite.py`
- Default stages: `ci`, `container_smoke`, `doc_sync`, `quality_regression`, `perf_cost_baseline`, `postgres_soak`
- Linux dry-run example:
  - `python scripts/run_linux_validation_suite.py --python python3 --dry-run --output docs/current/status/baselines/e13-linux-validation-suite-plan.json`
- Linux container stage dry-run example:
  - `python scripts/run_linux_validation_suite.py --python python3 --stages container_smoke --container-image-tag omni-skill-pipeline:beta --dry-run --output -`
- Linux execution example:
  - `python scripts/run_linux_validation_suite.py --python python3`

## TP-E13-05 Postgres Soak Validation

- Plan report: `docs/current/status/baselines/e13-postgres-soak-plan.json`
- Benchmark report: `docs/current/status/baselines/e13-postgres-soak-benchmark-report.json`
- Runner script: `scripts/run_postgres_soak_validation.py`
- Linux dry-run example:
  - `python scripts/run_postgres_soak_validation.py --python python3 --dry-run --output docs/current/status/baselines/e13-postgres-soak-plan.json`
- Linux execution example:
  - `python scripts/run_postgres_soak_validation.py --python python3 --postgres-dsn "$OMNI_TEST_POSTGRES_DSN"`
