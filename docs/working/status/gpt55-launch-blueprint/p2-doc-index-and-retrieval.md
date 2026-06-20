# P2 文档索引与检索扩展施工方案

## 目标

清理文档路径漂移，并约束 pgvector/Qdrant 扩展，避免后续施工被历史目录、旧术语或占位能力误导。

## 文档路径治理

### 当前分层

| 层级 | 含义 |
| --- | --- |
| `docs/latest/` | 最新已发布使用手册层 |
| `docs/working/` | 当前迭代层 |
| `docs/releases/` | 发布层 |
| `docs/archive/` | 归档层 |
| `docs/reviews/` | 阶段评审、能力评估和风险复盘 |

### 扫描命令

```powershell
rg -n "docs/current|docs/history" README.md docs scripts tests
```

处理规则：

- live README、latest、working、release 文档中命中旧路径时，优先改成当前分层。
- archive 或 historical evidence 中命中旧路径时，可以保留，但要能看出它是历史证据。
- 生成证据中的绝对路径不强制重写，除非它被当前操作文档引用为 live 路径。

### doc sync 验收

```powershell
python scripts\doc_sync.py --output -
```

如果 doc sync 失败，先修 live 文档链接和索引，再处理历史证据。

## 检索后端边界

当前 pgvector/Qdrant 不是 P0 上线阻塞。不得为了“看起来更完整”提前引入中间件。

### 启动条件

同时满足以下任意一类真实需求时，才启动检索后端施工：

- 真实 loop 需要跨 skill 或跨项目相似案例召回。
- reviewer 需要按历史审核结果检索相似失败。
- agent 需要根据上下文召回历史 runbook 或 examples。
- 文件系统和 JSON manifest 查询已经无法满足延迟、召回率或数据规模要求。

### ADR 必填内容

启动前必须补充 ADR，至少包含：

- 选择 pgvector、Qdrant 或继续文件索引的理由。
- 数据模型和索引字段。
- 写入路径和回放策略。
- 查询 API。
- integration test。
- recall、latency、cost 指标。
- 回滚方案。

### 可用检查命令

```powershell
python scripts\roadmap_ext.py --stage retrieval_layer --dry-run --print-json
python scripts\pg_ga.py --stage postgres_repository_contract --dry-run --print-json
```

`pg_ga.py` 只证明 Postgres 轨道的契约或 dry-run，不等价于 pgvector 已生产可用。

## 完成定义

- 当前文档索引不再误导到旧目录。
- release note 不宣称未完成的检索后端能力。
- 检索后端未启动时，明确标记为 Future Track。
- 检索后端启动时，有 ADR、测试、指标和回滚。
