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
- Generated outputs:
  - `docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-report.json`
  - `docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-summary.md`
  - `docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-metrics-manifest.json`
- Linux example:
  - `python scripts/run_real_trial_loop_collection.py --run-report docs/current/status/baselines/controlled-trial/controlled-trial-run-report.json --output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-report.json --summary-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-summary.md --manifest-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-metrics-manifest.json`
- Batch real-loop manifest example (GL-17):
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
  - strict mode example:
    - `python scripts/run_real_trial_loop_collection.py --loop-manifest-dir docs/current/status/baselines/real-trial-loop-collection/manifests --loop-manifest-pattern "*.json" --strict-loop-manifest-contract --output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-report.json --summary-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-summary.md --manifest-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-metrics-manifest.json`

## GL-13 Real Trial Launch Evidence Bridge

- Bridge script: `scripts/run_real_trial_launch_evidence.py`
- Purpose: chain GL-12 loop collection -> trial metrics collector -> launch readiness gate with one command.
- Key outputs:
  - `docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-report.json`
  - `docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-summary.md`
  - `docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-metrics-manifest.json`
  - `docs/current/status/baselines/controlled-trial/trial-metrics-report.json`
  - `docs/current/status/baselines/controlled-trial/trial-metrics-summary.md`
  - `docs/current/status/baselines/broad-launch-readiness-report.json`
  - `docs/current/status/baselines/broad-launch-readiness-summary.md`
- Linux example:
  - `python scripts/run_real_trial_launch_evidence.py --run-report docs/current/status/baselines/controlled-trial/controlled-trial-run-report.json --collection-report-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-report.json --collection-summary-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-summary.md --real-trial-manifest-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-metrics-manifest.json --trial-metrics-report-output docs/current/status/baselines/controlled-trial/trial-metrics-report.json --trial-metrics-summary-output docs/current/status/baselines/controlled-trial/trial-metrics-summary.md --launch-readiness-output docs/current/status/baselines/broad-launch-readiness-report.json --launch-readiness-summary-output docs/current/status/baselines/broad-launch-readiness-summary.md --evidence-pack-output docs/current/status/baselines/real-trial-loop-collection/real-trial-launch-evidence-pack.json --max-evidence-age-hours 0`
- Batch manifest directory mode (GL-17):
  - `python scripts/run_real_trial_launch_evidence.py --loop-manifest-dir docs/current/status/baselines/real-trial-loop-collection/manifests --loop-manifest-pattern "*.json" --collection-report-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-report.json --collection-summary-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-summary.md --real-trial-manifest-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-metrics-manifest.json --trial-metrics-report-output docs/current/status/baselines/controlled-trial/trial-metrics-report.json --trial-metrics-summary-output docs/current/status/baselines/controlled-trial/trial-metrics-summary.md --launch-readiness-output docs/current/status/baselines/broad-launch-readiness-report.json --launch-readiness-summary-output docs/current/status/baselines/broad-launch-readiness-summary.md --evidence-pack-output docs/current/status/baselines/real-trial-loop-collection/real-trial-launch-evidence-pack.json --max-evidence-age-hours 0`

## GL-16 Controlled External Beta Evidence Pack

- Pack output:
  - `docs/current/status/baselines/real-trial-loop-collection/real-trial-launch-evidence-pack.json`
- Pack contract:
  - machine-readable launch decision summary for controlled external Beta review handoff
  - explicit classification of total loops/modalities vs launch-gate-eligible real loops/modalities
  - real evidence source/reviewer trace missing counts and current launch blocker list

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
