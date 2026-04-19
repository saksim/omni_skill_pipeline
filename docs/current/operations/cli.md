# CLI

## Entry

- CLI module: `src/omni_skill_pipeline/cli.py`
- Interpreter: `D:\code_environment\anaconda_all_css\py311\python.exe`

## Base Pattern

```powershell
$env:PYTHONPATH='src'
& 'D:\code_environment\anaconda_all_css\py311\python.exe' -m omni_skill_pipeline.cli <command> ...
```

## Commands

### distill-text

```powershell
$env:PYTHONPATH='src'
& 'D:\code_environment\anaconda_all_css\py311\python.exe' -m omni_skill_pipeline.cli distill-text `
  --file examples\text_note.md `
  --domain database
```

### distill-audio

```powershell
$env:PYTHONPATH='src'
& 'D:\code_environment\anaconda_all_css\py311\python.exe' -m omni_skill_pipeline.cli distill-audio `
  --audio-path examples\audio_transcript.srt `
  --domain ops
```

### distill-image

```powershell
$env:PYTHONPATH='src'
& 'D:\code_environment\anaconda_all_css\py311\python.exe' -m omni_skill_pipeline.cli distill-image `
  --image-path examples\demo_image.png `
  --domain observability
```

### distill-tabular

```powershell
$env:PYTHONPATH='src'
& 'D:\code_environment\anaconda_all_css\py311\python.exe' -m omni_skill_pipeline.cli distill-tabular `
  --file examples\demo_timeseries.csv `
  --time-column timestamp `
  --value-column latency_ms `
  --value-column error_rate `
  --entity-column service `
  --domain incident_response
```

### distill-video

```powershell
$env:PYTHONPATH='src'
& 'D:\code_environment\anaconda_all_css\py311\python.exe' -m omni_skill_pipeline.cli distill-video `
  --video-path examples\demo_video.mp4 `
  --domain incident_response `
  --max-keyframes 6 `
  --scene-threshold 0.32 `
  --dedupe-distance 5
```

### show-template

```powershell
$env:PYTHONPATH='src'
& 'D:\code_environment\anaconda_all_css\py311\python.exe' -m omni_skill_pipeline.cli show-template
```