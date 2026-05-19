# Controlled Trial Sample Manifest Pack (CBT-02)

This directory defines the controlled business trial sample manifest contract used by `CBT-02`.

## Files

- `trial-sample-manifest.template.json`
  - Required-field template for controlled trial intake.
- `trial-sample-text.example.json`
- `trial-sample-audio.example.json`
- `trial-sample-image.example.json`
- `trial-sample-video.example.json`
- `trial-sample-tabular.example.json`
- `trial-sample-mixed-corpus.example.json`
  - Modality-specific examples required by `CBT-02`.

## Required Fields Per Sample

Every sample entry must include:

- `modality`
- `scenario`
- `source_owner`
- `sensitivity`
- `asset_list`
- `review_owner`
- `target_package_format`
- `expected_output_type`

## Validation

Use `scripts/validate_trial_manifest.py`:

```bash
python scripts/validate_trial_manifest.py \
  --manifest docs/current/status/baselines/trial-manifests/trial-sample-text.example.json \
  --output docs/current/status/baselines/trial-manifests/trial-sample-text.validation.json
```

Validation rules:

- Required fields must be non-empty.
- `samples` must be non-empty.
- `asset_list` must be a non-empty list.
- Unsupported sensitivity levels fail with actionable errors.
- Unsupported modality or target package format fails with actionable errors.
