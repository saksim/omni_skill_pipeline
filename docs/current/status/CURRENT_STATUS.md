# Current Status

## 判词

当前项目已经从“规划文档”推进到“可扩展的多模态蒸馏内核”。

## 当前已更新

### 文档与契约

- 根入口文档已收敛为 `README.md`
- 架构文档已细分为：
  - `docs/current/architecture/ARCHITECTURE.md`
  - `docs/current/architecture/skill-distillation-v2.md`
  - `docs/current/architecture/skill-distillation-v2-roadmap.md`
  - `docs/current/architecture/skill-distillation-v2-implementation-backlog.md`
  - `docs/current/architecture/system-overview.md`
  - `docs/current/architecture/data-flow.md`
  - `docs/current/architecture/providers.md`
  - `docs/current/architecture/storage.md`
- 契约文档已迁移到 `docs/current/contracts/`
- 状态文档已迁移到 `docs/current/status/`
- E0 基线包已落地到 `docs/current/status/baselines/`
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

### E0 基线补齐

- 建立了 E0 样本清单：`docs/current/status/baselines/e0-sample-inventory.md`
- 建立了 2026-04-20 基线重放记录：`docs/current/status/baselines/e0-baseline-2026-04-20.md`
- 建立了评估口径：`docs/current/status/baselines/evaluation-rubric.md`
- 建立了机器可读 manifest：`docs/current/status/baselines/e0-baseline-manifest.json`
- 实际完成了 text / audio / image / video / tabular 五类样本重放
- 实际运行了 MVP 测试：`python -m unittest discover -s tests -p 'test_mvp.py'`

### V2 施工准备

- 已把 E1 及后续 Epic 落成施工任务单：`docs/current/architecture/skill-distillation-v2-work-orders.md`
- 已完成前五刀最小骨架闭环：
  - `TP-E1-01`：V2 基础 enum/dataclass（`Corpus/EvidenceNode/SemanticAtom/SkillGraph`）已落地
  - `TP-E1-02`：`EvidenceUnit -> EvidenceNode` 与 `SkillGraph -> SkillDocument -> SKILL.md` 兼容闭环已可跑
  - `TP-E3-01`：`EvidenceNode` 结构字段覆盖 `time_range/spatial_ref/structural_ref/payload/lineage`
  - `TP-E5-01`：`AtomExtractor` 主接口与 `LegacyInsightAtomExtractor` 过渡实现已落地
  - `TP-E6-01`：`SkillGraph` node/edge 模型与序列化测试已补齐

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

1. 继续 Batch A 收口：`TP-E1-03`（schema v2 草案与 contract 对齐）。
2. 进入 Batch B：`TP-E2-01 -> TP-E2-02`，先打通多资产 `Corpus` 请求与 service 组装。
3. 紧接 `TP-E3-02`（EvidenceBuilder）并保持与现有 adapter 输出兼容。
