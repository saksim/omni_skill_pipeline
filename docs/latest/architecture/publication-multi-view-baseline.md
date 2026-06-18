# Publication Multi-View Baseline

> Date: 2026-04-25  
> Task Card: `LC-R-36`  
> Scope: extend publication pipeline to emit checklist / decision tree views

## Verdict

`PublicationOrchestrator` 已根据 `DistillGoal.goal_type` 打通多视图发布路径。  
在保留 `SKILL.md + skill.json` 兼容输出的前提下，可按目标附加结构化发布视图：

- `extract_checklist` -> `checklist.json`
- `extract_decision_tree` -> `decision_tree.json`

## Runtime Contract

Goal 到 publication type 的映射：

- `build_skill` / default:
  - `skill_markdown`
  - `skill_json`
- `extract_checklist`:
  - `skill_markdown`
  - `skill_json`
  - `checklist_json`
- `extract_decision_tree`:
  - `skill_markdown`
  - `skill_json`
  - `decision_tree_json`

当 `decision` 节点为空时，`decision_tree.json` 自动补 `default` branch，避免空树输出。

## Test Landing

已将多视图发布验证纳入 `TP-E6-03` 测试脚本映射：

- `tests/test_publication_builder.py`
  - `test_builder_emits_checklist_and_decision_tree`
  - `test_builder_emits_default_decision_tree_when_graph_has_no_decisions`
- `tests/test_publication_orchestrator_split.py`
  - `test_orchestrator_chooses_goal_specific_publication_types`

执行入口：

```bash
python scripts/tp_tests.py TP-E6-03 --python python
```

## Next Cut

- `LC-R-37`: review queue operations surface（查看/认领/关闭）

## Follow-up Update

- `LC-R-37` completed on 2026-04-25: review queue operations surface (`list` / `claim` / `close`).
