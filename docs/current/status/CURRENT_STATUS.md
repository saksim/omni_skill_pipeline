# Current Status

## 判词

当前项目的主判断、GLM 对比、上线缺口与任务卡，统一以 [launch-readiness-master-plan.md](launch-readiness-master-plan.md) 为准。

## 当前入口

- 上线整合总卷: [launch-readiness-master-plan.md](launch-readiness-master-plan.md)
- 历史状态快照: [../../history/status/2026-04-24-current-status-pre-launch-master-plan.md](../../history/status/2026-04-24-current-status-pre-launch-master-plan.md)
- GLM5.1 旧评估归档: [../../history/assessments/2026-04-22-glm-5.1-project-assessment.md](../../history/assessments/2026-04-22-glm-5.1-project-assessment.md)

## 当前结论

- 内网试运行：可用
- 受控外部 Beta：尚需补齐 API、可观测性、发布门禁
- 正式 GA：尚需补齐 worker 语义、repository abstraction、持久层与 review queue

## 下一跳

1. 先读总卷中的功能矩阵
2. 再按任务卡顺序执行 `LC-L1-*`
3. 完成 Beta 阻断项后，再推进 `LC-L2-*`

## TP-E13-03 Release Switch Standard

- Current standard: [v2-release-switch-standard.md](v2-release-switch-standard.md)
- Latest decision snapshot: [../../history/status/2026-04-26-v2-release-switch-standard.md](../../history/status/2026-04-26-v2-release-switch-standard.md)

## TP-E13-05 Postgres Soak Runner

- Runner script: [../../../scripts/run_postgres_soak_validation.py](../../../scripts/run_postgres_soak_validation.py)
- Linux unified suite stage: `postgres_soak` in [../../../scripts/run_linux_validation_suite.py](../../../scripts/run_linux_validation_suite.py)

## TP-E13-06 Worker GA Runner

- Runner script: [../../../scripts/run_worker_ga_validation.py](../../../scripts/run_worker_ga_validation.py)
- Linux unified suite stage: `worker_ga` in [../../../scripts/run_linux_validation_suite.py](../../../scripts/run_linux_validation_suite.py)

## TP-E13-07 Provider GA Runner

- Runner script: [../../../scripts/run_provider_ga_validation.py](../../../scripts/run_provider_ga_validation.py)
- Linux unified suite stage: `provider_ga` in [../../../scripts/run_linux_validation_suite.py](../../../scripts/run_linux_validation_suite.py)

## TP-E13-08 Review Queue GA Runner

- Runner script: [../../../scripts/run_review_queue_ga_validation.py](../../../scripts/run_review_queue_ga_validation.py)
- Linux unified suite stage: `review_queue_ga` in [../../../scripts/run_linux_validation_suite.py](../../../scripts/run_linux_validation_suite.py)

## TP-E13-09 Calibration GA Runner

- Runner script: [../../../scripts/run_calibration_ga_validation.py](../../../scripts/run_calibration_ga_validation.py)
- Linux unified suite stage: `calibration_ga` in [../../../scripts/run_linux_validation_suite.py](../../../scripts/run_linux_validation_suite.py)

## TP-E13-10 Postgres GA Runner

- Runner script: [../../../scripts/run_postgres_ga_validation.py](../../../scripts/run_postgres_ga_validation.py)
- Linux unified suite stage: `postgres_ga` in [../../../scripts/run_linux_validation_suite.py](../../../scripts/run_linux_validation_suite.py)

## TP-E13-11 Roadmap Extension Runner

- Runner script: [../../../scripts/run_roadmap_extension_validation.py](../../../scripts/run_roadmap_extension_validation.py)
- Linux unified suite stage: `roadmap_extension` in [../../../scripts/run_linux_validation_suite.py](../../../scripts/run_linux_validation_suite.py)

## TP-E13-12 Release Gate Runner

- Runner script: [../../../scripts/run_release_gate_validation.py](../../../scripts/run_release_gate_validation.py)
- Stage packs: `beta_gate`, `ga_gate`, `roadmap_gate` (each delegates to [../../../scripts/run_linux_validation_suite.py](../../../scripts/run_linux_validation_suite.py) with curated stage groups)

## TP-E13-13 Release Switch Decision Runner

- Runner script: [../../../scripts/run_release_switch_validation.py](../../../scripts/run_release_switch_validation.py)
- Stage packs: `release_gate`, `release_contract`, `doc_sync`
- Decision output: `docs/current/status/baselines/e13-release-switch-decision-report.json` (`GO` / `HOLD`)

## TP-E13-14 Release Switch Evidence Pack Hardening

- Runner script: [../../../scripts/run_release_switch_validation.py](../../../scripts/run_release_switch_validation.py)
- Decision gate upgrade: `GO` now requires complete release-gate evidence pack (`release-gate` top-level + beta/ga/roadmap suite plans)
- New guard testcase: [../../../tests/test_release_switch_validation_script.py](../../../tests/test_release_switch_validation_script.py) `test_script_decision_only_holds_when_release_gate_pack_evidence_missing`

## TP-E13-15 Release Switch Evidence Freshness Gate

- Runner script: [../../../scripts/run_release_switch_validation.py](../../../scripts/run_release_switch_validation.py)
- Decision gate upgrade: default `--max-evidence-age-hours=24` enforces evidence freshness; stale reports force `HOLD`
- Escape hatch: set `--max-evidence-age-hours 0` to disable freshness gate for manual recovery/forensics runs

## TP-E13-16 Release Switch Future-Skew Gate

- Runner script: [../../../scripts/run_release_switch_validation.py](../../../scripts/run_release_switch_validation.py)
- Decision gate upgrade: default `--max-evidence-future-skew-hours=0.25` enforces future timestamp skew guard; over-skewed evidence forces `HOLD`
- Escape hatch: set `--max-evidence-future-skew-hours 0` to disable future-skew gate for manual recovery/forensics runs

## TP-E13-17 Release Switch Cohort-Skew Gate

- Runner script: [../../../scripts/run_release_switch_validation.py](../../../scripts/run_release_switch_validation.py)
- Decision gate upgrade: default `--max-evidence-cohort-skew-hours=12` enforces evidence cohort consistency; mixed-batch evidence age spread forces `HOLD`
- Escape hatch: set `--max-evidence-cohort-skew-hours 0` to disable cohort-skew gate for manual recovery/forensics runs

## TP-E13-18 Release Switch Output-Binding Gate

- Runner script: [../../../scripts/run_release_switch_validation.py](../../../scripts/run_release_switch_validation.py)
- Decision gate upgrade: default behavior enforces release-gate `beta_gate/ga_gate/roadmap_gate` stage `--output` bindings to exactly match `--beta-suite-output/--ga-suite-output/--roadmap-suite-output`; mismatches force `HOLD`
- Escape hatch: set `--skip-release-gate-output-binding-check` to bypass binding gate for manual recovery/forensics runs
## TP-E13-19 Release Switch Stage-Contract Gate

- Runner script: [../../../scripts/run_release_switch_validation.py](../../../scripts/run_release_switch_validation.py)
- Decision gate upgrade: default behavior enforces release-gate stage commands must stay on `scripts/run_linux_validation_suite.py` and preserve expected `--stages` packs; contract drift forces `HOLD`
- Escape hatch: set `--skip-release-gate-stage-contract-check` to bypass stage-contract gate for manual recovery/forensics runs

## TP-E13-20 Release Switch Option-Override Gate

- Runner script: [../../../scripts/run_release_switch_validation.py](../../../scripts/run_release_switch_validation.py)
- Decision gate upgrade: default behavior enforces each release-gate stage command keeps single `--stages` and `--output` occurrences; repeated options causing override ambiguity force `HOLD`
- Escape hatch: set `--skip-release-gate-option-override-check` to bypass option-override gate for manual recovery/forensics runs

## TP-E13-21 Release Switch Relaxed-Flags Gate

- Runner script: [../../../scripts/run_release_switch_validation.py](../../../scripts/run_release_switch_validation.py)
- Decision gate upgrade: default behavior rejects release-gate stage commands containing relaxed flags (`--allow-regression`, `--no-coverage`, `--container-skip-build`, `--container-skip-run`, `--allow-secondary-failures`); any hit forces `HOLD`
- Escape hatch: set `--skip-release-gate-relaxed-flags-check` to bypass relaxed-flags gate for manual recovery/forensics runs

## TP-E13-22 Release Switch Dry-Run Gate

- Runner script: [../../../scripts/run_release_switch_validation.py](../../../scripts/run_release_switch_validation.py)
- Decision gate upgrade: default behavior rejects release-gate stage commands containing `--dry-run`; any pseudo-execution flag hit forces `HOLD`
- Escape hatch: set `--skip-release-gate-dry-run-check` to bypass dry-run gate for manual recovery/forensics runs

## TP-E13-23 Release Switch Script-Position Gate

- Runner script: [../../../scripts/run_release_switch_validation.py](../../../scripts/run_release_switch_validation.py)
- Decision gate upgrade: default behavior enforces each release-gate stage command executes `scripts/run_linux_validation_suite.py` as the first script token; decoy token-only spoofing forces `HOLD`
- Escape hatch: set `--skip-release-gate-script-position-check` to bypass script-position gate for manual recovery/forensics runs

## TP-E13-24 Release Switch Inline-Exec Gate

- Runner script: [../../../scripts/run_release_switch_validation.py](../../../scripts/run_release_switch_validation.py)
- Decision gate upgrade: default behavior enforces release-gate stage commands cannot include python inline-dispatch flags (`-c`, `-m`, `-`) before the linux-suite script token; bypass attempts force `HOLD`
- Escape hatch: set `--skip-release-gate-inline-exec-check` to bypass inline-exec gate for manual recovery/forensics runs

## TP-E13-25 Release Switch Script-Anchor Gate

- Runner script: [../../../scripts/run_release_switch_validation.py](../../../scripts/run_release_switch_validation.py)
- Decision gate upgrade: default behavior enforces release-gate stage commands resolve the executed linux-suite script token to repository canonical path (`scripts/run_linux_validation_suite.py`); same-name external path spoofing forces `HOLD`
- Escape hatch: set `--skip-release-gate-script-anchor-check` to bypass script-anchor gate for manual recovery/forensics runs

## TP-E13-26 Release Switch Python-Binding Gate

- Runner script: [../../../scripts/run_release_switch_validation.py](../../../scripts/run_release_switch_validation.py)
- Decision gate upgrade: default behavior enforces release-gate stage commands keep `--python` single-occurrence, value-equal to release-switch input `--python`, and launcher-prefix bound to that same value; any python-binding drift forces `HOLD`
- Escape hatch: set `--skip-release-gate-python-binding-check` to bypass python-binding gate for manual recovery/forensics runs

## TP-E13-27 Release Switch Coverage-Floor Gate

- Runner script: [../../../scripts/run_release_switch_validation.py](../../../scripts/run_release_switch_validation.py)
- Decision gate upgrade: default behavior enforces release-gate `beta_gate` keeps `--coverage-fail-under` bound to release-switch input and at/above release floor (`50`); threshold drift/downgrade forces `HOLD`
- Escape hatch: set `--skip-release-gate-coverage-floor-check` to bypass coverage-floor gate for manual recovery/forensics runs

## TP-E13-28 Release Switch Python-Optimization Gate

- Runner script: [../../../scripts/run_release_switch_validation.py](../../../scripts/run_release_switch_validation.py)
- Decision gate upgrade: default behavior rejects release-gate stage launchers containing python optimization flags (`-O`, `-OO`) before the linux-suite script token; assert-bypass launchers force `HOLD`
- Escape hatch: set `--skip-release-gate-python-optimization-check` to bypass python-optimization gate for manual recovery/forensics runs

## TP-E13-29 Release Switch Python-Option Optimization Gate

- Runner script: [../../../scripts/run_release_switch_validation.py](../../../scripts/run_release_switch_validation.py)
- Decision gate upgrade: default behavior rejects release-gate stage `--python` relay values containing optimization flags (`-O`, `-OO`); relay optimization drift now forces `HOLD`
- Escape hatch: set `--skip-release-gate-python-option-optimization-check` to bypass python-option-optimization gate for manual recovery/forensics runs

## TP-E13-30 Release Switch Python-Optimize Env Gate

- Runner script: [../../../scripts/run_release_switch_validation.py](../../../scripts/run_release_switch_validation.py)
- Decision gate upgrade: default behavior rejects `PYTHONOPTIMIZE=*` env assignments in release-gate stage launchers and stage `--python` relay values; env-based assert-bypass drift now forces `HOLD`
- Escape hatch: set `--skip-release-gate-python-optimize-env-check` to bypass python-optimize-env gate for manual recovery/forensics runs

## TP-E13-31 Release Switch Python-Option Inline-Exec Gate

- Runner script: [../../../scripts/run_release_switch_validation.py](../../../scripts/run_release_switch_validation.py)
- Decision gate upgrade: default behavior rejects release-gate stage `--python` relay values containing inline-dispatch flags (`-c`, `-m`, `-`); relay dispatch drift now forces `HOLD`
- Escape hatch: set `--skip-release-gate-python-option-inline-exec-check` to bypass python-option-inline-exec gate for manual recovery/forensics runs

## TP-E13-32 Release Switch Python-Path Env Gate

- Runner script: [../../../scripts/run_release_switch_validation.py](../../../scripts/run_release_switch_validation.py)
- Decision gate upgrade: default behavior rejects `PYTHONPATH=*` env assignments in release-gate stage launchers and stage `--python` relay values; module-resolution redirection drift now forces `HOLD`
- Escape hatch: set `--skip-release-gate-python-path-env-check` to bypass python-path-env gate for manual recovery/forensics runs

## TP-E13-33 Release Switch Python-Home Env Gate

- Runner script: [../../../scripts/run_release_switch_validation.py](../../../scripts/run_release_switch_validation.py)
- Decision gate upgrade: default behavior rejects `PYTHONHOME=*` env assignments in release-gate stage launchers and stage `--python` relay values; runtime-home redirection drift now forces `HOLD`
- Escape hatch: set `--skip-release-gate-python-home-env-check` to bypass python-home-env gate for manual recovery/forensics runs

## TP-E13-34 Release Switch Python-User-Base Env Gate

- Runner script: [../../../scripts/run_release_switch_validation.py](../../../scripts/run_release_switch_validation.py)
- Decision gate upgrade: default behavior rejects `PYTHONUSERBASE=*` env assignments in release-gate stage launchers and stage `--python` relay values; user-site package redirection drift now forces `HOLD`
- Escape hatch: set `--skip-release-gate-python-user-base-env-check` to bypass python-user-base-env gate for manual recovery/forensics runs

## TP-E13-35 Release Switch Python-Breakpoint Env Gate

- Runner script: [../../../scripts/run_release_switch_validation.py](../../../scripts/run_release_switch_validation.py)
- Decision gate upgrade: default behavior rejects `PYTHONBREAKPOINT=*` env assignments in release-gate stage launchers and stage `--python` relay values; breakpoint-dispatch hook drift now forces `HOLD`
- Escape hatch: set `--skip-release-gate-python-breakpoint-env-check` to bypass python-breakpoint-env gate for manual recovery/forensics runs

## TP-E13-36 Release Switch Python-Startup Env Gate

- Runner script: [../../../scripts/run_release_switch_validation.py](../../../scripts/run_release_switch_validation.py)
- Decision gate upgrade: default behavior rejects `PYTHONSTARTUP=*` env assignments in release-gate stage launchers and stage `--python` relay values; startup-hook injection drift now forces `HOLD`
- Escape hatch: set `--skip-release-gate-python-startup-env-check` to bypass python-startup-env gate for manual recovery/forensics runs

## TP-E13-37 Release Switch Python-Inspect Env Gate

- Runner script: [../../../scripts/run_release_switch_validation.py](../../../scripts/run_release_switch_validation.py)
- Decision gate upgrade: default behavior rejects `PYTHONINSPECT=*` env assignments in release-gate stage launchers and stage `--python` relay values; interactive-dispatch drift now forces `HOLD`
- Escape hatch: set `--skip-release-gate-python-inspect-env-check` to bypass python-inspect-env gate for manual recovery/forensics runs

## TP-E13-38 Release Switch Python-Warnings Env Gate

- Runner script: [../../../scripts/run_release_switch_validation.py](../../../scripts/run_release_switch_validation.py)
- Decision gate upgrade: default behavior rejects `PYTHONWARNINGS=*` env assignments in release-gate stage launchers and stage `--python` relay values; warning-filter drift now forces `HOLD`
- Escape hatch: set `--skip-release-gate-python-warnings-env-check` to bypass python-warnings-env gate for manual recovery/forensics runs
