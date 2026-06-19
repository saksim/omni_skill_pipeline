# Internal Dogfood Launch Docs

This directory contains working-level construction and verification documents
for the internal dogfood launch track.

Use `docs/latest/operations/` for current operator manuals. Use this directory
only when you need the historical construction plan, gate details, launch record
template, or risk notes behind the internal dogfood decision.

## Documents

- [Construction Plan](../2026-06-18-internal-dogfood-launch-construction-plan.md)
- [P0 Workflow Fail Remediation](p0-workflow-fail-remediation.md)
- [Internal Dogfood Gate Spec](internal-dogfood-gate-spec.md)
- [Verification Runbook](verification-runbook.md)
- [Risk, Rollback, and Observation](risk-rollback-observation.md)
- [Launch Record Template](launch-record-template.md)

## Boundary

Internal dogfood is not external Beta, GA, or SaaS.

It proves:

- internal operators can start the current code
- CI and basic smoke checks have no blocking failure for the internal path
- generated skills can be reviewed and used internally
- limitations and rollback points are recorded

It does not prove:

- real external business-loop coverage
- production uptime or public reliability
- safe automated publication without human review
- replacement of `scripts/launch_gate.py` for external launch decisions
