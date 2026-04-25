# E0 Baseline Pack

## 判词

此目录用于固化 V2 改造前的 E0 基线。目标不是保存“好看”的输出，而是保存“可对照、可复验、可审判”的当前事实。

## 包含内容

- [e0-sample-inventory.md](D:\download\gaming\new_program\data_helper\3_omni_skill_pipeline\docs\current\status\baselines\e0-sample-inventory.md)
  - 样本清单、用途、已知缺口
- [e0-baseline-2026-04-20.md](D:\download\gaming\new_program\data_helper\3_omni_skill_pipeline\docs\current\status\baselines\e0-baseline-2026-04-20.md)
  - 2026-04-20 实际重放结果、观察与结论
- [evaluation-rubric.md](D:\download\gaming\new_program\data_helper\3_omni_skill_pipeline\docs\current\status\baselines\evaluation-rubric.md)
  - 后续 V2 所有阶段共用的评估口径
- [e0-baseline-manifest.json](D:\download\gaming\new_program\data_helper\3_omni_skill_pipeline\docs\current\status\baselines\e0-baseline-manifest.json)
  - 机器可读的样本与基线草稿映射
- `e8-dual-write-benchmark-report.json`（由 `scripts/benchmark_dual_write.py` 生成）
  - file-only 与 file+postgres dual-write 的基础时延报告

## 用法

每次推进 V2 任一阶段时，都应执行以下动作：

1. 选取对应样本集
2. 重放当前实现
3. 按 `evaluation-rubric.md` 评分
4. 与 E0 基线对比
5. 记录是变强、持平，还是退化

## 注意

- E0 基线允许包含低质量输出，因为它的职责是反映真相，不是粉饰问题。
- 当前图片与视频基线故意保留了明显 OCR 噪声，它们正是 V2 必须优先斩断的病灶。
