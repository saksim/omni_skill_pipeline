# 内部玩具上线施工计划

> 日期：2026-06-18
> 状态：working
> 目标：将项目从“等待真实外部试运行证据”降级为“内部 dogfood / 内部玩具上线”，先完成可运行、可验证、可回滚的内部上线闭环。

## 一句话结论

本轮不追求外部 Beta、GA 或 SaaS，就按 **Internal Dogfood Launch** 推进：修掉 workflow 硬失败，新增内部上线门禁，跑通本地/API/容器最小验收，并把正式 `launch_gate.py` 的 `HOLD` 保留为外部上线阻断。

## 依据

- [项目卡点评估（2026-06-18）](2026-06-18-project-blocker-assessment.md)
- [Broad Product Launch Plan](2026-05-25-broad-product-launch-plan.md)
- [Current Status](CURRENT_STATUS.md)
- [API](../../latest/operations/api.md)
- [Launch Beta Runbook](../../latest/operations/runbooks/launch-beta.md)

## 项目上下文卡

| 项 | 当前事实 |
| --- | --- |
| 产品目标 | Agent Skill Compiler 内部 dogfood，不宣称外部 Beta |
| 当前正式 launch gate | `scripts/launch_gate.py` 仍为 `HOLD`，主因是真实 launch-gate-eligible loop 不足 |
| 用户约束 | 当前拿不到真实业务结果，接受降级为内部玩具 |
| 已知 workflow fail | `.github/workflows/ci.yml` 调用 `scripts/run_ci.py`，仓库实际脚本是 `scripts/ci.py` |
| API 入口 | `python -m uvicorn apps.api.main:app --reload` |
| 健康检查 | `GET /healthz` |
| 文档层 | 本计划属于 `docs/working/status/` |

## 范围锁定

### 本轮只做

- 明确定义内部上线口径和内部门禁。
- 修复 workflow 中确定的硬失败。
- 建立内部 dogfood 的最小验收链路。
- 记录上线、观察、回滚和失败处理流程。

### 本轮不做

- 不把 `scripts/launch_gate.py` 改成对外上线放行。
- 不伪造真实业务 loop。
- 不承诺外部 Beta、GA 或 SaaS。
- 不新增复杂 UI、租户平台化、Qdrant 或分布式 worker。
- 不降低正式 release switch / launch gate 的安全语义。

## 门禁分层

| Gate | 用途 | 允许 fixture/simulated evidence | 阻塞内部上线 | 阻塞外部上线 |
| --- | --- | --- | --- | --- |
| `release_switch.py` | 工程发布证据 | 视脚本规则而定 | 是 | 是 |
| `launch_gate.py` | 外部 Beta/GA readiness | 否 | 否 | 是 |
| `internal_launch_gate.py` | 内部 dogfood readiness | 是，但必须标注 | 是 | 否 |

核心原则：

> `launch_gate.py` 的 `HOLD` 不再阻塞内部玩具上线，但必须在所有文档和输出中保留为“外部上线不可用”的事实。

## 主从技能编排

| 角色 | 职责 |
| --- | --- |
| 主责：top-engineering-orchestrator | 拆分阶段、锁定范围、组织 Patch Contract 和验收闭环 |
| 从责：top-product-strategist | 定义内部上线、非目标、验收场景 |
| 从责：top-qa | 定义测试矩阵、质量门禁、回滚条件 |
| 从责：devops | 修 workflow、CI、artifact 上传和运行脚本 |
| 从责：top-architect | 仅在新增内部门禁脚本边界时介入 |

## 施工阶段

### S0：冻结口径与工作树

目标：确保施工从干净状态开始。

步骤：

1. 执行 `git status --short`。
2. 若存在未提交改动，判断是否属于本轮施工。
3. 本轮改动必须只触碰：
   - `.github/workflows/ci.yml`
   - `scripts/internal_launch_gate.py`
   - `tests/test_internal_launch_gate.py`
   - `docs/working/status/internal-dogfood-launch/*`
   - 必要索引文档
4. 如果发现其他文件被改动，先暂停并确认来源。

验收：

- 没有未解释的脏改动。
- 当前分支清楚。

### S1：修复 P0 workflow 硬失败

目标：让 GitHub Actions 至少能找到正确 CI 脚本。

已知问题：

```yaml
run: python scripts/run_ci.py --coverage-fail-under 50 --coverage-xml coverage.xml
```

仓库实际存在：

```text
scripts/ci.py
```

推荐修复：

```yaml
run: python scripts/ci.py --coverage-fail-under 50 --coverage-xml coverage.xml
```

细则：[P0 Workflow Fail Remediation](internal-dogfood-launch/p0-workflow-fail-remediation.md)

验收：

- `.github/workflows/ci.yml` 不再引用不存在的 `scripts/run_ci.py`。
- 本地可执行 `python scripts/ci.py --coverage-fail-under 50 --coverage-xml coverage.xml`。

### S2：建立本地 CI 基线

目标：拿到当前 fail 清单，不先猜测。

步骤：

1. 安装依赖：
   ```powershell
   python -m pip install --upgrade pip
   python -m pip install -r requirements-dev.txt
   ```
2. 执行：
   ```powershell
   python scripts\ci.py --coverage-fail-under 50 --coverage-xml coverage.xml --keep-going
   ```
3. 将失败分成四类：
   - 脚本/路径失败
   - 依赖/环境失败
   - 测试断言失败
   - coverage 门槛失败
4. 只把“阻塞内部上线”的失败列入 P0。

验收：

- 有一份明确 fail 清单。
- 每个 fail 有归类、owner、修复方式、回归命令。

### S3：新增内部 dogfood gate

目标：建立不污染正式 launch gate 的内部上线判定。

推荐新增：

```text
scripts/internal_launch_gate.py
tests/test_internal_launch_gate.py
docs/working/status/baselines/internal-dogfood-readiness-report.json
docs/working/status/baselines/internal-dogfood-readiness-summary.md
```

决策值：

- `READY_FOR_INTERNAL_DOGFOOD`
- `HOLD`

最低放行条件：

- CI 通过或仅存在已豁免的非阻塞项。
- `launch_gate.py` 的失败原因只来自真实 loop 覆盖不足。
- `GET /healthz` 可返回 ready 或可接受的内部 degraded 说明。
- 至少一个 CLI 或 API happy path 可完成。
- 所有输出标注 `internal_dogfood_only=true` 或等价语义。

细则：[Internal Dogfood Gate Spec](internal-dogfood-launch/internal-dogfood-gate-spec.md)

验收：

```powershell
python scripts\internal_launch_gate.py --output - --summary-output - --print-json
```

输出 `READY_FOR_INTERNAL_DOGFOOD` 或带明确 blocker 的 `HOLD`。

### S4：内部上线最小运行链路

目标：让内部用户能访问 API 或本地 CLI。

本地 API：

```powershell
python -m uvicorn apps.api.main:app --reload
```

探活：

```powershell
curl http://127.0.0.1:8000/healthz
```

Docker 可选：

```powershell
python scripts\container_smoke.py --dry-run
python scripts\container_smoke.py --image-tag omni-skill-pipeline:dogfood --port 18000
```

细则：[Verification Runbook](internal-dogfood-launch/verification-runbook.md)

验收：

- `/healthz` 可访问。
- `GET /v1/templates/skill` 可访问。
- 至少一个 `distill/text` 或 CLI 示例成功。
- 失败时可按回滚文档处理。

### S5：上线记录与风险告知

目标：让内部玩具上线有可追踪记录。

新增或更新：

```text
docs/working/status/internal-dogfood-launch/launch-record-template.md
docs/working/status/baselines/internal-dogfood-readiness-report.json
docs/working/status/baselines/internal-dogfood-readiness-summary.md
```

必须记录：

- `release_id`
- commit SHA
- operator
- CI 结果
- internal gate 结果
- API health 结果
- 已知风险
- 是否回滚

细则：[Risk, Rollback, and Observation](internal-dogfood-launch/risk-rollback-observation.md)

### S6：workflow fail 逐项清理

目标：把“各种 fail”变成可关闭的施工队列。

处理顺序：

1. 先修路径和脚本名漂移。
2. 再修依赖安装和 import。
3. 再修确定性测试失败。
4. 最后处理 coverage 或慢测。

禁止：

- 不得为了过 CI 直接降低 coverage floor。
- 不得把外部 launch gate 的 `HOLD` 改成 `GO`。
- 不得把真实 loop 条件改成 fixture 可替代。

### S7：内部上线后观察

观察窗口：

- 立即：上线后 15 分钟。
- 短窗：上线后 2 小时。
- 次日：上线后 24 小时。

观察项：

- `/healthz`
- API 4xx/5xx 分布
- provider failure
- 临时目录增长
- 生成 artifact 数量
- reviewer queue 积压
- 人工使用反馈

## P0/P1/P2 拆分

### P0：上线前必须完成

| 任务 | 文件 | 验收 |
| --- | --- | --- |
| 修 CI 脚本路径 | `.github/workflows/ci.yml` | 不再引用 `scripts/run_ci.py` |
| 建内部 gate 规格 | `scripts/internal_launch_gate.py`、测试、文档 | 可输出内部上线决策 |
| 跑通 CI 基线 | `scripts/ci.py` | 有通过结果或明确 P0 fail |
| 跑通 API health | `apps/api/main.py` 运行面 | `/healthz` 可访问 |
| 写上线记录 | working docs / baselines | 可追踪 release_id 和结果 |

### P1：上线后立即收敛

| 任务 | 文件 | 验收 |
| --- | --- | --- |
| Docker smoke 实跑 | `scripts/container_smoke.py` | 容器 healthz 成功 |
| doc sync 对齐新分层 | `scripts/doc_sync.py`、docs | 不再指向旧 `docs/current/` |
| CLI/API happy path 扩展 | tests / docs | text + template + review queue 基础可用 |
| fail 队列闭环 | issue 文档或施工记录 | 每个 fail 有状态 |

### P2：内部玩具稳定后再做

| 任务 | 文件 | 验收 |
| --- | --- | --- |
| 真实 loop 收集 | real-trial-loop docs | 逐步推动正式 launch gate |
| review feedback 校准 | quality docs / scripts | 形成真实 edit distance |
| 平台化准备 | tenant/cost/audit docs | 只在 dogfood 有价值后推进 |

## Patch Contract

本施工计划允许的后续代码改动：

- 修改 `.github/workflows/ci.yml`。
- 新增 `scripts/internal_launch_gate.py`。
- 新增 `tests/test_internal_launch_gate.py`。
- 新增内部上线 readiness baseline 输出。
- 更新 `docs/INDEX.md` 与 working 文档。

本施工计划禁止的后续代码改动：

- 不改低 `scripts/launch_gate.py` 的真实 loop 要求。
- 不删除 release switch 安全门禁。
- 不删除 review 强制语义。
- 不把 fixture 标记为真实 evidence。

## 验收闭环

建议最终验收命令：

```powershell
git status --short
python scripts\ci.py --coverage-fail-under 50 --coverage-xml coverage.xml
python scripts\launch_gate.py --output - --summary-output - --max-evidence-age-hours 0 --print-json
python scripts\internal_launch_gate.py --output - --summary-output - --print-json
python -m uvicorn apps.api.main:app --reload
curl http://127.0.0.1:8000/healthz
```

判定：

- `ci.py` 必须通过。
- `launch_gate.py` 可以 `HOLD`，但 blocker 必须解释为外部真实证据不足。
- `internal_launch_gate.py` 必须 `READY_FOR_INTERNAL_DOGFOOD`。
- API health 必须可访问。

## 下轮 Handoff

下一轮可以直接进入 P0 施工：

1. 修 `.github/workflows/ci.yml`。
2. 跑 `python scripts\ci.py --coverage-fail-under 50 --coverage-xml coverage.xml --keep-going`。
3. 按失败分类修 P0。
4. 新增 `scripts/internal_launch_gate.py`。
5. 生成内部上线 readiness baseline。
