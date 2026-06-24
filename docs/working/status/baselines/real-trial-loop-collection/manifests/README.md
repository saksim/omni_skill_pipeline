# 真实闭环 Manifest 目录

在运行 GL-13 批量摄入前，把操作者收集并脱敏后的真实 loop manifest JSON 放在本目录。

本目录在源码仓库中只保留本 README。release artifact pipeline 不会在这里生成真实 Beta 证据。真实原始数据应放在本地未入库目录 `data/real-inputs/<batch-id>/`，本目录只接收脱敏 manifest。

不要只放一个 `source` 文件就声明闭环完成。每个槽位必须先在本地形成 source bundle：`source/`、`task.md`、`expected.md`、`review.md` 和 `run-evidence.json`。其中 `expected.md` 用来定义业务上什么结果算正确；没有它只能证明文件被处理过，不能证明项目做对了。

合格 manifest 必须是 JSON object，顶层必须包含 `loops` 数组。每个 GL-63 槽位 manifest 只能包含该槽位的一条 loop，不允许混入其他槽位、其他模态或多条合格 loop。每条可进入 launch gate 的记录都必须携带真实证据标签和追溯字段，例如 `evidence_origin=real`、`launch_gate_eligible=true`、`source_system`、`source_reference`、`collected_at_utc`、`review_task_id`、`reviewed_by` 和 `reviewed_at_utc`。

优先阅读：

```text
docs/latest/operations/runbooks/real-data-intake-and-validation.md
```

运行 GL-13 前，先执行：

```powershell
python -B scripts\gl64_real_loop_manifest_preflight.py --fail-on-invalid --fail-on-pending
```

只有 `REAL_LOOP_MANIFEST_PREFLIGHT_READY` 表示所有 GL-63 目标 manifest 文件都已存在，且结构上允许进入下一步摄入。从本槽位目录运行 GL-13 时，必须传入 `--require-manifest-preflight-ready`，这样 GL-64 只要报告 pending 或 invalid 槽位，摄入就会自动停止。

字段契约可参考父目录的 `real-trial-loop-metrics-manifest.template.json`，但不能把 template 直接当成真实证据提交。当前推荐的最小可上线数据等级是公开 demo 闭环：公开或自有真实文件 + task + expected + review + run evidence + 脱敏 manifest。
