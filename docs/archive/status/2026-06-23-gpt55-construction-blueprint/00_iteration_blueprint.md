# Omni Skill Pipeline 迭代蓝图总览

## 1. 项目定位

当前项目的目标是把文本、PDF/代码、音频、图片、视频等多模态输入，转化为可复用、可追溯、可审核的技能工件，例如：

- `SKILL.md`
- `skill.json`
- `SkillGraph`
- 发布包
- 验收 manifest
- agent smoke 记录
- launch gate 证据

它本质上不是普通的“文档生成器”，而是一个“技能生产流水线”：输入材料，经过抽取、整理、质量检查、发布打包，最终形成可被不同 Agent 使用的能力包。

## 2. 本次评估的总体结论

对项目当前状态的判断如下：

| 维度 | 结论 |
|---|---|
| 内部 dogfood | 基本可用，但仍需修复一致性问题 |
| 外部 Beta | HOLD |
| GA / SaaS / 生产级 | 不具备 |
| 多模态核心 CLI | 代表性路径可运行 |
| 真实数据闭环 | 未完成，launch-gate eligible 为 0/10 |
| 发布产物闭环 | GitHub checkout 环境下可能可行，附件源码包形态不可复现 |
| 操作文档 | 主体较完整，但不是全量完整 |
| 是否做到极致 | 没有，仍有明显工程、证据、质量、部署、安全缺口 |

## 3. 已确认可运行的能力

本次评估中，代表性路径显示以下能力可以运行：

| 能力 | 状态 | 说明 |
|---|---|---|
| `omni-skill --help` | 可运行 | CLI 入口存在 |
| `distill-text` | 可运行 | 能从文本生成技能草稿 |
| `distill-audio` | 可运行 | transcript-first 路径成立 |
| `distill-image` | 可运行 | 但 OCR 输出质量一般 |
| `distill-tabular` | 可运行 | 能做基础 profiling/insight |
| `distill-video` | 可运行 | 依赖 transcript/keyframe/OCR，理解质量偏 dogfood |
| `distill-corpus` | 可运行 | 能汇总多资产生成 corpus 工件 |
| `export-skill` | 可运行 | 能导出 portable/agent package |
| `doc_sync` | 可运行 | 当前规则内 13 项通过 |
| `gl64_real_loop_manifest_preflight` | 可运行 | 非严格模式能输出 pending/missing 状态 |
| `trial_metrics` | 可运行 | 结论阻塞 GA |
| `launch_gate` | 可运行 | 结论 HOLD |
| `agent_smoke --validate-matrix` | 可运行 | 记录矩阵完整，但不是所有 agent 实跑 |
| wheel build | 可运行 | `python -m pip wheel . --no-deps` 可生成 wheel |

## 4. 已确认的关键缺口

### 4.1 P0：直接阻塞外部 Beta 的缺口

| 编号 | 缺口 | 当前影响 | 目标状态 |
|---|---|---|---|
| P0-1 | 真实样本闭环不足 | launch-gate eligible loops = 0/10 | 完成 10 条覆盖 text/audio/image/video 的真实闭环 |
| P0-2 | 导出后校验失败 | `export-skill` 成功但 `validate-skill` 报 `REVIEW_APPROVAL_MISSING` | `distill -> export -> validate` 一条链路通过 |
| P0-3 | release artifact 源码包形态不可复现 | `git archive failed: not a git repository` | Git checkout 与源码包两种形态都可构建，或文档强约束环境 |

### 4.2 P1：阻碍工程可信度的缺口

| 编号 | 缺口 | 当前影响 | 目标状态 |
|---|---|---|---|
| P1-1 | Python 版本声明过宽 | `requires-python >=3.11` 但 Python 3.13 依赖安装路径不顺 | 明确支持 3.11/3.12，或真正适配 3.13 |
| P1-2 | 全量 CI 稳定性未独立证明 | 当前环境未能完整跑完全量 829 tests | 标准 Python 3.11/3.12 下提供完整 CI 证据 |
| P1-3 | 脚本文档地图不完整 | 关键脚本缺失于 script-name-map | 所有 `scripts/*.py` 均有文档映射 |
| P1-4 | agent smoke 不是真实全量运行 | 记录矩阵完整，但 2 个 `not_run` | 三类 Agent 均有真实运行证据 |
| P1-5 | OCR/image/video 质量未达生产级 | 能跑，但输出噪声明显 | 引入多模态质量门禁和失败兜底 |

### 4.3 P2：生产化增强

| 编号 | 缺口 | 当前影响 | 目标状态 |
|---|---|---|---|
| P2-1 | Docker real smoke 未闭环 | 当前仅 dry-run 可验证 | Docker build/run/health/logs/cleanup 全链路通过 |
| P2-2 | Postgres/dual-write 生产验证不足 | 仍偏工程预留 | 持久化、迁移、回滚、soak 测试可验收 |
| P2-3 | K8s/生产部署缺失 | 无生产部署闭环 | Helm/Kustomize、readiness、liveness、autoscaling |
| P2-4 | 生产级密钥管理缺失 | API key/ASR/OCR/provider secret 不适合生产 | Vault/KMS/Secret Manager 集成 |
| P2-5 | 产品形态未闭环 | CLI 有，Web/GUI/API console 不完整 | 明确 Beta 产品入口和用户流程 |

## 5. 推荐版本路线

### 当前版本定位

```text
v0.2.5-internal.2 = 内部 dogfood 版本
```

允许：

- 内部试跑；
- 固定样例演示；
- 受控工程验证；
- 针对真实样本采集证据。

不允许：

- 宣称外部 Beta ready；
- 宣称 GA；
- 宣称生产级多模态理解；
- 宣称所有 Agent 已真实验证；
- 宣称 Docker/Postgres/K8s/密钥管理已完成生产闭环。

### 下一版目标

```text
v0.2.6-internal.3 = 自证闭环版本
```

必须完成：

1. `distill -> export -> validate` 全链路通过。
2. 10 条真实样本闭环证据齐全。
3. `launch_gate decision=READY` 或至少不存在真实闭环类 P0 blocker。
4. release artifact 在标准环境可复现。
5. script-name-map 全覆盖。
6. Python 支持矩阵明确。
7. agent smoke 不再主要依赖 `not_run` 记录。

### 后续 Beta 目标

```text
v0.3.0-beta.1 = controlled external beta
```

进入该阶段前，必须具备：

- 至少 10 条真实样本闭环；
- 至少 3 个外部候选用户场景；
- 失败工单与人工复核机制；
- 数据脱敏与 manifest 审计流程；
- 可复现 release artifact；
- Beta 用户操作手册；
- Agent 使用手册；
- 回滚方案。

## 6. 总体施工顺序

建议严格按以下顺序推进。

### 阶段 A：先修自证闭环

1. 修复 `export-skill` 与 `validate-skill` 状态不一致。
2. 修复 release artifact 可复现性。
3. 收紧 Python 版本矩阵。
4. 确认标准 Python 3.11/3.12 全量测试。

### 阶段 B：补真实样本证据

1. 设计 10 条真实样本闭环。
2. 采集 source bundle，但不入库。
3. 提交脱敏 manifest。
4. 运行 GL-64 preflight。
5. 运行 trial metrics。
6. 运行 launch gate。

### 阶段 C：补文档与 Agent 证据

1. 补全 script-name-map。
2. 补全所有脚本 runbook。
3. 完成三类 Agent 真实 smoke。
4. 为每条真实 loop 关联 agent smoke evidence。

### 阶段 D：产品化与生产化

1. Docker real smoke。
2. Postgres/dual-write soak。
3. Secret 管理。
4. API/Web/GUI 入口。
5. 多租户与权限。
6. 性能压测与可观测性。

## 7. 总体验收门槛

下一版最小验收命令建议如下：

```bash
python -m pip install -e '.[dev]'
pytest
python scripts/doc_sync.py --output -
python scripts/gl64_real_loop_manifest_preflight.py --fail-on-invalid --fail-on-pending
python scripts/trial_metrics.py --manifest <real_manifest> --fail-on-ga-blocker
python scripts/launch_gate.py --max-evidence-age-hours <N> --print-json
python -m pip wheel . --no-deps --wheel-dir dist
python scripts/release_artifacts.py --release-id local-test --output-dir /tmp/release --dist-dir dist --coverage-xml coverage.xml
python scripts/release_consumer_smoke.py --release-dir /tmp/release --expected-release-id local-test
```

核心 CLI 自证链路：

```bash
omni-skill distill-text --title "Demo Text" --file examples/text_note.md
omni-skill export-skill --bundle <bundle.json> --target portable --output-root /tmp/omni_export
omni-skill validate-skill --package /tmp/omni_export/skills/portable/<slug>
```

期望：

```text
status=pass
launch_gate decision=READY
0 missing real loop manifest
0 invalid real loop manifest
0 P0 blocker
```

## 8. 施工原则

1. 不要再做泛泛“功能增强”。先修闭环。
2. 所有能力必须有命令、输出、失败码、证据路径。
3. 所有真实样本必须脱敏，真实 source bundle 不入 repo。
4. 所有文档必须能反向驱动命令运行。
5. 所有 claimed feature 必须至少有一个 smoke 或 test。
6. 任何 `not_run` 只能用于内部解释，不能作为 Beta readiness 证据。
7. 所有 release artifact 必须可复现。
8. 所有版本支持必须以 CI 矩阵为准，而不是 pyproject 单行声明。
