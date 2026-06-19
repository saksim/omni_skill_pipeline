from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / 'scripts' / 'doc_sync.py'
VALID_ARCH_MIGRATION_DOC = """# V1 -> V2 Migration Guide

## 1. 迁移范围与前置条件

- 保持 CLI/API 外部接口兼容。
- 先完成双写稳定，再执行主链切换。

## 2. 兼容层决策

- 低风险增量继续走 V1 兼容层。
- 新功能优先走 V2 graph 主链。

## 3. 迁移步骤

1. 使用 TP-E8-03 双写路径校验仓储一致性。
2. 使用 TP-E10-02 校验 API V2 输出契约。
3. 切换默认 publication 读取到 V2 graph metadata。

## 4. 回退策略

- 任何异常先切回 V1 兼容渲染层。
- 保留 dual-write，禁止删除既有 artifact key。

## 5. 风险清单

- schema 演进导致旧 artifact 读取失败。
- reviewer 侧仍读取 legacy 字段导致误判。
"""
VALID_OPS_MIGRATION_DOC = """# V1 -> V2 Migration Runbook

## Linux 执行序列

```bash
python scripts/tp_tests.py TP-E8-03 TP-E10-02 TP-E13-02 --python python3
python scripts/doc_sync.py --output docs/working/status/baselines/e13-doc-sync-check-report.json
```

## 回退操作序列

1. 将 worker 发布配置回滚到 V1 兼容模板。
2. 维持 dual-write，仅关闭 V2 默认读取开关。
3. 复核最近 24h artifact 是否均可回放。

## 风险观察点

- publication 视图缺字段时的降级路径是否稳定。
- review queue 消费是否仍可追踪 request_id/trace_id。
"""
VALID_RELEASE_STANDARD_DOC = """# V2 Release Switch Standard

## 1. Purpose

Define objective gates for promoting V2 as the default mainline.

## 2. Hard Gates

- `graph_is_source_of_truth`: all downstream publications are rendered from SkillGraph metadata.
- `review_queue_operational`: review queue list/claim/close flow is active and traceable.
- `publication_view_count>=2`: markdown + at least one structured publication are both available.
- `postgres_repository_stable`: PostgreSQL repository write/read paths are stable with rollback guard.
- `regression_beats_v1`: baseline regression metrics are not worse than V1.

## 3. Evidence Requirements

- `TP-E9-03` lineage links are persisted and queryable.
- `TP-E11-03` quality regression report is generated with pass status.
- Attach the latest doc-sync report, regression report, and readiness snapshot.

## 4. Cutover Decision

- If all hard gates pass, mark decision as `GO`.
- If any hard gate fails, mark decision as `HOLD` and keep compatibility path enabled.

## 5. Rollback Trigger

- Any regression on traceability or reviewer edit distance after cutover.
- Any sustained repository write/read mismatch in production.

## 6. Command Pack

```bash
python scripts/tp_tests.py TP-E9-03 TP-E11-03 TP-E13-03 --python python3
python scripts/doc_sync.py --output docs/working/status/baselines/e13-doc-sync-check-report.json
```
"""
VALID_RELEASE_HISTORY_DOC = """# 2026-04-26 V2 Release Switch Snapshot

## Decision Snapshot

- Decision: HOLD
- Scope: keep V1 compatibility as default; continue V2 hardening.

## Gate Checklist

- `graph_is_source_of_truth`: pass
- `review_queue_operational`: pass
- `publication_view_count>=2`: pass
- `postgres_repository_stable`: pending long-run soak
- `regression_beats_v1`: pending full Linux regression run

## Evidence Links

- Standard: `docs/releases/standards/v2-release-switch-standard.md`
- TP references: `TP-E9-03`, `TP-E11-03`

## Pending Risks

- Linux long-run benchmark and regression are not yet completed.
- Production-grade cutover rehearsal still pending.
"""
VALID_LAUNCH_BETA_RUNBOOK = """# Launch Beta Runbook

## 判词

本手册用于 `LC-L1-19` 外部 Beta 发布前后操作。

## Deploy

```bash
python scripts/ci.py --coverage-fail-under 50 --coverage-xml coverage.xml
python scripts/container_smoke.py --image-tag omni-skill-pipeline:beta --port 18000
```

## Acceptance

- `GET /healthz` 返回 `200` 且 `status=ready`

## Log Inspection

```bash
docker logs --tail 300 omni-skill-beta
```

## Temp Cleanup

```bash
python scripts/prune_tmp.py --dry-run
```

## Rollback

1. 下线当前 Beta 容器。
2. 启动上一稳定镜像。
"""
VALID_DOCKER_ZERO_TO_RELEASE_RUNBOOK = """# Docker Zero-to-Release Runbook

## Verdict

Bare Linux host starts from Docker Engine only.

## Scope

Use Dockerfile.test and python:3.11-slim for tests and release.

## Host Assumptions

Docker Engine can run docker build, docker run --rm, docker run -d, --network host, docker exec, docker logs, docker cp, docker rm -f.

## Python Contract

pyproject.toml declares requires-python = ">=3.11"; no host Python is required.

## Source Bootstrap

Prepare Dockerfile.test, Dockerfile.test.dockerignore, scripts, tests, docs.

## Image Build

```bash
docker build -f Dockerfile.test -t omni-skill-pipeline:test .
docker build -t omni-skill-pipeline:beta .
```

## Packaging Artifacts

```bash
tar -czf omni-skill-pipeline-source-release.tar.gz .
docker save omni-skill-pipeline:beta -o omni-skill-pipeline-runtime-release.image.tar
docker save omni-skill-pipeline:test -o omni-skill-pipeline-test-release.image.tar
sha256sum -c SHA256SUMS
docker load -i omni-skill-pipeline-runtime-release.image.tar
```

## Docker-Only Test Gate

```bash
docker run --rm omni-skill-pipeline:test python scripts/ci.py --python python3 --keep-going --isolate-test-files
docker run --rm --network host -v /var/run/docker.sock:/var/run/docker.sock omni-skill-pipeline:test python scripts/linux_validate.py --python python3 --keep-going
docker run --rm --network host -v /var/run/docker.sock:/var/run/docker.sock omni-skill-pipeline:test python scripts/release_switch.py --python python3 --keep-going
docker cp omni-release-gate:/app/docs/working/status/baselines ./baselines-from-container
```

## Release Decision

GO can continue; HOLD blocks production promotion.

## Code Update Rebuild

```bash
git pull --ff-only
docker build --pull -f Dockerfile.test -t omni-skill-pipeline:test .
docker tag "omni-skill-pipeline:${RELEASE_ID}" omni-skill-pipeline:stable
```

## Deploy

```bash
docker run -d --name omni-skill-beta -p 8000:8000 omni-skill-pipeline:beta
docker exec omni-skill-beta python --version
curl -fsS http://127.0.0.1:8000/healthz
```

## Acceptance

healthz and auth probes must pass.

## Observability

```bash
docker logs --tail 300 omni-skill-beta
```

## Rollback

```bash
docker rm -f omni-skill-beta
```

## Common Release Scenarios

Common Release Scenarios include first deploy, code update, config update, offline deploy, rebuild, rollback.

## From Zero Checklist

Build test image, package artifacts, docker load image tar, run test gate, deploy runtime image, verify, then rollback if needed.
"""
VALID_PRODUCTION_OPS_RUNBOOK = """# Production Operations Baseline

## Deploy Workflow
docker run --rm -d --name omni-skill-beta omni-skill-pipeline:beta

## Validation Workflow
python scripts/release_gate.py --python python3
python scripts/launch_gate.py --output docs/working/status/baselines/broad-launch-readiness-report.json --summary-output docs/working/status/baselines/broad-launch-readiness-summary.md
python scripts/doc_sync.py --output docs/working/status/baselines/e13-doc-sync-check-report.json
python scripts/ops_evidence.py --output docs/working/status/baselines/operations-readiness-report.json --summary-output docs/working/status/baselines/operations-readiness-summary.md

## Rollback Workflow
docker logs --tail 300 omni-skill-beta

## Backup Workflow
backup

## Restore Workflow
restore

## Incident Response Workflow
incident

## Log Inspection Workflow
docker logs omni-skill-beta

## Alert Workflow
alert

## Evidence Collection Workflow
evidence
"""
VALID_API_OPS_CONTRACT_DOC = """## Health / Readiness

- `GET /healthz`
- Ready response: `200` with `{"status":"ready","checks":[...]}`
- Degraded response: `503` with `{"status":"degraded","checks":[...]}`

## Authentication

- `OMNI_API_KEY`
- `X-API-Key`
- `Authorization: Bearer`

## Rate Limiting

- `Retry-After`
- `Rate limit exceeded.`

## Error Contract

- `error.type`
- `error.code`

## Endpoints

- `GET /healthz`
- `POST /v1/distill/text`
"""


class DocSyncCheckScriptTests(unittest.TestCase):
    def test_docker_zero_to_release_check_reports_missing_markers(self) -> None:
        spec = importlib.util.spec_from_file_location('run_doc_sync_check', SCRIPT_PATH)
        self.assertIsNotNone(spec)
        assert spec is not None
        module = importlib.util.module_from_spec(spec)
        self.assertIsNotNone(spec.loader)
        assert spec.loader is not None
        spec.loader.exec_module(module)

        check = module._check_docker_zero_to_release_runbook_completeness(
            '# Docker Zero-to-Release Runbook\n\n## Deploy\n\nincomplete\n'
        )

        self.assertEqual(check.get('status'), 'fail')
        self.assertEqual(check.get('name'), 'docker_zero_to_release_runbook_completeness')
        self.assertIn('## Host Assumptions', check['details']['missing_required_headings'])
        self.assertIn('Docker Engine', check['details']['missing_required_markers'])

    def test_script_smoke_validates_docs_against_code_surfaces(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            repo_root = tmp_path / 'repo'
            repo_root.mkdir(parents=True, exist_ok=True)

            readme_path = repo_root / 'README.md'
            cli_source_path = repo_root / 'cli.py'
            api_source_path = repo_root / 'api_app.py'
            worker_source_path = repo_root / 'worker.py'
            tp_source_path = repo_root / 'tp_tests.py'
            cli_doc_path = repo_root / 'cli.md'
            api_doc_path = repo_root / 'api.md'
            worker_doc_path = repo_root / 'worker.md'
            testing_doc_path = repo_root / 'testing.md'
            arch_migration_doc_path = repo_root / 'v1-to-v2-migration-guide.md'
            ops_migration_doc_path = repo_root / 'v1-to-v2-migration-runbook.md'
            release_standard_doc_path = repo_root / 'v2-release-switch-standard.md'
            release_history_doc_path = repo_root / '2026-04-26-v2-release-switch-standard.md'
            launch_beta_runbook_path = repo_root / 'launch-beta.md'
            production_ops_runbook_path = repo_root / 'production-operations-baseline.md'
            docker_zero_to_release_runbook_path = repo_root / 'docker-zero-to-release.md'
            output_path = repo_root / 'doc-sync-report.json'

            (repo_root / 'docs').mkdir()
            linked_doc = repo_root / 'docs' / 'index.md'
            linked_doc.write_text('# index\n', encoding='utf-8')

            readme_path.write_text(
                '# README\n\n- [docs](docs/index.md)\n',
                encoding='utf-8',
            )
            cli_source_path.write_text(
                "subparsers.add_parser('distill-text')\nsubparsers.add_parser('show-template')\n",
                encoding='utf-8',
            )
            api_source_path.write_text(
                "@app.get('/healthz')\n@app.post('/v1/distill/text')\n",
                encoding='utf-8',
            )
            worker_source_path.write_text(
                "if kind == 'text':\n    pass\nif kind == 'review_queue':\n    pass\n",
                encoding='utf-8',
            )
            tp_source_path.write_text(
                '"TP-E10-01": [],\n"TP-E13-01": [],\n"TP-E13-02": [],\n"TP-E13-03": [],\n',
                encoding='utf-8',
            )
            cli_doc_path.write_text(
                '### distill-text\n### show-template\n',
                encoding='utf-8',
            )
            api_doc_path.write_text(VALID_API_OPS_CONTRACT_DOC, encoding='utf-8')
            worker_doc_path.write_text(
                '- `text`\n- `review_queue`\n',
                encoding='utf-8',
            )
            testing_doc_path.write_text(
                'TP-E10-01\nTP-E13-01\nTP-E13-02\nTP-E13-03\n',
                encoding='utf-8',
            )
            arch_migration_doc_path.write_text(VALID_ARCH_MIGRATION_DOC, encoding='utf-8')
            ops_migration_doc_path.write_text(VALID_OPS_MIGRATION_DOC, encoding='utf-8')
            release_standard_doc_path.write_text(VALID_RELEASE_STANDARD_DOC, encoding='utf-8')
            release_history_doc_path.write_text(VALID_RELEASE_HISTORY_DOC, encoding='utf-8')
            launch_beta_runbook_path.write_text(VALID_LAUNCH_BETA_RUNBOOK, encoding='utf-8')
            production_ops_runbook_path.write_text(VALID_PRODUCTION_OPS_RUNBOOK, encoding='utf-8')
            docker_zero_to_release_runbook_path.write_text(
                VALID_DOCKER_ZERO_TO_RELEASE_RUNBOOK,
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--readme',
                    str(readme_path),
                    '--cli-source',
                    str(cli_source_path),
                    '--api-source',
                    str(api_source_path),
                    '--worker-source',
                    str(worker_source_path),
                    '--tp-source',
                    str(tp_source_path),
                    '--cli-doc',
                    str(cli_doc_path),
                    '--api-doc',
                    str(api_doc_path),
                    '--worker-doc',
                    str(worker_doc_path),
                    '--testing-doc',
                    str(testing_doc_path),
                    '--arch-migration-doc',
                    str(arch_migration_doc_path),
                    '--ops-migration-doc',
                    str(ops_migration_doc_path),
                    '--release-standard-doc',
                    str(release_standard_doc_path),
                    '--release-history-doc',
                    str(release_history_doc_path),
                    '--launch-beta-runbook',
                    str(launch_beta_runbook_path),
                    '--docker-zero-to-release-runbook',
                    str(docker_zero_to_release_runbook_path),
                    '--production-ops-runbook',
                    str(production_ops_runbook_path),
                    '--output',
                    str(output_path),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Doc sync checks=', completed.stdout)
            self.assertIn('All doc sync checks passed.', completed.stdout)
            report = json.loads(output_path.read_text(encoding='utf-8'))
            self.assertEqual(report.get('status'), 'pass')
            self.assertEqual(report.get('failed_count'), 0)

    def test_script_reports_stale_pending_tp_markers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            repo_root = tmp_path / 'repo'
            repo_root.mkdir(parents=True, exist_ok=True)

            readme_path = repo_root / 'README.md'
            cli_source_path = repo_root / 'cli.py'
            api_source_path = repo_root / 'api_app.py'
            worker_source_path = repo_root / 'worker.py'
            tp_source_path = repo_root / 'tp_tests.py'
            cli_doc_path = repo_root / 'cli.md'
            api_doc_path = repo_root / 'api.md'
            worker_doc_path = repo_root / 'worker.md'
            testing_doc_path = repo_root / 'testing.md'
            arch_migration_doc_path = repo_root / 'v1-to-v2-migration-guide.md'
            ops_migration_doc_path = repo_root / 'v1-to-v2-migration-runbook.md'
            release_standard_doc_path = repo_root / 'v2-release-switch-standard.md'
            release_history_doc_path = repo_root / '2026-04-26-v2-release-switch-standard.md'
            launch_beta_runbook_path = repo_root / 'launch-beta.md'
            production_ops_runbook_path = repo_root / 'production-operations-baseline.md'

            (repo_root / 'docs').mkdir()
            (repo_root / 'docs' / 'index.md').write_text('# index\n', encoding='utf-8')

            readme_path.write_text('# README\n- [docs](docs/index.md)\n', encoding='utf-8')
            cli_source_path.write_text("subparsers.add_parser('distill-text')\n", encoding='utf-8')
            api_source_path.write_text("@app.post('/v1/distill/text')\n", encoding='utf-8')
            worker_source_path.write_text("if kind == 'text':\n    pass\n", encoding='utf-8')
            tp_source_path.write_text('"TP-E10-03": [],\n', encoding='utf-8')
            cli_doc_path.write_text('### distill-text\n', encoding='utf-8')
            api_doc_path.write_text(
                '- `POST /v1/distill/text`\n- worker 任务类型升级仍待 `TP-E10-03`\n',
                encoding='utf-8',
            )
            worker_doc_path.write_text('- `text`\n', encoding='utf-8')
            testing_doc_path.write_text('TP-E10-03\n', encoding='utf-8')
            arch_migration_doc_path.write_text(VALID_ARCH_MIGRATION_DOC, encoding='utf-8')
            ops_migration_doc_path.write_text(VALID_OPS_MIGRATION_DOC, encoding='utf-8')
            release_standard_doc_path.write_text(VALID_RELEASE_STANDARD_DOC, encoding='utf-8')
            release_history_doc_path.write_text(VALID_RELEASE_HISTORY_DOC, encoding='utf-8')
            launch_beta_runbook_path.write_text(VALID_LAUNCH_BETA_RUNBOOK, encoding='utf-8')
            production_ops_runbook_path.write_text(
                '# Production Operations Baseline\n\n## Deploy Workflow\n\nincomplete\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--readme',
                    str(readme_path),
                    '--cli-source',
                    str(cli_source_path),
                    '--api-source',
                    str(api_source_path),
                    '--worker-source',
                    str(worker_source_path),
                    '--tp-source',
                    str(tp_source_path),
                    '--cli-doc',
                    str(cli_doc_path),
                    '--api-doc',
                    str(api_doc_path),
                    '--worker-doc',
                    str(worker_doc_path),
                    '--testing-doc',
                    str(testing_doc_path),
                    '--arch-migration-doc',
                    str(arch_migration_doc_path),
                    '--ops-migration-doc',
                    str(ops_migration_doc_path),
                    '--release-standard-doc',
                    str(release_standard_doc_path),
                    '--release-history-doc',
                    str(release_history_doc_path),
                    '--launch-beta-runbook',
                    str(launch_beta_runbook_path),
                    '--production-ops-runbook',
                    str(production_ops_runbook_path),
                    '--output',
                    '-',
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1)
            self.assertIn('stale_pending_tp_marker', completed.stdout)
            self.assertIn('TP-E10-03', completed.stdout)

    def test_script_reports_incomplete_v1_to_v2_migration_docs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            repo_root = tmp_path / 'repo'
            repo_root.mkdir(parents=True, exist_ok=True)

            readme_path = repo_root / 'README.md'
            cli_source_path = repo_root / 'cli.py'
            api_source_path = repo_root / 'api_app.py'
            worker_source_path = repo_root / 'worker.py'
            tp_source_path = repo_root / 'tp_tests.py'
            cli_doc_path = repo_root / 'cli.md'
            api_doc_path = repo_root / 'api.md'
            worker_doc_path = repo_root / 'worker.md'
            testing_doc_path = repo_root / 'testing.md'
            arch_migration_doc_path = repo_root / 'v1-to-v2-migration-guide.md'
            ops_migration_doc_path = repo_root / 'v1-to-v2-migration-runbook.md'
            release_standard_doc_path = repo_root / 'v2-release-switch-standard.md'
            release_history_doc_path = repo_root / '2026-04-26-v2-release-switch-standard.md'
            launch_beta_runbook_path = repo_root / 'launch-beta.md'
            production_ops_runbook_path = repo_root / 'production-operations-baseline.md'

            (repo_root / 'docs').mkdir()
            (repo_root / 'docs' / 'index.md').write_text('# index\n', encoding='utf-8')

            readme_path.write_text('# README\n- [docs](docs/index.md)\n', encoding='utf-8')
            cli_source_path.write_text("subparsers.add_parser('distill-text')\n", encoding='utf-8')
            api_source_path.write_text("@app.post('/v1/distill/text')\n", encoding='utf-8')
            worker_source_path.write_text("if kind == 'text':\n    pass\n", encoding='utf-8')
            tp_source_path.write_text('"TP-E10-02": [],\n"TP-E13-02": [],\n', encoding='utf-8')
            cli_doc_path.write_text('### distill-text\n', encoding='utf-8')
            api_doc_path.write_text('- `POST /v1/distill/text`\n', encoding='utf-8')
            worker_doc_path.write_text('- `text`\n', encoding='utf-8')
            testing_doc_path.write_text('TP-E10-02\nTP-E13-02\n', encoding='utf-8')
            release_standard_doc_path.write_text(VALID_RELEASE_STANDARD_DOC, encoding='utf-8')
            release_history_doc_path.write_text(VALID_RELEASE_HISTORY_DOC, encoding='utf-8')
            arch_migration_doc_path.write_text(
                '# V1 -> V2 Migration Guide\n\n## 3. 迁移步骤\n\n1. switch\n\n## 4. 回退策略\n\n1. rollback\n',
                encoding='utf-8',
            )
            ops_migration_doc_path.write_text(
                '# V1 -> V2 Migration Runbook\n\n## Linux 执行序列\n\npython scripts/tp_tests.py TP-E13-02 --python python3\n',
                encoding='utf-8',
            )
            launch_beta_runbook_path.write_text(VALID_LAUNCH_BETA_RUNBOOK, encoding='utf-8')
            production_ops_runbook_path.write_text(
                '# Production Operations Baseline\n\n## Deploy Workflow\n\nincomplete\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--readme',
                    str(readme_path),
                    '--cli-source',
                    str(cli_source_path),
                    '--api-source',
                    str(api_source_path),
                    '--worker-source',
                    str(worker_source_path),
                    '--tp-source',
                    str(tp_source_path),
                    '--cli-doc',
                    str(cli_doc_path),
                    '--api-doc',
                    str(api_doc_path),
                    '--worker-doc',
                    str(worker_doc_path),
                    '--testing-doc',
                    str(testing_doc_path),
                    '--arch-migration-doc',
                    str(arch_migration_doc_path),
                    '--ops-migration-doc',
                    str(ops_migration_doc_path),
                    '--release-standard-doc',
                    str(release_standard_doc_path),
                    '--release-history-doc',
                    str(release_history_doc_path),
                    '--launch-beta-runbook',
                    str(launch_beta_runbook_path),
                    '--production-ops-runbook',
                    str(production_ops_runbook_path),
                    '--output',
                    '-',
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1)
            self.assertIn('migration_guide_completeness', completed.stdout)
            self.assertIn('missing_arch_headings', completed.stdout)

    def test_script_reports_incomplete_release_switch_docs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            repo_root = tmp_path / 'repo'
            repo_root.mkdir(parents=True, exist_ok=True)

            readme_path = repo_root / 'README.md'
            cli_source_path = repo_root / 'cli.py'
            api_source_path = repo_root / 'api_app.py'
            worker_source_path = repo_root / 'worker.py'
            tp_source_path = repo_root / 'tp_tests.py'
            cli_doc_path = repo_root / 'cli.md'
            api_doc_path = repo_root / 'api.md'
            worker_doc_path = repo_root / 'worker.md'
            testing_doc_path = repo_root / 'testing.md'
            arch_migration_doc_path = repo_root / 'v1-to-v2-migration-guide.md'
            ops_migration_doc_path = repo_root / 'v1-to-v2-migration-runbook.md'
            release_standard_doc_path = repo_root / 'v2-release-switch-standard.md'
            release_history_doc_path = repo_root / '2026-04-26-v2-release-switch-standard.md'
            launch_beta_runbook_path = repo_root / 'launch-beta.md'
            production_ops_runbook_path = repo_root / 'production-operations-baseline.md'

            (repo_root / 'docs').mkdir()
            (repo_root / 'docs' / 'index.md').write_text('# index\n', encoding='utf-8')

            readme_path.write_text('# README\n- [docs](docs/index.md)\n', encoding='utf-8')
            cli_source_path.write_text("subparsers.add_parser('distill-text')\n", encoding='utf-8')
            api_source_path.write_text("@app.post('/v1/distill/text')\n", encoding='utf-8')
            worker_source_path.write_text("if kind == 'text':\n    pass\n", encoding='utf-8')
            tp_source_path.write_text('"TP-E11-03": [],\n"TP-E13-03": [],\n', encoding='utf-8')
            cli_doc_path.write_text('### distill-text\n', encoding='utf-8')
            api_doc_path.write_text('- `POST /v1/distill/text`\n', encoding='utf-8')
            worker_doc_path.write_text('- `text`\n', encoding='utf-8')
            testing_doc_path.write_text('TP-E11-03\nTP-E13-03\n', encoding='utf-8')
            arch_migration_doc_path.write_text(VALID_ARCH_MIGRATION_DOC, encoding='utf-8')
            ops_migration_doc_path.write_text(VALID_OPS_MIGRATION_DOC, encoding='utf-8')
            release_standard_doc_path.write_text(
                '# V2 Release Switch Standard\n\n## 1. Purpose\n\nincomplete\n',
                encoding='utf-8',
            )
            release_history_doc_path.write_text(
                '# Snapshot\n\n## Decision Snapshot\n\n- HOLD\n',
                encoding='utf-8',
            )
            launch_beta_runbook_path.write_text(VALID_LAUNCH_BETA_RUNBOOK, encoding='utf-8')
            production_ops_runbook_path.write_text(VALID_PRODUCTION_OPS_RUNBOOK, encoding='utf-8')

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--readme',
                    str(readme_path),
                    '--cli-source',
                    str(cli_source_path),
                    '--api-source',
                    str(api_source_path),
                    '--worker-source',
                    str(worker_source_path),
                    '--tp-source',
                    str(tp_source_path),
                    '--cli-doc',
                    str(cli_doc_path),
                    '--api-doc',
                    str(api_doc_path),
                    '--worker-doc',
                    str(worker_doc_path),
                    '--testing-doc',
                    str(testing_doc_path),
                    '--arch-migration-doc',
                    str(arch_migration_doc_path),
                    '--ops-migration-doc',
                    str(ops_migration_doc_path),
                    '--release-standard-doc',
                    str(release_standard_doc_path),
                    '--release-history-doc',
                    str(release_history_doc_path),
                    '--launch-beta-runbook',
                    str(launch_beta_runbook_path),
                    '--production-ops-runbook',
                    str(production_ops_runbook_path),
                    '--output',
                    '-',
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1)
            self.assertIn('release_switch_standard_completeness', completed.stdout)
            self.assertIn('missing_gate_markers', completed.stdout)

    def test_script_reports_incomplete_api_ops_contract_docs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            repo_root = tmp_path / 'repo'
            repo_root.mkdir(parents=True, exist_ok=True)

            readme_path = repo_root / 'README.md'
            cli_source_path = repo_root / 'cli.py'
            api_source_path = repo_root / 'api_app.py'
            worker_source_path = repo_root / 'worker.py'
            tp_source_path = repo_root / 'tp_tests.py'
            cli_doc_path = repo_root / 'cli.md'
            api_doc_path = repo_root / 'api.md'
            worker_doc_path = repo_root / 'worker.md'
            testing_doc_path = repo_root / 'testing.md'
            arch_migration_doc_path = repo_root / 'v1-to-v2-migration-guide.md'
            ops_migration_doc_path = repo_root / 'v1-to-v2-migration-runbook.md'
            release_standard_doc_path = repo_root / 'v2-release-switch-standard.md'
            release_history_doc_path = repo_root / '2026-04-26-v2-release-switch-standard.md'
            launch_beta_runbook_path = repo_root / 'launch-beta.md'
            production_ops_runbook_path = repo_root / 'production-operations-baseline.md'

            (repo_root / 'docs').mkdir()
            (repo_root / 'docs' / 'index.md').write_text('# index\n', encoding='utf-8')

            readme_path.write_text('# README\n- [docs](docs/index.md)\n', encoding='utf-8')
            cli_source_path.write_text("subparsers.add_parser('distill-text')\n", encoding='utf-8')
            api_source_path.write_text(
                "@app.get('/healthz')\n@app.post('/v1/distill/text')\n",
                encoding='utf-8',
            )
            worker_source_path.write_text("if kind == 'text':\n    pass\n", encoding='utf-8')
            tp_source_path.write_text('"TP-E13-01": [],\n', encoding='utf-8')
            cli_doc_path.write_text('### distill-text\n', encoding='utf-8')
            api_doc_path.write_text('- `GET /healthz`\n- `POST /v1/distill/text`\n', encoding='utf-8')
            worker_doc_path.write_text('- `text`\n', encoding='utf-8')
            testing_doc_path.write_text('TP-E13-01\n', encoding='utf-8')
            arch_migration_doc_path.write_text(VALID_ARCH_MIGRATION_DOC, encoding='utf-8')
            ops_migration_doc_path.write_text(VALID_OPS_MIGRATION_DOC, encoding='utf-8')
            release_standard_doc_path.write_text(VALID_RELEASE_STANDARD_DOC, encoding='utf-8')
            release_history_doc_path.write_text(VALID_RELEASE_HISTORY_DOC, encoding='utf-8')
            launch_beta_runbook_path.write_text(VALID_LAUNCH_BETA_RUNBOOK, encoding='utf-8')
            production_ops_runbook_path.write_text(VALID_PRODUCTION_OPS_RUNBOOK, encoding='utf-8')

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--readme',
                    str(readme_path),
                    '--cli-source',
                    str(cli_source_path),
                    '--api-source',
                    str(api_source_path),
                    '--worker-source',
                    str(worker_source_path),
                    '--tp-source',
                    str(tp_source_path),
                    '--cli-doc',
                    str(cli_doc_path),
                    '--api-doc',
                    str(api_doc_path),
                    '--worker-doc',
                    str(worker_doc_path),
                    '--testing-doc',
                    str(testing_doc_path),
                    '--arch-migration-doc',
                    str(arch_migration_doc_path),
                    '--ops-migration-doc',
                    str(ops_migration_doc_path),
                    '--release-standard-doc',
                    str(release_standard_doc_path),
                    '--release-history-doc',
                    str(release_history_doc_path),
                    '--launch-beta-runbook',
                    str(launch_beta_runbook_path),
                    '--production-ops-runbook',
                    str(production_ops_runbook_path),
                    '--output',
                    '-',
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1)
            self.assertIn('api_ops_contract_completeness', completed.stdout)
            self.assertIn('missing_required_sections', completed.stdout)

    def test_script_reports_incomplete_launch_beta_runbook(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            repo_root = tmp_path / 'repo'
            repo_root.mkdir(parents=True, exist_ok=True)

            readme_path = repo_root / 'README.md'
            cli_source_path = repo_root / 'cli.py'
            api_source_path = repo_root / 'api_app.py'
            worker_source_path = repo_root / 'worker.py'
            tp_source_path = repo_root / 'tp_tests.py'
            cli_doc_path = repo_root / 'cli.md'
            api_doc_path = repo_root / 'api.md'
            worker_doc_path = repo_root / 'worker.md'
            testing_doc_path = repo_root / 'testing.md'
            arch_migration_doc_path = repo_root / 'v1-to-v2-migration-guide.md'
            ops_migration_doc_path = repo_root / 'v1-to-v2-migration-runbook.md'
            release_standard_doc_path = repo_root / 'v2-release-switch-standard.md'
            release_history_doc_path = repo_root / '2026-04-26-v2-release-switch-standard.md'
            launch_beta_runbook_path = repo_root / 'launch-beta.md'
            production_ops_runbook_path = repo_root / 'production-operations-baseline.md'

            (repo_root / 'docs').mkdir()
            (repo_root / 'docs' / 'index.md').write_text('# index\n', encoding='utf-8')

            readme_path.write_text('# README\n- [docs](docs/index.md)\n', encoding='utf-8')
            cli_source_path.write_text("subparsers.add_parser('distill-text')\n", encoding='utf-8')
            api_source_path.write_text("@app.post('/v1/distill/text')\n", encoding='utf-8')
            worker_source_path.write_text("if kind == 'text':\n    pass\n", encoding='utf-8')
            tp_source_path.write_text('"TP-E11-03": [],\n"TP-E13-01": [],\n', encoding='utf-8')
            cli_doc_path.write_text('### distill-text\n', encoding='utf-8')
            api_doc_path.write_text('- `POST /v1/distill/text`\n', encoding='utf-8')
            worker_doc_path.write_text('- `text`\n', encoding='utf-8')
            testing_doc_path.write_text('TP-E11-03\nTP-E13-01\n', encoding='utf-8')
            arch_migration_doc_path.write_text(VALID_ARCH_MIGRATION_DOC, encoding='utf-8')
            ops_migration_doc_path.write_text(VALID_OPS_MIGRATION_DOC, encoding='utf-8')
            release_standard_doc_path.write_text(VALID_RELEASE_STANDARD_DOC, encoding='utf-8')
            release_history_doc_path.write_text(VALID_RELEASE_HISTORY_DOC, encoding='utf-8')
            launch_beta_runbook_path.write_text(
                '# Launch Beta Runbook\n\n## Deploy\n\npython scripts/ci.py --coverage-fail-under 50\n',
                encoding='utf-8',
            )
            production_ops_runbook_path.write_text(VALID_PRODUCTION_OPS_RUNBOOK, encoding='utf-8')

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--readme',
                    str(readme_path),
                    '--cli-source',
                    str(cli_source_path),
                    '--api-source',
                    str(api_source_path),
                    '--worker-source',
                    str(worker_source_path),
                    '--tp-source',
                    str(tp_source_path),
                    '--cli-doc',
                    str(cli_doc_path),
                    '--api-doc',
                    str(api_doc_path),
                    '--worker-doc',
                    str(worker_doc_path),
                    '--testing-doc',
                    str(testing_doc_path),
                    '--arch-migration-doc',
                    str(arch_migration_doc_path),
                    '--ops-migration-doc',
                    str(ops_migration_doc_path),
                    '--release-standard-doc',
                    str(release_standard_doc_path),
                    '--release-history-doc',
                    str(release_history_doc_path),
                    '--launch-beta-runbook',
                    str(launch_beta_runbook_path),
                    '--production-ops-runbook',
                    str(production_ops_runbook_path),
                    '--output',
                    '-',
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1)
            self.assertIn('launch_beta_runbook_completeness', completed.stdout)
            self.assertIn('missing_required_headings', completed.stdout)

    def test_script_reports_incomplete_production_ops_runbook(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            repo_root = tmp_path / 'repo'
            repo_root.mkdir(parents=True, exist_ok=True)

            readme_path = repo_root / 'README.md'
            cli_source_path = repo_root / 'cli.py'
            api_source_path = repo_root / 'api_app.py'
            worker_source_path = repo_root / 'worker.py'
            tp_source_path = repo_root / 'tp_tests.py'
            cli_doc_path = repo_root / 'cli.md'
            api_doc_path = repo_root / 'api.md'
            worker_doc_path = repo_root / 'worker.md'
            testing_doc_path = repo_root / 'testing.md'
            arch_migration_doc_path = repo_root / 'v1-to-v2-migration-guide.md'
            ops_migration_doc_path = repo_root / 'v1-to-v2-migration-runbook.md'
            release_standard_doc_path = repo_root / 'v2-release-switch-standard.md'
            release_history_doc_path = repo_root / '2026-04-26-v2-release-switch-standard.md'
            launch_beta_runbook_path = repo_root / 'launch-beta.md'
            production_ops_runbook_path = repo_root / 'production-operations-baseline.md'

            (repo_root / 'docs').mkdir()
            (repo_root / 'docs' / 'index.md').write_text('# index\n', encoding='utf-8')

            readme_path.write_text('# README\n- [docs](docs/index.md)\n', encoding='utf-8')
            cli_source_path.write_text("subparsers.add_parser('distill-text')\n", encoding='utf-8')
            api_source_path.write_text("@app.post('/v1/distill/text')\n", encoding='utf-8')
            worker_source_path.write_text("if kind == 'text':\n    pass\n", encoding='utf-8')
            tp_source_path.write_text('"TP-E11-03": [],\n"TP-E13-01": [],\n', encoding='utf-8')
            cli_doc_path.write_text('### distill-text\n', encoding='utf-8')
            api_doc_path.write_text(VALID_API_OPS_CONTRACT_DOC, encoding='utf-8')
            worker_doc_path.write_text('- `text`\n', encoding='utf-8')
            testing_doc_path.write_text('TP-E11-03\nTP-E13-01\n', encoding='utf-8')
            arch_migration_doc_path.write_text(VALID_ARCH_MIGRATION_DOC, encoding='utf-8')
            ops_migration_doc_path.write_text(VALID_OPS_MIGRATION_DOC, encoding='utf-8')
            release_standard_doc_path.write_text(VALID_RELEASE_STANDARD_DOC, encoding='utf-8')
            release_history_doc_path.write_text(VALID_RELEASE_HISTORY_DOC, encoding='utf-8')
            launch_beta_runbook_path.write_text(VALID_LAUNCH_BETA_RUNBOOK, encoding='utf-8')
            production_ops_runbook_path.write_text(
                '# Production Operations Baseline\n\n## Deploy Workflow\n\nincomplete\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--readme',
                    str(readme_path),
                    '--cli-source',
                    str(cli_source_path),
                    '--api-source',
                    str(api_source_path),
                    '--worker-source',
                    str(worker_source_path),
                    '--tp-source',
                    str(tp_source_path),
                    '--cli-doc',
                    str(cli_doc_path),
                    '--api-doc',
                    str(api_doc_path),
                    '--worker-doc',
                    str(worker_doc_path),
                    '--testing-doc',
                    str(testing_doc_path),
                    '--arch-migration-doc',
                    str(arch_migration_doc_path),
                    '--ops-migration-doc',
                    str(ops_migration_doc_path),
                    '--release-standard-doc',
                    str(release_standard_doc_path),
                    '--release-history-doc',
                    str(release_history_doc_path),
                    '--launch-beta-runbook',
                    str(launch_beta_runbook_path),
                    '--production-ops-runbook',
                    str(production_ops_runbook_path),
                    '--output',
                    '-',
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1)
            self.assertIn('production_ops_runbook_completeness', completed.stdout)
            self.assertIn('missing_required_headings', completed.stdout)


if __name__ == '__main__':
    unittest.main()
