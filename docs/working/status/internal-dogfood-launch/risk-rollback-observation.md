# Risk, Rollback, and Observation

## 目标

定义内部 dogfood 上线的风险、观察窗口和回滚条件。

## 风险矩阵

| 风险 | 等级 | 触发条件 | 处理 |
| --- | --- | --- | --- |
| 将内部上线误称为外部 Beta | P0 | 文档或状态输出使用 external beta/GA 口径 | 立即修正文档和状态输出 |
| CI 仍失败 | P0 | `scripts/ci.py` 非零退出 | 阻塞内部上线 |
| API health 不可用 | P0 | `/healthz` 非 200 或无法连接 | 阻塞内部上线 |
| 生成 artifact 被误发布 | P0 | 未 review artifact 被标为可发布 | 回滚并修 review 默认值 |
| provider 不可用 | P1 | OpenAI 或上游 provider 失败 | 可降级为 heuristic / fixture 内部演示 |
| Docker 不可用 | P1 | 当前环境无 Docker | 先走本地 API，上 Linux host 补跑 |
| 文档路径漂移 | P1 | doc sync 指向旧 `docs/current/` | 修 doc sync 或 baseline |
| coverage 低于门槛 | P1/P0 | 低于 50 | 若 CI 阻断则 P0，否则补测试 |

## 回滚条件

命中任一条件必须回滚或暂停：

- `/healthz` 持续不可用。
- CI 入口再次失效。
- 生成结果出现未审核发布。
- 内部用户无法完成最小 CLI/API 使用。
- 日志出现持续 5xx 或 runtime error。
- 文档或状态误导为外部 Beta / GA。

## 回滚步骤

### 本地 API

1. 停止 `uvicorn` 进程。
2. 记录失败命令和日志。
3. 回到上一 commit 或上一稳定分支。

### Docker

```powershell
docker logs --tail 300 omni-skill-dogfood
docker rm -f omni-skill-dogfood
```

如有上一稳定镜像：

```powershell
docker run --rm -d --name omni-skill-dogfood -p 18000:8000 omni-skill-pipeline:stable
```

### Git

只回滚本轮改动：

```powershell
git restore .github/workflows/ci.yml
git restore scripts/internal_launch_gate.py
git restore tests/test_internal_launch_gate.py
```

如果文件已提交，使用 `git revert <commit>`，不要使用 `git reset --hard`。

## 观察窗口

### T+15 分钟

检查：

- `/healthz`
- API 是否有 5xx
- CLI smoke 是否可用

### T+2 小时

检查：

- artifact 数量是否异常增长
- `.tmp_omni_media/` 是否异常增长
- provider failure 是否集中
- review queue 是否积压

### T+24 小时

检查：

- 内部用户是否完成至少一次手动使用
- 是否有无法恢复的错误
- 是否需要继续 dogfood、回滚、或推进真实 loop 收集

## 观察命令

API：

```powershell
curl http://127.0.0.1:8000/healthz
```

Docker：

```powershell
docker logs --tail 300 omni-skill-dogfood
```

临时目录：

```powershell
python scripts\prune_tmp.py --dry-run
```

正式 launch gate 复核：

```powershell
python scripts\launch_gate.py --output - --summary-output - --max-evidence-age-hours 0 --print-json
```

内部 gate 复核：

```powershell
python scripts\internal_launch_gate.py --output - --summary-output - --print-json
```

## 事故记录模板

```text
incident_id:
detected_at:
detected_by:
impact:
trigger:
logs:
rollback_required:
rollback_completed_at:
root_cause:
follow_up:
owner:
```

## 降级策略

如果 provider 不可用：

- 保留 API 和 CLI。
- 暂停真实 provider 调用。
- 使用 fixture/heuristic 做内部演示。
- 明确标注输出不能作为真实业务结果。

如果 Docker 不可用：

- 改用本地 `uvicorn`。
- 将 Docker smoke 标记为 `not_run`。
- 在 Linux host 补跑。

如果正式 launch gate 继续 `HOLD`：

- 不处理为内部上线 blocker。
- 在 release note 中标注外部上线仍不可用。
- 保持真实 loop 收集为后续 P2。
