# Real Trial Evidence Hygiene 20260618T0926Z

- Scope: real-trial loop collection evidence-chain hardening under the internal dogfood launch construction plan.
- Main construction doc: `docs/working/status/2026-06-18-internal-dogfood-launch-construction-plan.md`.
- Status meaning: this round makes GL13 evidence replay deterministic inside the `docs/working/` layer. It does not claim that real launch-gate loop volume has been collected.

## Closed This Round

### GL13 evidence path hygiene

- Construction item: harden the real-loop collection evidence chain so generated evidence does not carry stale `docs/current/`, repository-absolute, temporary, or Windows long-path-expanded paths.
- Status: closed.
- Symptom: the GL13 evidence pack could complete locally but still carried stale path evidence from older document layers or temp runs, and Windows parser-level aliases could be re-expanded into overlong output paths during downstream evidence generation.
- Change: `scripts/gl13_launch_evidence.py` now normalizes repository-internal evidence paths to repository-relative text, adds a `path_hygiene` summary to the launch evidence pack, and keeps Windows long-path aliases sticky once generated.
- Regression coverage: `tests/test_gl13_launch_evidence.py` now verifies repository path normalization, stale `docs/current/` detection, and Windows alias stickiness.

## Baseline Refresh

- Command: `python -B scripts\gl13_launch_evidence.py --no-run-doc-sync --max-evidence-age-hours 0`.
- Result: pass.
- Launch decision: `HOLD`.
- Collection status: `COLLECTION_INCOMPLETE`.
- Real eligible complete loops: `0/10`.
- Modalities covered: `0/4`.
- Failed check: `trial_loop_volume_and_modality_coverage`.
- Evidence hygiene: `old_docs_current_path_count=0`, `repo_root_absolute_path_count=0`, `external_absolute_path_count=0`.

## Verification

- `python -B -m unittest tests.test_gl13_launch_evidence.RealTrialLaunchEvidenceScriptTests.test_evidence_pack_path_hygiene_normalizes_repo_paths_and_flags_old_current`: pass.
- `python -B -m unittest tests.test_gl13_launch_evidence.RealTrialLaunchEvidenceScriptTests.test_pipeline_produces_ready_for_controlled_beta_with_real_loop`: pass.
- `python -B -c "from pathlib import Path; compile(Path('scripts/gl13_launch_evidence.py').read_text(encoding='utf-8-sig'), 'scripts/gl13_launch_evidence.py', 'exec'); print('syntax_ok')"`: pass.

## Still Open

- Docker smoke real run: not completed in this round; base image pull is still an external environment blocker.
- Real loop collection: not completed in this round; no new real submissions were added, so the launch gate still has `0/10` eligible complete real loops and `0/4` modalities.
- Review feedback calibration: not completed in this round.
- Platform preparation: not completed in this round.

External launch remains `HOLD`; this round improves evidence reliability for the internal toy/dogfood path without changing the official launch gate.
