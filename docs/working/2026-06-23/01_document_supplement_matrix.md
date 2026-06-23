# 文档补充矩阵：哪些缺口需要额外文档

## 1. 目的

本文件用于把评估中发现的每一个问题拆解为：

- 是否需要额外文档；
- 需要什么文档；
- 文档应服务于谁；
- 文档最低应包含什么；
- 该文档如何验收。

原则：

> 只要一个能力需要 GPT5.5 或工程模型继续施工，就必须把目标、边界、命令、证据、验收标准写清楚。否则后续模型会继续“看似修复，实际绕路”。

## 2. 总体矩阵

| 编号 | 问题/能力 | 是否需要额外文档 | 文档位置 | 原因 | 优先级 |
|---|---|---:|---|---|---|
| D-01 | 项目总体迭代路线 | 是 | `00_iteration_blueprint.md` | 需要统一版本定位与施工顺序 | P0 |
| D-02 | `distill -> export -> validate` 闭环失败 | 是 | `02_p0_export_validate_closure.md` | 属于代码与文档共同缺陷，必须给出 source of truth | P0 |
| D-03 | 10 条真实样本闭环证据 | 是 | `03_p0_real_loop_evidence_spec.md` | 外部 Beta/GA 最大阻塞项 | P0 |
| D-04 | release artifact 可复现 | 是 | `04_p0_release_artifact_reproducibility.md` | 附件源码包形态运行失败，需明确修复路线 | P0 |
| D-05 | Python 支持矩阵与 CI | 是 | `05_p1_python_ci_matrix.md` | `>=3.11` 声明过宽，依赖实际不一致 | P1 |
| D-06 | 脚本地图与操作文档 | 是 | `06_p1_script_doc_map.md` | 当前关键脚本未被 script-name-map 覆盖 | P1 |
| D-07 | agent smoke 真实运行证据 | 是 | `07_p1_agent_smoke_real_evidence.md` | 当前更像记录矩阵，不等于 agent 实跑 | P1 |
| D-08 | OCR/ASR/image/video 质量门禁 | 是 | `08_p1_multimodal_quality_gate.md` | 多模态能跑但质量未达生产级 | P1 |
| D-09 | Docker/Postgres/K8s/密钥管理 | 是 | `09_p2_productionization_roadmap.md` | 属于生产增强，需阶段化而非一口吃掉 | P2 |
| D-10 | GPT5.5 施工总提示词 | 是 | `10_gpt55_construction_prompt.md` | 便于直接交给工程模型执行 | P0 |
| D-11 | GUI/Web/API Console 产品形态 | 暂缓，后续需要 | 可追加 `11_product_surface_spec.md` | 当前首要任务是闭环，不应过早扩产品面 | P2 |
| D-12 | 性能/并发/队列压测 | 暂缓，后续需要 | 可追加 `12_perf_and_scale_spec.md` | 当前功能正确性与证据闭环优先 | P2 |
| D-13 | 治理/删除/留存策略 | 局部需要 | 可并入生产安全文档 | 当前有 governance 基础，但生产合规还不足 | P2 |
| D-14 | 用户 Beta 操作手册 | 后续需要 | 可追加 `13_beta_user_runbook.md` | 只有进入 external beta 前才需要 | P2 |

## 3. 哪些现有文档可以继续沿用

以下文档方向是有价值的，不建议推倒重写：

| 现有文档/方向 | 处理建议 |
|---|---|
| CLI 操作文档 | 保留，补充导出校验失败修复后的流程 |
| testing 操作文档 | 保留，增加 Python 版本矩阵和全量 CI 证据要求 |
| real-data intake runbook | 保留，按真实 loop evidence spec 加强 |
| CURRENT_STATUS | 保留，但需同步真实状态和 P0 blocker |
| release notes | 保留，但不要暗示 Beta ready |
| launch gate 文档 | 保留，补充 eligible loop 与 fixture loop 的区别 |
| agent smoke 文档 | 保留，但必须强调 `not_run` 不能作为 Beta 证据 |

## 4. 哪些文档必须新增或重写

### 4.1 必须新增：导出校验闭环文档

原因：当前 `export-skill` 能生成包，但 `validate-skill` 对 fresh export 报 `REVIEW_APPROVAL_MISSING`。这不是简单测试缺失，而是生命周期状态模型不清楚。

文档必须定义：

- review 状态有哪些；
- auto publish 是否等于 approved；
- `review_task.json`、`bundle.json`、`agent_skill_package.json` 谁是 source of truth；
- validator 应该看哪个字段；
- draft、approved、published、rejected 各自能否导出；
- portable package 是否允许 draft 包通过校验。

### 4.2 必须新增：真实样本闭环证据规范

原因：当前 10 条 controlled trial 是 fixture，不是真实业务 loop。外部 Beta/GA 卡在这里。

文档必须定义：

- 10 条 loop 的 slot 分配；
- source bundle 本地保存规则；
- 脱敏 manifest schema；
- human review schema；
- run evidence schema；
- agent smoke evidence schema；
- 不合格 evidence 的判定标准。

### 4.3 必须新增：release artifact 可复现文档

原因：当前源码包运行 release artifact 打包失败，原因是依赖 Git 仓库。必须明确构建前置条件或实现 fallback。

文档必须定义：

- Git checkout 模式；
- source tarball 模式；
- build outputs；
- checksums；
- release manifest；
- consumer smoke；
- 失败码和排查路径。

### 4.4 必须新增：脚本地图完整性文档

原因：当前 doc sync 通过，但 `script-name-map.md` 没有覆盖所有脚本，说明 doc sync 规则不足。

文档必须定义：

- 每个 `scripts/*.py` 必须被索引；
- 每个脚本至少有 purpose、inputs、outputs、examples、failure modes；
- doc sync 必须自动扫描脚本清单；
- 任何新增脚本必须同时更新 script-name-map。

## 5. 文档验收规则

每个补充文档完成后，必须满足以下条件：

1. 读者不看源码，也能知道该能力是做什么的。
2. 读者能复制其中命令运行。
3. 每个命令都有预期输出或判定规则。
4. 每个失败模式都有处理方式。
5. 每个文档都说明对应的 P0/P1/P2 风险。
6. 每个文档都说明何时可以认为该项完成。
7. 每个文档都能被 GPT5.5 用作施工上下文。

## 6. 对后续工程模型的要求

后续 GPT5.5 施工时，必须遵守：

- 不允许只修改 README；
- 不允许只让测试 mock 通过；
- 不允许把 `not_run` 包装成 pass；
- 不允许把 fixture loop 当真实 loop；
- 不允许删除 launch gate 阻塞项来制造 ready；
- 不允许扩大功能面绕开 P0；
- 任何修复都必须附测试、文档、验收命令。
