# Docker Zero-to-Release Runbook

## Verdict

本手册是裸 Linux 测试到上线的主流程：宿主机只需要 Docker Engine 与基础 shell 工具，不要求安装 Python；项目 Python 由 Docker 镜像提供。

## Scope

- 目标：从 Bare Linux 机器完成源码准备、测试镜像构建、模块化测试门禁、运行镜像构建、部署、验收、观测、回滚。
- 发布对象：`LC-L1-19` 外部 Beta 与后续同构发布。
- 运行入口：`Dockerfile` -> `python:3.11-slim` -> `python -m uvicorn apps.api.main:app --host 0.0.0.0 --port 8000`。
- 测试入口：`Dockerfile.test`，用于把 `tests/`、`scripts/`、`docs/` 放进 Python 3.11 测试容器。

## Host Assumptions

裸 Linux 宿主机只要求：

- Docker Engine 已安装，且当前用户执行 `docker ps` 不报权限错误。
- 可访问镜像源以拉取 `python:3.11-slim`，并可执行 `docker build`、`docker run --rm`、`docker run --rm -d`、`docker exec`、`docker logs`、`docker cp`、`docker rm -f`。
- 基础工具：`bash`、`curl`、`tar`。若没有 `git`，由发布机上传源码压缩包后解压。
- 如需完整 PostgreSQL 验证，准备 `OMNI_TEST_POSTGRES_DSN`；没有该 DSN 时只能做非 PostgreSQL 部分或得到 HOLD。

宿主机禁止假设：

- 不要求 `python`、`python3`、`pip`、`venv`。
- 不在宿主机安装 Python 包。
- 不把 `.env.runtime`、OpenAI key、API key 写进镜像层。

## Python Contract

- 项目声明：`pyproject.toml` 中 `requires-python = ">=3.11"`。
- 当前运行镜像：`Dockerfile` 使用 `python:3.11-slim`。
- 当前测试镜像：`Dockerfile.test` 也使用 `python:3.11-slim`。
- 魔尊确认的 Python 3.11 与项目要求一致；除非后续 `pyproject.toml` 提高版本，否则线上按 Python 3.11 执行。

在 Docker-only 场景中，下面命令里的 `python` 都是在容器内执行，不是宿主机 Python：

```bash
docker run --rm omni-skill-pipeline:test python --version
```

预期输出主版本为 `Python 3.11.x`。

## Source Bootstrap

方式 A：宿主机有 `git`。

```bash
git clone <repo-url> omni-skill-pipeline
cd omni-skill-pipeline
```

方式 B：宿主机没有 `git`，从构建机上传源码包。

```bash
tar -xzf omni-skill-pipeline.tar.gz
cd omni-skill-pipeline
```

源码目录必须包含：

- `Dockerfile`
- `Dockerfile.test`
- `Dockerfile.test.dockerignore`
- `pyproject.toml`
- `requirements-dev.txt`
- `src/`
- `apps/`
- `scripts/`
- `tests/`
- `docs/`

兼容说明：

- 根 `.dockerignore` 已显式 re-include `tests/`，用于兼容不支持 `Dockerfile.test.dockerignore` 的旧 Docker Engine。
- 运行镜像仍不会把 `tests/` 打进最终 image，因为 `Dockerfile` 没有 `COPY tests`；只是 build context 会包含测试目录。

## Image Build

先构建测试镜像，测试镜像包含 dev 依赖、测试脚本、测试用例和 Docker CLI：

```bash
docker build -f Dockerfile.test -t omni-skill-pipeline:test .
docker run --rm omni-skill-pipeline:test python --version
```

再构建运行镜像，运行镜像不包含 `tests/`，保持生产镜像收敛：

```bash
docker build -t omni-skill-pipeline:beta .
```

## Docker-Only Test Gate

### 1. 最小 CI 门禁

```bash
docker run --rm \
  -v "$PWD/docs/current/status/baselines:/app/docs/current/status/baselines" \
  omni-skill-pipeline:test \
  python scripts/run_ci.py --python python3 --keep-going --coverage-fail-under 50 --coverage-xml docs/current/status/baselines/coverage.xml
```

判定：

- 失败时不要只看最后一条错误，`--keep-going` 会继续执行后续模块并汇总失败模块。
- 产物优先看 `docs/current/status/baselines/coverage.xml` 与终端 summary。

### 2. 容器烟测

运行镜像健康检查不依赖宿主 Python：

```bash
docker rm -f omni-skill-pipeline-smoke 2>/dev/null || true
docker run --rm -d --name omni-skill-pipeline-smoke -p 18000:8000 omni-skill-pipeline:beta
curl -fsS http://127.0.0.1:18000/healthz
docker logs --tail 200 omni-skill-pipeline-smoke
docker rm -f omni-skill-pipeline-smoke
```

判定：

- `curl` 返回非 0 或 healthz 不是 ready/degraded JSON，禁止上线。
- 日志出现连续 5xx、import error、配置缺失，禁止上线。

### 3. 分模块 Linux 验证

需要让测试容器内的脚本调用宿主 Docker 时，挂载 Docker socket，并在 Linux 上使用 `--network host`，否则测试容器内访问 `127.0.0.1:18000` 时看不到宿主 Docker 暴露的烟测端口：

```bash
docker run --rm --network host \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v "$PWD/docs/current/status/baselines:/app/docs/current/status/baselines" \
  -e OMNI_TEST_POSTGRES_DSN="$OMNI_TEST_POSTGRES_DSN" \
  omni-skill-pipeline:test \
  python scripts/run_linux_validation_suite.py --python python3 --keep-going --container-image-tag omni-skill-pipeline:beta
```

如果只想先定位某几个模块，使用 `--stages` 缩小范围：

```bash
docker run --rm --network host \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v "$PWD/docs/current/status/baselines:/app/docs/current/status/baselines" \
  omni-skill-pipeline:test \
  python scripts/run_linux_validation_suite.py --python python3 --keep-going --stages ci doc_sync quality_regression container_smoke
```

模块规例：

| Stage | 目的 | 失败影响 |
| --- | --- | --- |
| `ci` | 单元/合同/覆盖率基础门禁 | 记录失败模块，继续后续 stage |
| `container_smoke` | 构建运行镜像并探测 `/healthz` | 验证容器启动链路 |
| `doc_sync` | 文档与 CLI/API/worker/testing 合同同步 | 防止上线文档漂移 |
| `quality_regression` | 质量回归证据 | 标记质量退化点 |
| `perf_cost_baseline` | 性能/成本基线 | 标记性能退化点 |
| `postgres_soak` / `postgres_ga` | PostgreSQL 长稳与 GA 验证 | 缺 DSN 时不能判 GO |
| `worker_ga` / `review_queue_ga` / `provider_ga` | Worker、review queue、provider 验证 | 定位服务面问题 |
| `calibration_ga` | 校准阈值验证 | 定位质量阈值偏移 |
| `roadmap_extension` | 路线图扩展验证 | 定位发布范围漂移 |

### 4. Release Switch 总闸

总闸同样在测试容器内执行：

```bash
docker run --rm --network host \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v "$PWD/docs/current/status/baselines:/app/docs/current/status/baselines" \
  -e OMNI_TEST_POSTGRES_DSN="$OMNI_TEST_POSTGRES_DSN" \
  omni-skill-pipeline:test \
  python scripts/run_release_switch_validation.py --python python3 --keep-going --container-image-tag omni-skill-pipeline:beta
```

判定：

- `GO`：允许进入 Deploy。
- `HOLD`：不能上线；根据汇总的 failed stage 和 evidence 文件定位。
- 单个案例失败不会遮蔽整体结果，因为 `--keep-going` 会继续跑完可执行 stage。

需要保留容器内证据时，用非 `--rm` 容器复制：

```bash
docker run --name omni-release-gate --network host \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e OMNI_TEST_POSTGRES_DSN="$OMNI_TEST_POSTGRES_DSN" \
  omni-skill-pipeline:test \
  python scripts/run_release_switch_validation.py --python python3 --keep-going --container-image-tag omni-skill-pipeline:beta
docker cp omni-release-gate:/app/docs/current/status/baselines ./baselines-from-container
docker rm -f omni-release-gate
```

## Release Decision

上线前必须同时满足：

- 测试镜像可构建，`python --version` 为 Python 3.11.x。
- 运行镜像 `docker build -t omni-skill-pipeline:beta .` 成功。
- `scripts/run_ci.py --python python3 --keep-going` 无阻断失败。
- `scripts/run_linux_validation_suite.py --python python3 --keep-going` 输出可归因的模块结果。
- `scripts/run_release_switch_validation.py --python python3 --keep-going` 给出 `GO`，或发布负责人明确接受 `HOLD` 风险但不得称为正式通过。
- `curl -fsS http://127.0.0.1:18000/healthz` 通过容器烟测。

## Deploy

准备运行环境文件，文件只留在宿主机：

```bash
cat > .env.runtime <<'EOF'
OPENAI_API_KEY=replace_me
OMNI_API_KEY=replace_me_if_auth_enabled
OMNI_LOG_FORMAT=json
OMNI_LOG_LEVEL=INFO
OMNI_TMP_MEDIA_ROOT=/app/.tmp_omni_media
EOF
chmod 600 .env.runtime
```

拉起 Beta：

```bash
docker rm -f omni-skill-beta 2>/dev/null || true
docker run --rm -d \
  --name omni-skill-beta \
  -p 8000:8000 \
  --env-file .env.runtime \
  -v omni_skill_drafts:/app/skills/drafts \
  -v omni_skill_published:/app/skills/published \
  -v omni_skill_tmp_media:/app/.tmp_omni_media \
  omni-skill-pipeline:beta
```

确认容器内 Python 与服务状态：

```bash
docker exec omni-skill-beta python --version
curl -fsS http://127.0.0.1:8000/healthz
```

## Acceptance

最小验收：

```bash
curl -fsS http://127.0.0.1:8000/healthz
curl -fsS http://127.0.0.1:8000/v1/templates/skill
```

开启 `OMNI_API_KEY` 时验证鉴权：

```bash
curl -i http://127.0.0.1:8000/v1/templates/skill
curl -i -H "X-API-Key: wrong" http://127.0.0.1:8000/v1/templates/skill
curl -fsS -H "X-API-Key: $OMNI_API_KEY" http://127.0.0.1:8000/v1/templates/skill
```

判定：

- `/healthz` 必须可访问。
- 鉴权开启时，无 key 与错 key 必须失败，正确 key 必须成功。
- distill happy path 样例按 `docs/current/operations/api.md` 分 text/audio/image/tabular/video 执行。

## Observability

日志巡检：

```bash
docker logs --tail 300 omni-skill-beta
docker logs omni-skill-beta | grep -E '"event":"(api_request_completed|distill_start|distill_complete)"'
docker logs omni-skill-beta | grep -E '"status_code":(4|5)[0-9]{2}'
```

临时目录与卷巡检：

```bash
docker exec omni-skill-beta sh -lc 'du -sh /app/.tmp_omni_media /app/skills/drafts /app/skills/published 2>/dev/null || true'
```

清理动作仍在容器内执行：

```bash
docker run --rm --volumes-from omni-skill-beta omni-skill-pipeline:test python scripts/prune_tmp_media.py --dry-run
docker run --rm --volumes-from omni-skill-beta omni-skill-pipeline:test python scripts/prune_tmp_media.py --retention-hours 24
```

## Rollback

触发条件：

- `/healthz` 持续异常。
- 核心 API 5xx 连续出现且 10 分钟内不能止血。
- 鉴权、限流、数据写回、review queue 行为偏离合同。
- Release Switch 证据被证明不完整或误判。

回滚：

```bash
docker logs --tail 300 omni-skill-beta > rollback-omni-skill-beta.log
docker rm -f omni-skill-beta
docker run --rm -d \
  --name omni-skill-beta \
  -p 8000:8000 \
  --env-file .env.runtime \
  -v omni_skill_drafts:/app/skills/drafts \
  -v omni_skill_published:/app/skills/published \
  -v omni_skill_tmp_media:/app/.tmp_omni_media \
  omni-skill-pipeline:stable
curl -fsS http://127.0.0.1:8000/healthz
```

## From Zero Checklist

1. 拿到源码：`git clone` 或 `tar -xzf`。
2. 确认宿主 Docker：`docker ps`。
3. 构建测试镜像：`docker build -f Dockerfile.test -t omni-skill-pipeline:test .`。
4. 确认容器 Python 版本：`docker run --rm omni-skill-pipeline:test python --version`。
5. 构建运行镜像：`docker build -t omni-skill-pipeline:beta .`。
6. 执行最小 CI：`docker run --rm omni-skill-pipeline:test python scripts/run_ci.py --python python3 --keep-going --coverage-fail-under 50`。
7. 执行容器烟测：`docker run --rm -d --name omni-skill-pipeline-smoke -p 18000:8000 omni-skill-pipeline:beta` 后 `curl -fsS http://127.0.0.1:18000/healthz`。
8. 执行分模块 Linux 验证：`docker run --rm --network host -v /var/run/docker.sock:/var/run/docker.sock omni-skill-pipeline:test python scripts/run_linux_validation_suite.py --python python3 --keep-going --container-image-tag omni-skill-pipeline:beta`。
9. 执行 Release Switch 总闸：`docker run --rm --network host -v /var/run/docker.sock:/var/run/docker.sock omni-skill-pipeline:test python scripts/run_release_switch_validation.py --python python3 --keep-going --container-image-tag omni-skill-pipeline:beta`。
10. 结果为 `GO` 后写 `.env.runtime`，启动 `omni-skill-beta`。
11. 执行 `/healthz`、template、鉴权、核心 distill happy path 验收。
12. 巡检 `docker logs`，异常则 `docker rm -f omni-skill-beta` 并回滚到 `omni-skill-pipeline:stable`。
