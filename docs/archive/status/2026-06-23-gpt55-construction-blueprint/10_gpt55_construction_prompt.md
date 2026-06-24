# GPT5.5 施工总提示词

以下内容可直接交给 GPT5.5 / 代码工程模型作为施工任务上下文。

---

## 任务背景

你正在维护 `omni_skill_pipeline` 项目。该项目的目标是把文本、PDF/代码、音频、图片、视频等多模态输入，转化为可复用、可追溯、可审核的技能工件，例如 `SKILL.md`、`skill.json`、`SkillGraph`、发布包和验收 manifest。它是一个“技能生产流水线”：输入材料，经过抽取、整理、质量检查、发布打包，最终形成可被不同 Agent 使用的能力包。

当前版本为 `v0.2.5-internal.2`，只能定位为内部 dogfood。外部 Beta/GA 仍 HOLD。

## 总体目标

把项目推进到：

```text
v0.2.6-internal.3 = 自证闭环版本
```

必须优先修复 P0，不要先做 GUI/K8s/复杂新功能。

## 已确认问题

### P0

1. 真实样本闭环不足：launch-gate eligible loops = 0/10。
2. `distill -> export -> validate` 闭环失败：fresh export 后 `validate-skill` 报 `REVIEW_APPROVAL_MISSING`。
3. release artifact 在普通源码包形态下不可复现：`git archive failed: not a git repository`。

### P1

1. Python 版本声明过宽：`requires-python >=3.11`，但 Python 3.13 依赖安装路径不顺。
2. 全量 CI 稳定性未独立证明。
3. `script-name-map.md` 没有覆盖所有 `scripts/*.py`。
4. agent smoke 当前更像记录矩阵，不是全部 Agent 真实运行证据。
5. OCR/image/video 能跑但质量未达生产级。

## 施工优先级

### 第一优先级：修复导出校验闭环

必须让以下命令链通过：

```bash
omni-skill distill-text --title "Demo Text" --file examples/text_note.md
omni-skill export-skill --bundle skills/drafts/<generated-slug>/bundle.json --target portable --output-root /tmp/omni_export
omni-skill validate-skill --package /tmp/omni_export/skills/portable/<generated-slug>
```

期望：

```text
status=pass
```

修复要求：明确 review/lifecycle source of truth；`review_task.json`、`bundle.json`、`agent_skill_package.json` 状态一致；`auto_publish` 不得导致最终导出包仍是 `draft`；validator 不得通过删除 `REVIEW_APPROVAL_MISSING` 来伪修复；增加正反向测试。

重点文件可能包括：

```text
src/omni_skill_pipeline/cli.py
src/omni_skill_pipeline/models.py
src/omni_skill_pipeline/assembly/lifecycle.py
src/omni_skill_pipeline/exporters/agent_skill_exporter.py
src/omni_skill_pipeline/publication/portable_skill_renderer.py
src/omni_skill_pipeline/validation/skill_usability.py
src/omni_skill_pipeline/review/packet.py
```

请以实际源码定位为准。

### 第二优先级：修复 release artifact 可复现性

当前失败原因是普通源码包不是有效 Git 仓库。请支持 source tree fallback，或至少强文档约束。

推荐实现：

```text
if git archive unavailable:
    create source archive from current source tree
    exclude .git, .venv, __pycache__, dist, build, .pytest_cache, *.pyc
    record source_archive_mode=source_tree_fallback in release_manifest.json
```

验收命令：

```bash
python -m pip wheel . --no-deps --wheel-dir dist
python scripts/release_artifacts.py --release-id local-source-tree-test --output-dir /tmp/omni_release --dist-dir dist --coverage-xml coverage.xml
python scripts/release_consumer_smoke.py --release-dir /tmp/omni_release --expected-release-id local-source-tree-test
```

### 第三优先级：收紧 Python 支持矩阵

如果不真正支持 Python 3.13，请改为：

```toml
requires-python = ">=3.11,<3.13"
```

并更新 README、testing docs、CI matrix。如果选择支持 Python 3.13，则必须升级依赖约束并让 3.13 CI 通过。

### 第四优先级：补齐 script-name-map

所有 `scripts/*.py` 必须进入 `docs/latest/operations/script-name-map.md`。至少补入：`gl63_real_loop_intake_workpack.py`、`gl64_real_loop_manifest_preflight.py`、`internal_dogfood_smoke.py`、`internal_launch_gate.py`、`release_artifacts.py`、`release_consumer_smoke.py`。同时增强 `scripts/doc_sync.py`：如果新增脚本未被 script-name-map 记录，则 CI 失败。

### 第五优先级：补真实样本闭环

补齐 10 条真实 loop，覆盖 text/audio/image/video。每条必须有 source bundle ref、source hash、business expectation、run command、run evidence、human review、agent smoke evidence、sanitized manifest。

验收：

```bash
python scripts/gl64_real_loop_manifest_preflight.py --fail-on-invalid --fail-on-pending --print-json
python scripts/trial_metrics.py --manifest <real_manifest> --fail-on-ga-blocker --print-summary
python scripts/launch_gate.py --max-evidence-age-hours <N> --print-json
```

期望：

```text
missing=0
invalid=0
launch_gate_eligible_complete_loops>=10
modalities include text,audio,image,video
GA blockers=no
Launch readiness decision=READY
```

## 禁止事项

不允许：只改 README 不改代码；删除 gate/check 来制造 ready；把 fixture/mock/demo 伪装成真实 loop；把 `not_run` agent smoke 计为 pass；让 draft package 默认 validate pass；删除 `REVIEW_APPROVAL_MISSING` 逻辑；跳过 release consumer smoke；扩展新功能绕开 P0；将 Python 支持写成 `>=3.11` 但只测试 3.11；把 OCR 乱码清洗成看似正确的事实。

## 最终交付要求

每个修复 PR 必须包含代码修改、单元测试/集成测试、CLI 验收命令、文档更新、失败模式说明、release/launch gate 影响说明。

最终提交前运行：

```bash
python -m pip install -e '.[dev]'
pytest
python scripts/doc_sync.py --output -
omni-skill distill-text --title "Demo Text" --file examples/text_note.md
omni-skill export-skill --bundle <bundle.json> --target portable --output-root /tmp/omni_export
omni-skill validate-skill --package /tmp/omni_export/skills/portable/<slug>
python -m pip wheel . --no-deps --wheel-dir dist
python scripts/release_artifacts.py --release-id local-test --output-dir /tmp/release --dist-dir dist --coverage-xml coverage.xml
python scripts/release_consumer_smoke.py --release-dir /tmp/release --expected-release-id local-test
```

只有上述通过后，才可以继续做真实样本闭环与 external beta 准备。
