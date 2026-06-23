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

## 数据范式

不能只放一个 `source` 文件就算完成。每个槽位必须是一个本地 source bundle，用来证明“这个输入来自真实文件、项目实际处理过、结果有人审过、并且知道什么叫正确”。

每个槽位目录建议使用以下结构：

```text
data/real-inputs/<batch-id>/
  slot-001-text/
    source/
      source.pdf
    task.md
    expected.md
    review.md
    run-evidence.json
    quality-evidence.json
  slot-002-audio/
    source/
      source.mp3
    task.md
    expected.md
    review.md
    run-evidence.json
```

每个槽位的最小范式如下：

| 文件或目录 | 是否必须 | 作用 | 进入仓库 |
| --- | --- | --- | --- |
| `source/` | 是 | 原始输入文件，可以是 PDF、代码库压缩包、Markdown、音频、图片或视频 | 否 |
| `task.md` | 是 | 本槽位希望项目完成的业务任务，例如“从 PDF 提炼可复用技能” | 否 |
| `expected.md` | 是 | 业务上认为正确的内容、必须命中的要点、拒绝条件和评分口径 | 否 |
| `review.md` | 是 | 人工审阅记录，说明输出是否通过、改了几轮、主要问题是什么 | 否 |
| `run-evidence.json` | 是 | 本地运行证据，记录耗时、产物数量、provider 调用数、重试次数、成本估算 | 否 |
| `quality-evidence.json` | 是 | 多模态质量评分、人审结论、OCR/ASR 降级说明 | 可脱敏汇总后入库 |
| 脱敏 manifest | 是 | 仓库内可追溯、可验证的闭环记录 | 是 |

`source/` 里可以放多个文件，但一个 GL-63 槽位只能形成一个合格 loop。比如一个代码库压缩包可以包含多文件，但它仍然对应 `real-loop-005-text.json` 里的一条 `loops[0]`。

### `task.md` 最小内容

```markdown
# Task

- business_scenario: public-demo-skill-distillation
- input_modality: text
- requested_action: 从输入文件中提炼一个可复用的技能说明、关键约束和验证步骤。
- expected_artifact_type: SKILL.md draft + skill metadata summary
- operator_note: 使用公开或自有样本模拟真实业务，不包含客户隐私和生产凭证。
```

### `expected.md` 最小内容

```markdown
# Expected Outcome

- must_include:
  - 输入文件的核心主题。
  - 至少 3 条可执行步骤或规则。
  - 至少 1 条限制、风险或不适用场景。
- must_not_include:
  - 凭证、token、cookie、私钥、未脱敏个人信息。
  - 与源文件无关的臆造事实。
- pass_criteria:
  - 主要事实与源文件一致。
  - 人工审阅后 `review_outcome=approved`。
  - 多模态质量门禁为 `MULTIMODAL_QUALITY_GATE_READY` 或该 loop 的 `quality_gate_status=passed`。
  - agent smoke 实际执行，结果不是 `not_run` 或 `skipped`。
```

### `review.md` 最小内容

```markdown
# Review

- review_task_id: review-public-demo-001
- reviewed_by: operator
- reviewed_at_utc: 2026-06-23T10:30:00Z
- review_outcome: approved
- revisions_before_approval: 1
- reviewer_edit_distance_pct: 18.0
- reviewer_notes: 输出覆盖了 expected.md 的 must_include，未发现敏感信息。
```

### `run-evidence.json` 最小内容

```json
{
  "latency_ms": 910.0,
  "provider_failure_count": 0,
  "provider_call_count": 2,
  "retry_count": 0,
  "artifact_count": 1,
  "estimated_cost_usd": 0.01,
  "agent_smoke_result": "passed"
}
```

### `quality-evidence.json` 最小内容

质量证据必须来自人工复核后的真实输出，不得用 demo/fixture 代替。每条记录至少包含：

```json
{
  "loop_id": "real-image-slot-003",
  "modality": "image",
  "quality_scores": {
    "faithfulness": 4,
    "completeness": 4,
    "reusability": 4,
    "traceability": 4,
    "safety_redaction": 5,
    "agent_usability": 4
  },
  "critical_issues": [],
  "minor_issues": [],
  "requires_human_review": true,
  "human_review_decision": "approved_for_beta_evidence",
  "ocr_confidence": 0.72,
  "uncertain_regions": []
}
```

生成或校验质量门禁报告：

```powershell
python scripts\multimodal_quality_gate.py --evidence docs\working\status\baselines\real-trial-loop-collection\real-trial-multimodal-quality-evidence.json --fail-on-blocked --print-json
```

该命令只有在 `text,audio,image,video` 均有通过记录、关键阈值达标、无 critical issue、且人审批准时才输出 `MULTIMODAL_QUALITY_GATE_READY`。若 OCR/ASR provider 不可用，证据里必须包含 transcript 或 graceful degradation 说明，不能把低置信输出当确定事实。

这些本地文件用于指导处理和复核，不直接进入仓库。仓库只提交脱敏后的 manifest；manifest 可以引用 `task_reference`、`expected_reference`、`review_task_id`、`artifact_reference` 这类稳定编号，但不能写入本机绝对路径、未脱敏原文或敏感信息。

## 业务期望正确内容是否必须提供

如果目标只是证明“项目能读取文件并产生产物”，`expected.md` 可以很薄；但如果目标是让项目真正可优化、可回归、可判断质量，`expected.md` 必须提供。

原因很简单：没有期望正确内容，系统只能验证“跑过了”，不能判断“做对了”。后续要优化 prompt、模型调用、技能生成质量、跨 agent smoke 或成本/质量权衡时，`expected.md` 和 `review.md` 是主要依据。

本项目采用以下分级：

| 等级 | 可接受数据 | 能证明什么 | 是否足以解除 HOLD |
| --- | --- | --- | --- |
| L0 fixture | 人工模板、空文件、mock、placeholder | 只能测代码路径 | 否 |
| L1 真实来源无期望 | 真实 PDF/代码/音视频，但没有 `expected.md` 和审阅 | 只能测摄入能力 | 否 |
| L2 公开 demo 闭环 | 公开或自有真实文件 + task + expected + review + run evidence | 可以证明公开 demo 上线闭环 | 是，前提是 10 槽位全过 |
| L3 真实业务闭环 | 授权业务数据 + task + expected + review + run evidence | 可以证明业务 Beta/GA 准备度 | 是 |

当前如果你拿不到商业真实数据，推荐使用 L2：公开 demo 闭环。它不能证明“客户生产业务已经验证”，但足够把当前 HOLD 从“没有真实闭环证据”推进为“公开 demo 样本闭环已达标”。

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
      "source_bundle_ref": "local-secure-store://real_loop_sources/RL-001/source_bundle",
      "source_hashes": [
        {
          "filename": "redacted-source.md",
          "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        }
      ],
      "business_expectation_ref": "docs/working/status/baselines/real-trial-loop-collection/real-trial-loop-intake-workpack-summary.md",
      "run_evidence_ref": "docs/working/status/baselines/real-trial-loop-collection/real-trial-loop-intake-workpack-summary.md",
      "human_review_ref": "docs/working/status/baselines/real-trial-loop-collection/real-trial-loop-intake-workpack-summary.md",
      "agent_smoke_ref": "docs/working/status/baselines/real-trial-loop-collection/real-trial-loop-intake-workpack-summary.md",
      "quality_gate_ref": "docs/working/status/baselines/real-trial-loop-collection/real-trial-multimodal-quality-gate-summary.md",
      "generated_bundle_hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "collected_at_utc": "2026-06-20T01:00:00Z",
      "review_task_id": "review-INC-2001",
      "reviewed_by": "reviewer-a",
      "reviewed_at_utc": "2026-06-20T01:30:00Z",
      "review_outcome": "approved",
      "redaction_status": "passed",
      "pii_status": "no_raw_pii_in_repo",
      "review_status": "approved",
      "quality_gate_status": "passed",
      "revisions_before_approval": 1,
      "reviewer_edit_distance_pct": 18.0,
      "agent_smoke_result": "passed",
      "latency_ms": 910.0,
      "provider_failure_count": 0,
      "provider_call_count": 2,
      "retry_count": 0,
      "artifact_count": 1,
      "estimated_cost_usd": 0.01,
      "backfill_slot_index": 1,
      "backfill_action_id": "gl23-slot-001-text",
      "task_reference": "public-demo-001-task",
      "expected_reference": "public-demo-001-expected",
      "artifact_reference": "public-demo-001-artifact",
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
- 业务正确性证据：本地 `expected.md` 必须说明必须命中的内容、拒绝条件和通过标准。
- 运行证据：本地 `run-evidence.json` 必须能对应 manifest 中的 `latency_ms`、`provider_failure_count`、`provider_call_count`、`retry_count`、`artifact_count` 和 `estimated_cost_usd`。
- 质量证据：`quality-evidence.json` 必须通过 `scripts\multimodal_quality_gate.py`，manifest 必须记录 `quality_gate_ref` 和 `quality_gate_status=passed`。

## 验收命令

先扫描模板污染：

```powershell
rg -n "TEMPLATE_REQUIRED|placeholder|fixture|mock" docs\working\status\baselines\real-trial-loop-collection\manifests
```

先跑质量门禁：

```powershell
python scripts\multimodal_quality_gate.py --fail-on-blocked --print-json
```

然后跑 GL-64 manifest 预检：

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
- multimodal quality gate 为 `MULTIMODAL_QUALITY_GATE_READY`，每条 manifest 的 `quality_gate_status=passed`。
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
