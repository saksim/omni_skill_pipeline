---
name: "dashboard screenshots to alert diagnostic skill"
description: "Use when Use when converting image evidence into build_skill.. Fixture OCR: service latency dashboard status: degraded"
---

# dashboard screenshots to alert diagnostic skill

## Workflow
1. Fixture OCR: service latency dashboard status: degraded (Why: Derived from evidence fallback because no procedure atoms were found.)
2. Fixture OCR: service latency dashboard (Why: Derived from evidence fallback because no procedure atoms were found.)
3. status: degraded (Why: Derived from evidence fallback because no procedure atoms were found.)

## Decision Rules
- No explicit branch rule was extracted; execute workflow order first.

## Validation
- Confirm each key conclusion can be traced back to evidence_refs.

## Failure Modes
- Do not auto-publish trial output before human review approval.

## References
- [Evidence](references/evidence.md)
- [Examples](references/examples.md)
