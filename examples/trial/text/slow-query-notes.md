# PostgreSQL Slow Query Notes

## Incident Context
- Service: order-api
- Window: 2026-05-18T08:10Z to 2026-05-18T08:45Z
- Primary symptom: p95 latency moved from 120ms to 680ms

## Observations
1. `pg_stat_statements` shows `SELECT * FROM order_events WHERE order_id = $1 ORDER BY created_at DESC LIMIT 1` as the dominant query.
2. `EXPLAIN ANALYZE` reports row estimate mismatch (~30x) on the `order_events` table.
3. Buffer reads spike during replay windows after deploy.

## Current Guidance
1. Refresh table statistics before adding indexes.
2. Add one composite index only if estimate mismatch remains after stats refresh.
3. Verify p95 latency and buffer hit ratio before and after change.

## Failure Modes
- Do not ship query rewrite and index change in one release.
- Do not create overlapping indexes without write-amplification checks.
