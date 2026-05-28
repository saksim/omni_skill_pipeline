# E0 Baseline Pack

## Verdict

This directory preserves comparable baseline evidence packs for controlled-trial and broad-launch execution.

## Included Packs

- `trial-manifests/`: controlled-trial sample manifest contracts and modality examples.
- `trial-metrics/`: trial metrics collector template/report/summary artifacts.
- `controlled-trial/`: controlled-trial runner outputs.
- `real-trial-loop-collection/`: GL-12 real-loop evidence collection outputs.

## CBT-11 End-to-End Trial Runner

- Runner script: `scripts/run_controlled_trial.py`
- Operations runbook: `docs/current/operations/runbooks/controlled-trial-loop.md`
- Default output directory: `docs/current/status/baselines/controlled-trial/`
- Key outputs:
  - `controlled-trial-execution-plan.json`
  - `controlled-trial-run-report.json`
  - `trial-metrics-manifest.json`
  - `trial-metrics-report.json`
  - `trial-metrics-summary.md`

## GL-12 Real Trial Loop Collection

- Collector script: `scripts/run_real_trial_loop_collection.py`
- Operations runbook: `docs/current/operations/runbooks/real-trial-loop-collection.md`
- Template manifest:
  - `docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-metrics-manifest.template.json`
- Batch input directory:
  - `docs/current/status/baselines/real-trial-loop-collection/manifests/`
  - This directory is an operator drop zone for real-loop `.json` manifests. Release artifacts do not populate it.
- Generated outputs:
  - `docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-report.json`
  - `docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-summary.md`
  - `docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-metrics-manifest.json`
  - `docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-backfill-plan.json`
  - `docs/current/status/baselines/real-trial-loop-collection/real-trial-backfill-execution-report.json`
  - `docs/current/status/baselines/real-trial-loop-collection/real-trial-backfill-execution-summary.md`
  - `docs/current/status/baselines/real-trial-loop-collection/real-trial-backfill-intake-actions-report.json`
  - `docs/current/status/baselines/real-trial-loop-collection/real-trial-backfill-intake-actions-summary.md`
  - `docs/current/status/baselines/real-trial-loop-collection/real-trial-backfill-submission-templates-report.json`
  - `docs/current/status/baselines/real-trial-loop-collection/real-trial-backfill-submission-templates-summary.md`
  - `docs/current/status/baselines/real-trial-loop-collection/real-trial-backfill-submission-manifest.template.json`
  - `docs/current/status/baselines/real-trial-loop-collection/real-trial-backfill-handoff-report.json`
  - `docs/current/status/baselines/real-trial-loop-collection/real-trial-backfill-handoff-summary.md`
  - `docs/current/status/baselines/real-trial-loop-collection/real-trial-backfill-handoff-escalations-report.json`
  - `docs/current/status/baselines/real-trial-loop-collection/real-trial-backfill-handoff-escalations-summary.md`
- Linux example:
  - `python scripts/run_real_trial_loop_collection.py --run-report docs/current/status/baselines/controlled-trial/controlled-trial-run-report.json --output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-report.json --summary-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-summary.md --manifest-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-metrics-manifest.json`
- Batch real-loop manifest example (GL-17):
  - Place at least one real-loop JSON manifest in `docs/current/status/baselines/real-trial-loop-collection/manifests/` before running this mode.
  - `python scripts/run_real_trial_loop_collection.py --loop-manifest-dir docs/current/status/baselines/real-trial-loop-collection/manifests --loop-manifest-pattern "*.json" --output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-report.json --summary-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-summary.md --manifest-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-metrics-manifest.json`
- GL-18 manifest-contract behavior:
  - default batch intake skips non-loop-manifest JSON files and reports:
    - `ingested_loop_manifest_count`
    - `skipped_non_loop_manifest_count`
    - `skipped_non_loop_manifest_paths`
    - `duplicate_resolution_count`
    - `duplicate_resolution_records`
    - `launch_gate_alignment.target_launch_modalities`
    - `launch_gate_alignment.covered_target_launch_modalities`
    - `launch_gate_alignment.missing_target_launch_modalities`
    - `launch_gate_alignment.recommended_next_modalities`
    - `launch_gate_alignment.launch_gate_eligible_complete_loop_count_by_modality`
    - `launch_gate_alignment.target_launch_modality_loop_counts`
    - `launch_gate_alignment.recommended_backfill_slot_count`
    - `launch_gate_alignment.recommended_backfill_slots`
  - strict mode example:
    - `python scripts/run_real_trial_loop_collection.py --loop-manifest-dir docs/current/status/baselines/real-trial-loop-collection/manifests --loop-manifest-pattern "*.json" --strict-loop-manifest-contract --output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-report.json --summary-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-summary.md --manifest-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-metrics-manifest.json`

## GL-13 Real Trial Launch Evidence Bridge

- Bridge script: `scripts/run_real_trial_launch_evidence.py`
- Purpose: chain GL-12 loop collection -> trial metrics collector -> launch readiness gate with one command.
- Key outputs:
  - `docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-report.json`
  - `docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-summary.md`
  - `docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-metrics-manifest.json`
  - `docs/current/status/baselines/real-trial-loop-collection/real-trial-backfill-execution-report.json`
  - `docs/current/status/baselines/real-trial-loop-collection/real-trial-backfill-execution-summary.md`
  - `docs/current/status/baselines/real-trial-loop-collection/real-trial-backfill-intake-actions-report.json`
  - `docs/current/status/baselines/real-trial-loop-collection/real-trial-backfill-intake-actions-summary.md`
  - `docs/current/status/baselines/real-trial-loop-collection/real-trial-backfill-submission-templates-report.json`
  - `docs/current/status/baselines/real-trial-loop-collection/real-trial-backfill-submission-templates-summary.md`
  - `docs/current/status/baselines/real-trial-loop-collection/real-trial-backfill-submission-manifest.template.json`
  - `docs/current/status/baselines/real-trial-loop-collection/real-trial-backfill-handoff-report.json`
  - `docs/current/status/baselines/real-trial-loop-collection/real-trial-backfill-handoff-summary.md`
  - `docs/current/status/baselines/real-trial-loop-collection/real-trial-backfill-handoff-escalations-report.json`
  - `docs/current/status/baselines/real-trial-loop-collection/real-trial-backfill-handoff-escalations-summary.md`
  - `docs/current/status/baselines/controlled-trial/trial-metrics-report.json`
  - `docs/current/status/baselines/controlled-trial/trial-metrics-summary.md`
  - `docs/current/status/baselines/broad-launch-readiness-report.json`
  - `docs/current/status/baselines/broad-launch-readiness-summary.md`
- Linux example:
  - `python scripts/run_real_trial_launch_evidence.py --run-report docs/current/status/baselines/controlled-trial/controlled-trial-run-report.json --collection-report-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-report.json --collection-summary-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-summary.md --real-trial-manifest-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-metrics-manifest.json --trial-metrics-report-output docs/current/status/baselines/controlled-trial/trial-metrics-report.json --trial-metrics-summary-output docs/current/status/baselines/controlled-trial/trial-metrics-summary.md --launch-readiness-output docs/current/status/baselines/broad-launch-readiness-report.json --launch-readiness-summary-output docs/current/status/baselines/broad-launch-readiness-summary.md --evidence-pack-output docs/current/status/baselines/real-trial-loop-collection/real-trial-launch-evidence-pack.json --max-evidence-age-hours 0`
- Batch manifest directory mode (GL-17):
  - Place at least one real-loop JSON manifest in `docs/current/status/baselines/real-trial-loop-collection/manifests/` before running this mode. An empty directory fails fast and does not fall back to fixture evidence.
  - `python scripts/run_real_trial_launch_evidence.py --loop-manifest-dir docs/current/status/baselines/real-trial-loop-collection/manifests --loop-manifest-pattern "*.json" --collection-report-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-report.json --collection-summary-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-summary.md --real-trial-manifest-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-metrics-manifest.json --trial-metrics-report-output docs/current/status/baselines/controlled-trial/trial-metrics-report.json --trial-metrics-summary-output docs/current/status/baselines/controlled-trial/trial-metrics-summary.md --launch-readiness-output docs/current/status/baselines/broad-launch-readiness-report.json --launch-readiness-summary-output docs/current/status/baselines/broad-launch-readiness-summary.md --evidence-pack-output docs/current/status/baselines/real-trial-loop-collection/real-trial-launch-evidence-pack.json --max-evidence-age-hours 0`

## GL-16 Controlled External Beta Evidence Pack

- Pack output:
  - `docs/current/status/baselines/real-trial-loop-collection/real-trial-launch-evidence-pack.json`
- Pack contract:
  - machine-readable launch decision summary for controlled external Beta review handoff
  - explicit classification of total loops/modalities vs launch-gate-eligible real loops/modalities
  - real evidence source/reviewer trace missing counts and current launch blocker list
  - GL-22 backfill execution progress fields:
    - `backfill_execution_status`
    - `backfill_execution_fulfilled_slot_count`
    - `backfill_execution_remaining_slot_count`
    - `backfill_execution_gained_target_launch_modality_loop_counts`
  - GL-30 submission-backed execution fields:
    - `backfill_execution_submission_backed_status`
    - `backfill_execution_submission_backed_fulfilled_slot_count`
    - `backfill_execution_submission_backed_remaining_slot_count`
    - `backfill_execution_fulfilled_without_submission_linkage_count`
    - `backfill_execution_submission_linked_without_modality_delta_count`
  - GL-28 real submission linkage fields:
    - `backfill_execution_submission_linked_slot_count`
    - `backfill_execution_submission_slot_linked_count`
    - `backfill_execution_submission_action_linked_count`
    - `backfill_execution_unmatched_submission_linkage_count`
    - `backfill_execution_submission_linkage_records`
    - `backfill_execution_unmatched_submission_linkages`
  - GL-23 intake action bridge fields:
    - `backfill_intake_status`
    - `backfill_intake_total_action_count`
    - `backfill_intake_pending_action_count`
    - `backfill_intake_closed_action_count`
    - `backfill_intake_owner`
  - GL-31 submission template bridge fields:
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
  - GL-24 handoff bridge fields:
    - `backfill_handoff_status`
    - `backfill_handoff_total_queue_item_count`
    - `backfill_handoff_open_queue_item_count`
    - `backfill_handoff_submission_linked_pending_ack_count`
    - `backfill_handoff_closure_acknowledged_count`
    - `backfill_handoff_owner`
  - GL-29 linkage-aware handoff assignment fields:
    - `backfill_handoff_submission_linkage_strategy_counts`
    - `backfill_handoff_submission_unlinked_count`
    - `backfill_handoff_submission_unlinked_records`
  - GL-25 acknowledgement linkage fields:
    - `evidence_paths.real_trial_backfill_handoff_acknowledgements_report`
    - `backfill_handoff_acknowledgement_input_count`
    - `backfill_handoff_acknowledgement_valid_count`
    - `backfill_handoff_acknowledgement_invalid_count`
    - `backfill_handoff_acknowledgement_invalid_records`
  - GL-26 acknowledgement SLA tracking fields:
    - `backfill_handoff_acknowledgement_sla_status`
    - `backfill_handoff_acknowledgement_sla_hours`
    - `backfill_handoff_acknowledgement_overdue_hours`
    - `backfill_handoff_acknowledgement_sla_evaluation_timestamp_utc`
    - `backfill_handoff_acknowledgement_within_sla_count`
    - `backfill_handoff_acknowledgement_sla_breached_count`
    - `backfill_handoff_acknowledgement_overdue_count`
    - `backfill_handoff_acknowledgement_tracking_incomplete_count`
    - `backfill_handoff_acknowledgement_sla_breached_queue_items`
    - `backfill_handoff_acknowledgement_overdue_queue_items`
    - `backfill_handoff_acknowledgement_tracking_incomplete_queue_items`
  - GL-27 escalation export fields:
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

## GL-14 Real Trial Reviewer Trace Contract

- Real launch-gate-eligible loops now require reviewer trace fields:
  - `review_task_id`
  - `reviewed_by`
  - `reviewed_at_utc`
- Collector/trial-metrics/launch-gate now surface and block on:
  - `real_evidence_missing_review_trace_count`
- Missing reviewer trace keeps evidence status `COLLECTION_INCOMPLETE` and launch decision at `HOLD`.

## Notes

- GL-12 outputs classify evidence; they do not bypass launch readiness gate.
- Final launch decision must still be evaluated by `scripts/run_launch_readiness_gate.py`.

