---
name: "screen recording walkthrough to SOP skill"
description: "Use when Use when converting video evidence into build_skill.. Open release dashboard and verify gate status is GO."
---

# screen recording walkthrough to SOP skill

## Workflow
1. Evaluate rule: If regression persists, roll back and attach evidence pack. (Why: Derived from rule atom fallback because no procedure atoms were found.)
2. Evaluate rule: If regression persists, roll back and attach evidence pack. (Why: Derived from rule atom fallback because no procedure atoms were found.)

## Decision Rules
- If regression persists, roll back and attach evidence pack. -> Apply the matching action.

## Validation
- Open release dashboard and verify gate status is GO.

## Failure Modes
- Do not auto-publish trial output before human review approval.

## References
- [Evidence](references/evidence.md)
- [Examples](references/examples.md)
