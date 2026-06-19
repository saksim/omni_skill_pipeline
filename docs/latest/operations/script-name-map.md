# Script Name Map

Script entry points use compact names. GL scripts use `glNN_*` because the GL number is the stable task key. Other operational scripts use short action-oriented names. Schema versions, generated artifact filenames, and report filenames remain unchanged for compatibility.

## GL real-trial scripts

| GL | Current script | Previous script | Test module | Schema version |
| --- | --- | --- | --- | --- |
| GL-12 | `scripts/gl12_collect_loops.py` | `scripts/run_real_trial_loop_collection.py` | `tests.test_gl12_collect_loops` | `real_trial_loop_collection.v1` |
| GL-13 | `scripts/gl13_launch_evidence.py` | `scripts/run_real_trial_launch_evidence.py` | `tests.test_gl13_launch_evidence` | evidence bridge |
| GL-22 | `scripts/gl22_backfill_exec.py` | `scripts/run_real_trial_backfill_execution.py` | `tests.test_gl22_backfill_exec` | `real_trial_backfill_execution.v1` |
| GL-23 | `scripts/gl23_intake_actions.py` | `scripts/run_real_trial_backfill_intake_actions.py` | `tests.test_gl23_intake_actions` | `real_trial_backfill_intake_actions.v1` |
| GL-24 | `scripts/gl24_handoff.py` | `scripts/run_real_trial_backfill_handoff.py` | `tests.test_gl24_handoff` | `real_trial_backfill_handoff.v1` |
| GL-27 | `scripts/gl27_handoff_escalations.py` | `scripts/run_real_trial_backfill_handoff_escalations.py` | `tests.test_gl27_handoff_escalations` | `real_trial_backfill_handoff_escalations.v1` |
| GL-31 | `scripts/gl31_submission_templates.py` | `scripts/run_real_trial_backfill_submission_templates.py` | `tests.test_gl31_submission_templates` | `real_trial_backfill_submission_templates.v1` |
| GL-33 | `scripts/gl33_submission_consumption.py` | `scripts/run_real_trial_backfill_submission_consumption.py` | `tests.test_gl33_submission_consumption` | `real_trial_backfill_submission_consumption.v1` |
| GL-35 | `scripts/gl35_submission_throughput.py` | `scripts/run_real_trial_submission_throughput.py` | `tests.test_gl35_submission_throughput` | `real_trial_submission_throughput.v1` |
| GL-37 | `scripts/gl37_submission_queue.py` | `scripts/run_real_trial_submission_queue.py` | `tests.test_gl37_submission_queue` | `real_trial_submission_queue.v1` |
| GL-38 | `scripts/gl38_queue_completion.py` | `scripts/run_real_trial_submission_queue_completion.py` | `tests.test_gl38_queue_completion` | `real_trial_submission_queue_completion.v1` |
| GL-39 | `scripts/gl39_queue_commitments.py` | `scripts/run_real_trial_submission_queue_commitments.py` | `tests.test_gl39_queue_commitments` | `real_trial_submission_queue_commitments.v1` |
| GL-40 | `scripts/gl40_commitment_closure.py` | `scripts/run_real_trial_submission_queue_commitment_closure.py` | `tests.test_gl40_commitment_closure` | `real_trial_submission_queue_commitment_closure.v1` |
| GL-41 | `scripts/gl41_queue_followup.py` | `scripts/run_real_trial_submission_queue_followup.py` | `tests.test_gl41_queue_followup` | `real_trial_submission_queue_followup.v1` |
| GL-42 | `scripts/gl42_followup_resolution.py` | `scripts/run_real_trial_submission_queue_followup_resolution.py` | `tests.test_gl42_followup_resolution` | `real_trial_submission_queue_followup_resolution.v1` |
| GL-43 | `scripts/gl43_resolution_escalations.py` | `scripts/run_real_trial_submission_queue_followup_resolution_escalations.py` | `tests.test_gl43_resolution_escalations` | `real_trial_submission_queue_followup_resolution_escalations.v1` |
| GL-44 | `scripts/gl44_escalation_ack.py` | `scripts/run_real_trial_submission_queue_followup_resolution_escalation_acknowledgements.py` | `tests.test_gl44_escalation_ack` | `real_trial_submission_queue_followup_resolution_escalation_acknowledgements.v1` |
| GL-45 | `scripts/gl45_escalation_throughput.py` | `scripts/run_real_trial_submission_queue_followup_resolution_escalation_throughput.py` | `tests.test_gl45_escalation_throughput` | `real_trial_submission_queue_followup_resolution_escalation_throughput.v1` |
| GL-46 | `scripts/gl46_action_plan.py` | `scripts/run_real_trial_submission_queue_followup_resolution_escalation_action_plan.py` | `tests.test_gl46_action_plan` | `real_trial_submission_queue_followup_resolution_escalation_action_plan.v1` |
| GL-47 | `scripts/gl47_action_plan_closure.py` | `scripts/run_real_trial_submission_queue_followup_resolution_escalation_action_plan_closure.py` | `tests.test_gl47_action_plan_closure` | `real_trial_submission_queue_followup_resolution_escalation_action_plan_closure.v1` |
| GL-48 | `scripts/gl48_action_plan_cadence.py` | `scripts/run_real_trial_submission_queue_followup_resolution_escalation_action_plan_closure_cadence.py` | `tests.test_gl48_action_plan_cadence` | `real_trial_submission_queue_followup_resolution_escalation_action_plan_closure_cadence.v1` |
| GL-49 | `scripts/gl49_cadence_escalations.py` | `scripts/run_real_trial_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations.py` | `tests.test_gl49_cadence_escalations` | `real_trial_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations.v1` |
| GL-50 | `scripts/gl50_ack_ingestion.py` | `scripts/run_real_trial_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion.py` | `tests.test_gl50_ack_ingestion` | `real_trial_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion.v1` |
| GL-51 | `scripts/gl51_ack_closure.py` | `scripts/run_real_trial_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure.py` | `tests.test_gl51_ack_closure` | `real_trial_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure.v1` |
| GL-52 | `scripts/gl52_ack_closure_cadence.py` | `scripts/run_real_trial_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence.py` | `tests.test_gl52_ack_closure_cadence` | `real_trial_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence.v1` |
| GL-53 | `scripts/gl53_ack_cadence_escalations.py` | `scripts/run_real_trial_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations.py` | `tests.test_gl53_ack_cadence_escalations` | `real_trial_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations.v1` |
| GL-54 | `scripts/gl54_ack_escalation_closure.py` | `scripts/run_real_trial_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure.py` | `tests.test_gl54_ack_escalation_closure` | `real_trial_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure.v1` |
| GL-55 | `scripts/gl55_escalation_closure_cadence.py` | `scripts/run_real_trial_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence.py` | `tests.test_gl55_escalation_closure_cadence` | `real_trial_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence.v1` |
| GL-56 | `scripts/gl56_closure_cadence_escalations.py` | `scripts/run_real_trial_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations.py` | `tests.test_gl56_closure_cadence_escalations` | `real_trial_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations.v1` |

## Operational scripts

| Current script | Previous script |
| --- | --- |
| `scripts/agent_smoke.py` | `scripts/run_agent_smoke_record.py` |
| `scripts/bench_dual_write.py` | `scripts/benchmark_dual_write.py` |
| `scripts/ci.py` | `scripts/run_ci.py` |
| `scripts/container_smoke.py` | `scripts/run_container_smoke.py` |
| `scripts/controlled_trial.py` | `scripts/run_controlled_trial.py` |
| `scripts/doc_sync.py` | `scripts/run_doc_sync_check.py` |
| `scripts/export_schema.py` | `scripts/export_skill_schema.py` |
| `scripts/ga_calibration.py` | `scripts/run_calibration_ga_validation.py` |
| `scripts/ga_review_queue.py` | `scripts/run_review_queue_ga_validation.py` |
| `scripts/launch_gate.py` | `scripts/run_launch_readiness_gate.py` |
| `scripts/linux_release.sh` | `scripts/run_linux_release_test.sh` |
| `scripts/linux_validate.py` | `scripts/run_linux_validation_suite.py` |
| `scripts/ops_evidence.py` | `scripts/run_ops_readiness_evidence.py` |
| `scripts/perf_baseline.py` | `scripts/run_perf_cost_baseline.py` |
| `scripts/pg_ga.py` | `scripts/run_postgres_ga_validation.py` |
| `scripts/pg_soak.py` | `scripts/run_postgres_soak_validation.py` |
| `scripts/provider_ga.py` | `scripts/run_provider_ga_validation.py` |
| `scripts/prune_tmp.py` | `scripts/prune_tmp_media.py` |
| `scripts/quality_loop.py` | `scripts/run_quality_feedback_loop.py` |
| `scripts/quality_regression.py` | `scripts/run_quality_regression.py` |
| `scripts/release_gate.py` | `scripts/run_release_gate_validation.py` |
| `scripts/release_switch.py` | `scripts/run_release_switch_validation.py` |
| `scripts/roadmap_ext.py` | `scripts/run_roadmap_extension_validation.py` |
| `scripts/skill_usability.py` | `scripts/run_skill_usability_validator.py` |
| `scripts/tp_tests.py` | `scripts/run_tp_tests.py` |
| `scripts/trial_metrics.py` | `scripts/run_trial_metrics_collector.py` |
| `scripts/trial_security.py` | `scripts/run_trial_security_gate.py` |
| `scripts/tune_review.py` | `scripts/tune_review_policy.py` |
| `scripts/validate_manifest.py` | `scripts/validate_trial_manifest.py` |
| `scripts/worker_ga.py` | `scripts/run_worker_ga_validation.py` |

New GL scripts should follow the same pattern: `scripts/glNN_short_purpose.py` and `tests/test_glNN_short_purpose.py`. New operational scripts should keep the shortest clear action name and add a row here when replacing an existing entry point.
