# Internal Dogfood Verification Runbook

## 目标

提供内部玩具上线前后的可执行验收步骤。

## 前置条件

- Python 3.11 可用。
- 已安装项目依赖。
- 当前分支包含 workflow 修复。
- 如果执行 Docker smoke，Docker CLI 可用。

## Step 1：安装依赖

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

验收：

```powershell
python -m pip check
```

通过条件：

- 无依赖冲突。

## Step 2：CI 基线

```powershell
python scripts\ci.py --coverage-fail-under 50 --coverage-xml coverage.xml --keep-going
```

通过条件：

- exit code 为 `0`。
- 生成 `coverage.xml`。

失败处理：

- 不直接降低 `--coverage-fail-under`。
- 将失败归入 workflow、dependency、test、coverage、artifact 五类。

## Step 3：正式 launch gate 说明

```powershell
python scripts\launch_gate.py --output - --summary-output - --max-evidence-age-hours 0 --print-json
```

内部上线允许：

- 结果为 `HOLD`。
- 失败原因仅为真实 trial loop 覆盖不足。

内部上线不允许：

- 失败原因包含安全、doc sync、ops readiness、dry-run/relaxed evidence 等硬阻断。

## Step 4：内部 dogfood gate

```powershell
python scripts\internal_launch_gate.py --output - --summary-output - --print-json
```

通过条件：

- `decision=READY_FOR_INTERNAL_DOGFOOD`。

失败处理：

- 根据 `failed_checks` 修复。
- 不改正式 launch gate 规则。

## Step 5：本地 API 启动

```powershell
python -m uvicorn apps.api.main:app --reload
```

在另一个终端执行：

```powershell
curl http://127.0.0.1:8000/healthz
curl http://127.0.0.1:8000/v1/templates/skill
```

通过条件：

- `/healthz` 返回 HTTP 200。
- `/v1/templates/skill` 可读。

## Step 6：CLI happy path

建议执行一个最小 CLI smoke。

```powershell
python -m omni_skill_pipeline.cli show-template
```

通过条件：

- 命令成功退出。
- 输出包含 skill template 内容。

## Step 6.1: API happy path smoke

When the local API is running, execute the internal dogfood API smoke:

```powershell
python scripts\internal_dogfood_smoke.py --base-url http://127.0.0.1:8000 --output docs\working\status\baselines\internal-dogfood-api-smoke-report.json --summary-output docs\working\status\baselines\internal-dogfood-api-smoke-summary.md
```

Dry-run plan:

```powershell
python scripts\internal_dogfood_smoke.py --dry-run
```

Pass conditions:
- `/healthz` returns HTTP 2xx.
- `/v1/templates/skill` returns non-empty content.
- `/v1/distill/text` returns a skill payload.
- `/v1/review/queue` returns an `items` list.
- If text distillation creates a pending review task, that task is visible in the pending review queue.
- The JSON and Markdown smoke evidence files are written for launch-record review.

## Step 7：Docker smoke

如果当前环境有 Docker：

```powershell
python scripts\container_smoke.py --dry-run
python scripts\container_smoke.py --image-tag omni-skill-pipeline:dogfood --port 18000
python scripts\container_smoke.py --image-tag omni-skill-pipeline:dogfood --port 18000 --docker-config-dir .tmp_docker_config --output docs\working\status\baselines\internal-dogfood-container-smoke-report.json --summary-output docs\working\status\baselines\internal-dogfood-container-smoke-summary.md
```

`internal-dogfood-container-smoke-report.json` must be read before judging this step. A successful internal Docker smoke requires `decision=PASS` and `healthz=pass`; `docker_cli=pass` and `docker_daemon=pass` alone only prove the Docker host is reachable.

Known structured failure categories:

- `docker_cli_missing`: Docker CLI is not installed or not in `PATH`.
- `docker_daemon_unavailable`: Docker daemon is not reachable.
- `docker_base_image_pull_failed`: build reached Docker but could not pull base image metadata/token.
- `docker_build_failed`: Docker build failed after base-image access.
- `docker_run_failed`: container did not start.
- `health_check_failed`: container started but `/healthz` did not become available.

如果当前环境无 Docker：

- 记录为 `not_run`。
- 不作为第一天内部上线 blocker。
- 需要在 Linux/Docker host 上补跑。

## Step 8：上线记录

每次内部上线记录：

```text
release_id:
commit_sha:
operator:
started_at:
ended_at:
ci_result:
official_launch_gate_result:
internal_launch_gate_result:
api_health_result:
docker_smoke_result:
known_risks:
rollback_triggered:
notes:
```

建议路径：

```text
docs/working/status/baselines/internal-dogfood-readiness-summary.md
docs/working/status/baselines/internal-dogfood-readiness-report.json
```

## 最终判定

可以内部上线：

- CI 通过。
- internal dogfood gate 通过。
- API health 通过。
- 正式 launch gate 的 `HOLD` 仅由真实 evidence 不足导致。
- 已记录 internal-only 口径。

必须 HOLD：

- CI 入口坏。
- API 无法启动或 healthz 不可用。
- 安全/泄密/doc sync/ops 硬阻断。
- 内部门禁无法输出清晰报告。
