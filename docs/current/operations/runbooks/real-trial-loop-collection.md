# Real Trial Loop Collection (GL-12 / GL-13 / GL-16)

## Verdict

This runbook defines how to collect and classify real controlled-trial loops for launch-gate evidence.
It does not authorize GA claims. Output statuses are evidence tracking states only.

## Scope

- Collector script: `scripts/run_real_trial_loop_collection.py`
- Bridge script: `scripts/run_real_trial_launch_evidence.py`
- Input sources:
  - one or more controlled-trial run reports (`controlled-trial-run-report.json`)
  - one or more explicit real-loop manifests (`--loop-manifest`)
- Output artifacts:
  - `real-trial-loop-collection-report.json`
  - `real-trial-loop-collection-summary.md`
  - `real-trial-loop-metrics-manifest.json`
  - `real-trial-launch-evidence-pack.json`
- Baseline template:
  - `docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-metrics-manifest.template.json`

## Preconditions

- Real loops must be explicitly labeled:
  - `evidence_origin=real`
  - `launch_gate_eligible=true`
  - `source_system`, `source_reference`, `collected_at_utc`
  - `review_task_id`, `reviewed_by`, `reviewed_at_utc`
- Fixture/synthetic loops may exist in the same report, but they must remain non-launch-gate-eligible.

## Collect From Controlled-Trial Run Report

```bash
python scripts/run_real_trial_loop_collection.py \
  --run-report docs/current/status/baselines/controlled-trial/controlled-trial-run-report.json \
  --output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-report.json \
  --summary-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-summary.md \
  --manifest-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-metrics-manifest.json
```

## Merge Multiple Run Reports

```bash
python scripts/run_real_trial_loop_collection.py \
  --run-report docs/current/status/baselines/controlled-trial/controlled-trial-run-report-a.json \
  --run-report docs/current/status/baselines/controlled-trial/controlled-trial-run-report-b.json \
  --output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-report.json \
  --summary-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-summary.md \
  --manifest-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-metrics-manifest.json
```

## Batch Ingest Real Loop Manifests (GL-17)

When real loops are collected outside the controlled-trial fixture runner, ingest them in batch from one or more manifest directories.

```bash
python scripts/run_real_trial_loop_collection.py \
  --loop-manifest-dir docs/current/status/baselines/real-trial-loop-collection/manifests \
  --loop-manifest-pattern "*.json" \
  --output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-report.json \
  --summary-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-summary.md \
  --manifest-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-metrics-manifest.json
```

Optional recursive scan:

```bash
python scripts/run_real_trial_loop_collection.py \
  --loop-manifest-dir docs/current/status/baselines/real-trial-loop-collection/manifests \
  --loop-manifest-pattern "**/*.json" \
  --loop-manifest-recursive
```

Default batch behavior is tolerant: JSON files that do not have top-level `loops` are skipped and reported in
`skipped_non_loop_manifest_paths`.
Use strict contract mode to fail fast instead:

```bash
python scripts/run_real_trial_loop_collection.py \
  --loop-manifest-dir docs/current/status/baselines/real-trial-loop-collection/manifests \
  --loop-manifest-pattern "*.json" \
  --strict-loop-manifest-contract
```

The collection report now includes:

- `input_loop_manifest_dir_count`
- `source_loop_manifest_dirs`
- `ingested_loop_manifest_count`
- `skipped_non_loop_manifest_count`
- `skipped_non_loop_manifest_paths`
- `launch_gate_alignment.missing_complete_loops_to_threshold`
- `launch_gate_alignment.missing_modalities_to_threshold`

## Strict Blocker Mode

```bash
python scripts/run_real_trial_loop_collection.py \
  --run-report docs/current/status/baselines/controlled-trial/controlled-trial-run-report.json \
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
  - `python scripts/run_launch_readiness_gate.py --output - --summary-output -`

## GL-13 One-Command Evidence Pipeline

For controlled external Beta operations, use the GL-13 bridge script to run:

1. real-loop collection
2. trial metrics report generation
3. launch-readiness gate evaluation
4. GL-16 evidence pack publication

```bash
python scripts/run_real_trial_launch_evidence.py \
  --run-report docs/current/status/baselines/controlled-trial/controlled-trial-run-report.json \
  --collection-report-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-report.json \
  --collection-summary-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-summary.md \
  --real-trial-manifest-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-metrics-manifest.json \
  --trial-metrics-report-output docs/current/status/baselines/controlled-trial/trial-metrics-report.json \
  --trial-metrics-summary-output docs/current/status/baselines/controlled-trial/trial-metrics-summary.md \
  --launch-readiness-output docs/current/status/baselines/broad-launch-readiness-report.json \
  --launch-readiness-summary-output docs/current/status/baselines/broad-launch-readiness-summary.md \
  --evidence-pack-output docs/current/status/baselines/real-trial-loop-collection/real-trial-launch-evidence-pack.json \
  --max-evidence-age-hours 0
```

Batch manifest mode:

```bash
python scripts/run_real_trial_launch_evidence.py \
  --loop-manifest-dir docs/current/status/baselines/real-trial-loop-collection/manifests \
  --loop-manifest-pattern "*.json" \
  --collection-report-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-report.json \
  --collection-summary-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-collection-summary.md \
  --real-trial-manifest-output docs/current/status/baselines/real-trial-loop-collection/real-trial-loop-metrics-manifest.json \
  --trial-metrics-report-output docs/current/status/baselines/controlled-trial/trial-metrics-report.json \
  --trial-metrics-summary-output docs/current/status/baselines/controlled-trial/trial-metrics-summary.md \
  --launch-readiness-output docs/current/status/baselines/broad-launch-readiness-report.json \
  --launch-readiness-summary-output docs/current/status/baselines/broad-launch-readiness-summary.md \
  --evidence-pack-output docs/current/status/baselines/real-trial-loop-collection/real-trial-launch-evidence-pack.json \
  --max-evidence-age-hours 0
```

Optional strict CI-style behavior:

```bash
python scripts/run_real_trial_launch_evidence.py \
  --run-report docs/current/status/baselines/controlled-trial/controlled-trial-run-report.json \
  --fail-on-blocker \
  --fail-on-hold
```

## GL-16 Evidence Pack Contract

GL-16 publishes `real-trial-launch-evidence-pack.json` as machine-readable reviewer/operator handoff:

- decision and readiness level (controlled external Beta scope)
- source input accounting (`run-report` + `loop-manifest`)
- evidence classification:
  - total loop/modality coverage
  - launch-gate-eligible real loop/modality coverage
  - missing real source/reviewer trace counts
- launch-gate blocker summary

This evidence pack does not override launch readiness policy and does not permit GA claims.
