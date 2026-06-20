# Real Trial Loop Manifest Preflight Summary

- Status: `REAL_LOOP_MANIFEST_PREFLIGHT_PENDING`
- Launch gate policy unchanged: `true`
- GL-63 workpack: `docs/working/status/baselines/real-trial-loop-collection/real-trial-loop-intake-workpack-report.json`
- Manifest directory: `docs/working/status/baselines/real-trial-loop-collection/manifests`
- Valid items: `0/10`
- Missing items: `10`
- Invalid items: `0`
- Accepted loop rows: `0`

## Slot Readiness
- Required slots: `10`
- Ready slots: `0`
- Blocked slots: `10`
- Missing slot files: `10`
- Invalid slot files: `0`
- First blocking slot: `1` `text` `docs/working/status/baselines/real-trial-loop-collection/manifests/real-loop-001-text.json`

## Modality Readiness
- Target launch modalities: `text, audio, image, video`
- Covered target modalities: `none`
- Missing target modalities: `text, audio, image, video`

## Operator Action Plan
- Status: `action_required`
- Pending actions: `10`
- `drop_real_manifest` slot=1 modality=text manifest=docs/working/status/baselines/real-trial-loop-collection/manifests/real-loop-001-text.json failures=manifest_file_missing
- `drop_real_manifest` slot=2 modality=audio manifest=docs/working/status/baselines/real-trial-loop-collection/manifests/real-loop-002-audio.json failures=manifest_file_missing
- `drop_real_manifest` slot=3 modality=image manifest=docs/working/status/baselines/real-trial-loop-collection/manifests/real-loop-003-image.json failures=manifest_file_missing
- `drop_real_manifest` slot=4 modality=video manifest=docs/working/status/baselines/real-trial-loop-collection/manifests/real-loop-004-video.json failures=manifest_file_missing
- `drop_real_manifest` slot=5 modality=text manifest=docs/working/status/baselines/real-trial-loop-collection/manifests/real-loop-005-text.json failures=manifest_file_missing
- `drop_real_manifest` slot=6 modality=audio manifest=docs/working/status/baselines/real-trial-loop-collection/manifests/real-loop-006-audio.json failures=manifest_file_missing
- `drop_real_manifest` slot=7 modality=image manifest=docs/working/status/baselines/real-trial-loop-collection/manifests/real-loop-007-image.json failures=manifest_file_missing
- `drop_real_manifest` slot=8 modality=video manifest=docs/working/status/baselines/real-trial-loop-collection/manifests/real-loop-008-video.json failures=manifest_file_missing
- `drop_real_manifest` slot=9 modality=text manifest=docs/working/status/baselines/real-trial-loop-collection/manifests/real-loop-009-text.json failures=manifest_file_missing
- `drop_real_manifest` slot=10 modality=audio manifest=docs/working/status/baselines/real-trial-loop-collection/manifests/real-loop-010-audio.json failures=manifest_file_missing

## Warning Codes
- `real_loop_manifests_missing`
- `real_loop_manifest_preflight_not_ready`
- `real_loop_slot_gap_action_plan_required`

## Item Preflight
- `gl63-real-loop-intake-slot-001-text` status=missing modality=text manifest=docs/working/status/baselines/real-trial-loop-collection/manifests/real-loop-001-text.json accepted=0 failures=manifest_file_missing
- `gl63-real-loop-intake-slot-002-audio` status=missing modality=audio manifest=docs/working/status/baselines/real-trial-loop-collection/manifests/real-loop-002-audio.json accepted=0 failures=manifest_file_missing
- `gl63-real-loop-intake-slot-003-image` status=missing modality=image manifest=docs/working/status/baselines/real-trial-loop-collection/manifests/real-loop-003-image.json accepted=0 failures=manifest_file_missing
- `gl63-real-loop-intake-slot-004-video` status=missing modality=video manifest=docs/working/status/baselines/real-trial-loop-collection/manifests/real-loop-004-video.json accepted=0 failures=manifest_file_missing
- `gl63-real-loop-intake-slot-005-text` status=missing modality=text manifest=docs/working/status/baselines/real-trial-loop-collection/manifests/real-loop-005-text.json accepted=0 failures=manifest_file_missing
- `gl63-real-loop-intake-slot-006-audio` status=missing modality=audio manifest=docs/working/status/baselines/real-trial-loop-collection/manifests/real-loop-006-audio.json accepted=0 failures=manifest_file_missing
- `gl63-real-loop-intake-slot-007-image` status=missing modality=image manifest=docs/working/status/baselines/real-trial-loop-collection/manifests/real-loop-007-image.json accepted=0 failures=manifest_file_missing
- `gl63-real-loop-intake-slot-008-video` status=missing modality=video manifest=docs/working/status/baselines/real-trial-loop-collection/manifests/real-loop-008-video.json accepted=0 failures=manifest_file_missing
- `gl63-real-loop-intake-slot-009-text` status=missing modality=text manifest=docs/working/status/baselines/real-trial-loop-collection/manifests/real-loop-009-text.json accepted=0 failures=manifest_file_missing
- `gl63-real-loop-intake-slot-010-audio` status=missing modality=audio manifest=docs/working/status/baselines/real-trial-loop-collection/manifests/real-loop-010-audio.json accepted=0 failures=manifest_file_missing

## Next Command

```powershell
python -B scripts\gl13_launch_evidence.py --loop-manifest-dir docs/working/status/baselines/real-trial-loop-collection/manifests --strict-loop-manifest-contract --require-manifest-preflight-ready --no-run-doc-sync --max-evidence-age-hours 0
```
