# Completed Capabilities Archive 2026-06-19

This archive records capabilities that have graduated out of active
construction by `v0.2.3-internal.1`. It is historical evidence for what the
project has already completed. It is not the current operations manual; use
`docs/latest/` for current procedures.

## Archive Decision

The project has completed an internal dogfood release track for the
non-infrastructure path:

- package and source publication through GitHub Releases
- installed-wheel consumer verification
- internal API dogfood smoke
- review queue visibility for dogfood output
- local file-backed artifact encryption

This is sufficient for internal dogfood. It is not sufficient for an external
Beta, GA, SaaS, or production-runtime claim.

## Completed Release Milestones

| Release | Completion Status | Completed Capability |
| --- | --- | --- |
| `v0.2.0-internal.1` | Archived complete | Formal GitHub Release workflow, release artifact pack, release manifest, release summary, checksums, and operator release runbook. |
| `v0.2.1-internal.1` | Archived complete | Packaged contract resources inside the wheel, installed-wheel template fallback, release consumer smoke script, and workflow consumer-smoke gate. |
| `v0.2.2-internal.1` | Archived complete | Internal dogfood API smoke path for health, template, text distill, pending review queue visibility, JSON/Markdown smoke evidence, and API version metadata alignment. |
| `v0.2.3-internal.1` | Archived complete | Optional Fernet envelopes for file-backed local artifacts, encrypted review queue continuity, missing-key failure behavior, config wiring, and service factory wiring. |

## Completed Capability Areas

### Documentation Lifecycle

- The repository uses four lifecycle layers:
  - `docs/latest/`: current published manuals.
  - `docs/working/`: active iteration plans, baselines, and evidence.
  - `docs/releases/`: changelog, release notes, and release standards.
  - `docs/archive/`: historical and completed-capability records.
- The current index is `docs/INDEX.md`.
- Root documentation is kept in `README.md`.

### Core Distillation Path

- The project has a working evidence-to-skill pipeline for text, audio, image,
  video, tabular/time-series, and corpus inputs.
- The V2 semantic layer includes `Corpus`, `EvidenceNode`, `SemanticAtom`,
  `SkillGraph`, and `Publication`.
- File-backed distillation writes skill documents, bundle metadata, publication
  manifests, quality artifacts, review artifacts, and reviewer packets under
  `skills/drafts/`.

### Review And Governance

- Quality scoring, review policy, review task creation, review feedback,
  reviewer packet generation, and review queue operations are implemented.
- Review queue operations support list, claim/consume, close, approve, reject,
  and needs-rework flows.
- Early governance surfaces exist for cost/audit/deletion/retention records,
  tenant access controls, quota checks, and platform-console summary views.

### Release And Consumer Handoff

- The `Release` workflow builds source, wheel, coverage, manifest, summary, and
  checksum assets.
- Human-readable release notes are stored in `docs/releases/notes/`.
- `scripts/release_consumer_smoke.py` verifies checksums, manifest contract,
  wheel installation, and installed CLI template access.
- The release consumer smoke is wired into `.github/workflows/release.yml`
  before artifact upload/publication.

### Internal Dogfood Runtime Evidence

- `scripts/internal_launch_gate.py` can distinguish internal dogfood readiness
  from the stricter external launch gate.
- `scripts/internal_dogfood_smoke.py` validates local API health, template
  retrieval, text distillation, and pending review queue visibility.
- Current internal dogfood readiness evidence reports
  `READY_FOR_INTERNAL_DOGFOOD`.
- The external launch gate remains `HOLD`; that is expected and correct.

### Local Artifact Encryption

- `FileArtifactRepository` supports optional `fernet` encryption for local
  artifact files and review queue files.
- Encryption is disabled by default for backwards compatibility.
- Encrypted artifacts remain queryable and consumable when the same configured
  key is available.
- Existing plaintext artifacts remain readable while encryption is disabled.

## Explicit Non-Completed Items

The following items are not archived as complete and must not be presented as
current release claims:

- external Beta readiness
- GA readiness
- public SaaS readiness
- launch-gate-eligible real business loop volume
- OCR hardening beyond existing review-required behavior
- Docker real-run closure in this environment
- Postgres production validation
- K8s, Helm, or Kubernetes operations
- Vault/KMS integration
- automated key rotation
- production backup/restore validation against live infrastructure
- broad public performance benchmark

## Evidence Pointers

- Release notes:
  - `docs/releases/notes/v0.2.0-internal.1.md`
  - `docs/releases/notes/v0.2.1-internal.1.md`
  - `docs/releases/notes/v0.2.2-internal.1.md`
  - `docs/releases/notes/v0.2.3-internal.1.md`
- Current release changelog: `docs/releases/CHANGELOG.md`
- GitHub Release runbook:
  `docs/latest/operations/runbooks/github-release-workflow.md`
- Artifact encryption runbook:
  `docs/latest/operations/runbooks/artifact-encryption.md`
- Internal dogfood readiness summary:
  `docs/working/status/baselines/internal-dogfood-readiness-summary.md`
- Internal dogfood API smoke summary:
  `docs/working/status/baselines/internal-dogfood-api-smoke-summary.md`

## Maintenance Rule

When a future release completes one of the explicit non-completed items, add a
new release note under `docs/releases/notes/`, update the current operation
manual in `docs/latest/`, and create a new archive record only after the
capability has shipped and passed its documented evidence gate.
