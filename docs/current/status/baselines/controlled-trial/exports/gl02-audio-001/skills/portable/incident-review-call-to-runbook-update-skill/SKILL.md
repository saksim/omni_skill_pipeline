---
name: "incident review call to runbook update skill"
description: "Use when Use when converting audio evidence into build_skill.. Merge those monitors into one incident stream before next shift."
---

# incident review call to runbook update skill

## Workflow
1. Evaluate rule: Merge those monitors into one incident stream before next shift. (Why: Derived from rule atom fallback because no procedure atoms were found.)

## Decision Rules
- When rule conditions are met. -> Merge those monitors into one incident stream before next shift.

## Validation
- Confirm each key conclusion can be traced back to evidence_refs.

## Failure Modes
- Do not auto-publish trial output before human review approval.

## References
- [Evidence](references/evidence.md)
- [Examples](references/examples.md)
