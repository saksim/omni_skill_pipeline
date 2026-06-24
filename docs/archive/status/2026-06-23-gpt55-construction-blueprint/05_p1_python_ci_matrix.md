# P1：Python 支持矩阵与 CI 稳定性说明

## 1. 背景

当前 `pyproject.toml` 中存在：

```toml
requires-python = ">=3.11"
```

同时依赖包含：

```toml
numpy>=1.26,<2.0
```

评估环境为 Python 3.13.5，正常依赖安装路径出现不一致。这意味着 `>=3.11` 的声明过宽，会误导使用者认为 Python 3.13 也被支持。

## 2. 风险

1. 用户用 Python 3.13 安装失败。
2. 外部 Beta 环境不可控，安装问题会被误认为产品不可用。
3. CI 只测 Python 3.11，但包声明支持所有更高版本，会造成信任缺口。
4. 后续依赖升级时可能引入隐性破坏。

## 3. 推荐策略

### 策略 A：收紧支持矩阵，推荐当前采用

将 `pyproject.toml` 改为：

```toml
requires-python = ">=3.11,<3.13"
```

文档中明确：

```text
Supported Python: 3.11, 3.12
Not yet supported: 3.13
```

### 策略 B：真正支持 Python 3.13

如果要支持 3.13，则必须：

- 升级 `numpy` 约束；
- 检查 `pandas/scipy/sklearn/opencv/tesseract` 等依赖；
- 在 CI 矩阵加入 Python 3.13；
- 全量测试通过；
- release wheel 在 3.13 可安装。

当前建议先采用策略 A，避免扩大施工范围。

## 4. CI 矩阵建议

最小矩阵：

```yaml
python-version: ["3.11", "3.12"]
```

可选扩展：

```yaml
python-version: ["3.11", "3.12", "3.13"]
allow-failure: ["3.13"]
```

但如果 pyproject 不声明 3.13 支持，不应把 3.13 的失败作为阻塞。

## 5. 测试分层

建议把测试分成：

| 层级 | 命令 | 目标 |
|---|---|---|
| unit | `pytest tests/test_*.py` | 纯 Python 快速测试 |
| cli smoke | `omni-skill ...` | CLI 代表性路径 |
| integration | `pytest -m integration` | 依赖文件/外部工具的集成测试 |
| release | `scripts/release_artifacts.py` | 发布产物 |
| consumer | `scripts/release_consumer_smoke.py` | 消费者可用性 |
| real-loop | `gl64 + trial_metrics + launch_gate` | 真实证据门禁 |
| docker | `container_smoke.py` | 容器真实运行 |

## 6. 当前需要补强的 CI 证据

下一版必须生成并归档：

```text
ci_summary_python_3_11.json
ci_summary_python_3_12.json
coverage.xml
doc_sync.json
release_artifacts.json
release_consumer_smoke.json
launch_gate.json
```

如果 full test 在某个环境超时，必须记录：

- 哪个测试超时；
- 是否环境相关；
- 是否被标记为 slow/integration；
- 是否应该调整 timeout；
- 是否存在死循环/子进程不退出。

## 7. 建议施工任务

### T1：修改 pyproject 版本范围

```toml
requires-python = ">=3.11,<3.13"
```

除非同步支持 3.13。

### T2：补文档

在 README / operations/testing 中增加：

```text
Supported runtime: Python 3.11 and 3.12.
Python 3.13 is not part of the supported matrix for v0.2.x.
```

### T3：CI 增加矩阵

在 GitHub Actions 中加入 3.11/3.12。

### T4：隔离 slow/integration 测试

如果存在会跑完整 CI 脚本的测试，必须：

- 设置合理 timeout；
- 标记 `@pytest.mark.slow`；
- 避免子进程递归调用 full suite；
- 在 PR CI 中只跑 smoke，在 nightly 跑 full。

### T5：补 install smoke

每个 Python 版本均执行：

```bash
python -m pip install -e '.[dev]'
omni-skill --help
python -m pip wheel . --no-deps --wheel-dir dist
```

## 8. 验收命令

```bash
python -m pip install -e '.[dev]'
pytest
python scripts/doc_sync.py --output -
python -m pip wheel . --no-deps --wheel-dir dist
```

CI 中 Python 3.11 与 3.12 均必须通过。

## 9. 完成定义

1. pyproject 与 README 支持矩阵一致。
2. CI 实际测试版本与声明一致。
3. Python 3.13 若不支持，安装失败不算产品 bug，但文档必须提前说明。
4. full test 至少在 3.11 通过。
5. 3.12 至少通过 unit + cli + release smoke。
6. CI artifact 中保留测试摘要。

## 10. 禁止的伪修复

不允许：

- 仍写 `>=3.11` 但只测 3.11；
- 删除难跑测试来制造通过；
- 把超时测试简单 skip 且无 issue/说明；
- 不改文档只改 CI；
- 不改 CI 只改文档。
