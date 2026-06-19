# Operations Index

This is the current operations entry point for `v0.2.3-internal.1`.

The current supported launch posture is internal dogfood only. Use these docs
to run, verify, package, and operate the repository in the internal path. Do not
use them as evidence for external Beta, GA, SaaS, Docker/Postgres production, or
K8s readiness.

## Current Operator Path

1. Prepare the environment with [Environment](env.md) and `.env.example`.
2. Verify local CLI/package availability with [CLI](cli.md).
3. Run the local regression gate in [Testing](testing.md).
4. For GitHub release packaging, follow
   [GitHub Release Workflow](runbooks/github-release-workflow.md).
5. For file-backed artifact protection, follow
   [Artifact Encryption](runbooks/artifact-encryption.md).
6. For live internal API dogfood evidence, use the internal dogfood smoke
   command documented in the release notes and runbooks.

## Current Operation Domains

- [CLI](cli.md)
- [API](api.md)
- [Worker](worker.md)
- [Environment](env.md)
- [Testing](testing.md)
- [Script Name Map](script-name-map.md)
- GitHub release workflow: `.github/workflows/release.yml`
- Standard Linux release test script: `bash scripts/linux_release.sh`
- [V1 -> V2 Migration Runbook](v1-to-v2-migration-runbook.md)

## Expansion Zones

- [Runbooks](runbooks/README.md)
- [GitHub Release Workflow](runbooks/github-release-workflow.md)
- [Artifact Encryption](runbooks/artifact-encryption.md)
- [Docker Zero-to-Release Runbook](runbooks/docker-zero-to-release.md)
- [Launch Beta Runbook](runbooks/launch-beta.md)
- [Production Operations Baseline](runbooks/production-operations-baseline.md)
- [Controlled External Beta Onboarding](runbooks/controlled-external-beta-onboarding.md)
- [Environments](environments/README.md)
- [Interfaces](interfaces/README.md)

## Current Boundaries

- `v0.2.3-internal.1` completes the non-infrastructure internal dogfood path.
- Local file artifact encryption is optional and off by default.
- Docker, Postgres, K8s, Vault/KMS, automated key rotation, OCR hardening, and
  external real-loop collection are not current completed release claims.
- `scripts/launch_gate.py` may still return `HOLD`; that blocks external launch
  claims, not internal dogfood operation.

## Notes

- This is the current operations documentation entry point.
- Detailed instructions are split by execution surface so CLI, API, worker, environment, runbook, and script-name material stay maintainable.
