# 变更日志

## 2026-06-20

### v0.2.5-internal.2

- 新增中文真实数据接入与验收手册，约定后续真实原始数据放在本地 `data/real-inputs/<batch-id>/`，仓库只提交脱敏后的真实闭环 manifest。
- 明确 10 个 GL-63 manifest 槽位、4 个目标模态、单槽位单 loop、source trace、review trace 和 agent smoke 记录的验收要求。
- 将当前没有真实业务数据时的发布口径收敛为内部 dogfood 或内部玩具，不声明外部 Beta、GA、SaaS 或生产可用。
- 补齐内部 dogfood 与真实数据接入预案归档，并将 README、latest 操作入口、runbook 索引、release note 和主索引更新到 `v0.2.5-internal.2`。
- 将 package metadata 版本更新为 `0.2.5`，服务于本轮内部 release package。
- 修复 release artifact 测试对旧版本号 `0.2.4` 的硬编码，使发版 workflow 能跟随 `pyproject.toml` 版本推进；`v0.2.5-internal.2` 取代未成功发布的 `v0.2.5-internal.1` tag。

### v0.2.4-internal.1

- 将当前操作入口、runbook、环境变量、测试说明、归档入口和发布入口整理为面向中文工程师的一线文档。
- 新增 `v0.2.4-internal.1` 中文发布说明，明确本轮 release 是文档与发布记录补齐，不新增外部 Beta、GA、SaaS 或生产部署承诺。
- 新增中文文档与发布记录归档，说明本轮核验没有发现需要从 `latest/working/releases` 迁移到 `archive` 的孤立历史文档。
- 将 README、`docs/latest/`、`docs/releases/`、`docs/archive/` 的版本索引更新到 `v0.2.4-internal.1` 发版候选。

## 2026-06-19

### v0.2.3-internal.1

- 为 file-backed artifact 增加可选 Fernet 加密 envelope。
- 增加 artifact 加密环境变量配置和 service factory wiring。
- 保持默认明文兼容；只有显式启用加密时才写入加密 envelope。
- 增加加密 review queue 连续性测试和缺 key 失败行为覆盖。
- 补充本地 dogfood artifact 加密启用方式和 release 边界说明。

### v0.2.2-internal.1

- 修复 internal dogfood API smoke payload 与当前 schema 的兼容性。
- 为 `scripts/internal_dogfood_smoke.py` 增加 JSON 和 Markdown 输出。
- 增加 live API dogfood smoke 证据，覆盖 health、template、text distill 和 review queue trace。
- 让 FastAPI OpenAPI version metadata 与 package version 对齐。
- 刷新 broad launch readiness 和 internal dogfood readiness 证据。

### v0.2.1-internal.1

- 将 `SKILL.template.md` 和 `skill.schema.json` 打入 Python wheel，修复 installed-wheel 场景下的 `show-template`。
- 为非源码仓安装场景增加 packaged-contract fallback。
- 增加 `scripts/release_consumer_smoke.py`，验证 release checksum、manifest contract、wheel 安装和 installed CLI template 访问。
- 在 `Release` workflow 的 artifact 上传和发布前加入 consumer smoke。
- 增加 `v0.2.1-internal.1` 发布说明。

## 2026-04-19

### 文档

- 增加根目录 `README.md`，作为唯一根级入口文档。
- 将 architecture 和 contracts 移入当时的当前文档层，后续该层重命名为 `docs/latest/`。
- 增加 `docs/INDEX.md`。
- 增加 `docs/working/status/CURRENT_STATUS.md`。
- 增加 `docs/releases/CHANGELOG.md`。

### 项目骨架

- 增加 Python project metadata 和 package layout。
- 增加 API entry、worker entry、repository、renderer、service 和 schema modules。

### Skill 契约

- 增加 `skill.schema.json`。
- 增加 `SKILL.template.md`。
- 增加 schema export script。

### 蒸馏流水线

- 增加 adapter、provider、insight extraction 和 skill composition 的可插拔接口。
- 增加 heuristic insight extractor 和 heuristic skill composer。
- 增加 composer/provider fallback 策略。

### 输入 Adapter

- 增加 text adapter。
- 增加 audio adapter。
- 增加 image adapter。
- 增加 video adapter。
- 增加 tabular/time-series adapter。

### Provider 集成

- 增加 OpenAI ASR / LLM / Vision providers。
- 增加 Tesseract OCR provider。
- 增加 FFmpeg / FFprobe media processor。

### 视频能力改进

- 增加基于 `ffprobe` 的视频探测。
- 增加 scene-based candidate sampling。
- 增加长视频 adaptive interval sampling。
- 增加短视频 fallback frame extraction。
- 增加 perceptual hash frame deduplication。
- 增加跨 timeline bucket 的 distributed frame selection。

### 结构化数据改进

- 增加 schema、missingness、entity summary、numeric profile 和 time-series anomaly 证据生成。
- 将 tabular 输出统一为 `EvidenceUnit`，使用 `TABLE / METRIC / EVENT` content types。

## 2026-04-20

### 架构

- 增加 `docs/latest/architecture/skill-distillation-v2.md`，记录当前诊断、V2 目标架构、领域模型演进和架构决策。
- 增加 `docs/working/architecture/skill-distillation-v2-roadmap.md`，定义未来实施的分阶段步骤、验收标准和迁移约束。
- 增加 `docs/working/architecture/skill-distillation-v2-implementation-backlog.md`，枚举 V2 开发 backlog、task packages、文件触点、依赖和验收标准。
- 增加 `docs/working/architecture/skill-distillation-v2-work-orders.md`，将 E1+ backlog 转换为可直接执行的施工单。
- 更新 `README.md`、`docs/working/status/CURRENT_STATUS.md`、`docs/latest/architecture/ARCHITECTURE.md` 和 `docs/INDEX.md`，暴露新的 V2 设计文档。

### 状态

- 增加 `docs/working/status/baselines/README.md`，作为 E0 baseline pack 入口。
- 增加 `docs/working/status/baselines/e0-sample-inventory.md`，枚举当前 baseline samples 和已知覆盖缺口。
- 增加 `docs/working/status/baselines/e0-baseline-2026-04-20.md`，记录实际 baseline replay 命令、观察输出和结论。
- 增加 `docs/working/status/baselines/evaluation-rubric.md`，定义未来 V2 对比的通用评估指标。
- 增加 `docs/working/status/baselines/e0-baseline-manifest.json`，作为机器可读 baseline manifest。
- 记录当前 MVP 测试套件已通过 `python -m unittest discover -s tests -p 'test_mvp.py'`。
