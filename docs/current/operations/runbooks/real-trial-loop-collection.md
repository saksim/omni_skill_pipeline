# Real Trial Loop Collection (GL-12 / GL-13 / GL-16)



## Verdict



This runbook defines how to collect and classify real controlled-trial loops for launch-gate evidence.

It does not authorize GA claims. Output statuses are evidence tracking states only.



## Scope



- Collector script: `scripts/run_real_trial_loop_collection.py`

- Bridge script: `scripts/run_real_trial_launch_evidence.py`

- Input sources:

  - one or more controlled-trial run reports (`controlled-trial-run-report.json`)

  - one or more explicit real-loop manifests (`--loop-manifest`)

- Output artifacts:

  - `real-trial-loop-collection-report.json`

  - `real-trial-loop-collection-summary.md`

  - `real-trial-loop-metrics-manifest.json`

  - `real-trial-loop-backfill-plan.json`

  - `real-trial-backfill-execution-report.json`

  - `real-trial-backfill-execution-summary.md`

  - `real-trial-launch-evidence-pack.json`

- Baseline template:

  - `docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-metrics-manifest.template.json`



## Preconditions



- Real loops must be explicitly labeled:

  - `evidence_origin=real`

  - `launch_gate_eligible=true`

  - `source_system`, `source_reference`, `collected_at_utc`

  - `review_task_id`, `reviewed_by`, `reviewed_at_utc`

- Fixture/synthetic loops may exist in the same report, but they must remain non-launch-gate-eligible.



## Collect From Controlled-Trial Run Report



```bash

python scripts/run_real_trial_loop_collection.py \

  --run-report docs/current/status/baselines/controlled-trial/controlled-trial-run-report.json \

  --output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-report.json \

  --summary-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-summary.md \

  --manifest-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-metrics-manifest.json

```



## Merge Multiple Run Reports



```bash

python scripts/run_real_trial_loop_collection.py \

  --run-report docs/current/status/baselines/controlled-trial/controlled-trial-run-report-a.json \

  --run-report docs/current/status/baselines/controlled-trial/controlled-trial-run-report-b.json \

  --output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-report.json \

  --summary-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-summary.md \

  --manifest-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-metrics-manifest.json

```



## Batch Ingest Real Loop Manifests (GL-17)



When real loops are collected outside the controlled-trial fixture runner, ingest them in batch from one or more manifest directories.



```bash

python scripts/run_real_trial_loop_collection.py \

  --loop-manifest-dir docs/current/status/baselines/real-trial-loop-collection/manifests \

  --loop-manifest-pattern "*.json" \

  --output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-report.json \

  --summary-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-summary.md \

  --manifest-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-metrics-manifest.json

```



Optional recursive scan:



```bash

python scripts/run_real_trial_loop_collection.py \

  --loop-manifest-dir docs/current/status/baselines/real-trial-loop-collection/manifests \

  --loop-manifest-pattern "**/*.json" \

  --loop-manifest-recursive

```



Default batch behavior is tolerant: JSON files that do not have top-level `loops` are skipped and reported in

`skipped_non_loop_manifest_paths`.

Use strict contract mode to fail fast instead:



```bash

python scripts/run_real_trial_loop_collection.py \

  --loop-manifest-dir docs/current/status/baselines/real-trial-loop-collection/manifests \

  --loop-manifest-pattern "*.json" \

  --strict-loop-manifest-contract

```



The collection report now includes:



- `input_loop_manifest_dir_count`

- `source_loop_manifest_dirs`

- `ingested_loop_manifest_count`

- `skipped_non_loop_manifest_count`

- `skipped_non_loop_manifest_paths`

- `duplicate_resolution_count`

- `duplicate_resolution_records`

- `launch_gate_alignment.missing_complete_loops_to_threshold`

- `launch_gate_alignment.missing_modalities_to_threshold`

- `launch_gate_alignment.target_launch_modalities`

- `launch_gate_alignment.covered_target_launch_modalities`

- `launch_gate_alignment.missing_target_launch_modalities`

- `launch_gate_alignment.recommended_next_modalities`

- `launch_gate_alignment.launch_gate_eligible_complete_loop_count_by_modality`

- `launch_gate_alignment.target_launch_modality_loop_counts`

- `launch_gate_alignment.recommended_backfill_slot_count`

- `launch_gate_alignment.recommended_backfill_slots`



GL-21 backfill plan output:



- `--backfill-plan-output` emits `real_trial_loop_backfill_plan.v1`.

- The plan does not claim readiness; it translates current threshold gaps into explicit loop intake slots:

  - missing target modalities first (`reason=missing_target_launch_modality`)

  - remaining volume gaps next (`reason=loop_volume_gap_after_modality_coverage`)



GL-22 backfill execution tracking:



- `scripts/run_real_trial_backfill_execution.py` compares GL-21 plan slots against current GL-12 collection coverage.

- It emits:

  - `real_trial_backfill_execution.v1` JSON report

  - markdown summary with slot fulfillment progress and current launch-gap snapshot

- This step does not alter launch policy. Final launch readiness is still decided by `run_launch_readiness_gate.py`.

- Example:



```bash

python scripts/run_real_trial_backfill_execution.py \

  --backfill-plan docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-backfill-plan.json \

  --collection-report docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-report.json \

  --output docs/current/status/baselines/real-trial-loop-collection/real-trial-backfill-execution-report.json \

  --summary-output docs/current/status/baselines/real-trial-loop-collection/real-trial-backfill-execution-summary.md

```



GL-23 intake actions bridge:



- `scripts/run_real_trial_backfill_intake_actions.py` converts GL-21 slots and GL-22 execution status into operator-facing intake actions.

- It emits:

  - `real_trial_backfill_intake_actions.v1` JSON report

  - markdown summary with pending action list and launch-gap snapshot

- Each action includes closure evidence requirements for next-loop submission:

  - required loop-manifest fields (`loop_id`, `modality`, `evidence_origin`, `launch_gate_eligible`, source/review trace fields)

  - required values (`evidence_origin=real`, `launch_gate_eligible=true`, `status=complete`, modality match)

- Example:



```bash

python scripts/run_real_trial_backfill_intake_actions.py \

  --backfill-plan docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-backfill-plan.json \

  --backfill-execution-report docs/current/status/baselines/real-trial-loop-collection/real-trial-backfill-execution-report.json \

  --output docs/current/status/baselines/real-trial-loop-collection/real-trial-backfill-intake-actions-report.json \

  --summary-output docs/current/status/baselines/real-trial-loop-collection/real-trial-backfill-intake-actions-summary.md \

  --owner controlled-beta-ops

```



GL-24 handoff bridge:

- `scripts/run_real_trial_backfill_handoff.py` converts GL-23 intake actions and GL-12 collected real-loop submissions into deterministic assignee queue items plus closure acknowledgement records.
- It emits:
  - `real_trial_backfill_handoff.v1` JSON report
  - markdown summary with open queue items and closure-acknowledged counts
- Queue item statuses:
  - `open`: no matching launch-gate-eligible real submission acknowledged yet
  - `submission_linked_pending_ack`: matched real submission linked, but operator acknowledgement is missing or submitted loop-id does not match linked loop-id
  - `closure_acknowledged`: matched real submission plus matching operator acknowledgement loop-id
- Optional operator acknowledgement contract (GL-25):
  - pass `--acknowledgements-report <json>` with `acknowledgements[]` rows including:
    - `queue_item_id` or `action_id`
    - `submitted_loop_id`
    - `acknowledged_by`
    - `acknowledged_at_utc` (UTC timestamp)
  - handoff report emits `acknowledgement_snapshot` diagnostics and `submission_linked_pending_ack_count`.
- GL-26 acknowledgement SLA/aging contract:
  - handoff stage accepts:
    - `--pending-ack-sla-hours` (default `24`)
    - `--pending-ack-overdue-hours` (default `72`)
    - `--now-utc` (optional deterministic evaluation clock)
  - for each `submission_linked_pending_ack` item, handoff report emits:
    - `pending_ack_sla_state` (`within_sla` / `sla_breached` / `overdue` / `missing_reference_timestamp`)
    - `pending_ack_age_hours`
    - `pending_ack_sla_deadline_utc`
    - `pending_ack_overdue_deadline_utc`
    - `escalation_action`
  - report-level SLA block:
    - `acknowledgement_sla_snapshot.acknowledgement_sla_status`
    - `pending_ack_within_sla_count`
    - `pending_ack_sla_breached_count`
    - `pending_ack_overdue_count`
    - `pending_ack_missing_reference_timestamp_count`
  - optional policy exit:
    - `--fail-on-ack-overdue` returns non-zero when overdue pending-ack items exist.
- GL-27 operator escalation exports:
  - `scripts/run_real_trial_backfill_handoff_escalations.py` converts GL-24/GL-26 handoff outputs into operator-facing escalation exports.
  - escalation export outputs:
    - `real_trial_backfill_handoff_escalations.v1` JSON report
    - markdown summary
  - escalation status values:
    - `ESCALATION_NOT_REQUIRED`
    - `ESCALATION_BREACH_ACTION_REQUIRED`
    - `ESCALATION_OVERDUE_ACTION_REQUIRED`
    - `ESCALATION_TRACKING_INCOMPLETE`
  - exported escalation cohorts:
    - `sla_breached_items`
    - `overdue_items`
    - `tracking_incomplete_items`
  - optional policy exits:
    - `--fail-on-breached`
    - `--fail-on-overdue`
- Example:

```bash
python scripts/run_real_trial_backfill_handoff.py \
  --intake-actions-report docs/current/status/baselines/real-trial-loop-collection/real-trial-backfill-intake-actions-report.json \
  --collection-report docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-report.json \
  --acknowledgements-report docs/current/status/baselines/real-trial-loop-collection/real-trial-backfill-handoff-acknowledgements.json \
  --pending-ack-sla-hours 24 \
  --pending-ack-overdue-hours 72 \
  --output docs/current/status/baselines/real-trial-loop-collection/real-trial-backfill-handoff-report.json \
  --summary-output docs/current/status/baselines/real-trial-loop-collection/real-trial-backfill-handoff-summary.md \
  --owner controlled-beta-ops
```

```bash
python scripts/run_real_trial_backfill_handoff_escalations.py \
  --handoff-report docs/current/status/baselines/real-trial-loop-collection/real-trial-backfill-handoff-report.json \
  --output docs/current/status/baselines/real-trial-loop-collection/real-trial-backfill-handoff-escalations-report.json \
  --summary-output docs/current/status/baselines/real-trial-loop-collection/real-trial-backfill-handoff-escalations-summary.md \
  --owner controlled-beta-ops
```


Duplicate loop ids (loop_id) are resolved deterministically:



- prefer row with newer `reviewed_at_utc`

- if equal/missing, prefer newer `collected_at_utc`

- if still tied, use stable source-path ordering



This keeps batch evidence accumulation idempotent while preserving an audit record in `duplicate_resolution_records`.



## Strict Blocker Mode



```bash

python scripts/run_real_trial_loop_collection.py \

  --run-report docs/current/status/baselines/controlled-trial/controlled-trial-run-report.json \

  --fail-on-blocker

```



## Output Status Contract



- `READY_FOR_CONTROLLED_BETA_EVIDENCE`

  - threshold met for launch-gate-eligible real complete loops and modalities

  - no missing source-trace on real loops

  - no missing review-trace on real loops

- `COLLECTION_INCOMPLETE`

  - any blocker remains



## Exit Codes



- `0`: collection completed

- `1`: `--fail-on-blocker` and blockers remain

- `2`: invalid input contract (missing files, malformed loop metrics, bad evidence labeling)



## Safety Rules



- Do not mark fixture/synthetic loops as launch-gate-eligible.

- Do not claim `READY_FOR_GA_REVIEW` from this collector alone.

- Always verify final launch status via:

  - `python scripts/run_launch_readiness_gate.py --output - --summary-output -`



## GL-13 One-Command Evidence Pipeline



For controlled external Beta operations, use the GL-13 bridge script to run:



1. real-loop collection

2. GL-22 backfill execution tracking

3. GL-23 intake actions generation

4. GL-24 handoff queue + closure acknowledgement generation
5. GL-25 acknowledgement linkage verification (optional acknowledgement input)
6. GL-26 acknowledgement SLA aging/escalation diagnostics
7. GL-27 handoff escalation export generation
8. trial metrics report generation
9. launch-readiness gate evaluation
10. GL-16 evidence pack publication


```bash

python scripts/run_real_trial_launch_evidence.py \

  --run-report docs/current/status/baselines/controlled-trial/controlled-trial-run-report.json \

  --collection-report-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-report.json \

  --collection-summary-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-summary.md \

  --real-trial-manifest-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-metrics-manifest.json \

  --trial-metrics-report-output docs/current/status/baselines/controlled-trial/trial-metrics-report.json \

  --trial-metrics-summary-output docs/current/status/baselines/controlled-trial/trial-metrics-summary.md \

  --launch-readiness-output docs/current/status/baselines/broad-launch-readiness-report.json \

  --launch-readiness-summary-output docs/current/status/baselines/broad-launch-readiness-summary.md \

  --backfill-handoff-escalations-output docs/current/status/baselines/real-trial-loop-collection/real-trial-backfill-handoff-escalations-report.json \

  --backfill-handoff-escalations-summary-output docs/current/status/baselines/real-trial-loop-collection/real-trial-backfill-handoff-escalations-summary.md \

  --evidence-pack-output docs/current/status/baselines/real-trial-loop-collection/real-trial-launch-evidence-pack.json \

  --max-evidence-age-hours 0

```



Batch manifest mode:



```bash

python scripts/run_real_trial_launch_evidence.py \

  --loop-manifest-dir docs/current/status/baselines/real-trial-loop-collection/manifests \

  --loop-manifest-pattern "*.json" \

  --collection-report-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-report.json \

  --collection-summary-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-summary.md \

  --real-trial-manifest-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-metrics-manifest.json \

  --trial-metrics-report-output docs/current/status/baselines/controlled-trial/trial-metrics-report.json \

  --trial-metrics-summary-output docs/current/status/baselines/controlled-trial/trial-metrics-summary.md \

  --launch-readiness-output docs/current/status/baselines/broad-launch-readiness-report.json \

    --backfill-handoff-escalations-output docs/current/status/baselines/real-trial-loop-collection/real-trial-backfill-handoff-escalations-report.json \\

  --backfill-handoff-escalations-summary-output docs/current/status/baselines/real-trial-loop-collection/real-trial-backfill-handoff-escalations-summary.md \\

 docs/current/status/baselines/real-trial-loop-collection/real-trial-launch-evidence-pack.json \

  --max-evidence-age-hours 0

```



Optional strict CI-style behavior:



```bash

python scripts/run_real_trial_launch_evidence.py \

  --run-report docs/current/status/baselines/controlled-trial/controlled-trial-run-report.json \

  --fail-on-blocker \

  --fail-on-hold

```



Optional explicit launch-modality target set for GL-20 gap diagnostics:



```bash

python scripts/run_real_trial_loop_collection.py \

  --loop-manifest-dir docs/current/status/baselines/real-trial-loop-collection/manifests \

  --loop-manifest-pattern "*.json" \

  --target-launch-modalities "text,audio,image,video"

```



## GL-16 Evidence Pack Contract



GL-16 publishes `real-trial-launch-evidence-pack.json` as machine-readable reviewer/operator handoff:



- decision and readiness level (controlled external Beta scope)

- source input accounting (`run-report` + `loop-manifest`)

- evidence classification:

  - total loop/modality coverage

  - launch-gate-eligible real loop/modality coverage

  - target modality coverage and modality-specific next-gap suggestions

  - missing real source/reviewer trace counts

- launch-gate blocker summary

- GL-27 escalation exports:
  - `evidence_paths.real_trial_backfill_handoff_escalations_report`
  - `evidence_paths.real_trial_backfill_handoff_escalations_summary`
  - `backfill_handoff_escalation_status`
  - `backfill_handoff_escalation_owner`
  - `backfill_handoff_escalation_total_item_count`
  - `backfill_handoff_escalation_sla_breached_item_count`
  - `backfill_handoff_escalation_overdue_item_count`
  - `backfill_handoff_escalation_tracking_incomplete_item_count`
  - `backfill_handoff_escalation_sla_breached_items`
  - `backfill_handoff_escalation_overdue_items`
  - `backfill_handoff_escalation_tracking_incomplete_items`



This evidence pack does not override launch readiness policy and does not permit GA claims.






