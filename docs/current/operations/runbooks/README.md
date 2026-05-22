# Runbooks

## Available Runbooks

- Standard pre-release test script: `bash scripts/run_linux_release_test.sh`
- [Docker Zero-to-Release](docker-zero-to-release.md): bare Linux, Docker-only testing, release gate, deploy, acceptance, rollback.
- [Launch Beta](launch-beta.md): external beta deploy, acceptance, rollback, log inspection, and temp cleanup.
- [Controlled Trial Loop](controlled-trial-loop.md): CBT-11 end-to-end controlled-trial runner (`manifest -> distill -> review packet -> export -> validate -> metrics`).
- [Agent Smoke Protocol](agent-smoke-protocol.md): CBT-12 manual live-agent smoke checks for Codex/Claude Code/OpenCode plus status recording (`agent_smoke_passed` / `agent_smoke_failed` / `not_run`).

## Notes

- Runbooks are executable operations docs; keep commands aligned with `scripts/` and current API contracts.
- For pre-release evidence collection, prefer `scripts/run_linux_release_test.sh` over manually copying individual commands. It produces `release-artifacts-<release_id>.tar.gz` with logs, exit codes, baselines, and summary files.
