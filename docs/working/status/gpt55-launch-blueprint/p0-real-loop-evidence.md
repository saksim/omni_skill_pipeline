# P0 真实业务闭环证据施工方案

## 目标

把 launch-gate-eligible real loops 从 `0/10` 补到至少 `10/10`，并覆盖至少 4 个真实模态。该目标是外部 Beta/GA 的最大阻塞项。

## 输入文档

- [项目能力与目标达成度评审 2026-06-20](../../../reviews/2026-06-20-project-capability-review.md)
- [Real Trial Loop Intake Workpack Summary](../baselines/real-trial-loop-collection/real-trial-loop-intake-workpack-summary.md)
- [Real Trial Loop Manifest Preflight Summary](../baselines/real-trial-loop-collection/real-trial-loop-manifest-preflight-summary.md)
- [真实数据接入与验收手册](../../../latest/operations/runbooks/real-data-intake-and-validation.md)
- [Real Trial Loop Collection Runbook](../../../latest/operations/runbooks/real-trial-loop-collection.md)

## 当前状态

| 指标 | 当前值 | 目标值 |
| --- | --- | --- |
| launch-gate-eligible real loops | `0` | `>=10` |
| launch-gate-eligible modalities | `0` | `>=4` |
| 缺失目标模态 | `text, audio, image, video` | `none` |
| 待填 manifest | `10` | `0` |

当前没有真实业务数据时，本施工包只能支持内部 dogfood 或内部玩具口径，不得声明外部 Beta/GA。后续拿到真实数据后，先按 [真实数据接入与验收手册](../../../latest/operations/runbooks/real-data-intake-and-validation.md) 投递本地原始数据和脱敏 manifest，再执行本文的 GL-64、GL-13、trial metrics 与 launch gate 验收。

## Manifest 槽位

| 槽位 | 目标模态 | 文件 |
| --- | --- | --- |
| 001 | text | `docs/working/status/baselines/real-trial-loop-collection/manifests/real-loop-001-text.json` |
| 002 | audio | `docs/working/status/baselines/real-trial-loop-collection/manifests/real-loop-002-audio.json` |
| 003 | image | `docs/working/status/baselines/real-trial-loop-collection/manifests/real-loop-003-image.json` |
| 004 | video | `docs/working/status/baselines/real-trial-loop-collection/manifests/real-loop-004-video.json` |
| 005 | text | `docs/working/status/baselines/real-trial-loop-collection/manifests/real-loop-005-text.json` |
| 006 | audio | `docs/working/status/baselines/real-trial-loop-collection/manifests/real-loop-006-audio.json` |
| 007 | image | `docs/working/status/baselines/real-trial-loop-collection/manifests/real-loop-007-image.json` |
| 008 | video | `docs/working/status/baselines/real-trial-loop-collection/manifests/real-loop-008-video.json` |
| 009 | text | `docs/working/status/baselines/real-trial-loop-collection/manifests/real-loop-009-text.json` |
| 010 | audio | `docs/working/status/baselines/real-trial-loop-collection/manifests/real-loop-010-audio.json` |

## 单条 loop 必填字段

每个 manifest 必须是 JSON object，且包含顶层 `loops` 数组。每条进入 launch gate 的 loop 必须满足：

每个 GL-63 槽位 manifest 只能包含一个本槽位 loop。不得在 `real-loop-001-text.json` 这类槽位文件中混入其它槽位、其它模态或多个合格 loop；GL-64 会将此类文件标记为 `invalid`，避免 GL-13 读取整个 manifest 时把污染行带入后续证据链。

| 字段 | 要求 |
| --- | --- |
| `loop_id` | 唯一，建议格式 `real-{modality}-slot-{nnn}` |
| `status` | 必须为 `complete` |
| `modality` | 必须与槽位一致 |
| `evidence_origin` | 必须为 `real` |
| `launch_gate_eligible` | 必须为 `true` |
| `source_system` | 真实来源系统，不允许 `TEMPLATE_REQUIRED` |
| `source_reference` | 可追溯工单、记录、会议或样本引用 |
| `collected_at_utc` | UTC 时间戳 |
| `review_task_id` | 人审任务 ID |
| `reviewed_by` | 审核人 |
| `reviewed_at_utc` | UTC 审核时间 |
| `review_outcome` | `approved`、`rejected` 或明确状态 |
| `revisions_before_approval` | 返修次数 |
| `reviewer_edit_distance_pct` | 审核编辑距离百分比 |
| `agent_smoke_result` | `passed`、`failed` 或 `not_run`，不得留空 |
| `backfill_slot_index` | 必须等于 GL-63 槽位编号 |
| `backfill_action_id` | 必须绑定 GL-63 intake item 或对应 GL-23 action |
| `published_without_review` | 外部发布前必须为 `false` |
| `critical_secret_or_pii_leak` | 必须为 `false` |
| `high_severity_incident` | 必须为 `false` |

## 合格样例

```json
{
  "manifest_id": "real-loop-001-text",
  "manifest_version": "1.0",
  "loops": [
    {
      "loop_id": "real-text-slot-001",
      "status": "complete",
      "modality": "text",
      "evidence_origin": "real",
      "launch_gate_eligible": true,
      "source_system": "pilot-ops",
      "source_reference": "ticket://INC-2001",
      "collected_at_utc": "2026-06-20T01:00:00Z",
      "review_task_id": "review-INC-2001",
      "reviewed_by": "reviewer-a",
      "reviewed_at_utc": "2026-06-20T01:30:00Z",
      "review_outcome": "approved",
      "revisions_before_approval": 1,
      "reviewer_edit_distance_pct": 18.0,
      "agent_smoke_result": "passed",
      "published_without_review": false,
      "critical_secret_or_pii_leak": false,
      "high_severity_incident": false,
      "latency_ms": 910.0,
      "provider_failure_count": 0,
      "provider_call_count": 2,
      "retry_count": 0,
      "artifact_count": 8,
      "estimated_cost_usd": 0.31,
      "backfill_slot_index": 1,
      "backfill_action_id": "gl23-slot-001-text"
    }
  ]
}
```

## 施工步骤

### 1. 冻结模板污染

先扫描待提交 manifest 是否仍有模板占位。

```powershell
rg -n "TEMPLATE_REQUIRED|placeholder|fixture|mock" docs\working\status\baselines\real-trial-loop-collection\manifests
```

只要命中真实 manifest，就停止 ingestion，回到证据采集。

### 2. 填充 10 个真实 manifest

使用 `docs/working/status/baselines/real-trial-loop-collection/real-trial-backfill-submission-manifest.template.json` 作为字段参考，但不能直接把 template 文件复制成真实证据。

每个槽位需要绑定：

- 真实输入或来源引用。
- 真实生成产物。
- 真实 review task。
- reviewer 结论。
- agent smoke 结果或明确未运行原因。
- GL-63 槽位编号和 GL-23/GL-63 intake action。

### 3. 执行 GL-64 结构预检

```powershell
python -B scripts\gl64_real_loop_manifest_preflight.py --fail-on-invalid --fail-on-pending
```

只接受 `REAL_LOOP_MANIFEST_PREFLIGHT_READY`。如果出现 missing 或 invalid，按报告逐项修正，不进入下一步。

GL-64 报告中需要重点阅读以下区块：

| 区块 | 用途 |
| --- | --- |
| `slot_readiness` | 汇总 10 个槽位的 ready、missing、invalid、blocked 数量，并列出缺失或非法 manifest 路径 |
| `modality_readiness` | 汇总 text、audio、image、video 的目标覆盖、已覆盖模态、缺失模态和各模态槽位数 |
| `operator_action_plan` | 输出下一步操作清单；`drop_real_manifest` 表示需要投递真实 manifest，`repair_real_manifest` 表示已有文件但字段或证据不合格 |

执行顺序必须是：

1. 先看 `operator_action_plan.next_actions`，按槽位逐个补充或修复真实 manifest。
2. 再看 `modality_readiness.missing_target_launch_modalities`，优先补齐仍为 `missing` 的目标模态。
3. 最后看 `slot_readiness.blocked_slot_count`，必须降为 `0` 才能进入 GL-13。

`operator_action_plan.next_commands.placeholder_scan` 会给出模板污染扫描命令；只要真实 manifest 命中 `TEMPLATE_REQUIRED`、`placeholder`、`fixture` 或 `mock`，必须先回到证据采集，不得进入 GL-13。

### 4. 执行 GL-13 evidence ingestion

```powershell
python -B scripts\gl13_launch_evidence.py --loop-manifest-dir docs\working\status\baselines\real-trial-loop-collection\manifests --strict-loop-manifest-contract --require-manifest-preflight-ready --max-evidence-age-hours 0
```

若环境临时目录不可写，先修复本地运行环境。不得将运行环境失败解释为项目已经通过。

`--require-manifest-preflight-ready` 会在 GL-13 摄入前自动运行 GL-64，并在任一槽位仍为 `missing` 或 `invalid` 时停止摄入。该开关不创建真实证据，只把“GL-64 READY 后才能进入 GL-13”的人工步骤固化为机器门禁。

GL-13 生成的 `real-trial-launch-evidence-pack.json` 会携带 GL-64 预检摘要字段：

- `evidence_classification.real_loop_manifest_preflight_status`
- `evidence_classification.real_loop_manifest_preflight_blocked_slot_count`
- `evidence_classification.real_loop_manifest_preflight_missing_target_launch_modalities`
- `evidence_classification.real_loop_manifest_preflight_operator_next_actions`

这些字段只用于 reviewer/operator 定位缺口，不改变 launch gate 结论。若 `real_loop_manifest_preflight_status` 不是 `REAL_LOOP_MANIFEST_PREFLIGHT_READY`，必须继续修 manifest，不得把 GL-13 产物解释为可上线。

### 5. 运行 trial metrics

```powershell
python scripts\trial_metrics.py --manifest docs\working\status\baselines\real-trial-loop-collection\real-trial-loop-metrics-manifest.json --print-summary --fail-on-ga-blocker
```

必须确认：

- complete loops `>=10`。
- launch-gate eligible loops `>=10`。
- modalities `>=4`。
- source trace missing `0`。
- review trace missing `0`。
- placeholder field count `0`。

### 6. 运行 launch gate

```powershell
python scripts\launch_gate.py --output - --summary-output - --max-evidence-age-hours 0 --print-json
```

如果仍为 `HOLD`，只允许基于 blocker 列表继续修证据，不允许修改阈值绕过。

## 完成定义

- 10 个槽位都有真实 manifest。
- GL-64 预检通过。
- GL-13 生成新的 launch evidence pack。
- `trial_loop_volume_and_modality_coverage` 不再出现为 blocker。
- 所有真实证据都有 source trace 和 review trace。
