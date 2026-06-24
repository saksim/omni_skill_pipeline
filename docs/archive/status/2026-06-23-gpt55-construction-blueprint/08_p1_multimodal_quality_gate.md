# P1：多模态质量验收与 OCR/ASR 加固规范

## 1. 背景

项目支持 text/audio/image/tabular/video/corpus 等输入，代表性 CLI 路径可运行。但评估中看到 image/OCR 输出存在明显噪声，video 也主要依赖 transcript + keyframe + OCR，不应被宣称为生产级多模态理解。

因此需要建立多模态质量门禁。

## 2. 当前能力边界

| Modality | 当前状态 | 风险 |
|---|---|---|
| text | 相对稳 | 长文本/PDF/代码结构化仍需真实样本验证 |
| audio | transcript-first 稳 | 无 transcript 时依赖 ASR provider，不应默认宣称可用 |
| image | 可运行 | OCR 噪声明显，图表/截图理解不稳定 |
| tabular | 可运行 | 数据规模、异常值、列语义需验证 |
| video | 可运行 | 主要是 transcript + keyframes，不是完整视频理解 |
| corpus | 可运行 | 多资产聚合质量依赖各 modality 上游质量 |

## 3. 质量门禁目标

多模态质量不要求一步到生产极致，但 Beta 前必须有：

1. 每类输入的最小样本集。
2. 每类输入的质量评分标准。
3. 每类输入的失败模式。
4. 每类输入的人工复核流程。
5. OCR/ASR provider 不可用时的降级说明。
6. 质量不过关时不能进入 launch evidence。

## 4. 评分维度

每个输出建议按 1-5 分评分：

| 维度 | 含义 |
|---|---|
| Faithfulness | 是否忠于源材料 |
| Completeness | 是否覆盖关键内容 |
| Reusability | 是否能形成可复用技能 |
| Traceability | 是否能追溯到来源/证据 |
| Safety/Redaction | 是否避免泄露敏感信息 |
| Agent Usability | Agent 是否能按该技能执行 |

建议 Beta 候选最低门槛：

```text
Faithfulness >= 4
Traceability >= 4
Safety/Redaction >= 5
Agent Usability >= 4
No critical issue
```

## 5. Modality-specific 验收规则

### 5.1 Text

必须验证长文本、结构化文档、操作手册、代码/README、PDF 转文本后的材料。失败模式包括摘要过泛、步骤丢失、把背景知识写成源材料事实、无法生成可执行技能。

### 5.2 Audio

必须区分 transcript-first、第三方 ASR、无 transcript 无 ASR 三种路径。当前可优先宣称 transcript-first；无 transcript 且无 ASR provider 不应宣称可用。

### 5.3 Image

必须验证纯文字截图、UI 截图、流程图、图表、告警截图。OCR 质量门槛：关键术语识别准确、不把乱码作为事实、低置信内容必须标记 uncertain、无法识别时必须 graceful degradation。

建议输出中增加：

```json
{
  "ocr_confidence": 0.0,
  "uncertain_regions": [],
  "requires_human_review": true
}
```

### 5.4 Video

必须明确当前视频理解模型：

```text
video = transcript + keyframe extraction + image/OCR analysis + timeline assembly
```

不要宣称 full semantic video understanding。必须验证有 transcript 的视频、无 transcript 的视频、操作录屏、培训视频、有画面文字的视频、场景切换明显的视频。

## 6. 质量 evidence schema

```json
{
  "loop_id": "RL-003",
  "modality": "image",
  "quality_scores": {
    "faithfulness": 4,
    "completeness": 3,
    "reusability": 4,
    "traceability": 4,
    "safety_redaction": 5,
    "agent_usability": 4
  },
  "critical_issues": [],
  "minor_issues": [
    "One OCR token is uncertain and was correctly marked uncertain."
  ],
  "requires_human_review": true,
  "human_review_decision": "approved_for_beta_evidence"
}
```

## 7. Provider 配置文档要求

| Provider | 用途 | 是否必需 | 失败时行为 |
|---|---|---:|---|
| Tesseract OCR | image/video OCR | 可选但推荐 | 标记 OCR unavailable |
| OpenAI ASR | audio transcription | 可选 | 要求 transcript-path |
| Media/ffmpeg | video keyframe | 视功能而定 | video distill graceful fail |

## 8. 验收命令

```bash
omni-skill distill-text --title "RL Text" --file <real_text>
omni-skill distill-audio --title "RL Audio" --transcript-path <real_transcript>
omni-skill distill-image --title "RL Image" --image-path <real_image>
omni-skill distill-video --title "RL Video" --video-path <real_video> --transcript-path <real_transcript>
python scripts/quality_regression.py --print-json
python scripts/trial_metrics.py --manifest <real_manifest> --fail-on-ga-blocker
```

## 9. 完成定义

1. text/audio/image/video 均有真实样本质量评分。
2. OCR 输出不再把明显乱码当确定事实。
3. ASR/provider 不可用时行为明确。
4. video 文档明确当前理解边界。
5. quality gate 能阻止低质量样本进入 launch evidence。
6. 人审可追溯。

## 10. 禁止的伪修复

不允许：把 OCR 乱码直接清洗成看似正确的内容但无证据；无 transcript 时假装音频已理解；视频只抽一帧却宣称理解全视频；删除 uncertain 标记；用 demo 图片替代真实 image loop；没有人审就把多模态样本标记 eligible。
