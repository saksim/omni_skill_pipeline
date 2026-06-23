# P0：导出校验闭环修复说明

## 1. 背景

当前项目的核心价值是把输入材料转成可被 Agent 使用的技能工件。因此以下链路必须可靠：

```text
distill -> review/lifecycle -> export -> validate -> agent consume
```

评估中发现：

```bash
omni-skill distill-text --title "Demo Text" --file examples/text_note.md
omni-skill export-skill --bundle skills/drafts/<slug>/bundle.json --target all --output-root /tmp/omni_export
omni-skill validate-skill --package /tmp/omni_export/skills/portable/<slug>
```

`export-skill` 能成功，但 `validate-skill` 失败：

```text
status=fail
failure_codes=REVIEW_APPROVAL_MISSING
```

这说明导出成功不等于导出包可被认可使用。对一个“技能生产流水线”而言，这是 P0 问题。

## 2. 当前现象

评估中观察到的状态不一致：

| 文件/对象 | 观察到的状态 | 问题 |
|---|---|---|
| `review_task.json` | `decision=auto_publish` / `status=published` | 看起来已经发布 |
| `bundle.json` | skill 层仍是 `review_status=draft` | 与 review task 不一致 |
| `agent_skill_package.json` | 仍是 `review_status=draft` | 导出包没有继承发布状态 |
| `validate-skill` | `REVIEW_APPROVAL_MISSING` | validator 认为缺少审核批准 |

## 3. 影响

如果不修复，会导致：

1. 生成的技能包不能自证可用。
2. 内部 demo 可以跑，但 agent consumer 无法信任包状态。
3. release artifact 即使打出来，也可能包含不可验证技能。
4. 后续真实样本闭环会被状态字段卡住。
5. 外部 Beta 用户会遇到“导出成功但校验失败”的体验断裂。

## 4. 必须定义的生命周期模型

建议统一以下状态模型。

### 4.1 Skill lifecycle 状态

| 状态 | 含义 | 是否可导出 | 是否可 validate pass |
|---|---|---:|---:|
| `draft` | 初始草稿，未完成审核 | 可选，默认不建议 | 否 |
| `review_required` | 需要人工审核 | 否 | 否 |
| `approved` | 已审核批准，但未发布 | 是 | 是 |
| `published` | 已发布 | 是 | 是 |
| `rejected` | 审核拒绝 | 否 | 否 |
| `deprecated` | 已废弃 | 可选 | 视策略而定 |

### 4.2 Review decision 状态

| decision | 含义 | 对 skill lifecycle 的影响 |
|---|---|---|
| `auto_publish` | 规则允许自动发布 | 应把 skill lifecycle 更新为 `published` |
| `approve` | 人工批准 | 应把 skill lifecycle 更新为 `approved` 或 `published` |
| `request_changes` | 需要修改 | 应保持 `review_required` |
| `reject` | 拒绝 | 应更新为 `rejected` |

### 4.3 Source of truth

必须明确 source of truth，建议如下：

| 对象 | 角色 |
|---|---|
| `bundle.json` | 技能包主状态 source of truth |
| `review_task.json` | 审核过程记录，不应单独作为最终状态 |
| `agent_skill_package.json` | 导出包，应继承 `bundle.json` 的最终状态 |
| validator | 只信任导出包中的最终 lifecycle/review status 与审核证明 |

## 5. 建议代码施工范围

需要重点检查和修改：

```text
src/omni_skill_pipeline/cli.py
src/omni_skill_pipeline/models.py
src/omni_skill_pipeline/assembly/lifecycle.py
src/omni_skill_pipeline/exporters/agent_skill_exporter.py
src/omni_skill_pipeline/publication/portable_skill_renderer.py
src/omni_skill_pipeline/validation/skill_usability.py
src/omni_skill_pipeline/review/packet.py
tests/
```

说明：具体函数名以源码为准，施工模型应先定位：

- skill lifecycle 写入位置；
- review packet 生成位置；
- export package 构建位置；
- validate-skill 检查 `REVIEW_APPROVAL_MISSING` 的位置；
- 测试 fixture 中对 review status 的预期。

## 6. 施工任务拆解

### T1：定位 validator 失败条件

目标：找到 `REVIEW_APPROVAL_MISSING` 的判定逻辑。

输出：

- 判定字段清单；
- 当前导出包缺少哪些字段；
- 当前是否有测试覆盖。

### T2：统一生命周期字段

目标：当 `review_task.decision=auto_publish` 且 `review_task.status=published` 时，`bundle.json` 和导出包不得仍是 `draft`。

建议规则：

```text
if review_task.decision in ["auto_publish", "approve"] and review_task.status in ["approved", "published"]:
    skill.review_status = "published" or "approved"
```

### T3：导出包继承最终状态

目标：`agent_skill_package.json`、portable package manifest、skill metadata 均继承最终状态。

不得出现：

```json
{"review_status": "draft"}
```

除非用户明确执行 `--allow-draft-export`。

### T4：validator 支持明确策略

建议 `validate-skill` 默认拒绝 draft：

```text
review_status in ["approved", "published"] -> pass
review_status in ["draft", "review_required"] -> fail REVIEW_APPROVAL_MISSING
review_status == "rejected" -> fail REVIEW_REJECTED
```

如果确实需要开发态校验，新增：

```bash
omni-skill validate-skill --package <path> --allow-draft
```

开发态 pass 不能作为 release gate 证据。

### T5：补测试

必须新增或修复测试：

1. fresh `distill-text` 后 bundle 状态正确。
2. auto publish 后 bundle 状态不是 draft。
3. export 后 `agent_skill_package.json` 状态继承。
4. validate approved/published package pass。
5. validate draft package fail。
6. validate rejected package fail。
7. `--allow-draft` 只在开发态放行。

## 7. 验收命令

### 7.1 最小闭环

```bash
rm -rf /tmp/omni_export skills/drafts/demo-text-*
omni-skill distill-text --title "Demo Text" --file examples/text_note.md
omni-skill export-skill --bundle skills/drafts/<generated-slug>/bundle.json --target portable --output-root /tmp/omni_export
omni-skill validate-skill --package /tmp/omni_export/skills/portable/<generated-slug>
```

期望：

```text
status=pass
```

### 7.2 全目标闭环

```bash
omni-skill export-skill --bundle skills/drafts/<generated-slug>/bundle.json --target all --output-root /tmp/omni_export
find /tmp/omni_export -name 'agent_skill_package.json' -o -name 'manifest.json'
omni-skill validate-skill --package /tmp/omni_export/skills/portable/<generated-slug>
```

期望：

- portable package validate pass；
- agent package 中 review/lifecycle 状态不是 draft；
- manifest 中有审核证明或自动发布证明；
- 无 `REVIEW_APPROVAL_MISSING`。

## 8. 完成定义

该 P0 项只有在以下条件全部满足时才算完成：

1. 新生成技能可以导出。
2. 新导出技能可以通过 `validate-skill`。
3. draft/rejected package 仍会被正确拒绝。
4. 相关状态字段在 `bundle.json`、`review_task.json`、导出 manifest、agent package 中一致。
5. 新增测试覆盖正向和反向路径。
6. CLI 文档更新，说明默认审核/发布策略。
7. release gate 或 launch gate 不再被该问题间接阻塞。

## 9. 禁止的伪修复

不允许：

- 直接删除 `REVIEW_APPROVAL_MISSING` 检查；
- 让所有 draft 包默认 pass；
- 只修改测试 fixture，不改实际导出逻辑；
- 只改文档，不改代码；
- 把 `auto_publish` 写进 `review_task.json` 但不更新最终包状态；
- 为了通过 validator，把状态硬编码成 `published`，但没有审核记录。
