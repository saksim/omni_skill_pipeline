# System Overview

## 判词

当前实现采用 `Hexagonal + Provider/Fallback + Local Artifact Store` 架构。

## Core Principles

- Core 只关心 `Asset / EvidenceUnit / Insight / SkillDocument`
- Adapters 负责多模态输入归一化
- Providers 负责外部能力调用
- Pipeline 负责 insight extraction 与 skill composition
- Repository 负责工件落盘，不承担业务规则

## Capability Boundary

### 已落地

- 文本入口：`txt/md/markdown/rst/log/json/html/doc/docx/pdf`
- 音频入口：`audio -> transcript -> skill`
- 图像入口：`image -> OCR + scene summary -> skill`
- 视频入口：`video -> audio + shot/keyframe + OCR + scene summary -> skill`
- 表格/时间序列入口：`tabular/time-series -> schema + metrics + events -> skill`
- CLI / API / Worker 三套入口
- 本地工件仓储：`asset.json / evidence.json / insights.json / skill.json / SKILL.md / bundle.json`

### 外部依赖

- Python interpreter: `D:\code_environment\anaconda_all_css\py311\python.exe`
- OpenAI Python SDK
- Tesseract OCR
- FFmpeg / FFprobe

### 当前非目标

- PostgreSQL 真持久化
- Qdrant 检索
- Review UI
- 多 Agent 蒸馏链

## Module Boundaries

| 模块 | 路径 | 责任 | 不该做什么 |
| --- | --- | --- | --- |
| Domain Models | `src/omni_skill_pipeline/models.py` | 核心对象与请求模型 | 不直接调用外部服务 |
| Interfaces | `src/omni_skill_pipeline/interfaces.py` | 统一协议层 | 不写具体逻辑 |
| Adapters | `src/omni_skill_pipeline/adapters/` | 输入归一化 | 不直接写盘 |
| Providers | `src/omni_skill_pipeline/providers/` | 外部能力调用 | 不做业务决策 |
| Pipeline | `src/omni_skill_pipeline/pipeline.py` | Insight 提取、heuristic 组合 | 不关心 HTTP / CLI |
| Service | `src/omni_skill_pipeline/service.py` | 主编排 | 不关心数据库实现 |
| Repository | `src/omni_skill_pipeline/repository.py` | 工件落盘 | 不改业务规则 |
| Renderer | `src/omni_skill_pipeline/render.py` | 渲染 `SKILL.md` | 不关心模态 |
| API | `src/omni_skill_pipeline/api_app.py` | HTTP 层 | 不复制蒸馏逻辑 |
| Worker | `src/omni_skill_pipeline/worker.py` | 本地任务消费 | 不复制蒸馏逻辑 |

## Runtime Topology

```text
CLI / API / Worker Job
        |
        v
DistillationService
        |
        +--> TextAdapter
        +--> AudioAdapter
        +--> ImageAdapter
        +--> TabularAdapter
        +--> VideoAdapter
        |
        v
LoadedAsset(asset + evidence_units + title_hint)
        |
        v
InsightExtractor
        |
        v
SkillComposer
        |
        v
MarkdownRenderer + FileArtifactRepository
```

## Runtime State Machine

```text
RECEIVED
  -> VALIDATED
  -> LOADED
  -> NORMALIZED
  -> EXTRACTED
  -> COMPOSED
  -> RENDERED
  -> PERSISTED
  -> REVIEW_PENDING
  -> PUBLISHED | REJECTED
```

当前真实落地的状态：

- `RECEIVED`
- `VALIDATED`
- `LOADED`
- `NORMALIZED`
- `EXTRACTED`
- `COMPOSED`
- `RENDERED`
- `PERSISTED`