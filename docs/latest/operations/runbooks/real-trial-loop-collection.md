# Real Trial Loop Collection (GL-12 / GL-13 / GL-16)



## Verdict



This runbook defines how to collect and classify real controlled-trial loops for launch-gate evidence.

It does not authorize GA claims. Output statuses are evidence tracking states only.



## Scope



- Collector script: `scripts/gl12_collect_loops.py`

- Bridge script: `scripts/gl13_launch_evidence.py`

- Input sources:

  - one or more controlled-trial run reports (`controlled-trial-run-report.json`)

  - one or more explicit real-loop manifests (`--loop-manifest`)

  - one or more real-loop manifest directories (`--loop-manifest-dir`)

- Output artifacts:

  - `real-trial-loop-collection-report.json`

  - `real-trial-loop-collection-summary.md`

  - `real-trial-loop-metrics-manifest.json`

  - `real-trial-loop-backfill-plan.json`

  - `real-trial-backfill-execution-report.json`

  - `real-trial-backfill-execution-summary.md`

  - `real-trial-launch-evidence-pack.json`

- Baseline template:

  - `docs/working/status/baselines/real-trial-loop-collection/real-trial-loop-metrics-manifest.template.json`



## Preconditions



- Real loops must be explicitly labeled:

  - `evidence_origin=real`

  - `launch_gate_eligible=true`

  - `source_system`, `source_reference`, `collected_at_utc`

  - `review_task_id`, `reviewed_by`, `reviewed_at_utc`

- Fixture/synthetic loops may exist in the same report, but they must remain non-launch-gate-eligible.



## Collect From Controlled-Trial Run Report



```bash

python scripts/gl12_collect_loops.py \

  --run-report docs/working/status/baselines/controlled-trial/controlled-trial-run-report.json \

  --output docs/working/status/baselines/real-trial-loop-collection/real-trial-loop-collection-report.json \

  --summary-output docs/working/status/baselines/real-trial-loop-collection/real-trial-loop-collection-summary.md \

  --manifest-output docs/working/status/baselines/real-trial-loop-collection/real-trial-loop-metrics-manifest.json

```



## Merge Multiple Run Reports



```bash

python scripts/gl12_collect_loops.py \

  --run-report docs/working/status/baselines/controlled-trial/controlled-trial-run-report-a.json \

  --run-report docs/working/status/baselines/controlled-trial/controlled-trial-run-report-b.json \

  --output docs/working/status/baselines/real-trial-loop-collection/real-trial-loop-collection-report.json \

  --summary-output docs/working/status/baselines/real-trial-loop-collection/real-trial-loop-collection-summary.md \

  --manifest-output docs/working/status/baselines/real-trial-loop-collection/real-trial-loop-metrics-manifest.json

```



## Batch Ingest Real Loop Manifests (GL-17)



When real loops are collected outside the controlled-trial fixture runner, ingest them in batch from one or more manifest directories.

Before running this mode, place at least one real-loop `.json` manifest in
`docs/working/status/baselines/real-trial-loop-collection/manifests/`. Release artifacts do not generate
operator-collected Beta evidence in this directory.



```bash

python scripts/gl12_collect_loops.py \

  --loop-manifest-dir docs/working/status/baselines/real-trial-loop-collection/manifests \

  --loop-manifest-pattern "*.json" \

  --output docs/working/status/baselines/real-trial-loop-collection/real-trial-loop-collection-report.json \

  --summary-output docs/working/status/baselines/real-trial-loop-collection/real-trial-loop-collection-summary.md \

  --manifest-output docs/working/status/baselines/real-trial-loop-collection/real-trial-loop-metrics-manifest.json

```



Optional recursive scan:



```bash

python scripts/gl12_collect_loops.py \

  --loop-manifest-dir docs/working/status/baselines/real-trial-loop-collection/manifests \

  --loop-manifest-pattern "**/*.json" \

  --loop-manifest-recursive

```



Default batch behavior is tolerant: JSON files that do not have top-level `loops` are skipped and reported in

`skipped_non_loop_manifest_paths`.

Use strict contract mode to fail fast instead:



```bash

python scripts/gl12_collect_loops.py \

  --loop-manifest-dir docs/working/status/baselines/real-trial-loop-collection/manifests \

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

- `launch_gate_alignment.real_evidence_backfill_slot_linked_count`

- `launch_gate_alignment.real_evidence_backfill_action_linked_count`

- `launch_gate_alignment.real_evidence_backfill_linkage_complete_count`

- `launch_gate_alignment.real_evidence_backfill_linkage_missing_count`

- `launch_gate_alignment.recommended_backfill_slot_count`

- `launch_gate_alignment.recommended_backfill_slots`



GL-21 backfill plan output:



- `--backfill-plan-output` emits `real_trial_loop_backfill_plan.v1`.

- The plan does not claim readiness; it translates current threshold gaps into explicit loop intake slots:

  - missing target modalities first (`reason=missing_target_launch_modality`)

  - remaining volume gaps next (`reason=loop_volume_gap_after_modality_coverage`)



GL-22 backfill execution tracking:



- `scripts/gl22_backfill_exec.py` compares GL-21 plan slots against current GL-12 collection coverage.

- It emits:

  - `real_trial_backfill_execution.v1` JSON report

  - markdown summary with slot fulfillment progress and current launch-gap snapshot
  - GL-30 submission-backed execution diagnostics:
    - `submission_backed_execution_status`
    - `submission_backed_slot_counts.submission_backed_fulfilled_slot_count`
    - `submission_backed_slot_counts.submission_backed_remaining_slot_count`
    - `submission_backed_slot_counts.fulfilled_without_submission_linkage_count`
    - `submission_backed_slot_counts.submission_linked_without_modality_delta_count`
  - explicit GL-28 submission linkage diagnostics:
    - `slot_execution_records[].expected_action_id`
    - `slot_execution_records[].submission_linked`
    - `slot_execution_records[].submission_linkage_resolution`
    - `submission_linkage_counts` (`slot_linked_count`, `action_linked_count`, `submission_linked_slot_count`, `unmatched_submission_linkage_count`)
    - `submission_linkage_records`
    - `unmatched_submission_linkages`

- This step does not alter launch policy. Final launch readiness is still decided by `launch_gate.py`.
- GL-30 interpretation rule:
  - `execution_status` reports plan-slot progress from modality coverage delta.
  - `submission_backed_execution_status` reports plan-slot progress from explicit real submission linkage.
  - launch readiness ownership is unchanged; these are execution-evidence diagnostics only.
- GL-28 submission linkage contract for real external Beta evidence:
  - real loop rows may optionally include:
    - `backfill_slot_index` (`int > 0`)
    - `backfill_action_id` (for example `gl23-slot-001-text`)
  - these fields are evidence-linkage metadata only; they do not bypass launch-gate checks.

- Example:



```bash

python scripts/gl22_backfill_exec.py \

  --backfill-plan docs/working/status/baselines/real-trial-loop-collection/real-trial-loop-backfill-plan.json \

  --collection-report docs/working/status/baselines/real-trial-loop-collection/real-trial-loop-collection-report.json \

  --output docs/working/status/baselines/real-trial-loop-collection/real-trial-backfill-execution-report.json \

  --summary-output docs/working/status/baselines/real-trial-loop-collection/real-trial-backfill-execution-summary.md

```



GL-23 intake actions bridge:



- `scripts/gl23_intake_actions.py` converts GL-21 slots and GL-22 execution status into operator-facing intake actions.

- It emits:

  - `real_trial_backfill_intake_actions.v1` JSON report

  - markdown summary with pending action list and launch-gap snapshot

- Each action includes closure evidence requirements for next-loop submission:

  - required loop-manifest fields (`loop_id`, `modality`, `evidence_origin`, `launch_gate_eligible`, source/review trace fields)

  - required values (`evidence_origin=real`, `launch_gate_eligible=true`, `status=complete`, modality match)

- Example:



```bash

python scripts/gl23_intake_actions.py \

  --backfill-plan docs/working/status/baselines/real-trial-loop-collection/real-trial-loop-backfill-plan.json \

  --backfill-execution-report docs/working/status/baselines/real-trial-loop-collection/real-trial-backfill-execution-report.json \

  --output docs/working/status/baselines/real-trial-loop-collection/real-trial-backfill-intake-actions-report.json \

  --summary-output docs/working/status/baselines/real-trial-loop-collection/real-trial-backfill-intake-actions-summary.md \

  --owner controlled-beta-ops

```



GL-24 handoff bridge:

- `scripts/gl24_handoff.py` converts GL-23 intake actions and GL-12 collected real-loop submissions into deterministic assignee queue items plus closure acknowledgement records.
- It emits:
  - `real_trial_backfill_handoff.v1` JSON report
  - markdown summary with open queue items and closure-acknowledged counts
- Queue item statuses:
  - `open`: no matching launch-gate-eligible real submission acknowledged yet
  - `submission_linked_pending_ack`: matched real submission linked, but operator acknowledgement is missing or submitted loop-id does not match linked loop-id
  - `closure_acknowledged`: matched real submission plus matching operator acknowledgement loop-id
- GL-29 linkage-aware submission assignment policy:
  - handoff first attempts explicit GL-28 linkage match by `action_id` and `backfill_slot_index`.
  - fallback order when exact linkage is unavailable:
    - `action_id_only`
    - `slot_index_only`
    - `modality_fallback`
    - `none` (no submission linked, queue item remains open)
  - handoff report exposes:
    - `queue_items[].submission_linkage_strategy`
    - `submission_linkage_snapshot.linkage_strategy_counts`
    - `submission_linkage_snapshot.unlinked_submission_count`
    - `submission_linkage_snapshot.unlinked_submissions`
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
  - `scripts/gl27_handoff_escalations.py` converts GL-24/GL-26 handoff outputs into operator-facing escalation exports.
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
python scripts/gl24_handoff.py \
  --intake-actions-report docs/working/status/baselines/real-trial-loop-collection/real-trial-backfill-intake-actions-report.json \
  --collection-report docs/working/status/baselines/real-trial-loop-collection/real-trial-loop-collection-report.json \
  --acknowledgements-report docs/working/status/baselines/real-trial-loop-collection/real-trial-backfill-handoff-acknowledgements.json \
  --pending-ack-sla-hours 24 \
  --pending-ack-overdue-hours 72 \
  --output docs/working/status/baselines/real-trial-loop-collection/real-trial-backfill-handoff-report.json \
  --summary-output docs/working/status/baselines/real-trial-loop-collection/real-trial-backfill-handoff-summary.md \
  --owner controlled-beta-ops
```

```bash
python scripts/gl27_handoff_escalations.py \
  --handoff-report docs/working/status/baselines/real-trial-loop-collection/real-trial-backfill-handoff-report.json \
  --output docs/working/status/baselines/real-trial-loop-collection/real-trial-backfill-handoff-escalations-report.json \
  --summary-output docs/working/status/baselines/real-trial-loop-collection/real-trial-backfill-handoff-escalations-summary.md \
  --owner controlled-beta-ops
```


Duplicate loop ids (loop_id) are resolved deterministically:



- prefer row with newer `reviewed_at_utc`

- if equal/missing, prefer newer `collected_at_utc`

- if still tied, use stable source-path ordering



This keeps batch evidence accumulation idempotent while preserving an audit record in `duplicate_resolution_records`.



## Strict Blocker Mode



```bash

python scripts/gl12_collect_loops.py \

  --run-report docs/working/status/baselines/controlled-trial/controlled-trial-run-report.json \

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

  - `python scripts/launch_gate.py --output - --summary-output -`



## GL-13 One-Command Evidence Pipeline



For controlled external Beta operations, use the GL-13 bridge script to run:



1. real-loop collection

2. GL-22 backfill execution tracking

3. GL-23 intake actions generation

4. GL-31 submission manifest template generation
5. GL-33 submission consumption (`real inputs -> consumed manifest`)
6. GL-34 consumed-manifest ingestion replay (conditional):
   - when GL-33 reports `consumed_loop_count > 0`, bridge re-runs GL-12 + trial metrics + GL-22 + GL-23 + GL-31 with `--loop-manifest <consumed-manifest-path>`.
7. GL-35 submission throughput diagnostics (`snapshot delta` for sustained real-loop accumulation)
8. GL-37 operator submission queue + evidence-refresh cadence diagnostics
9. GL-24 handoff queue + closure acknowledgement generation
10. GL-38 queue completion evidence + cadence-cycle net-new movement verification
11. GL-25 acknowledgement linkage verification (optional acknowledgement input)
12. GL-26 acknowledgement SLA aging/escalation diagnostics
13. GL-27 handoff escalation export generation
14. GL-39 submission queue commitment diagnostics
15. GL-40 submission queue commitment-closure diagnostics
16. GL-41 submission queue follow-up diagnostics
17. GL-42 submission queue follow-up resolution diagnostics
18. GL-43 submission queue follow-up resolution escalation exports
19. GL-44 submission queue follow-up resolution escalation acknowledgement diagnostics
20. GL-45 submission queue follow-up resolution escalation throughput diagnostics
21. GL-46 submission queue follow-up resolution escalation action-plan diagnostics
22. GL-47 submission queue follow-up resolution escalation action-plan closure diagnostics
23. GL-48 submission queue follow-up resolution escalation action-plan closure cadence diagnostics
24. GL-49 submission queue follow-up resolution escalation action-plan closure cadence escalation diagnostics
25. GL-50 submission queue follow-up resolution escalation action-plan closure cadence escalation acknowledgement-ingestion diagnostics
26. GL-51 submission queue follow-up resolution escalation action-plan closure cadence escalation acknowledgement-closure diagnostics
27. GL-52 submission queue follow-up resolution escalation action-plan closure cadence escalation acknowledgement-closure cadence diagnostics
28. GL-53 submission queue follow-up resolution escalation action-plan closure cadence escalation acknowledgement-closure cadence escalation diagnostics
29. GL-54 submission queue follow-up resolution escalation action-plan closure cadence escalation acknowledgement-closure cadence escalation closure diagnostics
30. GL-55 submission queue follow-up resolution escalation action-plan closure cadence escalation acknowledgement-closure cadence escalation closure cadence diagnostics
31. launch-readiness gate evaluation
32. GL-16 evidence pack publication

GL-34 replay diagnostics are exposed in GL-16 pack:

- `input_sources.backfill_submission_ingestion_replay_applied`
- `input_sources.backfill_submission_ingestion_replay_manifest_paths`
- `input_sources.backfill_submission_ingestion_consumed_loop_count`
- `input_sources.backfill_submission_ingestion_status`
- `evidence_classification.backfill_submission_ingestion_replay_applied`
- `evidence_classification.backfill_submission_ingestion_consumed_loop_count`
- `evidence_classification.backfill_submission_ingestion_status`

GL-35 throughput diagnostics are exposed in GL-16 pack:

- `evidence_paths.real_trial_backfill_submission_throughput_report`
- `evidence_paths.real_trial_backfill_submission_throughput_summary`
- `evidence_classification.backfill_submission_throughput_status`
- `evidence_classification.backfill_submission_throughput_threshold_met`
- `evidence_classification.backfill_submission_throughput_warning_codes`
- `evidence_classification.backfill_submission_throughput_previous_snapshot_available`
- `evidence_classification.backfill_submission_throughput_net_new_loop_count`
- `evidence_classification.backfill_submission_throughput_dropped_loop_count`
- `evidence_classification.backfill_submission_throughput_net_new_loop_ids`
- `evidence_classification.backfill_submission_throughput_dropped_loop_ids`
- `evidence_classification.backfill_submission_throughput_current_missing_loops_to_threshold`
- `evidence_classification.backfill_submission_throughput_current_missing_modalities_to_threshold`
- `evidence_classification.backfill_submission_throughput_current_remaining_slot_count`
- `evidence_classification.backfill_submission_throughput_current_submission_backed_remaining_slot_count`
- `evidence_classification.backfill_submission_throughput_action_plan_status`
- `evidence_classification.backfill_submission_throughput_action_plan_blockers`
- `evidence_classification.backfill_submission_throughput_pending_submission_action_count`
- `evidence_classification.backfill_submission_throughput_recommended_submission_action_count`
- `evidence_classification.backfill_submission_throughput_priority_modalities`
- `evidence_classification.backfill_submission_throughput_recommended_submission_actions`
- `evidence_classification.backfill_submission_throughput_submission_consumption_status`
- `evidence_classification.backfill_submission_throughput_submission_template_loop_count`
- `evidence_classification.backfill_submission_throughput_submission_pending_template_loop_count`
- `evidence_classification.backfill_submission_throughput_submission_invalid_count`
- `evidence_classification.backfill_submission_throughput_submission_unresolved_count`

GL-36 execution-focus interpretation:

- `ACTION_PLAN_WAITING_FOR_SUBMISSIONS`: throughput is below threshold and pipeline has concrete pending submission actions by modality/slot.
- `ACTION_PLAN_BLOCKED_BY_SUBMISSION_ERRORS`: submission rows exist but invalid/unresolved rows must be fixed before throughput can progress.
- `ACTION_PLAN_NOT_REQUIRED`: thresholds are met or no additional submission action is needed for the current snapshot.

GL-37 submission queue diagnostics are exposed in GL-16 pack:

- `evidence_paths.real_trial_backfill_submission_queue_report`
- `evidence_paths.real_trial_backfill_submission_queue_summary`
- `evidence_classification.backfill_submission_queue_status`
- `evidence_classification.backfill_submission_queue_warning_codes`
- `evidence_classification.backfill_submission_queue_total_item_count`
- `evidence_classification.backfill_submission_queue_pending_item_count`
- `evidence_classification.backfill_submission_queue_blocked_item_count`
- `evidence_classification.backfill_submission_queue_pending_item_count_by_modality`
- `evidence_classification.backfill_submission_queue_blocked_item_count_by_modality`
- `evidence_classification.backfill_submission_queue_item_action_plan_status`
- `evidence_classification.backfill_submission_queue_item_action_plan_blockers`
- `evidence_classification.backfill_submission_queue_item_priority_modalities`
- `evidence_classification.backfill_submission_queue_item_pending_submission_action_count`
- `evidence_classification.backfill_submission_queue_item_recommended_submission_action_count`
- `evidence_classification.backfill_submission_queue_items`
- `evidence_classification.backfill_submission_queue_refresh_interval_hours`
- `evidence_classification.backfill_submission_queue_refresh_cadence_status`
- `evidence_classification.backfill_submission_queue_refresh_previous_generated_at_utc`
- `evidence_classification.backfill_submission_queue_refresh_next_due_utc`
- `evidence_classification.backfill_submission_queue_refresh_due_in_hours`
- `evidence_classification.backfill_submission_queue_refresh_evaluated_at_utc`

GL-38 queue completion diagnostics are exposed in GL-16 pack:

- `evidence_paths.real_trial_backfill_submission_queue_completion_report`
- `evidence_paths.real_trial_backfill_submission_queue_completion_summary`
- `evidence_classification.backfill_submission_queue_completion_status`
- `evidence_classification.backfill_submission_queue_completion_progress_status`
- `evidence_classification.backfill_submission_queue_cycle_verification_status`
- `evidence_classification.backfill_submission_queue_completion_warning_codes`
- `evidence_classification.backfill_submission_queue_completion_submitted_item_count`
- `evidence_classification.backfill_submission_queue_completion_closed_item_count`
- `evidence_classification.backfill_submission_queue_completion_open_item_count`
- `evidence_classification.backfill_submission_queue_completion_missing_handoff_item_count`
- `evidence_classification.backfill_submission_queue_completion_unknown_transition_item_count`
- `evidence_classification.backfill_submission_queue_cycle_net_new_movement_verified`
- `evidence_classification.backfill_submission_queue_cycle_throughput_net_new_loop_count`
- `evidence_classification.backfill_submission_queue_cycle_throughput_net_new_loop_ids`
- `evidence_classification.backfill_submission_queue_cycle_submitted_item_delta_from_previous_cycle`
- `evidence_classification.backfill_submission_queue_cycle_closed_item_delta_from_previous_cycle`
- `evidence_classification.backfill_submission_queue_cycle_open_item_delta_from_previous_cycle`
- `evidence_classification.backfill_submission_queue_completion_transition_records`

GL-39 submission queue commitment diagnostics are exposed in GL-16 pack:

- `evidence_paths.real_trial_backfill_submission_queue_commitments_report`
- `evidence_paths.real_trial_backfill_submission_queue_commitments_summary`
- `evidence_classification.backfill_submission_queue_commitment_status`
- `evidence_classification.backfill_submission_queue_cadence_run_obligation_status`
- `evidence_classification.backfill_submission_queue_commitment_total_count`
- `evidence_classification.backfill_submission_queue_commitment_pending_submission_count`
- `evidence_classification.backfill_submission_queue_commitment_pending_acknowledgement_count`
- `evidence_classification.backfill_submission_queue_commitment_blocked_submission_errors_count`
- `evidence_classification.backfill_submission_queue_commitment_escalation_required_count`
- `evidence_classification.backfill_submission_queue_commitment_rebuild_required_count`
- `evidence_classification.backfill_submission_queue_owner_commitment_counts`
- `evidence_classification.backfill_submission_queue_unresolved_execution_blockers`
- `evidence_classification.backfill_submission_queue_commitment_rows`
- `evidence_classification.backfill_submission_queue_commitment_cycle_snapshot`

GL-40 submission queue commitment-closure diagnostics are exposed in GL-16 pack:

- `evidence_paths.real_trial_backfill_submission_queue_commitment_closure_report`
- `evidence_paths.real_trial_backfill_submission_queue_commitment_closure_summary`
- `evidence_classification.backfill_submission_queue_commitment_closure_status`
- `evidence_classification.backfill_submission_queue_commitment_cadence_run_closure_status`
- `evidence_classification.backfill_submission_queue_commitment_closure_warning_codes`
- `evidence_classification.backfill_submission_queue_commitment_closure_total_count`
- `evidence_classification.backfill_submission_queue_commitment_closure_closed_with_acknowledgement_count`
- `evidence_classification.backfill_submission_queue_commitment_closure_active_count`
- `evidence_classification.backfill_submission_queue_commitment_stale_rollover_count`
- `evidence_classification.backfill_submission_queue_commitment_net_new_closed_with_acknowledgement_count`
- `evidence_classification.backfill_submission_queue_commitment_closure_rows`
- `evidence_classification.backfill_submission_queue_commitment_closure_acknowledgement_rows`
- `evidence_classification.backfill_submission_queue_commitment_stale_rollover_rows`

GL-41 submission queue follow-up diagnostics are exposed in GL-16 pack:

- `evidence_paths.real_trial_backfill_submission_queue_followup_report`
- `evidence_paths.real_trial_backfill_submission_queue_followup_summary`
- `evidence_classification.backfill_submission_queue_followup_status`
- `evidence_classification.backfill_submission_queue_followup_warning_codes`
- `evidence_classification.backfill_submission_queue_followup_commitment_closure_status_gl40`
- `evidence_classification.backfill_submission_queue_followup_cadence_run_closure_status_gl40`
- `evidence_classification.backfill_submission_queue_followup_closure_warning_codes_gl40`
- `evidence_classification.backfill_submission_queue_followup_total_action_count`
- `evidence_classification.backfill_submission_queue_followup_open_action_count`
- `evidence_classification.backfill_submission_queue_followup_closed_action_count`
- `evidence_classification.backfill_submission_queue_followup_stale_rollover_action_count`
- `evidence_classification.backfill_submission_queue_followup_acknowledgement_completion_action_count`
- `evidence_classification.backfill_submission_queue_followup_acknowledgement_closed_action_count`
- `evidence_classification.backfill_submission_queue_followup_blocked_action_count`
- `evidence_classification.backfill_submission_queue_followup_owner_counts`
- `evidence_classification.backfill_submission_queue_followup_action_rows`

GL-42 submission queue follow-up resolution diagnostics are exposed in GL-16 pack:

- `evidence_paths.real_trial_backfill_submission_queue_followup_resolution_report`
- `evidence_paths.real_trial_backfill_submission_queue_followup_resolution_summary`
- `evidence_classification.backfill_submission_queue_followup_resolution_status`
- `evidence_classification.backfill_submission_queue_followup_resolution_warning_codes`
- `evidence_classification.backfill_submission_queue_followup_resolution_total_action_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_open_action_count_gl41`
- `evidence_classification.backfill_submission_queue_followup_resolution_closed_action_count_gl41`
- `evidence_classification.backfill_submission_queue_followup_resolution_resolved_action_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_in_progress_action_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_unresolved_action_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_submission_linked_action_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_closure_acknowledged_action_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_consumed_submission_action_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_submission_invalid_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_submission_unresolved_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_owner_counts`
- `evidence_classification.backfill_submission_queue_followup_resolution_rows`

GL-43 submission queue follow-up resolution escalation diagnostics are exposed in GL-16 pack:

- `evidence_paths.real_trial_backfill_submission_queue_followup_resolution_escalations_report`
- `evidence_paths.real_trial_backfill_submission_queue_followup_resolution_escalations_summary`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_status`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_warning_codes`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_total_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_open_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_blocked_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_pending_ack_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_active_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_owner_counts`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_rows`

GL-44 submission queue follow-up resolution escalation acknowledgement diagnostics are exposed in GL-16 pack:

- `evidence_paths.real_trial_backfill_submission_queue_followup_resolution_escalation_acknowledgements_report`
- `evidence_paths.real_trial_backfill_submission_queue_followup_resolution_escalation_acknowledgements_summary`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_acknowledgement_status`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_acknowledgement_warning_codes`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_acknowledgement_total_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_acknowledgement_open_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_acknowledgement_resolved_acknowledged_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_acknowledgement_pending_ack_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_acknowledgement_blocked_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_acknowledgement_owner_counts`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_acknowledgement_rows`

GL-45 submission queue follow-up resolution escalation throughput diagnostics are exposed in GL-16 pack:

- `evidence_paths.real_trial_backfill_submission_queue_followup_resolution_escalation_throughput_report`
- `evidence_paths.real_trial_backfill_submission_queue_followup_resolution_escalation_throughput_summary`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_throughput_status`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_throughput_warning_codes`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_throughput_net_new_resolved_acknowledged_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_throughput_net_new_resolved_submission_loop_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_throughput_net_new_launch_gate_eligible_loop_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_throughput_unresolved_ack_closed_loop_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_throughput_unresolved_acknowledged_submission_loop_ids`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_throughput_net_new_resolved_submission_loop_ids`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_throughput_net_new_launch_gate_eligible_loop_ids`

GL-46 submission queue follow-up resolution escalation action-plan diagnostics are exposed in GL-16 pack:

- `evidence_paths.real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_report`
- `evidence_paths.real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_summary`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_status`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_warning_codes`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_total_action_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_open_action_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closed_action_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_unresolved_ack_mapping_action_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_recommended_backfill_slot_action_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_rows`

GL-47 submission queue follow-up resolution escalation action-plan closure diagnostics are exposed in GL-16 pack:

- `evidence_paths.real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_report`
- `evidence_paths.real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_summary`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_status`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_warning_codes`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_total_action_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_open_action_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_closed_action_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_carried_open_action_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_net_new_closed_action_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_stale_open_action_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_net_new_launch_gate_eligible_loop_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_open_action_count_delta`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_carried_open_action_ids`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_net_new_closed_action_ids`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_net_new_launch_gate_eligible_loop_ids`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_rows`

GL-48 submission queue follow-up resolution escalation action-plan closure cadence diagnostics are exposed in GL-16 pack:

- `evidence_paths.real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_report`
- `evidence_paths.real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_summary`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_status`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_warning_codes`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_total_action_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_open_action_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_stale_open_action_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_stall_cycle_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_overdue_stalled_cycles_threshold`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_refresh_interval_hours`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_state`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_previous_generated_at_utc`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_next_refresh_due_utc`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_due_in_hours`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_evaluated_at_utc`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_rows`

GL-49 submission queue follow-up resolution escalation action-plan closure cadence escalation diagnostics are exposed in GL-16 pack:

- `evidence_paths.real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_report`
- `evidence_paths.real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_summary`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_status`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_warning_codes`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_total_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_open_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_blocked_overdue_stalled_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_due_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_monitor_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_cadence_stall_cycle_count_gl48`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_cadence_overdue_stalled_cycles_threshold_gl48`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_escalate_after_due_hours`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_owner_counts`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_rows`

GL-50 submission queue follow-up resolution escalation action-plan closure cadence escalation acknowledgement-ingestion diagnostics are exposed in GL-16 pack:

- `evidence_paths.real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_report`
- `evidence_paths.real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_summary`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_status`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_warning_codes`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_total_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_open_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_closed_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_with_ack_record_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_with_matching_ack_loop_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_with_mismatched_ack_loop_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_missing_ack_record_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_without_handoff_queue_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_unreferenced_acknowledgement_record_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_owner_counts`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_rows`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_input_present`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_input_path`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_input_acknowledgement_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_valid_acknowledgement_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_invalid_acknowledgement_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_invalid_acknowledgement_records`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_unreferenced_acknowledgement_records`

GL-51 submission queue follow-up resolution escalation action-plan closure cadence escalation acknowledgement-closure diagnostics are exposed in GL-16 pack:

- `evidence_paths.real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_report`
- `evidence_paths.real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_summary`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_status`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_warning_codes`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_total_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_open_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_closed_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_previous_open_item_count_gl50`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_carried_open_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_stale_open_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_net_new_closed_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_ack_loop_mismatch_open_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_ack_missing_open_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_missing_handoff_open_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_net_new_launch_gate_eligible_loop_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_open_item_count_delta`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_carried_open_item_ids`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_net_new_closed_item_ids`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_net_new_launch_gate_eligible_loop_ids`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_rows`

GL-52 submission queue follow-up resolution escalation action-plan closure cadence escalation acknowledgement-closure cadence diagnostics are exposed in GL-16 pack:

- `evidence_paths.real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_report`
- `evidence_paths.real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_summary`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_status`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_warning_codes`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_total_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_open_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_stale_open_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_net_new_closed_item_count_gl51`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_net_new_launch_gate_eligible_loop_count_gl51`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_stall_cycle_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_overdue_stalled_cycles_threshold`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_refresh_interval_hours`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_state`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_previous_generated_at_utc`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_next_refresh_due_utc`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_due_in_hours`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_evaluated_at_utc`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_rows`

GL-53 submission queue follow-up resolution escalation action-plan closure cadence escalation acknowledgement-closure cadence escalation diagnostics are exposed in GL-16 pack:

- `evidence_paths.real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_report`
- `evidence_paths.real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_summary`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_status`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_warning_codes`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_total_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_open_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_blocked_overdue_stalled_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_due_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_monitor_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_cadence_stall_cycle_count_gl52`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_cadence_overdue_stalled_cycles_threshold_gl52`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_escalate_after_due_hours`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_owner_counts`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_rows`

GL-54 submission queue follow-up resolution escalation action-plan closure cadence escalation acknowledgement-closure cadence escalation closure diagnostics are exposed in GL-16 pack:

- `evidence_paths.real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_report`
- `evidence_paths.real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_summary`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_status`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_warning_codes`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_total_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_open_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_previous_open_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_carried_open_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_stale_open_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_net_new_open_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_net_new_closed_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_net_new_closed_backed_by_ack_ingestion_item_count_gl50`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_net_new_closed_without_ack_ingestion_item_count_gl50`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_ack_ingestion_closed_item_count_gl50`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_ack_ingestion_open_item_count_gl50`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_owner_counts`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_carried_open_item_ids`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_net_new_open_item_ids`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_net_new_closed_item_ids`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_net_new_closed_backed_by_ack_ingestion_item_ids_gl50`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_net_new_closed_without_ack_ingestion_item_ids_gl50`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_rows`

GL-55 submission queue follow-up resolution escalation action-plan closure cadence escalation acknowledgement-closure cadence escalation closure cadence diagnostics are exposed in GL-16 pack:

- `evidence_paths.real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_report`
- `evidence_paths.real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_summary`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_status`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_warning_codes`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_total_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_open_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_stale_open_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_net_new_closed_item_count_gl54`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_net_new_closed_backed_by_ack_ingestion_item_count_gl50`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_stall_cycle_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_overdue_stalled_cycles_threshold`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_refresh_interval_hours`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_state`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_previous_generated_at_utc`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_next_refresh_due_utc`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_due_in_hours`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_evaluated_at_utc`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_rows`

GL-56 submission queue follow-up resolution escalation action-plan closure cadence escalation acknowledgement-closure cadence escalation closure cadence escalations diagnostics are exposed in GL-16 pack:

- `evidence_paths.real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_report`
- `evidence_paths.real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_summary`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_status`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_warning_codes`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_total_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_open_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_blocked_overdue_stalled_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_due_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_monitor_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_cadence_stall_cycle_count_gl55`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_cadence_overdue_stalled_cycles_threshold_gl55`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_escalate_after_due_hours`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_owner_counts`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_rows`

GL-57 submission queue follow-up resolution escalation action-plan closure cadence escalation acknowledgement-closure cadence escalation closure cadence escalation closure diagnostics are exposed in GL-16 pack:

- `evidence_paths.real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_report`
- `evidence_paths.real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_summary`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_status`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_warning_codes`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_total_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_open_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_previous_open_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_carried_open_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_stale_open_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_open_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_backed_by_gl54_net_new_closed_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_without_gl54_net_new_closed_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_gl54_net_new_closed_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_gl54_net_new_closed_action_item_count`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_owner_counts`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_carried_open_item_ids`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_open_item_ids`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_item_ids`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_backed_by_gl54_net_new_closed_item_ids`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_without_gl54_net_new_closed_item_ids`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_gl54_net_new_closed_item_ids`
- `evidence_classification.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_rows`


```bash

python scripts/gl13_launch_evidence.py \

  --run-report docs/working/status/baselines/controlled-trial/controlled-trial-run-report.json \

  --collection-report-output docs/working/status/baselines/real-trial-loop-collection/real-trial-loop-collection-report.json \

  --collection-summary-output docs/working/status/baselines/real-trial-loop-collection/real-trial-loop-collection-summary.md \

  --real-trial-manifest-output docs/working/status/baselines/real-trial-loop-collection/real-trial-loop-metrics-manifest.json \

  --trial-metrics-report-output docs/working/status/baselines/controlled-trial/trial-metrics-report.json \

  --trial-metrics-summary-output docs/working/status/baselines/controlled-trial/trial-metrics-summary.md \

  --launch-readiness-output docs/working/status/baselines/broad-launch-readiness-report.json \

  --launch-readiness-summary-output docs/working/status/baselines/broad-launch-readiness-summary.md \

  --backfill-handoff-escalations-output docs/working/status/baselines/real-trial-loop-collection/real-trial-backfill-handoff-escalations-report.json \

  --backfill-handoff-escalations-summary-output docs/working/status/baselines/real-trial-loop-collection/real-trial-backfill-handoff-escalations-summary.md \

  --evidence-pack-output docs/working/status/baselines/real-trial-loop-collection/real-trial-launch-evidence-pack.json \

  --max-evidence-age-hours 0

```



Batch manifest mode:

Before running this mode, place at least one real-loop `.json` manifest in
`docs/working/status/baselines/real-trial-loop-collection/manifests/`. An empty directory fails fast and will not fall
back to the fixture controlled-trial report.



```bash

python scripts/gl13_launch_evidence.py \

  --loop-manifest-dir docs/working/status/baselines/real-trial-loop-collection/manifests \

  --loop-manifest-pattern "*.json" \

  --collection-report-output docs/working/status/baselines/real-trial-loop-collection/real-trial-loop-collection-report.json \

  --collection-summary-output docs/working/status/baselines/real-trial-loop-collection/real-trial-loop-collection-summary.md \

  --real-trial-manifest-output docs/working/status/baselines/real-trial-loop-collection/real-trial-loop-metrics-manifest.json \

  --trial-metrics-report-output docs/working/status/baselines/controlled-trial/trial-metrics-report.json \

  --trial-metrics-summary-output docs/working/status/baselines/controlled-trial/trial-metrics-summary.md \

  --launch-readiness-output docs/working/status/baselines/broad-launch-readiness-report.json \

  --launch-readiness-summary-output docs/working/status/baselines/broad-launch-readiness-summary.md \

  --backfill-handoff-escalations-output docs/working/status/baselines/real-trial-loop-collection/real-trial-backfill-handoff-escalations-report.json \

  --backfill-handoff-escalations-summary-output docs/working/status/baselines/real-trial-loop-collection/real-trial-backfill-handoff-escalations-summary.md \

  --evidence-pack-output docs/working/status/baselines/real-trial-loop-collection/real-trial-launch-evidence-pack.json \

  --max-evidence-age-hours 0

```



Optional strict CI-style behavior:



```bash

python scripts/gl13_launch_evidence.py \

  --run-report docs/working/status/baselines/controlled-trial/controlled-trial-run-report.json \

  --fail-on-blocker \

  --fail-on-hold

```



Optional explicit launch-modality target set for GL-20 gap diagnostics:



```bash

python scripts/gl12_collect_loops.py \

  --loop-manifest-dir docs/working/status/baselines/real-trial-loop-collection/manifests \

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
  - real evidence template placeholder diagnostics (`real_evidence_template_placeholder_*`)

- launch-gate blocker summary

- GL-31 submission template exports:
  - `evidence_paths.real_trial_backfill_submission_templates_report`
  - `evidence_paths.real_trial_backfill_submission_templates_summary`
  - `evidence_paths.real_trial_backfill_submission_manifest_template`
  - `backfill_submission_template_status`
  - `backfill_submission_template_total_action_count`
  - `backfill_submission_template_pending_action_count`
  - `backfill_submission_template_generated_count`
  - `backfill_submission_template_missing_count`
  - `backfill_submission_template_owner`
  - `backfill_submission_template_missing_actions`

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

## GL-31 Submission Templates

- `scripts/gl31_submission_templates.py` converts GL-23 pending actions to operator-ready real-loop manifest templates.
- Outputs:
  - `real_trial_backfill_submission_templates.v1` JSON report
  - markdown summary
  - `real_trial_backfill_submission_manifest.template.json` containing template loop rows with:
    - required launch-gate-eligible real evidence fields
    - GL-28 linkage fields (`backfill_slot_index`, `backfill_action_id`)
    - `TEMPLATE_REQUIRED_*` placeholders that must be replaced before GL-12/GL-13 ingestion
- This stage does not claim readiness; it only operationalizes pending slot submission preparation.
- GL-32 strictness:
  - Any real loop that still contains `TEMPLATE_REQUIRED_*` in required trace fields is treated as evidence-contract incomplete.
  - Such loops are excluded from launch-gate-eligible real coverage and reported via:
    - `launch_gate_alignment.real_evidence_template_placeholder_loop_count`
    - `launch_gate_alignment.real_evidence_template_placeholder_field_count`
    - `launch_gate_alignment.real_evidence_template_placeholder_records`
  - Launch gate remains `HOLD` until placeholder values are replaced with real submitted evidence fields.

## GL-33 Submission Template Consumption

- `scripts/gl33_submission_consumption.py` consumes GL-31 template loops using real external Beta submission rows and emits an ingestion-ready manifest.
- Inputs:
  - `real-trial-backfill-submission-manifest.template.json`
  - `real-trial-backfill-submission-real-inputs.json` (operator-provided real submission rows)
- Outputs:
  - `real_trial_backfill_submission_consumption.v1` JSON report
  - markdown summary
  - `manifests/real-trial-backfill-submission-manifest.consumed.json` (GL-12/GL-13 ingestible loop manifest)
- Contract:
  - requires real trace fields (`loop_id`, `source_system`, `source_reference`, `collected_at_utc`, `review_task_id`, `reviewed_by`, `reviewed_at_utc`)
  - rejects unresolved template mappings, missing required fields, invalid UTC timestamps, and any remaining `TEMPLATE_REQUIRED_*` values
  - does not override launch decision policy; launch decision remains owned by `launch_gate.py`

Example:

```bash
python scripts/gl31_submission_templates.py \
  --intake-actions-report docs/working/status/baselines/real-trial-loop-collection/real-trial-backfill-intake-actions-report.json \
  --output docs/working/status/baselines/real-trial-loop-collection/real-trial-backfill-submission-templates-report.json \
  --summary-output docs/working/status/baselines/real-trial-loop-collection/real-trial-backfill-submission-templates-summary.md \
  --manifest-template-output docs/working/status/baselines/real-trial-loop-collection/real-trial-backfill-submission-manifest.template.json \
  --owner controlled-beta-ops
```

```bash
python scripts/gl33_submission_consumption.py \
  --submission-manifest-template docs/working/status/baselines/real-trial-loop-collection/real-trial-backfill-submission-manifest.template.json \
  --real-submissions-input docs/working/status/baselines/real-trial-loop-collection/real-trial-backfill-submission-real-inputs.json \
  --output docs/working/status/baselines/real-trial-loop-collection/real-trial-backfill-submission-consumption-report.json \
  --summary-output docs/working/status/baselines/real-trial-loop-collection/real-trial-backfill-submission-consumption-summary.md \
  --consumed-manifest-output docs/working/status/baselines/real-trial-loop-collection/manifests/real-trial-backfill-submission-manifest.consumed.json \
  --owner controlled-beta-ops
```






