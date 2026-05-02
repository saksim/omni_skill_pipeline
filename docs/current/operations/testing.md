# Testing

## 閸掋倛鐦?
鏉╂瑤閲滄禒鎾崇秼閸撳秷铔嬮惃鍕Ц `unittest` 娴ｆ挾閮撮敍灞肩瑝閺?`pytest` 娴ｆ挾閮撮敍娑欑ゴ鐠囨洖鍨介弬顓☆洣閹稿骞囬張澶愭懠鐠侯垶鐛欑亸闈╃礉娑撳秷顩﹂幏鍧楁晩閸掓垵鍙块妴?
## 閺堫剙婀撮悳顖氼暔鐎靛綊缍?
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

## 閸忋劑鍣洪崶鐐茬秺

```bash
python scripts/run_ci.py
```

鐠囥儱鍙嗛崣锝勭窗缂佺喍绔撮幍褑顢戦敍?
- `python -m coverage run --parallel-mode -m unittest discover -s tests -p 'test_*.py'`
- `python scripts/run_tp_tests.py --all --python <current-python>`
- `python -m coverage combine`
- `python -m coverage report --show-missing --fail-under <threshold>`
- `python -m coverage xml -o coverage.xml`

姒涙顓?coverage fail-under 娑?`50`閿涘苯褰查柅姘崇箖閸欏倹鏆熺憰鍡欐磰閵?
缁€杞扮伐閿涙碍褰佹姗€妲囬崐鐓庡煂 `65`

```bash
python scripts/run_ci.py --coverage-fail-under 65
```

缁€杞扮伐閿涙矮绮庨崷銊︽拱閸︽澘鎻╅柅鐔肩崣闁槒绶敍灞煎閺冭泛鍙ч梻?coverage

```bash
python scripts/run_ci.py --no-coverage
```

## 鐎圭懓娅掗悜鐔哥ゴ閼存碍婀?
鐎圭懓娅掗崺铏瑰殠閻戠喐绁撮敍鍫熺€娲殔閸?+ 閸氼垰濮╃€圭懓娅?+ 鏉烆喛顕?`/healthz`閿涘绱?
```bash
python scripts/run_container_smoke.py --image-tag omni-skill-pipeline:local --port 18000
```

閸欘亞婀呴幍褑顢戠拋鈥冲灊閿涘奔绗夐惇鐔割劀鐠嬪啰鏁?Docker閿?
```bash
python scripts/run_container_smoke.py --dry-run
```

Linux 缂佺喍绔存灞剧ゴ閺冭泛缂撶拋顔炬纯閹恒儰濞囬悽銊嚉閼存碍婀伴敍灞肩稊娑?`LC-L1-18` 閻ㄥ嫬顔愰崳銊ユ礀瑜版帒鍙嗛崣锝冣偓?
## Dual-Write Benchmark Harness

`LC-L2-33` 瀵洖鍙?dual-write 閸╁搫鍣懘姘拱閿?
```bash
python scripts/benchmark_dual_write.py --iterations 20 --skip-postgres
python scripts/benchmark_dual_write.py --iterations 20 --postgres-dsn "$OMNI_TEST_POSTGRES_DSN"
```

- 缁楊兛绔存稉顏勬嚒娴犮倕褰уù?file repository baseline閵?- 缁楊兛绨╂稉顏勬嚒娴犮倖绁?file + Postgres dual-write 閺冭泛娆㈤妴?- 姒涙顓婚幎銉ユ啞閽€鐣屾磸閿涙瓪docs/current/status/baselines/e8-dual-write-benchmark-report.json`閵?
## 鐎规艾鎮滈幍褑顢?
閺屻儳婀呰ぐ鎾冲瀹稿弶妲х亸?Task Package:

```bash
python scripts/run_tp_tests.py --list
```

閹笛嗩攽閸楁洑閲滃銉ュ礋:

```bash
python scripts/run_tp_tests.py TP-E6-02 --python python
```

閹笛嗩攽婢舵矮閲滃銉ュ礋:

```bash
python scripts/run_tp_tests.py TP-E1-01 TP-E1-02 TP-E1-03 TP-E2-01 TP-E2-02 TP-E2-03 TP-E3-01 TP-E3-02 TP-E3-03 TP-E4-01 TP-E4-02 TP-E4-03 TP-E4-04 TP-E4-05 TP-E5-01 TP-E5-02 TP-E5-03 TP-E5-04 TP-E6-01 TP-E6-02 TP-E6-03 TP-E6-04 TP-E7-01 TP-E7-02 TP-E7-03 TP-E7-04 TP-E8-01 TP-E8-02 TP-E8-03 TP-E8-04 TP-E9-01 TP-E9-02 TP-E9-03 TP-E10-01 TP-E10-02 TP-E10-03 TP-E11-01 TP-E11-02 TP-E11-03 TP-E11-04 TP-E12-01 TP-E12-02 TP-E12-03 TP-E12-04 TP-E13-01 TP-E13-02 TP-E13-03 TP-E13-04 TP-E13-05 TP-E13-06 TP-E13-07 TP-E13-08 TP-E13-09 TP-E13-10 TP-E13-11 TP-E13-12 TP-E13-13 TP-E13-14 TP-E13-15 TP-E13-16 TP-E13-17 TP-E13-18 TP-E13-19 TP-E13-20 TP-E13-21 TP-E13-22 TP-E13-23 TP-E13-24 TP-E13-25 TP-E13-26 TP-E13-27 TP-E13-28 TP-E13-29 TP-E13-30 TP-E13-31 TP-E13-32 TP-E13-33 TP-E13-34 TP-E13-35 TP-E13-36 TP-E13-37 TP-E13-38 TP-E13-39 TP-E13-40 TP-E13-41 TP-E13-42 TP-E13-43 TP-E13-44 TP-E13-45 TP-E13-46 TP-E13-47 TP-E13-48 TP-E13-49 TP-E13-50 TP-E13-51 TP-E13-52 TP-E13-53 TP-E13-54 TP-E13-55 TP-E13-56 TP-E13-57 TP-E13-58 TP-E13-59 TP-E13-60 TP-E13-61 TP-E13-62 TP-E13-63 TP-E13-64 TP-E13-65 TP-E13-66 TP-E13-67 TP-E13-68 TP-E13-69 TP-E13-70 TP-E13-71 TP-E13-72 TP-E13-73 TP-E13-74 TP-E13-75 TP-E13-76 TP-E13-77 TP-E13-78 TP-E13-79 TP-E13-80 TP-E13-81 TP-E13-82 TP-E13-83 TP-E13-84 --python python3
```

## 瑜版挸澧犵憰鍡欐磰闁插秶鍋?
- `tests/test_mvp.py`: 鐟曞棛娲?text / audio / image / video / tabular 娑撴槒鐭惧?- `tests/test_v2_schema_and_corpus.py`: 鐟曞棛娲?corpus 缂佸嫯顥婇妴涔竨blication閵嗕构uality閵嗕购eview artifacts
- `tests/test_quality_scoring.py`: 鐟曞棛娲婄拹銊╁櫤鐠囧嫬鍨?- `tests/test_review_policy.py`: 鐟曞棛娲?review threshold 娑?reason codes
- `tests/test_dual_write_repository.py`: 鐟曞棛娲?dual-write 娑?娴犲簼绮ㄩ崒銊攽娑撹桨绗屾径杈Е娣囨繃濮?- `tests/test_benchmark_dual_write.py`: 鐟曞棛娲?dual-write benchmark 閼存碍婀伴悜鐔哥ゴ
- `tests/test_similarity_retrieval.py`: 鐟曞棛娲婂Λ鈧槐銏″▕鐠灺扳偓涔畁memory baseline 閹烘帒绨妴涔ckend 闁鐎烽崡鐘辩秴鐞涘奔璐?- `tests/test_lifecycle_decision_engine.py`: 鐟曞棛娲?lifecycle `new/revise/merge/supersede/reject` 閸愬磭鐡ラ崚鍡樼ウ
- `tests/test_publication_builder.py`: 鐟曞棛娲?checklist/decision_tree 鏉堟挸鍤稉搴㈡￥ decision 閸︾儤娅?fallback
- `tests/test_publication_orchestrator_split.py`: 鐟曞棛娲?goal_type 妞瑰崬濮╅惃?publication type 闁瀚?- `tests/test_api_app.py`: 鐟曞棛娲?distill API 鏉堟挸鍙嗘潪顒佸床閵嗕線鏁婄拠顖涙Ё鐏忓嫪绗?TP-E10-02 閻?V2 鏉堟挸鍤總鎴犲鐎涙顔?- `tests/test_worker.py`: 鐟曞棛娲?TP-E10-03 worker 閺傞鎹㈤崝锛勮閸ㄥ绱檙eview_queue/rebuild_publication/revise_skill閿?- `tests/test_transformers_regression.py`: 鐟曞棛娲?TP-E11-01 濡€崇€?鏉烆剚宕查崳銊ュ瀻閺€顖氭礀瑜版帪绱檚kill_type閵嗕躬vidence 閼辨艾鎮庨妴涔磂gacy atom bridge閿?- `tests/test_doc_sync_check_script.py`: 鐟曞棛娲?TP-E13-01 / TP-E13-02 / TP-E13-03 閺傚洦銆傞崥灞绢劄濡偓閺屻儴鍓奸張顒婄礄濠ф劗鐖滅悰銊╂桨 + 鏉╀胶些閹稿洤宕?+ 閸欐垵绔烽崚鍥ㄥ床閺嶅洤鍣?+ LC-L1-19 Beta runbook 婵傛垹瀹抽敍?- `tests/test_linux_validation_suite_script.py`: 鐟曞棛娲?TP-E13-04 Linux 缂佺喍绔存灞芥缂傛牗甯撻懘姘拱閿涘牓妯佸▓鐢电摣闁鈧礁鎳℃禒銈嗗ⅵ閸栧懌鈧龚ry-run 鐠佲€冲灊閽€鐣屾磸閵嗕恭ontainer smoke / postgres_soak / postgres_ga / worker_ga / review_queue_ga / provider_ga / calibration_ga / roadmap_extension 閸欏倹鏆熼柅蹇庣炊閿?- `tests/test_postgres_soak_validation_script.py`: 鐟曞棛娲?TP-E13-05 Postgres 闂€璺ㄇ旀灞芥閼存碍婀伴敍鍦盤 閸ョ偛缍婄紓鏍ㄥ笓閵嗕攻enchmark 閸欏倹鏆熼妴涔╯n fail-fast閿?- `tests/test_worker_ga_validation_script.py`: 鐟曞棛娲?TP-E13-06 worker GA 妤犲矁鐦夐懘姘拱閿涘牓妯佸▓鐢电摣闁鈧龚ry-run 鐠佲€冲灊閽€鐣屾磸閿?- `tests/test_provider_ga_validation_script.py`: 鐟曞棛娲?TP-E13-07 provider GA 妤犲矁鐦夐懘姘拱閿涘澁etry/circuit-breaker/failure-budget/audit 鐠佲€冲灊缂傛牗甯撻敍?- `tests/test_review_queue_ga_validation_script.py`: 鐟曞棛娲?TP-E13-08 review queue GA 妤犲矁鐦夐懘姘拱閿涘澁epository/service/api/feedback 闂冭埖顔岀紓鏍ㄥ笓娑撳海鐡柅澶涚礆
- `tests/test_calibration_ga_validation_script.py`: 鐟曞棛娲?TP-E13-09 calibration GA 妤犲矁鐦夐懘姘拱閿涘牓妲囬崐鐓庮殩缁撅负鈧浇鐨熼崣鍌涘Г閸涘鈧沟anifest/report 閸欏倹鏆熼柅蹇庣炊閿?- `tests/test_postgres_ga_validation_script.py`: 鐟曞棛娲?TP-E13-10 Postgres GA 妤犲矁鐦夐懘姘拱閿涘澁epository/dual-write/benchmark 闂冭埖顔岀紓鏍ㄥ笓閵嗕龚sn fail-fast閵嗕攻enchmark 閸欏倹鏆熼柅蹇庣炊閿?- `tests/test_roadmap_extension_validation_script.py`: 鐟曞棛娲?TP-E13-11 roadmap extension 妤犲矁鐦夐懘姘拱閿涘湢C-R-34~37 閻?retrieval/lifecycle/publication/review queue surface 闂冭埖顔岀紓鏍ㄥ笓娑撳海鐡柅澶涚礆
- `tests/test_release_gate_validation_script.py`: 鐟曞棛娲?TP-E13-12 閸欐垵绔烽梻銊ь洣閼辨艾鎮庨懘姘拱閿涘潌eta/ga/roadmap 闂冭埖顔岀粵娑⑩偓澶夌瑢 coverage/container/postgres/calibration 閸欏倹鏆熼柅蹇庣炊閿?- `tests/test_release_switch_validation_script.py`: 鐟曞棛娲?TP-E13-13 / TP-E13-14 / TP-E13-15 / TP-E13-16 / TP-E13-17 / TP-E13-18 / TP-E13-19 / TP-E13-20 / TP-E13-21 / TP-E13-22 / TP-E13-23 / TP-E13-24 / TP-E13-25 / TP-E13-26 / TP-E13-27 / TP-E13-28 / TP-E13-29 / TP-E13-30 / TP-E13-31 / TP-E13-32 / TP-E13-33 / TP-E13-34 / TP-E13-35 / TP-E13-36 / TP-E13-37 閸欐垵绔烽崚鍥ㄥ床閸掋倕鐣鹃懘姘拱閿涘澁elease-gate/TP/doc-sync 缂傛牗甯撻妴涔╡cision-only GO/HOLD閵嗕浇鐦夐幑顔煎瘶閳ユ粌鐣弫瀛樷偓?+ 閸欘垱澧界悰灞芥嚒娴犮倛顓搁崚鎺嗏偓婵嬫，缁備降鈧躬vidence freshness 閺冭埖鏅ラ梻銊ь洣閵嗕公uture timestamp skew 闂傘劎顩﹂妴涔hort skew 闂傘劎顩︽稉宸杄lease-gate output binding 闂傘劎顩︽稉?stage contract 闂傘劎顩︽稉?script-position 闂傘劎顩︽稉?option override 闂傘劎顩︽稉?relaxed-flag 闂傘劎顩?+ dry-run 闂傘劎顩?+ script-anchor 闂傘劎顩?+ python-binding 闂傘劎顩?+ coverage-floor 闂傘劎顩?+ python-optimization 闂傘劎顩?+ python-option-optimization 闂傘劎顩?+ python-optimize-env 闂傘劎顩?+ python-option-inline-exec 闂傘劎顩?+ python-path-env 闂傘劎顩?+ python-home-env 闂傘劎顩?+ python-user-base-env 闂傘劎顩?+ python-breakpoint-env 闂傘劎顩?+ python-startup-env 闂傘劎顩?+ python-inspect-env 闂傘劎顩﹂敍?- `tests/test_tp_registry.py`: 鐟曞棛娲?TP 濞夈劌鍞界悰銊ょ瑢 `skill-distillation-v2-work-orders.md` 閻ㄥ嫬寮婚崥鎴濈暚閺佸瓨鈧冾嚠姒绘劧绱欏蹇旀Ё鐏?+ 楠炵晫浼掗弰鐘茬殸閿?
## 瑜版挸澧犵紓鍝勫經

- FastAPI/ASGI API 閼奉亜濮╅崠鏍ㄧゴ鐠囨洖鍑＄憰鍡欐磰閺嶇绺炬總鎴犲閿涙稐绮涚紓铏规埂鐎?provider 閺佸懘娈板▔銊ュ弳娑撳氦绀嬫潪钘夋簚閺?- coverage fail-under 娴犲秵妲告穱婵嗙暓闂冨牆鈧》绱檂50`閿涘绱濋崥搴ｇ敾鎼存棃娈㈢拹銊╁櫤閸╄櫣鍤庨幓鎰磳
- 鐏忔碍妫ら悽鐔堕獓缁狙嗙鏉炶棄甯囧ù瀣剁礄瑜版挸澧犳禒鍛箒 dual-write benchmark smoke harness閿?- 閻喎鐤?provider failure-mode 鐟曞棛娲婃禒宥呬焊閽?
## 缂佸瓨濮㈢憴鍕灟

濮ｅ繑顐奸弬鏉款杻 `TP-*` 瀹搞儱宕熼弮璁圭礉閼峰啿鐨崥灞绢劄鐎瑰本鍨氭稉澶夋娴滃绱?
1. 閸?`tests/` 閽€鑺ョゴ鐠?case
2. 閸?`scripts/run_tp_tests.py` 閻?`TP_TEST_CASES` 娑擃厾娅ョ拋鐗堟Ё鐏?3. 閸︺劍婀伴弬鍥︽閺囧瓨鏌婄憰鍡欐磰閼煎啫娲挎稉搴㈡煀婢х偛浼愰崡鏇☆嚛閺勫函绱欓獮鍓佲€樻穱?`tests/test_tp_registry.py` 鐎靛綊缍?work-orders閿?
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

## TP-E13-39 Additions

- Extended `scripts/run_release_switch_validation.py` with release-gate python-env-wildcard gate: decision now rejects unknown `PYTHON*` assignments in stage launchers and `--python` relay values (already-registered gate keys excluded) before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_unknown_python_env_assignment` to assert unknown `PYTHON*` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_python_env_wildcard_gate` to assert `--skip-release-gate-python-env-wildcard-check` disables the gate for emergency recovery.
- Added `TP-E13-39` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only with python-env-wildcard gate example: `python scripts/run_release_switch_validation.py --decision-only --python "env PYTHONUNBUFFERED=1 python3" --doc-sync-report docs/current/status/baselines/e13-doc-sync-check-report.json --quality-report docs/current/status/baselines/e11-quality-regression-report.json --perf-report docs/current/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/current/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/current/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/current/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/current/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/current/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-40 Additions

- Extended `scripts/run_release_switch_validation.py` with release-gate path-env gate: decision now rejects `PATH=*` assignments in stage launchers and `--python` relay values before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_path_env_assignment` to assert `PATH` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_path_env_gate` to assert `--skip-release-gate-path-env-check` disables the gate for emergency recovery.
- Added `TP-E13-40` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only with path-env gate example: `python scripts/run_release_switch_validation.py --decision-only --python "env PATH=/tmp/rogue python3" --doc-sync-report docs/current/status/baselines/e13-doc-sync-check-report.json --quality-report docs/current/status/baselines/e11-quality-regression-report.json --perf-report docs/current/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/current/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/current/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/current/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/current/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/current/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-41 Additions

- Extended `scripts/run_release_switch_validation.py` with release-gate ld-preload-env gate: decision now rejects `LD_PRELOAD=*` assignments in stage launchers and `--python` relay values before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_ld_preload_env_assignment` to assert `LD_PRELOAD` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_ld_preload_env_gate` to assert `--skip-release-gate-ld-preload-env-check` disables the gate for emergency recovery.
- Added `TP-E13-41` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only with ld-preload-env gate example: `python scripts/run_release_switch_validation.py --decision-only --python "env LD_PRELOAD=/tmp/evil.so python3" --doc-sync-report docs/current/status/baselines/e13-doc-sync-check-report.json --quality-report docs/current/status/baselines/e11-quality-regression-report.json --perf-report docs/current/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/current/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/current/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/current/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/current/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/current/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-42 Additions

- Extended `scripts/run_release_switch_validation.py` with release-gate ld-library-path-env gate: decision now rejects `LD_LIBRARY_PATH=*` assignments in stage launchers and `--python` relay values before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_ld_library_path_env_assignment` to assert `LD_LIBRARY_PATH` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_ld_library_path_env_gate` to assert `--skip-release-gate-ld-library-path-env-check` disables the gate for emergency recovery.
- Added `TP-E13-42` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only with ld-library-path-env gate example: `python scripts/run_release_switch_validation.py --decision-only --python "env LD_LIBRARY_PATH=/tmp/evil-lib python3" --doc-sync-report docs/current/status/baselines/e13-doc-sync-check-report.json --quality-report docs/current/status/baselines/e11-quality-regression-report.json --perf-report docs/current/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/current/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/current/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/current/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/current/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/current/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-43 Additions

- Extended `scripts/run_release_switch_validation.py` with release-gate ld-audit-env gate: decision now rejects `LD_AUDIT=*` assignments in stage launchers and `--python` relay values before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_ld_audit_env_assignment` to assert `LD_AUDIT` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_ld_audit_env_gate` to assert `--skip-release-gate-ld-audit-env-check` disables the gate for emergency recovery.
- Added `TP-E13-43` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only with ld-audit-env gate example: `python scripts/run_release_switch_validation.py --decision-only --python "env LD_AUDIT=/tmp/evil.audit.so python3" --doc-sync-report docs/current/status/baselines/e13-doc-sync-check-report.json --quality-report docs/current/status/baselines/e11-quality-regression-report.json --perf-report docs/current/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/current/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/current/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/current/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/current/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/current/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-44 Additions

- Extended `scripts/run_release_switch_validation.py` with release-gate ld-env-wildcard gate: decision now rejects unknown `LD_*` assignments in stage launchers and `--python` relay values (already-registered gate keys excluded) before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_unknown_ld_env_assignment` to assert unknown `LD_*` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_ld_env_wildcard_gate` to assert `--skip-release-gate-ld-env-wildcard-check` disables the gate for emergency recovery.
- Added `TP-E13-44` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only with ld-env-wildcard gate example: `python scripts/run_release_switch_validation.py --decision-only --python "env LD_DEBUG=files python3" --doc-sync-report docs/current/status/baselines/e13-doc-sync-check-report.json --quality-report docs/current/status/baselines/e11-quality-regression-report.json --perf-report docs/current/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/current/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/current/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/current/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/current/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/current/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-45 Additions

- Extended `scripts/run_release_switch_validation.py` with release-gate glibc-tunables-env gate: decision now rejects `GLIBC_TUNABLES=*` assignments in stage launchers and `--python` relay values before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_glibc_tunables_env_assignment` to assert `GLIBC_TUNABLES` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_glibc_tunables_env_gate` to assert `--skip-release-gate-glibc-tunables-env-check` disables the gate for emergency recovery.
- Added `TP-E13-45` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only with glibc-tunables-env gate example: `python scripts/run_release_switch_validation.py --decision-only --python "env GLIBC_TUNABLES=glibc.malloc.check=3 python3" --doc-sync-report docs/current/status/baselines/e13-doc-sync-check-report.json --quality-report docs/current/status/baselines/e11-quality-regression-report.json --perf-report docs/current/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/current/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/current/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/current/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/current/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/current/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-46 Additions

- Extended `scripts/run_release_switch_validation.py` with release-gate glibc-env-wildcard gate: decision now rejects unknown `GLIBC_*` assignments (registered gate keys excluded) in stage launchers and `--python` relay values before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_unknown_glibc_env_assignment` to assert unknown `GLIBC_*` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_glibc_env_wildcard_gate` to assert `--skip-release-gate-glibc-env-wildcard-check` disables the gate for emergency recovery.
- Added `TP-E13-46` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only with glibc-env-wildcard gate example: `python scripts/run_release_switch_validation.py --decision-only --python "env GLIBC_MEMUSAGE=1 python3" --doc-sync-report docs/current/status/baselines/e13-doc-sync-check-report.json --quality-report docs/current/status/baselines/e11-quality-regression-report.json --perf-report docs/current/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/current/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/current/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/current/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/current/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/current/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-47 Additions

- Extended `scripts/run_release_switch_validation.py` with release-gate malloc-env-wildcard gate: decision now rejects unknown `MALLOC_*` assignments (registered gate keys excluded) in stage launchers and `--python` relay values before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_unknown_malloc_env_assignment` to assert unknown `MALLOC_*` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_malloc_env_wildcard_gate` to assert `--skip-release-gate-malloc-env-wildcard-check` disables the gate for emergency recovery.
- Added `TP-E13-47` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only with malloc-env-wildcard gate example: `python scripts/run_release_switch_validation.py --decision-only --python "env MALLOC_SHADOW_POLICY=strict python3" --doc-sync-report docs/current/status/baselines/e13-doc-sync-check-report.json --quality-report docs/current/status/baselines/e11-quality-regression-report.json --perf-report docs/current/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/current/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/current/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/current/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/current/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/current/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-48 Additions

- Extended `scripts/run_release_switch_validation.py` with release-gate malloc-trace-env gate: decision now rejects `MALLOC_TRACE=*` assignments in stage launchers and `--python` relay values before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_malloc_trace_env_assignment` to assert `MALLOC_TRACE` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_malloc_trace_env_gate` to assert `--skip-release-gate-malloc-trace-env-check` disables the gate for emergency recovery.
- Added `TP-E13-48` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only with malloc-trace-env gate example: `python scripts/run_release_switch_validation.py --decision-only --python "env MALLOC_TRACE=/tmp/mtrace.log python3" --doc-sync-report docs/current/status/baselines/e13-doc-sync-check-report.json --quality-report docs/current/status/baselines/e11-quality-regression-report.json --perf-report docs/current/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/current/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/current/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/current/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/current/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/current/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-49 Additions

- Extended `scripts/run_release_switch_validation.py` with release-gate malloc-check-env gate: decision now rejects `MALLOC_CHECK_=*` assignments in stage launchers and `--python` relay values before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_malloc_check_env_assignment` to assert `MALLOC_CHECK_` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_malloc_check_env_gate` to assert `--skip-release-gate-malloc-check-env-check` disables the gate for emergency recovery.
- Added `TP-E13-49` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only with malloc-check-env gate example: `python scripts/run_release_switch_validation.py --decision-only --python "env MALLOC_CHECK_=3 python3" --doc-sync-report docs/current/status/baselines/e13-doc-sync-check-report.json --quality-report docs/current/status/baselines/e11-quality-regression-report.json --perf-report docs/current/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/current/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/current/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/current/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/current/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/current/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-50 Additions

- Extended `scripts/run_release_switch_validation.py` with release-gate malloc-perturb-env gate: decision now rejects `MALLOC_PERTURB_=*` assignments in stage launchers and `--python` relay values before allowing `GO`.
- Updated `tests/test_release_switch_validation_script.py` malloc wildcard gate fixtures to use unknown `MALLOC_SHADOW_POLICY=*` so wildcard coverage stays focused on unknown keys after `MALLOC_ARENA_MAX` becomes a dedicated gate.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_malloc_perturb_env_assignment` to assert `MALLOC_PERTURB_` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_malloc_perturb_env_gate` to assert `--skip-release-gate-malloc-perturb-env-check` disables the gate for emergency recovery.
- Added `TP-E13-50` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only with malloc-perturb-env gate example: `python scripts/run_release_switch_validation.py --decision-only --python "env MALLOC_PERTURB_=153 python3" --doc-sync-report docs/current/status/baselines/e13-doc-sync-check-report.json --quality-report docs/current/status/baselines/e11-quality-regression-report.json --perf-report docs/current/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/current/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/current/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/current/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/current/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/current/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-51 Additions

- Extended `scripts/run_release_switch_validation.py` with release-gate malloc-arena-max-env gate: decision now rejects `MALLOC_ARENA_MAX=*` assignments in stage launchers and `--python` relay values before allowing `GO`.
- Updated `tests/test_release_switch_validation_script.py` malloc wildcard gate fixtures to use unknown `MALLOC_SHADOW_POLICY=*` so wildcard coverage remains unknown-key focused after `MALLOC_ARENA_MAX` becomes a dedicated gate.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_malloc_arena_max_env_assignment` to assert `MALLOC_ARENA_MAX` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_malloc_arena_max_env_gate` to assert `--skip-release-gate-malloc-arena-max-env-check` disables the gate for emergency recovery.
- Added `TP-E13-51` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only with malloc-arena-max-env gate example: `python scripts/run_release_switch_validation.py --decision-only --python "env MALLOC_ARENA_MAX=8 python3" --doc-sync-report docs/current/status/baselines/e13-doc-sync-check-report.json --quality-report docs/current/status/baselines/e11-quality-regression-report.json --perf-report docs/current/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/current/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/current/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/current/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/current/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/current/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-53 Additions

- Extended `scripts/run_release_switch_validation.py` with release-gate malloc-mmap-max-env gate: decision now rejects `MALLOC_MMAP_MAX_=*` assignments in stage launchers and `--python` relay values before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_malloc_mmap_max_env_assignment` to assert `MALLOC_MMAP_MAX_` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_malloc_mmap_max_env_gate` to assert `--skip-release-gate-malloc-mmap-max-env-check` disables the gate for emergency recovery.
- Added `TP-E13-53` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only with malloc-mmap-max-env gate example: `python scripts/run_release_switch_validation.py --decision-only --python "env MALLOC_MMAP_MAX_=256 python3" --doc-sync-report docs/current/status/baselines/e13-doc-sync-check-report.json --quality-report docs/current/status/baselines/e11-quality-regression-report.json --perf-report docs/current/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/current/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/current/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/current/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/current/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/current/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-54 Additions

- Extended `scripts/run_release_switch_validation.py` with release-gate malloc-top-pad-env gate: decision now rejects `MALLOC_TOP_PAD_=*` assignments in stage launchers and `--python` relay values before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_malloc_top_pad_env_assignment` to assert `MALLOC_TOP_PAD_` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_malloc_top_pad_env_gate` to assert `--skip-release-gate-malloc-top-pad-env-check` disables the gate for emergency recovery.
- Added `TP-E13-54` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only with malloc-top-pad-env gate example: `python scripts/run_release_switch_validation.py --decision-only --python "env MALLOC_TOP_PAD_=131072 python3" --doc-sync-report docs/current/status/baselines/e13-doc-sync-check-report.json --quality-report docs/current/status/baselines/e11-quality-regression-report.json --perf-report docs/current/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/current/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/current/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/current/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/current/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/current/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-55 Additions

- Extended `scripts/run_release_switch_validation.py` with release-gate malloc-trim-threshold-env gate: decision now rejects `MALLOC_TRIM_THRESHOLD_=*` assignments in stage launchers and `--python` relay values before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_malloc_trim_threshold_env_assignment` to assert `MALLOC_TRIM_THRESHOLD_` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_malloc_trim_threshold_env_gate` to assert `--skip-release-gate-malloc-trim-threshold-env-check` disables the gate for emergency recovery.
- Added `TP-E13-55` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only with malloc-trim-threshold-env gate example: `python scripts/run_release_switch_validation.py --decision-only --python "env MALLOC_TRIM_THRESHOLD_=262144 python3" --doc-sync-report docs/current/status/baselines/e13-doc-sync-check-report.json --quality-report docs/current/status/baselines/e11-quality-regression-report.json --perf-report docs/current/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/current/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/current/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/current/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/current/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/current/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-56 Additions

- Extended `scripts/run_release_switch_validation.py` with release-gate malloc-arena-test-env gate: decision now rejects `MALLOC_ARENA_TEST=*` assignments in stage launchers and `--python` relay values before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_malloc_arena_test_env_assignment` to assert `MALLOC_ARENA_TEST` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_malloc_arena_test_env_gate` to assert `--skip-release-gate-malloc-arena-test-env-check` disables the gate for emergency recovery.
- Added `TP-E13-56` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only with malloc-arena-test-env gate example: `python scripts/run_release_switch_validation.py --decision-only --python "env MALLOC_ARENA_TEST=16 python3" --doc-sync-report docs/current/status/baselines/e13-doc-sync-check-report.json --quality-report docs/current/status/baselines/e11-quality-regression-report.json --perf-report docs/current/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/current/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/current/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/current/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/current/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/current/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-57 Additions

- Extended `scripts/run_release_switch_validation.py` with release-gate malloc-per-thread-env gate: decision now rejects `MALLOC_PER_THREAD=*` assignments in stage launchers and `--python` relay values before allowing `GO`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_holds_when_release_gate_stage_uses_malloc_per_thread_env_assignment` to assert `MALLOC_PER_THREAD` env assignments force `HOLD`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_can_disable_release_gate_malloc_per_thread_env_gate` to assert `--skip-release-gate-malloc-per-thread-env-check` disables the gate for emergency recovery.
- Added `TP-E13-57` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only with malloc-per-thread-env gate example: `python scripts/run_release_switch_validation.py --decision-only --python "env MALLOC_PER_THREAD=1 python3" --doc-sync-report docs/current/status/baselines/e13-doc-sync-check-report.json --quality-report docs/current/status/baselines/e11-quality-regression-report.json --perf-report docs/current/status/baselines/e11-perf-cost-baseline-report.json --postgres-soak-benchmark-report docs/current/status/baselines/e13-postgres-soak-benchmark-report.json --beta-suite-output docs/current/status/baselines/e13-release-gate-beta-suite-plan.json --ga-suite-output docs/current/status/baselines/e13-release-gate-ga-suite-plan.json --roadmap-suite-output docs/current/status/baselines/e13-release-gate-roadmap-suite-plan.json --release-gate-output docs/current/status/baselines/e13-release-gate-validation-plan.json --decision-output docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-58 Additions

- Extended `scripts/run_release_switch_validation.py` with `bulk_strategy_view` projection in decision JSON to support large-scale analytics without depending on ever-growing flat `evidence_summary` keys.
- `bulk_strategy_view` now emits stable aggregation fields: `schema_version`, `decision`, `gate_count`, `pass_count`, `hold_count`, `gate_status_bitmap`, `gate_status_index`, `gate_rows`, `check_enablement`, `evidence_status_counts`, and `evidence_freshness_counts`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_view_for_go_decision` for GO-path schema + consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_view_for_hold_decision` for HOLD-path schema + gate-index consistency checks.
- Added `TP-E13-58` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only sample remains unchanged; parse `bulk_strategy_view` from the same decision artifact: `docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-59 Additions

- Upgraded `bulk_strategy_view` to `release_switch_bulk_strategy.v2` for high-volume analytics rollups.
- Added deterministic aggregation keys for strategy clustering: `decision_code`, `hold_signature`, `pass_gate_indices`, `hold_gate_indices`, `gate_domain_index`, and `domain_rollup`.
- `domain_rollup` now exports per-domain `gate_count/pass_count/hold_count/pass_ratio` for direct group-by aggregation without scanning raw gate text.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_domain_rollup_for_go_decision` to validate GO-path signature and domain rollup consistency.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_domain_rollup_for_hold_decision` to validate HOLD-path signature, index vectors, and domain hold counts.
- Added `TP-E13-59` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `bulk_strategy_view` v2 from `docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-60 Additions

- Extended `scripts/run_release_switch_validation.py` with deterministic bulk signature digests: `hold_signature_sha256` and `strategy_signature_sha256`.
- `hold_signature_sha256` now pins `sha256(hold_signature)` for fixed-width signature indexing.
- `strategy_signature_sha256` now pins a canonical digest over `decision/gate_status_bitmap/pass_gate_indices/hold_gate_indices/check_enablement.enabled_keys/check_enablement.disabled_keys`.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_signature_hash_for_go_decision` for GO-path signature-digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_signature_hash_for_hold_decision` for HOLD-path signature-digest consistency checks.
- Added `TP-E13-60` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only sample remains unchanged; consume new hash fields from `docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-61 Additions

- Extended `scripts/run_release_switch_validation.py` with deterministic domain-rollup digest: `domain_rollup_sha256`.
- `domain_rollup_sha256` now pins a canonical digest over `decision/domain_rollup/gate_domain_index`, enabling fixed-width indexing for domain-level aggregation profiles.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_domain_rollup_hash_for_go_decision` for GO-path domain-rollup digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_domain_rollup_hash_for_hold_decision` for HOLD-path domain-rollup digest consistency checks.
- Added `TP-E13-61` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `domain_rollup_sha256` from `docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-62 Additions

- Extended `scripts/run_release_switch_validation.py` with deterministic evidence-profile digest: `evidence_profile_sha256`.
- `evidence_profile_sha256` now pins a canonical digest over `decision/evidence_file_count/evidence_status_counts/evidence_freshness_counts`, enabling fixed-width indexing for evidence-state aggregation profiles.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_evidence_profile_hash_for_go_decision` for GO-path evidence-profile digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_evidence_profile_hash_for_hold_decision` for HOLD-path evidence-profile digest consistency checks.
- Added `TP-E13-62` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `evidence_profile_sha256` from `docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-63 Additions

- Extended `scripts/run_release_switch_validation.py` with deterministic gate-status-index digest: `gate_status_index_sha256`.
- `gate_status_index_sha256` now pins a canonical digest over `decision/gate_names/gate_status_bitmap/gate_status_index`, enabling fixed-width indexing for gate-matrix aggregation profiles.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_gate_status_index_hash_for_go_decision` for GO-path gate-status-index digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_gate_status_index_hash_for_hold_decision` for HOLD-path gate-status-index digest consistency checks.
- Added `TP-E13-63` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `gate_status_index_sha256` from `docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-64 Additions

- Extended `scripts/run_release_switch_validation.py` with deterministic composite-profile digest: `composite_profile_sha256`.
- `composite_profile_sha256` now pins a canonical digest over `decision/hold_signature_sha256/strategy_signature_sha256/domain_rollup_sha256/evidence_profile_sha256/gate_status_index_sha256`, enabling one-key indexing for cross-dimension strategy profiles.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_composite_profile_hash_for_go_decision` for GO-path composite-profile digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_composite_profile_hash_for_hold_decision` for HOLD-path composite-profile digest consistency checks.
- Added `TP-E13-64` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `composite_profile_sha256` from `docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-65 Additions

- Extended `scripts/run_release_switch_validation.py` with deterministic strategy-envelope digest: `strategy_envelope_sha256`.
- `strategy_envelope_sha256` now pins a canonical digest over `decision/decision_code/gate_count/pass_count/hold_count/evidence_file_count/hold_signature_sha256/strategy_signature_sha256/domain_rollup_sha256/evidence_profile_sha256/gate_status_index_sha256/composite_profile_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_envelope_hash_for_go_decision` for GO-path strategy-envelope digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_envelope_hash_for_hold_decision` for HOLD-path strategy-envelope digest consistency checks.
- Added `TP-E13-65` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `strategy_envelope_sha256` from `docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-66 Additions

- Extended `scripts/run_release_switch_validation.py` with deterministic contract-signature digest: `contract_signature_sha256`.
- `contract_signature_sha256` now pins a canonical digest over `schema_version/decision/decision_code/gate_names/gate_domain_index/check_enablement.enabled_keys/check_enablement.disabled_keys/strategy_envelope_sha256`, enabling one-key contract drift detection across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_contract_signature_hash_for_go_decision` for GO-path contract-signature digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_contract_signature_hash_for_hold_decision` for HOLD-path contract-signature digest consistency checks.
- Added `TP-E13-66` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `contract_signature_sha256` from `docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-67 Additions

- Extended `scripts/run_release_switch_validation.py` with deterministic contract-envelope digest: `contract_envelope_sha256`.
- `contract_envelope_sha256` now pins a canonical digest over `schema_version/decision/decision_code/gate_count/pass_count/hold_count/evidence_file_count/contract_signature_sha256/strategy_envelope_sha256/composite_profile_sha256`, enabling one-key contract+posture reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_contract_envelope_hash_for_go_decision` for GO-path contract-envelope digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_contract_envelope_hash_for_hold_decision` for HOLD-path contract-envelope digest consistency checks.
- Added `TP-E13-67` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `contract_envelope_sha256` from `docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-68 Additions

- Extended `scripts/run_release_switch_validation.py` with deterministic release-fingerprint digest: `release_fingerprint_sha256`.
- `release_fingerprint_sha256` now pins a canonical digest over `schema_version/decision/decision_code/gate_count/pass_count/hold_count/evidence_file_count/hold_signature_sha256/strategy_envelope_sha256/contract_signature_sha256/contract_envelope_sha256/composite_profile_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key release-level reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_fingerprint_hash_for_go_decision` for GO-path release-fingerprint digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_fingerprint_hash_for_hold_decision` for HOLD-path release-fingerprint digest consistency checks.
- Added `TP-E13-68` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_fingerprint_sha256` from `docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-69 Additions

- Extended `scripts/run_release_switch_validation.py` with deterministic release-manifest digest: `release_manifest_sha256`.
- `release_manifest_sha256` now pins a canonical digest over `schema_version/decision/decision_code/gate_names/gate_status_bitmap/gate_domain_index/domain_rollup_sha256/evidence_profile_sha256/release_fingerprint_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key release-manifest replay/reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_manifest_hash_for_go_decision` for GO-path release-manifest digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_manifest_hash_for_hold_decision` for HOLD-path release-manifest digest consistency checks.
- Added `TP-E13-69` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_manifest_sha256` from `docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-70 Additions

- Extended `scripts/run_release_switch_validation.py` with deterministic release-root digest: `release_root_sha256`.
- `release_root_sha256` now pins a canonical digest over `schema_version/decision/decision_code/gate_count/pass_count/hold_count/evidence_file_count/hold_signature_sha256/strategy_signature_sha256/domain_rollup_sha256/evidence_profile_sha256/gate_status_index_sha256/composite_profile_sha256/strategy_envelope_sha256/contract_signature_sha256/contract_envelope_sha256/release_fingerprint_sha256/release_manifest_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key release posture reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_root_hash_for_go_decision` for GO-path release-root digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_root_hash_for_hold_decision` for HOLD-path release-root digest consistency checks.
- Added `TP-E13-70` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_root_sha256` from `docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-71 Additions

- Extended `scripts/run_release_switch_validation.py` with deterministic release-attestation digest: `release_attestation_sha256`.
- `release_attestation_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/hold_signature_sha256/strategy_signature_sha256/gate_status_bitmap/gate_status_index_sha256/domain_rollup_sha256/evidence_profile_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key release attestation/reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_attestation_hash_for_go_decision` for GO-path release-attestation digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_attestation_hash_for_hold_decision` for HOLD-path release-attestation digest consistency checks.
- Added `TP-E13-71` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_attestation_sha256` from `docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-72 Additions

- Extended `scripts/run_release_switch_validation.py` with deterministic release-verdict digest: `release_verdict_sha256`.
- `release_verdict_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/strategy_envelope_sha256/contract_envelope_sha256/composite_profile_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key verdict/reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_verdict_hash_for_go_decision` for GO-path release-verdict digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_verdict_hash_for_hold_decision` for HOLD-path release-verdict digest consistency checks.
- Added `TP-E13-72` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_verdict_sha256` from `docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-73 Additions

- Extended `scripts/run_release_switch_validation.py` with deterministic release-lineage digest: `release_lineage_sha256`.
- `release_lineage_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/hold_signature_sha256/strategy_signature_sha256/domain_rollup_sha256/evidence_profile_sha256/gate_status_index_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key release lineage replay/reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_lineage_hash_for_go_decision` for GO-path release-lineage digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_lineage_hash_for_hold_decision` for HOLD-path release-lineage digest consistency checks.
- Added `TP-E13-73` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_lineage_sha256` from `docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-74 Additions

- Extended `scripts/run_release_switch_validation.py` with deterministic release-capsule digest: `release_capsule_sha256`.
- `release_capsule_sha256` now pins a canonical digest over `schema_version/decision/decision_code/gate_count/pass_count/hold_count/evidence_file_count/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key compact release reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_capsule_hash_for_go_decision` for GO-path release-capsule digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_capsule_hash_for_hold_decision` for HOLD-path release-capsule digest consistency checks.
- Added `TP-E13-74` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_capsule_sha256` from `docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-75 Additions

- Extended `scripts/run_release_switch_validation.py` with deterministic release-anchor digest: `release_anchor_sha256`.
- `release_anchor_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key anchored release reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_anchor_hash_for_go_decision` for GO-path release-anchor digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_anchor_hash_for_hold_decision` for HOLD-path release-anchor digest consistency checks.
- Added `TP-E13-75` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_anchor_sha256` from `docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-76 Additions

- Extended `scripts/run_release_switch_validation.py` with deterministic release-beacon digest: `release_beacon_sha256`.
- `release_beacon_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key beaconed release routing/reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_beacon_hash_for_go_decision` for GO-path release-beacon digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_beacon_hash_for_hold_decision` for HOLD-path release-beacon digest consistency checks.
- Added `TP-E13-76` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_beacon_sha256` from `docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-77 Additions

- Extended `scripts/run_release_switch_validation.py` with deterministic release-constellation digest: `release_constellation_sha256`.
- `release_constellation_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key constellation routing/reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_constellation_hash_for_go_decision` for GO-path release-constellation digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_constellation_hash_for_hold_decision` for HOLD-path release-constellation digest consistency checks.
- Added `TP-E13-77` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_constellation_sha256` from `docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-78 Additions

- Extended `scripts/run_release_switch_validation.py` with deterministic release-galaxy digest: `release_galaxy_sha256`.
- `release_galaxy_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key galaxy routing/reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_galaxy_hash_for_go_decision` for GO-path release-galaxy digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_galaxy_hash_for_hold_decision` for HOLD-path release-galaxy digest consistency checks.
- Added `TP-E13-78` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_galaxy_sha256` from `docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-79 Additions

- Extended `scripts/run_release_switch_validation.py` with deterministic release-universe digest: `release_universe_sha256`.
- `release_universe_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key universe routing/reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_universe_hash_for_go_decision` for GO-path release-universe digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_universe_hash_for_hold_decision` for HOLD-path release-universe digest consistency checks.
- Added `TP-E13-79` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_universe_sha256` from `docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-80 Additions

- Extended `scripts/run_release_switch_validation.py` with deterministic release-multiverse digest: `release_multiverse_sha256`.
- `release_multiverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key multiverse routing/reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_multiverse_hash_for_go_decision` for GO-path release-multiverse digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_multiverse_hash_for_hold_decision` for HOLD-path release-multiverse digest consistency checks.
- Added `TP-E13-80` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_multiverse_sha256` from `docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-81 Additions

- Extended `scripts/run_release_switch_validation.py` with deterministic release-omniverse digest: `release_omniverse_sha256`.
- `release_omniverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key omniverse routing/reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_omniverse_hash_for_go_decision` for GO-path release-omniverse digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_omniverse_hash_for_hold_decision` for HOLD-path release-omniverse digest consistency checks.
- Added `TP-E13-81` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_omniverse_sha256` from `docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-82 Additions

- Extended `scripts/run_release_switch_validation.py` with deterministic release-hyperverse digest: `release_hyperverse_sha256`.
- `release_hyperverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key hyperverse routing/reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_hyperverse_hash_for_go_decision` for GO-path release-hyperverse digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_hyperverse_hash_for_hold_decision` for HOLD-path release-hyperverse digest consistency checks.
- Added `TP-E13-82` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_hyperverse_sha256` from `docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-83 Additions

- Extended `scripts/run_release_switch_validation.py` with deterministic release-megaverse digest: `release_megaverse_sha256`.
- `release_megaverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key megaverse routing/reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_megaverse_hash_for_go_decision` for GO-path release-megaverse digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_megaverse_hash_for_hold_decision` for HOLD-path release-megaverse digest consistency checks.
- Added `TP-E13-83` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_megaverse_sha256` from `docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-84 Additions

- Extended `scripts/run_release_switch_validation.py` with deterministic release-gigaverse digest: `release_gigaverse_sha256`.
- `release_gigaverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key gigaverse routing/reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_gigaverse_hash_for_go_decision` for GO-path release-gigaverse digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_gigaverse_hash_for_hold_decision` for HOLD-path release-gigaverse digest consistency checks.
- Added `TP-E13-84` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_gigaverse_sha256` from `docs/current/status/baselines/e13-release-switch-decision-report.json`.

## TP-E13-85 Additions

- Extended `scripts/run_release_switch_validation.py` with deterministic release-teraverse digest: `release_teraverse_sha256`.
- `release_teraverse_sha256` now pins a canonical digest over `schema_version/decision/decision_code/release_gigaverse_sha256/release_megaverse_sha256/release_hyperverse_sha256/release_omniverse_sha256/release_multiverse_sha256/release_universe_sha256/release_galaxy_sha256/release_constellation_sha256/release_beacon_sha256/release_anchor_sha256/release_capsule_sha256/release_lineage_sha256/release_verdict_sha256/release_attestation_sha256/release_root_sha256/release_manifest_sha256/release_fingerprint_sha256/contract_envelope_sha256/strategy_envelope_sha256/gate_status_index_sha256/composite_profile_sha256/domain_rollup_sha256/evidence_profile_sha256/hold_signature_sha256/strategy_signature_sha256/check_enablement.enabled_keys/check_enablement.disabled_keys`, enabling one-key teraverse routing/reconciliation across decision batches.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_teraverse_hash_for_go_decision` for GO-path release-teraverse digest consistency checks.
- Added `tests/test_release_switch_validation_script.py::test_script_decision_only_emits_bulk_strategy_release_teraverse_hash_for_hold_decision` for HOLD-path release-teraverse digest consistency checks.
- Added `TP-E13-85` mapping in `scripts/run_tp_tests.py`.
- Linux decision-only sample remains unchanged; consume `release_teraverse_sha256` from `docs/current/status/baselines/e13-release-switch-decision-report.json`.
