# Runbooks

## Available Runbooks

- Standard pre-release test script: `bash scripts/linux_release.sh`
- [Docker Zero-to-Release](docker-zero-to-release.md): bare Linux, Docker-only testing, release gate, deploy, acceptance, rollback.
- [Launch Beta](launch-beta.md): external beta deploy, acceptance, rollback, log inspection, and temp cleanup.
- [Production Operations Baseline](production-operations-baseline.md): GL-05 production operations workflow for deploy, validation, rollback, backup/restore, incident response, alerting, and operations evidence collection.
- [Controlled External Beta Onboarding](controlled-external-beta-onboarding.md): GL-03 operator flow for manifest validation, distill, review, export, validation, security gate, metrics, and readiness decision.
- [Controlled Trial Loop](controlled-trial-loop.md): CBT-11 end-to-end controlled-trial runner (`manifest -> distill -> review packet -> export -> validate -> metrics`).
- [Real Trial Loop Collection](real-trial-loop-collection.md): GL-12 collector plus GL-13 one-command bridge for real-loop evidence classification, trial metrics generation, and launch-gate progress tracking.
- [Agent Smoke Protocol](agent-smoke-protocol.md): CBT-12 manual live-agent smoke checks for Codex/Claude Code/OpenCode plus status recording (`agent_smoke_passed` / `agent_smoke_failed` / `not_run`).

## Notes

- Runbooks are executable operations docs; keep commands aligned with `scripts/` and current API contracts.
- For pre-release evidence collection, prefer `scripts/linux_release.sh` over manually copying individual commands. It produces `release-artifacts-<release_id>.tar.gz` with logs, exit codes, baselines, and summary files.
