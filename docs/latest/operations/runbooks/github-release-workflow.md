# GitHub Release Workflow

## Verdict

The repository has a lightweight release workflow for the current internal-to-main launch model.
It does not deploy to a production URL by itself. It turns a green `main` commit into a verifiable release candidate pack, and turns a `v*` tag into a GitHub Release.

Current published internal release: `v0.2.3-internal.1`.

## Entry Points

The workflow lives at:

```text
.github/workflows/release.yml
```

It runs on:

- push to `main`: build a release candidate artifact pack
- push of a `v*` tag: build the same pack and publish a GitHub Release
- manual `workflow_dispatch`: build a pack, optionally publish a GitHub Release when `publish_github_release=true` and `release_tag` is supplied

## Release Candidate Artifact

Every `main` push runs:

```bash
python scripts/ci.py --isolate-test-files --coverage-fail-under 50 --coverage-xml coverage.xml
python -m pip wheel . --no-deps --wheel-dir dist
python scripts/release_artifacts.py --release-id "$RELEASE_ID" --output-dir "release-artifacts/$RELEASE_ID" --dist-dir dist --coverage-xml coverage.xml
```

The uploaded artifact contains:

- `omni-skill-pipeline-source-<release_id>.tar.gz`
- Python wheel from `dist/`
- `coverage.xml`
- `release-manifest.json`
- `release-summary.md`
- `SHA256SUMS`

Use the candidate pack when you need a reproducible handoff before a formal tag.

## Formal GitHub Release

Before cutting a tag, add human-readable release notes when the release changes
operator or user behavior:

```text
docs/releases/notes/<release_tag>.md
```

When that file exists, `scripts/release_artifacts.py` includes it near the top of
the generated `release-summary.md`, before the machine metadata and artifact table.

Preferred path:

```bash
git fetch origin main
git checkout main
git pull --ff-only origin main
git tag <release_tag>
git push origin <release_tag>
```

Example:

```bash
git tag v0.2.3-internal.1
git push origin v0.2.3-internal.1
```

That tag triggers the release workflow and publishes a GitHub Release with the
generated artifact pack.

Manual path:

1. Open the `Release` workflow in GitHub Actions.
2. Run workflow from `main`.
3. Set `publish_github_release=true`.
4. Set `release_tag`, for example `v0.2.3-internal.1`.

The workflow creates the tag if it does not already exist, then runs:

```bash
gh release create "$RELEASE_TAG" release-artifacts/$RELEASE_ID/* --notes-file "release-artifacts/$RELEASE_ID/release-summary.md"
```

## Verification

Before treating a release as usable:

```bash
sha256sum -c SHA256SUMS
python -m pip install omni_skill_pipeline-*.whl
python -m omni_skill_pipeline.cli show-template
```

The automated consumer smoke is:

```bash
python scripts/release_consumer_smoke.py --release-dir . --expected-release-id <release_tag>
```

The `Release` workflow runs the same smoke against the generated artifact pack
before upload/publication.

For the latest published internal release:

```bash
python scripts/release_consumer_smoke.py --release-dir . --expected-release-id v0.2.3-internal.1
```

For container/API deployment, continue with:

```bash
bash scripts/linux_release.sh
```

The Docker/Postgres release switch remains the strict gate for full production
claims. The GitHub Release workflow is the stable packaging and publication
layer, not an external deployment proof.

## Rollback

If a GitHub Release is bad:

1. Mark it as pre-release or delete it from GitHub Releases.
2. Delete the tag only if operators have not consumed it.
3. Re-run the workflow from a fixed `main` commit with a new tag.

Do not overwrite an already consumed tag.
