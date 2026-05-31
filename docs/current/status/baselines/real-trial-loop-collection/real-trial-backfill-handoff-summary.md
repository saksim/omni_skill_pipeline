# Real Trial Backfill Handoff Summary

- Handoff status: `HANDOFF_ACTIONS_PENDING`
- Queue owner: `controlled-beta-ops`
- Total queue items: `10`
- Open queue items: `10`
- Submission-linked pending-ack items: `0`
- Closure acknowledged items: `0`
- Ack SLA status: `ACK_SLA_NOT_REQUIRED`
- Ack pending within SLA: `0`
- Ack SLA breached: `0`
- Ack overdue escalation: `0`
- Ack tracking incomplete: `0`
- Submission linkage strategy counts: `{'action_id_and_slot_index': 0, 'action_id_only': 0, 'slot_index_only': 0, 'modality_fallback': 0, 'none': 10}`
- Unlinked submissions: `0`
- Launch-gap missing loops: `10`
- Launch-gap missing modalities: `4`

## Open Queue Items
- `gl24-queue-gl23-slot-001-text` slot=1 modality=text reason=missing_target_launch_modality assignee=controlled-beta-ops
- `gl24-queue-gl23-slot-002-audio` slot=2 modality=audio reason=missing_target_launch_modality assignee=controlled-beta-ops
- `gl24-queue-gl23-slot-003-image` slot=3 modality=image reason=missing_target_launch_modality assignee=controlled-beta-ops
- `gl24-queue-gl23-slot-004-video` slot=4 modality=video reason=missing_target_launch_modality assignee=controlled-beta-ops
- `gl24-queue-gl23-slot-005-text` slot=5 modality=text reason=loop_volume_gap_after_modality_coverage assignee=controlled-beta-ops
- `gl24-queue-gl23-slot-006-audio` slot=6 modality=audio reason=loop_volume_gap_after_modality_coverage assignee=controlled-beta-ops
- `gl24-queue-gl23-slot-007-image` slot=7 modality=image reason=loop_volume_gap_after_modality_coverage assignee=controlled-beta-ops
- `gl24-queue-gl23-slot-008-video` slot=8 modality=video reason=loop_volume_gap_after_modality_coverage assignee=controlled-beta-ops
- `gl24-queue-gl23-slot-009-text` slot=9 modality=text reason=loop_volume_gap_after_modality_coverage assignee=controlled-beta-ops
- `gl24-queue-gl23-slot-010-audio` slot=10 modality=audio reason=loop_volume_gap_after_modality_coverage assignee=controlled-beta-ops

## Submission Linked Pending Operator Ack
- none

## Pending Ack SLA Breached Items
- none

## Pending Ack Overdue Escalation Items
- none
