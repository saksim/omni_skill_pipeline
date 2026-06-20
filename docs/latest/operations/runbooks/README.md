# Runbook 入口

## 可用 Runbook

- 标准 pre-release 测试脚本：`bash scripts/linux_release.sh`
- [GitHub Release 工作流](github-release-workflow.md)：`main` release candidate pack、`v*` tag GitHub Release、manifest、summary 和 checksum。
- [Artifact Encryption](artifact-encryption.md)：启用、验证、关闭并排查本地 file-backed artifact 与 review queue 文件的可选 Fernet 加密。
- [Docker Zero-to-Release](docker-zero-to-release.md)：裸 Linux、Docker-only 测试、release gate、deploy、验收和 rollback。
- [Launch Beta](launch-beta.md)：外部 beta deploy、验收、rollback、日志巡检和临时目录清理。
- [Production Operations Baseline](production-operations-baseline.md)：GL-05 生产操作流程，覆盖 deploy、validation、rollback、backup/restore、incident response、alerting 和 operations evidence collection。
- [Controlled External Beta Onboarding](controlled-external-beta-onboarding.md)：GL-03 操作流程，覆盖 manifest validation、distill、review、export、validation、security gate、metrics 和 readiness decision。
- [Controlled Trial Loop](controlled-trial-loop.md)：CBT-11 端到端 controlled-trial runner，流程为 `manifest -> distill -> review packet -> export -> validate -> metrics`。
- [真实数据接入与验收手册](real-data-intake-and-validation.md)：定义真实原始数据放置、脱敏 manifest 投递、GL-64/GL-13 验收和当前无真实数据时的内部 dogfood 口径。
- [Real Trial Loop Collection](real-trial-loop-collection.md)：GL-12 collector 与 GL-13 one-command bridge，用于 real-loop evidence classification、trial metrics generation 和 launch-gate progress tracking。
- [Agent Smoke Protocol](agent-smoke-protocol.md)：CBT-12 针对 Codex/Claude Code/OpenCode 的人工 live-agent smoke 检查和状态记录。

## 说明

- Runbook 是可执行操作文档；命令必须与 `scripts/` 和当前 API contract 保持一致。
- GitHub publication 使用 `Release` workflow。它会生成 source、wheel、coverage、manifest、summary 和 `SHA256SUMS`。
- 严格 container/API release 证据优先使用 `scripts/linux_release.sh`，不要手动复制分散命令。该脚本会输出包含日志、退出码、baseline 和 summary 的 `release-artifacts-<release_id>.tar.gz`。
- `v0.2.5-internal.1` 是当前内部 dogfood 发版候选边界。真实数据接入路径记录在 `real-data-intake-and-validation.md`；非基础设施加固路径记录在 `artifact-encryption.md`；Docker、Postgres、K8s 和 external real-loop gate 是独立门禁。
