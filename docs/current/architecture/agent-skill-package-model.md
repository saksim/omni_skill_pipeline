# Agent Skill Package Model

## Purpose

`AgentSkillPackage` is a packaging-domain model for controlled business trial outputs.  
It does not replace `SkillGraph`. `SkillGraph` remains the semantic source of truth; package models only describe deployable skill artifacts for agent runtimes.

## Separation of Concerns

- `SkillGraph`: semantic structure, evidence traceability, and lifecycle semantics.
- `AgentSkillPackage`: target runtime package metadata, file inventory, reference pointers, validation status, review status, and integrity hashes.

## Model Summary

Core model (`src/omni_skill_pipeline/models.py`):

- `AgentSkillPackage`
  - `package_name`
  - `description`
  - `target` (`codex`, `claude-code`, `opencode`, `portable`, `all`)
  - `files` (`AgentSkillPackageFile[]`)
  - `references` (`AgentSkillPackageReference[]`)
  - `validation_status` (`pending`, `passed`, `failed`)
  - `source_bundle` (`AgentSkillPackageSourceBundle`)
  - `review_status` (`draft`, `review_pending`, `published`, `rejected`)
  - `hashes`
  - `metadata`
  - `created_at`
  - `package_id`
- `AgentSkillPackageFile`
  - `relative_path`
  - `category`
  - `required`
  - `media_type`
  - `size_bytes`
  - `sha256`
- `AgentSkillPackageReference`
  - `reference_id`
  - `title`
  - `source_uri`
  - `reference_type`
  - `evidence_refs`
  - `metadata`
- `AgentSkillPackageSourceBundle`
  - `bundle_id`
  - `graph_id`
  - `skill_id`
  - `corpus_id`
  - `artifact_manifest_path`
  - `metadata`

## Validation Contract

`AgentSkillPackage.validate()` enforces:

- non-empty `package_name` and `description`
- non-empty package `files`
- per-file field checks
- per-reference field checks
- `source_bundle` has at least one source identifier
- all hash keys and values are non-empty

This keeps package metadata explicit and auditable before exporter/runtime integration.
