# Internal Dogfood GL13 Evidence Pack Repair 20260618T0854Z

- Scope: internal dogfood workflow fail closure, under the real-trial launch evidence workstream.
- Main construction doc: `docs/working/status/2026-06-18-internal-dogfood-launch-construction-plan.md`.
- Status meaning: this closes the GL13 evidence-pack crash that blocked full unittest discovery. It does not claim that the required real external launch loops have been collected.

## Closed This Round

### GL13 evidence pack signature drift

- Construction item: workflow fail closure for the real-loop evidence bridge.
- Status: closed.
- Symptom: `scripts/gl13_launch_evidence.py` completed GL12 through launch-readiness gate, then crashed while building the evidence pack because `main()` passed the final GL62 report keyword that `_build_evidence_pack()` did not accept.
- Change: `_build_evidence_pack()` now accepts the final GL62 closure-cadence-escalations report, exposes its report and summary paths in `source_artifacts`, and includes its status/counts/rows in `evidence_classification`.
- Regression coverage: `tests/test_gl13_launch_evidence.py` now has an AST guard that verifies the `_build_evidence_pack()` keyword-only signature stays in sync with the call site.

## Verification

- `python -B -m unittest tests.test_gl13_launch_evidence.RealTrialLaunchEvidenceScriptTests.test_evidence_pack_signature_matches_main_call_keywords`: pass.
- `python -B -m unittest tests.test_gl13_launch_evidence.RealTrialLaunchEvidenceScriptTests.test_pipeline_produces_ready_for_controlled_beta_with_real_loop`: pass.
- `python -B -m unittest tests.test_gl13_launch_evidence`: pass, 13 tests.
- `python -B -m unittest discover -s tests`: pass, 787 tests, 2 skipped.

## Still Open

- Docker smoke real run: not completed in this round.
- Real loop collection: not completed in this round; the evidence bridge is healthier, but no new real production loops were collected.
- Review feedback calibration: not completed in this round.
- Platform preparation: not completed in this round.

External launch remains `HOLD` under the official launch gate because required real trial loop volume and modality coverage are still missing.
