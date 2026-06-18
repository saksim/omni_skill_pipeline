# Data Flow

## Unified Rule

所有输入最终都必须归一到 `LoadedAsset -> EvidenceUnit[] -> Insight[] -> SkillDocument`。

## Text Flow

```text
Text Request
  -> TextAdapter
  -> TextReaderRegistry
  -> LoadedAsset(text)
  -> EvidenceUnit(paragraph)
  -> InsightExtractor
  -> SkillComposer
  -> artifacts
```

文本 reader 当前包含：

- Plain text reader
- JSON reader
- HTML reader
- DOC reader via `antiword`
- DOCX reader
- PDF reader via `pypdf` + `pdftotext` fallback

## Audio Flow

```text
Audio Request
  -> transcript / transcript_path / sidecar
     else -> AudioTranscriber
  -> TranscriptionResult
  -> EvidenceUnit(speech segment)
  -> InsightExtractor
  -> SkillComposer
  -> artifacts
```

## Image Flow

```text
Image Request
  -> OCRProvider.extract(image)
  -> ImageAnalyzer.analyze(image)
  -> EvidenceUnit(ocr) + EvidenceUnit(scene)
  -> InsightExtractor
  -> SkillComposer
  -> artifacts
```

## Video Flow

```text
Video Request
  -> FFmpegMediaProcessor.probe(video)
  -> FFmpegMediaProcessor.extract_audio(video)
  -> AudioAdapter / AudioTranscriber
  -> FFmpegMediaProcessor.extract_keyframes(video)
  -> OCRProvider.extract(frame)
  -> ImageAnalyzer.analyze(frame)
  -> merge speech + ocr + scene evidence
  -> InsightExtractor
  -> SkillComposer
  -> artifacts
```

### Long Video Strategy

- 先 `ffprobe` 获取时长、帧率、分辨率、帧数
- 再基于 `scene` 生成镜头候选帧
- 再基于自适应时间桶生成采样帧
- 对候选帧做感知哈希去重
- 在每个时间桶内优先选 `scene` 帧，避免长视频抽样扎堆
- 若没有任何候选帧，则回退到首帧/前几帧抽取

## Tabular / Time-Series Flow

```text
Tabular Request
  -> TabularAdapter
  -> schema / missingness / entity summary
  -> numeric profile / timeseries overview / anomaly events
  -> EvidenceUnit(TABLE / METRIC / EVENT)
  -> InsightExtractor
  -> SkillComposer
  -> artifacts
```

### Structured Evidence Types

- `TABLE`: schema、missingness、entity summary、generic guidance
- `METRIC`: numeric profile、timeseries overview、timeseries metric summary
- `EVENT`: anomaly windows、异常时间点提示

## Skill Output Flow

```text
LoadedAsset
  -> InsightExtractor
  -> SkillComposer
  -> SkillDocument
  -> MarkdownRenderer
  -> FileArtifactRepository
```