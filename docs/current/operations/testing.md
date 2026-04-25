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
python scripts/run_tp_tests.py TP-E4-01 TP-E4-02 TP-E4-03 TP-E4-04 TP-E4-05 TP-E5-02 TP-E5-03 TP-E5-04 TP-E6-01 TP-E6-02 TP-E6-03 TP-E6-04 TP-E7-01 TP-E7-02 TP-E7-03 TP-E7-04 TP-E8-02 TP-E8-03 TP-E9-01 TP-E9-02 TP-E9-03 TP-E10-01 TP-E10-02 TP-E10-03 TP-E11-01 TP-E11-04 --python python
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

## 当前缺口

- FastAPI/ASGI API 自动化测试已覆盖核心契约；仍缺真实 provider 故障注入与负载场景
- coverage fail-under 仍是保守阈值（`50`），后续应随质量基线提升
- 尚无生产级负载压测（当前仅有 dual-write benchmark smoke harness）
- 真实 provider failure-mode 覆盖仍偏薄

## 维护规则

每次新增 `TP-*` 工单时，至少同步完成三件事：

1. 在 `tests/` 落测试 case
2. 在 `scripts/run_tp_tests.py` 的 `TP_TEST_CASES` 中登记映射
3. 在本文件更新覆盖范围与新增工单说明

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
