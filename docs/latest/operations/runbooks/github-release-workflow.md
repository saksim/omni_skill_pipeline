# GitHub Release 工作流

## 结论

仓库已经具备轻量级 release workflow，用于当前 internal-to-main 的发布模型。

它本身不会部署到生产 URL。它的作用是把绿色 `main` commit 转成可验证的 release candidate pack，并在推送 `v*` tag 时生成 GitHub Release。

当前已发布内部版本：`v0.2.3-internal.1`。

## 入口

Workflow 文件：

```text
.github/workflows/release.yml
```

触发方式：

- push 到 `main`：构建 release candidate artifact pack。
- push `v*` tag：构建同一套 pack，并发布 GitHub Release。
- 手动 `workflow_dispatch`：构建 pack；当 `publish_github_release=true` 且提供 `release_tag` 时，可发布 GitHub Release。

## Release Candidate 工件

每次 `main` push 会执行：

```bash
python scripts/ci.py --isolate-test-files --coverage-fail-under 50 --coverage-xml coverage.xml
python -m pip wheel . --no-deps --wheel-dir dist
python scripts/release_artifacts.py --release-id "$RELEASE_ID" --output-dir "release-artifacts/$RELEASE_ID" --dist-dir dist --coverage-xml coverage.xml
```

上传 artifact 包含：

- `omni-skill-pipeline-source-<release_id>.tar.gz`
- `dist/` 中生成的 Python wheel
- `coverage.xml`
- `release-manifest.json`
- `release-summary.md`
- `SHA256SUMS`

正式打 tag 前，如果需要可复现交付，使用 candidate pack。

## 正式 GitHub Release

如果 release 改变了操作人员或用户行为，打 tag 前应新增人类可读 release notes：

```text
docs/releases/notes/<release_tag>.md
```

该文件存在时，`scripts/release_artifacts.py` 会把它插入生成的 `release-summary.md` 顶部，位于机器 metadata 和 artifact table 之前。

推荐路径：

```bash
git fetch origin main
git checkout main
git pull --ff-only origin main
git tag <release_tag>
git push origin <release_tag>
```

示例：

```bash
git tag v0.2.3-internal.1
git push origin v0.2.3-internal.1
```

该 tag 会触发 release workflow，并用生成的 artifact pack 发布 GitHub Release。

手动路径：

1. 打开 GitHub Actions 中的 `Release` workflow。
2. 从 `main` 运行 workflow。
3. 设置 `publish_github_release=true`。
4. 设置 `release_tag`，例如 `v0.2.3-internal.1`。

如果 tag 不存在，workflow 会先创建 tag，然后执行：

```bash
gh release create "$RELEASE_TAG" release-artifacts/$RELEASE_ID/* --notes-file "release-artifacts/$RELEASE_ID/release-summary.md"
```

## 验证

把 release 当作可用前，先执行：

```bash
sha256sum -c SHA256SUMS
python -m pip install omni_skill_pipeline-*.whl
python -m omni_skill_pipeline.cli show-template
```

自动 consumer smoke：

```bash
python scripts/release_consumer_smoke.py --release-dir . --expected-release-id <release_tag>
```

`Release` workflow 会在 artifact 上传/发布前，对生成的 artifact pack 执行同一条 smoke。

最新已发布内部版本示例：

```bash
python scripts/release_consumer_smoke.py --release-dir . --expected-release-id v0.2.3-internal.1
```

如果目标是 container/API deployment，继续执行：

```bash
bash scripts/linux_release.sh
```

Docker/Postgres release switch 仍是完整生产声明的严格门禁。GitHub Release workflow 是稳定的打包和发布层，不是外部部署证明。

## 回滚

如果 GitHub Release 有问题：

1. 在 GitHub Releases 中标记为 pre-release 或删除该 release。
2. 只有在确认操作人员尚未消费该 tag 时，才删除 tag。
3. 基于修复后的 `main` commit 使用新 tag 重新运行 workflow。

不要覆盖已经被消费的 tag。
