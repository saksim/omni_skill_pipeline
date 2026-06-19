# Controlled Trial Final Report Template (CBT-14)

> Purpose: summarize controlled-trial evidence into a launch-level decision without requiring reviewers to read raw artifacts.
> Scope: controlled business trial / controlled external Beta pre-trial only. This report does not declare formal GA release.

## 1. Report Metadata

- Report ID: `<report-id>`
- Prepared at (UTC): `<yyyy-mm-ddThh:mm:ssZ>`
- Prepared by: `<name-or-role>`
- Trial window: `<start-utc> -> <end-utc>`
- Release decision input: `<GO|HOLD>` from release-switch evidence

## 2. Evidence Inputs

- Controlled-trial run report: `<path-to-controlled-trial-run-report.json>`
- Trial metrics report: `<path-to-trial-metrics-report.json>`
- Trial metrics summary: `<path-to-trial-metrics-summary.md>`
- Agent smoke report: `<path-to-agent-smoke-report.json>`
- Trial security gate evidence: `<path(s)-or-embedded-summary>`

## 3. Executive Decision

- Recommended decision: `<CONTINUE_TRIAL|EXPAND_BETA|HOLD_FOR_REMEDIATION|GA_CANDIDATE>`
- GA discussion blocked: `<yes|no>`
- One-line rationale: `<short rationale>`
- Next launch level: `<controlled trial|controlled external beta expansion|ga-readiness review candidate>`

## 4. Trial Coverage and Throughput

- Complete loops: `<number>`
- Modalities covered (count): `<number>`
- Modalities covered (list): `<list>`
- Approved skills: `<number>`
- Rejected skills: `<number>`
- Review-required outputs published without review: `<number>`

## 5. Quality and Usability Metrics

- Reviewer approval rate (<=1 revision): `<0-1>`
- Median reviewer edit distance (%): `<number>`
- Agent smoke success rate for approved skills: `<0-1>`
- Reviewer notes coverage complete: `<yes|no>`

## 6. Reliability, Safety, and Cost

- Provider/runtime failure rate: `<0-1>`
- Retry count (total): `<number>`
- Median latency (ms): `<number>`
- Cost per accepted skill (USD): `<number>`
- Critical secret/PII leaks: `<number>`
- High-severity trial incidents: `<number>`

## 7. Success Criteria Checklist

| Condition ID | Status (`pass`/`fail`) | Actual | Expected |
| --- | --- | --- | --- |
| `release_run_go` | `<pass|fail>` | `<actual>` | `GO` |
| `loop_volume_and_modality_coverage` | `<pass|fail>` | `<loops/modalities>` | `>=10 loops and >=4 modalities` |
| `no_unreviewed_publication` | `<pass|fail>` | `<actual>` | `0` |
| `no_critical_secret_or_pii_leak` | `<pass|fail>` | `<actual>` | `0` |
| `no_high_severity_trial_incident` | `<pass|fail>` | `<actual>` | `0` |
| `reviewer_approval_rate` | `<pass|fail>` | `<actual>` | `>=0.8` |
| `median_reviewer_edit_distance` | `<pass|fail>` | `<actual>` | `<=25%` |
| `agent_smoke_success_rate` | `<pass|fail>` | `<actual>` | `>=0.8` |
| `provider_failure_rate` | `<pass|fail>` | `<actual>` | `<=pilot threshold` |
| `cost_per_accepted_skill` | `<pass|fail>` | `<actual>` | `recorded and accepted` |

## 8. Failure and Remediation Summary

- Failed condition IDs: `<list>`
- Root-cause summary: `<short paragraph>`
- Remediation owner: `<name-or-role>`
- Remediation deadline (UTC): `<yyyy-mm-dd>`
- Re-run gate: `<what must pass before next decision>`

## 9. Reviewer Notes

- Cross-modality consistency notes: `<notes>`
- Risk notes (OCR/transcript/keyframe/metrics/conflict): `<notes>`
- Known limitations: `<notes>`
- Open questions: `<notes>`

## 10. Decision Definitions

- `HOLD_FOR_REMEDIATION`
  - Use when any critical gate fails (`release_run_go`, `loop_volume_and_modality_coverage`, `no_unreviewed_publication`, `no_critical_secret_or_pii_leak`), or when trial risk is unresolved.
- `CONTINUE_TRIAL`
  - Use when critical safety/review gates pass but coverage/quality evidence is still insufficient for expansion.
- `EXPAND_BETA`
  - Use when critical gates pass and trial metrics are stable enough to broaden controlled external Beta scope (still review-first, still non-GA).
- `GA_CANDIDATE`
  - Use only when controlled-trial criteria are consistently satisfied and evidence supports entering a separate GA-readiness review; this is not an automatic GA declaration.
