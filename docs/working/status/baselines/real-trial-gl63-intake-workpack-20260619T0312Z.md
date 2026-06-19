# Real Trial GL63 Intake Workpack 20260619T0312Z

> Generated on 2026-06-19.

## Scope

- Construction item: GL-63 real-loop intake workpack.
- Goal: turn the current real trial coverage gap into explicit operator intake items without creating or counting any real evidence.
- Decision boundary: `launch_gate.py` remains the official external launch gate and still reports `HOLD`.

## What Changed

- Added `scripts/gl63_real_loop_intake_workpack.py`.
- Added `tests/test_gl63_real_loop_intake_workpack.py`.
- Generated:
  - `docs/working/status/baselines/real-trial-loop-collection/real-trial-loop-intake-workpack-report.json`
  - `docs/working/status/baselines/real-trial-loop-collection/real-trial-loop-intake-workpack-summary.md`

## Current Readback

- Workpack status: `REAL_LOOP_INTAKE_ACTION_REQUIRED`.
- External launch decision: `HOLD`.
- Collection status: `COLLECTION_INCOMPLETE`.
- Launch-gate-eligible real loops: `0/10`.
- Covered target modalities: `0/4`.
- Open intake items: `10`.
- Intake split:
  - `text`: `3`
  - `audio`: `3`
  - `image`: `2`
  - `video`: `2`
- Manifest drop directory: `docs/working/status/baselines/real-trial-loop-collection/manifests`.

## Required Operator Contract

Each submitted real-loop manifest item must keep:

- `evidence_origin=real`
- `launch_gate_eligible=true`
- `source_system`
- `source_reference`
- `collected_at_utc`
- `review_task_id`
- `reviewed_by`
- `reviewed_at_utc`
- `status=complete`
- `agent_smoke_result`
- `published_without_review=false`
- `critical_secret_or_pii_leak=false`
- `high_severity_incident=false`

Fixture or simulated rows must remain `launch_gate_eligible=false`.

## Verification

- `python -B -m unittest tests.test_gl63_real_loop_intake_workpack`: pass.
- `python -B scripts\gl63_real_loop_intake_workpack.py`: pass; generated 10 open intake items.

## Remaining Mainline Gaps

- Docker smoke real run: skipped this round by user request; prior blocker is external Docker base-image metadata/token pull.
- Real loop collection: still incomplete; GL-63 only makes the operator workpack explicit.
- Review feedback calibration: not completed in this round.
- Platform preparation: not completed in this round.
