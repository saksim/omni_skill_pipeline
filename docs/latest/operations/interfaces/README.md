# 操作接口

本文档列出当前操作接口，以及工程师在运行或变更这些接口前应该阅读的文档。

## CLI

入口：

```bash
python -m omni_skill_pipeline.cli <command>
```

主要命令：

- `show-template`
- `distill-text`
- `distill-audio`
- `distill-image`
- `distill-tabular`
- `distill-video`
- `distill-corpus`
- `export-skill`
- `validate-skill`
- `review-queue`
- `governance-report`
- `record-deletion`
- `upsert-retention-policy`

手册：`docs/latest/operations/cli.md`。

## API

入口：

```bash
python -m uvicorn apps.api.main:app --reload
```

主要路由：

- `GET /healthz`
- `GET /v1/templates/skill`
- `POST /v1/distill/text`
- `POST /v1/distill/audio`
- `POST /v1/distill/image`
- `POST /v1/distill/tabular`
- `POST /v1/distill/video`
- `POST /v1/distill/corpus`
- review queue routes
- governance routes

手册：`docs/latest/operations/api.md`。

## Worker

入口：

```bash
python -m omni_skill_pipeline.worker
```

当操作人员需要 filesystem queue 语义，而不是直接 CLI/API 调用时，使用 worker 处理排队的 distillation、review 和 publication 任务。

手册：`docs/latest/operations/worker.md`。

## Review Queue

CLI 示例：

```bash
python -m omni_skill_pipeline.cli review-queue --action list --queue-status pending --limit 20
python -m omni_skill_pipeline.cli review-queue --action claim --consumer reviewer-1
python -m omni_skill_pipeline.cli review-queue --action approve --review-task-id <id> --reviewer reviewer-1
```

当 `OMNI_ARTIFACT_ENCRYPTION_MODE=fernet` 且配置了正确 key 时，加密 queue 文件也可以被读取和操作。

手册：

- `docs/latest/operations/cli.md`
- `docs/latest/operations/runbooks/artifact-encryption.md`

## Release 工件

Release 工作流：

```text
.github/workflows/release.yml
```

生成的 release pack 包含：

- source archive
- wheel
- `coverage.xml`
- `release-manifest.json`
- `release-summary.md`
- `SHA256SUMS`

Consumer smoke：

```bash
python scripts/release_consumer_smoke.py --release-dir <release-dir> --expected-release-id <release-tag>
```

手册：`docs/latest/operations/runbooks/github-release-workflow.md`。

## Gate 接口

- 内部 dogfood gate：`python scripts/internal_launch_gate.py --output - --summary-output - --print-json`
- 外部 launch gate：`python scripts/launch_gate.py --output - --summary-output - --print-json`
- Release switch：`python scripts/release_switch.py ...`
- 文档同步：`python scripts/doc_sync.py --output -`

内部 dogfood readiness 和外部 launch readiness 是两个不同声明。不要把内部 `READY_FOR_INTERNAL_DOGFOOD` 当成外部上线批准。
