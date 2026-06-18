# Internal Dogfood Gate Spec

## 目标

新增内部 dogfood 专用上线门禁，允许在没有真实外部业务闭环的情况下进行内部试用，同时不破坏正式 `launch_gate.py` 的外部上线语义。

## 设计原则

1. 内部门禁只服务内部上线。
2. 正式 `scripts/launch_gate.py` 继续负责外部 Beta/GA readiness。
3. fixture/simulated evidence 可以用于内部 dogfood，但必须显式标注。
4. 任何内部放行结果不得被解释为外部可发布。

## 建议脚本

```text
scripts/internal_launch_gate.py
```

建议测试：

```text
tests/test_internal_launch_gate.py
```

建议输出：

```text
docs/working/status/baselines/internal-dogfood-readiness-report.json
docs/working/status/baselines/internal-dogfood-readiness-summary.md
```

## 决策值

| Decision | 含义 |
| --- | --- |
| `READY_FOR_INTERNAL_DOGFOOD` | 可以内部玩具上线 |
| `HOLD` | 内部上线仍存在阻断项 |

## 输入证据

| 输入 | 默认路径 | 必需 |
| --- | --- | --- |
| CI 结果 | 命令实时执行或外部传入 | 是 |
| launch gate 结果 | `scripts/launch_gate.py --print-json` | 是 |
| doc sync 结果 | `docs/working/status/baselines/e13-doc-sync-check-report.json` | 建议 |
| operations readiness | `docs/working/status/baselines/operations-readiness-report.json` | 建议 |
| API health | 实时 URL 或记录文件 | 是 |
| 内部样例结果 | controlled-trial fixture 或 CLI/API smoke | 是 |

## Checks

| Check ID | 阻塞 | 通过条件 |
| --- | --- | --- |
| `ci_entrypoint_available` | 是 | `scripts/ci.py` 存在，workflow 不引用缺失脚本 |
| `ci_baseline_passed` | 是 | CI 通过，或只存在明确豁免的非阻塞失败 |
| `official_launch_gate_accounted` | 是 | `launch_gate.py` 可运行，若 `HOLD`，blocker 必须可解释 |
| `official_launch_gate_not_overridden` | 是 | 内部门禁不得把外部 `HOLD` 改写为外部 `GO` |
| `api_health_ready` | 是 | `/healthz` 可访问且状态可解释 |
| `internal_sample_available` | 是 | 至少一个 CLI/API happy path 可完成 |
| `review_required_default` | 是 | 生成 artifact 不默认自动发布 |
| `internal_only_label_present` | 是 | 输出含 internal-only 语义 |
| `docs_indexed` | 否 | 内部上线文档已被索引 |

## 输出 JSON 结构

建议输出：

```json
{
  "schema_version": "internal_dogfood_readiness.v1",
  "generated_at_utc": "2026-06-18T00:00:00Z",
  "decision": "READY_FOR_INTERNAL_DOGFOOD",
  "decision_code": 0,
  "scope": "internal_dogfood_only",
  "external_launch_decision": "HOLD",
  "checks": [
    {
      "id": "ci_entrypoint_available",
      "status": "pass",
      "blocking": true,
      "details": "Workflow calls scripts/ci.py."
    }
  ],
  "failed_checks": [],
  "evidence_paths": {}
}
```

## CLI 形态

建议命令：

```powershell
python scripts\internal_launch_gate.py --output - --summary-output - --print-json
```

建议参数：

| 参数 | 用途 |
| --- | --- |
| `--output` | JSON 报告输出路径，`-` 表示 stdout |
| `--summary-output` | Markdown 摘要输出路径，`-` 表示 stdout |
| `--print-json` | 打印 JSON |
| `--launch-gate-report` | 可选，读取已有正式 launch gate 报告 |
| `--healthz-url` | 可选，实时检查 API health |
| `--allow-fixture-evidence` | 默认允许，但输出必须标注 internal-only |
| `--fail-on-hold` | CI 场景中将 `HOLD` 转为非零退出 |

## 施工步骤

1. 新增 `scripts/internal_launch_gate.py`。
2. 复用项目现有 JSON/Markdown 输出风格。
3. 读取或执行正式 `launch_gate.py`，但只把其结果作为外部上线说明。
4. 检查 `.github/workflows/ci.yml` 是否调用 `scripts/ci.py`。
5. 检查 healthz 或允许传入 health report。
6. 输出 JSON 和 summary。
7. 新增 `tests/test_internal_launch_gate.py` 覆盖 READY/HOLD。
8. 更新 docs 索引和 runbook。

## 测试场景

| 场景 | 预期 |
| --- | --- |
| workflow 调用缺失脚本 | `HOLD` |
| CI 通过、launch gate 因真实 loop 不足 HOLD | `READY_FOR_INTERNAL_DOGFOOD` |
| launch gate 有安全/文档/ops blocker | `HOLD` |
| API health 不可用 | `HOLD` |
| fixture evidence 未标注 internal-only | `HOLD` |

## 与正式 launch gate 的关系

内部 gate 可以说：

> 可以内部玩具上线。

内部 gate 不可以说：

> 可以外部 Beta。
> 可以 GA。
> 可以 SaaS。
> 真实业务闭环已达标。
