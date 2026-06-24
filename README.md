# Omni Skill Pipeline

Omni Skill Pipeline 用于把文本、音频、图像、视频、表格和混合语料证据，蒸馏成可复用、可追溯、可审核的技能工件：`SKILL.md`、`skill.json`、`SkillGraph`、publication manifest，以及可移植的 agent skill package。

当前发版候选版本是 `v0.2.5-internal.2`。这是内部 dogfood 与未来真实数据接入预案版本，不是外部 Beta、GA、SaaS 或生产部署承诺。

## 当前能力

- 文本：支持 `txt`、`md`、`markdown`、`rst`、`log`、`json`、`html`、`doc`、`docx`、`pdf`。
- 音频：支持 transcript-first 流程，可选接入 OpenAI ASR。
- 图像：支持 OCR 与场景摘要证据抽取；视觉/OCR 不确定内容仍需人工审核。
- 视频：支持 transcript、keyframe、OCR、场景摘要和时间线证据。
- 表格/时序：支持生成 `TABLE`、`METRIC`、`EVENT` 证据。
- V2 语义层：已包含 `Corpus`、`EvidenceNode`、`SemanticAtom`、`SkillGraph`、`Publication`。
- 审核控制：已包含质量评分、review policy、review task、review feedback、reviewer packet 和 review queue 操作。
- 发布交付：已包含 GitHub Release 工件包、校验和、可安装 wheel、发布说明和 release consumer smoke（发布消费者冒烟验证）。
- 内部 dogfood 加固：已包含 live API smoke 证据，以及本地 file-backed artifact 的可选 Fernet 加密。
- 上线门禁：已包含 release switch、trial metrics、agent smoke、CI evidence、多模态质量、GL-64 real-loop preflight、Docker/Postgres/K8s/secrets/product/observability readiness 的显式检查入口；这些门禁不会伪造真实外部证据。

## 快速开始

PowerShell:

```powershell
py -3.11 -m venv .venv
. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python -m omni_skill_pipeline.cli show-template
```

POSIX:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python -m omni_skill_pipeline.cli show-template
```

执行本地回归门禁：

```bash
python scripts/ci.py --isolate-test-files --coverage-fail-under 50 --coverage-xml coverage.xml
```

## 主要入口

- 包根目录：`src/omni_skill_pipeline/`
- CLI 入口：`src/omni_skill_pipeline/cli.py`
- API 应用：`apps/api/main.py`
- Worker 应用：`apps/worker/main.py`
- 模板契约：`docs/latest/contracts/SKILL.template.md`
- Skill schema：`docs/latest/contracts/skill.schema.json`
- 操作手册入口：`docs/latest/operations/OPERATIONS.md`

## 发布

- 当前内部发版候选：`v0.2.5-internal.2`
- 上一已发布内部 tag：`v0.2.4-internal.1`
- CI 门禁：`.github/workflows/ci.yml`
- Release 工作流：`.github/workflows/release.yml`
- 发布说明：`docs/releases/notes/v0.2.5-internal.2.md`
- GitHub Release 手册：`docs/latest/operations/runbooks/github-release-workflow.md`
- 本地 artifact 加密手册：`docs/latest/operations/runbooks/artifact-encryption.md`

正式 GitHub Release 通过推送 `v*` tag 创建，也可以手动触发 `Release` workflow，并设置 `publish_github_release=true` 与 `release_tag`。Release workflow 会生成源码包、wheel、`coverage.xml`、`release-manifest.json`、`release-summary.md`、`SHA256SUMS`，并在上传/发布前执行 release consumer smoke（发布消费者冒烟验证）。

## 文档分层

- `docs/latest/`：最新已发布手册和当前操作参考。
- `docs/working/`：当前迭代计划、状态、baseline 和证据。
- `docs/releases/`：changelog、发布说明和发布决策标准。
- `docs/archive/`：历史评估、已替代状态快照和已完成能力归档。

选择文档时先从 `docs/INDEX.md` 开始。

## 当前工程判断

内部 dogfood 路径已经可供内部使用。广义外部上线 gate 仍保持 `HOLD`，原因是 launch-gate-eligible 的真实业务闭环证据仍不足：当前仓库没有 10 个可上线真实 loop，也没有 text/audio/image/video 四类真实模态覆盖。后续拿到真实数据或公开 demo 闭环样本时，先按 `docs/latest/operations/runbooks/real-data-intake-and-validation.md` 投递本地原始数据和脱敏 manifest，再运行 GL-64、GL-13、trial metrics 与 launch gate。Docker、Postgres、K8s、Vault/KMS、生产 key rotation、OCR hardening 和外部真实闭环采集，仍不属于当前内部版本已完成边界，除非后续 release 明确关闭这些能力。
