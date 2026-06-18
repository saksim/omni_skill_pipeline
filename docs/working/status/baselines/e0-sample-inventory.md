# E0 Sample Inventory

## 判词

E0 样本集必须覆盖当前系统真实入口，同时暴露当前系统最痛的模态缺陷。现阶段以仓库自带 `examples/` 为主，并辅以现有测试样本与 draft 产物。

## 样本清单

| Sample ID | Modality | Source | Purpose | Current Replay Path | Notes |
| --- | --- | --- | --- | --- | --- |
| `T01` | text | `examples/text_note.md` | 验证文档型 procedure/rule/verification 抽取 | CLI `distill-text` | 当前最稳定样本之一 |
| `A01` | audio | `examples/audio_transcript.srt` | 验证 transcript-only 音频链 | CLI `distill-audio --transcript-path` | 目前没有独立原始音频基线，属于覆盖缺口 |
| `I01` | image | `examples/demo_image.png` | 暴露图片 OCR/scene 质量问题 | CLI `distill-image` | 当前输出明显存在 OCR 污染 |
| `V01` | video | `examples/demo_video.mp4` | 暴露视频抽帧/OCR 路径的语义损失 | CLI `distill-video` | 当前输出高度退化 |
| `TS01` | tabular/time-series | `examples/demo_timeseries.csv` | 验证 schema/metric/event 型 evidence | CLI `distill-tabular` | evidence 丰富，但最终 step 仍混入 schema 噪声 |
| `UT01` | text/image/audio/video synthetic | `tests/test_mvp.py` 内置 fixture | 保证最小功能回归 | `python -m unittest discover -s tests -p 'test_mvp.py'` | 不作为业务质量样本，只作为功能基线 |

## 覆盖判断

当前 E0 已覆盖：

- 文档 procedure skill
- transcript-only audio skill
- 图片 OCR / scene
- 视频 audio + keyframe + OCR
- 表格 / 时序 evidence

当前 E0 未覆盖：

- 原始音频文件 ASR 基线
- PDF / DOCX / HTML 等复杂文档结构基线
- 多资产联合蒸馏基线
- 多语言 OCR / ASR 基线
- 真实长视频与长时序大样本基线

## 推荐后续补样本

- `A02`: 原始会议音频 `wav/mp3`
- `D02`: 带表格和代码块的 PDF
- `D03`: 带章节层级的 DOCX
- `V02`: 带字幕轨与较长时间线的视频
- `TS02`: 多实体、多指标的时序数据
- `C01`: 文档 + 音频 + 图片的联合 corpus

## 结论

E0 样本集已经足以支持 V2 第一轮改造与回归，但还不足以支撑 V2 最终发布验收。后续至少要补齐原始音频、复杂文档、联合 corpus 三类样本。
