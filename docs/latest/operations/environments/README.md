# 操作环境

本文档说明不同运行环境应该使用哪些命令，以及每种环境可以声明什么 release claim。

## 本地开发环境

用途：编辑代码、运行单测、调试 CLI/API 行为、生成本地 artifact。

使用：

```bash
python -m pip install -r requirements-dev.txt
python -m omni_skill_pipeline.cli show-template
python scripts/ci.py --isolate-test-files --coverage-fail-under 50 --coverage-xml coverage.xml
```

可选本地 artifact 加密：

```bash
export OMNI_ARTIFACT_ENCRYPTION_MODE=fernet
export OMNI_ARTIFACT_ENCRYPTION_KEY="<generated-key>"
```

详见 `docs/latest/operations/runbooks/artifact-encryption.md`。

## 内部 Dogfood 环境

用途：让内部操作人员运行当前 package，并采集内部 API/CLI/review queue 证据。

预期口径：

- `internal_dogfood_only=true`
- 生成 skill 的安全默认值仍是人工 review。
- 外部 launch gate 可以继续保持 `HOLD`。
- 生成证据应写入 `docs/working/status/baselines/`。

推荐检查：

```bash
python scripts/internal_launch_gate.py --output - --summary-output - --print-json
python -m uvicorn apps.api.main:app --reload
python scripts/internal_dogfood_smoke.py --base-url http://127.0.0.1:8000 --output - --summary-output -
```

## Release 打包环境

用途：从 `main` 或 `v*` tag 生成可验证的 GitHub Release artifact pack。

使用：

```bash
python scripts/ci.py --isolate-test-files --coverage-fail-under 50 --coverage-xml coverage.xml
python -m pip wheel . --no-deps --wheel-dir dist
python scripts/release_artifacts.py --release-id "$RELEASE_ID" --output-dir "release-artifacts/$RELEASE_ID" --dist-dir dist --coverage-xml coverage.xml
python scripts/release_consumer_smoke.py --release-dir "release-artifacts/$RELEASE_ID" --expected-release-id "$RELEASE_ID"
```

详见 `docs/latest/operations/runbooks/github-release-workflow.md`。

## 基础设施验证环境

用途：Docker/Postgres/runtime deployment 验证。

当前状态：

- Docker real-run closure 不属于 `v0.2.4-internal.1` 已归档完成范围。
- Postgres 生产验证不属于 `v0.2.4-internal.1` 已归档完成范围。
- K8s/Helm/Kubernetes 操作不是当前已完成 release claim。

只有当环境具备对应服务时，才使用更严格的基础设施 runbook：

```bash
bash scripts/linux_release.sh
```

详见 `docs/latest/operations/runbooks/docker-zero-to-release.md` 和 `docs/latest/operations/runbooks/production-operations-baseline.md`。

## 外部 Beta / GA

外部 launch gate 在 launch-gate-eligible 的真实业务闭环达到阈值前，仍应保持 `HOLD`。

不要把内部 dogfood 证据包装成外部 Beta、GA 或 SaaS 证据。
