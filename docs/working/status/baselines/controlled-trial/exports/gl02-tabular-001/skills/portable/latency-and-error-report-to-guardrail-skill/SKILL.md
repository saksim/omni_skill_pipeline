---
name: "latency and error report to guardrail skill"
description: "Use when Use when converting tabular evidence into build_skill.. Confirm row count and dtype assumptions before interpreting the table."
---

# latency and error report to guardrail skill

## Workflow
1. Confirm row count and dtype assumptions before interpreting the table. (Why: Derived from semantic atom.)
2. Normalize time zones, units, and duplicated keys before aggregation. (Why: Derived from semantic atom.)
3. timestamp :: str (Why: Derived from semantic atom.)
4. service :: str (Why: Derived from semantic atom.)
5. latency_ms :: int64 (Why: Derived from semantic atom.)
6. error_rate :: float64 (Why: Derived from semantic atom.)
7. cost_usd :: float64 (Why: Derived from semantic atom.)
8. Inspect the highest-missing columns before trusting downstream trends. (Why: Derived from semantic atom.)
9. timestamp missing_pct=0.0 (Why: Derived from semantic atom.)
10. service missing_pct=0.0 (Why: Derived from semantic atom.)
11. latency_ms missing_pct=0.0 (Why: Derived from semantic atom.)
12. error_rate missing_pct=0.0 (Why: Derived from semantic atom.)
13. cost_usd missing_pct=0.0 (Why: Derived from semantic atom.)
14. Compare per-entity counts before aggregating the whole table. (Why: Derived from semantic atom.)
15. 2026-05-18T08:00:00 -> 1 rows (Why: Derived from semantic atom.)
16. 2026-05-18T08:05:00 -> 1 rows (Why: Derived from semantic atom.)
17. 2026-05-18T08:10:00 -> 1 rows (Why: Derived from semantic atom.)
18. 2026-05-18T08:15:00 -> 1 rows (Why: Derived from semantic atom.)
19. 2026-05-18T08:20:00 -> 1 rows (Why: Derived from semantic atom.)
20. Review distribution shape before setting thresholds on latency_ms. (Why: Derived from semantic atom.)
21. Review distribution shape before setting thresholds on error_rate. (Why: Derived from semantic atom.)
22. Review distribution shape before setting thresholds on cost_usd. (Why: Derived from semantic atom.)
23. Sort by timestamp before comparing neighboring measurements. (Why: Derived from semantic atom.)
24. Investigate abrupt deltas before averaging the full observation window. (Why: Derived from semantic atom.)
25. Sort latency_ms by timestamp before comparing local deltas. (Why: Derived from semantic atom.)
26. Review the largest jump around 2026-05-18 08:40:00 before trusting a global trend. (Why: Derived from semantic atom.)
27. change_point=2026-05-18 08:20:00 delta=124.0000 (Why: Derived from semantic atom.)
28. change_point=2026-05-18 08:25:00 delta=134.0000 (Why: Derived from semantic atom.)
29. change_point=2026-05-18 08:30:00 delta=119.0000 (Why: Derived from semantic atom.)
30. change_point=2026-05-18 08:40:00 delta=-158.0000 (Why: Derived from semantic atom.)
31. change_point=2026-05-18 08:45:00 delta=-134.0000 (Why: Derived from semantic atom.)
32. anomaly_interval=2026-05-18 08:20:00 -> 2026-05-18 08:40:00 (Why: Derived from semantic atom.)
33. anomaly_at=2026-05-18 08:20:00 (Why: Derived from semantic atom.)
34. anomaly_at=2026-05-18 08:25:00 (Why: Derived from semantic atom.)
35. anomaly_at=2026-05-18 08:30:00 (Why: Derived from semantic atom.)
36. anomaly_at=2026-05-18 08:35:00 (Why: Derived from semantic atom.)
37. anomaly_at=2026-05-18 08:40:00 (Why: Derived from semantic atom.)
38. Sort error_rate by timestamp before comparing local deltas. (Why: Derived from semantic atom.)
39. Review the largest jump around 2026-05-18 08:25:00 before trusting a global trend. (Why: Derived from semantic atom.)
40. change_point=2026-05-18 08:20:00 delta=0.0050 (Why: Derived from semantic atom.)
41. change_point=2026-05-18 08:25:00 delta=0.0070 (Why: Derived from semantic atom.)
42. change_point=2026-05-18 08:30:00 delta=0.0050 (Why: Derived from semantic atom.)
43. change_point=2026-05-18 08:35:00 delta=-0.0060 (Why: Derived from semantic atom.)
44. change_point=2026-05-18 08:40:00 delta=-0.0070 (Why: Derived from semantic atom.)
45. change_point=2026-05-18 08:45:00 delta=-0.0050 (Why: Derived from semantic atom.)
46. anomaly_interval=2026-05-18 08:20:00 -> 2026-05-18 08:40:00 (Why: Derived from semantic atom.)
47. anomaly_at=2026-05-18 08:20:00 (Why: Derived from semantic atom.)
48. anomaly_at=2026-05-18 08:25:00 (Why: Derived from semantic atom.)
49. anomaly_at=2026-05-18 08:30:00 (Why: Derived from semantic atom.)
50. anomaly_at=2026-05-18 08:35:00 (Why: Derived from semantic atom.)
51. anomaly_at=2026-05-18 08:40:00 (Why: Derived from semantic atom.)
52. Sort cost_usd by timestamp before comparing local deltas. (Why: Derived from semantic atom.)
53. Review the largest jump around 2026-05-18 08:20:00 before trusting a global trend. (Why: Derived from semantic atom.)
54. change_point=2026-05-18 08:20:00 delta=1.8000 (Why: Derived from semantic atom.)
55. change_point=2026-05-18 08:45:00 delta=-1.6000 (Why: Derived from semantic atom.)
56. anomaly_interval=2026-05-18 08:20:00 -> 2026-05-18 08:40:00 (Why: Derived from semantic atom.)
57. anomaly_at=2026-05-18 08:20:00 (Why: Derived from semantic atom.)
58. anomaly_at=2026-05-18 08:25:00 (Why: Derived from semantic atom.)
59. anomaly_at=2026-05-18 08:30:00 (Why: Derived from semantic atom.)
60. anomaly_at=2026-05-18 08:35:00 (Why: Derived from semantic atom.)
61. anomaly_at=2026-05-18 08:40:00 (Why: Derived from semantic atom.)

## Decision Rules
- If a column mixes numeric and string forms, clean it before trend analysis. -> Apply the matching action.
- If missingness jumps after a date boundary, inspect upstream ingestion or schema drift. -> Apply the matching action.
- If one entity dominates the sample, review entity bias before reading the global average. -> Apply the matching action.
- If latency_ms shows a long tail, inspect outliers before computing a baseline. -> Apply the matching action.
- If error_rate shows a long tail, inspect outliers before computing a baseline. -> Apply the matching action.
- If cost_usd shows a long tail, inspect outliers before computing a baseline. -> Apply the matching action.
- If anomalies cluster near a timestamp boundary, inspect deploys, ingest gaps, or backfills first. -> Apply the matching action.
- If latency_ms deviates more than the rolling baseline, inspect deploys, schema changes, or data loss first. -> Apply the matching action.
- When rule conditions are met. -> When anomalies cluster, inspect the shared upstream dependency before per-row debugging.
- If error_rate deviates more than the rolling baseline, inspect deploys, schema changes, or data loss first. -> Apply the matching action.
- If cost_usd deviates more than the rolling baseline, inspect deploys, schema changes, or data loss first. -> Apply the matching action.

## Validation
- Verify the business grain of one row before building any skill from this table.
- Verify whether null means unavailable, zero, or not applicable in the source system.
- Verify extreme rows against source records and unit assumptions.
- Verify each anomaly against raw rows immediately before and after the flagged timestamp.
- Verify each flagged point against neighboring rows and source records.

## Failure Modes
- Do not auto-publish trial output before human review approval.

## References
- [Evidence](references/evidence.md)
- [Examples](references/examples.md)
