# Agent Smoke 操作规程

## 结论

本规程用于落实 CBT-12：对已批准的 skill 包，在以下三个 agent 中进行可复现的人工 smoke 验证：

- Codex
- Claude Code
- OpenCode

目标是形成受控试运行证据，不是把外部 agent 可用性强行接入离线 CI。

## 适用范围

- 在离线 CI 之外执行真实 agent smoke。
- 每次只验证一个已批准的 skill 包。
- 每个 `skill_id + agent` 只能保留一条当前状态记录。
- 合法状态只有：
  - `agent_smoke_passed`
  - `agent_smoke_failed`
  - `not_run`

## 前置条件

- skill 包已经通过人工审核。
- 目标 skill 包已经导出到对应 agent 可发现的位置。
- 试运行环境不包含受监管数据、生产密钥或真实客户敏感数据。

## Smoke 记录字段

每次 agent smoke 必须保留以下字段：

| 字段 | 说明 |
| --- | --- |
| `trigger_prompt` | 发送给 agent 的原始触发提示词 |
| `expected_skill_selection` | 预期被选择的 skill 标识，例如 `package_name` 或目录名 |
| `expected_task_output` | 预期输出行为 |
| `selected_skill` | 实际观测到的 skill 标识 |
| `observed_task_output` | 实际观测到的输出摘要 |
| `status` | `agent_smoke_passed`、`agent_smoke_failed` 或 `not_run` |
| `reason` | 选择当前状态的简短原因 |
| `failure_code` | `status=agent_smoke_failed` 时必填 |

## 触发提示词要求

提示词必须让 skill 选择具备可验证性：

1. 明确场景和目标产物。
2. 要求输出一个具体交付物。
3. 包含可核验要求。

示例：

```text
Use the incident runbook skill to triage this sanitized outage summary.
Return: (1) root-cause hypothesis, (2) rollback decision, (3) post-checklist.
Include evidence references for each recommendation.
```

## 分 agent 人工检查

### Codex

1. 确认 skill 已在 Codex skill path 中可发现。
2. 运行触发提示词。
3. 核验实际选择的 skill 和输出是否符合预期。
4. 使用下方脚本记录状态。

### Claude Code

1. 确认 `SKILL.md` 已在 Claude Code skill path 中可发现。
2. 运行同一触发提示词。
3. 核验实际选择的 skill 和输出。
4. 使用下方脚本记录状态。

### OpenCode

1. 确认 `SKILL.md` 已在 OpenCode skill path 中可发现。
2. 运行同一触发提示词。
3. 核验实际选择的 skill 和输出。
4. 使用下方脚本记录状态。

## 记录命令

脚本：

```powershell
python scripts\agent_smoke.py
```

默认报告路径：

```text
docs/working/status/baselines/controlled-trial/agent-smoke-report.json
```

### 通过样例

```powershell
python scripts\agent_smoke.py `
  --skill-id trial-skill-001 `
  --agent codex `
  --status agent_smoke_passed `
  --reason "Selected expected skill and produced expected checklist." `
  --trigger-prompt "Use the incident runbook skill to triage the sample issue." `
  --expected-skill-selection incident-runbook-skill `
  --expected-task-output "Checklist with rollback and validation steps." `
  --selected-skill incident-runbook-skill `
  --observed-task-output "Produced checklist with rollback and validation."
```

### 失败样例

```powershell
python scripts\agent_smoke.py `
  --skill-id trial-skill-001 `
  --agent claude-code `
  --status agent_smoke_failed `
  --reason "Skill selected but validation section missing." `
  --trigger-prompt "Use the incident runbook skill to triage the sample issue." `
  --expected-skill-selection incident-runbook-skill `
  --expected-task-output "Checklist with rollback and validation steps." `
  --selected-skill incident-runbook-skill `
  --observed-task-output "Output omitted validation checks." `
  --failure-code missing_validation_section
```

### 未运行样例

```powershell
python scripts\agent_smoke.py `
  --skill-id trial-skill-001 `
  --agent opencode `
  --status not_run `
  --reason "Agent environment unavailable in this window." `
  --trigger-prompt "Use the incident runbook skill to triage the sample issue." `
  --expected-skill-selection incident-runbook-skill `
  --expected-task-output "Checklist with rollback and validation steps."
```

## 三端矩阵校验

记录完成后，必须执行只读矩阵校验，确认每个目标 skill 都存在 Codex、Claude Code、OpenCode 三个格子的记录。

校验默认报告：

```powershell
python scripts\agent_smoke.py --validate-matrix --fail-on-incomplete --print-json
```

校验指定 skill：

```powershell
python scripts\agent_smoke.py `
  --validate-matrix `
  --required-skill-id trial-skill-001 `
  --fail-on-incomplete `
  --print-json
```

校验多个 skill：

```powershell
python scripts\agent_smoke.py `
  --validate-matrix `
  --required-skill-id trial-skill-001,trial-skill-002 `
  --fail-on-incomplete `
  --print-json
```

输出状态含义：

| 状态 | 含义 |
| --- | --- |
| `AGENT_SMOKE_MATRIX_READY` | 所有必需 skill 和 agent 格子都有合法记录 |
| `AGENT_SMOKE_MATRIX_INCOMPLETE` | 存在缺失格子或记录字段不完整 |
| `AGENT_SMOKE_MATRIX_EMPTY` | 没有可校验的 skill 记录 |

注意：矩阵校验只检查记录完整性，不会证明 smoke 真实发生。真实运行证据仍必须来自人工执行记录。

## 隔离规则

- 受控试运行阶段保持人工 agent smoke。
- 不要把外部 agent 可用性作为离线 CI 的硬依赖，除非可靠性已经被证明且经过明确批准。
- 不允许为了通过矩阵校验伪造 `agent_smoke_passed`。agent 不可用时应记录 `not_run` 和原因。

## 完成定义

CBT-12 满足时，必须同时符合：

- 每个已批准 skill 对 Codex、Claude Code、OpenCode 都有记录。
- 每条记录状态为 `agent_smoke_passed`、`agent_smoke_failed` 或 `not_run`。
- 每条记录都有非空 `reason`。
- `python scripts\agent_smoke.py --validate-matrix --fail-on-incomplete --print-json` 返回 `AGENT_SMOKE_MATRIX_READY`。
