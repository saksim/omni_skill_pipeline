# Testing

## 判词

所有 `TP-*` 功能斩杀后，测试必须绑定到可直接调用的具体 `unittest case id`，并可在 Linux 一次性执行。

## 本地环境对齐

建议始终在隔离虚拟环境内执行测试，避免宿主机的旧版 `pyarrow/numexpr/bottleneck` 污染 `pandas` 导入链。

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

## 全量回归

仓库已经提供统一 CI 入口，先跑全量回归，再按 `TP-*` 定位局部工单：

```bash
python3 scripts/run_ci.py
```

## 一键调用（Linux）

先查看当前已映射工单与案例：

```bash
python3 scripts/run_tp_tests.py --list
```

执行单个工单（示例：`TP-E6-02`）：

```bash
python3 scripts/run_tp_tests.py TP-E6-02 --python python3
```

一次执行多个工单：

```bash
python3 scripts/run_tp_tests.py TP-E4-01 TP-E4-02 TP-E4-03 TP-E4-04 TP-E4-05 TP-E5-02 TP-E5-03 TP-E5-04 TP-E6-01 TP-E6-02 TP-E6-03 TP-E6-04 TP-E7-01 TP-E7-02 TP-E7-03 TP-E7-04 --python python3
```

执行所有已登记工单：

```bash
python3 scripts/run_tp_tests.py --all --python python3
```

## CI

- GitHub Actions 工作流位于 `.github/workflows/ci.yml`
- CI 与本地统一复用 `scripts/run_ci.py`
- CI 安装入口位于 `requirements-dev.txt`

## 当前已登记工单

- `TP-E4-01`：文档结构解析增强
- `TP-E4-02`：音频语义增强
- `TP-E4-03`：图片布局增强
- `TP-E4-04`：视频时间语义增强
- `TP-E4-05`：时序 baseline/change point/drift 增强
- `TP-E5-02`：Heuristic Atom 抽取增强
- `TP-E5-03`：模态专用 Atom 策略增强
- `TP-E5-04`：LLM Atom 增强与 fallback 保障
- `TP-E6-01`：SkillGraph node/edge 模型增强
- `TP-E6-02`：SkillGraphBuilder 构图与追溯增强
- `TP-E6-03`：PublicationBuilder 输出与落盘增强
- `TP-E6-04`：V1 renderer 兼容与 skill_markdown 回归保障
- `TP-E7-01`：质量评分器与六分项落盘增强
- `TP-E7-02`：ReviewPolicy 阈值决策与理由码输出
- `TP-E7-03`：ReviewTask 结构化落地与修正建议持久化
- `TP-E7-04`：ReviewFeedback 回流到 atom/graph/policy 的修订信号

## 维护规则

每次新增功能工单时，必须同步做三件事：

1. 在 `tests/` 中落地具体测试函数（case id 可直接执行）。
2. 在 `scripts/run_tp_tests.py` 的 `TP_TEST_CASES` 里登记该工单与 case id。
3. 在本文件更新“当前已登记工单”。
