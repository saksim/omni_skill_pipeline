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

### CBT-02 Trial Sample Manifest

- Status: Complete
- Recommended model: Codex 5.3
- Goal: define a machine-readable manifest for controlled trial samples.
- Files: `docs/current/status/baselines/`, optional `scripts/validate_trial_manifest.py`, tests under `tests/`
- Work:
  - Add a trial sample manifest template with modality, scenario, source owner, sensitivity, asset list, review owner, target package format, and expected output type.
  - Add validation for required fields and unsupported sensitivity levels.
- Acceptance:
  - Invalid manifests fail with actionable messages.
  - Example manifests exist for text, audio, image, video, tabular, and mixed corpus.
- Evidence:
  - Added template `docs/current/status/baselines/trial-manifests/trial-sample-manifest.template.json` with required fields: `modality`, `scenario`, `source_owner`, `sensitivity`, `asset_list`, `review_owner`, `target_package_format`, `expected_output_type`.
  - Added modality examples: `trial-sample-text.example.json`, `trial-sample-audio.example.json`, `trial-sample-image.example.json`, `trial-sample-video.example.json`, `trial-sample-tabular.example.json`, `trial-sample-mixed-corpus.example.json`.
  - Added validator `scripts/validate_trial_manifest.py` with actionable errors for missing required fields and unsupported `sensitivity`/`modality`/`target_package_format`.
  - Added focused tests `tests/test_validate_trial_manifest_script.py` for valid manifest pass path plus invalid-field actionable failure paths.

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

### CBT-05 Trial Metrics Collector

- Recommended model: Codex 5.3
- Goal: record whether the trial is working.
- Files: `scripts/`, `src/omni_skill_pipeline/quality/`, `docs/current/status/baselines/`, tests under `tests/`
- Work:
  - Collect review outcome, reviewer edit distance, latency, provider failure, retry count, artifact count, and cost placeholder.
  - Emit a JSON report and a short Markdown summary.
- Acceptance:
  - Report includes all success criteria fields from this document.
  - A failing report clearly states which GA discussion condition failed.

### CBT-06 Agent Skill Package Model

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

### CBT-07 Portable Skill Renderer

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

### CBT-08 Target Exporters

- Recommended model: Codex 5.3
- Goal: export packages for Codex, Claude Code, OpenCode, portable, and all targets.
- Files: `src/omni_skill_pipeline/cli.py`, `src/omni_skill_pipeline/exporters/`, `docs/current/operations/cli.md`, tests under `tests/`
- Work:
  - Add `export-skill` or `--export-agent-skill`.
  - Support `--target codex`, `--target claude-code`, `--target opencode`, `--target portable`, and `--target all`.
  - Write target-specific directory layouts.
- Acceptance:
  - CLI smoke tests prove every target writes `SKILL.md` to the expected path.

### CBT-09 Skill Usability Validator

- Recommended model: Codex 5.3
- Goal: reject packages that are not safe or usable enough for trial.
- Files: `src/omni_skill_pipeline/validation/`, `scripts/`, tests under `tests/`
- Work:
  - Validate frontmatter, name/description quality, required sections, max length, references, secret/path leakage, and dangerous command markers.
  - Emit explicit failure codes.
- Acceptance:
  - Validator catches missing frontmatter, weak description, leaked absolute path, token-like secret, and missing review approval.

### CBT-10 Multimodal Trial Fixtures

- Recommended model: Codex 5.3
- Goal: create non-sensitive fixture packs for all trial modalities.
- Files: `examples/`, `docs/current/status/baselines/`, tests under `tests/`
- Work:
  - Add tiny representative fixtures or fixture manifests for text, audio transcript, image OCR stub, video keyframe/transcript stub, tabular data, and mixed corpus.
  - Avoid binary bloat. Use stubs where full media would be too large.
- Acceptance:
  - CI can run fixture-based tests without network access and without real provider calls.

### CBT-11 End-to-End Trial Runner

- Recommended model: Codex 5.5 for flow review, Codex 5.3 for script implementation
- Goal: run one controlled-trial loop reproducibly.
- Files: `scripts/run_controlled_trial.py`, `docs/current/operations/runbooks/`, tests under `tests/`
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

### CBT-12 Agent Smoke Protocol

- Recommended model: Codex 5.5
- Goal: define how approved skills are tested in a real agent workflow.
- Files: `docs/current/operations/runbooks/`, optional `scripts/`
- Work:
  - Define manual smoke checks for Codex, Claude Code, and OpenCode.
  - Define trigger prompt, expected skill selection, expected task output, and failure recording.
  - Keep live-agent runs separate from offline CI unless automation becomes reliable.
- Acceptance:
  - Every approved trial skill can be marked `agent_smoke_passed`, `agent_smoke_failed`, or `not_run` with reason.

### CBT-13 Trial Security Gate

- Recommended model: Codex 5.5 for policy, Codex 5.3 for implementation
- Goal: block unsafe trial artifacts before package export.
- Files: `src/omni_skill_pipeline/redaction.py`, `src/omni_skill_pipeline/validation/`, `scripts/`, tests under `tests/`
- Work:
  - Reuse existing redaction and extend package-level checks.
  - Reject secrets, private local absolute paths, dangerous production commands, and unapproved sensitive data classes.
  - Attach risk labels to reviewer packet.
- Acceptance:
  - Tests prove unsafe packages fail before export.

### CBT-14 Trial Report and GO/GA Decision

- Recommended model: Codex 5.5
- Goal: convert trial evidence into a decision.
- Files: `docs/current/status/baselines/`, `docs/current/status/`
- Work:
  - Add a final controlled-trial report template.
  - Include modality coverage, approval rate, edit distance, agent smoke success, cost, failures, and reviewer notes.
  - Define decisions: `CONTINUE_TRIAL`, `EXPAND_BETA`, `HOLD_FOR_REMEDIATION`, `GA_CANDIDATE`.
- Acceptance:
  - A reviewer can decide the next launch level from the report without reading raw artifacts.

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
