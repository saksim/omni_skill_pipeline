# Latest Docs

Latest is the published manual layer: the documentation someone should use today.

Current published internal release: `v0.2.3-internal.1`.

Use this layer for:

- Architecture and data-flow references that describe the current system.
- Contracts, schemas, and templates consumed by runtime or release tooling.
- Operations runbooks for API, CLI, worker, environment, testing, and deployment flows.

Do not put iteration plans, generated evidence, or historical snapshots here.

## Primary Manuals

- Operations: `operations/OPERATIONS.md`
- Runbooks: `operations/runbooks/README.md`
- GitHub Release workflow: `operations/runbooks/github-release-workflow.md`
- Artifact encryption: `operations/runbooks/artifact-encryption.md`
- Environment variables: `operations/env.md`

## Boundary

The current latest manuals support internal dogfood operation. External Beta,
GA, SaaS, Docker/Postgres production, K8s, Vault/KMS, automated key rotation,
and OCR hardening require separate evidence gates before they can be treated as
completed release claims.
