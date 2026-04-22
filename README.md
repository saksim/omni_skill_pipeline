# Omni Skill Pipeline

将多模态输入蒸馏为可复用、可追溯、可演化的 `SKILL.md` 技能体系。

## 判词

这不是“文件转 Markdown 工具”，而是一个 `Evidence -> Skill` 的知识蒸馏内核。

当前已接入的输入域：

- 文本：`txt / md / markdown / rst / log / json / html / doc / docx / pdf`
- 音频：`audio -> transcript -> skill`
- 图像：`image -> OCR + scene -> skill`
- 视频：`video -> audio + shot/keyframe + OCR + scene -> skill`
- 表格/时间序列：`tabular/time-series -> TABLE / METRIC / EVENT -> skill`

## 入口

- Python interpreter: `D:\code_environment\anaconda_all_css\py311\python.exe`
- Package root: `src/omni_skill_pipeline/`
- API app: `apps/api/main.py`
- Worker app: `apps/worker/main.py`

## 文档导航

### Current

- 文档总索引: [docs/INDEX.md](D:\download\gaming\new_program\data_helper\3_omni_skill_pipeline\docs\INDEX.md)
- 架构入口: [docs/current/architecture/ARCHITECTURE.md](D:\download\gaming\new_program\data_helper\3_omni_skill_pipeline\docs\current\architecture\ARCHITECTURE.md)
- V2 设计: [docs/current/architecture/skill-distillation-v2.md](D:\download\gaming\new_program\data_helper\3_omni_skill_pipeline\docs\current\architecture\skill-distillation-v2.md)
- V2 路线图: [docs/current/architecture/skill-distillation-v2-roadmap.md](D:\download\gaming\new_program\data_helper\3_omni_skill_pipeline\docs\current\architecture\skill-distillation-v2-roadmap.md)
- V2 开发拆解: [docs/current/architecture/skill-distillation-v2-implementation-backlog.md](D:\download\gaming\new_program\data_helper\3_omni_skill_pipeline\docs\current\architecture\skill-distillation-v2-implementation-backlog.md)
- V2 施工任务单: [docs/current/architecture/skill-distillation-v2-work-orders.md](D:\download\gaming\new_program\data_helper\3_omni_skill_pipeline\docs\current\architecture\skill-distillation-v2-work-orders.md)
- 系统总览: [docs/current/architecture/system-overview.md](D:\download\gaming\new_program\data_helper\3_omni_skill_pipeline\docs\current\architecture\system-overview.md)
- 数据流: [docs/current/architecture/data-flow.md](D:\download\gaming\new_program\data_helper\3_omni_skill_pipeline\docs\current\architecture\data-flow.md)
- Provider: [docs/current/architecture/providers.md](D:\download\gaming\new_program\data_helper\3_omni_skill_pipeline\docs\current\architecture\providers.md)
- 存储: [docs/current/architecture/storage.md](D:\download\gaming\new_program\data_helper\3_omni_skill_pipeline\docs\current\architecture\storage.md)
- E0 基线包: [docs/current/status/baselines/README.md](D:\download\gaming\new_program\data_helper\3_omni_skill_pipeline\docs\current\status\baselines\README.md)
- 契约: [docs/current/contracts/skill.schema.json](D:\download\gaming\new_program\data_helper\3_omni_skill_pipeline\docs\current\contracts\skill.schema.json)
- 模板: [docs/current/contracts/SKILL.template.md](D:\download\gaming\new_program\data_helper\3_omni_skill_pipeline\docs\current\contracts\SKILL.template.md)
- 当前状态: [docs/current/status/CURRENT_STATUS.md](D:\download\gaming\new_program\data_helper\3_omni_skill_pipeline\docs\current\status\CURRENT_STATUS.md)
- 运行入口: [docs/current/operations/OPERATIONS.md](D:\download\gaming\new_program\data_helper\3_omni_skill_pipeline\docs\current\operations\OPERATIONS.md)
- CLI: [docs/current/operations/cli.md](D:\download\gaming\new_program\data_helper\3_omni_skill_pipeline\docs\current\operations\cli.md)
- API: [docs/current/operations/api.md](D:\download\gaming\new_program\data_helper\3_omni_skill_pipeline\docs\current\operations\api.md)
- Worker: [docs/current/operations/worker.md](D:\download\gaming\new_program\data_helper\3_omni_skill_pipeline\docs\current\operations\worker.md)
- Environment: [docs/current/operations/env.md](D:\download\gaming\new_program\data_helper\3_omni_skill_pipeline\docs\current\operations\env.md)
- Testing: [docs/current/operations/testing.md](D:\download\gaming\new_program\data_helper\3_omni_skill_pipeline\docs\current\operations\testing.md)

### History

- 变更历史: [docs/history/CHANGELOG.md](D:\download\gaming\new_program\data_helper\3_omni_skill_pipeline\docs\history\CHANGELOG.md)

## 当前能力

- 可插拔 Adapter / Provider / Composer 架构
- OpenAI ASR / LLM / Vision provider
- Tesseract OCR provider
- FFmpeg / FFprobe 视频处理链
- 本地工件仓储：`skill.json / SKILL.md / evidence.json / bundle.json`

## 当前目录

```text
./README.md
./docs/
./src/
./apps/
./examples/
./skills/
```

## 下一跳

- 看设计细节：去 `docs/current/architecture/`
- 看运行方法：去 `docs/current/operations/`
- 看当前进度：去 `docs/current/status/`
- 看契约定义：去 `docs/current/contracts/`
