# P0 Workflow Fail Remediation

## 目标

修掉当前 GitHub Actions 中确定存在的 workflow 硬失败，使 CI 至少能调用仓库内真实存在的测试脚本。

## 已确认问题

`.github/workflows/ci.yml` 当前调用：

```yaml
run: python scripts/run_ci.py --coverage-fail-under 50 --coverage-xml coverage.xml
```

仓库实际存在：

```text
scripts/ci.py
```

因此当前 workflow 在 GitHub Actions 中会因为脚本不存在而失败。

## 推荐修复

直接修改 `.github/workflows/ci.yml`：

```yaml
run: python scripts/ci.py --coverage-fail-under 50 --coverage-xml coverage.xml
```

## 不推荐方案

新增 `scripts/run_ci.py` shim 也能修，但不推荐作为首选。

原因：

- 仓库文档和 `doc_sync.py` 已经以 `scripts/ci.py` 为主入口。
- 增加 shim 会制造第二个 CI 入口。
- 后续 release switch 也可能继续围绕 `scripts/ci.py` 做合同检查。

只有在外部系统已经固定调用 `scripts/run_ci.py` 且短期不能改时，才考虑 shim。

## 施工步骤

### Step 0：确认工作树

```powershell
git status --short
```

验收：

- 没有未解释改动。
- 如有未提交改动，确认是否属于本轮施工。

### Step 1：确认脚本存在性

```powershell
Test-Path scripts\ci.py
Test-Path scripts\run_ci.py
```

预期：

- `scripts\ci.py` 为 `True`。
- `scripts\run_ci.py` 为 `False` 或不存在。

### Step 2：修改 workflow

修改文件：

```text
.github/workflows/ci.yml
```

替换：

```text
python scripts/run_ci.py
```

为：

```text
python scripts/ci.py
```

### Step 3：本地验证 CI 命令

```powershell
python scripts\ci.py --coverage-fail-under 50 --coverage-xml coverage.xml --keep-going
```

如果命令失败，继续按失败分类处理，不要先改低门槛。

### Step 4：验证 workflow 不再引用旧脚本

```powershell
rg -n "scripts/run_ci.py|scripts/ci.py" .github docs scripts README.md
```

验收：

- `.github/workflows/ci.yml` 只引用 `scripts/ci.py`。
- 不存在仍要求 workflow 使用 `scripts/run_ci.py` 的当前文档。

### Step 5：提交前检查

```powershell
git diff --check
git status --short
```

验收：

- 没有 trailing whitespace。
- 只修改预期文件。

## 失败分类与处理

| 失败类型 | 现象 | 处理 |
| --- | --- | --- |
| 脚本不存在 | `can't open file scripts/run_ci.py` | 修 workflow 路径 |
| 依赖缺失 | `ModuleNotFoundError` | 检查 `requirements-dev.txt` 和 CI install |
| 测试失败 | unittest assertion fail | 定位失败测试，按 bug 修 |
| coverage 不足 | `Coverage failure` | 补测试或确认是否为非 P0，禁止直接降阈值 |
| artifact 缺失 | 没有 `coverage.xml` | 检查 `--coverage-xml` 和 coverage post-processing |

## P0 验收标准

- GitHub Actions 能启动 `scripts/ci.py`。
- 本地 CI 命令可执行。
- 如果仍失败，失败原因已经不是“脚本路径错误”。

## 回滚

如修改后出现不可预期问题，回滚方式：

```powershell
git restore .github/workflows/ci.yml
```

不要回滚其他文件。
