# Changelog

## 2026-06-19

### v0.2.1-internal.1

- Fixed installed-wheel `show-template` by packaging `SKILL.template.md` and `skill.schema.json` inside the Python wheel.
- Added packaged-contract fallback in runtime settings for non-repository installs.
- Added `scripts/release_consumer_smoke.py` to verify release checksums, manifest contract, wheel installation, and installed CLI template access.
- Added the consumer smoke to the `Release` workflow before artifact upload and publication.
- Added release notes for `v0.2.1-internal.1`.

## 2026-04-19

### Documentation

- Added root `README.md` as the single root-level entry document.
- Moved architecture and contracts into the then-current docs layer, later renamed to `docs/latest/`.
- Added `docs/INDEX.md`.
- Added `docs/working/status/CURRENT_STATUS.md`.
- Added `docs/releases/CHANGELOG.md`.

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

## 2026-04-20

### Architecture

- Added `docs/latest/architecture/skill-distillation-v2.md` to record the current diagnosis, V2 target architecture, domain model evolution, and architecture decisions.
- Added `docs/working/architecture/skill-distillation-v2-roadmap.md` to define phased implementation steps, acceptance criteria, and migration constraints for future implementation.
- Added `docs/working/architecture/skill-distillation-v2-implementation-backlog.md` to enumerate the full V2 development backlog, task packages, file touchpoints, dependencies, and acceptance criteria for future implementation.
- Added `docs/working/architecture/skill-distillation-v2-work-orders.md` to turn E1+ backlog items into directly executable work orders for future implementation.
- Updated `README.md`, `docs/working/status/CURRENT_STATUS.md`, `docs/latest/architecture/ARCHITECTURE.md`, and `docs/INDEX.md` to expose the new V2 design documents.

### Status

- Added `docs/working/status/baselines/README.md` as the E0 baseline pack entry.
- Added `docs/working/status/baselines/e0-sample-inventory.md` to enumerate current baseline samples and known coverage gaps.
- Added `docs/working/status/baselines/e0-baseline-2026-04-20.md` to record actual baseline replay commands, observed outputs, and conclusions.
- Added `docs/working/status/baselines/evaluation-rubric.md` to define the common evaluation metrics for future V2 comparisons.
- Added `docs/working/status/baselines/e0-baseline-manifest.json` as a machine-readable baseline manifest.
- Recorded that the current MVP test suite passed via `python -m unittest discover -s tests -p 'test_mvp.py'`.
