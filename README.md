# Omni Skill Pipeline

Omni Skill Pipeline distills text, audio, image, video, tabular, and mixed
corpus evidence into reusable, traceable, reviewable skill artifacts:
`SKILL.md`, `skill.json`, `SkillGraph`, publication manifests, and portable
agent skill packages.

The current published release is `v0.2.3-internal.1`. It is an internal
dogfood release, not an external Beta, GA, SaaS, or production deployment
claim.

## Current Capabilities

- Text: `txt`, `md`, `markdown`, `rst`, `log`, `json`, `html`, `doc`, `docx`,
  and `pdf` inputs.
- Audio: transcript-first and optional OpenAI ASR path.
- Image: OCR and scene-summary evidence extraction, still requiring human
  review for uncertain visual/OCR output.
- Video: transcript, keyframe, OCR, scene summary, and timeline evidence.
- Tabular/time-series: `TABLE`, `METRIC`, and `EVENT` evidence generation.
- V2 semantics: `Corpus`, `EvidenceNode`, `SemanticAtom`, `SkillGraph`, and
  `Publication`.
- Review controls: quality scoring, review policy, review task, review
  feedback, reviewer packet, and review queue operations.
- Release handoff: GitHub Release artifact pack, checksums, installable wheel,
  release notes, and release consumer smoke.
- Internal dogfood hardening: live API smoke evidence and optional Fernet
  encryption for file-backed local artifacts.

## Quick Start

PowerShell:

```powershell
py -3.11 -m venv .venv
. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python -m omni_skill_pipeline.cli show-template
```

POSIX:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python -m omni_skill_pipeline.cli show-template
```

Run the normal local regression gate:

```bash
python scripts/ci.py --isolate-test-files --coverage-fail-under 50 --coverage-xml coverage.xml
```

## Main Entry Points

- Package root: `src/omni_skill_pipeline/`
- CLI entry: `src/omni_skill_pipeline/cli.py`
- API app: `apps/api/main.py`
- Worker app: `apps/worker/main.py`
- Template contract: `docs/latest/contracts/SKILL.template.md`
- Skill schema: `docs/latest/contracts/skill.schema.json`
- Operations index: `docs/latest/operations/OPERATIONS.md`

## Release

- Current internal release: `v0.2.3-internal.1`
- CI gate: `.github/workflows/ci.yml`
- Release workflow: `.github/workflows/release.yml`
- Release notes: `docs/releases/notes/v0.2.3-internal.1.md`
- GitHub Release runbook:
  `docs/latest/operations/runbooks/github-release-workflow.md`
- Local artifact encryption runbook:
  `docs/latest/operations/runbooks/artifact-encryption.md`

Formal GitHub Releases are created from `v*` tags or by manually dispatching
the `Release` workflow with `publish_github_release=true` and `release_tag`.
The release workflow builds a source archive, wheel, `coverage.xml`,
`release-manifest.json`, `release-summary.md`, `SHA256SUMS`, and runs the
release consumer smoke before upload/publication.

## Documentation Layers

- `docs/latest/`: latest published manuals and current operating references.
- `docs/working/`: current iteration plans, status, baselines, and evidence.
- `docs/releases/`: changelog, release notes, and release decision standards.
- `docs/archive/`: historical assessments, superseded status snapshots, and
  archived completed capability records.

Start from `docs/INDEX.md` when deciding which document to use.

## Current Engineering Position

The internal dogfood path is ready for internal use. The broad external launch
gate remains `HOLD` because launch-gate-eligible real business loops are still
insufficient. Docker, Postgres, K8s, Vault/KMS, production key rotation, OCR
hardening, and external real-loop collection remain outside the completed
internal release boundary unless a future release explicitly closes them.
