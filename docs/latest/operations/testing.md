# 测试

## 当前操作入口

`v0.2.6-internal.3` 发版候选的一线操作优先使用本节命令。后面的 TP 附录是历史测试映射和生成记录，主要用于 doc sync 与回归追溯，不是日常操作入口。

本地回归：

```bash
python scripts/ci.py --isolate-test-files --coverage-fail-under 50 --coverage-xml coverage.xml
```

构建或下载 release pack 后，执行 release consumer smoke：

```bash
python scripts/release_consumer_smoke.py --release-dir <release-dir> --expected-release-id <release-tag>
```

最新已发布内部版本示例：

```bash
python scripts/release_consumer_smoke.py --release-dir . --expected-release-id v0.2.6-internal.3
```

本地 artifact 加密回归：

```bash
python -m unittest tests.test_artifact_encryption tests.test_openai_provider_config tests.test_service_factory_split
```

文档同步门禁：

```bash
python scripts/doc_sync.py --output -
```

CI evidence contract:

```bash
python scripts/ci_evidence.py --evidence-dir ci-evidence --fail-on-blocked --print-json
```

The archived CI evidence directory must contain:

- `ci_summary_python_3_11.json`
- `ci_summary_python_3_12.json`
- `coverage.xml`
- `doc_sync.json`
- `release_artifacts.json`
- `release_consumer_smoke.json`
- `launch_gate.json`

`launch_gate.json` may still report `HOLD` while real external loop evidence is incomplete; this command only verifies that CI archived an explicit launch-gate artifact.

Strict launch readiness can require the archived CI evidence explicitly:

```bash
python scripts/launch_gate.py --require-ci-evidence --ci-evidence-report docs/working/status/baselines/ci-matrix/ci_evidence_report.json --print-json
```

The CI evidence report validates the Python 3.11/3.12 matrix summaries, coverage XML, doc-sync output, release artifacts, release consumer smoke, and launch-gate artifact before strict launch readiness can pass.

Strict launch readiness can also require the multimodal quality gate evidence explicitly:

```bash
python scripts/launch_gate.py --require-multimodal-quality-gate --multimodal-quality-gate-report docs/working/status/baselines/real-trial-loop-collection/real-trial-multimodal-quality-gate-report.json --print-json
```

The multimodal quality gate report must be `MULTIMODAL_QUALITY_GATE_READY`, cover text/audio/image/video, have no blocked quality records, and preserve the OCR/ASR fallback and human-review evidence contract.

Strict launch readiness can also require GL-64 real-loop manifest preflight evidence explicitly:

```bash
python scripts/launch_gate.py --require-real-loop-preflight --real-loop-preflight-report docs/working/status/baselines/real-trial-loop-collection/real-trial-loop-manifest-preflight-report.json --print-json
```

The real-loop preflight report must be `REAL_LOOP_MANIFEST_PREFLIGHT_READY`, use `real_trial_loop_manifest_preflight.v1`, have zero missing/invalid/pending items, and have no blocked slot or operator action before launch evidence can pass.

Docker/Postgres/K8s 生产验证不属于 `v0.2.6-internal.3` 的外部生产 ready 声明。只有在具备 Docker 的 host 上，且目标是基础设施验证时，才使用 `bash scripts/linux_release.sh`。

## Standard Linux Release Test

上线前的标准测试入口是 Linux/Docker-only 脚本：

```bash
bash scripts/linux_release.sh
```

该入口只要求宿主 Linux 具备 Docker、基础 shell 工具和项目源码；Python、coverage、测试依赖都在 `omni-skill-pipeline:test` 容器内执行。

可选环境变量：

```bash
export OMNI_TEST_POSTGRES_DSN='postgresql://...'
export OMNI_API_KEY='same-key-used-by-.env.runtime-if-auth-enabled'
export RELEASE_ID="$(date -u +%Y%m%dT%H%M%SZ)"
bash scripts/linux_release.sh
```

产物：

- `release-artifacts/<RELEASE_ID>/summary.tsv`
- `release-artifacts/<RELEASE_ID>/summary.json`
- `release-artifacts/<RELEASE_ID>/logs/*.log`
- `release-artifacts/<RELEASE_ID>/logs/*.exit`
- `release-artifacts/<RELEASE_ID>/baselines/*`
- `release-artifacts-<RELEASE_ID>.tar.gz`

把 `release-artifacts-<RELEASE_ID>.tar.gz` 交给评审者即可复盘每个阶段的日志、退出码、coverage、release switch 证据和最终 GO/HOLD 判定。

## 判词

这个仓当前走的是 `unittest` 体系，不是 `pytest` 体系；测试判断要按现有链路验尸，不要拿错刑具。

## 本地环境对齐

Supported runtime for `v0.2.x`: Python `3.11` and `3.12`. Python `3.13`
is outside the supported matrix until dependency constraints and CI are
updated together.

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
python scripts/ci.py
```

该入口会统一执行：

- Docker 容器内默认按 `tests/test_*.py` 逐文件隔离执行，宿主环境默认使用 `unittest discover`
- `python -m coverage run --parallel-mode -m unittest discover -s tests -p 'test_*.py'`（宿主默认）
- `python scripts/tp_tests.py --all --python <current-python>`
- `python -m coverage combine`
- `python -m coverage report --show-missing --fail-under <threshold>`
- `python -m coverage xml -o coverage.xml`

默认 coverage fail-under 为 `50`，可通过参数覆盖。

示例：提高阈值到 `65`

```bash
python scripts/ci.py --coverage-fail-under 65
```

示例：仅在本地快速验逻辑，临时关闭 coverage

```bash
python scripts/ci.py --no-coverage
```

示例：Docker/Linux 下按文件隔离定位，避免单个大进程被 SIGKILL 后失去具体失败面：

```bash
python scripts/ci.py --keep-going --isolate-test-files
```

示例：只定位 API 相关文件，不跑 TP 套件：

```bash
python scripts/ci.py --no-coverage --keep-going --isolate-test-files --test-pattern 'test_api_*.py' --skip-tp-suite
```

## 容器烟测脚本

容器基线烟测（构建镜像 + 记录 image size + 容器内 CLI smoke + 启动容器 + 轮询 `/healthz`）：

```bash
python scripts/container_smoke.py --image-tag omni-skill-pipeline:local --port 18000
```

只看执行计划，不真正调用 Docker：

```bash
python scripts/container_smoke.py --dry-run
```

GitHub Actions CI 在 Python 3.11/3.12 matrix 成功后也会执行真实 Docker smoke job，并上传 `docker-smoke-evidence` artifact，内含 `container_smoke_report.json` 与 `container_smoke_summary.md`。报告必须记录 image size、`omni-skill --help` CLI smoke、`/healthz` API smoke、container logs 与 cleanup 结果；`--dry-run`、`--skip-build` 或 `--skip-run` 结果不能作为 Docker readiness 证据。

Linux 统一验测时建议直接使用该脚本，作为 `LC-L1-18` 的容器回归入口。

Docker readiness also has two levels. The default command checks the static Dockerfile, `.dockerignore`, container smoke script, CI artifact wiring, and operations docs:

```bash
python scripts/docker_readiness.py --print-json
```

Strict Docker readiness requires live non-dry-run evidence for image build, image size, CLI smoke, container run, `/healthz`, logs, and cleanup; it must be wired into launch gate explicitly:

```bash
python scripts/docker_readiness.py --require-live-evidence --fail-on-blocked --print-json
python scripts/launch_gate.py --require-docker-readiness --docker-readiness-report docs/working/status/baselines/docker-readiness-report.json --print-json
```

Do not treat `--dry-run`, `--skip-build`, or `--skip-run` container smoke output as Docker readiness evidence.

## Dual-Write Benchmark Harness

`LC-L2-33` 引入 dual-write 基准脚本：

```bash
python scripts/bench_dual_write.py --iterations 20 --skip-postgres
python scripts/bench_dual_write.py --iterations 20 --postgres-dsn "$OMNI_TEST_POSTGRES_DSN"
```

- 第一个命令只测 file repository baseline。
- 第二个命令测 file + Postgres dual-write 时延。
- 默认报告落盘：`docs/working/status/baselines/e8-dual-write-benchmark-report.json`。

Postgres/dual-write readiness 需要真实执行报告，不能使用 dry-run 计划替代：

```bash
python scripts/pg_ga.py --postgres-dsn "$OMNI_TEST_POSTGRES_DSN"
python scripts/pg_soak.py --postgres-dsn "$OMNI_TEST_POSTGRES_DSN"
python scripts/bench_dual_write.py --iterations 120 --postgres-dsn "$OMNI_TEST_POSTGRES_DSN" --output docs/working/status/baselines/e13-postgres-soak-benchmark-report.json
python scripts/ops_evidence.py --output docs/working/status/baselines/operations-readiness-report.json --summary-output docs/working/status/baselines/operations-readiness-summary.md
python scripts/postgres_readiness.py --fail-on-blocked --print-json
```

`postgres_readiness.py` only returns `POSTGRES_READINESS_READY` when the Postgres GA report and soak report are `execution_mode=executed` with `decision=PASS`, the benchmark has `run_postgres=true`, schema migration SQL exists, backup/restore operations evidence exists, and the retention policy CLI surface is documented.

Secrets readiness has two levels. The default command checks repo secret hygiene, placeholders, and docs:

```bash
python scripts/secrets_readiness.py --print-json
```

Production secret-management readiness requires external Secret Manager/Vault/KMS evidence and must be wired into launch gate explicitly:

```bash
python scripts/secrets_readiness.py --require-production-manager --fail-on-blocked --print-json
python scripts/launch_gate.py --require-secrets-readiness --secrets-readiness-report docs/working/status/baselines/secrets-readiness-report.json --print-json
```

Do not treat local `.env.example`, `OMNI_ARTIFACT_ENCRYPTION_KEY_ID`, or internal dogfood encryption docs as proof that Vault/KMS/Secret Manager integration is complete.

K8s readiness also has two levels. The default command checks static manifest hygiene only:

```bash
python scripts/k8s_readiness.py --print-json
```

Production Kubernetes readiness requires external cluster evidence and must be wired into launch gate explicitly:

```bash
kubectl apply --dry-run=server -f k8s/
kubectl rollout status deployment/omni-skill-pipeline -n omni-skill-pipeline
kubectl logs deployment/omni-skill-pipeline -n omni-skill-pipeline --tail=200
python scripts/k8s_readiness.py --require-cluster-evidence --fail-on-blocked --print-json
python scripts/launch_gate.py --require-k8s-readiness --k8s-readiness-report docs/working/status/baselines/k8s-readiness-report.json --print-json
```

Do not treat the repository `k8s/` manifests or static readiness report as proof that a live Kubernetes rollout, server-side dry-run, or log inspection has completed.

Product surface readiness also has two levels. The default command checks the P2-5 static beta product-entry contract only:

```bash
python scripts/product_surface_readiness.py --print-json
```

Strict beta product-surface readiness requires live operator evidence covering source intake, job run, generated skill preview, human review, export/validate, evidence/manifest, and launch gate dashboard review:

```bash
python scripts/product_surface_readiness.py --require-live-evidence --fail-on-blocked --print-json
python scripts/launch_gate.py --require-product-surface-readiness --product-surface-readiness-report docs/working/status/baselines/product-surface-readiness-report.json --print-json
```

Do not treat the static API/console surface as proof that a real external beta user completed the workflow.

Observability readiness also has two levels. The default command checks the P2 static observability contract only:

```bash
python scripts/observability_readiness.py --print-json
```

Strict production observability readiness requires live dashboard or evidence-bundle proof covering job duration, job success/fail, retry, modality success rate, human review scores, release artifact build pass/fail, agent smoke pass/fail, and redaction/secret access failures:

```bash
python scripts/observability_readiness.py --require-live-evidence --fail-on-blocked --print-json
python scripts/launch_gate.py --require-observability-readiness --observability-readiness-report docs/working/status/baselines/observability-readiness-report.json --print-json
```

Do not treat the static trial metrics, platform console fields, or release evidence contract as proof that a live production dashboard has been reviewed.

## 定向执行

查看当前已映射 Task Package:

```bash
python scripts/tp_tests.py --list
```

执行单个工单:

```bash
python scripts/tp_tests.py TP-E6-02 --python python
```

执行多个工单:

```bash
python scripts/tp_tests.py TP-E1-01 TP-E1-02 TP-E1-03 TP-E2-01 TP-E2-02 TP-E2-03 TP-E3-01 TP-E3-02 TP-E3-03 TP-E4-01 TP-E4-02 TP-E4-03 TP-E4-04 TP-E4-05 TP-E5-01 TP-E5-02 TP-E5-03 TP-E5-04 TP-E6-01 TP-E6-02 TP-E6-03 TP-E6-04 TP-E7-01 TP-E7-02 TP-E7-03 TP-E7-04 TP-E8-01 TP-E8-02 TP-E8-03 TP-E8-04 TP-E9-01 TP-E9-02 TP-E9-03 TP-E10-01 TP-E10-02 TP-E10-03 TP-E11-01 TP-E11-02 TP-E11-03 TP-E11-04 TP-E12-01 TP-E12-02 TP-E12-03 TP-E12-04 TP-E13-01 TP-E13-02 TP-E13-03 TP-E13-04 TP-E13-05 TP-E13-06 TP-E13-07 TP-E13-08 TP-E13-09 TP-E13-10 TP-E13-11 TP-E13-12 --python python3
```

## 当前覆盖重点

- `tests/test_mvp.py`: 覆盖 text / audio / image / video / tabular 主路径
- `tests/test_v2_schema_and_corpus.py`: 覆盖 corpus 组装、publication、quality、review artifacts
- `tests/test_quality_scoring.py`: 覆盖质量评分
- `tests/test_review_policy.py`: 覆盖 review threshold 与 reason codes
- `tests/test_dual_write_repository.py`: 覆盖 dual-write 主/从仓储行为与失败保护
- `tests/test_bench_dual_write.py`: 覆盖 dual-write benchmark 脚本烟测
- `tests/test_similarity_retrieval.py`: 覆盖检索抽象、inmemory baseline 排序、backend 选型占位行为，以及 whitespace-tags 输入校验与 step/graph overlap 结构化语义加权排序
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
2. 在 `scripts/tp_tests.py` 的 `TP_TEST_CASES` 中登记映射
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
- Added `TP-E12-01` mapping in `scripts/tp_tests.py`.
- Batch example: `python scripts/tp_tests.py TP-E11-02 TP-E11-03 TP-E11-04 TP-E12-01 --python python`.

## TP-E12-02 Additions

- Added provider call audit counters/snapshots in `src/omni_skill_pipeline/providers/openai_provider.py`.
- Added adapter-level provider call metadata in `src/omni_skill_pipeline/adapters/audio.py`, `src/omni_skill_pipeline/adapters/image.py`, and `src/omni_skill_pipeline/adapters/video.py`.
- Added corpus-level provider footprint aggregation in `src/omni_skill_pipeline/service.py`.
- Added `tests/test_provider_audit_tp_e12.py` for provider audit and corpus footprint assertions.
- Added `TP-E12-02` mapping in `scripts/tp_tests.py`.
- Linux batch example: `python scripts/tp_tests.py TP-E12-01 TP-E12-02 --python python3`.

## TP-E12-03 Additions

- Added recursive redaction helpers in `src/omni_skill_pipeline/redaction.py` to sanitize sensitive keys and inline bearer/token-like values.
- Added request/adapter metadata sanitization in `src/omni_skill_pipeline/service.py` before persistence.
- Added repository-side defense-in-depth redaction in `src/omni_skill_pipeline/repository.py` before writing artifact files.
- Added `tests/test_security_redaction_tp_e12.py` for service payload redaction and file artifact persistence redaction assertions.
- Added `TP-E12-03` mapping in `scripts/tp_tests.py`.
- Linux batch example: `python scripts/tp_tests.py TP-E12-01 TP-E12-02 TP-E12-03 --python python3`.

## TP-E12-04 Additions

- Added explicit scratch cleanup status handling in `src/omni_skill_pipeline/adapters/video.py`; cleanup failures now record deferred recovery entries for prune jobs.
- Added intermediate keyframe candidate cleanup in `src/omni_skill_pipeline/providers/media.py` so only selected frames remain during processing.
- Added `tests/test_tmp_artifact_governance_tp_e12.py` to cover success cleanup and deferred cleanup-recovery behavior.
- Added `tests/test_media_provider.py::MediaProcessorTests.test_cleanup_unselected_frames_keeps_selected_only` for intermediate-frame lifecycle cleanup.
- Added `TP-E12-04` mapping in `scripts/tp_tests.py`.
- Linux batch example: `python scripts/tp_tests.py TP-E12-01 TP-E12-02 TP-E12-03 TP-E12-04 --python python3`.

## TP-E13-01 Additions

- Added `scripts/doc_sync.py` to verify README/CLI/API/worker/testing docs stay aligned with source surfaces.
- Extended `scripts/doc_sync.py` with `api_ops_contract_completeness` check for `docs/latest/operations/api.md` (`LC-L1-16` auth/rate-limit/error/health contract).
- Extended `scripts/doc_sync.py` with `launch_beta_runbook_completeness` check for `docs/latest/operations/runbooks/launch-beta.md` (`LC-L1-19` checklist contract).
- Added `tests/test_doc_sync_check_script.py` coverage for API ops-contract incomplete fail-path.
- Added `tests/test_doc_sync_check_script.py` coverage for launch-beta incomplete-contract fail-path.
- Added `TP-E13-01` mapping in `scripts/tp_tests.py`.
- Linux doc sync example: `python scripts/doc_sync.py --output docs/working/status/baselines/e13-doc-sync-check-report.json`.
- Linux batch example: `python scripts/tp_tests.py TP-E12-01 TP-E12-02 TP-E12-03 TP-E12-04 TP-E13-01 --python python3`.

## TP-E13-02 Additions

- Added `docs/latest/architecture/v1-to-v2-migration-guide.md` with migration steps, rollback strategy, and risk register.
- Added `docs/latest/operations/v1-to-v2-migration-runbook.md` with Linux execution and rollback sequence.
- Extended `scripts/doc_sync.py` with `migration_guide_completeness` check and migration doc path args.
- Extended `tests/test_doc_sync_check_script.py` with incomplete-migration-doc fail-path assertions.
- Added `TP-E13-02` mapping in `scripts/tp_tests.py`.
- Linux batch example: `python scripts/tp_tests.py TP-E13-01 TP-E13-02 --python python3`.

## TP-E13-03 Additions

- Added `docs/releases/standards/v2-release-switch-standard.md` with hard-gate rules and cutover/rollback criteria.
- Added `docs/releases/status/2026-04-26-v2-release-switch-standard.md` as the first decision snapshot baseline.
- Extended `scripts/doc_sync.py` with `release_switch_standard_completeness` check and release status doc path args.
- Extended `tests/test_doc_sync_check_script.py` with release-switch incomplete-doc fail-path assertions.
- Added `TP-E13-03` mapping in `scripts/tp_tests.py`.
- Linux batch example: `python scripts/tp_tests.py TP-E13-01 TP-E13-02 TP-E13-03 --python python3`.

## TP-E13-04 Additions

- Added `scripts/linux_validate.py` to orchestrate Linux unified validation stages (`ci`, `container_smoke`, `doc_sync`, `quality_regression`, `perf_cost_baseline`, `postgres_soak`).
- Added `tests/test_linux_validation_suite_script.py` for dry-run plan output, stage-filter behavior, and `container_smoke` option forwarding coverage.
- Added `TP-E13-04` mapping in `scripts/tp_tests.py`.
- Linux dry-run example: `python scripts/linux_validate.py --python python3 --dry-run --output docs/working/status/baselines/e13-linux-validation-suite-plan.json`.
- Linux container-only dry-run example: `python scripts/linux_validate.py --python python3 --stages container_smoke --container-image-tag omni-skill-pipeline:beta --dry-run --output -`.
- Linux execution example: `python scripts/linux_validate.py --python python3`.
- Linux aggregate execution example: `python scripts/linux_validate.py --python python3 --keep-going`; this keeps later stages running after an earlier failure and prints a stage failure summary.

## TP-E13-05 Additions

- Added `scripts/pg_soak.py` to orchestrate Postgres soak command pack (`tp_postgres`, `review_queue`, `dual_write_benchmark`).
- Extended `scripts/linux_validate.py` with `postgres_soak` stage so Linux full-pack can include Postgres long-run validation.
- Added `tests/test_postgres_soak_validation_script.py` for dry-run plan output, stage filtering, benchmark args, and DSN fail-fast behavior.
- Updated `tests/test_linux_validation_suite_script.py` for the new `postgres_soak` stage in default command pack and postgres option forwarding coverage.
- Added `TP-E13-05` mapping in `scripts/tp_tests.py`.
- Linux dry-run example: `python scripts/pg_soak.py --python python3 --dry-run --output docs/working/status/baselines/e13-postgres-soak-plan.json`.
- Linux execution example: `python scripts/pg_soak.py --python python3 --postgres-dsn "$OMNI_TEST_POSTGRES_DSN"`.

## TP-E13-06 Additions

- Added `scripts/worker_ga.py` to orchestrate worker GA-hardening command pack (`worker_corpus`, `worker_retry`, `worker_idempotency`, `worker_claim_lock`, `worker_task_types`).
- Added `tests/test_worker_ga_validation_script.py` for dry-run plan output and stage-filter behavior.
- Extended `scripts/linux_validate.py` with `worker_ga` stage so Linux full-pack can include worker GA hardening validation.
- Updated `tests/test_linux_validation_suite_script.py` with worker_ga stage forwarding coverage.
- Added `TP-E13-06` mapping in `scripts/tp_tests.py`.
- Linux dry-run example: `python scripts/worker_ga.py --python python3 --dry-run --output docs/working/status/baselines/e13-worker-ga-validation-plan.json`.
- Linux stage-only dry-run example: `python scripts/worker_ga.py --python python3 --stages worker_retry worker_claim_lock --dry-run --output -`.

## TP-E13-07 Additions

- Added `scripts/provider_ga.py` to orchestrate provider GA-hardening command pack (`provider_retry`, `provider_circuit_breaker`, `provider_failure_budget`, `provider_config_contract`, `provider_call_audit`, `provider_footprint`).
- Added `tests/test_provider_ga_validation_script.py` for default dry-run plan output and stage-filter behavior.
- Extended `scripts/linux_validate.py` with `provider_ga` stage so Linux full-pack can include provider GA hardening validation.
- Updated `tests/test_linux_validation_suite_script.py` with provider_ga stage forwarding coverage.
- Added `TP-E13-07` mapping in `scripts/tp_tests.py`.
- Linux dry-run example: `python scripts/provider_ga.py --python python3 --dry-run --output docs/working/status/baselines/e13-provider-ga-validation-plan.json`.
- Linux stage-only dry-run example: `python scripts/provider_ga.py --python python3 --stages provider_circuit_breaker provider_call_audit --dry-run --output -`.

## TP-E13-08 Additions

- Added `scripts/ga_review_queue.py` to orchestrate review queue GA-hardening command pack (`review_queue_repository`, `review_queue_service`, `review_queue_api`, `review_feedback`, `review_feedback_consumer`).
- Added `tests/test_review_queue_ga_validation_script.py` for default dry-run plan output and stage-filter behavior.
- Extended `scripts/linux_validate.py` with `review_queue_ga` stage so Linux full-pack can include review queue hardening validation.
- Updated `tests/test_linux_validation_suite_script.py` with review_queue_ga stage forwarding coverage.
- Added `TP-E13-08` mapping in `scripts/tp_tests.py`.
- Linux dry-run example: `python scripts/ga_review_queue.py --python python3 --dry-run --output docs/working/status/baselines/e13-review-queue-ga-validation-plan.json`.
- Linux stage-only dry-run example: `python scripts/ga_review_queue.py --python python3 --stages review_queue_api review_feedback_consumer --dry-run --output -`.

## TP-E13-09 Additions

- Added `scripts/ga_calibration.py` to orchestrate calibration GA-hardening command pack (`calibration_contract`, `review_policy_contract`, `calibration_report`).
- Added `tests/test_calibration_ga_validation_script.py` for default dry-run plan output and calibration option-forwarding behavior.
- Extended `scripts/linux_validate.py` with `calibration_ga` stage so Linux full-pack can include LC-L2-31 threshold calibration validation.
- Updated `tests/test_linux_validation_suite_script.py` with calibration_ga stage forwarding coverage.
- Added `TP-E13-09` mapping in `scripts/tp_tests.py`.
- Linux dry-run example: `python scripts/ga_calibration.py --python python3 --dry-run --output docs/working/status/baselines/e13-calibration-ga-validation-plan.json`.
- Linux stage-only dry-run example: `python scripts/ga_calibration.py --python python3 --stages calibration_report --manifest docs/working/status/baselines/e7-calibration-manifest.json --calibration-report-output docs/working/status/baselines/e7-calibration-report.json --margin 0.03 --dry-run --output -`.

## TP-E13-10 Additions

- Added `scripts/pg_ga.py` to orchestrate Postgres GA-hardening command pack (`postgres_repository_contract`, `postgres_repository_integration`, `dual_write_contract`, `dual_write_integration`, `dual_write_benchmark`).
- Added `tests/test_postgres_ga_validation_script.py` for default dry-run plan output, stage filtering, benchmark option-forwarding, and DSN fail-fast behavior.
- Extended `scripts/linux_validate.py` with `postgres_ga` stage and forwarding for `postgres-dsn`, `postgres-ga-iterations`, `postgres-ga-output`, and benchmark output options.
- Updated `tests/test_linux_validation_suite_script.py` with postgres_ga stage forwarding coverage.
- Added `TP-E13-10` mapping in `scripts/tp_tests.py`.
- Linux dry-run example: `python scripts/pg_ga.py --python python3 --dry-run --output docs/working/status/baselines/e13-postgres-ga-validation-plan.json`.
- Linux stage-only dry-run example: `python scripts/pg_ga.py --python python3 --stages dual_write_contract dual_write_benchmark --postgres-dsn "$OMNI_TEST_POSTGRES_DSN" --benchmark-iterations 120 --benchmark-output docs/working/status/baselines/e13-postgres-ga-benchmark-report.json --dry-run --output -`.

## TP-E13-11 Additions

- Added `scripts/roadmap_ext.py` to orchestrate LC-R-34~37 command pack (`retrieval_layer`, `lifecycle_engine`, `publication_expansion`, `review_queue_surface`).
- Added `tests/test_roadmap_extension_validation_script.py` for default dry-run plan output and stage-filter behavior.
- Extended `scripts/linux_validate.py` with `roadmap_extension` stage and forwarding for `--roadmap-extension-output`.
- Updated `tests/test_linux_validation_suite_script.py` with roadmap_extension stage forwarding coverage.
- Added `TP-E13-11` mapping in `scripts/tp_tests.py`.
- Linux dry-run example: `python scripts/roadmap_ext.py --python python3 --dry-run --output docs/working/status/baselines/e13-roadmap-extension-validation-plan.json`.
- Linux stage-only dry-run example: `python scripts/roadmap_ext.py --python python3 --stages retrieval_layer review_queue_surface --dry-run --output -`.

## TP-E13-12 Additions

- Added `scripts/release_gate.py` to orchestrate release gate command packs (`beta_gate`, `ga_gate`, `roadmap_gate`) by delegating to `scripts/linux_validate.py`.
- Added `tests/test_release_gate_validation_script.py` for default dry-run plan output, beta-only stage forwarding, and ga-stage postgres/calibration option forwarding.
- Added `TP-E13-12` mapping in `scripts/tp_tests.py` and synced `tests/test_tp_registry.py` known-work-order assertions.
- Linux dry-run example: `python scripts/release_gate.py --python python3 --dry-run --output docs/working/status/baselines/e13-release-gate-validation-plan.json`.
- Linux beta-only dry-run example: `python scripts/release_gate.py --python python3 --stages beta_gate --coverage-fail-under 65 --container-image-tag omni-skill-pipeline:beta --dry-run --output -`.

## TP-E13-13 Additions

- Added `scripts/release_switch.py` to orchestrate release-gate + TP contract + doc-sync command packs and emit `GO/HOLD` decision report from evidence files.
- Added `tests/test_release_switch_validation_script.py` for dry-run plan output, release-gate option forwarding, `--decision-only` GO coverage, and HOLD exit-code contract (`1` by default, `0` with `--allow-hold`).
- Added `TP-E13-13` mapping in `scripts/tp_tests.py` and synced work-order registry checks via `tests/test_tp_registry.py`.
- Linux dry-run example: `python scripts/release_switch.py --python python3 --dry-run --output docs/working/status/baselines/e13-release-switch-validation-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.
- Linux decision-only example: `python scripts/release_switch.py --decision-only --doc-sync-report docs/working/status/baselines/e13-doc-sync-check-report.json --quality-report docs/working/status/baselines/e11-quality-regression-report.json --perf-report docs/working/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/working/status/baselines/e13-postgres-soak-benchmark-report.json --ga-suite-output docs/working/status/baselines/e13-release-gate-ga-suite-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.
- Linux decision-only HOLD-allow example: `python scripts/release_switch.py --decision-only --allow-hold --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-14 Additions

- Extended `scripts/release_switch.py` decision evaluation to require full release-gate evidence packs (`release_gate_output` + `beta/ga/roadmap` suite plans) before emitting `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_pack_evidence_missing` to assert missing gate-pack evidence forces `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_pack_stage_commands_missing` to assert non-executable stage packs (missing `command`) force `HOLD`.
- Added `TP-E13-14` mapping in `scripts/tp_tests.py`.
- Linux decision-only full-evidence example: `python scripts/release_switch.py --decision-only --doc-sync-report docs/working/status/baselines/e13-doc-sync-check-report.json --quality-report docs/working/status/baselines/e11-quality-regression-report.json --perf-report docs/working/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/working/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/working/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/working/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/working/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/working/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-15 Additions

- Extended `scripts/release_switch.py` with evidence freshness gate: `--max-evidence-age-hours` (default `24`) now guards decision evidence files against stale reuse.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_evidence_files_are_stale` to assert stale evidence forces `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_evidence_freshness_gate` to assert `--max-evidence-age-hours 0` disables freshness gate for recovery scenarios.
- Added `TP-E13-15` mapping in `scripts/tp_tests.py`.
- Linux decision-only with freshness gate example: `python scripts/release_switch.py --decision-only --max-evidence-age-hours 24 --doc-sync-report docs/working/status/baselines/e13-doc-sync-check-report.json --quality-report docs/working/status/baselines/e11-quality-regression-report.json --perf-report docs/working/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/working/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/working/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/working/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/working/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/working/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-16 Additions

- Extended `scripts/release_switch.py` with future-skew gate: `--max-evidence-future-skew-hours` (default `0.25`) now guards decision evidence against future timestamp drift.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_evidence_files_are_future_skewed` to assert future-skewed evidence forces `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_future_skew_gate` to assert `--max-evidence-future-skew-hours 0` disables future-skew gate for recovery scenarios.
- Added `TP-E13-16` mapping in `scripts/tp_tests.py`.
- Linux decision-only with future-skew gate example: `python scripts/release_switch.py --decision-only --max-evidence-future-skew-hours 0.25 --doc-sync-report docs/working/status/baselines/e13-doc-sync-check-report.json --quality-report docs/working/status/baselines/e11-quality-regression-report.json --perf-report docs/working/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/working/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/working/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/working/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/working/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/working/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-17 Additions

- Extended `scripts/release_switch.py` with cohort-skew gate: `--max-evidence-cohort-skew-hours` (default `12`) now guards decision evidence against mixed-batch timestamp spread.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_evidence_cohort_age_spread_is_too_large` to assert oversized evidence age spread forces `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_evidence_cohort_skew_gate` to assert `--max-evidence-cohort-skew-hours 0` disables cohort-skew gate for recovery scenarios.
- Added `TP-E13-17` mapping in `scripts/tp_tests.py`.
- Linux decision-only with cohort-skew gate example: `python scripts/release_switch.py --decision-only --max-evidence-cohort-skew-hours 12 --doc-sync-report docs/working/status/baselines/e13-doc-sync-check-report.json --quality-report docs/working/status/baselines/e11-quality-regression-report.json --perf-report docs/working/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/working/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/working/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/working/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/working/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/working/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-18 Additions

- Extended `scripts/release_switch.py` with release-gate output-binding gate: release-gate stage `--output` paths must match `--beta-suite-output/--ga-suite-output/--roadmap-suite-output` evidence inputs before `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_outputs_do_not_match_evidence_paths` to assert path-binding drift forces `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_output_binding_gate` to assert `--skip-release-gate-output-binding-check` disables the binding gate for emergency recovery.
- Added `TP-E13-18` mapping in `scripts/tp_tests.py`.
- Linux decision-only with binding gate example: `python scripts/release_switch.py --decision-only --doc-sync-report docs/working/status/baselines/e13-doc-sync-check-report.json --quality-report docs/working/status/baselines/e11-quality-regression-report.json --perf-report docs/working/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/working/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/working/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/working/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/working/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/working/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.


## TP-E13-19 Additions

- Extended `scripts/release_switch.py` with release-gate stage-contract gate: decision now validates each release-gate stage command targets `scripts/linux_validate.py` and keeps expected `--stages` packs before `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_contract_mismatches` to assert stage-contract drift forces `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_stage_contract_gate` to assert `--skip-release-gate-stage-contract-check` disables the stage-contract gate for emergency recovery.
- Added `TP-E13-19` mapping in `scripts/tp_tests.py`.
- Linux decision-only with stage-contract gate example: `python scripts/release_switch.py --decision-only --doc-sync-report docs/working/status/baselines/e13-doc-sync-check-report.json --quality-report docs/working/status/baselines/e11-quality-regression-report.json --perf-report docs/working/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/working/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/working/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/working/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/working/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/working/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-20 Additions

- Extended `scripts/release_switch.py` with release-gate option-override gate: decision now validates `beta_gate/ga_gate/roadmap_gate` commands contain exactly one `--stages` and one `--output` option before `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_options_are_ambiguous` to assert repeated `--stages/--output` options force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_option_override_gate` to assert `--skip-release-gate-option-override-check` disables the option-override gate for emergency recovery.
- Added `TP-E13-20` mapping in `scripts/tp_tests.py`.
- Linux decision-only with option-override gate example: `python scripts/release_switch.py --decision-only --doc-sync-report docs/working/status/baselines/e13-doc-sync-check-report.json --quality-report docs/working/status/baselines/e11-quality-regression-report.json --perf-report docs/working/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/working/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/working/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/working/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/working/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/working/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-21 Additions

- Extended `scripts/release_switch.py` with release-gate relaxed-flags gate: decision now blocks `GO` when release-gate commands include `--allow-regression/--no-coverage/--container-skip-build/--container-skip-run/--allow-secondary-failures`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_relaxed_flags` to assert relaxed flags force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_relaxed_flags_gate` to assert `--skip-release-gate-relaxed-flags-check` disables the relaxed-flags gate for emergency recovery.
- Added `TP-E13-21` mapping in `scripts/tp_tests.py`.
- Linux decision-only with relaxed-flags gate example: `python scripts/release_switch.py --decision-only --doc-sync-report docs/working/status/baselines/e13-doc-sync-check-report.json --quality-report docs/working/status/baselines/e11-quality-regression-report.json --perf-report docs/working/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/working/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/working/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/working/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/working/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/working/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-22 Additions

- Extended `scripts/release_switch.py` with release-gate dry-run gate: decision now blocks `GO` when release-gate stage commands include `--dry-run` pseudo-execution flags.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_dry_run_flag` to assert `--dry-run` in release-gate stage commands forces `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_dry_run_gate` to assert `--skip-release-gate-dry-run-check` disables the dry-run gate for emergency recovery.
- Added `TP-E13-22` mapping in `scripts/tp_tests.py`.
- Linux decision-only with dry-run gate example: `python scripts/release_switch.py --decision-only --doc-sync-report docs/working/status/baselines/e13-doc-sync-check-report.json --quality-report docs/working/status/baselines/e11-quality-regression-report.json --perf-report docs/working/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/working/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/working/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/working/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/working/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/working/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-23 Additions

- Extended `scripts/release_switch.py` with release-gate script-position gate: decision now requires each release-gate stage to execute `scripts/linux_validate.py` as the first script token, preventing decoy-token spoofing from producing false `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_script_position_is_decoy` to assert decoy script-token plans force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_script_position_gate` to assert `--skip-release-gate-script-position-check` disables the script-position gate for emergency recovery.
- Added `TP-E13-23` mapping in `scripts/tp_tests.py`.
- Linux decision-only with script-position gate example: `python scripts/release_switch.py --decision-only --doc-sync-report docs/working/status/baselines/e13-doc-sync-check-report.json --quality-report docs/working/status/baselines/e11-quality-regression-report.json --perf-report docs/working/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/working/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/working/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/working/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/working/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/working/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-24 Additions

- Extended `scripts/release_switch.py` with release-gate inline-exec gate: decision now blocks `GO` when release-gate stage commands use python inline-dispatch flags (`-c`, `-m`, `-`) before `scripts/linux_validate.py` script token.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_inline_exec_flag` to assert inline-dispatch bypass plans force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_inline_exec_gate` to assert `--skip-release-gate-inline-exec-check` disables the inline-exec gate for emergency recovery.
- Added `TP-E13-24` mapping in `scripts/tp_tests.py`.
- Linux decision-only with inline-exec gate example: `python scripts/release_switch.py --decision-only --doc-sync-report docs/working/status/baselines/e13-doc-sync-check-report.json --quality-report docs/working/status/baselines/e11-quality-regression-report.json --perf-report docs/working/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/working/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/working/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/working/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/working/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/working/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-25 Additions

- Extended `scripts/release_switch.py` with release-gate script-anchor gate: decision now requires release-gate stage commands to resolve `scripts/linux_validate.py` to repository canonical path before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_script_path_is_not_repo_canonical` to assert same-name external script path spoofing forces `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_script_anchor_gate` to assert `--skip-release-gate-script-anchor-check` disables the script-anchor gate for emergency recovery.
- Added `TP-E13-25` mapping in `scripts/tp_tests.py`.
- Linux decision-only with script-anchor gate example: `python scripts/release_switch.py --decision-only --doc-sync-report docs/working/status/baselines/e13-doc-sync-check-report.json --quality-report docs/working/status/baselines/e11-quality-regression-report.json --perf-report docs/working/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/working/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/working/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/working/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/working/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/working/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-26 Additions

- Extended `scripts/release_switch.py` with release-gate python-binding gate: decision now requires each release-gate stage command to keep `--python` single-occurrence, value-equal to release-switch `--python`, and launcher-prefix consistent with that value before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_python_binding_mismatches` to assert `--python` drift in release-gate stage commands forces `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_python_binding_gate` to assert `--skip-release-gate-python-binding-check` disables the python-binding gate for emergency recovery.
- Added `TP-E13-26` mapping in `scripts/tp_tests.py`.
- Linux decision-only with python-binding gate example: `python scripts/release_switch.py --decision-only --python python3 --doc-sync-report docs/working/status/baselines/e13-doc-sync-check-report.json --quality-report docs/working/status/baselines/e11-quality-regression-report.json --perf-report docs/working/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/working/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/working/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/working/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/working/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/working/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-27 Additions

- Extended `scripts/release_switch.py` with release-gate coverage-floor gate: decision now requires `beta_gate` to keep `--coverage-fail-under` value bound to release-switch input and not lower than `50` before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_coverage_floor_is_downgraded` to assert coverage-threshold downgrade forces `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_coverage_floor_gate` to assert `--skip-release-gate-coverage-floor-check` disables the coverage-floor gate for emergency recovery.
- Added `TP-E13-27` mapping in `scripts/tp_tests.py`.
- Linux decision-only with coverage-floor gate example: `python scripts/release_switch.py --decision-only --coverage-fail-under 50 --doc-sync-report docs/working/status/baselines/e13-doc-sync-check-report.json --quality-report docs/working/status/baselines/e11-quality-regression-report.json --perf-report docs/working/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/working/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/working/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/working/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/working/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/working/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-28 Additions

- Extended `scripts/release_switch.py` with release-gate python-optimization gate: decision now requires `beta_gate/ga_gate/roadmap_gate` launchers to avoid python optimization flags (`-O`, `-OO`) before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_python_optimization_flag` to assert python optimization flags force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_python_optimization_gate` to assert `--skip-release-gate-python-optimization-check` disables the gate for emergency recovery.
- Added `TP-E13-28` mapping in `scripts/tp_tests.py`.
- Linux decision-only with python-optimization gate example: `python scripts/release_switch.py --decision-only --python "python3 -O" --doc-sync-report docs/working/status/baselines/e13-doc-sync-check-report.json --quality-report docs/working/status/baselines/e11-quality-regression-report.json --perf-report docs/working/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/working/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/working/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/working/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/working/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/working/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-29 Additions

- Extended `scripts/release_switch.py` with release-gate python-option-optimization gate: decision now requires `beta_gate/ga_gate/roadmap_gate` `--python` relay values to avoid python optimization flags (`-O`, `-OO`) before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_python_option_uses_optimization_flag` to assert optimization flags in stage `--python` relay values force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_python_option_optimization_gate` to assert `--skip-release-gate-python-option-optimization-check` disables the gate for emergency recovery.
- Added `TP-E13-29` mapping in `scripts/tp_tests.py`.
- Linux decision-only with python-option-optimization gate example: `python scripts/release_switch.py --decision-only --skip-release-gate-python-binding-check --doc-sync-report docs/working/status/baselines/e13-doc-sync-check-report.json --quality-report docs/working/status/baselines/e11-quality-regression-report.json --perf-report docs/working/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/working/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/working/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/working/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/working/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/working/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-30 Additions

- Extended `scripts/release_switch.py` with release-gate python-optimize-env gate: decision now rejects `PYTHONOPTIMIZE=*` assignments in stage launchers and `--python` relay values before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_python_optimize_env_assignment` to assert `PYTHONOPTIMIZE` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_python_optimize_env_gate` to assert `--skip-release-gate-python-optimize-env-check` disables the gate for emergency recovery.
- Added `TP-E13-30` mapping in `scripts/tp_tests.py`.
- Linux decision-only with python-optimize-env gate example: `python scripts/release_switch.py --decision-only --python "env PYTHONOPTIMIZE=2 python3" --doc-sync-report docs/working/status/baselines/e13-doc-sync-check-report.json --quality-report docs/working/status/baselines/e11-quality-regression-report.json --perf-report docs/working/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/working/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/working/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/working/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/working/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/working/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-31 Additions

- Extended `scripts/release_switch.py` with release-gate python-option-inline-exec gate: decision now rejects `--python` relay values that include inline-dispatch flags (`-c`, `-m`, `-`) before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_python_option_uses_inline_exec_flag` to assert inline-dispatch flags in stage `--python` relay values force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_python_option_inline_exec_gate` to assert `--skip-release-gate-python-option-inline-exec-check` disables the gate for emergency recovery.
- Added `TP-E13-31` mapping in `scripts/tp_tests.py`.
- Linux decision-only with python-option-inline-exec gate example: `python scripts/release_switch.py --decision-only --skip-release-gate-python-binding-check --doc-sync-report docs/working/status/baselines/e13-doc-sync-check-report.json --quality-report docs/working/status/baselines/e11-quality-regression-report.json --perf-report docs/working/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/working/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/working/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/working/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/working/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/working/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-32 Additions

- Extended `scripts/release_switch.py` with release-gate python-path-env gate: decision now rejects `PYTHONPATH=*` assignments in stage launchers and `--python` relay values before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_python_path_env_assignment` to assert `PYTHONPATH` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_python_path_env_gate` to assert `--skip-release-gate-python-path-env-check` disables the gate for emergency recovery.
- Added `TP-E13-32` mapping in `scripts/tp_tests.py`.
- Linux decision-only with python-path-env gate example: `python scripts/release_switch.py --decision-only --python "env PYTHONPATH=/tmp/rogue python3" --doc-sync-report docs/working/status/baselines/e13-doc-sync-check-report.json --quality-report docs/working/status/baselines/e11-quality-regression-report.json --perf-report docs/working/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/working/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/working/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/working/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/working/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/working/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-33 Additions

- Extended `scripts/release_switch.py` with release-gate python-home-env gate: decision now rejects `PYTHONHOME=*` assignments in stage launchers and `--python` relay values before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_python_home_env_assignment` to assert `PYTHONHOME` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_python_home_env_gate` to assert `--skip-release-gate-python-home-env-check` disables the gate for emergency recovery.
- Added `TP-E13-33` mapping in `scripts/tp_tests.py`.
- Linux decision-only with python-home-env gate example: `python scripts/release_switch.py --decision-only --python "env PYTHONHOME=/tmp/rogue-home python3" --doc-sync-report docs/working/status/baselines/e13-doc-sync-check-report.json --quality-report docs/working/status/baselines/e11-quality-regression-report.json --perf-report docs/working/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/working/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/working/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/working/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/working/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/working/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-34 Additions

- Extended `scripts/release_switch.py` with release-gate python-user-base-env gate: decision now rejects `PYTHONUSERBASE=*` assignments in stage launchers and `--python` relay values before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_python_user_base_env_assignment` to assert `PYTHONUSERBASE` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_python_user_base_env_gate` to assert `--skip-release-gate-python-user-base-env-check` disables the gate for emergency recovery.
- Added `TP-E13-34` mapping in `scripts/tp_tests.py`.
- Linux decision-only with python-user-base-env gate example: `python scripts/release_switch.py --decision-only --python "env PYTHONUSERBASE=/tmp/rogue-userbase python3" --doc-sync-report docs/working/status/baselines/e13-doc-sync-check-report.json --quality-report docs/working/status/baselines/e11-quality-regression-report.json --perf-report docs/working/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/working/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/working/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/working/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/working/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/working/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-35 Additions

- Extended `scripts/release_switch.py` with release-gate python-breakpoint-env gate: decision now rejects `PYTHONBREAKPOINT=*` assignments in stage launchers and `--python` relay values before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_python_breakpoint_env_assignment` to assert `PYTHONBREAKPOINT` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_python_breakpoint_env_gate` to assert `--skip-release-gate-python-breakpoint-env-check` disables the gate for emergency recovery.
- Added `TP-E13-35` mapping in `scripts/tp_tests.py`.
- Linux decision-only with python-breakpoint-env gate example: `python scripts/release_switch.py --decision-only --python "env PYTHONBREAKPOINT=evil.hook python3" --doc-sync-report docs/working/status/baselines/e13-doc-sync-check-report.json --quality-report docs/working/status/baselines/e11-quality-regression-report.json --perf-report docs/working/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/working/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/working/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/working/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/working/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/working/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-36 Additions

- Extended `scripts/release_switch.py` with release-gate python-startup-env gate: decision now rejects `PYTHONSTARTUP=*` assignments in stage launchers and `--python` relay values before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_python_startup_env_assignment` to assert `PYTHONSTARTUP` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_python_startup_env_gate` to assert `--skip-release-gate-python-startup-env-check` disables the gate for emergency recovery.
- Added `TP-E13-36` mapping in `scripts/tp_tests.py`.
- Linux decision-only with python-startup-env gate example: `python scripts/release_switch.py --decision-only --python "env PYTHONSTARTUP=/tmp/evil-startup.py python3" --doc-sync-report docs/working/status/baselines/e13-doc-sync-check-report.json --quality-report docs/working/status/baselines/e11-quality-regression-report.json --perf-report docs/working/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/working/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/working/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/working/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/working/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/working/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-37 Additions

- Extended `scripts/release_switch.py` with release-gate python-inspect-env gate: decision now rejects `PYTHONINSPECT=*` assignments in stage launchers and `--python` relay values before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_python_inspect_env_assignment` to assert `PYTHONINSPECT` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_python_inspect_env_gate` to assert `--skip-release-gate-python-inspect-env-check` disables the gate for emergency recovery.
- Added `TP-E13-37` mapping in `scripts/tp_tests.py`.
- Linux decision-only with python-inspect-env gate example: `python scripts/release_switch.py --decision-only --python "env PYTHONINSPECT=1 python3" --doc-sync-report docs/working/status/baselines/e13-doc-sync-check-report.json --quality-report docs/working/status/baselines/e11-quality-regression-report.json --perf-report docs/working/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/working/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/working/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/working/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/working/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/working/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-38 Additions

- Extended `scripts/release_switch.py` with release-gate python-warnings-env gate: decision now rejects `PYTHONWARNINGS=*` assignments in stage launchers and `--python` relay values before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_python_warnings_env_assignment` to assert `PYTHONWARNINGS` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_python_warnings_env_gate` to assert `--skip-release-gate-python-warnings-env-check` disables the gate for emergency recovery.
- Added `TP-E13-38` mapping in `scripts/tp_tests.py`.
- Linux decision-only with python-warnings-env gate example: `python scripts/release_switch.py --decision-only --python "env PYTHONWARNINGS=ignore python3" --doc-sync-report docs/working/status/baselines/e13-doc-sync-check-report.json --quality-report docs/working/status/baselines/e11-quality-regression-report.json --perf-report docs/working/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/working/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/working/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/working/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/working/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/working/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-39 Additions

- Extended `scripts/release_switch.py` with release-gate python-env-wildcard gate: decision now rejects unknown `PYTHON*` assignments in stage launchers and `--python` relay values (already-registered gate keys excluded) before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_unknown_python_env_assignment` to assert unknown `PYTHON*` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_python_env_wildcard_gate` to assert `--skip-release-gate-python-env-wildcard-check` disables the gate for emergency recovery.
- Added `TP-E13-39` mapping in `scripts/tp_tests.py`.
- Linux decision-only with python-env-wildcard gate example: `python scripts/release_switch.py --decision-only --python "env PYTHONUNBUFFERED=1 python3" --doc-sync-report docs/working/status/baselines/e13-doc-sync-check-report.json --quality-report docs/working/status/baselines/e11-quality-regression-report.json --perf-report docs/working/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/working/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/working/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/working/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/working/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/working/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-40 Additions

- Extended `scripts/release_switch.py` with release-gate path-env gate: decision now rejects `PATH=*` assignments in stage launchers and `--python` relay values before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_path_env_assignment` to assert `PATH` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_path_env_gate` to assert `--skip-release-gate-path-env-check` disables the gate for emergency recovery.
- Added `TP-E13-40` mapping in `scripts/tp_tests.py`.
- Linux decision-only with path-env gate example: `python scripts/release_switch.py --decision-only --python "env PATH=/tmp/rogue python3" --doc-sync-report docs/working/status/baselines/e13-doc-sync-check-report.json --quality-report docs/working/status/baselines/e11-quality-regression-report.json --perf-report docs/working/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/working/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/working/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/working/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/working/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/working/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-41 Additions

- Extended `scripts/release_switch.py` with release-gate ld-preload-env gate: decision now rejects `LD_PRELOAD=*` assignments in stage launchers and `--python` relay values before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_ld_preload_env_assignment` to assert `LD_PRELOAD` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_ld_preload_env_gate` to assert `--skip-release-gate-ld-preload-env-check` disables the gate for emergency recovery.
- Added `TP-E13-41` mapping in `scripts/tp_tests.py`.
- Linux decision-only with ld-preload-env gate example: `python scripts/release_switch.py --decision-only --python "env LD_PRELOAD=/tmp/evil.so python3" --doc-sync-report docs/working/status/baselines/e13-doc-sync-check-report.json --quality-report docs/working/status/baselines/e11-quality-regression-report.json --perf-report docs/working/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/working/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/working/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/working/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/working/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/working/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-42 Additions

- Extended `scripts/release_switch.py` with release-gate ld-library-path-env gate: decision now rejects `LD_LIBRARY_PATH=*` assignments in stage launchers and `--python` relay values before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_ld_library_path_env_assignment` to assert `LD_LIBRARY_PATH` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_ld_library_path_env_gate` to assert `--skip-release-gate-ld-library-path-env-check` disables the gate for emergency recovery.
- Added `TP-E13-42` mapping in `scripts/tp_tests.py`.
- Linux decision-only with ld-library-path-env gate example: `python scripts/release_switch.py --decision-only --python "env LD_LIBRARY_PATH=/tmp/evil-lib python3" --doc-sync-report docs/working/status/baselines/e13-doc-sync-check-report.json --quality-report docs/working/status/baselines/e11-quality-regression-report.json --perf-report docs/working/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/working/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/working/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/working/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/working/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/working/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-43 Additions

- Extended `scripts/release_switch.py` with release-gate ld-audit-env gate: decision now rejects `LD_AUDIT=*` assignments in stage launchers and `--python` relay values before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_ld_audit_env_assignment` to assert `LD_AUDIT` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_ld_audit_env_gate` to assert `--skip-release-gate-ld-audit-env-check` disables the gate for emergency recovery.
- Added `TP-E13-43` mapping in `scripts/tp_tests.py`.
- Linux decision-only with ld-audit-env gate example: `python scripts/release_switch.py --decision-only --python "env LD_AUDIT=/tmp/evil.audit.so python3" --doc-sync-report docs/working/status/baselines/e13-doc-sync-check-report.json --quality-report docs/working/status/baselines/e11-quality-regression-report.json --perf-report docs/working/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/working/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/working/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/working/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/working/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/working/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-44 Additions

- Extended `scripts/release_switch.py` with release-gate ld-env-wildcard gate: decision now rejects unknown `LD_*` assignments in stage launchers and `--python` relay values (already-registered gate keys excluded) before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_unknown_ld_env_assignment` to assert unknown `LD_*` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_ld_env_wildcard_gate` to assert `--skip-release-gate-ld-env-wildcard-check` disables the gate for emergency recovery.
- Added `TP-E13-44` mapping in `scripts/tp_tests.py`.
- Linux decision-only with ld-env-wildcard gate example: `python scripts/release_switch.py --decision-only --python "env LD_DEBUG=files python3" --doc-sync-report docs/working/status/baselines/e13-doc-sync-check-report.json --quality-report docs/working/status/baselines/e11-quality-regression-report.json --perf-report docs/working/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/working/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/working/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/working/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/working/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/working/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-45 Additions

- Extended `scripts/release_switch.py` with release-gate glibc-tunables-env gate: decision now rejects `GLIBC_TUNABLES=*` assignments in stage launchers and `--python` relay values before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_glibc_tunables_env_assignment` to assert `GLIBC_TUNABLES` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_glibc_tunables_env_gate` to assert `--skip-release-gate-glibc-tunables-env-check` disables the gate for emergency recovery.
- Added `TP-E13-45` mapping in `scripts/tp_tests.py`.
- Linux decision-only with glibc-tunables-env gate example: `python scripts/release_switch.py --decision-only --python "env GLIBC_TUNABLES=glibc.malloc.check=3 python3" --doc-sync-report docs/working/status/baselines/e13-doc-sync-check-report.json --quality-report docs/working/status/baselines/e11-quality-regression-report.json --perf-report docs/working/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/working/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/working/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/working/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/working/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/working/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-46 Additions

- Extended `scripts/release_switch.py` with release-gate glibc-env-wildcard gate: decision now rejects unknown `GLIBC_*` assignments (registered gate keys excluded) in stage launchers and `--python` relay values before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_unknown_glibc_env_assignment` to assert unknown `GLIBC_*` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_glibc_env_wildcard_gate` to assert `--skip-release-gate-glibc-env-wildcard-check` disables the gate for emergency recovery.
- Added `TP-E13-46` mapping in `scripts/tp_tests.py`.
- Linux decision-only with glibc-env-wildcard gate example: `python scripts/release_switch.py --decision-only --python "env GLIBC_MEMUSAGE=1 python3" --doc-sync-report docs/working/status/baselines/e13-doc-sync-check-report.json --quality-report docs/working/status/baselines/e11-quality-regression-report.json --perf-report docs/working/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/working/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/working/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/working/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/working/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/working/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-47 Additions

- Extended `scripts/release_switch.py` with release-gate malloc-env-wildcard gate: decision now rejects unknown `MALLOC_*` assignments (registered gate keys excluded) in stage launchers and `--python` relay values before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_unknown_malloc_env_assignment` to assert unknown `MALLOC_*` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_malloc_env_wildcard_gate` to assert `--skip-release-gate-malloc-env-wildcard-check` disables the gate for emergency recovery.
- Added `TP-E13-47` mapping in `scripts/tp_tests.py`.
- Linux decision-only with malloc-env-wildcard gate example: `python scripts/release_switch.py --decision-only --python "env MALLOC_SHADOW_POLICY=strict python3" --doc-sync-report docs/working/status/baselines/e13-doc-sync-check-report.json --quality-report docs/working/status/baselines/e11-quality-regression-report.json --perf-report docs/working/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/working/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/working/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/working/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/working/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/working/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-48 Additions

- Extended `scripts/release_switch.py` with release-gate malloc-trace-env gate: decision now rejects `MALLOC_TRACE=*` assignments in stage launchers and `--python` relay values before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_malloc_trace_env_assignment` to assert `MALLOC_TRACE` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_malloc_trace_env_gate` to assert `--skip-release-gate-malloc-trace-env-check` disables the gate for emergency recovery.
- Added `TP-E13-48` mapping in `scripts/tp_tests.py`.
- Linux decision-only with malloc-trace-env gate example: `python scripts/release_switch.py --decision-only --python "env MALLOC_TRACE=/tmp/mtrace.log python3" --doc-sync-report docs/working/status/baselines/e13-doc-sync-check-report.json --quality-report docs/working/status/baselines/e11-quality-regression-report.json --perf-report docs/working/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/working/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/working/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/working/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/working/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/working/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-49 Additions

- Extended `scripts/release_switch.py` with release-gate malloc-check-env gate: decision now rejects `MALLOC_CHECK_=*` assignments in stage launchers and `--python` relay values before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_malloc_check_env_assignment` to assert `MALLOC_CHECK_` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_malloc_check_env_gate` to assert `--skip-release-gate-malloc-check-env-check` disables the gate for emergency recovery.
- Added `TP-E13-49` mapping in `scripts/tp_tests.py`.
- Linux decision-only with malloc-check-env gate example: `python scripts/release_switch.py --decision-only --python "env MALLOC_CHECK_=3 python3" --doc-sync-report docs/working/status/baselines/e13-doc-sync-check-report.json --quality-report docs/working/status/baselines/e11-quality-regression-report.json --perf-report docs/working/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/working/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/working/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/working/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/working/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/working/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-50 Additions

- Extended `scripts/release_switch.py` with release-gate malloc-perturb-env gate: decision now rejects `MALLOC_PERTURB_=*` assignments in stage launchers and `--python` relay values before allowing `GO`.
- Updated `tests/test_release_switch_validation_script.py` malloc wildcard gate fixtures to use unknown `MALLOC_SHADOW_POLICY=*` so wildcard coverage stays focused on unknown keys after `MALLOC_ARENA_MAX` becomes a dedicated gate.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_malloc_perturb_env_assignment` to assert `MALLOC_PERTURB_` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_malloc_perturb_env_gate` to assert `--skip-release-gate-malloc-perturb-env-check` disables the gate for emergency recovery.
- Added `TP-E13-50` mapping in `scripts/tp_tests.py`.
- Linux decision-only with malloc-perturb-env gate example: `python scripts/release_switch.py --decision-only --python "env MALLOC_PERTURB_=153 python3" --doc-sync-report docs/working/status/baselines/e13-doc-sync-check-report.json --quality-report docs/working/status/baselines/e11-quality-regression-report.json --perf-report docs/working/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/working/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/working/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/working/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/working/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/working/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-51 Additions

- Extended `scripts/release_switch.py` with release-gate malloc-arena-max-env gate: decision now rejects `MALLOC_ARENA_MAX=*` assignments in stage launchers and `--python` relay values before allowing `GO`.
- Updated `tests/test_release_switch_validation_script.py` malloc wildcard gate fixtures to use unknown `MALLOC_SHADOW_POLICY=*` so wildcard coverage remains unknown-key focused after `MALLOC_ARENA_MAX` becomes a dedicated gate.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_malloc_arena_max_env_assignment` to assert `MALLOC_ARENA_MAX` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_malloc_arena_max_env_gate` to assert `--skip-release-gate-malloc-arena-max-env-check` disables the gate for emergency recovery.
- Added `TP-E13-51` mapping in `scripts/tp_tests.py`.
- Linux decision-only with malloc-arena-max-env gate example: `python scripts/release_switch.py --decision-only --python "env MALLOC_ARENA_MAX=8 python3" --doc-sync-report docs/working/status/baselines/e13-doc-sync-check-report.json --quality-report docs/working/status/baselines/e11-quality-regression-report.json --perf-report docs/working/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/working/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/working/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/working/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/working/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/working/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-52 Additions

- Extended `scripts/release_switch.py` with release-gate malloc-mmap-threshold-env gate: decision now rejects `MALLOC_MMAP_THRESHOLD_=*` assignments in stage launchers and `--python` relay values before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_malloc_mmap_threshold_env_assignment` to assert `MALLOC_MMAP_THRESHOLD_` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_malloc_mmap_threshold_env_gate` to assert `--skip-release-gate-malloc-mmap-threshold-env-check` disables the gate for emergency recovery.
- Added `TP-E13-52` mapping in `scripts/tp_tests.py`.
- Linux decision-only with malloc-mmap-threshold-env gate example: `python scripts/release_switch.py --decision-only --python "env MALLOC_MMAP_THRESHOLD_=131072 python3" --doc-sync-report docs/working/status/baselines/e13-doc-sync-check-report.json --quality-report docs/working/status/baselines/e11-quality-regression-report.json --perf-report docs/working/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/working/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/working/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/working/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/working/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/working/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-53 Additions

- Extended `scripts/release_switch.py` with release-gate malloc-mmap-max-env gate: decision now rejects `MALLOC_MMAP_MAX_=*` assignments in stage launchers and `--python` relay values before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_malloc_mmap_max_env_assignment` to assert `MALLOC_MMAP_MAX_` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_malloc_mmap_max_env_gate` to assert `--skip-release-gate-malloc-mmap-max-env-check` disables the gate for emergency recovery.
- Added `TP-E13-53` mapping in `scripts/tp_tests.py`.
- Linux decision-only with malloc-mmap-max-env gate example: `python scripts/release_switch.py --decision-only --python "env MALLOC_MMAP_MAX_=256 python3" --doc-sync-report docs/working/status/baselines/e13-doc-sync-check-report.json --quality-report docs/working/status/baselines/e11-quality-regression-report.json --perf-report docs/working/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/working/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/working/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/working/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/working/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/working/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-54 Additions

- Extended `scripts/release_switch.py` with release-gate malloc-top-pad-env gate: decision now rejects `MALLOC_TOP_PAD_=*` assignments in stage launchers and `--python` relay values before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_malloc_top_pad_env_assignment` to assert `MALLOC_TOP_PAD_` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_malloc_top_pad_env_gate` to assert `--skip-release-gate-malloc-top-pad-env-check` disables the gate for emergency recovery.
- Added `TP-E13-54` mapping in `scripts/tp_tests.py`.
- Linux decision-only with malloc-top-pad-env gate example: `python scripts/release_switch.py --decision-only --python "env MALLOC_TOP_PAD_=131072 python3" --doc-sync-report docs/working/status/baselines/e13-doc-sync-check-report.json --quality-report docs/working/status/baselines/e11-quality-regression-report.json --perf-report docs/working/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/working/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/working/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/working/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/working/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/working/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-55 Additions

- Extended `scripts/release_switch.py` with release-gate malloc-trim-threshold-env gate: decision now rejects `MALLOC_TRIM_THRESHOLD_=*` assignments in stage launchers and `--python` relay values before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_malloc_trim_threshold_env_assignment` to assert `MALLOC_TRIM_THRESHOLD_` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_malloc_trim_threshold_env_gate` to assert `--skip-release-gate-malloc-trim-threshold-env-check` disables the gate for emergency recovery.
- Added `TP-E13-55` mapping in `scripts/tp_tests.py`.
- Linux decision-only with malloc-trim-threshold-env gate example: `python scripts/release_switch.py --decision-only --python "env MALLOC_TRIM_THRESHOLD_=262144 python3" --doc-sync-report docs/working/status/baselines/e13-doc-sync-check-report.json --quality-report docs/working/status/baselines/e11-quality-regression-report.json --perf-report docs/working/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/working/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/working/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/working/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/working/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/working/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-56 Additions

- Extended `scripts/release_switch.py` with release-gate malloc-arena-test-env gate: decision now rejects `MALLOC_ARENA_TEST=*` assignments in stage launchers and `--python` relay values before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_malloc_arena_test_env_assignment` to assert `MALLOC_ARENA_TEST` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_malloc_arena_test_env_gate` to assert `--skip-release-gate-malloc-arena-test-env-check` disables the gate for emergency recovery.
- Added `TP-E13-56` mapping in `scripts/tp_tests.py`.
- Linux decision-only with malloc-arena-test-env gate example: `python scripts/release_switch.py --decision-only --python "env MALLOC_ARENA_TEST=16 python3" --doc-sync-report docs/working/status/baselines/e13-doc-sync-check-report.json --quality-report docs/working/status/baselines/e11-quality-regression-report.json --perf-report docs/working/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/working/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/working/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/working/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/working/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/working/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-57 Additions

- Extended `scripts/release_switch.py` with release-gate malloc-per-thread-env gate: decision now rejects `MALLOC_PER_THREAD=*` assignments in stage launchers and `--python` relay values before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_malloc_per_thread_env_assignment` to assert `MALLOC_PER_THREAD` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_malloc_per_thread_env_gate` to assert `--skip-release-gate-malloc-per-thread-env-check` disables the gate for emergency recovery.
- Added `TP-E13-57` mapping in `scripts/tp_tests.py`.
- Linux decision-only with malloc-per-thread-env gate example: `python scripts/release_switch.py --decision-only --python "env MALLOC_PER_THREAD=1 python3" --doc-sync-report docs/working/status/baselines/e13-doc-sync-check-report.json --quality-report docs/working/status/baselines/e11-quality-regression-report.json --perf-report docs/working/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/working/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/working/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/working/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/working/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/working/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-58 Additions

- Extended `scripts/release_switch.py` with `bulk_strategy_view` projection in decision JSON to support large-scale analytics without depending on ever-growing flat `evidence_summary` keys.
- `bulk_strategy_view` now emits stable aggregation fields: `schema_version`, `decision`, `gate_count`, `pass_count`, `hold_count`, `gate_status_bitmap`, `gate_status_index`, `gate_rows`, `check_enablement`, `evidence_status_counts`, and `evidence_freshness_counts`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_view_for_go_decision` for GO-path schema + consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_view_for_hold_decision` for HOLD-path schema + gate-index consistency checks.
- Added `TP-E13-58` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; parse `bulk_strategy_view` from the same decision artifact: `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-59 Additions

- Upgraded `bulk_strategy_view` to `release_switch_bulk_strategy.v2` for high-volume analytics rollups.
- Added deterministic aggregation keys for strategy clustering: `decision_code`, `hold_signature`, `pass_gate_indices`, `hold_gate_indices`, `gate_domain_index`, and `domain_rollup`.
- `domain_rollup` now exports per-domain `gate_count/pass_count/hold_count/pass_ratio` for direct group-by aggregation without scanning raw gate text.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_domain_rollup_for_go_decision` to validate GO-path signature and domain rollup consistency.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_domain_rollup_for_hold_decision` to validate HOLD-path signature, index vectors, and domain hold counts.
- Added `TP-E13-59` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `bulk_strategy_view` v2 from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-60 Additions

- Extended `scripts/release_switch.py` with deterministic bulk signature digests: `hold_signature_sha256` and `strategy_signature_sha256`.
- `hold_signature_sha256` now pins `sha256(hold_signature)` for fixed-width signature indexing.
- `strategy_signature_sha256` now pins a canonical digest over `decision/gate_status_bitmap/pass_gate_indices/hold_gate_indices/check_enablement.enabled_keys/check_enablement.disabled_keys`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_signature_hash_for_go_decision` for GO-path signature-digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_signature_hash_for_hold_decision` for HOLD-path signature-digest consistency checks.
- Added `TP-E13-60` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume new hash fields from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-61 Additions

- Extended `scripts/release_switch.py` with deterministic domain-rollup digest: `domain_rollup_sha256`.
- `domain_rollup_sha256` now pins a canonical digest over `decision/domain_rollup/gate_domain_index`, enabling fixed-width indexing for domain-level aggregation profiles.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_domain_rollup_hash_for_go_decision` for GO-path domain-rollup digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_domain_rollup_hash_for_hold_decision` for HOLD-path domain-rollup digest consistency checks.
- Added `TP-E13-61` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `domain_rollup_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-62 Additions

- Extended `scripts/release_switch.py` with deterministic evidence-profile digest: `evidence_profile_sha256`.
- `evidence_profile_sha256` now pins a canonical digest over `decision/evidence_file_count/evidence_status_counts/evidence_freshness_counts`, enabling fixed-width indexing for evidence-state aggregation profiles.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_evidence_profile_hash_for_go_decision` for GO-path evidence-profile digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_evidence_profile_hash_for_hold_decision` for HOLD-path evidence-profile digest consistency checks.
- Added `TP-E13-62` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `evidence_profile_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-63 Additions

- Extended `scripts/release_switch.py` with deterministic gate-status-index digest: `gate_status_index_sha256`.
- `gate_status_index_sha256` now pins a canonical digest over `decision/gate_names/gate_status_bitmap/gate_status_index`, enabling fixed-width indexing for gate-matrix aggregation profiles.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_gate_status_index_hash_for_go_decision` for GO-path gate-status-index digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_gate_status_index_hash_for_hold_decision` for HOLD-path gate-status-index digest consistency checks.
- Added `TP-E13-63` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `gate_status_index_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-64 Additions

- Extended `scripts/release_switch.py` with deterministic composite-profile digest: `composite_profile_sha256`.
- `composite_profile_sha256` now pins a canonical digest over `decision/hold_signature_sha256/strategy_signature_sha256/domain_rollup_sha256/evidence_profile_sha256/gate_status_index_sha256`, enabling one-key indexing for cross-dimension strategy profiles.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_composite_profile_hash_for_go_decision` for GO-path composite-profile digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_composite_profile_hash_for_hold_decision` for HOLD-path composite-profile digest consistency checks.
- Added `TP-E13-64` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `composite_profile_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-65 Additions

- Extended `scripts/release_switch.py` with deterministic strategy-envelope digest: `strategy_envelope_sha256`.
- `strategy_envelope_sha256` now pins a canonical digest over `decision/decision_code/gate_count/pass_count/hold_count/evidence_file_count/hold_signature_sha256/strategy_signature_sha256/domain_rollup_sha256/evidence_profile_sha256/gate_status_index_sha256/composite_profile_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_envelope_hash_for_go_decision` for GO-path strategy-envelope digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_envelope_hash_for_hold_decision` for HOLD-path strategy-envelope digest consistency checks.
- Added `TP-E13-65` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `strategy_envelope_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-66 Additions

- Extended `scripts/release_switch.py` with deterministic contract-signature digest: `contract_signature_sha256`.
- `contract_signature_sha256` now pins a canonical digest over `schema_version/decision/decision_code/gate_names/gate_domain_index/check_enablement.enabled_keys/check_enablement.disabled_keys/strategy_envelope_sha256`, enabling one-key contract drift detection across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_contract_signature_hash_for_go_decision` for GO-path contract-signature digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_contract_signature_hash_for_hold_decision` for HOLD-path contract-signature digest consistency checks.
- Added `TP-E13-66` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `contract_signature_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-67 Additions

- Extended `scripts/release_switch.py` with deterministic contract-envelope digest: `contract_envelope_sha256`.
- `contract_envelope_sha256` now pins a canonical digest over `schema_version/decision/decision_code/gate_count/pass_count/hold_count/evidence_file_count/contract_signature_sha256/strategy_envelope_sha256/composite_profile_sha256`, enabling one-key contract+posture reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_contract_envelope_hash_for_go_decision` for GO-path contract-envelope digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_contract_envelope_hash_for_hold_decision` for HOLD-path contract-envelope digest consistency checks.
- Added `TP-E13-67` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `contract_envelope_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-68 Additions

- Extended `scripts/release_switch.py` with deterministic release-fingerprint digest: `release_fingerprint_sha256`.
- `release_fingerprint_sha256` now pins a canonical digest over `schema_version/decision/decision_code/gate_count/pass_count/hold_count/evidence_file_count/hold_signature_sha256/strategy_envelope_sha256/contract_signature_sha256/contract_envelope_sha256/composite_profile_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key release-level reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_fingerprint_hash_for_go_decision` for GO-path release-fingerprint digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_fingerprint_hash_for_hold_decision` for HOLD-path release-fingerprint digest consistency checks.
- Added `TP-E13-68` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_fingerprint_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-69 Additions

- Extended `scripts/release_switch.py` with deterministic release-manifest digest: `release_manifest_sha256`.
- `release_manifest_sha256` now pins a canonical digest over `schema_version/decision/decision_code/gate_names/gate_status_bitmap/gate_domain_index/domain_rollup_sha256/evidence_profile_sha256/release_fingerprint_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key release-manifest replay/reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_manifest_hash_for_go_decision` for GO-path release-manifest digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_manifest_hash_for_hold_decision` for HOLD-path release-manifest digest consistency checks.
- Added `TP-E13-69` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_manifest_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-70 Additions

- Extended `scripts/release_switch.py` with deterministic release-root digest: `release_root_sha256`.
- `release_root_sha256` now pins a canonical digest over `schema_version/decision/decision_code/gate_count/pass_count/hold_count/evidence_file_count/hold_signature_sha256/strategy_signature_sha256/domain_rollup_sha256/evidence_profile_sha256/gate_status_index_sha256/composite_profile_sha256/strategy_envelope_sha256/contract_signature_sha256/contract_envelope_sha256/release_fingerprint_sha256/release_manifest_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key release posture reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_root_hash_for_go_decision` for GO-path release-root digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_root_hash_for_hold_decision` for HOLD-path release-root digest consistency checks.
- Added `TP-E13-70` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_root_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-71 Additions

- Extended `scripts/release_switch.py` with deterministic release-attestation digest: `release_attestation_sha256`.
- `release_attestation_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/hold_signature_sha256/strategy_signature_sha256/gate_status_bitmap/gate_status_index_sha256/domain_rollup_sha256/evidence_profile_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key release attestation/reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_attestation_hash_for_go_decision` for GO-path release-attestation digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_attestation_hash_for_hold_decision` for HOLD-path release-attestation digest consistency checks.
- Added `TP-E13-71` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_attestation_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-72 Additions

- Extended `scripts/release_switch.py` with deterministic release-verdict digest: `release_verdict_sha256`.
- `release_verdict_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/strategy_envelope_sha256/contract_envelope_sha256/composite_profile_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key verdict/reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_verdict_hash_for_go_decision` for GO-path release-verdict digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_verdict_hash_for_hold_decision` for HOLD-path release-verdict digest consistency checks.
- Added `TP-E13-72` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_verdict_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-73 Additions

- Extended `scripts/release_switch.py` with deterministic release-lineage digest: `release_lineage_sha256`.
- `release_lineage_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/hold_signature_sha256/strategy_signature_sha256/domain_rollup_sha256/evidence_profile_sha256/gate_status_index_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key release lineage replay/reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_lineage_hash_for_go_decision` for GO-path release-lineage digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_lineage_hash_for_hold_decision` for HOLD-path release-lineage digest consistency checks.
- Added `TP-E13-73` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_lineage_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-74 Additions

- Extended `scripts/release_switch.py` with deterministic release-capsule digest: `release_capsule_sha256`.
- `release_capsule_sha256` now pins a canonical digest over `schema_version/decision/decision_code/gate_count/pass_count/hold_count/evidence_file_count/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key compact release reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_capsule_hash_for_go_decision` for GO-path release-capsule digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_capsule_hash_for_hold_decision` for HOLD-path release-capsule digest consistency checks.
- Added `TP-E13-74` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_capsule_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-75 Additions

- Extended `scripts/release_switch.py` with deterministic release-anchor digest: `release_anchor_sha256`.
- `release_anchor_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key anchored release reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_anchor_hash_for_go_decision` for GO-path release-anchor digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_anchor_hash_for_hold_decision` for HOLD-path release-anchor digest consistency checks.
- Added `TP-E13-75` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_anchor_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-76 Additions

- Extended `scripts/release_switch.py` with deterministic release-beacon digest: `release_beacon_sha256`.
- `release_beacon_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key beaconed release routing/reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_beacon_hash_for_go_decision` for GO-path release-beacon digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_beacon_hash_for_hold_decision` for HOLD-path release-beacon digest consistency checks.
- Added `TP-E13-76` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_beacon_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-77 Additions

- Extended `scripts/release_switch.py` with deterministic release-constellation digest: `release_constellation_sha256`.
- `release_constellation_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key constellation routing/reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_constellation_hash_for_go_decision` for GO-path release-constellation digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_constellation_hash_for_hold_decision` for HOLD-path release-constellation digest consistency checks.
- Added `TP-E13-77` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_constellation_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-78 Additions

- Extended `scripts/release_switch.py` with deterministic release-galaxy digest: `release_galaxy_sha256`.
- `release_galaxy_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key galaxy routing/reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_galaxy_hash_for_go_decision` for GO-path release-galaxy digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_galaxy_hash_for_hold_decision` for HOLD-path release-galaxy digest consistency checks.
- Added `TP-E13-78` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_galaxy_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-79 Additions

- Extended `scripts/release_switch.py` with deterministic release-universe digest: `release_universe_sha256`.
- `release_universe_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key universe routing/reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_universe_hash_for_go_decision` for GO-path release-universe digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_universe_hash_for_hold_decision` for HOLD-path release-universe digest consistency checks.
- Added `TP-E13-79` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_universe_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-80 Additions

- Extended `scripts/release_switch.py` with deterministic release-multiverse digest: `release_multiverse_sha256`.
- `release_multiverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key multiverse routing/reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_multiverse_hash_for_go_decision` for GO-path release-multiverse digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_multiverse_hash_for_hold_decision` for HOLD-path release-multiverse digest consistency checks.
- Added `TP-E13-80` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_multiverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-81 Additions

- Extended `scripts/release_switch.py` with deterministic release-omniverse digest: `release_omniverse_sha256`.
- `release_omniverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key omniverse routing/reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_omniverse_hash_for_go_decision` for GO-path release-omniverse digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_omniverse_hash_for_hold_decision` for HOLD-path release-omniverse digest consistency checks.
- Added `TP-E13-81` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_omniverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-82 Additions

- Extended `scripts/release_switch.py` with deterministic release-hyperverse digest: `release_hyperverse_sha256`.
- `release_hyperverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key hyperverse routing/reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_hyperverse_hash_for_go_decision` for GO-path release-hyperverse digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_hyperverse_hash_for_hold_decision` for HOLD-path release-hyperverse digest consistency checks.
- Added `TP-E13-82` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_hyperverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-83 Additions

- Extended `scripts/release_switch.py` with deterministic release-megaverse digest: `release_megaverse_sha256`.
- `release_megaverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key megaverse routing/reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_megaverse_hash_for_go_decision` for GO-path release-megaverse digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_megaverse_hash_for_hold_decision` for HOLD-path release-megaverse digest consistency checks.
- Added `TP-E13-83` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_megaverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-84 Additions

- Extended `scripts/release_switch.py` with deterministic release-gigaverse digest: `release_gigaverse_sha256`.
- `release_gigaverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key gigaverse routing/reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_gigaverse_hash_for_go_decision` for GO-path release-gigaverse digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_gigaverse_hash_for_hold_decision` for HOLD-path release-gigaverse digest consistency checks.
- Added `TP-E13-84` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_gigaverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-85 Additions

- Extended `scripts/release_switch.py` with deterministic release-teraverse digest: `release_teraverse_sha256`.
- `release_teraverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key teraverse routing/reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_teraverse_hash_for_go_decision` for GO-path release-teraverse digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_teraverse_hash_for_hold_decision` for HOLD-path release-teraverse digest consistency checks.
- Added `TP-E13-85` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_teraverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-86 Additions

- Extended `scripts/release_switch.py` with deterministic release-petaverse digest: `release_petaverse_sha256`.
- `release_petaverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key petaverse routing/reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_petaverse_hash_for_go_decision` for GO-path release-petaverse digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_petaverse_hash_for_hold_decision` for HOLD-path release-petaverse digest consistency checks.
- Added `TP-E13-86` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_petaverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-87 Additions

- Extended `scripts/release_switch.py` with deterministic release-exaverse digest: `release_exaverse_sha256`.
- `release_exaverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key exaverse routing/reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_exaverse_hash_for_go_decision` for GO-path release-exaverse digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_exaverse_hash_for_hold_decision` for HOLD-path release-exaverse digest consistency checks.
- Added `TP-E13-87` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_exaverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-88 Additions

- Extended `scripts/release_switch.py` with deterministic release-zettaverse digest: `release_zettaverse_sha256`.
- `release_zettaverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key zettaverse routing/reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_zettaverse_hash_for_go_decision` for GO-path release-zettaverse digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_zettaverse_hash_for_hold_decision` for HOLD-path release-zettaverse digest consistency checks.
- Added `TP-E13-88` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_zettaverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-89 Additions

- Extended `scripts/release_switch.py` with deterministic release-yottaverse digest: `release_yottaverse_sha256`.
- `release_yottaverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key yottaverse routing/reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_yottaverse_hash_for_go_decision` for GO-path release-yottaverse digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_yottaverse_hash_for_hold_decision` for HOLD-path release-yottaverse digest consistency checks.
- Added `TP-E13-89` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_yottaverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-90 Additions

- Extended `scripts/release_switch.py` with deterministic release-ronnaverse digest: `release_ronnaverse_sha256`.
- `release_ronnaverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key ronnaverse routing/reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_ronnaverse_hash_for_go_decision` for GO-path release-ronnaverse digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_ronnaverse_hash_for_hold_decision` for HOLD-path release-ronnaverse digest consistency checks.
- Added `TP-E13-90` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_ronnaverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-91 Additions

- Extended `scripts/release_switch.py` with deterministic release-quettaverse digest: `release_quettaverse_sha256`.
- `release_quettaverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key quettaverse routing/reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_quettaverse_hash_for_go_decision` for GO-path release-quettaverse digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_quettaverse_hash_for_hold_decision` for HOLD-path release-quettaverse digest consistency checks.
- Added `TP-E13-91` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_quettaverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-92 Additions

- Extended `scripts/release_switch.py` with deterministic release-apexverse digest: `release_apexverse_sha256`.
- `release_apexverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key apexverse routing/reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_apexverse_hash_for_go_decision` for GO-path release-apexverse digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_apexverse_hash_for_hold_decision` for HOLD-path release-apexverse digest consistency checks.
- Added `TP-E13-92` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_apexverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-93 Additions

- Extended `scripts/release_switch.py` with deterministic release-ultimaverse digest: `release_ultimaverse_sha256`.
- `release_ultimaverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key ultimaverse routing/reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_ultimaverse_hash_for_go_decision` for GO-path release-ultimaverse digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_ultimaverse_hash_for_hold_decision` for HOLD-path release-ultimaverse digest consistency checks.
- Added `TP-E13-93` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_ultimaverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-94 Additions

- Extended `scripts/release_switch.py` with deterministic release-transcendaverse digest: `release_transcendaverse_sha256`.
- `release_transcendaverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key transcendaverse routing/reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_transcendaverse_hash_for_go_decision` for GO-path release-transcendaverse digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_transcendaverse_hash_for_hold_decision` for HOLD-path release-transcendaverse digest consistency checks.
- Added `TP-E13-94` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_transcendaverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-95 Additions

- Extended `scripts/release_switch.py` with deterministic release-infinitaverse digest: `release_infinitaverse_sha256`.
- `release_infinitaverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key infinitaverse routing/reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_infinitaverse_hash_for_go_decision` for GO-path release-infinitaverse digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_infinitaverse_hash_for_hold_decision` for HOLD-path release-infinitaverse digest consistency checks.
- Added `TP-E13-95` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_infinitaverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-96 Additions

- Extended `scripts/release_switch.py` with deterministic release-eternaverse digest: `release_eternaverse_sha256`.
- `release_eternaverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key eternaverse routing/reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_eternaverse_hash_for_go_decision` for GO-path release-eternaverse digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_eternaverse_hash_for_hold_decision` for HOLD-path release-eternaverse digest consistency checks.
- Added `TP-E13-96` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_eternaverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-97 Additions

- Extended `scripts/release_switch.py` with deterministic release-timelessverse digest: `release_timelessverse_sha256`.
- `release_timelessverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key timelessverse routing/reconciliation across decision batches.
- Added testcase:
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_timelessverse_hash_for_go_decision`
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_timelessverse_hash_for_hold_decision`
- Added `TP-E13-97` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_timelessverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-98 Additions

- Extended `scripts/release_switch.py` with deterministic release-aeonverse digest: `release_aeonverse_sha256`.
- `release_aeonverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key aeonverse routing/reconciliation across decision batches.
- Added testcase:
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_aeonverse_hash_for_go_decision`
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_aeonverse_hash_for_hold_decision`
- Added `TP-E13-98` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_aeonverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-99 Additions

- Extended `scripts/release_switch.py` with deterministic release-epochverse digest: `release_epochverse_sha256`.
- `release_epochverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key epochverse routing/reconciliation across decision batches.
- Added testcase:
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_epochverse_hash_for_go_decision`
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_epochverse_hash_for_hold_decision`
- Added `TP-E13-99` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_epochverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-100 Additions

- Extended `scripts/release_switch.py` with deterministic release-eraverse digest: `release_eraverse_sha256`.
- `release_eraverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key eraverse routing/reconciliation across decision batches.
- Added testcase:
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_eraverse_hash_for_go_decision`
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_eraverse_hash_for_hold_decision`
- Added `TP-E13-100` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_eraverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-101 Additions

- Extended `scripts/release_switch.py` with deterministic release-metaverse digest: `release_metaverse_sha256`.
- `release_metaverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key metaverse routing/reconciliation across decision batches.
- Added testcase:
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_metaverse_hash_for_go_decision`
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_metaverse_hash_for_hold_decision`
- Added `TP-E13-101` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_metaverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-102 Additions

- Extended `scripts/release_switch.py` with deterministic release-paraverse digest: `release_paraverse_sha256`.
- `release_paraverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key paraverse routing/reconciliation across decision batches.
- Added testcase:
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_paraverse_hash_for_go_decision`
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_paraverse_hash_for_hold_decision`
- Added `TP-E13-102` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_paraverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-103 Additions

- Extended `scripts/release_switch.py` with deterministic release-polyverse digest: `release_polyverse_sha256`.
- `release_polyverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key polyverse routing/reconciliation across decision batches.
- Added testcase:
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_polyverse_hash_for_go_decision`
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_polyverse_hash_for_hold_decision`
- Added `TP-E13-103` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_polyverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-104 Additions

- Extended `scripts/release_switch.py` with deterministic release-panverse digest: `release_panverse_sha256`.
- `release_panverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key panverse routing/reconciliation across decision batches.
- Added testcase:
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_panverse_hash_for_go_decision`
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_panverse_hash_for_hold_decision`
- Added `TP-E13-104` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_panverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-105 Additions

- Extended `scripts/release_switch.py` with deterministic release-holoverse digest: `release_holoverse_sha256`.
- `release_holoverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key holoverse routing/reconciliation across decision batches.
- Added testcase:
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_holoverse_hash_for_go_decision`
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_holoverse_hash_for_hold_decision`
- Added `TP-E13-105` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_holoverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-106 Additions

- Extended `scripts/release_switch.py` with deterministic release-neoverse digest: `release_neoverse_sha256`.
- `release_neoverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key neoverse routing/reconciliation across decision batches.
- Added testcase:
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_neoverse_hash_for_go_decision`
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_neoverse_hash_for_hold_decision`
- Added `TP-E13-106` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_neoverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-107 Additions

- Extended `scripts/release_switch.py` with deterministic release-novaverse digest: `release_novaverse_sha256`.
- `release_novaverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key novaverse routing/reconciliation across decision batches.
- Added testcase:
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_novaverse_hash_for_go_decision`
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_novaverse_hash_for_hold_decision`
- Added `TP-E13-107` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_novaverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-108 Additions

- Extended `scripts/release_switch.py` with deterministic release-supernovaverse digest: `release_supernovaverse_sha256`.
- `release_supernovaverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key supernovaverse routing/reconciliation across decision batches.
- Added testcase:
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_supernovaverse_hash_for_go_decision`
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_supernovaverse_hash_for_hold_decision`
- Added `TP-E13-108` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_supernovaverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-109 Additions

- Extended `scripts/release_switch.py` with deterministic release-hypernovaverse digest: `release_hypernovaverse_sha256`.
- `release_hypernovaverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key hypernovaverse routing/reconciliation across decision batches.
- Added testcase:
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_hypernovaverse_hash_for_go_decision`
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_hypernovaverse_hash_for_hold_decision`
- Added `TP-E13-109` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_hypernovaverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-110 Additions

- Extended `scripts/release_switch.py` with deterministic release-ultranovaverse digest: `release_ultranovaverse_sha256`.
- `release_ultranovaverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key ultranovaverse routing/reconciliation across decision batches.
- Added testcase:
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_ultranovaverse_hash_for_go_decision`
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_ultranovaverse_hash_for_hold_decision`
- Added `TP-E13-110` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_ultranovaverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-111 Additions

- Extended `scripts/release_switch.py` with deterministic release-omeganovaverse digest: `release_omeganovaverse_sha256`.
- `release_omeganovaverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key omeganovaverse routing/reconciliation across decision batches.
- Added testcase:
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_omeganovaverse_hash_for_go_decision`
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_omeganovaverse_hash_for_hold_decision`
- Added `TP-E13-111` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_omeganovaverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-112 Additions

- Extended `scripts/release_switch.py` with deterministic release-alphanovaverse digest: `release_alphanovaverse_sha256`.
- `release_alphanovaverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key alphanovaverse routing/reconciliation across decision batches.
- Added testcase:
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_alphanovaverse_hash_for_go_decision`
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_alphanovaverse_hash_for_hold_decision`
- Added `TP-E13-112` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_alphanovaverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-113 Additions

- Extended `scripts/release_switch.py` with deterministic release-betanovaverse digest: `release_betanovaverse_sha256`.
- `release_betanovaverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key betanovaverse routing/reconciliation across decision batches.
- Added testcase:
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_betanovaverse_hash_for_go_decision`
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_betanovaverse_hash_for_hold_decision`
- Added `TP-E13-113` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_betanovaverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-114 Additions

- Extended `scripts/release_switch.py` with deterministic release-gammanovaverse digest: `release_gammanovaverse_sha256`.
- `release_gammanovaverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key gammanovaverse routing/reconciliation across decision batches.
- Added testcase:
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_gammanovaverse_hash_for_go_decision`
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_gammanovaverse_hash_for_hold_decision`
- Added `TP-E13-114` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_gammanovaverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-115 Additions

- Extended `scripts/release_switch.py` with deterministic release-deltanovaverse digest: `release_deltanovaverse_sha256`.
- `release_deltanovaverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_gammanovaverse_sha256/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key deltanovaverse routing/reconciliation across decision batches.
- Added testcase:
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_deltanovaverse_hash_for_go_decision`
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_deltanovaverse_hash_for_hold_decision`
- Added `TP-E13-115` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_deltanovaverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-116 Additions

- Extended `scripts/release_switch.py` with deterministic release-epsilonnovaverse digest: `release_epsilonnovaverse_sha256`.
- `release_epsilonnovaverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_deltanovaverse_sha256/release_gammanovaverse_sha256/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key epsilonnovaverse routing/reconciliation across decision batches.
- Added testcase:
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_epsilonnovaverse_hash_for_go_decision`
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_epsilonnovaverse_hash_for_hold_decision`
- Added `TP-E13-116` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_epsilonnovaverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-117 Additions

- Extended `scripts/release_switch.py` with deterministic release-zetanovaverse digest: `release_zetanovaverse_sha256`.
- `release_zetanovaverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_epsilonnovaverse_sha256/release_deltanovaverse_sha256/release_gammanovaverse_sha256/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key zetanovaverse routing/reconciliation across decision batches.
- Added testcase:
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_zetanovaverse_hash_for_go_decision`
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_zetanovaverse_hash_for_hold_decision`
- Added `TP-E13-117` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_zetanovaverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-118 Additions

- Extended `scripts/release_switch.py` with deterministic release-etanovaverse digest: `release_etanovaverse_sha256`.
- `release_etanovaverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_zetanovaverse_sha256/release_epsilonnovaverse_sha256/release_deltanovaverse_sha256/release_gammanovaverse_sha256/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key etanovaverse routing/reconciliation across decision batches.
- Added testcase:
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_etanovaverse_hash_for_go_decision`
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_etanovaverse_hash_for_hold_decision`
- Added `TP-E13-118` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_etanovaverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-119 Additions

- Extended `scripts/release_switch.py` with deterministic release-thetanovaverse digest: `release_thetanovaverse_sha256`.
- `release_thetanovaverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_etanovaverse_sha256/release_zetanovaverse_sha256/release_epsilonnovaverse_sha256/release_deltanovaverse_sha256/release_gammanovaverse_sha256/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key thetanovaverse routing/reconciliation across decision batches.
- Added testcase:
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_thetanovaverse_hash_for_go_decision`
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_thetanovaverse_hash_for_hold_decision`
- Added `TP-E13-119` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_thetanovaverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-120 Additions

- Extended `scripts/release_switch.py` with deterministic release-iotanovaverse digest: `release_iotanovaverse_sha256`.
- `release_iotanovaverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_thetanovaverse_sha256/release_etanovaverse_sha256/release_zetanovaverse_sha256/release_epsilonnovaverse_sha256/release_deltanovaverse_sha256/release_gammanovaverse_sha256/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key iotanovaverse routing/reconciliation across decision batches.
- Added testcase:
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_iotanovaverse_hash_for_go_decision`
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_iotanovaverse_hash_for_hold_decision`
- Added `TP-E13-120` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_iotanovaverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-121 Additions

- Extended `scripts/release_switch.py` with deterministic release-kappanovaverse digest: `release_kappanovaverse_sha256`.
- `release_kappanovaverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_iotanovaverse_sha256/release_thetanovaverse_sha256/release_etanovaverse_sha256/release_zetanovaverse_sha256/release_epsilonnovaverse_sha256/release_deltanovaverse_sha256/release_gammanovaverse_sha256/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key kappanovaverse routing/reconciliation across decision batches.
- Added testcase:
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_kappanovaverse_hash_for_go_decision`
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_kappanovaverse_hash_for_hold_decision`
- Added `TP-E13-121` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_kappanovaverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-122 Additions

- Extended `scripts/release_switch.py` with deterministic release-lambdanovaverse digest: `release_lambdanovaverse_sha256`.
- `release_lambdanovaverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_kappanovaverse_sha256/release_iotanovaverse_sha256/release_thetanovaverse_sha256/release_etanovaverse_sha256/release_zetanovaverse_sha256/release_epsilonnovaverse_sha256/release_deltanovaverse_sha256/release_gammanovaverse_sha256/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key lambdanovaverse routing/reconciliation across decision batches.
- Added testcase:
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_lambdanovaverse_hash_for_go_decision`
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_lambdanovaverse_hash_for_hold_decision`
- Added `TP-E13-122` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_lambdanovaverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-123 Additions

- Extended `scripts/release_switch.py` with deterministic release-munovaverse digest: `release_munovaverse_sha256`.
- `release_munovaverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_lambdanovaverse_sha256/release_kappanovaverse_sha256/release_iotanovaverse_sha256/release_thetanovaverse_sha256/release_etanovaverse_sha256/release_zetanovaverse_sha256/release_epsilonnovaverse_sha256/release_deltanovaverse_sha256/release_gammanovaverse_sha256/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key munovaverse routing/reconciliation across decision batches.
- Added testcase:
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_munovaverse_hash_for_go_decision`
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_munovaverse_hash_for_hold_decision`
- Added `TP-E13-123` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_munovaverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-124 Additions

- Extended `scripts/release_switch.py` with deterministic release-nunovaverse digest: `release_nunovaverse_sha256`.
- `release_nunovaverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_munovaverse_sha256/release_lambdanovaverse_sha256/release_kappanovaverse_sha256/release_iotanovaverse_sha256/release_thetanovaverse_sha256/release_etanovaverse_sha256/release_zetanovaverse_sha256/release_epsilonnovaverse_sha256/release_deltanovaverse_sha256/release_gammanovaverse_sha256/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key nunovaverse routing/reconciliation across decision batches.
- Added testcase:
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_nunovaverse_hash_for_go_decision`
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_nunovaverse_hash_for_hold_decision`
- Added `TP-E13-124` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_nunovaverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-125 Additions

- Extended `scripts/release_switch.py` with deterministic release-xinovaverse digest: `release_xinovaverse_sha256`.
- `release_xinovaverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_nunovaverse_sha256/release_munovaverse_sha256/release_lambdanovaverse_sha256/release_kappanovaverse_sha256/release_iotanovaverse_sha256/release_thetanovaverse_sha256/release_etanovaverse_sha256/release_zetanovaverse_sha256/release_epsilonnovaverse_sha256/release_deltanovaverse_sha256/release_gammanovaverse_sha256/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key xinovaverse routing/reconciliation across decision batches.
- Added testcase:
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_xinovaverse_hash_for_go_decision`
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_xinovaverse_hash_for_hold_decision`
- Added `TP-E13-125` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_xinovaverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-126 Additions

- Extended `scripts/release_switch.py` with deterministic release-omicronovaverse digest: `release_omicronovaverse_sha256`.
- `release_omicronovaverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_xinovaverse_sha256/release_nunovaverse_sha256/release_munovaverse_sha256/release_lambdanovaverse_sha256/release_kappanovaverse_sha256/release_iotanovaverse_sha256/release_thetanovaverse_sha256/release_etanovaverse_sha256/release_zetanovaverse_sha256/release_epsilonnovaverse_sha256/release_deltanovaverse_sha256/release_gammanovaverse_sha256/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key omicronovaverse routing/reconciliation across decision batches.
- Added testcase:
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_omicronovaverse_hash_for_go_decision`
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_omicronovaverse_hash_for_hold_decision`
- Added `TP-E13-126` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_omicronovaverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-127 Additions

- Extended `scripts/release_switch.py` with deterministic release-pinovaverse digest: `release_pinovaverse_sha256`.
- `release_pinovaverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_omicronovaverse_sha256/release_xinovaverse_sha256/release_nunovaverse_sha256/release_munovaverse_sha256/release_lambdanovaverse_sha256/release_kappanovaverse_sha256/release_iotanovaverse_sha256/release_thetanovaverse_sha256/release_etanovaverse_sha256/release_zetanovaverse_sha256/release_epsilonnovaverse_sha256/release_deltanovaverse_sha256/release_gammanovaverse_sha256/release_betanovaverse_sha256/release_alphanovaverse_sha256/release_omeganovaverse_sha256/release_ultranovaverse_sha256/release_hypernovaverse_sha256/release_supernovaverse_sha256/release_novaverse_sha256/release_neoverse_sha256/release_holoverse_sha256/release_panverse_sha256/release_polyverse_sha256/release_paraverse_sha256/release_metaverse_sha256/release_eraverse_sha256/release_epochverse_sha256/release_aeonverse_sha256/release_timelessverse_sha256/release_eternaverse_sha256/release_infinitaverse_sha256/release_transcendaverse_sha256/release_ultimaverse_sha256/release_apexverse_sha256/release_quettaverse_sha256/release_ronnaverse_sha256/release_yottaverse_sha256/release_zettaverse_sha256/release_exaverse_sha256/release_petaverse_sha256/release_teraverse_sha256/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key pinovaverse routing/reconciliation across decision batches.
- Added testcase:
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_pinovaverse_hash_for_go_decision`
  - `tests/test_release_switch_validation_script.py::ReleaseSwitchValidationScriptTests.test_script_decision_only_emits_bulk_strategy_release_pinovaverse_hash_for_hold_decision`
- Added `TP-E13-127` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_pinovaverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## Linux Release Script Entry Clarification

- Run `bash scripts/linux_release.sh` on the bare Linux host after cloning the repository.
- Do not enter a Docker container manually before running the script; it builds Docker images on the host and executes CI, Linux validation suite, API acceptance, and release-switch validation inside Docker.
- Upload `release-artifacts-<RELEASE_ID>.tar.gz` for review. The reviewer can use `summary.json`, `summary.tsv`, `logs/*.log`, `logs/*.exit`, and `baselines/*` to reconstruct every stage result.

## TP-E13-128 Additions

- Extended `scripts/release_switch.py` with deterministic release-rhonovaverse digest: `release_rhonovaverse_sha256`.
- Added testcase coverage for GO and HOLD release-rhonovaverse digest emission in `tests/test_release_switch_validation_script.py`.
- Added `TP-E13-128` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_rhonovaverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-129 Additions

- Extended `scripts/release_switch.py` with deterministic release-sigmanovaverse digest: `release_sigmanovaverse_sha256`.
- Added testcase coverage for GO and HOLD release-sigmanovaverse digest emission in `tests/test_release_switch_validation_script.py`.
- Added `TP-E13-129` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_sigmanovaverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-130 Additions

- Extended `scripts/release_switch.py` with deterministic release-taunovaverse digest: `release_taunovaverse_sha256`.
- Added testcase coverage for GO and HOLD release-taunovaverse digest emission in `tests/test_release_switch_validation_script.py`.
- Added `TP-E13-130` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_taunovaverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-131 Additions

- Extended `scripts/release_switch.py` with deterministic release-upsilonnovaverse digest: `release_upsilonnovaverse_sha256`.
- Added testcase coverage for GO and HOLD release-upsilonnovaverse digest emission in `tests/test_release_switch_validation_script.py`.
- Added `TP-E13-131` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_upsilonnovaverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-132 Additions

- Extended `scripts/release_switch.py` with deterministic release-phinovaverse digest: `release_phinovaverse_sha256`.
- Added testcase coverage for GO and HOLD release-phinovaverse digest emission in `tests/test_release_switch_validation_script.py`.
- Added `TP-E13-132` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_phinovaverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-133 Additions

- Extended `scripts/release_switch.py` with deterministic release-chinovaverse digest: `release_chinovaverse_sha256`.
- Added testcase coverage for GO and HOLD release-chinovaverse digest emission in `tests/test_release_switch_validation_script.py`.
- Added `TP-E13-133` mapping in `scripts/tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_chinovaverse_sha256` from `docs/working/status/baselines/e13-release-switch-decision-report.json`.
