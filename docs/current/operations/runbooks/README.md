# Runbooks

## Available Runbooks

- Standard pre-release test script: `bash scripts/run_linux_release_test.sh`
- [Docker Zero-to-Release](docker-zero-to-release.md): bare Linux, Docker-only testing, release gate, deploy, acceptance, rollback.
- [Launch Beta](launch-beta.md): external beta deploy, acceptance, rollback, log inspection, and temp cleanup.

## Notes

- Runbooks are executable operations docs; keep commands aligned with `scripts/` and current API contracts.
- For pre-release evidence collection, prefer `scripts/run_linux_release_test.sh` over manually copying individual commands. It produces `release-artifacts-<release_id>.tar.gz` with logs, exit codes, baselines, and summary files.
