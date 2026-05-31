# E7 Calibration Guide

## Goal

Calibrate review policy thresholds using labeled samples where `quality_scores` are compared against human `reviewer_judgement`.

## Dataset

- Manifest: `docs/current/status/baselines/e7-calibration-manifest.json`
- Required fields per sample:
  - `sample_id`
  - `modality`
  - `quality_scores`
  - `reviewer_judgement.decision` (`auto_publish` / `review_required` / `reject`)

## Tuning Script

```bash
python scripts/tune_review.py \
  --manifest docs/current/status/baselines/e7-calibration-manifest.json \
  --output docs/current/status/baselines/e7-calibration-report.json \
  --print-json
```

## Output

The report includes:

- agreement summary (`matched`, `mismatched`, `accuracy`)
- confusion matrix (`reviewer` vs `policy`)
- mismatch details per sample
- current/suggested threshold sets and deltas

This report is the minimum contract for `LC-L2-31`.
