# V1 -> V2 Migration Runbook

## 判词

迁移执行只做三件事：先验测、再切换、可回退。所有命令按 Linux 环境编排，统一在窗口内一次完成。

## Linux 执行序列

```bash
python scripts/tp_tests.py TP-E8-03 TP-E10-02 TP-E13-02 --python python3
python scripts/doc_sync.py --output docs/current/status/baselines/e13-doc-sync-check-report.json
```

切换后追加最小业务烟测（按当前业务入口命令）：

```bash
python scripts/tp_tests.py TP-E12-01 TP-E12-02 --python python3
```

## 回退操作序列

1. 将默认读取路径切回 V1 兼容层（保留 V2 artifact，不做删除）。
2. 重新执行 `python scripts/tp_tests.py TP-E8-03 TP-E10-02 --python python3` 验证回退链路。
3. 重新生成 doc sync 报告，确认迁移说明仍与实际代码一致。
4. 记录故障样本 request_id/trace_id，转入下个窗口处理。

## 风险观察点

- `review_status` 与 `review_task` 是否出现不一致。
- publication 视图缺字段时，fallback 是否命中 legacy 输出。
- 切换窗口内 provider 调用审计是否出现异常峰值。
- doc sync 报告是否出现 `migration_guide_completeness` 失败。

## 变更窗口清单

- 变更前：冻结非必要发布，保留回退开关。
- 变更中：实时记录执行命令与返回码。
- 变更后：保留报告产物与关键日志至少 7 天。
