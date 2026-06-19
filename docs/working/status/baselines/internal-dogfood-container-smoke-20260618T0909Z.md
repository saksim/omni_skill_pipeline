# Internal Dogfood Container Smoke 20260618T0909Z

- Scope: internal dogfood P1 Docker smoke.
- Main construction doc: `docs/working/status/2026-06-18-internal-dogfood-launch-construction-plan.md`.
- Status meaning: this record turns Docker smoke from an unclassified manual step into a structured, reproducible evidence chain. It does not close the P1 acceptance item because container `/healthz` was not reached.

## Closed This Round

### Container smoke structured evidence

- Construction item: P1 `Docker smoke 实跑`.
- Status: partially executed, environment-blocked.
- Change: `scripts/container_smoke.py` now emits structured JSON and Markdown summaries, performs Docker daemon preflight, supports `--docker-config-dir` for hosts with unreadable default Docker config, and classifies failures by stage.
- Regression coverage: `tests/test_container_smoke.py` now verifies dry-run report output and missing-Docker-CLI report semantics.

## Real Run Result

- Command:
  - `python -B scripts\container_smoke.py --image-tag omni-skill-pipeline:dogfood --port 18000 --timeout-seconds 60 --docker-config-dir .tmp_docker_config --output docs\working\status\baselines\internal-dogfood-container-smoke-report.json --summary-output docs\working\status\baselines\internal-dogfood-container-smoke-summary.md --print-json`
- Result: `FAIL`.
- Passed stages:
  - `docker_cli`
  - `docker_daemon`
- Failed stage:
  - `image_build`
- Failure category:
  - `docker_base_image_pull_failed`
- Cause: Docker daemon was reachable, but Docker build could not fetch metadata/token for `docker.io/library/python:3.11-slim`.
- Evidence:
  - `docs/working/status/baselines/internal-dogfood-container-smoke-report.json`
  - `docs/working/status/baselines/internal-dogfood-container-smoke-summary.md`

## Verification

- `python -B -m unittest tests.test_container_smoke`: pass.
- `python -B scripts\container_smoke.py --dry-run --image-tag omni-skill-pipeline:dogfood --port 18000 --output .tmp-container-smoke-dry-report.json --summary-output .tmp-container-smoke-dry-summary.md`: pass; temporary files removed after inspection.
- Real Docker smoke: fail at image build before container run; `/healthz` was not reached.

## Still Open

- Docker smoke real run: not completed because container healthz did not pass.
- Real loop collection: not completed.
- Review feedback calibration on real material: not completed.
- Platform preparation: not completed.

External launch remains `HOLD` under the official launch gate because required real trial loop volume and modality coverage are still missing.
