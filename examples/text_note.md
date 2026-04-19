# PostgreSQL Slow Query Review

## Context

This note captures a repeatable way to review slow SQL queries before blindly adding indexes.

## Procedure

1. Capture the worst queries from `pg_stat_statements`.
2. Run `EXPLAIN ANALYZE` and compare the actual plan with the expected access path.
3. Measure whether the bottleneck is I/O, CPU, or lock contention.

## Rules

If the query is I/O bound, review index coverage before rewriting business logic.
If row estimates diverge sharply from actual rows, inspect stale statistics.

## Anti-patterns

Avoid adding overlapping indexes without calculating write amplification.
Do not change the query text and the index strategy at the same time.

## Verification

Verify the fix by comparing latency, buffer hits, and row estimates before and after the change.

