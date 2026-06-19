# Internal Dogfood Fail Queue Update 20260618T0806Z

- Scope: internal dogfood only.
- Main construction doc: `docs/working/status/2026-06-18-internal-dogfood-launch-construction-plan.md`.
- Status meaning: this record closes the P1 fail-queue bookkeeping requirement by assigning each observed fail a state. It does not claim external launch readiness.

## Closed This Round

### TP full-suite Windows command length

- Construction item: P1 fail queue closure.
- Status: closed.
- Symptom: `scripts/tp_tests.py --all` previously built one very long `python -m unittest ...` command for 394 case IDs and could hit Windows `[WinError 206] The filename or extension is too long`.
- Change: `scripts/tp_tests.py` now chunks generated unittest commands by `--max-command-chars`, defaulting to `24000` characters on Windows.
- Regression coverage: `tests/test_tp_registry.py` now covers the chunked dry-run path.
- Verification:
  - `python -m unittest tests.test_tp_registry`: pass.
  - `python scripts\tp_tests.py TP-E1-01 TP-E1-02 TP-E1-03 --dry-run --python python --max-command-chars 360`: pass, emits multiple chunks.
  - `python scripts\tp_tests.py --all --dry-run --python python`: pass, emits 3 chunks.
  - `python scripts\ci.py --no-coverage --skip-full-suite --keep-going`: pass; TP registry execution ran in 3 chunks.

## Still Open

### Full CI coverage dependency

- Construction item: CI baseline / fail queue.
- Status: open, environment dependency.
- Current evidence: `python scripts\ci.py --coverage-fail-under 50 --coverage-xml coverage.xml --keep-going` still exits non-zero because the local Python environment has no `coverage` module.
- Current failure text: `No module named coverage`.
- Important distinction: TP registry full execution now passes in chunks; this is no longer blocked by command length.
- Next action: install or restore the project dev test dependency set containing `coverage`, then rerun full CI with the normal coverage gate.

## Remaining Construction Items

- Docker smoke real run: not completed in this round.
- CLI/API happy-path expansion: not completed in this round.
- Real loop collection: not completed in this round.
- Review feedback calibration: not completed in this round.
- Platform preparation: not completed in this round.

External launch remains `HOLD` under the official launch gate because real trial loop volume and modality coverage are still missing.
