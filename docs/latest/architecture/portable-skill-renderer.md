# Portable Skill Renderer

## Purpose

`PortableSkillRenderer` converts `SkillDocument + SkillGraph` into an agent-native `SKILL.md` that stays concise for controlled-trial usage while preserving long-form evidence in `references/`.

The renderer is intentionally separate from semantic modeling:

- `SkillGraph` remains the semantic source of truth.
- Portable rendering is a publication view optimized for Codex / Claude Code / OpenCode style consumption.

## Output Contract

`src/omni_skill_pipeline/publication/portable_skill_renderer.py`

- Frontmatter:
  - `name`
  - `description` (trigger-oriented summary)
- Required sections:
  - `Workflow`
  - `Decision Rules`
  - `Validation`
  - `Failure Modes`
  - `References`
- References split:
  - `references/evidence.md`
  - `references/examples.md`

## Line-Limit Contract

- Main `SKILL.md` line count is capped by `line_limit`.
- Default line limit: `220`.
- Config/env control:
  - `OMNI_PORTABLE_SKILL_MARKDOWN_LINE_LIMIT` (minimum enforced: `21`)

When the source graph is long, the renderer keeps required sections but trims extra bullets first, and keeps long evidence payload in references files.

## Publication Integration

`PublicationBuilder` now uses `PortableSkillRenderer` for `PublicationType.SKILL_MARKDOWN`:

- publication content includes:
  - `text`
  - `description`
  - `line_count`
  - `line_limit`
  - `references`
- metadata renderer tag:
  - `portable_skill_markdown_v1`

`FileArtifactRepository` writes the main `SKILL.md` plus reference files under publication output:

- `publications/SKILL.md`
- `publications/references/evidence.md`
- `publications/references/examples.md`

## Controlled-Trial Positioning

This renderer supports **controlled business trial** and **controlled external beta pre-trial** workflow only:

- all artifacts remain review-first (`REVIEW_REQUIRED` when trial review mode is enabled)
- no GA claim is implied by portable render output alone
