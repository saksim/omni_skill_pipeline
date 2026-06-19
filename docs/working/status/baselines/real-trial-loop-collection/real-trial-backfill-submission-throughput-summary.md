# Real Trial Submission Throughput Summary

- Throughput status: `THROUGHPUT_STALLED`
- Threshold met: `false`
- Previous snapshot available: `true`
- Current eligible real loops: `0`
- Previous eligible real loops: `0`
- Net new eligible real loops: `0`
- Current missing loops to threshold: `10`
- Current missing modalities to threshold: `4`
- Current remaining backfill slots: `10`
- Current submission-backed remaining slots: `10`
- Current consumed submission loops: `0`
- Execution focus status: `ACTION_PLAN_WAITING_FOR_SUBMISSIONS`
- Pending submission actions: `10`

## Warning Codes
- `no_net_new_launch_gate_eligible_real_loops`
- `modality_gap_persists`

## Priority Modalities
- `audio` pending_slots=3
- `text` pending_slots=3
- `image` pending_slots=2
- `video` pending_slots=2

## Recommended Submission Actions
- action=gl23-slot-001-text slot=1 modality=text reason=pending_template_submission_required
- action=gl23-slot-002-audio slot=2 modality=audio reason=pending_template_submission_required
- action=gl23-slot-003-image slot=3 modality=image reason=pending_template_submission_required
- action=gl23-slot-004-video slot=4 modality=video reason=pending_template_submission_required
- action=gl23-slot-005-text slot=5 modality=text reason=pending_template_submission_required
- action=gl23-slot-006-audio slot=6 modality=audio reason=pending_template_submission_required
- action=gl23-slot-007-image slot=7 modality=image reason=pending_template_submission_required
- action=gl23-slot-008-video slot=8 modality=video reason=pending_template_submission_required
- action=gl23-slot-009-text slot=9 modality=text reason=pending_template_submission_required
- action=gl23-slot-010-audio slot=10 modality=audio reason=pending_template_submission_required

## Net New Loop IDs
- none
