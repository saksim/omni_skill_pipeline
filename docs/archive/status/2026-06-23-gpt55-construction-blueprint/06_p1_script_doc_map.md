# P1：操作脚本地图与文档同步补全说明

## 1. 背景

项目已有 `docs/latest/operations/script-name-map.md` 和 `scripts/doc_sync.py`，但评估发现：当前 script-name-map 没有覆盖全部脚本。尤其一些关键脚本缺失。

这说明：

```text
doc_sync pass != 操作文档全覆盖
```

## 2. 当前发现的缺失脚本

至少以下脚本需要补入 script-name-map：

```text
scripts/gl57_closure_cadence_escalation_closure.py
scripts/gl58_closure_cadence_escalation_closure_cadence.py
scripts/gl59_closure_cadence_escalation_closure_cadence_escalations.py
scripts/gl60_closure_cadence_escalation_closure_cadence_escalation_closure.py
scripts/gl61_closure_cadence_escalation_closure_cadence_escalation_closure_cadence.py
scripts/gl62_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations.py
scripts/gl63_real_loop_intake_workpack.py
scripts/gl64_real_loop_manifest_preflight.py
scripts/internal_dogfood_smoke.py
scripts/internal_launch_gate.py
scripts/release_artifacts.py
scripts/release_consumer_smoke.py
```

其中 P0/P1 高价值脚本是：

```text
gl63_real_loop_intake_workpack.py
gl64_real_loop_manifest_preflight.py
internal_dogfood_smoke.py
internal_launch_gate.py
release_artifacts.py
release_consumer_smoke.py
```

## 3. 风险

1. 后续工程模型不知道脚本用途。
2. 新人无法复现发布/门禁流程。
3. 关键脚本缺少输入输出说明。
4. doc_sync 给出假安全感。
5. 外部 Beta 运行手册不完整。

## 4. 文档补全标准

每个脚本在 script-name-map 中至少应包含：

| 字段 | 必填 | 说明 |
|---|---:|---|
| Script name | 是 | 文件名 |
| Purpose | 是 | 脚本用途 |
| When to run | 是 | 何时运行 |
| Inputs | 是 | 输入文件/参数 |
| Outputs | 是 | 输出文件/状态 |
| Example command | 是 | 可复制命令 |
| Success criteria | 是 | 成功判定 |
| Failure modes | 是 | 常见失败 |
| Related gate | 是 | release/launch/GA/doc/real-loop |
| Owner | 可选 | 维护角色 |

## 5. 推荐 script-name-map 条目模板

```markdown
## scripts/gl64_real_loop_manifest_preflight.py

- Purpose: Validate the presence, structure, redaction status, and launch-gate eligibility of real-loop manifests.
- When to run: Before launch gate, before external beta readiness review, and after adding or updating real-loop evidence.
- Inputs:
  - `docs/working/status/real-loop-manifests/*.manifest.json`
  - Optional summary output path
- Outputs:
  - JSON summary with valid/invalid/missing/pending counts
  - Exit code 0/1 depending on strict flags
- Example:

```bash
python scripts/gl64_real_loop_manifest_preflight.py --fail-on-invalid --fail-on-pending --print-json
```

- Success criteria:
  - `missing=0`
  - `invalid=0`
  - no pending required evidence
- Failure modes:
  - Missing manifest slots
  - Invalid redaction status
  - Missing human review
  - Missing agent smoke evidence
- Related gate: Launch gate / real-loop evidence gate
```

## 6. doc_sync 增强建议

当前 `doc_sync.py` 应增加一条检查：

```text
Every scripts/*.py file must be mentioned in docs/latest/operations/script-name-map.md.
```

伪代码：

```python
scripts = sorted(Path("scripts").glob("*.py"))
map_text = Path("docs/latest/operations/script-name-map.md").read_text()
missing = [p.name for p in scripts if p.name not in map_text]
if missing:
    fail("SCRIPT_MAP_MISSING_ENTRIES", missing)
```

可以允许显式 ignore，但必须在文档中声明：

```text
scripts/_internal_helper.py: ignored because it is not user-facing and is imported only.
```

## 7. 操作文档层级建议

将脚本分为以下类别：

| 类别 | 示例 | 文档位置 |
|---|---|---|
| CLI/user-facing | `omni-skill ...` | `docs/latest/operations/cli.md` |
| release | `release_artifacts.py`, `release_consumer_smoke.py` | `docs/latest/operations/release.md` |
| real-loop | `gl63`, `gl64`, `launch_gate.py` | `docs/latest/operations/runbooks/real-data-intake-and-validation.md` |
| CI/testing | `ci.py`, `tp_tests.py`, `doc_sync.py` | `docs/latest/operations/testing.md` |
| Postgres/worker | `pg_ga.py`, `worker_ga.py` | `docs/latest/operations/postgres-worker.md` |
| governance | `ops_evidence.py`, `validate_manifest.py` | `docs/latest/operations/governance.md` |

## 8. 验收命令

```bash
python scripts/doc_sync.py --output -
python - <<'PY'
from pathlib import Path
scripts = sorted(p.name for p in Path('scripts').glob('*.py'))
text = Path('docs/latest/operations/script-name-map.md').read_text(encoding='utf-8')
missing = [s for s in scripts if s not in text]
print(missing)
raise SystemExit(1 if missing else 0)
PY
```

期望：

```text
[]
Doc sync checks pass
```

## 9. 完成定义

1. 所有 `scripts/*.py` 均在 script-name-map 中出现。
2. 每个关键脚本有可复制命令。
3. 每个关键脚本有成功/失败判定。
4. doc_sync 自动检查脚本覆盖率。
5. 新增脚本时，如果未补文档，CI 失败。

## 10. 禁止的伪修复

不允许：

- 只把脚本名塞进文档但不写用途；
- 在 doc_sync 中 hardcode pass；
- 把关键脚本加入 ignore；
- 删除脚本避免文档缺失；
- 对 P0/P1 脚本只写“一句话说明”。
