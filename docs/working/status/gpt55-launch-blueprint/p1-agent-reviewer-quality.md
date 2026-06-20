# P1 Agent Smoke 与 Reviewer Ops 施工方案

## 目标

补齐真实 agent 使用证据和真实 reviewer 操作数据，避免项目只达到数量门槛，却没有质量闭环。

## 输入文档

- [Agent Smoke Protocol](../../../latest/operations/runbooks/agent-smoke-protocol.md)
- [Controlled Trial Metrics Summary](../baselines/controlled-trial/trial-metrics-summary.md)
- [Real Trial Loop Collection Runbook](../../../latest/operations/runbooks/real-trial-loop-collection.md)

## 当前判断

当前 fixture 闭环里的 reviewer 指标和 agent smoke 指标表面上通过，但这些不等价于真实 Beta 证据。后续必须把相同字段迁移到 `evidence_origin=real` 的闭环上。

## Agent smoke 施工

### 覆盖范围

每个进入真实 launch gate 的 skill 包，至少记录：

- Codex smoke。
- Claude Code smoke。
- OpenCode smoke。

如果某个 agent 暂时不可用，必须记录 `status=not_run` 和明确原因。不能静默缺失。

### 执行命令模板

```powershell
python scripts\agent_smoke.py `
  --skill-id real-text-slot-001 `
  --agent codex `
  --status agent_smoke_passed `
  --reason "真实文本闭环可触发目标 skill" `
  --trigger-prompt "根据真实工单生成可执行 runbook" `
  --expected-skill-selection "database-slow-query-notes-to-review-skill" `
  --expected-task-output "生成审核后的 runbook" `
  --selected-skill "database-slow-query-notes-to-review-skill" `
  --observed-task-output "已生成并通过 reviewer 审核" `
  --print-json
```

失败样例也必须保留：

```powershell
python scripts\agent_smoke.py `
  --skill-id real-audio-slot-002 `
  --agent opencode `
  --status agent_smoke_failed `
  --reason "音频转写输入缺少时间戳，agent 未能稳定选择目标 skill" `
  --failure-code missing_audio_transcript_timestamp `
  --trigger-prompt "根据真实音频跟进记录生成复盘流程" `
  --expected-skill-selection "audio-follow-up-call-to-runbook-revision-skill" `
  --expected-task-output "生成可审核 runbook" `
  --selected-skill "audio-follow-up-call-to-runbook-revision-skill" `
  --observed-task-output "输出缺少可审核 runbook 的关键时间戳证据" `
  --print-json
```

若某个 agent 暂时不可用，不允许留空，应记录 `not_run`：

```powershell
python scripts\agent_smoke.py `
  --skill-id real-audio-slot-002 `
  --agent claude-code `
  --status not_run `
  --reason "Claude Code 环境本轮不可用，等待下一轮人工 smoke" `
  --trigger-prompt "根据真实音频跟进记录生成复盘流程" `
  --expected-skill-selection "audio-follow-up-call-to-runbook-revision-skill" `
  --expected-task-output "生成可审核 runbook" `
  --print-json
```

### 三端矩阵校验

记录完成后必须执行只读矩阵校验，确保每个真实 skill 包都有 Codex、Claude Code、OpenCode 三个格子的记录：

```powershell
python scripts\agent_smoke.py `
  --validate-matrix `
  --required-skill-id real-text-slot-001,real-audio-slot-002 `
  --fail-on-incomplete `
  --print-json
```

校验返回 `AGENT_SMOKE_MATRIX_READY` 才表示记录矩阵完整；如果返回 `AGENT_SMOKE_MATRIX_INCOMPLETE`，应先补缺失 agent 记录或补齐记录字段，再进入 launch gate 复核。

`launch_gate.py` 会复用同一套矩阵规则生成阻塞检查 `agent_smoke_matrix_coverage`。如果某个 skill 只记录了 Codex，但缺 Claude Code 或 OpenCode，launch gate 不能因为单格成功率为 100% 就放行。

`not_run` 的语义是“已明确记录不可运行原因”，不是成功。它可以补齐三端矩阵覆盖，但不会进入 `agent_smoke_success_rate` 的已执行记录分母；如果全部记录都是 `not_run`，上线门禁仍会失败。

### 质量门槛

- agent smoke success rate 不低于当前 launch gate 阈值。
- agent smoke matrix 必须覆盖所有真实 skill 包与 Codex、Claude Code、OpenCode 三端。
- `launch_gate.py` 中 `agent_smoke_matrix_coverage` 必须为 `pass`。
- `agent_smoke_success_rate` 至少需要 1 条实际执行过的 pass/fail 记录，`not_run` 只用于说明不可运行原因。
- 所有 failure code 必须可复现、可归类、可修复或被产品边界解释。
- 失败记录不得删除，只能补充修复后的新记录。

## Reviewer ops 施工

### 必填字段

每条真实 loop 必须有：

| 字段 | 要求 |
| --- | --- |
| `review_task_id` | 可追踪到审核任务 |
| `reviewed_by` | 可识别审核角色或人员 |
| `reviewed_at_utc` | UTC 时间 |
| `review_outcome` | approved、rejected 或 changes_requested |
| `revisions_before_approval` | 数字 |
| `reviewer_edit_distance_pct` | 数字 |
| `published_without_review` | 外部发布前必须为 `false` |

### 审核流程

1. reviewer 查看原始输入、生成 skill 包、reference、examples、risk note。
2. reviewer 给出 `approved`、`changes_requested` 或 `rejected`。
3. 如果返修，记录每一轮返修原因。
4. 最终通过时记录 revision count 和 edit distance。
5. 将 reviewer 字段写回 real loop manifest。

### 校准命令

```powershell
python scripts\tune_review.py --manifest docs\working\status\baselines\real-trial-loop-collection\real-trial-loop-metrics-manifest.json --print-json --fail-on-mismatch
```

若校准失败，不要先改阈值。先检查 reviewer 规则、样本分类、返修标准是否一致。

## Review queue 施工

如果真实审核开始形成排队压力，再启用 review queue 验证：

```powershell
python scripts\ga_review_queue.py --stage review_queue_repository --dry-run --print-json
python scripts\ga_review_queue.py --stage review_queue_service_flow --dry-run --print-json
python scripts\ga_review_queue.py --stage review_feedback --dry-run --print-json
```

只有 dry-run 通过后，才允许进入真实写入或 API 验证。

## 完成定义

- 所有 launch-gate-eligible real loops 都有 reviewer trace。
- 所有真实 skill 包都有 agent smoke 记录或明确不可运行原因。
- `trial_metrics.py --fail-on-ga-blocker` 不因 reviewer 或 agent 质量失败。
- `tune_review.py --fail-on-mismatch` 通过，或每个 mismatch 都有已登记修复计划。
