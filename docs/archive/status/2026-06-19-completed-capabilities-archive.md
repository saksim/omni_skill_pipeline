# 已完成能力归档 2026-06-19

本归档记录截至 `v0.2.3-internal.1` 已经脱离 active construction 的能力。它是“已经完成过什么”的历史证据，不是当前操作手册；当前操作请使用 `docs/latest/`。

## 归档结论

项目已经完成非基础设施路径的内部 dogfood 发布轨道：

- 通过 GitHub Releases 发布 package 和 source snapshot。
- 验证已安装 wheel 的消费者使用路径。
- 跑通内部 API dogfood smoke。
- 让 dogfood 输出进入 review queue 并可见。
- 为本地 file-backed artifact 提供可选加密。

这些能力足够支撑内部 dogfood，但不足以声明外部 Beta、GA、SaaS 或生产运行时就绪。

## 已完成发布里程碑

| 版本 | 归档状态 | 已完成能力 |
| --- | --- | --- |
| `v0.2.0-internal.1` | 已归档完成 | 正式 GitHub Release 工作流、release artifact pack、release manifest、release summary、checksum 和操作发布手册。 |
| `v0.2.1-internal.1` | 已归档完成 | 将 contract 资源打包进 wheel、installed-wheel template fallback、release consumer smoke 脚本和 workflow consumer-smoke 门禁。 |
| `v0.2.2-internal.1` | 已归档完成 | 内部 dogfood API smoke，覆盖 health、template、text distill、pending review queue 可见性、JSON/Markdown smoke 证据和 API version metadata 对齐。 |
| `v0.2.3-internal.1` | 已归档完成 | file-backed 本地 artifact 的可选 Fernet envelope、加密 review queue 连续性、缺 key 失败行为、config wiring 和 service factory wiring。 |

## 已完成能力域

### 文档生命周期

- 仓库采用四层文档结构：
  - `docs/latest/`：当前已发布手册。
  - `docs/working/`：当前迭代计划、baseline 和证据。
  - `docs/releases/`：changelog、release notes 和发布标准。
  - `docs/archive/`：历史记录和已完成能力归档。
- 当前总索引是 `docs/INDEX.md`。
- 根入口文档是 `README.md`。

### 核心蒸馏链路

- 项目已经具备 evidence-to-skill 主链，覆盖 text、audio、image、video、tabular/time-series 和 corpus 输入。
- V2 语义层包含 `Corpus`、`EvidenceNode`、`SemanticAtom`、`SkillGraph` 和 `Publication`。
- file-backed distillation 会在 `skills/drafts/` 下写出 skill document、bundle metadata、publication manifest、quality artifact、review artifact 和 reviewer packet。

### 审核与治理

- 已实现 quality scoring、review policy、review task 创建、review feedback、reviewer packet 和 review queue 操作。
- Review queue 支持 list、claim/consume、close、approve、reject 和 needs-rework。
- 早期 governance surface 已存在，覆盖 cost/audit/deletion/retention records、tenant access control、quota checks 和 platform-console summary view。

### 发布与消费者交付

- `Release` workflow 会构建 source、wheel、coverage、manifest、summary 和 checksum assets。
- 人类可读发布说明存放在 `docs/releases/notes/`。
- `scripts/release_consumer_smoke.py` 会校验 checksum、manifest contract、wheel install 和 installed CLI template access。
- Release consumer smoke（发布消费者冒烟验证）已接入 `.github/workflows/release.yml`，位于 artifact 上传/发布之前。

### 内部 dogfood 运行证据

- `scripts/internal_launch_gate.py` 能区分内部 dogfood readiness 和更严格的外部 launch gate。
- `scripts/internal_dogfood_smoke.py` 会校验本地 API health、template retrieval、text distillation 和 pending review queue visibility。
- 当前内部 dogfood readiness 证据为 `READY_FOR_INTERNAL_DOGFOOD`。
- 外部 launch gate 仍为 `HOLD`，这是预期且正确的状态。

### 本地 Artifact 加密

- `FileArtifactRepository` 支持对本地 artifact 文件和 review queue 文件启用可选 `fernet` 加密。
- 加密默认关闭，以保持向后兼容。
- 使用同一配置 key 时，加密 artifact 仍可查询、消费和关闭。
- 加密关闭时，既有 plaintext artifact 仍可读取。

## 明确未完成项

以下项目没有归档为完成，也不得作为当前 release claim 对外呈现：

- 外部 Beta readiness。
- GA readiness。
- 公共 SaaS readiness。
- launch-gate-eligible 的真实业务闭环数量。
- 超出当前 review-required 行为的 OCR hardening。
- 当前环境中的 Docker real-run closure。
- Postgres 生产验证。
- K8s、Helm 或 Kubernetes 操作。
- Vault/KMS 集成。
- 自动 key rotation。
- 针对真实基础设施的生产 backup/restore 验证。
- 广义公开 performance benchmark。

## 证据入口

- 发布说明：
  - `docs/releases/notes/v0.2.0-internal.1.md`
  - `docs/releases/notes/v0.2.1-internal.1.md`
  - `docs/releases/notes/v0.2.2-internal.1.md`
  - `docs/releases/notes/v0.2.3-internal.1.md`
- 当前 release changelog：`docs/releases/CHANGELOG.md`
- GitHub Release 手册：`docs/latest/operations/runbooks/github-release-workflow.md`
- Artifact 加密手册：`docs/latest/operations/runbooks/artifact-encryption.md`
- 内部 dogfood readiness 摘要：`docs/working/status/baselines/internal-dogfood-readiness-summary.md`
- 内部 dogfood API smoke 摘要：`docs/working/status/baselines/internal-dogfood-api-smoke-summary.md`

## 维护规则

后续如果某个“未完成项”在新的 release 中真正完成，必须先新增 `docs/releases/notes/` 下的 release note，更新 `docs/latest/` 的当前操作手册，并且只有在能力已发布且通过对应证据门禁后，才能新增新的 archive record。
