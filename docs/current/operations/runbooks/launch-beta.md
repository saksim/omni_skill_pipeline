# Launch Beta Runbook

## 判词

本手册用于 `LC-L1-19` 外部 Beta 发布前后操作，覆盖 deploy、rollback、验收、日志巡检与 `.tmp_omni_media/` 清理。

## Scope

- 目标环境：Linux 统一验测与受控外部 Beta。
- 服务入口：`apps/api/main.py`（容器内 `uvicorn apps.api.main:app`）。
- 当前基线：
  - 覆盖率门禁：`scripts/run_ci.py`
  - 容器烟测：`scripts/run_container_smoke.py`
  - 临时目录清理：`scripts/prune_tmp_media.py`

## Preflight Checklist

> 裸 Linux 且宿主机无 Python 时，优先执行 [Docker Zero-to-Release Runbook](docker-zero-to-release.md)。本手册保留 host Python 命令，是给已有 Python 执行环境的 Beta 快速发布链使用。

发布前必须满足：

- `requirements-dev.txt` 可安装成功。
- `OPENAI_API_KEY`、`OMNI_API_KEY`（若启用鉴权）在目标环境已配置。
- API 合同与错误语义已按 `docs/current/operations/api.md` 对齐。
- 临时目录保留策略已确认（`OMNI_TMP_MEDIA_RETENTION_HOURS`）。

## Deploy

### 1. Linux 统一测试门禁

```bash
python scripts/run_ci.py --coverage-fail-under 50 --coverage-xml coverage.xml
```

### 2. 容器构建与健康烟测

```bash
python scripts/run_container_smoke.py --image-tag omni-skill-pipeline:beta --port 18000
```

### 3. 正式拉起 Beta 实例

```bash
docker run --rm -d \
  --name omni-skill-beta \
  -p 8000:8000 \
  -e OPENAI_API_KEY="$OPENAI_API_KEY" \
  -e OMNI_API_KEY="$OMNI_API_KEY" \
  -e OMNI_LOG_FORMAT=json \
  -e OMNI_LOG_LEVEL=INFO \
  omni-skill-pipeline:beta
```

### 4. 发布后即时探活

```bash
curl -sS http://127.0.0.1:8000/healthz
```

预期：

- `status=ready`：允许继续放量。
- `status=degraded`：立即止血，进入 rollback 流程。

## Acceptance

Beta 验收最小清单：

- `GET /healthz` 返回 `200` 且 `status=ready`。
- `GET /v1/templates/skill` 可读。
- `POST /v1/distill/text`、`/audio`、`/image`、`/tabular`、`/video` 至少各完成一条 happy-path 样例。
- 鉴权开启时：
  - 无 key 返回 `401`
  - 错 key 返回 `403`
- 限流开启时：
  - 超限返回 `429`
  - 响应头包含 `Retry-After`
- 日志中存在 `api_request_completed`、`distill_start`、`distill_complete` 事件。

## Log Inspection

容器日志巡检（示例）：

```bash
docker logs --tail 300 omni-skill-beta
docker logs omni-skill-beta | grep -E '"event":"(api_request_completed|distill_start|distill_complete)"'
docker logs omni-skill-beta | grep -E '"status_code":(4|5)[0-9]{2}'
```

判定建议：

- 若 5xx 或 `runtime_error` 连续出现，视为高风险，进入 rollback。
- 若 `provider_unavailable` 激增，检查 provider 配置和上游可用性后再继续放量。

## Temp Cleanup

发布后/值班巡检周期执行：

```bash
python scripts/prune_tmp_media.py --dry-run
python scripts/prune_tmp_media.py --retention-hours 24
```

建议：

- 低流量：每 24 小时执行一次。
- 高频视频任务：每 6-12 小时执行一次。

## Rollback

触发条件（任一命中）：

- `healthz` 持续 `degraded`。
- 核心 distill 接口持续失败（5xx）且 10 分钟内无法止血。
- 鉴权/限流行为偏离合同，出现不可接受风险。

执行步骤：

1. 下线当前 Beta 容器：

```bash
docker rm -f omni-skill-beta
```

2. 启动上一稳定镜像（示例 tag：`omni-skill-pipeline:stable`）：

```bash
docker run --rm -d --name omni-skill-beta -p 8000:8000 omni-skill-pipeline:stable
```

3. 再次探活：

```bash
curl -sS http://127.0.0.1:8000/healthz
```

4. 记录回滚事件（时间、触发条件、日志摘要、后续修复 owner）。

## Release Record Template

每次 Beta 发布记录建议至少包含：

- `release_id`
- `image_tag`
- `operator`
- `start_time` / `end_time`
- `acceptance_result`
- `rollback_triggered`（yes/no）
- `incident_notes`
