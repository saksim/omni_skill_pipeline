# Controlled Business Trial Iteration

> Date: 2026-05-18  
> Scope: completed capability record, target adjustment, multimodal controlled trial scope, and next iteration task cards  
> Sources: `release-artifacts-20260518T080402Z.tar.gz`, `CURRENT_STATUS.md`, `launch-readiness-master-plan.md`, `2026-05-17-distillation-platform-strategy-assessment.md`, `skill-distillation-v2-roadmap.md`

## Verdict

The latest release run reached `GO`, with `overall PASS` and `gates(pass=47 hold=0)`. This changes the execution posture.

The next target should not be "full GA" or "multi-tenant SaaS". The right next target is:

> Controlled business trial: limited users, limited multimodal scenarios, limited data range, all outputs default to human REVIEW, and GA discussion only after a full real business loop.

This keeps the project aligned with the current evidence. The engineering release gate is now strong enough to start a controlled trial; the product proof is still too thin to claim broad GA.

## Completed Capability Record

### Phase 1

V2 Roadmap Phase 1 is complete.

- `Corpus`, `EvidenceNode`, `SemanticAtom`, `SkillGraph`, and `Publication` are implemented.
- V1-compatible `SkillDocument` remains available.
- `EvidenceUnit -> EvidenceNode` and `SkillGraph -> SkillDocument` compatibility paths exist.
- Core enums including atom, graph node, and lifecycle decision types exist.
- Serialization, schema, corpus, publication, review, lineage, and release-contract paths are covered by tests.

### Release Readiness

The following capabilities were previously tracked as Beta or GA gaps, but are now usable as controlled-trial foundations:

- Multimodal distillation for text, audio, image, video, tabular/time-series, and corpus inputs.
- API validation, auth, rate limiting, stable error response, request/trace context, readiness check.
- CLI/API/worker surfaces for core distillation and corpus flows.
- Quality scoring, review policy, review task persistence, review feedback, and review queue operations surface.
- Worker retry, idempotency, claim/lock, and task-type hardening.
- File repository, Postgres repository, dual-write repository, Postgres soak validation, and benchmark smoke harness.
- Similarity retrieval, lifecycle `new/revise/merge/supersede/reject`, and lineage links.
- Multi-view publications including `SKILL.md`, JSON, checklist, and decision tree.
- Linux release test entry, container smoke, release gate, release switch, doc sync, and evidence freshness/skew/contract hard gates.

The remaining work is not "make the core run". The remaining work is "prove the core creates business-useful agent skills under controlled conditions".

## Target Adjustment

### Previous Target

The 2026-04-24 launch plan treated L1 Beta as blocked by API, ops, worker, repository, release, and review-queue gaps. That was accurate then.

### Current Target

After the 2026-05-18 `GO`, those gaps are no longer the primary blocker. The target should move to:

- Controlled business trial first.
- Agent Skill Compiler as the short-term product wedge.
- Real sample quality, human review cost, agent usability, and operational failure rate as the deciding metrics.

### Deferred Targets

Do not make these the next milestone:

- Broad public Beta.
- Multi-tenant SaaS.
- Full SME collaboration UI.
- Mature vector knowledge base product.
- Fully automated skill publication without human review.

They remain valid, but they require trial evidence first.

## Controlled Trial Rules

Apply these to every trial scenario:

- Limit to 1-3 friendly users, teams, or internal workflows.
- Do not process regulated data, payment data, production credentials, secrets, or unsanitized customer PII.
- Mark every generated artifact as `REVIEW_REQUIRED` by default.
- No generated skill is considered published until a human reviewer approves it.
- Keep raw evidence, generated artifacts, review decision, reviewer edits, provider cost, latency, errors, and final agent smoke result.
- One complete loop means: input evidence -> distillation -> review -> revision or approval -> agent-native skill package -> agent uses the skill on a small task -> metrics report.

## Multimodal Trial Scope

### Text / Document

Allowed scenarios, choose 1-3:

- Incident postmortem or runbook document -> diagnostic skill.
- Database slow-query case notes -> DBA review skill.
- Product or operations handbook -> SOP skill.

Data range:

- 3-10 documents per pilot.
- Prefer Markdown, plain text, PDF, or DOCX.
- Each document should be under 50 pages or 100k characters for the first trial.
- Remove secrets, credentials, private customer names, and production-only URLs unless explicitly approved for internal trial.

Review rule:

- Reviewer must confirm factual accuracy, missing steps, dangerous commands, and whether the generated `description` triggers the right skill usage.

### Audio

Allowed scenarios, choose 1-3:

- Decision meeting recording -> decision/playbook skill.
- Incident review call -> runbook update skill.
- SME interview -> domain procedure skill.

Data range:

- 3-10 recordings per pilot.
- Each recording should be under 60 minutes.
- Prefer recordings with a transcript or clear speakers.
- Do not include sensitive HR, legal, medical, financial, or customer-confidential content in the first trial.

Review rule:

- Reviewer must compare the generated skill against transcript excerpts and confirm that decisions are not hallucinated from unclear speech.

### Image

Allowed scenarios, choose 1-3:

- Monitoring dashboard screenshot -> alert diagnostic skill.
- UI workflow screenshot set -> visual inspection or SOP skill.
- Architecture diagram -> system orientation skill.

Data range:

- 5-20 images per pilot.
- Use PNG/JPEG screenshots or diagrams.
- Blur API keys, user emails, customer names, tokens, internal hostnames, and unreleased product details unless the pilot is fully internal.

Review rule:

- Reviewer must confirm OCR correctness, visual interpretation, and whether any cropped/ambiguous UI state caused unsupported instructions.

### Video

Allowed scenarios, choose 1-3:

- Screen-recorded product operation -> SOP skill.
- Debugging or incident walkthrough video -> troubleshooting skill.
- Demo/training video -> onboarding skill.

Data range:

- 2-5 videos per pilot.
- Each video should be under 15 minutes for the first trial.
- Prefer screen recordings with clear subtitles or audio.
- Do not include credential entry, admin consoles with secrets, or private customer data.

Review rule:

- Reviewer must inspect selected keyframes, transcript, OCR, and final procedure order. All video-derived skills stay review-only until approved.

### Tabular / Time-Series

Allowed scenarios, choose 1-3:

- Service metric CSV -> metric diagnostic or guardrail skill.
- Latency/error/cost report -> operations decision tree.
- Eval or experiment CSV -> quality regression skill.

Data range:

- 3-10 files per pilot.
- CSV/TSV/JSON table preferred.
- Each file should be under 50 MB.
- Remove personal identifiers and customer-specific account IDs.

Review rule:

- Reviewer must validate metric names, units, thresholds, baseline windows, and whether the generated guardrail would create false alarms.

### Mixed Corpus

Allowed scenarios, choose 1-3:

- Incident bundle: postmortem, logs, dashboard screenshots, meeting transcript -> runbook skill.
- Feature release bundle: PR notes, docs, screenshots, demo video -> release/checklist skill.
- Support bundle: sanitized ticket notes, screenshots, recordings -> support playbook skill.

Data range:

- 1-3 corpus bundles per pilot.
- Each bundle should contain 2-8 assets.
- First trial should avoid more than one video per bundle.
- Every asset must have source, owner, sensitivity level, and allowed publication target.

Review rule:

- Reviewer must confirm cross-asset consistency, source priority, conflict handling, and whether the generated skill cites the right evidence.

## Trial Success Criteria

Controlled trial can be considered successful only if all conditions hold:

- Latest release run remains `GO`.
- At least 10 complete loops finish across at least 4 modalities.
- 0 unreviewed skills are published.
- 0 critical secret/PII leaks in generated artifacts.
- 0 high-severity production incidents caused by the trial.
- Reviewer approval rate is at least 80% after no more than one revision.
- Median reviewer edit distance is at or below 25%.
- Agent-native skill smoke success rate is at least 80% for approved skills.
- Provider/runtime failure rate stays below the agreed pilot threshold.
- Cost per accepted skill is recorded and accepted by the operator.

If any of the first four conditions fail, GA discussion stops and the next iteration must be remediation.

## Next Iteration Task Cards

### Model Assignment Guide

- Use Codex 5.5 for ambiguous product/architecture decisions, trial rubric design, safety boundaries, and end-to-end quality review.
- Use Codex 5.3 for bounded implementation work: schemas, scripts, validators, test cases, docs, and small service integrations.

### CBT-01 Completed Capability Snapshot

- Status: Complete
- Recommended model: Codex 5.3
- Goal: keep docs aligned with the latest `GO` state.
- Files: `docs/current/status/CURRENT_STATUS.md`, `README.md`, `docs/INDEX.md`
- Work:
  - Link this controlled-trial iteration doc from the main status and docs index.
  - Keep the 2026-04-24 launch plan marked as historical baseline.
  - Keep the 2026-05-17 strategy assessment as the strategic direction.
- Acceptance:
  - A new contributor can identify current capability, trial target, and next task-card entry from `README.md` or `docs/INDEX.md`.
- Evidence:
  - `README.md` now keeps the controlled-trial doc and strategy doc as active entry points while marking `launch-readiness-master-plan.md` as the historical 2026-04-24 baseline.
  - `docs/INDEX.md` now labels the launch-readiness master plan as historical baseline and keeps controlled-trial iteration as the active status entry.
  - `CURRENT_STATUS.md` already records latest `GO`, controlled business trial scope, and the controlled-trial iteration doc as the execution entry.
  - 2026-05-21 iterative re-check: verified all three entry docs still maintain the same controlled-trial/strategy/historical-baseline routing and did not regress after CBT-02+ updates.
  - 2026-05-21 iterative re-check (run 2): re-verified `README.md`, `docs/INDEX.md`, and `CURRENT_STATUS.md` keep controlled-trial as the active execution entry, strategy assessment as direction, and launch-readiness as historical baseline.
  - 2026-05-22 iterative re-check (run 3): re-validated `README.md`, `docs/INDEX.md`, and `CURRENT_STATUS.md` keep controlled-trial iteration as the active execution entry, strategy assessment as direction, and `launch-readiness-master-plan.md` as historical baseline only.
  - 2026-05-22 iterative re-check (run 4): confirmed `README.md`, `docs/INDEX.md`, and `CURRENT_STATUS.md` still route contributors to controlled trial as the active execution path, keep strategy assessment as direction, and keep `launch-readiness-master-plan.md` as historical baseline only.
  - 2026-05-22 iterative re-check (run 5): confirmed `README.md`, `docs/INDEX.md`, and `CURRENT_STATUS.md` continue to point to controlled business trial as the active execution route, keep the 2026-05-17 strategy assessment as direction, and keep `launch-readiness-master-plan.md` as historical baseline only.
  - 2026-05-22 iterative re-check (run 6): re-confirmed `README.md`, `docs/INDEX.md`, and `CURRENT_STATUS.md` still expose controlled business trial as the active execution route, keep the 2026-05-17 strategy assessment as direction, and preserve `launch-readiness-master-plan.md` as historical baseline only.
  - 2026-05-22 iterative re-check (run 7): re-validated `README.md`, `docs/INDEX.md`, and `CURRENT_STATUS.md` still keep controlled business trial as the active execution route, keep the 2026-05-17 strategy assessment as direction, and keep `launch-readiness-master-plan.md` as historical baseline only.
  - 2026-05-23 iterative re-check (run 8): re-validated `README.md`, `docs/INDEX.md`, and `CURRENT_STATUS.md` still route contributors to controlled business trial as active execution, keep the 2026-05-17 strategy assessment as direction, and keep `launch-readiness-master-plan.md` as historical baseline only.
  - 2026-05-23 iterative re-check (run 9): re-confirmed `README.md`, `docs/INDEX.md`, and `CURRENT_STATUS.md` still route contributors to controlled business trial as the active execution path, keep the 2026-05-17 strategy assessment as direction, and keep `launch-readiness-master-plan.md` as historical baseline only.
  - 2026-05-25 iterative re-check (run 10): re-verified `README.md`, `docs/INDEX.md`, and `CURRENT_STATUS.md` still keep controlled business trial as the active execution entry, keep the 2026-05-17 strategy assessment as direction, and keep `launch-readiness-master-plan.md` strictly as historical baseline (2026-04-24).

### CBT-02 Trial Sample Manifest

- Status: Complete
- Recommended model: Codex 5.3
- Goal: define a machine-readable manifest for controlled trial samples.
- Files: `docs/current/status/baselines/`, optional `scripts/validate_manifest.py`, tests under `tests/`
- Work:
  - Add a trial sample manifest template with modality, scenario, source owner, sensitivity, asset list, review owner, target package format, and expected output type.
  - Add validation for required fields and unsupported sensitivity levels.
- Acceptance:
  - Invalid manifests fail with actionable messages.
  - Example manifests exist for text, audio, image, video, tabular, and mixed corpus.
- Evidence:
  - Added template `docs/current/status/baselines/trial-manifests/trial-sample-manifest.template.json` with required fields: `modality`, `scenario`, `source_owner`, `sensitivity`, `asset_list`, `review_owner`, `target_package_format`, `expected_output_type`.
  - Added modality examples: `trial-sample-text.example.json`, `trial-sample-audio.example.json`, `trial-sample-image.example.json`, `trial-sample-video.example.json`, `trial-sample-tabular.example.json`, `trial-sample-mixed-corpus.example.json`.
  - Added validator `scripts/validate_manifest.py` with actionable errors for missing required fields and unsupported `sensitivity`/`modality`/`target_package_format`.
  - Added focused tests `tests/test_validate_trial_manifest_script.py` for valid manifest pass path plus invalid-field actionable failure paths.
  - 2026-05-22 iterative re-check (run 1): re-validated the CBT-02 artifact set (`trial-manifest` template/examples, `validate_manifest.py`, and `tests/test_validate_trial_manifest_script.py`) and confirmed manifest validation plus focused script tests still pass without regression.
  - 2026-05-23 iterative re-check (run 2): re-ran `validate_manifest.py` across all six modality example manifests and `tests.test_validate_trial_manifest_script`; confirmed required-field/support-level validation paths remain passing without regression, and doc sync remains green.
  - 2026-05-23 iterative re-check (run 3): re-ran `validate_manifest.py --output -` for all six modality example manifests (`text/audio/image/video/tabular/mixed-corpus`), re-ran `python -m unittest tests.test_validate_trial_manifest_script` (3 tests), and re-ran `python scripts/doc_sync.py --output -`; all remained passing with no regression.

### CBT-03 Default Human Review Mode

- Status: Complete
- Recommended model: Codex 5.3
- Goal: ensure controlled-trial outputs default to human review.
- Files: `src/omni_skill_pipeline/quality/`, `src/omni_skill_pipeline/service.py`, `docs/current/operations/`
- Work:
  - Add an explicit trial mode or configuration flag that forces `REVIEW_REQUIRED`.
  - Persist the reason code, for example `controlled_trial_requires_review`.
  - Document how to enable and disable the mode.
- Acceptance:
  - Tests prove trial mode prevents auto-publish even when quality score is high.
- Evidence:
  - Added controlled-trial review config in `src/omni_skill_pipeline/config.py` and `.env.example`:
    - `OMNI_CONTROLLED_TRIAL_REVIEW_MODE`
    - `OMNI_CONTROLLED_TRIAL_REVIEW_REASON_CODE` (default `controlled_trial_requires_review`)
  - Wired service composition to enforce review mode through `ReviewPolicy` in `src/omni_skill_pipeline/service_factory.py`.
  - Updated review policy `src/omni_skill_pipeline/quality/review_policy.py` to force `review_required` while preserving score snapshots and persisting the reason code.
  - Added tests proving high-quality scores still become `review_required` under trial mode and reason code is persisted:
    - `tests/test_review_policy.py`
    - `tests/test_v2_models.py`
    - `tests/test_review_feedback.py`
    - `tests/test_openai_provider_config.py`
    - `tests/test_service_factory_split.py`
  - Documented enable/disable behavior in `docs/current/operations/env.md`.
  - 2026-05-22 iterative re-check (run 1): re-ran focused CBT-03 review-mode tests (`tests.test_review_policy`, `tests.test_service_factory_split`, `tests.test_v2_models`, `tests.test_review_feedback`, `tests.test_openai_provider_config`) and confirmed controlled-trial mode still forces `review_required` with persisted `controlled_trial_requires_review` reason code.
  - 2026-05-23 iterative re-check (run 2): re-ran focused CBT-03 review-mode tests (`tests.test_review_policy`, `tests.test_service_factory_split`, `tests.test_v2_models`, `tests.test_review_feedback`, `tests.test_openai_provider_config`) and confirmed controlled-trial mode still forces `review_required` with persisted `controlled_trial_requires_review` reason code; doc sync remains green.
  - 2026-05-23 iterative re-check (run 3): re-verified controlled-trial review-mode wiring in `config.py`/`service_factory.py`/`review_policy.py` plus `docs/current/operations/env.md`, re-ran focused tests (`tests.test_review_policy`, `tests.test_service_factory_split`, `tests.test_v2_models`, `tests.test_review_feedback`, `tests.test_openai_provider_config`), and re-ran `python scripts/doc_sync.py --output -`; all remained passing with `review_required` enforced and reason code persisted as `controlled_trial_requires_review`.

### CBT-04 Reviewer Packet Generator

- Status: Complete
- Recommended model: Codex 5.3
- Goal: make human review faster and more consistent.
- Files: `src/omni_skill_pipeline/review/`, `src/omni_skill_pipeline/repository.py`, tests under `tests/`
- Work:
  - Generate a reviewer packet containing input summary, evidence links, generated skill, quality scores, risk flags, and approval checklist.
  - Include modality-specific checks for OCR, transcript, keyframes, metrics, and cross-asset conflicts.
- Acceptance:
  - Every controlled-trial output has a review packet artifact.
  - Tests cover at least one single-asset case and one mixed-corpus case.
- Evidence:
  - Added `src/omni_skill_pipeline/review/packet.py` with `ReviewerPacketBuilder`.
  - Reviewer packet includes input summary, evidence links, generated skill preview, quality scores, review policy, review feedback, risk flags, and approval checklist.
  - Modality-specific checklist coverage includes transcript, OCR/visual, keyframe sequence, metrics, and cross-asset consistency checks.
  - `DistillationService` now generates reviewer packets for single-asset and corpus distillation paths.
  - `FileArtifactRepository` persists `reviewer_packet.json` and records `reviewer_packet_path` on review queue items.
  - Added focused tests in `tests/test_reviewer_packet.py` for single-asset and mixed-corpus reviewer packet artifacts.
  - 2026-05-25 iterative re-check (run 1): re-verified reviewer-packet wiring in `src/omni_skill_pipeline/review/packet.py`, `src/omni_skill_pipeline/service.py`, and `src/omni_skill_pipeline/repository.py`; re-ran `python -m unittest tests.test_reviewer_packet` (2 tests, pass) and confirmed single-asset plus mixed-corpus reviewer packet artifacts still persist correctly without regression.

### CBT-05 Trial Metrics Collector

- Status: Complete
- Recommended model: Codex 5.3
- Goal: record whether the trial is working.
- Files: `scripts/`, `src/omni_skill_pipeline/quality/`, `docs/current/status/baselines/`, tests under `tests/`
- Work:
  - Collect review outcome, reviewer edit distance, latency, provider failure, retry count, artifact count, and cost placeholder.
  - Emit a JSON report and a short Markdown summary.
- Acceptance:
  - Report includes all success criteria fields from this document.
  - A failing report clearly states which GA discussion condition failed.
- Evidence:
  - Added collector module `src/omni_skill_pipeline/quality/trial_metrics.py`:
    - Aggregates review outcome, reviewer edit distance, latency, provider/runtime failures, retry count, artifact count, and cost placeholder fields.
    - Evaluates all trial success criteria and emits explicit failing condition IDs.
    - Marks critical GA blockers through `ga_discussion_blocked`.
  - Added CLI/report runner `scripts/trial_metrics.py`:
    - Emits JSON report and Markdown summary.
    - Supports `--fail-on-ga-blocker` for non-zero exit when critical GA conditions fail.
  - Added baseline template `docs/current/status/baselines/trial-metrics/trial-metrics-manifest.template.json`.
  - Added focused tests:
    - `tests/test_trial_metrics_collector.py`
    - `tests/test_trial_metrics_collector_script.py`
  - 2026-05-23 iterative re-check (run 1): re-ran focused CBT-05 metrics tests (`tests.test_trial_metrics_collector`, `tests.test_trial_metrics_collector_script`) and confirmed trial metrics JSON/Markdown outputs plus GA-blocker condition reporting remain passing; doc sync also remains green.
  - 2026-05-25 iterative re-check (run 2): re-verified CBT-05 collector/runner paths in `src/omni_skill_pipeline/quality/trial_metrics.py` and `scripts/trial_metrics.py`, re-ran focused tests (`tests.test_trial_metrics_collector`, `tests.test_trial_metrics_collector_script`), and re-ran `python scripts/doc_sync.py --output -`; all remained passing with GA-blocker condition reporting intact.

### CBT-06 Agent Skill Package Model

- Status: Complete
- Recommended model: Codex 5.5 for design, Codex 5.3 for implementation
- Goal: add a first-class package model for generated agent skills.
- Files: `src/omni_skill_pipeline/models.py`, `docs/current/architecture/`, tests under `tests/`
- Work:
  - Add `AgentSkillPackage` or equivalent model.
  - Include package name, description, target, files, references, validation status, source bundle, review status, and hashes.
  - Keep it separate from `SkillGraph`, which remains the semantic source of truth.
- Acceptance:
  - Model serializes cleanly.
  - Existing V2 model tests continue to pass.
- Evidence:
  - Added package-domain enums and models in `src/omni_skill_pipeline/models.py`:
    - `AgentSkillTarget`
    - `AgentSkillValidationStatus`
    - `AgentSkillPackage`
    - `AgentSkillPackageFile`
    - `AgentSkillPackageReference`
    - `AgentSkillPackageSourceBundle`
  - Added focused package validation contract (`AgentSkillPackage.validate`) that enforces:
    - required package name/description and non-empty file list
    - per-file and per-reference required field checks
    - source-bundle identifier presence
    - non-empty hash key/value pairs
  - Added focused tests in `tests/test_v2_models.py`:
    - `test_agent_skill_package_serialization_and_validation`
    - `test_agent_skill_package_validate_requires_source_bundle_identifier`
  - Added architecture doc `docs/current/architecture/agent-skill-package-model.md` and linked it in:
    - `docs/current/architecture/ARCHITECTURE.md`
    - `docs/INDEX.md`
  - 2026-05-23 iterative re-check (run 1): re-ran focused CBT-06 model tests (`tests.test_v2_models`) and confirmed `AgentSkillPackage` serialization/validation contracts remain passing with no regression; doc sync also remains green.

### CBT-07 Portable Skill Renderer

- Status: Complete
- Recommended model: Codex 5.3
- Goal: render a clean agent-native `SKILL.md`.
- Files: `src/omni_skill_pipeline/assembly/`, `src/omni_skill_pipeline/publication/`, tests under `tests/`
- Work:
  - Render YAML frontmatter with `name` and `description`.
  - Keep main `SKILL.md` concise.
  - Move long evidence, transcript, OCR, and examples into `references/`.
  - Include `Workflow`, `Decision Rules`, `Validation`, and `Failure Modes`.
- Acceptance:
  - Renderer tests assert frontmatter, required sections, and references split.
  - Main `SKILL.md` stays under the configured line limit.
- Evidence:
  - Added portable renderer module `src/omni_skill_pipeline/publication/portable_skill_renderer.py` and package export `src/omni_skill_pipeline/publication/__init__.py`.
  - `PublicationBuilder` now renders `PublicationType.SKILL_MARKDOWN` through `PortableSkillRenderer` with:
    - YAML frontmatter (`name`, `description`)
    - required sections (`Workflow`, `Decision Rules`, `Validation`, `Failure Modes`, `References`)
    - split references payload (`references/evidence.md`, `references/examples.md`)
    - line budget metadata (`line_count`, `line_limit`)
  - Added configurable line budget:
    - `Settings.portable_skill_markdown_line_limit`
    - env var `OMNI_PORTABLE_SKILL_MARKDOWN_LINE_LIMIT` (default `220`, floor `21`)
    - `.env.example` and `docs/current/operations/env.md` updated
  - `FileArtifactRepository` now writes markdown publication sidecar references into publication output tree:
    - `publications/references/evidence.md`
    - `publications/references/examples.md`
  - Added focused tests:
    - `tests/test_portable_skill_renderer.py`
    - `tests/test_publication_builder.py`
    - `tests/test_publication_orchestrator_split.py`
    - `tests/test_v2_schema_and_corpus.py`
    - `tests/test_service_factory_split.py`
    - `tests/test_openai_provider_config.py`
  - 2026-05-23 iterative re-check (run 1): re-ran focused CBT-07 renderer tests (`tests.test_portable_skill_renderer`, `tests.test_publication_builder`, `tests.test_publication_orchestrator_split`, `tests.test_v2_schema_and_corpus`, `tests.test_service_factory_split`, `tests.test_openai_provider_config`) and confirmed YAML frontmatter/required sections/reference split/line-budget behaviors remain passing; doc sync also remains green.

### CBT-08 Target Exporters

- Status: Complete
- Recommended model: Codex 5.3
- Goal: export packages for Codex, Claude Code, OpenCode, portable, and all targets.
- Files: `src/omni_skill_pipeline/cli.py`, `src/omni_skill_pipeline/exporters/`, `docs/current/operations/cli.md`, tests under `tests/`
- Work:
  - Add `export-skill` or `--export-agent-skill`.
  - Support `--target codex`, `--target claude-code`, `--target opencode`, `--target portable`, and `--target all`.
  - Write target-specific directory layouts.
- Acceptance:
  - CLI smoke tests prove every target writes `SKILL.md` to the expected path.
- Evidence:
  - Added exporter module `src/omni_skill_pipeline/exporters/agent_skill_exporter.py` and package export `src/omni_skill_pipeline/exporters/__init__.py`.
  - Added CLI command `export-skill` in `src/omni_skill_pipeline/cli.py` with `--bundle`, `--target`, `--output-root`, and support for `codex/claude-code/opencode/portable/all`.
  - Export now writes target-specific layouts and package metadata artifact `agent_skill_package.json` per target directory.
  - Added CLI operation doc updates in `docs/current/operations/cli.md` for `export-skill` usage and target mappings.
  - Added focused CLI smoke tests in `tests/test_cli.py`:
    - `test_export_skill_codex_target_writes_expected_layout`
    - `test_export_skill_claude_code_target_writes_expected_layout`
    - `test_export_skill_opencode_target_writes_expected_layout`
    - `test_export_skill_portable_target_writes_expected_layout`
    - `test_export_skill_all_target_writes_all_layouts`
  - 2026-05-23 iterative re-check (run 1): re-ran focused CBT-08 export-target CLI smoke tests (`tests.test_cli.CliCorpusCommandTests.test_export_skill_codex_target_writes_expected_layout`, `tests.test_cli.CliCorpusCommandTests.test_export_skill_claude_code_target_writes_expected_layout`, `tests.test_cli.CliCorpusCommandTests.test_export_skill_opencode_target_writes_expected_layout`, `tests.test_cli.CliCorpusCommandTests.test_export_skill_portable_target_writes_expected_layout`, `tests.test_cli.CliCorpusCommandTests.test_export_skill_all_target_writes_all_layouts`) and confirmed all target layouts still write expected `SKILL.md` artifacts; doc sync also remains green.

### CBT-09 Skill Usability Validator

- Status: Complete
- Recommended model: Codex 5.3
- Goal: reject packages that are not safe or usable enough for trial.
- Files: `src/omni_skill_pipeline/validation/`, `scripts/`, tests under `tests/`
- Work:
  - Validate frontmatter, name/description quality, required sections, max length, references, secret/path leakage, and dangerous command markers.
  - Emit explicit failure codes.
- Acceptance:
  - Validator catches missing frontmatter, weak description, leaked absolute path, token-like secret, and missing review approval.
- Evidence:
  - Added validator module `src/omni_skill_pipeline/validation/skill_usability.py` with explicit failure codes for:
    - frontmatter contract and name/description quality
    - required sections and max line budget
    - references directory presence/content
    - absolute-path leakage and token-like secret leakage
    - dangerous command markers and missing review approval signal
  - Added validation exports in `src/omni_skill_pipeline/validation/__init__.py`.
  - Added script runner `scripts/skill_usability.py` returning non-zero on failed validation and emitting JSON with `failure_codes`.
  - Added CLI command `validate-skill` in `src/omni_skill_pipeline/cli.py` with package-level status and failure-code output.
  - Added focused tests:
    - `tests/test_skill_usability_validator.py`
    - `tests/test_skill_usability_validator_script.py`
    - `tests/test_cli.py` (`validate-skill` pass/fail coverage)
  - Updated CLI docs `docs/current/operations/cli.md` with validator usage and exit-code contract.
  - 2026-05-23 iterative re-check (run 1): re-ran focused CBT-09 validator tests (`tests.test_skill_usability_validator`, `tests.test_skill_usability_validator_script`, `tests.test_cli.CliCorpusCommandTests.test_validate_skill_command_passes_for_safe_package`, `tests.test_cli.CliCorpusCommandTests.test_validate_skill_command_reports_failure_codes`) and confirmed usability failure-code contracts plus `validate-skill` CLI pass/fail paths remain passing; doc sync also remains green.

### CBT-10 Multimodal Trial Fixtures

- Status: Complete
- Recommended model: Codex 5.3
- Goal: create non-sensitive fixture packs for all trial modalities.
- Files: `examples/`, `docs/current/status/baselines/`, tests under `tests/`
- Work:
  - Add tiny representative fixtures or fixture manifests for text, audio transcript, image OCR stub, video keyframe/transcript stub, tabular data, and mixed corpus.
  - Avoid binary bloat. Use stubs where full media would be too large.
- Acceptance:
  - CI can run fixture-based tests without network access and without real provider calls.
- Evidence:
  - Added sanitized multimodal fixture pack under `examples/trial/`:
    - `text/slow-query-notes.md`, `text/query-bottleneck-summary.pdf`
    - `audio/incident-review-call.wav`, `audio/incident-review-call.transcript.md`
    - `image/service-latency-dashboard.png`, `image/error-rate-trend.png`
    - `video/feature-release-walkthrough.mp4`, `video/feature-release-walkthrough.srt`
    - `tabular/latency-error-report.csv`
    - `mixed/incident-postmortem.md`, `mixed/incident-dashboard.png`, `mixed/incident-review-transcript.md`
  - Added fixture inventory and usage notes: `examples/trial/README.md`.
  - Added focused offline fixture test suite `tests/test_trial_fixtures.py`:
    - validates all CBT-02 trial-manifest asset paths exist locally
    - runs text/audio/image/video/tabular distillation using fixture stubs without network/provider calls
    - runs mixed-corpus distillation loop on fixture bundle without network/provider calls

### CBT-11 End-to-End Trial Runner

- Status: Complete
- Recommended model: Codex 5.5 for flow review, Codex 5.3 for script implementation
- Goal: run one controlled-trial loop reproducibly.
- Files: `scripts/controlled_trial.py`, `docs/current/operations/runbooks/`, tests under `tests/`
- Work:
  - Input a trial manifest.
  - Run distillation.
  - Force review mode.
  - Produce reviewer packet.
  - Export agent skill package after simulated approval.
  - Run package validator.
  - Emit metrics report.
- Acceptance:
  - Dry-run mode produces an execution plan.
  - Smoke test runs fully on fixtures.
- Evidence:
  - Added runner script `scripts/controlled_trial.py` with full CBT-11 sequence:
    - trial-manifest validation
    - distillation request execution (single-asset and mixed corpus)
    - forced review mode through `OMNI_CONTROLLED_TRIAL_REVIEW_MODE`
    - reviewer packet presence check
    - simulated approval patch on bundle payload
    - target export + skill usability validation
    - trial-metrics manifest/report/summary generation
  - Added fixture-provider path (`--use-fixture-stubs`) for offline smoke execution without external provider/network requirements.
  - Added focused script tests `tests/test_controlled_trial_runner_script.py`:
    - dry-run execution plan generation
    - fixture smoke loop producing run report + metrics outputs
  - Added runbook `docs/current/operations/runbooks/controlled-trial-loop.md` and runbook index/baseline entry updates:
    - `docs/current/operations/runbooks/README.md`
    - `docs/current/status/baselines/README.md`

### CBT-12 Agent Smoke Protocol

- Status: Complete
- Recommended model: Codex 5.5
- Goal: define how approved skills are tested in a real agent workflow.
- Files: `docs/current/operations/runbooks/`, optional `scripts/`
- Work:
  - Define manual smoke checks for Codex, Claude Code, and OpenCode.
  - Define trigger prompt, expected skill selection, expected task output, and failure recording.
  - Keep live-agent runs separate from offline CI unless automation becomes reliable.
- Acceptance:
  - Every approved trial skill can be marked `agent_smoke_passed`, `agent_smoke_failed`, or `not_run` with reason.
- Evidence:
  - Added runbook `docs/current/operations/runbooks/agent-smoke-protocol.md` with:
    - manual smoke check flow for Codex, Claude Code, and OpenCode
    - trigger prompt contract
    - expected skill selection/output contract
    - explicit failure recording contract
    - live-agent/offline-CI separation rule for controlled trial
  - Added recorder script `scripts/agent_smoke.py`:
    - records one status row per `skill_id + agent`
    - supports statuses `agent_smoke_passed`, `agent_smoke_failed`, `not_run`
    - enforces non-empty `reason`
    - maps status to metrics-compatible `agent_smoke_result` (`passed`/`failed`/`not_run`)
    - writes/updates report `docs/current/status/baselines/controlled-trial/agent-smoke-report.json`
  - Added focused tests `tests/test_agent_smoke_record_script.py` covering:
    - pass path record creation
    - failure path contract enforcement (`agent_smoke_failed` requires `--failure-code`)
    - upsert path updating existing `skill_id + agent` record
  - Updated runbook index and baseline index:
    - `docs/current/operations/runbooks/README.md`
    - `docs/current/status/baselines/README.md`

### CBT-13 Trial Security Gate

- Status: Complete
- Recommended model: Codex 5.5 for policy, Codex 5.3 for implementation
- Goal: block unsafe trial artifacts before package export.
- Files: `src/omni_skill_pipeline/redaction.py`, `src/omni_skill_pipeline/validation/`, `scripts/`, tests under `tests/`
- Work:
  - Reuse existing redaction and extend package-level checks.
  - Reject secrets, private local absolute paths, dangerous production commands, and unapproved sensitive data classes.
  - Attach risk labels to reviewer packet.
- Acceptance:
  - Tests prove unsafe packages fail before export.
- Evidence:
  - Added dedicated gate module `src/omni_skill_pipeline/validation/trial_security_gate.py`:
    - reuses existing sensitive-key redaction heuristics (`is_sensitive_key`) and extends package-level blocking checks.
    - rejects secret/token leak patterns, private local absolute path leaks, dangerous production command markers, and unapproved sensitive data classes.
    - emits deterministic failure codes:
      - `TRIAL_SECRET_LEAK`
      - `TRIAL_PRIVATE_LOCAL_ABSOLUTE_PATH`
      - `TRIAL_DANGEROUS_PRODUCTION_COMMAND`
      - `TRIAL_UNAPPROVED_SENSITIVE_DATA_CLASS`
    - emits reviewer-packet-compatible `risk_labels`.
  - Added gate runner `scripts/trial_security.py`:
    - validates one bundle before export and returns non-zero on failure.
    - supports JSON output for audit evidence.
  - Enforced exporter pre-check in `src/omni_skill_pipeline/exporters/agent_skill_exporter.py`:
    - `export-skill` now fails fast before writing any target layout if trial security gate fails.
    - source URI mapping for exported evidence references now follows per-asset `corpus_assets` ownership when available.
  - Attached CBT-13 risk labels into reviewer packet generation in:
    - `src/omni_skill_pipeline/review/packet.py`
    - `src/omni_skill_pipeline/service.py`
    - risk labels now include `source=trial_security_gate` when unsafe markers are present.
  - Integrated gate into `scripts/controlled_trial.py`:
    - checks simulated-approved bundle before export.
    - records `trial_security_gate_report` per sample in run report.
  - Added focused tests:
    - `tests/test_trial_security_gate.py`
    - `tests/test_trial_security_gate_script.py`
    - `tests/test_agent_skill_exporter_security_gate.py`
    - `tests/test_reviewer_packet.py` (risk-label coverage)
    - `tests/test_cli.py` (`export-skill` gate-failure path)
    - `tests/test_controlled_trial_runner_script.py` (`trial_security_gate_report` presence)

### CBT-14 Trial Report and GO/GA Decision

- Status: Complete
- Recommended model: Codex 5.5
- Goal: convert trial evidence into a decision.
- Files: `docs/current/status/baselines/`, `docs/current/status/`
- Work:
  - Add a final controlled-trial report template.
  - Include modality coverage, approval rate, edit distance, agent smoke success, cost, failures, and reviewer notes.
  - Define decisions: `CONTINUE_TRIAL`, `EXPAND_BETA`, `HOLD_FOR_REMEDIATION`, `GA_CANDIDATE`.
- Acceptance:
  - A reviewer can decide the next launch level from the report without reading raw artifacts.
- Evidence:
  - Added final report template `docs/current/status/baselines/controlled-trial/controlled-trial-final-report.template.md` with:
    - required evidence input section for `controlled-trial-run-report.json`, `trial-metrics-report.json`, `trial-metrics-summary.md`, `agent-smoke-report.json`, and security-gate evidence.
    - required metric sections covering modality coverage, approval rate, reviewer edit distance, agent smoke success, cost, failures, and reviewer notes.
    - decision section with constrained decision set:
      - `CONTINUE_TRIAL`
      - `EXPAND_BETA`
      - `HOLD_FOR_REMEDIATION`
      - `GA_CANDIDATE`
    - explicit rule that `GA_CANDIDATE` means entering GA-readiness review, not direct GA declaration.
  - Updated baseline index `docs/current/status/baselines/README.md` with CBT-14 entry and report-template path, so reviewers can locate the decision template from the baseline entry doc.

## Recommended Execution Order

1. `CBT-01`, `CBT-02`, `CBT-03`
2. `CBT-04`, `CBT-05`, `CBT-10`
3. `CBT-06`, `CBT-07`, `CBT-08`, `CBT-09`
4. `CBT-11`, `CBT-12`, `CBT-13`
5. `CBT-14`

## Non-Goals For This Iteration

- Do not build full multi-tenant account management.
- Do not build a large review UI before reviewer packets prove the workflow.
- Do not require pgvector/Qdrant for the first controlled trial.
- Do not auto-publish skills from trial outputs.
- Do not promise formal GA before real trial evidence exists.
