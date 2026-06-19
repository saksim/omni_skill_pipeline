# Artifact 加密 Runbook

## 目的

本手册用于在内部 dogfood 路径中，为 file-backed artifact 和 review queue 文件启用可选本地加密。

本手册适用于 `v0.2.3-internal.1` 及后续版本。它不提供 Vault/KMS 集成、自动 key rotation、K8s secret 管理或 Postgres 加密。

## 范围

覆盖：

- `skills/drafts/` 下由 `FileArtifactRepository` 写出的 artifact。
- `skills/drafts/review_queue/` 下的 review queue 文件。
- 使用 repository mode `file` 的本地开发环境或内部 dogfood 环境。

不覆盖：

- Postgres repository 加密。
- dual-write primary database 加密。
- 云 secret manager 集成。
- 生产 key escrow 或自动轮换。
- 旧 plaintext artifact 的批量回溯迁移。

## 前置条件

- 已激活 Python 3.11 环境。
- 已通过 `python -m pip install -r requirements-dev.txt` 安装依赖，或已安装 release wheel。
- 已安装 `cryptography`。它是 `pyproject.toml` 中的 runtime dependency。
- 操作人员已经决定 Fernet key 存放在哪里，且该位置在仓库外。

不要提交 `OMNI_ARTIFACT_ENCRYPTION_KEY` 或任何生成 key。

## 生成 Key

```bash
python -c "from omni_skill_pipeline.artifact_crypto import generate_fernet_key; print(generate_fernet_key())"
```

把输出保存到本地 secret store、密码管理器或 CI secret。后续读取加密 artifact 时必须使用同一个 key。

## 启用加密

PowerShell:

```powershell
$env:OMNI_ARTIFACT_REPOSITORY_MODE = "file"
$env:OMNI_ARTIFACT_ENCRYPTION_MODE = "fernet"
$env:OMNI_ARTIFACT_ENCRYPTION_KEY = "<generated-key>"
$env:OMNI_ARTIFACT_ENCRYPTION_KEY_ID = "internal-dogfood-local"
```

POSIX:

```bash
export OMNI_ARTIFACT_REPOSITORY_MODE=file
export OMNI_ARTIFACT_ENCRYPTION_MODE=fernet
export OMNI_ARTIFACT_ENCRYPTION_KEY="<generated-key>"
export OMNI_ARTIFACT_ENCRYPTION_KEY_ID="internal-dogfood-local"
```

## 冒烟验证

跑一次小型 text distillation：

```bash
python -m omni_skill_pipeline.cli distill-text \
  --title "Artifact encryption smoke" \
  --content "Internal dogfood artifact encryption smoke." \
  --domain operations
```

然后检查 `skills/drafts/` 下任意一个新生成 JSON artifact。文件内容应是 JSON encryption envelope，并包含：

- `schema_version`: `omni_artifact_encryption.v1`
- `algorithm`: `fernet`
- `key_id`: 当前配置的 key id
- `ciphertext`: 加密后的 payload

原始 plaintext 不应在落盘文件中直接可读。

## Review Queue 冒烟验证

当生成需要 review 的输出时，pending queue item 也会被加密。配置了正确 key 的 repository 仍然可以 list 和 claim：

```bash
python -m omni_skill_pipeline.cli review-queue --action list --queue-status pending --limit 5
python -m omni_skill_pipeline.cli review-queue --action claim --consumer encryption-smoke
```

如果 key 缺失或错误，加密 queue entry 将无法读取。恢复正确 key 后再重试。

## 关闭加密

清空加密变量，或把 mode 设为 `off`。

PowerShell:

```powershell
$env:OMNI_ARTIFACT_ENCRYPTION_MODE = "off"
$env:OMNI_ARTIFACT_ENCRYPTION_KEY = ""
```

POSIX:

```bash
export OMNI_ARTIFACT_ENCRYPTION_MODE=off
unset OMNI_ARTIFACT_ENCRYPTION_KEY
```

重要行为：

- 加密关闭时，新 artifact 会以 plaintext 写入。
- 加密关闭时，旧 plaintext artifact 仍可读取。
- 既有加密 artifact 仍需要原 key；`off` 模式不会静默解密它们。

## 手动 Key Rotation

当前未实现自动 key rotation。如需手动轮换：

1. 停止所有使用 `FileArtifactRepository` 的写入进程。
2. 在所有必要加密 artifact 完成迁移或到期前，保留旧 key。
3. 生成新的 Fernet key。
4. 将 `OMNI_ARTIFACT_ENCRYPTION_KEY` 设为新 key，并更新 `OMNI_ARTIFACT_ENCRYPTION_KEY_ID`。
5. 执行上面的冒烟验证。
6. 在操作记录中写下 rotation 日期、旧 key id、新 key id 和 operator。

只要旧加密 artifact 仍可能需要读取，就不要删除旧 key。

## 排障

| 现象 | 可能原因 | 处理 |
| --- | --- | --- |
| `OMNI_ARTIFACT_ENCRYPTION_KEY is required` | 启用了 `fernet` 但未设置 key。 | 设置 `OMNI_ARTIFACT_ENCRYPTION_KEY`，或把 mode 改为 `off`。 |
| `must be a urlsafe base64-encoded 32-byte Fernet key` | key 格式错误。 | 使用 `generate_fernet_key` 重新生成。 |
| 启用加密后 review queue list 为空 | 现有加密 entry 无法用当前 key 解密。 | 恢复原 key，或在正确环境中检查 queue 文件。 |
| 新 artifact 仍出现 plaintext | 加密 mode 未设置/已关闭，或进程启动早于环境变量更新。 | 重启进程并确认环境变量。 |
| 关闭加密后无法读取加密 artifact | 加密文件仍需要 key。 | 使用原 key 重新启用 `fernet` 后读取。 |

## 验证命令

```bash
python -m unittest tests.test_artifact_encryption tests.test_openai_provider_config tests.test_service_factory_split
python scripts/doc_sync.py --output -
```

完整 release 打包请使用 [GitHub Release Workflow](github-release-workflow.md)。如果目标是 Docker/Postgres 生产声明，请继续使用更严格的基础设施 runbook，不要把本地加密 runbook 当作充分证据。
