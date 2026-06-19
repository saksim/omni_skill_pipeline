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
python scripts/ci.py
```

## 入口

- Package root: `src/omni_skill_pipeline/`
- CLI entry: `src/omni_skill_pipeline/cli.py`
- API app: `apps/api/main.py`
- Worker app: `apps/worker/main.py`
- Template contract: `docs/latest/contracts/SKILL.template.md`
- Skill schema: `docs/latest/contracts/skill.schema.json`

## 文档导航

### Layers

- 总索引: [docs/INDEX.md](docs/INDEX.md)
- 最新已发布手册: [docs/latest/README.md](docs/latest/README.md)
- 当前迭代材料: [docs/working/README.md](docs/working/README.md)
- 发布记录: [docs/releases/README.md](docs/releases/README.md)
- 历史归档: [docs/archive/README.md](docs/archive/README.md)

### Latest

- 架构入口: [docs/latest/architecture/ARCHITECTURE.md](docs/latest/architecture/ARCHITECTURE.md)
- V2 设计: [docs/latest/architecture/skill-distillation-v2.md](docs/latest/architecture/skill-distillation-v2.md)
- 运行文档入口: [docs/latest/operations/OPERATIONS.md](docs/latest/operations/OPERATIONS.md)
- API: [docs/latest/operations/api.md](docs/latest/operations/api.md)
- CLI: [docs/latest/operations/cli.md](docs/latest/operations/cli.md)
- Environment: [docs/latest/operations/env.md](docs/latest/operations/env.md)
- Testing: [docs/latest/operations/testing.md](docs/latest/operations/testing.md)

### Working

- 当前状态: [docs/working/status/CURRENT_STATUS.md](docs/working/status/CURRENT_STATUS.md)
- V2 路线图: [docs/working/architecture/skill-distillation-v2-roadmap.md](docs/working/architecture/skill-distillation-v2-roadmap.md)
- V2 开发拆解: [docs/working/architecture/skill-distillation-v2-implementation-backlog.md](docs/working/architecture/skill-distillation-v2-implementation-backlog.md)
- V2 施工任务单: [docs/working/architecture/skill-distillation-v2-work-orders.md](docs/working/architecture/skill-distillation-v2-work-orders.md)
- 试运行与发布基线: [docs/working/status/baselines/README.md](docs/working/status/baselines/README.md)

### Releases And Archive

- Changelog: [docs/releases/CHANGELOG.md](docs/releases/CHANGELOG.md)
- V2 release switch standard: [docs/releases/standards/v2-release-switch-standard.md](docs/releases/standards/v2-release-switch-standard.md)
- 评估归档入口: [docs/archive/assessments/glm-5.1-project-assessment.md](docs/archive/assessments/glm-5.1-project-assessment.md)

## 当前工程判断

- 多模态主链已经可跑通，并有 `unittest` 回归覆盖。
- 最新 Linux release run 已达到 `GO`，当前目标从补 Beta 阻断项调整为受控业务试运行。
- `test_mvp.py` 已覆盖 text / audio / image / video / tabular 主路径。
- `test_v2_schema_and_corpus.py` 已覆盖 corpus、publication、quality、review artifacts 落盘。
- API schema validation、auth、rate limiting、error contract、trace context、review queue、worker retry/idempotency、Postgres repository 与 release gate 已逐步落地。
- 受控业务试运行阶段要求限制客户/团队、限制多模态场景、限制数据范围，所有产物默认人工 REVIEW。
- 短期最弱环节不是主链能力，而是最后一公里：需要把内部 `SkillDocument / SkillGraph` 稳定编译成 Codex / Claude Code / OpenCode 可发现、可触发、可执行的 agent skill package，并用真实业务闭环证明质量。
- 广义产品上线不再沿用旧 L1/L2 缺口清单直接开工；后续以 `GL-*` 任务组推进受控外部 Beta、单团队 GA review 和平台化能力建设。
- 广义产品上线 readiness gate 已落地：`python scripts/launch_gate.py --output - --summary-output -` 会输出 `HOLD` / `READY_FOR_CONTROLLED_BETA` 等机器可读判定；当前仓库仍因 trial 覆盖不足保持 `HOLD`。

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
