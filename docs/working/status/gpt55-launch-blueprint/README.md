# GPT5.5 上线施工包

本目录是 2026-06-20 诊断后的后续施工入口，服务于 GPT5.5 或人类工程师继续推进上线。所有任务必须回到主蓝图：[GPT5.5 后续迭代蓝图](../2026-06-20-gpt55-iteration-blueprint.md)。

## 施工顺序

| 顺序 | 文档 | 目标 |
| --- | --- | --- |
| 1 | [P0 真实业务闭环证据施工方案](p0-real-loop-evidence.md) | 解决 launch gate 的最大阻塞，补齐 10 条真实闭环和 4 个模态 |
| 2 | [P1 Agent Smoke 与 Reviewer Ops 施工方案](p1-agent-reviewer-quality.md) | 让真实闭环具备 agent 使用证据和 reviewer 质量证据 |
| 3 | [P1 Runtime 与生产链路施工方案](p1-runtime-production-readiness.md) | 修复 Docker/container smoke，补强生产上线链路 |
| 4 | [P2 文档索引与检索扩展施工方案](p2-doc-index-and-retrieval.md) | 清理文档路径漂移，约束 pgvector/Qdrant 扩展边界 |
| 5 | [GPT5.5 交接提示词](gpt55-handoff-prompt.md) | 让后续模型按同一主线接手施工 |

## 当前不能跨过的事实

- 当前内部 dogfood 可用，但外部 Beta/GA 仍被真实证据门禁阻塞。
- 当前真实 launch-gate-eligible loops 是 `0/10`。
- 当前真实 launch-gate-eligible modalities 是 `0/4`。
- 当前 Docker smoke 失败点是 base image metadata 拉取或构建，不是应用 health endpoint 本身。
- 当前 pgvector/Qdrant 不在 P0 上线主路径内。

## 全局执行规则

1. `docs/working/status/*.md` 和本目录文档是施工主线。
2. 只做文档列出的能力。若发现必须新增文档外能力，先写原因并等待确认。
3. 不允许把模拟、fixture、template、placeholder、未审核产物计入真实 launch gate。
4. 每次阶段收尾必须写明剩余 blocker 数量和一句话改动概括。
5. 发布说明只允许展示已经由命令或人工审核证据支撑的能力。

## 全局验收命令

```powershell
python scripts\doc_sync.py --output -
python scripts\trial_metrics.py --manifest docs\working\status\baselines\real-trial-loop-collection\real-trial-loop-metrics-manifest.json --print-summary --fail-on-ga-blocker
python scripts\launch_gate.py --output - --summary-output - --max-evidence-age-hours 0 --print-json
```

如果运行环境没有可写临时目录，先修复运行环境再验收，不得用失败环境的结果覆盖项目状态。
