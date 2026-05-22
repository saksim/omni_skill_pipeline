# Incident Postmortem (Sanitized)

## Summary
An index regression and stale statistics amplified query latency during a controlled rollout.

## Timeline
- 08:10 UTC: latency alert fired.
- 08:16 UTC: oncall confirmed row estimate mismatch.
- 08:28 UTC: mitigated by rollback + stats refresh.

## Lessons
1. Validate estimator accuracy before index decisions.
2. Keep rollout guardrails tied to latency and error-rate together.
