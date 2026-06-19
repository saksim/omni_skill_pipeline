# Operation Environments

This document maps current operating environments to the correct commands and
release claims.

## Local Developer

Purpose: edit, run unit tests, debug CLI/API behavior, and generate local
artifacts.

Use:

```bash
python -m pip install -r requirements-dev.txt
python -m omni_skill_pipeline.cli show-template
python scripts/ci.py --isolate-test-files --coverage-fail-under 50 --coverage-xml coverage.xml
```

Optional local artifact encryption:

```bash
export OMNI_ARTIFACT_ENCRYPTION_MODE=fernet
export OMNI_ARTIFACT_ENCRYPTION_KEY="<generated-key>"
```

See `docs/latest/operations/runbooks/artifact-encryption.md`.

## Internal Dogfood

Purpose: let internal operators run the current package and collect internal
API/CLI/review queue evidence.

Expected posture:

- `internal_dogfood_only=true`
- manual review remains the safe default for generated skills
- external launch gate may remain `HOLD`
- generated evidence belongs in `docs/working/status/baselines/`

Recommended checks:

```bash
python scripts/internal_launch_gate.py --output - --summary-output - --print-json
python -m uvicorn apps.api.main:app --reload
python scripts/internal_dogfood_smoke.py --base-url http://127.0.0.1:8000 --output - --summary-output -
```

## Release Packaging

Purpose: produce a verifiable GitHub Release artifact pack from `main` or a
`v*` tag.

Use:

```bash
python scripts/ci.py --isolate-test-files --coverage-fail-under 50 --coverage-xml coverage.xml
python -m pip wheel . --no-deps --wheel-dir dist
python scripts/release_artifacts.py --release-id "$RELEASE_ID" --output-dir "release-artifacts/$RELEASE_ID" --dist-dir dist --coverage-xml coverage.xml
python scripts/release_consumer_smoke.py --release-dir "release-artifacts/$RELEASE_ID" --expected-release-id "$RELEASE_ID"
```

See `docs/latest/operations/runbooks/github-release-workflow.md`.

## Infrastructure Validation

Purpose: Docker/Postgres/runtime deployment validation.

Current status:

- Docker real-run closure is not part of the archived completed
  `v0.2.3-internal.1` scope.
- Postgres production validation is not part of the archived completed
  `v0.2.3-internal.1` scope.
- K8s/Helm/Kubernetes operation is not a current completed release claim.

Use the stricter infrastructure runbooks only when the environment has those
services available:

```bash
bash scripts/linux_release.sh
```

See `docs/latest/operations/runbooks/docker-zero-to-release.md` and
`docs/latest/operations/runbooks/production-operations-baseline.md`.

## External Beta / GA

The external launch gate is still expected to remain `HOLD` until
launch-gate-eligible real business loops meet the documented threshold.

Do not present internal dogfood evidence as external Beta, GA, or SaaS evidence.
