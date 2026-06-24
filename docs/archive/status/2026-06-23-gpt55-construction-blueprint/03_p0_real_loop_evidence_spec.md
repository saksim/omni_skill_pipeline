# P0：真实样本闭环证据规范

## 1. 背景

当前项目最大的外部 Beta/GA 阻塞项是缺少真实闭环证据。评估中确认：

```text
launch_gate_eligible_complete_loops = 0
launch_gate_eligible_modalities = 0
```

项目中虽然已有 controlled trial loop，但 evidence origin 为 fixture，不可作为真实业务闭环。

因此下一阶段必须补齐 10 条覆盖 text/audio/image/video 的真实样本闭环。

## 2. 核心原则

1. 真实 source bundle 不进入 repo。
2. repo 只提交脱敏 manifest、摘要、哈希、证据路径。
3. 每条 loop 必须有业务期望、运行证据、人工审阅、Agent smoke、脱敏 manifest。
4. fixture/mock/demo 不能算 launch-gate eligible。
5. 每条 loop 必须可追溯、可审核、可复跑。

## 3. 10 条 loop slot 规划

建议最小覆盖如下：

| Slot | Modality | 场景建议 | 目标 |
|---|---|---|---|
| RL-001 | text | 真实业务文档/操作说明 | 验证文本抽取与 SKILL.md 生成 |
| RL-002 | audio | 真实会议/访谈转写 | 验证 transcript-first 音频路径 |
| RL-003 | image | 真实截图/流程图/告警图 | 验证 OCR 与图像摘要 |
| RL-004 | video | 真实操作录屏/培训视频 | 验证 transcript + keyframe 视频路径 |
| RL-005 | text | 代码 README/规范文档 | 验证代码/文档类技能沉淀 |
| RL-006 | audio | 客服/运维复盘录音转写 | 验证时间线和行动项抽取 |
| RL-007 | image | 多页面截图/图表 | 验证图表/界面内容抽取 |
| RL-008 | video | 系统操作 walkthrough | 验证关键帧去重与场景分段 |
| RL-009 | text | PDF 转文本后的业务材料 | 验证长文本/分层文档 |
| RL-010 | audio 或 video | 复杂多说话人转写 | 验证噪声与人工复核流程 |

最低要求：

```text
text >= 3
audio >= 3
image >= 2
video >= 2
```

## 4. 每条 loop 必备证据

每条真实闭环必须包含：

| 证据 | 是否入 repo | 说明 |
|---|---:|---|
| source bundle | 否 | 原始真实材料，放在受控本地/对象存储 |
| source hash | 是 | 用于证明材料版本，不暴露内容 |
| business expectation | 是，脱敏 | 人工定义期望产物与验收点 |
| run command | 是 | 实际执行的 CLI/API 命令 |
| run evidence | 是，脱敏 | 输出摘要、日志路径、产物路径、状态 |
| generated skill bundle | 可选，需脱敏 | 若含敏感内容只保留摘要和 hash |
| human review | 是，脱敏 | 人工审阅结果和结论 |
| agent smoke evidence | 是，脱敏 | Agent 使用技能包的证据 |
| sanitized manifest | 是 | GL-64/launch gate 使用 |

## 5. 推荐目录结构

真实数据不入库时，可以在本地或对象存储维护：

```text
real_loop_sources/
  RL-001/
    source_bundle/
    source_hashes.json
    raw_run_logs/
    generated_artifacts/
  RL-002/
    ...
```

repo 内只提交：

```text
docs/working/status/real-loop-manifests/
  RL-001.manifest.json
  RL-002.manifest.json
  ...
  RL-010.manifest.json

docs/working/status/real-loop-reviews/
  RL-001.review.json
  ...

docs/working/status/real-loop-evidence/
  RL-001.run.json
  RL-001.agent-smoke.json
  ...
```

## 6. Manifest schema 建议

每条 manifest 建议包含：

```json
{
  "loop_id": "RL-001",
  "modality": "text",
  "evidence_origin": "real_business_sample",
  "source_bundle_ref": "local-secure-store://real_loop_sources/RL-001/source_bundle",
  "source_hashes": [
    {
      "filename": "redacted-source.md",
      "sha256": "..."
    }
  ],
  "business_expectation_ref": "docs/working/status/real-loop-evidence/RL-001.expectation.md",
  "run_evidence_ref": "docs/working/status/real-loop-evidence/RL-001.run.json",
  "human_review_ref": "docs/working/status/real-loop-reviews/RL-001.review.json",
  "agent_smoke_ref": "docs/working/status/real-loop-evidence/RL-001.agent-smoke.json",
  "generated_bundle_hash": "...",
  "redaction_status": "passed",
  "pii_status": "no_raw_pii_in_repo",
  "review_status": "approved",
  "launch_gate_eligible": true,
  "created_at": "2026-06-23T00:00:00Z",
  "reviewed_at": "2026-06-23T00:00:00Z"
}
```

## 7. Business expectation 模板

```markdown
# RL-001 Business Expectation

## Source Summary

- Modality: text
- Domain: <domain>
- Source type: <runbook / meeting / screenshot / video / etc.>
- Sensitivity: <low / medium / high>

## Expected Skill Outcome

The generated skill should help an Agent perform:

1. <expected capability 1>
2. <expected capability 2>
3. <expected capability 3>

## Must Include

- <must-have instruction or concept>
- <must-have workflow>
- <must-have caveat>

## Must Not Include

- Raw PII
- Customer secrets
- Internal credentials
- Unredacted source text

## Acceptance Criteria

- SKILL.md captures the core reusable procedure.
- skill.json contains meaningful metadata.
- SkillGraph has traceable nodes/edges.
- Manifest links to source hash and review evidence.
- Human reviewer marks the output as approved.
```

## 8. Human review schema

```json
{
  "loop_id": "RL-001",
  "reviewer": "redacted-human-reviewer",
  "reviewed_at": "2026-06-23T00:00:00Z",
  "decision": "approved",
  "scores": {
    "faithfulness": 4,
    "reusability": 4,
    "traceability": 5,
    "safety_redaction": 5,
    "agent_usability": 4
  },
  "findings": [
    {
      "severity": "minor",
      "area": "SKILL.md",
      "note": "One procedural step could be more explicit."
    }
  ],
  "required_changes": [],
  "approval_notes": "Approved for internal launch-gate evidence."
}
```

分数建议：

| 分数 | 含义 |
|---:|---|
| 1 | 不可用 |
| 2 | 明显缺陷 |
| 3 | 可 dogfood，但不可 Beta |
| 4 | 可作为 Beta 候选证据 |
| 5 | 高质量证据 |

## 9. Run evidence schema

```json
{
  "loop_id": "RL-001",
  "command": "omni-skill distill-text --title ... --file ...",
  "environment": {
    "python": "3.11.x",
    "os": "linux",
    "package_version": "0.2.6-internal.3"
  },
  "started_at": "2026-06-23T00:00:00Z",
  "ended_at": "2026-06-23T00:01:00Z",
  "exit_code": 0,
  "artifacts": [
    {
      "path": "skills/drafts/<slug>/bundle.json",
      "sha256": "..."
    }
  ],
  "stdout_excerpt": "redacted excerpt",
  "stderr_excerpt": "",
  "status": "passed"
}
```

## 10. Agent smoke evidence schema

```json
{
  "loop_id": "RL-001",
  "agent": "codex|claude-code|opencode",
  "agent_version": "...",
  "skill_package_ref": "...",
  "task_prompt": "Use this skill package to ...",
  "run_status": "passed",
  "transcript_ref": "docs/working/status/real-loop-evidence/RL-001.agent-transcript.redacted.md",
  "observed_result": "Agent followed the generated skill and produced expected output.",
  "reviewer_decision": "approved",
  "created_at": "2026-06-23T00:00:00Z"
}
```

## 11. 不合格证据判定

以下情况不得算 launch-gate eligible：

- 使用 fixture/mock/demo 样本；
- 没有 source hash；
- 没有业务期望；
- 没有人审；
- 只有自动测试，没有人工复核；
- agent smoke 为 `not_run`；
- manifest 中含 raw PII；
- 产物不可复现；
- 没有运行命令；
- 没有明确版本和环境；
- 只提供截图，没有结构化 evidence。

## 12. 验收命令

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

## 13. 完成定义

该 P0 项完成必须满足：

1. 10 条 manifest 全部存在。
2. 每条 manifest 均为真实业务样本。
3. 每条 manifest 均有 source hash。
4. 每条 manifest 均有 business expectation。
5. 每条 manifest 均有 run evidence。
6. 每条 manifest 均有 human review。
7. 每条 manifest 均有 agent smoke evidence。
8. GL-64 strict preflight 通过。
9. trial metrics 不再因 fixture-only 阻塞。
10. launch gate 不再因真实 loop 覆盖不足 HOLD。
