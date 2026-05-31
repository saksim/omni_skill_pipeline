# Controlled Trial Loop Runbook

## 判词

本手册对应 `CBT-11 End-to-End Trial Runner`，用于可重复执行单轮受控业务试运行闭环：

- 输入 CBT-02 trial manifest
- 执行 distillation
- 强制 `REVIEW_REQUIRED`
- 生成 reviewer packet
- 模拟人工批准后导出 skill package
- 执行 CBT-13 trial security gate（导出前拦截不安全产物）
- 执行 package validator
- 产出 trial metrics report + markdown summary

目标是验证受控试运行闭环，不是宣称 GA。

## Scope

- Runner script: `scripts/controlled_trial.py`
- 默认输出目录：`docs/current/status/baselines/controlled-trial/`
- 依赖链路：
  - `scripts/validate_manifest.py`
  - `src/omni_skill_pipeline/service.py`
  - `src/omni_skill_pipeline/review/packet.py`
  - `src/omni_skill_pipeline/exporters/agent_skill_exporter.py`
  - `src/omni_skill_pipeline/validation/trial_security_gate.py`
  - `src/omni_skill_pipeline/validation/skill_usability.py`
  - `src/omni_skill_pipeline/quality/trial_metrics.py`

## Preconditions

- `python` 可执行且依赖已安装（建议 Python 3.11）。
- manifest 满足 CBT-02 合同（`modality/scenario/source_owner/sensitivity/asset_list/review_owner/target_package_format/expected_output_type`）。
- 禁止把结果描述为正式 GA；闭环结果只可用于受控试运行或受控外部 Beta 前置试运行评估。

## Dry Run Plan

先生成执行计划，不跑 distillation：

```bash
python scripts/controlled_trial.py \
  --manifest docs/current/status/baselines/trial-manifests/trial-sample-mixed-corpus.example.json \
  --output-dir docs/current/status/baselines/controlled-trial \
  --dry-run
```

产物：

- `controlled-trial-execution-plan.json`

## Fixture Smoke Loop (Offline)

无外部 provider 条件下，使用 fixture stubs 执行一轮混合样本：

```bash
python scripts/controlled_trial.py \
  --manifest docs/current/status/baselines/trial-manifests/trial-sample-mixed-corpus.example.json \
  --output-dir docs/current/status/baselines/controlled-trial \
  --use-fixture-stubs \
  --target portable \
  --simulated-agent-smoke-result passed \
  --release-decision GO
```

说明：

- `--use-fixture-stubs` 会替换 OCR/image/video provider，避免网络和真实 provider 依赖。
- runner 默认注入：
  - `OMNI_CONTROLLED_TRIAL_REVIEW_MODE=1`
  - `OMNI_CONTROLLED_TRIAL_REVIEW_REASON_CODE=controlled_trial_requires_review`
- runner 会在导出前写入模拟人工批准标记（仅用于 CBT-11 闭环验证）。
- runner 会在导出前运行 CBT-13 trial security gate；命中密钥、本地绝对路径、危险生产指令和未批准敏感分类时直接失败。

## Optional Real-Service Loop

使用当前环境实际 provider 执行（不启用 fixture stubs）：

```bash
python scripts/controlled_trial.py \
  --manifest docs/current/status/baselines/trial-manifests/trial-sample-text.example.json \
  --output-dir docs/current/status/baselines/controlled-trial \
  --target codex
```

## Outputs

默认输出目录内会生成：

- `controlled-trial-execution-plan.json`
- `controlled-trial-run-report.json`
- `trial-metrics-manifest.json`
- `trial-metrics-report.json`
- `trial-metrics-summary.md`
- `simulated-approval/<sample_id>-bundle.approved.json`
- `exports/<sample_id>/.../SKILL.md`
- `exports/<sample_id>/.../agent_skill_package.json`
- `samples[*].trial_security_gate_report`（写入 `controlled-trial-run-report.json`）

## Exit Code Contract

- `0`: 执行成功（即便 metrics 结论为 fail，只要未启用 blocker fail）。
- `1`: 启用 `--fail-on-ga-blocker` 且触发 critical GA blocker。
- `2`: 参数/manifest/执行链路错误（包括 distill/export/validate/metrics 任一步失败）。

## Safety Rules

- 禁止用 `--dry-run`、跳过 validator、跳过 doc sync 结果来宣称完成受控试运行。
- 受控试运行阶段的 package 默认必须经人工审核；runner 内置“模拟批准”仅用于自动化闭环验证，不代表真实发布批准。
- 若 `trial-metrics-report.json` 中 `ga_discussion_blocked=true`，必须进入 remediation，不得推进 GA 讨论。
