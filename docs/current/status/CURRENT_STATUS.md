# Current Status

## 判词

当前项目已经从“规划文档”推进到“可扩展的多模态蒸馏内核”。

## 当前已更新

### 文档与契约

- 根入口文档已收敛为 `README.md`
- 架构文档已细分为：
  - `docs/current/architecture/ARCHITECTURE.md`
  - `docs/current/architecture/system-overview.md`
  - `docs/current/architecture/data-flow.md`
  - `docs/current/architecture/providers.md`
  - `docs/current/architecture/storage.md`
- 契约文档已迁移到 `docs/current/contracts/`
- 状态文档已迁移到 `docs/current/status/`
- 运行文档已细分为：
  - `docs/current/operations/OPERATIONS.md`
  - `docs/current/operations/cli.md`
  - `docs/current/operations/api.md`
  - `docs/current/operations/worker.md`
  - `docs/current/operations/env.md`
- 扩展占位域已建立：
  - `docs/current/operations/runbooks/`
  - `docs/current/operations/environments/`
  - `docs/current/operations/interfaces/`
- 历史变更文档已迁移到 `docs/history/`

### Python 工程骨架

- 建立了 `src/omni_skill_pipeline/` 主包
- 建立了 `apps/api/` 与 `apps/worker/` 入口
- 建立了 `interfaces.py` 协议层，统一 Adapter / Provider / Composer 接口
- 建立了 `repository.py`、`render.py`、`service.py` 等基础模块

### 多模态输入链

- 文本：支持 `txt / md / markdown / rst / log / json / html / doc / docx / pdf`
- 音频：支持 `transcript / transcript_path / sidecar transcript / OpenAI ASR`
- 图像：支持 `OCR + scene summary -> EvidenceUnit`
- 视频：支持 `audio + shot/keyframe + OCR + scene summary -> EvidenceUnit`
- 表格/时间序列：支持 `csv / tsv / txt / json / xlsx / xls -> EvidenceUnit`

## 当前已解决

### 结构性问题

- 解决了 skill 组合器与 provider 直接耦合的问题
- 解决了核心业务层无法插拔替换模型的问题
- 解决了文档、契约、代码路径散落根目录的问题
- 解决了 `docs/current/` 未按场景分域的问题
- 解决了架构与运行文档过长、不利于定位的问题

### 功能性问题

- 解决了音频链只能依赖手工 transcript 的问题
- 解决了图像链没有统一 EvidenceUnit 入口的问题
- 解决了视频链只有简单定间隔抽帧的问题
- 解决了超短视频容易抽不到帧的问题
- 解决了表格/时间序列无法进入统一主链的问题

### 视频链专项修复

- 增加 `ffprobe` 元数据探测
- 增加基于 `scene` 的镜头切分采样
- 增加自适应时间桶采样
- 增加短视频首帧回退
- 增加帧级感知哈希去重
- 增加按时间桶分布式选帧，避免长视频抽样扎堆

### 表格/时间序列专项补全

- 增加 schema evidence
- 增加 missingness evidence
- 增加 entity/group evidence
- 增加 numeric profile evidence
- 增加 time-series overview / metric / anomaly event evidence
- 让结构化输入统一落到 `TABLE / METRIC / EVENT` 类型的 `EvidenceUnit`

## 当前目录分层

```text
./README.md
./docs/
  current/
    architecture/
    contracts/
    status/
    operations/
      runbooks/
      environments/
      interfaces/
  history/
```

## 当前待解

- 尚未把文件系统仓储替换为 PostgreSQL Repository
- 尚未接入 Qdrant 检索
- 尚未建立 Review UI / Review Queue 实体流程
- 时间序列当前还是 heuristic profile，不是完整的统计建模管线
- 视频链还没有更细粒度的 subtitle track、scene cluster、frame caption cache

## 推荐下一刀

1. 把 `tabular/time-series` prompt 专门化，和通用 skill composer 解耦。
2. 把 `docs/current/operations/` 再拆成 `runbooks / environments / interfaces` 的实页内容，而不只是占位目录。
3. 把文件系统仓储升级到 PostgreSQL Repository。