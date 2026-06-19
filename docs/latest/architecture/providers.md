# Providers

## Provider Protocols

- `AudioTranscriber`
- `OCRProvider`
- `ImageAnalyzer`
- `MediaProcessor`
- `SkillComposer`

## Current Implementations

### Audio / LLM / Vision

- `OpenAIAudioTranscriber`
- `OpenAILLMSkillComposer`
- `OpenAIVisionAnalyzer`

### Local Providers

- `TesseractOCRProvider`
- `FFmpegMediaProcessor`

### Fallback Wrappers

- `FallbackAudioTranscriber`
- `FallbackOCRProvider`
- `FallbackImageAnalyzer`
- `FallbackSkillComposer`

## Fallback Order

### Skill Composer

```text
OpenAILLMSkillComposer
  -> HeuristicSkillComposer
```

### OCR

```text
TesseractOCRProvider
  -> OpenAIVisionAnalyzer.extract()
```

### Audio Transcription

```text
explicit transcript / transcript_path / sidecar transcript
  -> OpenAIAudioTranscriber
```

## Video Sampling Provider Rules

`FFmpegMediaProcessor` 当前承担：

- `probe()`：读取视频元数据
- `extract_audio()`：提取音轨
- `extract_keyframes()`：镜头候选 + 自适应采样 + 去重 + fallback

## Provider Constraints

- Providers 不能直接生成最终工件目录
- Providers 不能直接改业务规则
- Providers 只负责把外部能力输出为结构化结果
- fallback 层负责熔断与降级，不污染 service 主编排

## Configuration Surface

### OpenAI

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OMNI_OPENAI_LLM_MODEL`
- `OMNI_OPENAI_VISION_MODEL`
- `OMNI_OPENAI_TRANSCRIBE_MODEL`
- `OMNI_TRANSCRIPTION_LANGUAGE`

### Media / OCR

- `OMNI_FFMPEG_BIN`
- `OMNI_FFPROBE_BIN`
- `OMNI_TESSERACT_BIN`
- `OMNI_TESSERACT_LANGUAGES`

### Video Sampling

- `OMNI_KEYFRAME_INTERVAL_SECONDS`
- `OMNI_MAX_KEYFRAMES`
- `OMNI_VIDEO_SCENE_THRESHOLD`
- `OMNI_VIDEO_FRAME_DEDUPE_DISTANCE`

### Composer Policy

- `OMNI_PREFER_LLM_COMPOSER`