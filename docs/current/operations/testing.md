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
python scripts/run_tp_tests.py TP-E4-01 TP-E4-02 TP-E4-03 TP-E4-04 TP-E4-05 TP-E5-02 TP-E5-03 TP-E5-04 TP-E6-01 TP-E6-02 TP-E6-03 TP-E6-04 TP-E7-01 TP-E7-02 TP-E7-03 TP-E7-04 --python python
```

## 当前覆盖重点

- `tests/test_mvp.py`: 覆盖 text / audio / image / video / tabular 主路径
- `tests/test_v2_schema_and_corpus.py`: 覆盖 corpus 组装、publication、quality、review artifacts
- `tests/test_quality_scoring.py`: 覆盖质量评分
- `tests/test_review_policy.py`: 覆盖 review threshold 与 reason codes

## 当前缺口

- 尚无 FastAPI/ASGI API 层自动化测试
- coverage fail-under 仍是保守阈值（`50`），后续应随质量基线提升
- 尚无 performance benchmark
- 真实 provider failure-mode 覆盖仍偏薄

## 维护规则

每次新增 `TP-*` 工单时，至少同步完成三件事：

1. 在 `tests/` 落测试 case
2. 在 `scripts/run_tp_tests.py` 的 `TP_TEST_CASES` 中登记映射
3. 在本文件更新覆盖范围与新增工单说明
