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
  - `tests/test_tp_registry.py::TPRegistryScriptTests.test_list_command_exposes_known_work_orders` (TP mapping parity: missing + undocumented IDs)
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
- Default stages: `ci`, `container_smoke`, `doc_sync`, `quality_regression`, `perf_cost_baseline`, `postgres_soak`, `postgres_ga`, `worker_ga`, `review_queue_ga`, `provider_ga`, `calibration_ga`, `roadmap_extension`
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

## TP-E13-06 Worker GA Validation

- Plan report: `docs/current/status/baselines/e13-worker-ga-validation-plan.json`
- Runner script: `scripts/run_worker_ga_validation.py`
- Default stages: `worker_corpus`, `worker_retry`, `worker_idempotency`, `worker_claim_lock`, `worker_task_types`
- Linux dry-run example:
  - `python scripts/run_worker_ga_validation.py --python python3 --dry-run --output docs/current/status/baselines/e13-worker-ga-validation-plan.json`
- Linux stage-filter dry-run example:
  - `python scripts/run_worker_ga_validation.py --python python3 --stages worker_retry worker_claim_lock --dry-run --output -`

## TP-E13-07 Provider GA Validation

- Plan report: `docs/current/status/baselines/e13-provider-ga-validation-plan.json`
- Runner script: `scripts/run_provider_ga_validation.py`
- Default stages: `provider_retry`, `provider_circuit_breaker`, `provider_failure_budget`, `provider_config_contract`, `provider_call_audit`, `provider_footprint`
- Linux dry-run example:
  - `python scripts/run_provider_ga_validation.py --python python3 --dry-run --output docs/current/status/baselines/e13-provider-ga-validation-plan.json`
- Linux stage-filter dry-run example:
  - `python scripts/run_provider_ga_validation.py --python python3 --stages provider_circuit_breaker provider_call_audit --dry-run --output -`

## TP-E13-08 Review Queue GA Validation

- Plan report: `docs/current/status/baselines/e13-review-queue-ga-validation-plan.json`
- Runner script: `scripts/run_review_queue_ga_validation.py`
- Default stages: `review_queue_repository`, `review_queue_service`, `review_queue_api`, `review_feedback`, `review_feedback_consumer`
- Linux dry-run example:
  - `python scripts/run_review_queue_ga_validation.py --python python3 --dry-run --output docs/current/status/baselines/e13-review-queue-ga-validation-plan.json`
- Linux stage-filter dry-run example:
  - `python scripts/run_review_queue_ga_validation.py --python python3 --stages review_queue_api review_feedback_consumer --dry-run --output -`

## TP-E13-09 Calibration GA Validation

- Plan report: `docs/current/status/baselines/e13-calibration-ga-validation-plan.json`
- Calibration report: `docs/current/status/baselines/e7-calibration-report.json`
- Runner script: `scripts/run_calibration_ga_validation.py`
- Default stages: `calibration_contract`, `review_policy_contract`, `calibration_report`
- Linux dry-run example:
  - `python scripts/run_calibration_ga_validation.py --python python3 --dry-run --output docs/current/status/baselines/e13-calibration-ga-validation-plan.json`
- Linux stage-filter dry-run example:
  - `python scripts/run_calibration_ga_validation.py --python python3 --stages calibration_report --manifest docs/current/status/baselines/e7-calibration-manifest.json --calibration-report-output docs/current/status/baselines/e7-calibration-report.json --margin 0.03 --dry-run --output -`

## TP-E13-10 Postgres GA Validation

- Plan report: `docs/current/status/baselines/e13-postgres-ga-validation-plan.json`
- Benchmark report: `docs/current/status/baselines/e13-postgres-ga-benchmark-report.json`
- Runner script: `scripts/run_postgres_ga_validation.py`
- Default stages: `postgres_repository_contract`, `postgres_repository_integration`, `dual_write_contract`, `dual_write_integration`, `dual_write_benchmark`
- Linux dry-run example:
  - `python scripts/run_postgres_ga_validation.py --python python3 --dry-run --output docs/current/status/baselines/e13-postgres-ga-validation-plan.json`
- Linux stage-filter dry-run example:
  - `python scripts/run_postgres_ga_validation.py --python python3 --stages dual_write_contract dual_write_benchmark --postgres-dsn "$OMNI_TEST_POSTGRES_DSN" --benchmark-iterations 120 --benchmark-output docs/current/status/baselines/e13-postgres-ga-benchmark-report.json --dry-run --output -`

## TP-E13-11 Roadmap Extension Validation

- Plan report: `docs/current/status/baselines/e13-roadmap-extension-validation-plan.json`
- Runner script: `scripts/run_roadmap_extension_validation.py`
- Default stages: `retrieval_layer`, `lifecycle_engine`, `publication_expansion`, `review_queue_surface`
- Linux dry-run example:
  - `python scripts/run_roadmap_extension_validation.py --python python3 --dry-run --output docs/current/status/baselines/e13-roadmap-extension-validation-plan.json`
- Linux stage-filter dry-run example:
  - `python scripts/run_roadmap_extension_validation.py --python python3 --stages retrieval_layer review_queue_surface --dry-run --output -`

## TP-E13-12 Release Gate Validation

- Top-level plan report: `docs/current/status/baselines/e13-release-gate-validation-plan.json`
- Nested beta gate plan report: `docs/current/status/baselines/e13-release-gate-beta-suite-plan.json`
- Nested GA gate plan report: `docs/current/status/baselines/e13-release-gate-ga-suite-plan.json`
- Nested roadmap gate plan report: `docs/current/status/baselines/e13-release-gate-roadmap-suite-plan.json`
- Runner script: `scripts/run_release_gate_validation.py`
- Default stages: `beta_gate`, `ga_gate`, `roadmap_gate`
- Linux dry-run example:
  - `python scripts/run_release_gate_validation.py --python python3 --dry-run --output docs/current/status/baselines/e13-release-gate-validation-plan.json`
- Linux beta-only dry-run example:
  - `python scripts/run_release_gate_validation.py --python python3 --stages beta_gate --coverage-fail-under 65 --container-image-tag omni-skill-pipeline:beta --dry-run --output -`

## TP-E13-13 Release Switch Decision Validation

- Command plan report: `docs/current/status/baselines/e13-release-switch-validation-plan.json`
- Decision report: `docs/current/status/baselines/e13-release-switch-decision-report.json`
- Runner script: `scripts/run_release_switch_validation.py`
- Default stages: `release_gate`, `release_contract`, `doc_sync`
- Exit code contract: decision `HOLD` returns non-zero by default; use `--allow-hold` to force zero.
- Gate-pack evidence contract: `release-gate-output` + `beta-suite-output` + `ga-suite-output` + `roadmap-suite-output` must all be present, stage-complete, include executable `command` plans, and keep release-gate stage `--output` bindings aligned with provided nested evidence paths before `GO`.
- Linux dry-run example:
  - `python scripts/run_release_switch_validation.py --python python3 --dry-run --output docs/current/status/baselines/e13-release-switch-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`
- Linux decision-only example:
  - `python scripts/run_release_switch_validation.py --decision-only --doc-sync-report docs/current/status/baselines/e13-doc-sync-check-report.json --quality-report docs/current/status/baselines/e11-quality-regression-report.json --perf-report docs/current/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/current/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/current/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/current/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/current/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/current/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`
- Linux HOLD-allow example:
  - `python scripts/run_release_switch_validation.py --decision-only --allow-hold --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`

## TP-E13-14 Release Switch Evidence Pack Hardening

- Validation focus: missing or incomplete release-gate pack evidence must force decision `HOLD`.
- Added testcase:
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_holds_when_release_gate_pack_evidence_missing`
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_holds_when_release_gate_pack_stage_commands_missing`
- TP mapping:
  - `scripts/run_tp_tests.py` -> `TP-E13-14`

## TP-E13-15 Release Switch Evidence Freshness Gate

- Validation focus: stale decision evidence files must force `HOLD` by default.
- Freshness contract:
  - `--max-evidence-age-hours` defaults to `24`
  - `--max-evidence-age-hours 0` disables freshness gate for manual override
- Added testcase:
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_holds_when_evidence_files_are_stale`
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_can_disable_evidence_freshness_gate`
- TP mapping:
  - `scripts/run_tp_tests.py` -> `TP-E13-15`

## TP-E13-16 Release Switch Future-Skew Gate

- Validation focus: decision evidence files with future timestamps beyond skew threshold must force `HOLD`.
- Future-skew contract:
  - `--max-evidence-future-skew-hours` defaults to `0.25`
  - `--max-evidence-future-skew-hours 0` disables future-skew gate for manual override
- Added testcase:
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_holds_when_evidence_files_are_future_skewed`
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_can_disable_future_skew_gate`
- TP mapping:
  - `scripts/run_tp_tests.py` -> `TP-E13-16`

## TP-E13-17 Release Switch Cohort-Skew Gate

- Validation focus: decision evidence files with oversized cross-file timestamp spread must force `HOLD`.
- Cohort-skew contract:
  - `--max-evidence-cohort-skew-hours` defaults to `12`
  - `--max-evidence-cohort-skew-hours 0` disables cohort-skew gate for manual override
- Added testcase:
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_holds_when_evidence_cohort_age_spread_is_too_large`
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_can_disable_evidence_cohort_skew_gate`
- TP mapping:
  - `scripts/run_tp_tests.py` -> `TP-E13-17`

## TP-E13-18 Release Switch Output-Binding Gate

- Validation focus: release-gate stage `--output` paths must stay bound to the same nested evidence files passed into release-switch decision evaluation.
- Output-binding contract:
  - default behavior enforces release-gate `beta_gate/ga_gate/roadmap_gate` output-path alignment
  - stage output mismatch forces `HOLD`
  - `--skip-release-gate-output-binding-check` disables binding gate for manual recovery override
- Added testcase:
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_holds_when_release_gate_stage_outputs_do_not_match_evidence_paths`
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_can_disable_release_gate_output_binding_gate`
- TP mapping:
  - `scripts/run_tp_tests.py` -> `TP-E13-18`
