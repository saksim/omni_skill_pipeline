# Testing

## 鍒よ瘝

杩欎釜浠撳綋鍓嶈蛋鐨勬槸 `unittest` 浣撶郴锛屼笉鏄?`pytest` 浣撶郴锛涙祴璇曞垽鏂鎸夌幇鏈夐摼璺獙灏革紝涓嶈鎷块敊鍒戝叿銆?
## 鏈湴鐜瀵归綈

PowerShell:

```powershell
py -3.11 -m venv .venv
. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

POSIX:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

## 鍏ㄩ噺鍥炲綊

```bash
python scripts/run_ci.py
```

璇ュ叆鍙ｄ細缁熶竴鎵ц锛?
- `python -m coverage run --parallel-mode -m unittest discover -s tests -p 'test_*.py'`
- `python scripts/run_tp_tests.py --all --python <current-python>`
- `python -m coverage combine`
- `python -m coverage report --show-missing --fail-under <threshold>`
- `python -m coverage xml -o coverage.xml`

榛樿 coverage fail-under 涓?`50`锛屽彲閫氳繃鍙傛暟瑕嗙洊銆?
绀轰緥锛氭彁楂橀槇鍊煎埌 `65`

```bash
python scripts/run_ci.py --coverage-fail-under 65
```

绀轰緥锛氫粎鍦ㄦ湰鍦板揩閫熼獙閫昏緫锛屼复鏃跺叧闂?coverage

```bash
python scripts/run_ci.py --no-coverage
```

## 瀹瑰櫒鐑熸祴鑴氭湰

瀹瑰櫒鍩虹嚎鐑熸祴锛堟瀯寤洪暅鍍?+ 鍚姩瀹瑰櫒 + 杞 `/healthz`锛夛細

```bash
python scripts/run_container_smoke.py --image-tag omni-skill-pipeline:local --port 18000
```

鍙湅鎵ц璁″垝锛屼笉鐪熸璋冪敤 Docker锛?
```bash
python scripts/run_container_smoke.py --dry-run
```

Linux 缁熶竴楠屾祴鏃跺缓璁洿鎺ヤ娇鐢ㄨ鑴氭湰锛屼綔涓?`LC-L1-18` 鐨勫鍣ㄥ洖褰掑叆鍙ｃ€?
## Dual-Write Benchmark Harness

`LC-L2-33` 寮曞叆 dual-write 鍩哄噯鑴氭湰锛?
```bash
python scripts/benchmark_dual_write.py --iterations 20 --skip-postgres
python scripts/benchmark_dual_write.py --iterations 20 --postgres-dsn "$OMNI_TEST_POSTGRES_DSN"
```

- 绗竴涓懡浠ゅ彧娴?file repository baseline銆?- 绗簩涓懡浠ゆ祴 file + Postgres dual-write 鏃跺欢銆?- 榛樿鎶ュ憡钀界洏锛歚docs/current/status/baselines/e8-dual-write-benchmark-report.json`銆?
## 瀹氬悜鎵ц

鏌ョ湅褰撳墠宸叉槧灏?Task Package:

```bash
python scripts/run_tp_tests.py --list
```

鎵ц鍗曚釜宸ュ崟:

```bash
python scripts/run_tp_tests.py TP-E6-02 --python python
```

鎵ц澶氫釜宸ュ崟:

```bash
python scripts/run_tp_tests.py TP-E1-01 TP-E1-02 TP-E1-03 TP-E2-01 TP-E2-02 TP-E2-03 TP-E3-01 TP-E3-02 TP-E3-03 TP-E4-01 TP-E4-02 TP-E4-03 TP-E4-04 TP-E4-05 TP-E5-01 TP-E5-02 TP-E5-03 TP-E5-04 TP-E6-01 TP-E6-02 TP-E6-03 TP-E6-04 TP-E7-01 TP-E7-02 TP-E7-03 TP-E7-04 TP-E8-01 TP-E8-02 TP-E8-03 TP-E8-04 TP-E9-01 TP-E9-02 TP-E9-03 TP-E10-01 TP-E10-02 TP-E10-03 TP-E11-01 TP-E11-02 TP-E11-03 TP-E11-04 TP-E12-01 TP-E12-02 TP-E12-03 TP-E12-04 TP-E13-01 TP-E13-02 TP-E13-03 TP-E13-04 TP-E13-05 TP-E13-06 TP-E13-07 TP-E13-08 TP-E13-09 TP-E13-10 TP-E13-11 TP-E13-12 TP-E13-13 TP-E13-14 TP-E13-15 TP-E13-16 TP-E13-17 TP-E13-18 TP-E13-19 TP-E13-20 TP-E13-21 TP-E13-22 TP-E13-23 TP-E13-24 TP-E13-25 TP-E13-26 TP-E13-27 TP-E13-28 TP-E13-29 TP-E13-30 TP-E13-31 TP-E13-32 TP-E13-33 TP-E13-34 TP-E13-35 TP-E13-36 TP-E13-37 TP-E13-38 --python python3
```

## 褰撳墠瑕嗙洊閲嶇偣

- `tests/test_mvp.py`: 瑕嗙洊 text / audio / image / video / tabular 涓昏矾寰?- `tests/test_v2_schema_and_corpus.py`: 瑕嗙洊 corpus 缁勮銆乸ublication銆乹uality銆乺eview artifacts
- `tests/test_quality_scoring.py`: 瑕嗙洊璐ㄩ噺璇勫垎
- `tests/test_review_policy.py`: 瑕嗙洊 review threshold 涓?reason codes
- `tests/test_dual_write_repository.py`: 瑕嗙洊 dual-write 涓?浠庝粨鍌ㄨ涓轰笌澶辫触淇濇姢
- `tests/test_benchmark_dual_write.py`: 瑕嗙洊 dual-write benchmark 鑴氭湰鐑熸祴
- `tests/test_similarity_retrieval.py`: 瑕嗙洊妫€绱㈡娊璞°€乮nmemory baseline 鎺掑簭銆乥ackend 閫夊瀷鍗犱綅琛屼负
- `tests/test_lifecycle_decision_engine.py`: 瑕嗙洊 lifecycle `new/revise/merge/supersede/reject` 鍐崇瓥鍒嗘祦
- `tests/test_publication_builder.py`: 瑕嗙洊 checklist/decision_tree 杈撳嚭涓庢棤 decision 鍦烘櫙 fallback
- `tests/test_publication_orchestrator_split.py`: 瑕嗙洊 goal_type 椹卞姩鐨?publication type 閫夋嫨
- `tests/test_api_app.py`: 瑕嗙洊 distill API 杈撳叆杞崲銆侀敊璇槧灏勪笌 TP-E10-02 鐨?V2 杈撳嚭濂戠害瀛楁
- `tests/test_worker.py`: 瑕嗙洊 TP-E10-03 worker 鏂颁换鍔＄被鍨嬶紙review_queue/rebuild_publication/revise_skill锛?- `tests/test_transformers_regression.py`: 瑕嗙洊 TP-E11-01 妯″瀷/杞崲鍣ㄥ垎鏀洖褰掞紙skill_type銆乪vidence 鑱氬悎銆乴egacy atom bridge锛?- `tests/test_doc_sync_check_script.py`: 瑕嗙洊 TP-E13-01 / TP-E13-02 / TP-E13-03 鏂囨。鍚屾妫€鏌ヨ剼鏈紙婧愮爜琛ㄩ潰 + 杩佺Щ鎸囧崡 + 鍙戝竷鍒囨崲鏍囧噯 + LC-L1-19 Beta runbook 濂戠害锛?- `tests/test_linux_validation_suite_script.py`: 瑕嗙洊 TP-E13-04 Linux 缁熶竴楠屽案缂栨帓鑴氭湰锛堥樁娈电瓫閫夈€佸懡浠ゆ墦鍖呫€乨ry-run 璁″垝钀界洏銆乧ontainer smoke / postgres_soak / postgres_ga / worker_ga / review_queue_ga / provider_ga / calibration_ga / roadmap_extension 鍙傛暟閫忎紶锛?- `tests/test_postgres_soak_validation_script.py`: 瑕嗙洊 TP-E13-05 Postgres 闀跨ǔ楠屽案鑴氭湰锛圱P 鍥炲綊缂栨帓銆乥enchmark 鍙傛暟銆乨sn fail-fast锛?- `tests/test_worker_ga_validation_script.py`: 瑕嗙洊 TP-E13-06 worker GA 楠岃瘉鑴氭湰锛堥樁娈电瓫閫夈€乨ry-run 璁″垝钀界洏锛?- `tests/test_provider_ga_validation_script.py`: 瑕嗙洊 TP-E13-07 provider GA 楠岃瘉鑴氭湰锛坮etry/circuit-breaker/failure-budget/audit 璁″垝缂栨帓锛?- `tests/test_review_queue_ga_validation_script.py`: 瑕嗙洊 TP-E13-08 review queue GA 楠岃瘉鑴氭湰锛坮epository/service/api/feedback 闃舵缂栨帓涓庣瓫閫夛級
- `tests/test_calibration_ga_validation_script.py`: 瑕嗙洊 TP-E13-09 calibration GA 楠岃瘉鑴氭湰锛堥槇鍊煎绾︺€佽皟鍙傛姤鍛娿€乵anifest/report 鍙傛暟閫忎紶锛?- `tests/test_postgres_ga_validation_script.py`: 瑕嗙洊 TP-E13-10 Postgres GA 楠岃瘉鑴氭湰锛坮epository/dual-write/benchmark 闃舵缂栨帓銆乨sn fail-fast銆乥enchmark 鍙傛暟閫忎紶锛?- `tests/test_roadmap_extension_validation_script.py`: 瑕嗙洊 TP-E13-11 roadmap extension 楠岃瘉鑴氭湰锛圠C-R-34~37 鐨?retrieval/lifecycle/publication/review queue surface 闃舵缂栨帓涓庣瓫閫夛級
- `tests/test_release_gate_validation_script.py`: 瑕嗙洊 TP-E13-12 鍙戝竷闂ㄧ鑱氬悎鑴氭湰锛坆eta/ga/roadmap 闃舵绛涢€変笌 coverage/container/postgres/calibration 鍙傛暟閫忎紶锛?- `tests/test_release_switch_validation_script.py`: 瑕嗙洊 TP-E13-13 / TP-E13-14 / TP-E13-15 / TP-E13-16 / TP-E13-17 / TP-E13-18 / TP-E13-19 / TP-E13-20 / TP-E13-21 / TP-E13-22 / TP-E13-23 / TP-E13-24 / TP-E13-25 / TP-E13-26 / TP-E13-27 / TP-E13-28 / TP-E13-29 / TP-E13-30 / TP-E13-31 / TP-E13-32 / TP-E13-33 / TP-E13-34 / TP-E13-35 / TP-E13-36 / TP-E13-37 鍙戝竷鍒囨崲鍒ゅ畾鑴氭湰锛坮elease-gate/TP/doc-sync 缂栨帓銆乨ecision-only GO/HOLD銆佽瘉鎹寘鈥滃畬鏁存€?+ 鍙墽琛屽懡浠よ鍒掆€濋棬绂併€乪vidence freshness 鏃舵晥闂ㄧ銆乫uture timestamp skew 闂ㄧ銆乧ohort skew 闂ㄧ涓巖elease-gate output binding 闂ㄧ涓?stage contract 闂ㄧ涓?script-position 闂ㄧ涓?option override 闂ㄧ涓?relaxed-flag 闂ㄧ + dry-run 闂ㄧ + script-anchor 闂ㄧ + python-binding 闂ㄧ + coverage-floor 闂ㄧ + python-optimization 闂ㄧ + python-option-optimization 闂ㄧ + python-optimize-env 闂ㄧ + python-option-inline-exec 闂ㄧ + python-path-env 闂ㄧ + python-home-env 闂ㄧ + python-user-base-env 闂ㄧ + python-breakpoint-env 闂ㄧ + python-startup-env 闂ㄧ + python-inspect-env 闂ㄧ锛?- `tests/test_tp_registry.py`: 瑕嗙洊 TP 娉ㄥ唽琛ㄤ笌 `skill-distillation-v2-work-orders.md` 鐨勫弻鍚戝畬鏁存€у榻愶紙婕忔槧灏?+ 骞界伒鏄犲皠锛?
## 褰撳墠缂哄彛

- FastAPI/ASGI API 鑷姩鍖栨祴璇曞凡瑕嗙洊鏍稿績濂戠害锛涗粛缂虹湡瀹?provider 鏁呴殰娉ㄥ叆涓庤礋杞藉満鏅?- coverage fail-under 浠嶆槸淇濆畧闃堝€硷紙`50`锛夛紝鍚庣画搴旈殢璐ㄩ噺鍩虹嚎鎻愬崌
- 灏氭棤鐢熶骇绾ц礋杞藉帇娴嬶紙褰撳墠浠呮湁 dual-write benchmark smoke harness锛?- 鐪熷疄 provider failure-mode 瑕嗙洊浠嶅亸钖?
## 缁存姢瑙勫垯

姣忔鏂板 `TP-*` 宸ュ崟鏃讹紝鑷冲皯鍚屾瀹屾垚涓変欢浜嬶細

1. 鍦?`tests/` 钀芥祴璇?case
2. 鍦?`scripts/run_tp_tests.py` 鐨?`TP_TEST_CASES` 涓櫥璁版槧灏?3. 鍦ㄦ湰鏂囦欢鏇存柊瑕嗙洊鑼冨洿涓庢柊澧炲伐鍗曡鏄庯紙骞剁‘淇?`tests/test_tp_registry.py` 瀵归綈 work-orders锛?
## LC-R-37 Additions

- Added `TP-E9-03` for review queue operations surface.
- Added repository-level transition coverage in `tests/test_review_queue_repository.py`.
- Added service integration coverage in `tests/test_review_queue_integration.py`.
- Added API contract coverage in `tests/test_api_review_queue.py` for list/claim/close.
- Note: the previous API coverage gap statement is superseded for review queue scope; contract tests now exist in `tests/test_api_review_queue.py`.

## TP-E12-01 Additions

- Added structured trace fallback and chain fields in `src/omni_skill_pipeline/service.py`.
- Added per-job request/trace context propagation in `src/omni_skill_pipeline/worker.py`.
- Added `tests/test_trace_observability_tp_e12.py` for service/worker trace-chain coverage.
- Added `TP-E12-01` mapping in `scripts/run_tp_tests.py`.
- Batch example: `python scripts/run_tp_tests.py TP-E11-02 TP-E11-03 TP-E11-04 TP-E12-01 --python python`.

## TP-E12-02 Additions

- Added provider call audit counters/snapshots in `src/omni_skill_pipeline/providers/openai_provider.py`.
- Added adapter-level provider call metadata in `src/omni_skill_pipeline/adapters/audio.py`, `src/omni_skill_pipeline/adapters/image.py`, and `src/omni_skill_pipeline/adapters/video.py`.
- Added corpus-level provider footprint aggregation in `src/omni_skill_pipeline/service.py`.
- Added `tests/test_provider_audit_tp_e12.py` for provider audit and corpus footprint assertions.
- Added `TP-E12-02` mapping in `scripts/run_tp_tests.py`.
- Linux batch example: `python scripts/run_tp_tests.py TP-E12-01 TP-E12-02 --python python3`.

## TP-E12-03 Additions

- Added recursive redaction helpers in `src/omni_skill_pipeline/redaction.py` to sanitize sensitive keys and inline bearer/token-like values.
- Added request/adapter metadata sanitization in `src/omni_skill_pipeline/service.py` before persistence.
- Added repository-side defense-in-depth redaction in `src/omni_skill_pipeline/repository.py` before writing artifact files.
- Added `tests/test_security_redaction_tp_e12.py` for service payload redaction and file artifact persistence redaction assertions.
- Added `TP-E12-03` mapping in `scripts/run_tp_tests.py`.
- Linux batch example: `python scripts/run_tp_tests.py TP-E12-01 TP-E12-02 TP-E12-03 --python python3`.

## TP-E12-04 Additions

- Added explicit scratch cleanup status handling in `src/omni_skill_pipeline/adapters/video.py`; cleanup failures now record deferred recovery entries for prune jobs.
- Added intermediate keyframe candidate cleanup in `src/omni_skill_pipeline/providers/media.py` so only selected frames remain during processing.
- Added `tests/test_tmp_artifact_governance_tp_e12.py` to cover success cleanup and deferred cleanup-recovery behavior.
- Added `tests/test_media_provider.py::MediaProcessorTests.test_cleanup_unselected_frames_keeps_selected_only` for intermediate-frame lifecycle cleanup.
- Added `TP-E12-04` mapping in `scripts/run_tp_tests.py`.
- Linux batch example: `python scripts/run_tp_tests.py TP-E12-01 TP-E12-02 TP-E12-03 TP-E12-04 --python python3`.

## TP-E13-01 Additions

- Added `scripts/run_doc_sync_check.py` to verify README/CLI/API/worker/testing docs stay aligned with source surfaces.
- Extended `scripts/run_doc_sync_check.py` with `api_ops_contract_completeness` check for `docs/current/operations/api.md` (`LC-L1-16` auth/rate-limit/error/health contract).
- Extended `scripts/run_doc_sync_check.py` with `launch_beta_runbook_completeness` check for `docs/current/operations/runbooks/launch-beta.md` (`LC-L1-19` checklist contract).
- Added `tests/test_doc_sync_check_script.py` coverage for API ops-contract incomplete fail-path.
- Added `tests/test_doc_sync_check_script.py` coverage for launch-beta incomplete-contract fail-path.
- Extended `tests/test_tp_registry.py` with reverse-parity assertion so undocumented TP IDs in `run_tp_tests --list` fail fast.
- Added `TP-E13-01` mapping in `scripts/run_tp_tests.py`, including the TP registry parity check testcase.
- Linux doc sync example: `python scripts/run_doc_sync_check.py --output docs/current/status/baselines/e13-doc-sync-check-report.json`.
- Linux batch example: `python scripts/run_tp_tests.py TP-E12-01 TP-E12-02 TP-E12-03 TP-E12-04 TP-E13-01 --python python3`.

## TP-E13-02 Additions

- Added `docs/current/architecture/v1-to-v2-migration-guide.md` with migration steps, rollback strategy, and risk register.
- Added `docs/current/operations/v1-to-v2-migration-runbook.md` with Linux execution and rollback sequence.
- Extended `scripts/run_doc_sync_check.py` with `migration_guide_completeness` check and migration doc path args.
- Extended `tests/test_doc_sync_check_script.py` with incomplete-migration-doc fail-path assertions.
- Added `TP-E13-02` mapping in `scripts/run_tp_tests.py`.
- Linux batch example: `python scripts/run_tp_tests.py TP-E13-01 TP-E13-02 --python python3`.

## TP-E13-03 Additions

- Added `docs/current/status/v2-release-switch-standard.md` with hard-gate rules and cutover/rollback criteria.
- Added `docs/history/status/2026-04-26-v2-release-switch-standard.md` as the first decision snapshot baseline.
- Extended `scripts/run_doc_sync_check.py` with `release_switch_standard_completeness` check and release status doc path args.
- Extended `tests/test_doc_sync_check_script.py` with release-switch incomplete-doc fail-path assertions.
- Added `TP-E13-03` mapping in `scripts/run_tp_tests.py`.
- Linux batch example: `python scripts/run_tp_tests.py TP-E13-01 TP-E13-02 TP-E13-03 --python python3`.

## TP-E13-04 Additions

- Added `scripts/run_linux_validation_suite.py` to orchestrate Linux unified validation stages (`ci`, `container_smoke`, `doc_sync`, `quality_regression`, `perf_cost_baseline`, `postgres_soak`).
- Added `tests/test_linux_validation_suite_script.py` for dry-run plan output, stage-filter behavior, and `container_smoke` option forwarding coverage.
- Added `TP-E13-04` mapping in `scripts/run_tp_tests.py`.
- Linux dry-run example: `python scripts/run_linux_validation_suite.py --python python3 --dry-run --output docs/current/status/baselines/e13-linux-validation-suite-plan.json`.
- Linux container-only dry-run example: `python scripts/run_linux_validation_suite.py --python python3 --stages container_smoke --container-image-tag omni-skill-pipeline:beta --dry-run --output -`.
- Linux execution example: `python scripts/run_linux_validation_suite.py --python python3`.

## TP-E13-05 Additions

- Added `scripts/run_postgres_soak_validation.py` to orchestrate Postgres soak command pack (`tp_postgres`, `review_queue`, `dual_write_benchmark`).
- Extended `scripts/run_linux_validation_suite.py` with `postgres_soak` stage so Linux full-pack can include Postgres long-run validation.
- Added `tests/test_postgres_soak_validation_script.py` for dry-run plan output, stage filtering, benchmark args, and DSN fail-fast behavior.
- Updated `tests/test_linux_validation_suite_script.py` for the new `postgres_soak` stage in default command pack and postgres option forwarding coverage.
- Added `TP-E13-05` mapping in `scripts/run_tp_tests.py`.
- Linux dry-run example: `python scripts/run_postgres_soak_validation.py --python python3 --dry-run --output docs/current/status/baselines/e13-postgres-soak-plan.json`.
- Linux execution example: `python scripts/run_postgres_soak_validation.py --python python3 --postgres-dsn "$OMNI_TEST_POSTGRES_DSN"`.

## TP-E13-06 Additions

- Added `scripts/run_worker_ga_validation.py` to orchestrate worker GA-hardening command pack (`worker_corpus`, `worker_retry`, `worker_idempotency`, `worker_claim_lock`, `worker_task_types`).
- Added `tests/test_worker_ga_validation_script.py` for dry-run plan output and stage-filter behavior.
- Extended `scripts/run_linux_validation_suite.py` with `worker_ga` stage so Linux full-pack can include worker GA hardening validation.
- Updated `tests/test_linux_validation_suite_script.py` with worker_ga stage forwarding coverage.
- Added `TP-E13-06` mapping in `scripts/run_tp_tests.py`.
- Linux dry-run example: `python scripts/run_worker_ga_validation.py --python python3 --dry-run --output docs/current/status/baselines/e13-worker-ga-validation-plan.json`.
- Linux stage-only dry-run example: `python scripts/run_worker_ga_validation.py --python python3 --stages worker_retry worker_claim_lock --dry-run --output -`.

## TP-E13-07 Additions

- Added `scripts/run_provider_ga_validation.py` to orchestrate provider GA-hardening command pack (`provider_retry`, `provider_circuit_breaker`, `provider_failure_budget`, `provider_config_contract`, `provider_call_audit`, `provider_footprint`).
- Added `tests/test_provider_ga_validation_script.py` for default dry-run plan output and stage-filter behavior.
- Extended `scripts/run_linux_validation_suite.py` with `provider_ga` stage so Linux full-pack can include provider GA hardening validation.
- Updated `tests/test_linux_validation_suite_script.py` with provider_ga stage forwarding coverage.
- Added `TP-E13-07` mapping in `scripts/run_tp_tests.py`.
- Linux dry-run example: `python scripts/run_provider_ga_validation.py --python python3 --dry-run --output docs/current/status/baselines/e13-provider-ga-validation-plan.json`.
- Linux stage-only dry-run example: `python scripts/run_provider_ga_validation.py --python python3 --stages provider_circuit_breaker provider_call_audit --dry-run --output -`.

## TP-E13-08 Additions

- Added `scripts/run_review_queue_ga_validation.py` to orchestrate review queue GA-hardening command pack (`review_queue_repository`, `review_queue_service`, `review_queue_api`, `review_feedback`, `review_feedback_consumer`).
- Added `tests/test_review_queue_ga_validation_script.py` for default dry-run plan output and stage-filter behavior.
- Extended `scripts/run_linux_validation_suite.py` with `review_queue_ga` stage so Linux full-pack can include review queue hardening validation.
- Updated `tests/test_linux_validation_suite_script.py` with review_queue_ga stage forwarding coverage.
- Added `TP-E13-08` mapping in `scripts/run_tp_tests.py`.
- Linux dry-run example: `python scripts/run_review_queue_ga_validation.py --python python3 --dry-run --output docs/current/status/baselines/e13-review-queue-ga-validation-plan.json`.
- Linux stage-only dry-run example: `python scripts/run_review_queue_ga_validation.py --python python3 --stages review_queue_api review_feedback_consumer --dry-run --output -`.

## TP-E13-09 Additions

- Added `scripts/run_calibration_ga_validation.py` to orchestrate calibration GA-hardening command pack (`calibration_contract`, `review_policy_contract`, `calibration_report`).
- Added `tests/test_calibration_ga_validation_script.py` for default dry-run plan output and calibration option-forwarding behavior.
- Extended `scripts/run_linux_validation_suite.py` with `calibration_ga` stage so Linux full-pack can include LC-L2-31 threshold calibration validation.
- Updated `tests/test_linux_validation_suite_script.py` with calibration_ga stage forwarding coverage.
- Added `TP-E13-09` mapping in `scripts/run_tp_tests.py`.
- Linux dry-run example: `python scripts/run_calibration_ga_validation.py --python python3 --dry-run --output docs/current/status/baselines/e13-calibration-ga-validation-plan.json`.
- Linux stage-only dry-run example: `python scripts/run_calibration_ga_validation.py --python python3 --stages calibration_report --manifest docs/current/status/baselines/e7-calibration-manifest.json --calibration-report-output docs/current/status/baselines/e7-calibration-report.json --margin 0.03 --dry-run --output -`.

## TP-E13-10 Additions

- Added `scripts/run_postgres_ga_validation.py` to orchestrate Postgres GA-hardening command pack (`postgres_repository_contract`, `postgres_repository_integration`, `dual_write_contract`, `dual_write_integration`, `dual_write_benchmark`).
- Added `tests/test_postgres_ga_validation_script.py` for default dry-run plan output, stage filtering, benchmark option-forwarding, and DSN fail-fast behavior.
- Extended `scripts/run_linux_validation_suite.py` with `postgres_ga` stage and forwarding for `postgres-dsn`, `postgres-ga-iterations`, `postgres-ga-output`, and benchmark output options.
- Updated `tests/test_linux_validation_suite_script.py` with postgres_ga stage forwarding coverage.
- Added `TP-E13-10` mapping in `scripts/run_tp_tests.py`.
- Linux dry-run example: `python scripts/run_postgres_ga_validation.py --python python3 --dry-run --output docs/current/status/baselines/e13-postgres-ga-validation-plan.json`.
- Linux stage-only dry-run example: `python scripts/run_postgres_ga_validation.py --python python3 --stages dual_write_contract dual_write_benchmark --postgres-dsn "$OMNI_TEST_POSTGRES_DSN" --benchmark-iterations 120 --benchmark-output docs/current/status/baselines/e13-postgres-ga-benchmark-report.json --dry-run --output -`.

## TP-E13-11 Additions

- Added `scripts/run_roadmap_extension_validation.py` to orchestrate LC-R-34~37 command pack (`retrieval_layer`, `lifecycle_engine`, `publication_expansion`, `review_queue_surface`).
- Added `tests/test_roadmap_extension_validation_script.py` for default dry-run plan output and stage-filter behavior.
- Extended `scripts/run_linux_validation_suite.py` with `roadmap_extension` stage and forwarding for `--roadmap-extension-output`.
- Updated `tests/test_linux_validation_suite_script.py` with roadmap_extension stage forwarding coverage.
- Added `TP-E13-11` mapping in `scripts/run_tp_tests.py`.
- Linux dry-run example: `python scripts/run_roadmap_extension_validation.py --python python3 --dry-run --output docs/current/status/baselines/e13-roadmap-extension-validation-plan.json`.
- Linux stage-only dry-run example: `python scripts/run_roadmap_extension_validation.py --python python3 --stages retrieval_layer review_queue_surface --dry-run --output -`.

## TP-E13-12 Additions

- Added `scripts/run_release_gate_validation.py` to orchestrate release gate command packs (`beta_gate`, `ga_gate`, `roadmap_gate`) by delegating to `scripts/run_linux_validation_suite.py`.
- Added `tests/test_release_gate_validation_script.py` for default dry-run plan output, beta-only stage forwarding, and ga-stage postgres/calibration option forwarding.
- Added `TP-E13-12` mapping in `scripts/run_tp_tests.py` and synced `tests/test_tp_registry.py` known-work-order assertions.
- Linux dry-run example: `python scripts/run_release_gate_validation.py --python python3 --dry-run --output docs/current/status/baselines/e13-release-gate-validation-plan.json`.
- Linux beta-only dry-run example: `python scripts/run_release_gate_validation.py --python python3 --stages beta_gate --coverage-fail-under 65 --container-image-tag omni-skill-pipeline:beta --dry-run --output -`.

## TP-E13-13 Additions

- Added `scripts/run_release_switch_validation.py` to orchestrate release-gate + TP contract + doc-sync command packs and emit `GO/HOLD` decision report from evidence files.
- Added `tests/test_release_switch_validation_script.py` for dry-run plan output, release-gate option forwarding, `--decision-only` GO coverage, and HOLD exit-code contract (`1` by default, `0` with `--allow-hold`).
- Added `TP-E13-13` mapping in `scripts/run_tp_tests.py` and synced work-order registry checks via `tests/test_tp_registry.py`.
- Linux dry-run example: `python scripts/run_release_switch_validation.py --python python3 --dry-run --output docs/current/status/baselines/e13-release-switch-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.
- Linux decision-only example: `python scripts/run_release_switch_validation.py --decision-only --doc-sync-report docs/current/status/baselines/e13-doc-sync-check-report.json --quality-report docs/current/status/baselines/e11-quality-regression-report.json --perf-report docs/current/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/current/status/baselines/e13-postgres-soak-benchmark-report.json --ga-suite-output docs/current/status/baselines/e13-release-gate-ga-suite-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.
- Linux decision-only HOLD-allow example: `python scripts/run_release_switch_validation.py --decision-only --allow-hold --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-14 Additions

- Extended `scripts/run_release_switch_validation.py` decision evaluation to require full release-gate evidence packs (`release_gate_output` + `beta/ga/roadmap` suite plans) before emitting `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_pack_evidence_missing` to assert missing gate-pack evidence forces `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_pack_stage_commands_missing` to assert non-executable stage packs (missing `command`) force `HOLD`.
- Added `TP-E13-14` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only full-evidence example: `python scripts/run_release_switch_validation.py --decision-only --doc-sync-report docs/current/status/baselines/e13-doc-sync-check-report.json --quality-report docs/current/status/baselines/e11-quality-regression-report.json --perf-report docs/current/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/current/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/current/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/current/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/current/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/current/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-15 Additions

- Extended `scripts/run_release_switch_validation.py` with evidence freshness gate: `--max-evidence-age-hours` (default `24`) now guards decision evidence files against stale reuse.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_evidence_files_are_stale` to assert stale evidence forces `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_evidence_freshness_gate` to assert `--max-evidence-age-hours 0` disables freshness gate for recovery scenarios.
- Added `TP-E13-15` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only with freshness gate example: `python scripts/run_release_switch_validation.py --decision-only --max-evidence-age-hours 24 --doc-sync-report docs/current/status/baselines/e13-doc-sync-check-report.json --quality-report docs/current/status/baselines/e11-quality-regression-report.json --perf-report docs/current/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/current/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/current/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/current/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/current/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/current/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-16 Additions

- Extended `scripts/run_release_switch_validation.py` with future-skew gate: `--max-evidence-future-skew-hours` (default `0.25`) now guards decision evidence against future timestamp drift.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_evidence_files_are_future_skewed` to assert future-skewed evidence forces `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_future_skew_gate` to assert `--max-evidence-future-skew-hours 0` disables future-skew gate for recovery scenarios.
- Added `TP-E13-16` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only with future-skew gate example: `python scripts/run_release_switch_validation.py --decision-only --max-evidence-future-skew-hours 0.25 --doc-sync-report docs/current/status/baselines/e13-doc-sync-check-report.json --quality-report docs/current/status/baselines/e11-quality-regression-report.json --perf-report docs/current/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/current/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/current/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/current/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/current/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/current/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-17 Additions

- Extended `scripts/run_release_switch_validation.py` with cohort-skew gate: `--max-evidence-cohort-skew-hours` (default `12`) now guards decision evidence against mixed-batch timestamp spread.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_evidence_cohort_age_spread_is_too_large` to assert oversized evidence age spread forces `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_evidence_cohort_skew_gate` to assert `--max-evidence-cohort-skew-hours 0` disables cohort-skew gate for recovery scenarios.
- Added `TP-E13-17` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only with cohort-skew gate example: `python scripts/run_release_switch_validation.py --decision-only --max-evidence-cohort-skew-hours 12 --doc-sync-report docs/current/status/baselines/e13-doc-sync-check-report.json --quality-report docs/current/status/baselines/e11-quality-regression-report.json --perf-report docs/current/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/current/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/current/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/current/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/current/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/current/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-18 Additions

- Extended `scripts/run_release_switch_validation.py` with release-gate output-binding gate: release-gate stage `--output` paths must match `--beta-suite-output/--ga-suite-output/--roadmap-suite-output` evidence inputs before `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_outputs_do_not_match_evidence_paths` to assert path-binding drift forces `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_output_binding_gate` to assert `--skip-release-gate-output-binding-check` disables the binding gate for emergency recovery.
- Added `TP-E13-18` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only with binding gate example: `python scripts/run_release_switch_validation.py --decision-only --doc-sync-report docs/current/status/baselines/e13-doc-sync-check-report.json --quality-report docs/current/status/baselines/e11-quality-regression-report.json --perf-report docs/current/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/current/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/current/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/current/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/current/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/current/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.


## TP-E13-19 Additions

- Extended `scripts/run_release_switch_validation.py` with release-gate stage-contract gate: decision now validates each release-gate stage command targets `scripts/run_linux_validation_suite.py` and keeps expected `--stages` packs before `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_contract_mismatches` to assert stage-contract drift forces `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_stage_contract_gate` to assert `--skip-release-gate-stage-contract-check` disables the stage-contract gate for emergency recovery.
- Added `TP-E13-19` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only with stage-contract gate example: `python scripts/run_release_switch_validation.py --decision-only --doc-sync-report docs/current/status/baselines/e13-doc-sync-check-report.json --quality-report docs/current/status/baselines/e11-quality-regression-report.json --perf-report docs/current/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/current/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/current/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/current/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/current/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/current/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-20 Additions

- Extended `scripts/run_release_switch_validation.py` with release-gate option-override gate: decision now validates `beta_gate/ga_gate/roadmap_gate` commands contain exactly one `--stages` and one `--output` option before `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_options_are_ambiguous` to assert repeated `--stages/--output` options force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_option_override_gate` to assert `--skip-release-gate-option-override-check` disables the option-override gate for emergency recovery.
- Added `TP-E13-20` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only with option-override gate example: `python scripts/run_release_switch_validation.py --decision-only --doc-sync-report docs/current/status/baselines/e13-doc-sync-check-report.json --quality-report docs/current/status/baselines/e11-quality-regression-report.json --perf-report docs/current/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/current/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/current/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/current/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/current/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/current/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-21 Additions

- Extended `scripts/run_release_switch_validation.py` with release-gate relaxed-flags gate: decision now blocks `GO` when release-gate commands include `--allow-regression/--no-coverage/--container-skip-build/--container-skip-run/--allow-secondary-failures`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_relaxed_flags` to assert relaxed flags force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_relaxed_flags_gate` to assert `--skip-release-gate-relaxed-flags-check` disables the relaxed-flags gate for emergency recovery.
- Added `TP-E13-21` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only with relaxed-flags gate example: `python scripts/run_release_switch_validation.py --decision-only --doc-sync-report docs/current/status/baselines/e13-doc-sync-check-report.json --quality-report docs/current/status/baselines/e11-quality-regression-report.json --perf-report docs/current/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/current/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/current/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/current/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/current/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/current/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-22 Additions

- Extended `scripts/run_release_switch_validation.py` with release-gate dry-run gate: decision now blocks `GO` when release-gate stage commands include `--dry-run` pseudo-execution flags.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_dry_run_flag` to assert `--dry-run` in release-gate stage commands forces `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_dry_run_gate` to assert `--skip-release-gate-dry-run-check` disables the dry-run gate for emergency recovery.
- Added `TP-E13-22` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only with dry-run gate example: `python scripts/run_release_switch_validation.py --decision-only --doc-sync-report docs/current/status/baselines/e13-doc-sync-check-report.json --quality-report docs/current/status/baselines/e11-quality-regression-report.json --perf-report docs/current/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/current/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/current/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/current/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/current/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/current/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-23 Additions

- Extended `scripts/run_release_switch_validation.py` with release-gate script-position gate: decision now requires each release-gate stage to execute `scripts/run_linux_validation_suite.py` as the first script token, preventing decoy-token spoofing from producing false `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_script_position_is_decoy` to assert decoy script-token plans force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_script_position_gate` to assert `--skip-release-gate-script-position-check` disables the script-position gate for emergency recovery.
- Added `TP-E13-23` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only with script-position gate example: `python scripts/run_release_switch_validation.py --decision-only --doc-sync-report docs/current/status/baselines/e13-doc-sync-check-report.json --quality-report docs/current/status/baselines/e11-quality-regression-report.json --perf-report docs/current/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/current/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/current/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/current/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/current/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/current/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-24 Additions

- Extended `scripts/run_release_switch_validation.py` with release-gate inline-exec gate: decision now blocks `GO` when release-gate stage commands use python inline-dispatch flags (`-c`, `-m`, `-`) before `scripts/run_linux_validation_suite.py` script token.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_inline_exec_flag` to assert inline-dispatch bypass plans force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_inline_exec_gate` to assert `--skip-release-gate-inline-exec-check` disables the inline-exec gate for emergency recovery.
- Added `TP-E13-24` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only with inline-exec gate example: `python scripts/run_release_switch_validation.py --decision-only --doc-sync-report docs/current/status/baselines/e13-doc-sync-check-report.json --quality-report docs/current/status/baselines/e11-quality-regression-report.json --perf-report docs/current/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/current/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/current/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/current/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/current/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/current/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-25 Additions

- Extended `scripts/run_release_switch_validation.py` with release-gate script-anchor gate: decision now requires release-gate stage commands to resolve `scripts/run_linux_validation_suite.py` to repository canonical path before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_script_path_is_not_repo_canonical` to assert same-name external script path spoofing forces `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_script_anchor_gate` to assert `--skip-release-gate-script-anchor-check` disables the script-anchor gate for emergency recovery.
- Added `TP-E13-25` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only with script-anchor gate example: `python scripts/run_release_switch_validation.py --decision-only --doc-sync-report docs/current/status/baselines/e13-doc-sync-check-report.json --quality-report docs/current/status/baselines/e11-quality-regression-report.json --perf-report docs/current/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/current/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/current/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/current/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/current/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/current/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-26 Additions

- Extended `scripts/run_release_switch_validation.py` with release-gate python-binding gate: decision now requires each release-gate stage command to keep `--python` single-occurrence, value-equal to release-switch `--python`, and launcher-prefix consistent with that value before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_python_binding_mismatches` to assert `--python` drift in release-gate stage commands forces `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_python_binding_gate` to assert `--skip-release-gate-python-binding-check` disables the python-binding gate for emergency recovery.
- Added `TP-E13-26` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only with python-binding gate example: `python scripts/run_release_switch_validation.py --decision-only --python python3 --doc-sync-report docs/current/status/baselines/e13-doc-sync-check-report.json --quality-report docs/current/status/baselines/e11-quality-regression-report.json --perf-report docs/current/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/current/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/current/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/current/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/current/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/current/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-27 Additions

- Extended `scripts/run_release_switch_validation.py` with release-gate coverage-floor gate: decision now requires `beta_gate` to keep `--coverage-fail-under` value bound to release-switch input and not lower than `50` before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_coverage_floor_is_downgraded` to assert coverage-threshold downgrade forces `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_coverage_floor_gate` to assert `--skip-release-gate-coverage-floor-check` disables the coverage-floor gate for emergency recovery.
- Added `TP-E13-27` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only with coverage-floor gate example: `python scripts/run_release_switch_validation.py --decision-only --coverage-fail-under 50 --doc-sync-report docs/current/status/baselines/e13-doc-sync-check-report.json --quality-report docs/current/status/baselines/e11-quality-regression-report.json --perf-report docs/current/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/current/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/current/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/current/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/current/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/current/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-28 Additions

- Extended `scripts/run_release_switch_validation.py` with release-gate python-optimization gate: decision now requires `beta_gate/ga_gate/roadmap_gate` launchers to avoid python optimization flags (`-O`, `-OO`) before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_python_optimization_flag` to assert python optimization flags force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_python_optimization_gate` to assert `--skip-release-gate-python-optimization-check` disables the gate for emergency recovery.
- Added `TP-E13-28` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only with python-optimization gate example: `python scripts/run_release_switch_validation.py --decision-only --python "python3 -O" --doc-sync-report docs/current/status/baselines/e13-doc-sync-check-report.json --quality-report docs/current/status/baselines/e11-quality-regression-report.json --perf-report docs/current/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/current/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/current/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/current/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/current/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/current/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-29 Additions

- Extended `scripts/run_release_switch_validation.py` with release-gate python-option-optimization gate: decision now requires `beta_gate/ga_gate/roadmap_gate` `--python` relay values to avoid python optimization flags (`-O`, `-OO`) before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_python_option_uses_optimization_flag` to assert optimization flags in stage `--python` relay values force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_python_option_optimization_gate` to assert `--skip-release-gate-python-option-optimization-check` disables the gate for emergency recovery.
- Added `TP-E13-29` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only with python-option-optimization gate example: `python scripts/run_release_switch_validation.py --decision-only --skip-release-gate-python-binding-check --doc-sync-report docs/current/status/baselines/e13-doc-sync-check-report.json --quality-report docs/current/status/baselines/e11-quality-regression-report.json --perf-report docs/current/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/current/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/current/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/current/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/current/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/current/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-30 Additions

- Extended `scripts/run_release_switch_validation.py` with release-gate python-optimize-env gate: decision now rejects `PYTHONOPTIMIZE=*` assignments in stage launchers and `--python` relay values before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_python_optimize_env_assignment` to assert `PYTHONOPTIMIZE` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_python_optimize_env_gate` to assert `--skip-release-gate-python-optimize-env-check` disables the gate for emergency recovery.
- Added `TP-E13-30` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only with python-optimize-env gate example: `python scripts/run_release_switch_validation.py --decision-only --python "env PYTHONOPTIMIZE=2 python3" --doc-sync-report docs/current/status/baselines/e13-doc-sync-check-report.json --quality-report docs/current/status/baselines/e11-quality-regression-report.json --perf-report docs/current/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/current/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/current/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/current/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/current/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/current/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-31 Additions

- Extended `scripts/run_release_switch_validation.py` with release-gate python-option-inline-exec gate: decision now rejects `--python` relay values that include inline-dispatch flags (`-c`, `-m`, `-`) before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_python_option_uses_inline_exec_flag` to assert inline-dispatch flags in stage `--python` relay values force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_python_option_inline_exec_gate` to assert `--skip-release-gate-python-option-inline-exec-check` disables the gate for emergency recovery.
- Added `TP-E13-31` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only with python-option-inline-exec gate example: `python scripts/run_release_switch_validation.py --decision-only --skip-release-gate-python-binding-check --doc-sync-report docs/current/status/baselines/e13-doc-sync-check-report.json --quality-report docs/current/status/baselines/e11-quality-regression-report.json --perf-report docs/current/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/current/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/current/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/current/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/current/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/current/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-32 Additions

- Extended `scripts/run_release_switch_validation.py` with release-gate python-path-env gate: decision now rejects `PYTHONPATH=*` assignments in stage launchers and `--python` relay values before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_python_path_env_assignment` to assert `PYTHONPATH` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_python_path_env_gate` to assert `--skip-release-gate-python-path-env-check` disables the gate for emergency recovery.
- Added `TP-E13-32` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only with python-path-env gate example: `python scripts/run_release_switch_validation.py --decision-only --python "env PYTHONPATH=/tmp/rogue python3" --doc-sync-report docs/current/status/baselines/e13-doc-sync-check-report.json --quality-report docs/current/status/baselines/e11-quality-regression-report.json --perf-report docs/current/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/current/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/current/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/current/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/current/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/current/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-33 Additions

- Extended `scripts/run_release_switch_validation.py` with release-gate python-home-env gate: decision now rejects `PYTHONHOME=*` assignments in stage launchers and `--python` relay values before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_python_home_env_assignment` to assert `PYTHONHOME` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_python_home_env_gate` to assert `--skip-release-gate-python-home-env-check` disables the gate for emergency recovery.
- Added `TP-E13-33` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only with python-home-env gate example: `python scripts/run_release_switch_validation.py --decision-only --python "env PYTHONHOME=/tmp/rogue-home python3" --doc-sync-report docs/current/status/baselines/e13-doc-sync-check-report.json --quality-report docs/current/status/baselines/e11-quality-regression-report.json --perf-report docs/current/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/current/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/current/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/current/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/current/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/current/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-34 Additions

- Extended `scripts/run_release_switch_validation.py` with release-gate python-user-base-env gate: decision now rejects `PYTHONUSERBASE=*` assignments in stage launchers and `--python` relay values before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_python_user_base_env_assignment` to assert `PYTHONUSERBASE` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_python_user_base_env_gate` to assert `--skip-release-gate-python-user-base-env-check` disables the gate for emergency recovery.
- Added `TP-E13-34` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only with python-user-base-env gate example: `python scripts/run_release_switch_validation.py --decision-only --python "env PYTHONUSERBASE=/tmp/rogue-userbase python3" --doc-sync-report docs/current/status/baselines/e13-doc-sync-check-report.json --quality-report docs/current/status/baselines/e11-quality-regression-report.json --perf-report docs/current/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/current/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/current/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/current/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/current/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/current/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-35 Additions

- Extended `scripts/run_release_switch_validation.py` with release-gate python-breakpoint-env gate: decision now rejects `PYTHONBREAKPOINT=*` assignments in stage launchers and `--python` relay values before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_python_breakpoint_env_assignment` to assert `PYTHONBREAKPOINT` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_python_breakpoint_env_gate` to assert `--skip-release-gate-python-breakpoint-env-check` disables the gate for emergency recovery.
- Added `TP-E13-35` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only with python-breakpoint-env gate example: `python scripts/run_release_switch_validation.py --decision-only --python "env PYTHONBREAKPOINT=evil.hook python3" --doc-sync-report docs/current/status/baselines/e13-doc-sync-check-report.json --quality-report docs/current/status/baselines/e11-quality-regression-report.json --perf-report docs/current/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/current/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/current/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/current/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/current/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/current/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-36 Additions

- Extended `scripts/run_release_switch_validation.py` with release-gate python-startup-env gate: decision now rejects `PYTHONSTARTUP=*` assignments in stage launchers and `--python` relay values before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_python_startup_env_assignment` to assert `PYTHONSTARTUP` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_python_startup_env_gate` to assert `--skip-release-gate-python-startup-env-check` disables the gate for emergency recovery.
- Added `TP-E13-36` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only with python-startup-env gate example: `python scripts/run_release_switch_validation.py --decision-only --python "env PYTHONSTARTUP=/tmp/evil-startup.py python3" --doc-sync-report docs/current/status/baselines/e13-doc-sync-check-report.json --quality-report docs/current/status/baselines/e11-quality-regression-report.json --perf-report docs/current/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/current/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/current/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/current/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/current/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/current/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-37 Additions

- Extended `scripts/run_release_switch_validation.py` with release-gate python-inspect-env gate: decision now rejects `PYTHONINSPECT=*` assignments in stage launchers and `--python` relay values before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_python_inspect_env_assignment` to assert `PYTHONINSPECT` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_python_inspect_env_gate` to assert `--skip-release-gate-python-inspect-env-check` disables the gate for emergency recovery.
- Added `TP-E13-37` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only with python-inspect-env gate example: `python scripts/run_release_switch_validation.py --decision-only --python "env PYTHONINSPECT=1 python3" --doc-sync-report docs/current/status/baselines/e13-doc-sync-check-report.json --quality-report docs/current/status/baselines/e11-quality-regression-report.json --perf-report docs/current/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/current/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/current/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/current/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/current/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/current/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-38 Additions

- Extended `scripts/run_release_switch_validation.py` with release-gate python-warnings-env gate: decision now rejects `PYTHONWARNINGS=*` assignments in stage launchers and `--python` relay values before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_python_warnings_env_assignment` to assert `PYTHONWARNINGS` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_python_warnings_env_gate` to assert `--skip-release-gate-python-warnings-env-check` disables the gate for emergency recovery.
- Added `TP-E13-38` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only with python-warnings-env gate example: `python scripts/run_release_switch_validation.py --decision-only --python "env PYTHONWARNINGS=ignore python3" --doc-sync-report docs/current/status/baselines/e13-doc-sync-check-report.json --quality-report docs/current/status/baselines/e11-quality-regression-report.json --perf-report docs/current/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/current/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/current/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/current/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/current/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/current/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.
