# 操作文档审计 2026-06-19

## 目的

本审计记录 `v0.2.3-internal.1` 之后完成的文档刷新。目标是让当前操作手册与最新内部 dogfood release 保持一致，并记录哪些历史能力已经归档。

2026-06-20 追加：本轮中文文档刷新已经纳入 `v0.2.4-internal.1` 发版候选，归档记录见 `docs/archive/status/2026-06-20-documentation-localization-archive.md`。

## 范围

已检查并更新：

- `README.md`
- `docs/INDEX.md`
- `docs/latest/README.md`
- `docs/latest/operations/OPERATIONS.md`
- `docs/latest/operations/env.md`
- `docs/latest/operations/testing.md`
- `docs/latest/operations/environments/README.md`
- `docs/latest/operations/interfaces/README.md`
- `docs/latest/operations/runbooks/README.md`
- `docs/latest/operations/runbooks/github-release-workflow.md`
- `docs/latest/operations/runbooks/artifact-encryption.md`
- `docs/archive/README.md`
- `docs/archive/status/2026-06-19-completed-capabilities-archive.md`
- `docs/working/status/internal-dogfood-launch/README.md`
- `.env.example`

已阅读但未全文重写：

- 大体量 historical working 施工日志。它们包含旧上下文和生成证据；已完成事实现在由 archive record 表达，不再作为当前操作源。

## 已完成归档

完成态归档文件：

```text
docs/archive/status/2026-06-19-completed-capabilities-archive.md
```

已归档完成：

- 正式 GitHub Release 工作流和 artifact pack。
- packaged contract resources 与 installed-wheel fallback。
- release consumer smoke。
- 内部 dogfood API smoke 证据。
- API version metadata 对齐。
- 本地 file artifact 加密。
- 加密 review queue 连续性。
- 当前文档生命周期分层。

未归档为完成：

- 外部 Beta readiness。
- GA/SaaS readiness。
- 真实 launch-gate-eligible 业务闭环数量。
- OCR hardening。
- Docker real-run closure。
- Postgres 生产验证。
- K8s/Kubernetes 操作。
- Vault/KMS 集成。
- 自动 key rotation。

## 操作手册更新

当前操作路径已经在以下文件中明确：

- `docs/latest/operations/OPERATIONS.md`
- `docs/latest/operations/testing.md`
- `docs/latest/operations/runbooks/README.md`

Artifact 加密已有可执行 runbook：

```text
docs/latest/operations/runbooks/artifact-encryption.md
```

环境与接口占位文档已替换为可操作说明：

- `docs/latest/operations/environments/README.md`
- `docs/latest/operations/interfaces/README.md`

## 验证计划

执行：

```bash
python scripts/doc_sync.py --output -
python -m unittest tests.test_artifact_encryption tests.test_openai_provider_config tests.test_service_factory_split
git diff --check
```

预期结果：

- doc sync 通过。
- 加密/config/service factory 定向测试通过。
- 无 whitespace 错误。

## 一句话总结

已归档截至 `v0.2.3-internal.1` 的内部 dogfood 完成能力，并刷新操作手册，让工程师能从当前文档直接运行、验证、发布和启用本地 artifact 加密。
