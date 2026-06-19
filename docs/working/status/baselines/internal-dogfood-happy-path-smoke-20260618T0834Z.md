# Internal Dogfood Happy Path Smoke 20260618T0834Z

- Scope: internal dogfood only.
- Main construction doc: `docs/working/status/2026-06-18-internal-dogfood-launch-construction-plan.md`.
- Construction item: P1 `CLI/API happy path` expansion.
- Status: completed for the internal dogfood smoke surface.

## Capability Added

`scripts/internal_dogfood_smoke.py` provides a single runtime smoke command for the local API:

```powershell
python scripts\internal_dogfood_smoke.py --base-url http://127.0.0.1:8000
```

It checks:

- `GET /healthz`
- `GET /v1/templates/skill`
- `POST /v1/distill/text`
- `GET /v1/review/queue`
- pending review queue visibility when text distillation returns a pending review task

Dry-run plan:

```powershell
python scripts\internal_dogfood_smoke.py --dry-run
```

## Verification

- `python -B -m unittest tests.test_internal_dogfood_smoke`: pass.
- `python -B scripts\internal_dogfood_smoke.py --dry-run --base-url http://127.0.0.1:18000`: pass.
- `python -B -m unittest tests.test_api_review_queue tests.test_api_app tests.test_cli`: pass when run outside the read-only sandbox because these tests need temporary directories.
- `python -B scripts\doc_sync.py --output -`: pass, 13/13.
- `python scripts\ci.py --no-coverage --skip-tp-suite --keep-going`: fail, 786 tests ran with 9 failures and 1 error in existing `test_gl13_launch_evidence` cases.

## Environment Notes

- The combined API/review/CLI regression test fails in the read-only sandbox only because `tempfile` cannot find a writable temporary directory.
- The same test command passes in the normal local execution environment.
- The no-coverage full unittest discovery failure is not caused by `scripts/internal_dogfood_smoke.py`; the extracted failing tests are all existing GL13 real-trial launch evidence tests.

## Remaining Construction Items

- Docker smoke real run: not completed in this round.
- Real loop collection: not completed in this round.
- Review feedback calibration: not completed in this round.
- Platform preparation: not completed in this round.

External launch remains `HOLD` under the official launch gate because real trial loop volume and modality coverage are still missing.
