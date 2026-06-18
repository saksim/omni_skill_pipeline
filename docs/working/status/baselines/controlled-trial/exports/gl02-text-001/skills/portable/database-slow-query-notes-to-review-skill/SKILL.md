---
name: "database slow-query notes to review skill"
description: "Use when Use when converting text evidence into build_skill.. Service: order-api"
---

# database slow-query notes to review skill

## Workflow
1. Service: order-api (Why: Derived from semantic atom.)
2. Window: 2026-05-18T08:10Z to 2026-05-18T08:45Z (Why: Derived from semantic atom.)
3. Primary symptom: p95 latency moved from 120ms to 680ms (Why: Derived from semantic atom.)
4. `pg_stat_statements` shows `SELECT * FROM order_events WHERE order_id = $1 ORDER BY created_at DESC LIMIT 1` as the dominant query. (Why: Derived from semantic atom.)
5. `EXPLAIN ANALYZE` reports row estimate mismatch (~30x) on the `order_events` table. (Why: Derived from semantic atom.)
6. Buffer reads spike during replay windows after deploy. (Why: Derived from semantic atom.)
7. Refresh table statistics before adding indexes. (Why: Derived from semantic atom.)
8. Add one composite index only if estimate mismatch remains after stats refresh. (Why: Derived from semantic atom.)
9. Verify p95 latency and buffer hit ratio before and after change. (Why: Derived from semantic atom.)
10. Do not ship query rewrite and index change in one release. (Why: Derived from semantic atom.)
11. Do not create overlapping indexes without write-amplification checks. (Why: Derived from semantic atom.)

## Decision Rules
- No explicit branch rule was extracted; execute workflow order first.

## Validation
- Confirm each key conclusion can be traced back to evidence_refs.

## Failure Modes
- Do not auto-publish trial output before human review approval.

## References
- [Evidence](references/evidence.md)
- [Examples](references/examples.md)
