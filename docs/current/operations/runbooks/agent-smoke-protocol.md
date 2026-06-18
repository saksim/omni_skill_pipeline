# Agent Smoke Protocol

## Verdict

This runbook implements CBT-12 by defining one manual, reproducible smoke protocol for approved skills on:

- Codex
- Claude Code
- OpenCode

The goal is controlled-trial verification, not GA automation.

## Scope

- Run live-agent smoke checks outside offline CI.
- Use one approved skill package at a time.
- Record one status per `skill_id + agent`:
  - `agent_smoke_passed`
  - `agent_smoke_failed`
  - `not_run`

## Preconditions

- Skill package already approved by human review.
- Target package exported for the selected agent.
- Trial environment does not include regulated data or production secrets.

## Smoke Template

For each agent run, define and preserve these fields:

- `trigger_prompt`: exact prompt sent to the agent.
- `expected_skill_selection`: expected skill identity (`package_name` or folder name).
- `expected_task_output`: expected output behavior.
- `selected_skill`: observed skill identity.
- `observed_task_output`: observed output behavior.
- `status`: `agent_smoke_passed` / `agent_smoke_failed` / `not_run`.
- `reason`: short reason for the chosen status.
- `failure_code`: required when status is `agent_smoke_failed`.

## Trigger Prompt Contract

Use a prompt that makes skill selection testable:

1. Mention scenario and desired outcome.
2. Require a concrete deliverable.
3. Include a validation request.

Example:

```text
Use the incident runbook skill to triage this sanitized outage summary.
Return: (1) root-cause hypothesis, (2) rollback decision, (3) post-checklist.
Include evidence references for each recommendation.
```

## Agent-Specific Manual Checks

### Codex

1. Ensure skill is discoverable in Codex skill path.
2. Run trigger prompt.
3. Verify selected skill and output against expectations.
4. Record status using the script below.

### Claude Code

1. Ensure `SKILL.md` is discoverable under Claude skill path.
2. Run the same trigger prompt.
3. Verify selected skill and output.
4. Record status.

### OpenCode

1. Ensure `SKILL.md` is discoverable under OpenCode skill path.
2. Run the same trigger prompt.
3. Verify selected skill and output.
4. Record status.

## Recording Command

Script: `scripts/agent_smoke.py`

Report output (default):

- `docs/current/status/baselines/controlled-trial/agent-smoke-report.json`

### Passed Example

```bash
python scripts/agent_smoke.py \
  --skill-id trial-skill-001 \
  --agent codex \
  --status agent_smoke_passed \
  --reason "Selected expected skill and produced expected checklist." \
  --trigger-prompt "Use the incident runbook skill to triage the sample issue." \
  --expected-skill-selection incident-runbook-skill \
  --expected-task-output "Checklist with rollback and validation steps." \
  --selected-skill incident-runbook-skill \
  --observed-task-output "Produced checklist with rollback and validation."
```

### Failed Example

```bash
python scripts/agent_smoke.py \
  --skill-id trial-skill-001 \
  --agent claude-code \
  --status agent_smoke_failed \
  --reason "Skill selected but validation section missing." \
  --trigger-prompt "Use the incident runbook skill to triage the sample issue." \
  --expected-skill-selection incident-runbook-skill \
  --expected-task-output "Checklist with rollback and validation steps." \
  --selected-skill incident-runbook-skill \
  --observed-task-output "Output omitted validation checks." \
  --failure-code missing_validation_section
```

### Not Run Example

```bash
python scripts/agent_smoke.py \
  --skill-id trial-skill-001 \
  --agent opencode \
  --status not_run \
  --reason "Agent environment unavailable in this window." \
  --trigger-prompt "Use the incident runbook skill to triage the sample issue." \
  --expected-skill-selection incident-runbook-skill \
  --expected-task-output "Checklist with rollback and validation steps."
```

## Separation Rule

- Keep live-agent smoke checks manual in controlled trial.
- Do not gate offline CI on live-agent availability unless reliability is proven and explicitly approved.

## Exit Criteria

CBT-12 acceptance is met when each approved skill can be recorded for each target agent as:

- `agent_smoke_passed`, or
- `agent_smoke_failed`, or
- `not_run`,

and each record includes a non-empty reason.
