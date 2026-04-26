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
