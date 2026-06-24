# P0：Release Artifact 可复现发布说明

## 1. 背景

当前项目已有 release artifact、GitHub Release、发版产物校验等机制。但评估中在附件源码包形态下运行：

```bash
python scripts/release_artifacts.py \
  --release-id test-eval \
  --output-dir /tmp/omni_release_artifacts \
  --dist-dir /tmp/omni_dist \
  --coverage-xml coverage.xml
```

失败：

```text
release artifact packaging failed: git archive failed: fatal: not a git repository
```

这说明 release artifact 脚本依赖有效 Git 仓库。若只在 GitHub Actions checkout 中使用，可能成立；但附件源码包、客户交付源码包、本地解压包无法复现。

## 2. 风险

如果不修复，会导致：

1. 发布流程只能在特定 CI 环境中运行。
2. 用户拿到源码包无法复现 release artifact。
3. 外部 Beta 交付包难以审计。
4. release consumer smoke 无法独立执行。
5. 后续安全扫描、SBOM、签名、checksum 体系无法稳定落地。

## 3. 目标

Release artifact 必须支持以下两种模式之一：

### 推荐：双模式支持

| 模式 | 条件 | 行为 |
|---|---|---|
| Git checkout 模式 | 当前目录是有效 git repo | 使用 `git archive` 生成 source archive |
| Source tree fallback 模式 | 当前目录不是 git repo | 直接基于当前 source tree 打包，并排除临时目录 |

### 可接受：强文档约束

如果暂不实现 fallback，文档必须明确：

```text
release_artifacts.py 只能在有效 Git checkout 中运行，不支持普通源码解压包。
```

但这只适合 internal，不建议用于 external beta。

## 4. 建议代码施工范围

重点检查：

```text
scripts/release_artifacts.py
scripts/release_consumer_smoke.py
scripts/release_gate.py
.github/workflows/*release*.yml
docs/latest/operations/*release*.md
docs/releases/notes/*
```

## 5. Source tree fallback 设计

### 5.1 fallback 触发条件

```text
git rev-parse --is-inside-work-tree != 0
or
git archive failed
```

### 5.2 fallback 排除规则

打包源码树时必须排除：

```text
.git/
.venv/
venv/
__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
dist/
build/
*.egg-info/
/tmp/
*.pyc
.DS_Store
node_modules/
```

### 5.3 fallback manifest 字段

release manifest 中必须记录：

```json
{
  "source_archive_mode": "git_archive|source_tree_fallback",
  "git_commit": "<commit-or-null>",
  "git_dirty": false,
  "source_archive_sha256": "...",
  "fallback_excludes": [".git", ".venv", "__pycache__"]
}
```

如果是 fallback 模式，`git_commit` 可为 null，但必须记录 source archive hash。

## 6. Release artifact 最小产物清单

建议 release 输出目录至少包含：

```text
release/
  release_manifest.json
  checksums.sha256
  source_archive.tar.gz
  dist/
    omni_skill_pipeline-<version>-py3-none-any.whl
  coverage.xml
  test_summary.json
  doc_sync.json
  launch_gate.json
  consumer_smoke.json
```

其中：

| 文件 | 必须 | 说明 |
|---|---:|---|
| `release_manifest.json` | 是 | release source of truth |
| `checksums.sha256` | 是 | 所有产物 checksum |
| `source_archive.tar.gz` | 是 | 源码归档 |
| wheel | 是 | 可安装发布物 |
| `coverage.xml` | 是 | 覆盖率证据 |
| `test_summary.json` | 是 | 测试摘要 |
| `doc_sync.json` | 是 | 文档同步证据 |
| `launch_gate.json` | 是 | 发布门禁证据 |
| `consumer_smoke.json` | 是 | 消费者验证证据 |

## 7. Consumer smoke 设计

`release_consumer_smoke.py` 应验证：

1. release manifest 存在；
2. release id 匹配；
3. checksum 文件完整；
4. wheel 可安装；
5. CLI 可执行；
6. 基础命令可运行；
7. portable skill package 可被 validate；
8. release artifact 中不包含明显临时文件。

## 8. 验收命令

### 8.1 Git checkout 模式

```bash
python -m pip wheel . --no-deps --wheel-dir dist
python scripts/release_artifacts.py \
  --release-id local-git-test \
  --output-dir /tmp/omni_release_git \
  --dist-dir dist \
  --coverage-xml coverage.xml
python scripts/release_consumer_smoke.py \
  --release-dir /tmp/omni_release_git \
  --expected-release-id local-git-test
```

期望全部通过。

### 8.2 Source tree fallback 模式

模拟源码包：

```bash
mkdir -p /tmp/source_tree_test
rsync -a --exclude .git ./ /tmp/source_tree_test/
cd /tmp/source_tree_test
python -m pip wheel . --no-deps --wheel-dir dist
python scripts/release_artifacts.py \
  --release-id local-source-tree-test \
  --output-dir /tmp/omni_release_source_tree \
  --dist-dir dist \
  --coverage-xml coverage.xml
python scripts/release_consumer_smoke.py \
  --release-dir /tmp/omni_release_source_tree \
  --expected-release-id local-source-tree-test
```

期望：

```text
source_archive_mode=source_tree_fallback
consumer smoke pass
```

## 9. 完成定义

该项完成必须满足：

1. Git checkout 模式可发布。
2. 普通源码树模式可发布，或文档明确拒绝且 release gate 能给出清晰错误。
3. release manifest 记录 archive mode。
4. 所有产物有 checksum。
5. release consumer smoke 通过。
6. CI 中包含 release artifact 测试。
7. 操作文档说明本地复现步骤。

## 10. 禁止的伪修复

不允许：

- 捕获 git 错误后仍返回 success；
- 只生成空 source archive；
- 忽略 checksum；
- 只在 GitHub Actions 能跑，文档不说明限制；
- consumer smoke 只检查文件存在，不检查可安装/可执行；
- 通过删除 release artifact 步骤来让 gate 通过。
