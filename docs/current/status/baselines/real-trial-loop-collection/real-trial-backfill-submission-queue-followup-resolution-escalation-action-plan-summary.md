# Real Trial Submission Queue Follow-Up Resolution Escalation Action Plan Summary

- GL-45 throughput status: `ESCALATION_ACK_THROUGHPUT_STALLED`
- GL-46 action-plan status: `ACTION_PLAN_OPEN`
- Total action items: `10`
- Open action items: `10`
- Missing loops to threshold: `10`
- Missing modalities to threshold: `4`

## Warning Codes
- `no_net_new_resolved_acknowledgements`
- `no_net_new_launch_gate_eligible_real_loops`
- `modality_gap_persists`
- `loop_volume_gap_persists`
- `open_acknowledgement_items_present`
- `escalation_ack_blocked`
- `open_escalation_acknowledgement_items_present`
- `open_followup_resolution_escalation_action_plan_items_present`

## Action Items
- `gl46-slot-001-text` type=collect_launch_gate_eligible_real_loop modality=text slot=1 reason=missing_target_launch_modality
- `gl46-slot-002-audio` type=collect_launch_gate_eligible_real_loop modality=audio slot=2 reason=missing_target_launch_modality
- `gl46-slot-003-image` type=collect_launch_gate_eligible_real_loop modality=image slot=3 reason=missing_target_launch_modality
- `gl46-slot-004-video` type=collect_launch_gate_eligible_real_loop modality=video slot=4 reason=missing_target_launch_modality
- `gl46-slot-005-text` type=collect_launch_gate_eligible_real_loop modality=text slot=5 reason=loop_volume_gap_after_modality_coverage
- `gl46-slot-006-audio` type=collect_launch_gate_eligible_real_loop modality=audio slot=6 reason=loop_volume_gap_after_modality_coverage
- `gl46-slot-007-image` type=collect_launch_gate_eligible_real_loop modality=image slot=7 reason=loop_volume_gap_after_modality_coverage
- `gl46-slot-008-video` type=collect_launch_gate_eligible_real_loop modality=video slot=8 reason=loop_volume_gap_after_modality_coverage
- `gl46-slot-009-text` type=collect_launch_gate_eligible_real_loop modality=text slot=9 reason=loop_volume_gap_after_modality_coverage
- `gl46-slot-010-audio` type=collect_launch_gate_eligible_real_loop modality=audio slot=10 reason=loop_volume_gap_after_modality_coverage
