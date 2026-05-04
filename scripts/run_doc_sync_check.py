from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_README_PATH = REPO_ROOT / 'README.md'
DEFAULT_CLI_SOURCE_PATH = REPO_ROOT / 'src' / 'omni_skill_pipeline' / 'cli.py'
DEFAULT_API_SOURCE_PATH = REPO_ROOT / 'src' / 'omni_skill_pipeline' / 'api_app.py'
DEFAULT_WORKER_SOURCE_PATH = REPO_ROOT / 'src' / 'omni_skill_pipeline' / 'worker.py'
DEFAULT_TP_SOURCE_PATH = REPO_ROOT / 'scripts' / 'run_tp_tests.py'
DEFAULT_CLI_DOC_PATH = REPO_ROOT / 'docs' / 'current' / 'operations' / 'cli.md'
DEFAULT_API_DOC_PATH = REPO_ROOT / 'docs' / 'current' / 'operations' / 'api.md'
DEFAULT_WORKER_DOC_PATH = REPO_ROOT / 'docs' / 'current' / 'operations' / 'worker.md'
DEFAULT_TESTING_DOC_PATH = REPO_ROOT / 'docs' / 'current' / 'operations' / 'testing.md'
DEFAULT_ARCH_MIGRATION_DOC_PATH = (
    REPO_ROOT / 'docs' / 'current' / 'architecture' / 'v1-to-v2-migration-guide.md'
)
DEFAULT_OPS_MIGRATION_DOC_PATH = (
    REPO_ROOT / 'docs' / 'current' / 'operations' / 'v1-to-v2-migration-runbook.md'
)
DEFAULT_RELEASE_STANDARD_DOC_PATH = (
    REPO_ROOT / 'docs' / 'current' / 'status' / 'v2-release-switch-standard.md'
)
DEFAULT_RELEASE_HISTORY_DOC_PATH = (
    REPO_ROOT / 'docs' / 'history' / 'status' / '2026-04-26-v2-release-switch-standard.md'
)
DEFAULT_LAUNCH_BETA_RUNBOOK_PATH = (
    REPO_ROOT / 'docs' / 'current' / 'operations' / 'runbooks' / 'launch-beta.md'
)
DEFAULT_DOCKER_ZERO_TO_RELEASE_RUNBOOK_PATH = (
    REPO_ROOT / 'docs' / 'current' / 'operations' / 'runbooks' / 'docker-zero-to-release.md'
)
DEFAULT_OUTPUT_PATH = REPO_ROOT / 'docs' / 'current' / 'status' / 'baselines' / 'e13-doc-sync-check-report.json'

_MARKDOWN_LINK_PATTERN = re.compile(r'\[[^\]]+\]\(([^)]+)\)')
_CLI_COMMAND_PATTERN = re.compile(r"add_parser\('([a-z0-9_-]+)'")
_API_ROUTE_PATTERN = re.compile(r"@app\.(get|post)\('([^']+)'\)")
_WORKER_KIND_PATTERN = re.compile(r"if kind == '([a-z_]+)'")
_TP_ID_PATTERN = re.compile(r'"(TP-E\d{1,2}-\d{2})"\s*:')
_STALE_PENDING_TP_PATTERN = re.compile(r'(?:\u5f85|pending)\s*`?(TP-E\d{1,2}-\d{2})`?', re.IGNORECASE)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Check whether external docs stay in sync with current CLI/API/worker/testing surfaces.',
    )
    parser.add_argument('--readme', default=str(DEFAULT_README_PATH), help='README path.')
    parser.add_argument('--cli-source', default=str(DEFAULT_CLI_SOURCE_PATH), help='CLI source path.')
    parser.add_argument('--api-source', default=str(DEFAULT_API_SOURCE_PATH), help='API source path.')
    parser.add_argument('--worker-source', default=str(DEFAULT_WORKER_SOURCE_PATH), help='Worker source path.')
    parser.add_argument('--tp-source', default=str(DEFAULT_TP_SOURCE_PATH), help='TP mapping source path.')
    parser.add_argument('--cli-doc', default=str(DEFAULT_CLI_DOC_PATH), help='CLI operation doc path.')
    parser.add_argument('--api-doc', default=str(DEFAULT_API_DOC_PATH), help='API operation doc path.')
    parser.add_argument('--worker-doc', default=str(DEFAULT_WORKER_DOC_PATH), help='Worker operation doc path.')
    parser.add_argument('--testing-doc', default=str(DEFAULT_TESTING_DOC_PATH), help='Testing operation doc path.')
    parser.add_argument(
        '--arch-migration-doc',
        default=str(DEFAULT_ARCH_MIGRATION_DOC_PATH),
        help='Architecture migration guide path.',
    )
    parser.add_argument(
        '--ops-migration-doc',
        default=str(DEFAULT_OPS_MIGRATION_DOC_PATH),
        help='Operations migration runbook path.',
    )
    parser.add_argument(
        '--release-standard-doc',
        default=str(DEFAULT_RELEASE_STANDARD_DOC_PATH),
        help='V2 release switch standard doc path.',
    )
    parser.add_argument(
        '--release-history-doc',
        default=str(DEFAULT_RELEASE_HISTORY_DOC_PATH),
        help='Release switch decision history snapshot path.',
    )
    parser.add_argument(
        '--launch-beta-runbook',
        default=str(DEFAULT_LAUNCH_BETA_RUNBOOK_PATH),
        help='Launch-beta runbook path.',
    )
    parser.add_argument(
        '--docker-zero-to-release-runbook',
        default=str(DEFAULT_DOCKER_ZERO_TO_RELEASE_RUNBOOK_PATH),
        help='Docker-first zero-to-release runbook path.',
    )
    parser.add_argument(
        '--output',
        default=str(DEFAULT_OUTPUT_PATH),
        help='Output report JSON path. Use "-" to skip writing file.',
    )
    parser.add_argument('--print-json', action='store_true', help='Print full JSON report.')
    return parser.parse_args()


def _read_utf8(path: Path) -> str:
    return path.read_text(encoding='utf-8')


def _check_required_files(paths: dict[str, Path]) -> dict[str, Any]:
    missing = [name for name, path in paths.items() if not path.is_file()]
    return {
        'name': 'required_files_exist',
        'status': 'pass' if not missing else 'fail',
        'details': {
            'missing': missing,
            'checked': {name: str(path) for name, path in paths.items()},
        },
    }


def _check_readme_links(readme_text: str, *, repo_root: Path) -> dict[str, Any]:
    broken: list[str] = []
    checked_count = 0
    for raw_target in _MARKDOWN_LINK_PATTERN.findall(readme_text):
        target = str(raw_target).strip()
        if not target:
            continue
        if '://' in target:
            continue
        if target.startswith('#'):
            continue
        resolved = (repo_root / target).resolve() if not Path(target).is_absolute() else Path(target)
        checked_count += 1
        if not resolved.exists():
            broken.append(target)
    return {
        'name': 'readme_markdown_links',
        'status': 'pass' if not broken else 'fail',
        'details': {
            'checked_count': checked_count,
            'broken': broken,
        },
    }


def _check_cli_commands(cli_source_text: str, cli_doc_text: str) -> dict[str, Any]:
    commands = sorted(set(_CLI_COMMAND_PATTERN.findall(cli_source_text)))
    missing = [command for command in commands if ('### %s' % command) not in cli_doc_text]
    return {
        'name': 'cli_command_docs',
        'status': 'pass' if not missing else 'fail',
        'details': {
            'commands': commands,
            'missing': missing,
        },
    }


def _check_api_routes(api_source_text: str, api_doc_text: str) -> dict[str, Any]:
    routes = sorted(set((method.upper(), path) for method, path in _API_ROUTE_PATTERN.findall(api_source_text)))
    missing: list[str] = []
    for method, path in routes:
        marker = '`%s %s`' % (method, path)
        if marker not in api_doc_text:
            missing.append('%s %s' % (method, path))
    return {
        'name': 'api_route_docs',
        'status': 'pass' if not missing else 'fail',
        'details': {
            'routes': ['%s %s' % (method, path) for method, path in routes],
            'missing': missing,
        },
    }


def _check_api_ops_contract(api_doc_text: str) -> dict[str, Any]:
    required_sections = [
        '## Health / Readiness',
        '## Authentication',
        '## Rate Limiting',
        '## Error Contract',
    ]
    required_markers = [
        'OMNI_API_KEY',
        'X-API-Key',
        'Authorization: Bearer',
        'Rate limit exceeded.',
        'Retry-After',
        'error.type',
        'error.code',
        'GET /healthz',
        'status":"ready"',
        'status":"degraded"',
    ]
    missing_required_sections = [item for item in required_sections if item not in api_doc_text]
    missing_required_markers = [item for item in required_markers if item not in api_doc_text]
    missing_any = missing_required_sections or missing_required_markers
    return {
        'name': 'api_ops_contract_completeness',
        'status': 'fail' if missing_any else 'pass',
        'details': {
            'missing_required_sections': missing_required_sections,
            'missing_required_markers': missing_required_markers,
        },
    }


def _check_worker_kinds(worker_source_text: str, worker_doc_text: str) -> dict[str, Any]:
    kinds = sorted(set(_WORKER_KIND_PATTERN.findall(worker_source_text)))
    missing = [kind for kind in kinds if ('- `%s`' % kind) not in worker_doc_text]
    return {
        'name': 'worker_kind_docs',
        'status': 'pass' if not missing else 'fail',
        'details': {
            'kinds': kinds,
            'missing': missing,
        },
    }


def _extract_recent_tp_ids(tp_source_text: str) -> list[str]:
    output: list[str] = []
    for tp_id in _TP_ID_PATTERN.findall(tp_source_text):
        match = re.match(r'TP-E(\d{1,2})-(\d{2})', tp_id)
        if match is None:
            continue
        epic = int(match.group(1))
        if epic < 10:
            continue
        output.append(tp_id)
    return sorted(set(output))


def _check_recent_tp_mentions(tp_source_text: str, testing_doc_text: str) -> dict[str, Any]:
    recent_tp_ids = _extract_recent_tp_ids(tp_source_text)
    missing = [tp_id for tp_id in recent_tp_ids if tp_id not in testing_doc_text]
    return {
        'name': 'testing_doc_recent_tp_mentions',
        'status': 'pass' if not missing else 'fail',
        'details': {
            'recent_tp_ids': recent_tp_ids,
            'missing': missing,
        },
    }


def _check_stale_pending_tp_markers(
    tp_source_text: str,
    docs_to_scan: dict[str, str],
) -> dict[str, Any]:
    known_tp_ids = set(_TP_ID_PATTERN.findall(tp_source_text))
    stale_hits: list[dict[str, str]] = []
    for name, text in docs_to_scan.items():
        for match in _STALE_PENDING_TP_PATTERN.finditer(text):
            tp_id = match.group(1)
            if tp_id not in known_tp_ids:
                continue
            stale_hits.append(
                {
                    'doc': name,
                    'tp_id': tp_id,
                    'snippet': match.group(0),
                }
            )
    return {
        'name': 'stale_pending_tp_marker',
        'status': 'pass' if not stale_hits else 'fail',
        'details': {
            'stale_hits': stale_hits,
        },
    }


def _check_migration_guide_completeness(arch_doc_text: str, ops_doc_text: str) -> dict[str, Any]:
    required_arch_headings = [
        '## 3. 迁移步骤',
        '## 4. 回退策略',
        '## 5. 风险清单',
    ]
    required_ops_headings = [
        '## Linux 执行序列',
        '## 回退操作序列',
        '## 风险观察点',
    ]
    required_refs = ['TP-E8-03', 'TP-E10-02']
    required_ops_commands = [
        'python scripts/run_tp_tests.py',
        'python scripts/run_doc_sync_check.py',
    ]

    missing_arch_headings = [item for item in required_arch_headings if item not in arch_doc_text]
    missing_ops_headings = [item for item in required_ops_headings if item not in ops_doc_text]
    merged_text = '%s\n%s' % (arch_doc_text, ops_doc_text)
    missing_refs = [item for item in required_refs if item not in merged_text]
    missing_ops_commands = [item for item in required_ops_commands if item not in ops_doc_text]

    missing_any = (
        missing_arch_headings or missing_ops_headings or missing_refs or missing_ops_commands
    )
    return {
        'name': 'migration_guide_completeness',
        'status': 'fail' if missing_any else 'pass',
        'details': {
            'missing_arch_headings': missing_arch_headings,
            'missing_ops_headings': missing_ops_headings,
            'missing_refs': missing_refs,
            'missing_ops_commands': missing_ops_commands,
        },
    }


def _check_release_switch_standard(standard_doc_text: str, history_doc_text: str) -> dict[str, Any]:
    required_standard_headings = [
        '## 1. Purpose',
        '## 2. Hard Gates',
        '## 3. Evidence Requirements',
        '## 4. Cutover Decision',
        '## 5. Rollback Trigger',
    ]
    required_history_headings = [
        '## Decision Snapshot',
        '## Gate Checklist',
        '## Evidence Links',
        '## Pending Risks',
    ]
    required_gate_markers = [
        'graph_is_source_of_truth',
        'review_queue_operational',
        'publication_view_count>=2',
        'postgres_repository_stable',
        'regression_beats_v1',
    ]
    required_refs = ['TP-E9-03', 'TP-E11-03']
    required_standard_commands = [
        'python scripts/run_tp_tests.py',
        'python scripts/run_doc_sync_check.py',
    ]
    required_history_refs = ['v2-release-switch-standard.md']

    missing_standard_headings = [
        item for item in required_standard_headings if item not in standard_doc_text
    ]
    missing_history_headings = [
        item for item in required_history_headings if item not in history_doc_text
    ]
    missing_gate_markers = [item for item in required_gate_markers if item not in standard_doc_text]
    merged_text = '%s\n%s' % (standard_doc_text, history_doc_text)
    missing_refs = [item for item in required_refs if item not in merged_text]
    missing_standard_commands = [item for item in required_standard_commands if item not in standard_doc_text]
    missing_history_refs = [item for item in required_history_refs if item not in history_doc_text]

    missing_any = (
        missing_standard_headings
        or missing_history_headings
        or missing_gate_markers
        or missing_refs
        or missing_standard_commands
        or missing_history_refs
    )
    return {
        'name': 'release_switch_standard_completeness',
        'status': 'fail' if missing_any else 'pass',
        'details': {
            'missing_standard_headings': missing_standard_headings,
            'missing_history_headings': missing_history_headings,
            'missing_gate_markers': missing_gate_markers,
            'missing_refs': missing_refs,
            'missing_standard_commands': missing_standard_commands,
            'missing_history_refs': missing_history_refs,
        },
    }


def _check_launch_beta_runbook_completeness(launch_beta_runbook_text: str) -> dict[str, Any]:
    required_headings = [
        '## Deploy',
        '## Acceptance',
        '## Log Inspection',
        '## Temp Cleanup',
        '## Rollback',
    ]
    required_markers = [
        'LC-L1-19',
        'python scripts/run_ci.py',
        'python scripts/run_container_smoke.py',
        'docker logs',
        'python scripts/prune_tmp_media.py',
    ]

    missing_required_headings = [
        item for item in required_headings if item not in launch_beta_runbook_text
    ]
    missing_required_markers = [
        item for item in required_markers if item not in launch_beta_runbook_text
    ]
    missing_any = missing_required_headings or missing_required_markers
    return {
        'name': 'launch_beta_runbook_completeness',
        'status': 'fail' if missing_any else 'pass',
        'details': {
            'missing_required_headings': missing_required_headings,
            'missing_required_markers': missing_required_markers,
        },
    }


def _check_docker_zero_to_release_runbook_completeness(
    docker_zero_to_release_runbook_text: str,
) -> dict[str, Any]:
    required_headings = [
        '## Verdict',
        '## Scope',
        '## Host Assumptions',
        '## Python Contract',
        '## Source Bootstrap',
        '## Image Build',
        '## Packaging Artifacts',
        '## Docker-Only Test Gate',
        '## Release Decision',
        '## Code Update Rebuild',
        '## Deploy',
        '## Acceptance',
        '## Observability',
        '## Rollback',
        '## Common Release Scenarios',
        '## From Zero Checklist',
    ]
    required_markers = [
        'Bare Linux',
        'Docker Engine',
        'requires-python = ">=3.11"',
        'python:3.11-slim',
        'Dockerfile.test',
        'tar -czf',
        'docker save',
        'docker load -i',
        'sha256sum -c SHA256SUMS',
        'Code Update Rebuild',
        'git pull --ff-only',
        'docker build --pull -f Dockerfile.test',
        'docker tag "omni-skill-pipeline:${RELEASE_ID}" omni-skill-pipeline:stable',
        'Common Release Scenarios',
        'docker build -f Dockerfile.test -t omni-skill-pipeline:test .',
        'docker build -t omni-skill-pipeline:beta .',
        'docker run --rm',
        'docker run --rm -d',
        '--network host',
        'docker exec omni-skill-beta python --version',
        'docker cp',
        'docker logs',
        'docker rm -f',
        'curl -fsS http://127.0.0.1:8000/healthz',
        'scripts/run_ci.py --python python3 --keep-going',
        'scripts/run_linux_validation_suite.py --python python3 --keep-going',
        'scripts/run_release_switch_validation.py --python python3 --keep-going',
    ]

    missing_required_headings = [
        item for item in required_headings if item not in docker_zero_to_release_runbook_text
    ]
    missing_required_markers = [
        item for item in required_markers if item not in docker_zero_to_release_runbook_text
    ]
    missing_any = missing_required_headings or missing_required_markers
    return {
        'name': 'docker_zero_to_release_runbook_completeness',
        'status': 'fail' if missing_any else 'pass',
        'details': {
            'missing_required_headings': missing_required_headings,
            'missing_required_markers': missing_required_markers,
        },
    }


def _build_report(*, checks: list[dict[str, Any]]) -> dict[str, Any]:
    failed = [check for check in checks if check.get('status') != 'pass']
    return {
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'check_count': len(checks),
        'pass_count': len(checks) - len(failed),
        'failed_count': len(failed),
        'status': 'pass' if not failed else 'fail',
        'failed_checks': [check.get('name') for check in failed],
        'checks': checks,
    }


def _print_summary(report: dict[str, Any]) -> None:
    print(
        'Doc sync checks=%s pass=%s fail=%s'
        % (report['check_count'], report['pass_count'], report['failed_count'])
    )
    if report['failed_checks']:
        print('Failed checks: %s' % ', '.join(report['failed_checks']))
        for check in report['checks']:
            if check.get('status') == 'pass':
                continue
            print('- %s: %s' % (check.get('name'), json.dumps(check.get('details', {}), ensure_ascii=False)))
    else:
        print('All doc sync checks passed.')


def _write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main() -> int:
    args = _parse_args()

    paths = {
        'readme': Path(args.readme).resolve(),
        'cli_source': Path(args.cli_source).resolve(),
        'api_source': Path(args.api_source).resolve(),
        'worker_source': Path(args.worker_source).resolve(),
        'tp_source': Path(args.tp_source).resolve(),
        'cli_doc': Path(args.cli_doc).resolve(),
        'api_doc': Path(args.api_doc).resolve(),
        'worker_doc': Path(args.worker_doc).resolve(),
        'testing_doc': Path(args.testing_doc).resolve(),
        'arch_migration_doc': Path(args.arch_migration_doc).resolve(),
        'ops_migration_doc': Path(args.ops_migration_doc).resolve(),
        'release_standard_doc': Path(args.release_standard_doc).resolve(),
        'release_history_doc': Path(args.release_history_doc).resolve(),
        'launch_beta_runbook': Path(args.launch_beta_runbook).resolve(),
        'docker_zero_to_release_runbook': Path(args.docker_zero_to_release_runbook).resolve(),
    }

    checks: list[dict[str, Any]] = [_check_required_files(paths)]
    if checks[0]['status'] == 'pass':
        readme_text = _read_utf8(paths['readme'])
        cli_source_text = _read_utf8(paths['cli_source'])
        api_source_text = _read_utf8(paths['api_source'])
        worker_source_text = _read_utf8(paths['worker_source'])
        tp_source_text = _read_utf8(paths['tp_source'])
        cli_doc_text = _read_utf8(paths['cli_doc'])
        api_doc_text = _read_utf8(paths['api_doc'])
        worker_doc_text = _read_utf8(paths['worker_doc'])
        testing_doc_text = _read_utf8(paths['testing_doc'])
        arch_migration_doc_text = _read_utf8(paths['arch_migration_doc'])
        ops_migration_doc_text = _read_utf8(paths['ops_migration_doc'])
        release_standard_doc_text = _read_utf8(paths['release_standard_doc'])
        release_history_doc_text = _read_utf8(paths['release_history_doc'])
        launch_beta_runbook_text = _read_utf8(paths['launch_beta_runbook'])
        docker_zero_to_release_runbook_text = _read_utf8(paths['docker_zero_to_release_runbook'])

        checks.extend(
            [
                _check_readme_links(readme_text, repo_root=paths['readme'].parent),
                _check_cli_commands(cli_source_text, cli_doc_text),
                _check_api_routes(api_source_text, api_doc_text),
                _check_api_ops_contract(api_doc_text),
                _check_worker_kinds(worker_source_text, worker_doc_text),
                _check_recent_tp_mentions(tp_source_text, testing_doc_text),
                _check_migration_guide_completeness(arch_migration_doc_text, ops_migration_doc_text),
                _check_release_switch_standard(release_standard_doc_text, release_history_doc_text),
                _check_launch_beta_runbook_completeness(launch_beta_runbook_text),
                _check_docker_zero_to_release_runbook_completeness(docker_zero_to_release_runbook_text),
                _check_stale_pending_tp_markers(
                    tp_source_text,
                    {
                        'README.md': readme_text,
                        'docs/current/operations/api.md': api_doc_text,
                        'docs/current/operations/cli.md': cli_doc_text,
                        'docs/current/operations/worker.md': worker_doc_text,
                        'docs/current/operations/testing.md': testing_doc_text,
                        'docs/current/architecture/v1-to-v2-migration-guide.md': arch_migration_doc_text,
                        'docs/current/operations/v1-to-v2-migration-runbook.md': ops_migration_doc_text,
                        'docs/current/status/v2-release-switch-standard.md': release_standard_doc_text,
                        'docs/history/status/2026-04-26-v2-release-switch-standard.md': release_history_doc_text,
                        'docs/current/operations/runbooks/launch-beta.md': launch_beta_runbook_text,
                        'docs/current/operations/runbooks/docker-zero-to-release.md': (
                            docker_zero_to_release_runbook_text
                        ),
                    },
                ),
            ]
        )

    report = _build_report(checks=checks)
    _print_summary(report)

    output_path = str(args.output or '').strip()
    if output_path and output_path != '-':
        _write_report(Path(output_path).resolve(), report)

    if args.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['failed_count'] == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())

