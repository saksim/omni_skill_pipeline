# Changelog

## 2026-04-19

### Documentation

- Added root `README.md` as the single root-level entry document.
- Moved architecture and contracts into `docs/current/`.
- Added `docs/INDEX.md`.
- Added `docs/current/status/CURRENT_STATUS.md`.
- Added `docs/history/CHANGELOG.md`.

### Project Scaffolding

- Added Python project metadata and package layout.
- Added API entry, worker entry, repository, renderer, service, and schema modules.

### Skill Contracts

- Added `skill.schema.json`.
- Added `SKILL.template.md`.
- Added schema export script.

### Distillation Pipeline

- Added pluggable interfaces for adapters, providers, insight extraction, and skill composition.
- Added heuristic insight extractor and heuristic skill composer.
- Added fallback composer/provider strategy.

### Input Adapters

- Added text adapter.
- Added audio adapter.
- Added image adapter.
- Added video adapter.
- Added tabular/time-series adapter.

### Provider Integrations

- Added OpenAI ASR / LLM / Vision providers.
- Added Tesseract OCR provider.
- Added FFmpeg / FFprobe media processor.

### Video Improvements

- Added video probing via `ffprobe`.
- Added scene-based candidate sampling.
- Added adaptive interval sampling for long videos.
- Added short-video fallback frame extraction.
- Added perceptual hash frame deduplication.
- Added distributed frame selection across timeline buckets.

### Structured Data Improvements

- Added schema, missingness, entity summary, numeric profile, and time-series anomaly evidence generation.
- Unified tabular output into `EvidenceUnit` with `TABLE / METRIC / EVENT` content types.
