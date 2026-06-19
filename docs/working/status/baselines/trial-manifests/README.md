# Controlled Trial Sample Manifest Pack (CBT-02)

This directory defines controlled-trial sample manifest contracts.

## Files

- `trial-sample-manifest.template.json`
- `trial-sample-text.example.json`
- `trial-sample-audio.example.json`
- `trial-sample-image.example.json`
- `trial-sample-video.example.json`
- `trial-sample-tabular.example.json`
- `trial-sample-mixed-corpus.example.json`
- `trial-sample-launch-expansion-fixture.example.json`

## GL-12 Real Loop Collection Note

`trial-sample-launch-expansion-fixture.example.json` is fixture-only evidence expansion and must not be counted as launch-gate-eligible real loops.
For GL-12 real-loop evidence tracking, use:

- `scripts/gl12_collect_loops.py`
- `docs/working/status/baselines/real-trial-loop-collection/real-trial-loop-metrics-manifest.template.json`

## Validation

```bash
python scripts/validate_manifest.py \
  --manifest docs/working/status/baselines/trial-manifests/trial-sample-text.example.json \
  --output docs/working/status/baselines/trial-manifests/trial-sample-text.validation.json
```
