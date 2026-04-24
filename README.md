# Omni Skill Pipeline

将多模态输入蒸馏为可复用、可追溯、可演化的 `SKILL.md` / `skill.json` / publication artifacts。

## 判词

这不是“文件转 Markdown 工具”，而是一条 `Evidence -> SkillDocument / SkillGraph -> Publication` 的知识蒸馏主链。

## 当前能力

- 文本：支持 `txt / md / markdown / rst / log / json / html / doc / docx / pdf`
- 音频：支持 `audio -> transcript -> skill`，可接 OpenAI ASR
- 图像：支持 `image -> OCR + scene summary -> skill`
- 视频：支持 `video -> audio + keyframe + OCR + scene summary -> skill`
- 表格与时序：支持 `tabular/time-series -> TABLE / METRIC / EVENT -> skill`
- V2 语义层：已落地 `Corpus`、`EvidenceNode`、`SemanticAtom`、`SkillGraph`、`Publication`
- 质量门禁：已落地 quality scoring、review policy、review task、review feedback 持久化
- 输出工件：默认写入 `skills/drafts/`，包含 `SKILL.md`、`skill.json`、`bundle.json`、publication manifest 与 review artifacts

## 快速开始

### 1. 准备 Python 3.11 环境

PowerShell:

```powershell
py -3.11 -m venv .venv
. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

POSIX:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

### 2. 验证 CLI 可用

```bash
python -m omni_skill_pipeline.cli show-template
```

### 3. 跑一次本地回归

```bash
python scripts/run_ci.py
```

## 入口

- Package root: `src/omni_skill_pipeline/`
- CLI entry: `src/omni_skill_pipeline/cli.py`
- API app: `apps/api/main.py`
- Worker app: `apps/worker/main.py`
- Template contract: `docs/current/contracts/SKILL.template.md`
- Skill schema: `docs/current/contracts/skill.schema.json`

## 文档导航

### Current

- 总索引: [docs/INDEX.md](docs/INDEX.md)
- 架构入口: [docs/current/architecture/ARCHITECTURE.md](docs/current/architecture/ARCHITECTURE.md)
- V2 设计: [docs/current/architecture/skill-distillation-v2.md](docs/current/architecture/skill-distillation-v2.md)
- V2 路线图: [docs/current/architecture/skill-distillation-v2-roadmap.md](docs/current/architecture/skill-distillation-v2-roadmap.md)
- V2 开发拆解: [docs/current/architecture/skill-distillation-v2-implementation-backlog.md](docs/current/architecture/skill-distillation-v2-implementation-backlog.md)
- V2 施工任务单: [docs/current/architecture/skill-distillation-v2-work-orders.md](docs/current/architecture/skill-distillation-v2-work-orders.md)
- 当前状态: [docs/current/status/CURRENT_STATUS.md](docs/current/status/CURRENT_STATUS.md)
- 运行文档入口: [docs/current/operations/OPERATIONS.md](docs/current/operations/OPERATIONS.md)
- API: [docs/current/operations/api.md](docs/current/operations/api.md)
- CLI: [docs/current/operations/cli.md](docs/current/operations/cli.md)
- Environment: [docs/current/operations/env.md](docs/current/operations/env.md)
- Testing: [docs/current/operations/testing.md](docs/current/operations/testing.md)
- 项目评估: [docs/glm-5.1-project-assessment.md](docs/glm-5.1-project-assessment.md)

### History

- Changelog: [docs/history/CHANGELOG.md](docs/history/CHANGELOG.md)

## 当前工程判断

- 多模态主链已经可跑通，并有 `unittest` 回归覆盖。
- `test_mvp.py` 已覆盖 text / audio / image / video / tabular 主路径。
- `test_v2_schema_and_corpus.py` 已覆盖 corpus、publication、quality、review artifacts 落盘。
- 当前最弱环节不是主链能力，而是 API 外部化前的 hardening：auth、request validation、rate limiting、logging/trace、repository abstraction。

## 目录骨架

```text
./README.md
./docs/
./src/
./apps/
./examples/
./skills/
./tests/
```
