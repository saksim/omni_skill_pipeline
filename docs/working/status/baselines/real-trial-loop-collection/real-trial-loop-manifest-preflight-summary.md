# Real Trial Loop Manifest Preflight Summary

- Status: `REAL_LOOP_MANIFEST_PREFLIGHT_PENDING`
- Launch gate policy unchanged: `true`
- GL-63 workpack: `docs/working/status/baselines/real-trial-loop-collection/real-trial-loop-intake-workpack-report.json`
- Manifest directory: `docs/working/status/baselines/real-trial-loop-collection/manifests`
- Valid items: `0/10`
- Missing items: `10`
- Invalid items: `0`
- Accepted loop rows: `0`

## Warning Codes
- `real_loop_manifests_missing`
- `real_loop_manifest_preflight_not_ready`

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
python -B scripts\gl13_launch_evidence.py --loop-manifest-dir docs/working/status/baselines/real-trial-loop-collection/manifests --strict-loop-manifest-contract --no-run-doc-sync --max-evidence-age-hours 0
```
