# 操作文档入口

这是 `v0.2.4-internal.1` 发版候选的当前操作入口。

当前支持的上线姿态是内部 dogfood。使用这些文档可以在内部路径下运行、验证、打包和操作本仓库。不要把这些文档当作外部 Beta、GA、SaaS、Docker/Postgres 生产验证或 K8s readiness 的证据。

## 当前操作路径

1. 按 [Environment](env.md) 和 `.env.example` 准备环境。
2. 按 [CLI](cli.md) 验证本地 CLI/package 可用。
3. 按 [Testing](testing.md) 跑本地回归门禁。
4. 需要 GitHub release package 时，按 [GitHub Release Workflow](runbooks/github-release-workflow.md) 执行。
5. 需要保护 file-backed artifact 时，按 [Artifact Encryption](runbooks/artifact-encryption.md) 执行。
6. 需要 live internal API dogfood 证据时，使用 release notes 和 runbook 中记录的 internal dogfood smoke 命令。

## 当前操作域

- [CLI](cli.md)
- [API](api.md)
- [Worker](worker.md)
- [Environment](env.md)
- [Testing](testing.md)
- [Script Name Map](script-name-map.md)
- GitHub release workflow：`.github/workflows/release.yml`
- 标准 Linux release 测试脚本：`bash scripts/linux_release.sh`
- [V1 -> V2 Migration Runbook](v1-to-v2-migration-runbook.md)

## 扩展入口

- [Runbooks](runbooks/README.md)
- [GitHub Release Workflow](runbooks/github-release-workflow.md)
- [Artifact Encryption](runbooks/artifact-encryption.md)
- [Docker Zero-to-Release Runbook](runbooks/docker-zero-to-release.md)
- [Launch Beta Runbook](runbooks/launch-beta.md)
- [Production Operations Baseline](runbooks/production-operations-baseline.md)
- [Controlled External Beta Onboarding](runbooks/controlled-external-beta-onboarding.md)
- [Environments](environments/README.md)
- [Interfaces](interfaces/README.md)

## 当前边界

- `v0.2.4-internal.1` 继承已完成的非基础设施内部 dogfood 路径，并补齐中文操作文档、发布记录和归档记录。
- 本地 file artifact 加密是可选能力，默认关闭。
- Docker、Postgres、K8s、Vault/KMS、自动 key rotation、OCR hardening 和 external real-loop collection 都不是当前已完成 release claim。
- `scripts/launch_gate.py` 仍可能返回 `HOLD`；这会阻断外部上线声明，不阻断内部 dogfood 操作。

## 说明

- 本文件是当前操作文档入口。
- 细节按执行界面拆分到 CLI、API、worker、environment、runbook 和 script-name 文档中，避免单个文件过大。
