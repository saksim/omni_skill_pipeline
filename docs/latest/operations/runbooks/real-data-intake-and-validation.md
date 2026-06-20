# 真实数据接入与验收手册

本手册定义后续拿到真实业务数据后，应该如何把数据交给项目、放到哪里、如何生成可验证 manifest，以及如何跑完上线前验收。

当前仓库没有真实业务数据，所以当前版本只能声明为内部 dogfood 或内部玩具，不声明外部 Beta、GA、SaaS 或生产可用。

## 接入结论

- 真实原始数据放在本地未入库目录：`data/real-inputs/<batch-id>/`。
- 仓库只提交脱敏后的真实闭环 manifest：`docs/working/status/baselines/real-trial-loop-collection/manifests/`。
- 每个 GL-63 槽位只能有一个 manifest 文件，每个文件只能包含该槽位的一条合格 loop。
- 没有真实 source trace、review trace 和 agent smoke 记录时，不允许设置 `launch_gate_eligible=true`。
- `fixture`、`mock`、`template`、`placeholder`、未审核产物和人工未确认结果永远不能伪装成真实上线证据。

## 数据怎么给项目

推荐由操作者交付一个真实数据批次目录，目录名使用日期和批次号：

```text
data/real-inputs/2026-06-20-batch-001/
```

目录内建议按槽位或模态分组：

```text
data/real-inputs/2026-06-20-batch-001/
  slot-001-text/
  slot-002-audio/
  slot-003-image/
  slot-004-video/
  reviewer-notes/
  source-references.md
```

`data/real-inputs/` 已加入 `.gitignore`。该目录只用于本地或受控环境运行，不进入仓库，不进入 release 包。

## 仓库里应该提交什么

提交到仓库的是脱敏后的 manifest，而不是真实原件。目标路径固定为：

```text
docs/working/status/baselines/real-trial-loop-collection/manifests/
```

必须使用以下 10 个目标槽位文件名：

| 槽位 | 模态 | manifest 文件 |
| --- | --- | --- |
| 001 | text | `real-loop-001-text.json` |
| 002 | audio | `real-loop-002-audio.json` |
| 003 | image | `real-loop-003-image.json` |
| 004 | video | `real-loop-004-video.json` |
| 005 | text | `real-loop-005-text.json` |
| 006 | audio | `real-loop-006-audio.json` |
| 007 | image | `real-loop-007-image.json` |
| 008 | video | `real-loop-008-video.json` |
| 009 | text | `real-loop-009-text.json` |
| 010 | audio | `real-loop-010-audio.json` |

每个 manifest 是 JSON object，顶层必须包含 `loops` 数组，且数组只能有一个元素。

## 单条 loop 最小字段

每条可进入上线门禁的 loop 至少需要这些字段：

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
      "backfill_slot_index": 1,
      "backfill_action_id": "gl23-slot-001-text",
      "published_without_review": false,
      "critical_secret_or_pii_leak": false,
      "high_severity_incident": false
    }
  ]
}
```

真实原件路径、本机绝对路径、客户姓名、账号、凭证、token、生产 URL 和未脱敏 PII 不应写入 manifest。需要追溯时写入可审计引用，例如工单号、受控存储对象 ID、内部审阅记录 ID 或脱敏样本编号。

## 接入前检查

确认原始数据不包含禁止内容：

- 生产凭证、token、cookie、私钥。
- 受监管的医疗、支付、法务、HR 或高度敏感客户资料。
- 未经授权的客户 PII。
- 未经审核就要发布的产物。

确认每条 loop 有三类证据：

- 来源证据：`source_system`、`source_reference`、`collected_at_utc`。
- 审核证据：`review_task_id`、`reviewed_by`、`reviewed_at_utc`、`review_outcome`。
- agent 证据：`agent_smoke_result`，或者明确的失败记录和失败原因。

## 验收命令

先扫描模板污染：

```powershell
rg -n "TEMPLATE_REQUIRED|placeholder|fixture|mock" docs\working\status\baselines\real-trial-loop-collection\manifests
```

再跑 GL-64 manifest 预检：

```powershell
python -B scripts\gl64_real_loop_manifest_preflight.py --fail-on-invalid --fail-on-pending
```

只有输出状态为 `REAL_LOOP_MANIFEST_PREFLIGHT_READY`，才允许继续 GL-13：

```powershell
python -B scripts\gl13_launch_evidence.py --loop-manifest-dir docs\working\status\baselines\real-trial-loop-collection\manifests --strict-loop-manifest-contract --require-manifest-preflight-ready --max-evidence-age-hours 0
```

生成 trial metrics：

```powershell
python scripts\trial_metrics.py --manifest docs\working\status\baselines\real-trial-loop-collection\real-trial-loop-metrics-manifest.json --print-summary --fail-on-ga-blocker
```

最后跑 launch gate：

```powershell
python scripts\launch_gate.py --output - --summary-output - --max-evidence-age-hours 0 --print-json
```

文档同步检查：

```powershell
python scripts\doc_sync.py --output -
```

## 通过标准

真实数据接入完成后，至少满足：

- 10 个目标槽位 manifest 全部存在。
- GL-64 状态为 `REAL_LOOP_MANIFEST_PREFLIGHT_READY`。
- launch-gate-eligible complete real loops `>=10`。
- launch-gate-eligible modalities 覆盖 `text, audio, image, video`。
- source trace missing 为 `0`。
- review trace missing 为 `0`。
- placeholder field count 为 `0`。
- `critical_secret_or_pii_leak` 为 `0`。

如果 `launch_gate.py` 仍返回 `HOLD`，只能按 blocker 继续修证据，不能放宽阈值或改写 release note 口径。

## 当前无真实数据时的口径

如果没有真实业务数据，本项目可以继续完成内部 dogfood、文档、打包、加密、本地 API smoke、agent smoke 协议和 release 机制，但必须保留以下边界：

- 不声明外部 Beta。
- 不声明 GA。
- 不声明 SaaS 或生产部署 ready。
- 不把空 manifest、模板 manifest 或模拟结果计入真实闭环。
- Release Note 必须明确当前 blocker 是真实业务闭环证据不足，而不是代码门禁已经全部完成。
