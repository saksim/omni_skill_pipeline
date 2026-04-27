from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / 'scripts' / 'run_release_switch_validation.py'


def _plan_payload(
    stage_names: list[str],
    *,
    include_command: bool = True,
    stage_output_paths: dict[str, Path] | None = None,
    stage_commands: dict[str, list[str]] | None = None,
) -> dict[str, object]:
    stages: list[dict[str, object]] = []
    for stage_name in stage_names:
        stage_payload: dict[str, object] = {'name': stage_name}
        if include_command:
            command: list[str]
            if stage_commands and stage_name in stage_commands:
                command = list(stage_commands[stage_name])
            else:
                command = ['python3', '-m', 'unittest', stage_name]
                output_path = (stage_output_paths or {}).get(stage_name)
                if output_path is not None:
                    command.extend(['--output', str(output_path.resolve())])
            stage_payload['command'] = command
        stages.append(stage_payload)
    return {
        'stage_count': len(stages),
        'stages': stages,
    }


def _release_gate_stage_contract_commands(
    *,
    beta_output: Path,
    ga_output: Path,
    roadmap_output: Path,
    coverage_fail_under: float = 50.0,
) -> dict[str, list[str]]:
    return {
        'beta_gate': [
            'python3',
            'scripts/run_linux_validation_suite.py',
            '--python',
            'python3',
            '--stages',
            'ci',
            'container_smoke',
            'doc_sync',
            'quality_regression',
            'perf_cost_baseline',
            '--coverage-fail-under',
            str(float(coverage_fail_under)),
            '--output',
            str(beta_output.resolve()),
        ],
        'ga_gate': [
            'python3',
            'scripts/run_linux_validation_suite.py',
            '--python',
            'python3',
            '--stages',
            'postgres_soak',
            'postgres_ga',
            'worker_ga',
            'review_queue_ga',
            'provider_ga',
            'calibration_ga',
            '--output',
            str(ga_output.resolve()),
        ],
        'roadmap_gate': [
            'python3',
            'scripts/run_linux_validation_suite.py',
            '--python',
            'python3',
            '--stages',
            'roadmap_extension',
            '--output',
            str(roadmap_output.resolve()),
        ],
    }


def _write_go_decision_evidence_bundle(tmp_path: Path) -> dict[str, Path]:
    doc_sync_path = tmp_path / 'e13-doc-sync-check-report.json'
    quality_path = tmp_path / 'e11-quality-regression-report.json'
    perf_path = tmp_path / 'e11-perf-cost-baseline-report.json'
    postgres_soak_path = tmp_path / 'e13-postgres-soak-benchmark-report.json'
    beta_suite_path = tmp_path / 'e13-release-gate-beta-suite-plan.json'
    ga_suite_path = tmp_path / 'e13-release-gate-ga-suite-plan.json'
    roadmap_suite_path = tmp_path / 'e13-release-gate-roadmap-suite-plan.json'
    release_gate_path = tmp_path / 'e13-release-gate-validation-plan.json'
    standard_path = tmp_path / 'v2-release-switch-standard.md'
    decision_path = tmp_path / 'release-switch-decision.json'

    doc_sync_path.write_text(
        json.dumps(
            {
                'status': 'pass',
                'failed_count': 0,
                'checks': [
                    {'name': 'release_switch_standard_completeness', 'status': 'pass'},
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + '\n',
        encoding='utf-8',
    )
    quality_path.write_text(
        json.dumps({'regressed_count': 0}, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8',
    )
    perf_path.write_text(
        json.dumps({'regressed_count': 0}, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8',
    )
    postgres_soak_path.write_text(
        json.dumps(
            {
                'run_postgres': True,
                'runs': {
                    'dual_write': {
                        'summary': {'count': 4},
                    }
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + '\n',
        encoding='utf-8',
    )
    beta_suite_path.write_text(
        json.dumps(
            _plan_payload(
                [
                    'ci',
                    'container_smoke',
                    'doc_sync',
                    'quality_regression',
                    'perf_cost_baseline',
                ]
            ),
            ensure_ascii=False,
            indent=2,
        )
        + '\n',
        encoding='utf-8',
    )
    ga_suite_path.write_text(
        json.dumps(
            _plan_payload(
                [
                    'postgres_soak',
                    'postgres_ga',
                    'worker_ga',
                    'provider_ga',
                    'calibration_ga',
                    'review_queue_ga',
                ]
            ),
            ensure_ascii=False,
            indent=2,
        )
        + '\n',
        encoding='utf-8',
    )
    roadmap_suite_path.write_text(
        json.dumps(
            _plan_payload(['roadmap_extension']),
            ensure_ascii=False,
            indent=2,
        )
        + '\n',
        encoding='utf-8',
    )
    release_gate_path.write_text(
        json.dumps(
            _plan_payload(
                ['beta_gate', 'ga_gate', 'roadmap_gate'],
                stage_output_paths={
                    'beta_gate': beta_suite_path,
                    'ga_gate': ga_suite_path,
                    'roadmap_gate': roadmap_suite_path,
                },
                stage_commands=_release_gate_stage_contract_commands(
                    beta_output=beta_suite_path,
                    ga_output=ga_suite_path,
                    roadmap_output=roadmap_suite_path,
                ),
            ),
            ensure_ascii=False,
            indent=2,
        )
        + '\n',
        encoding='utf-8',
    )
    standard_path.write_text(
        '\n'.join(
            [
                '# V2 Release Switch Standard',
                '- graph_is_source_of_truth',
                '- review_queue_operational',
                '- publication_view_count>=2',
                '- postgres_repository_stable',
                '- regression_beats_v1',
            ]
        )
        + '\n',
        encoding='utf-8',
    )

    return {
        'doc_sync_path': doc_sync_path,
        'quality_path': quality_path,
        'perf_path': perf_path,
        'postgres_soak_path': postgres_soak_path,
        'beta_suite_path': beta_suite_path,
        'ga_suite_path': ga_suite_path,
        'roadmap_suite_path': roadmap_suite_path,
        'release_gate_path': release_gate_path,
        'standard_path': standard_path,
        'decision_path': decision_path,
    }


class ReleaseSwitchValidationScriptTests(unittest.TestCase):
    def test_script_dry_run_emits_default_release_switch_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            output_path = tmp_path / 'release-switch-plan.json'
            decision_path = tmp_path / 'release-switch-decision.json'
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--python',
                    'python3',
                    '--dry-run',
                    '--output',
                    str(output_path),
                    '--decision-output',
                    str(decision_path),
                    '--doc-sync-report',
                    str(tmp_path / 'doc-sync-report.json'),
                    '--quality-report',
                    str(tmp_path / 'quality-report.json'),
                    '--perf-report',
                    str(tmp_path / 'perf-report.json'),
                    '--postgres-soak-benchmark-report',
                    str(tmp_path / 'postgres-soak-benchmark-report.json'),
                    '--ga-suite-output',
                    str(tmp_path / 'release-gate-ga-suite-plan.json'),
                    '--release-standard-doc',
                    str(tmp_path / 'v2-release-switch-standard.md'),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Selected stages: release_gate, release_contract, doc_sync', completed.stdout)
            self.assertIn('scripts/run_release_gate_validation.py', completed.stdout)
            self.assertIn('scripts/run_tp_tests.py TP-E9-03 TP-E11-03 TP-E13-03', completed.stdout)
            self.assertIn('scripts/run_doc_sync_check.py', completed.stdout)

            plan = json.loads(output_path.read_text(encoding='utf-8'))
            self.assertEqual(plan.get('stage_count'), 3)
            self.assertEqual(
                [item.get('name') for item in plan.get('stages', [])],
                ['release_gate', 'release_contract', 'doc_sync'],
            )

            decision = json.loads(decision_path.read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            self.assertGreaterEqual(int(decision.get('hold_count', 0)), 1)
            missing = decision.get('missing_or_invalid_evidence', [])
            self.assertTrue(missing)

    def test_script_respects_stage_selection_and_option_forwarding(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                '--python',
                'python3',
                '--stages',
                'release_gate',
                '--coverage-fail-under',
                '72.5',
                '--no-coverage',
                '--allow-regression',
                '--container-image-tag',
                'omni-skill-pipeline:rc',
                '--container-name',
                'omni-release-switch',
                '--container-host',
                '0.0.0.0',
                '--container-port',
                '19090',
                '--container-timeout-seconds',
                '41',
                '--container-interval-seconds',
                '2',
                '--container-skip-build',
                '--postgres-dsn',
                'postgresql://validator',
                '--postgres-soak-iterations',
                '88',
                '--postgres-ga-iterations',
                '99',
                '--allow-secondary-failures',
                '--calibration-margin',
                '0.06',
                '--dry-run',
                '--output',
                '-',
                '--decision-output',
                '-',
            ],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn('Selected stages: release_gate', completed.stdout)
        self.assertIn('--coverage-fail-under 72.5', completed.stdout)
        self.assertIn('--no-coverage', completed.stdout)
        self.assertIn('--allow-regression', completed.stdout)
        self.assertIn('--container-image-tag omni-skill-pipeline:rc', completed.stdout)
        self.assertIn('--container-name omni-release-switch', completed.stdout)
        self.assertIn('--container-host 0.0.0.0', completed.stdout)
        self.assertIn('--container-port 19090', completed.stdout)
        self.assertIn('--container-timeout-seconds 41.0', completed.stdout)
        self.assertIn('--container-interval-seconds 2.0', completed.stdout)
        self.assertIn('--container-skip-build', completed.stdout)
        self.assertIn('--postgres-dsn postgresql://validator', completed.stdout)
        self.assertIn('--postgres-soak-iterations 88', completed.stdout)
        self.assertIn('--postgres-ga-iterations 99', completed.stdout)
        self.assertIn('--allow-secondary-failures', completed.stdout)
        self.assertIn('--calibration-margin 0.06', completed.stdout)
        self.assertNotIn('scripts/run_tp_tests.py', completed.stdout)
        self.assertNotIn('scripts/run_doc_sync_check.py --output', completed.stdout)

    def test_script_decision_only_can_emit_go_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            doc_sync_path = tmp_path / 'e13-doc-sync-check-report.json'
            quality_path = tmp_path / 'e11-quality-regression-report.json'
            perf_path = tmp_path / 'e11-perf-cost-baseline-report.json'
            postgres_soak_path = tmp_path / 'e13-postgres-soak-benchmark-report.json'
            beta_suite_path = tmp_path / 'e13-release-gate-beta-suite-plan.json'
            ga_suite_path = tmp_path / 'e13-release-gate-ga-suite-plan.json'
            roadmap_suite_path = tmp_path / 'e13-release-gate-roadmap-suite-plan.json'
            release_gate_path = tmp_path / 'e13-release-gate-validation-plan.json'
            standard_path = tmp_path / 'v2-release-switch-standard.md'
            decision_path = tmp_path / 'release-switch-decision.json'

            doc_sync_path.write_text(
                json.dumps(
                    {
                        'status': 'pass',
                        'failed_count': 0,
                        'checks': [
                            {'name': 'release_switch_standard_completeness', 'status': 'pass'},
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + '\n',
                encoding='utf-8',
            )
            quality_path.write_text(
                json.dumps({'regressed_count': 0}, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            perf_path.write_text(
                json.dumps({'regressed_count': 0}, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            postgres_soak_path.write_text(
                json.dumps(
                    {
                        'run_postgres': True,
                        'runs': {
                            'dual_write': {
                                'summary': {'count': 4},
                            }
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + '\n',
                encoding='utf-8',
            )
            beta_suite_path.write_text(
                json.dumps(
                    _plan_payload(
                        [
                            'ci',
                            'container_smoke',
                            'doc_sync',
                            'quality_regression',
                            'perf_cost_baseline',
                        ]
                    ),
                    ensure_ascii=False,
                    indent=2,
                )
                + '\n',
                encoding='utf-8',
            )
            ga_suite_path.write_text(
                json.dumps(
                    _plan_payload(
                        [
                            'postgres_soak',
                            'postgres_ga',
                            'worker_ga',
                            'provider_ga',
                            'calibration_ga',
                            'review_queue_ga',
                        ]
                    ),
                    ensure_ascii=False,
                    indent=2,
                )
                + '\n',
                encoding='utf-8',
            )
            roadmap_suite_path.write_text(
                json.dumps(
                    _plan_payload(['roadmap_extension']),
                    ensure_ascii=False,
                    indent=2,
                )
                + '\n',
                encoding='utf-8',
            )
            release_gate_path.write_text(
                json.dumps(
                    _plan_payload(
                        ['beta_gate', 'ga_gate', 'roadmap_gate'],
                        stage_output_paths={
                            'beta_gate': beta_suite_path,
                            'ga_gate': ga_suite_path,
                            'roadmap_gate': roadmap_suite_path,
                        },
                        stage_commands=_release_gate_stage_contract_commands(
                            beta_output=beta_suite_path,
                            ga_output=ga_suite_path,
                            roadmap_output=roadmap_suite_path,
                        ),
                    ),
                    ensure_ascii=False,
                    indent=2,
                )
                + '\n',
                encoding='utf-8',
            )
            standard_path.write_text(
                '\n'.join(
                    [
                        '# V2 Release Switch Standard',
                        '- graph_is_source_of_truth',
                        '- review_queue_operational',
                        '- publication_view_count>=2',
                        '- postgres_repository_stable',
                        '- regression_beats_v1',
                    ]
                )
                + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(doc_sync_path),
                    '--quality-report',
                    str(quality_path),
                    '--perf-report',
                    str(perf_path),
                    '--postgres-soak-benchmark-report',
                    str(postgres_soak_path),
                    '--beta-suite-output',
                    str(beta_suite_path),
                    '--ga-suite-output',
                    str(ga_suite_path),
                    '--roadmap-suite-output',
                    str(roadmap_suite_path),
                    '--release-gate-output',
                    str(release_gate_path),
                    '--release-standard-doc',
                    str(standard_path),
                    '--decision-output',
                    str(decision_path),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(decision_path.read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            self.assertEqual(decision.get('hold_count'), 0)
            self.assertEqual(decision.get('pass_count'), 17)
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_stage_pack_complete'))
            self.assertTrue(summary.get('release_gate_output_binding_pass'))
            self.assertTrue(summary.get('release_gate_stage_contract_pass'))
            self.assertTrue(summary.get('release_gate_script_position_pass'))
            self.assertTrue(summary.get('release_gate_python_binding_pass'))
            self.assertTrue(summary.get('release_gate_python_optimization_pass'))
            self.assertTrue(summary.get('release_gate_coverage_floor_pass'))
            self.assertTrue(summary.get('release_gate_inline_exec_pass'))
            self.assertTrue(summary.get('release_gate_option_override_pass'))
            self.assertTrue(summary.get('release_gate_dry_run_pass'))
            self.assertTrue(summary.get('release_gate_relaxed_flags_pass'))
            self.assertTrue(summary.get('beta_suite_stage_pack_complete'))
            self.assertTrue(summary.get('ga_suite_stage_pack_complete'))
            self.assertTrue(summary.get('roadmap_suite_stage_pack_complete'))
            self.assertTrue(summary.get('evidence_cohort_skew_gate_pass'))

    def test_script_decision_only_holds_when_release_gate_pack_evidence_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            doc_sync_path = tmp_path / 'e13-doc-sync-check-report.json'
            quality_path = tmp_path / 'e11-quality-regression-report.json'
            perf_path = tmp_path / 'e11-perf-cost-baseline-report.json'
            postgres_soak_path = tmp_path / 'e13-postgres-soak-benchmark-report.json'
            beta_suite_path = tmp_path / 'e13-release-gate-beta-suite-plan.json'
            ga_suite_path = tmp_path / 'e13-release-gate-ga-suite-plan.json'
            roadmap_suite_path = tmp_path / 'e13-release-gate-roadmap-suite-plan.json'
            release_gate_path = tmp_path / 'missing-release-gate-plan.json'
            standard_path = tmp_path / 'v2-release-switch-standard.md'
            decision_path = tmp_path / 'release-switch-decision.json'

            doc_sync_path.write_text(
                json.dumps(
                    {
                        'status': 'pass',
                        'failed_count': 0,
                        'checks': [
                            {'name': 'release_switch_standard_completeness', 'status': 'pass'},
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + '\n',
                encoding='utf-8',
            )
            quality_path.write_text(
                json.dumps({'regressed_count': 0}, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            perf_path.write_text(
                json.dumps({'regressed_count': 0}, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            postgres_soak_path.write_text(
                json.dumps(
                    {
                        'run_postgres': True,
                        'runs': {
                            'dual_write': {
                                'summary': {'count': 4},
                            }
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + '\n',
                encoding='utf-8',
            )
            beta_suite_path.write_text(
                json.dumps(
                    _plan_payload(
                        [
                            'ci',
                            'container_smoke',
                            'doc_sync',
                            'quality_regression',
                            'perf_cost_baseline',
                        ]
                    ),
                    ensure_ascii=False,
                    indent=2,
                )
                + '\n',
                encoding='utf-8',
            )
            ga_suite_path.write_text(
                json.dumps(
                    _plan_payload(
                        [
                            'postgres_soak',
                            'postgres_ga',
                            'worker_ga',
                            'review_queue_ga',
                            'provider_ga',
                            'calibration_ga',
                        ]
                    ),
                    ensure_ascii=False,
                    indent=2,
                )
                + '\n',
                encoding='utf-8',
            )
            roadmap_suite_path.write_text(
                json.dumps(
                    _plan_payload(['roadmap_extension']),
                    ensure_ascii=False,
                    indent=2,
                )
                + '\n',
                encoding='utf-8',
            )
            standard_path.write_text(
                '\n'.join(
                    [
                        '# V2 Release Switch Standard',
                        '- graph_is_source_of_truth',
                        '- review_queue_operational',
                        '- publication_view_count>=2',
                        '- postgres_repository_stable',
                        '- regression_beats_v1',
                    ]
                )
                + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(doc_sync_path),
                    '--quality-report',
                    str(quality_path),
                    '--perf-report',
                    str(perf_path),
                    '--postgres-soak-benchmark-report',
                    str(postgres_soak_path),
                    '--beta-suite-output',
                    str(beta_suite_path),
                    '--ga-suite-output',
                    str(ga_suite_path),
                    '--roadmap-suite-output',
                    str(roadmap_suite_path),
                    '--release-gate-output',
                    str(release_gate_path),
                    '--release-standard-doc',
                    str(standard_path),
                    '--decision-output',
                    str(decision_path),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(decision_path.read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_stage_pack_complete'))
            missing_paths = {item.get('path') for item in decision.get('missing_or_invalid_evidence', [])}
            self.assertIn(str(release_gate_path.resolve()), missing_paths)

    def test_script_decision_only_holds_when_release_gate_pack_stage_commands_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            doc_sync_path = tmp_path / 'e13-doc-sync-check-report.json'
            quality_path = tmp_path / 'e11-quality-regression-report.json'
            perf_path = tmp_path / 'e11-perf-cost-baseline-report.json'
            postgres_soak_path = tmp_path / 'e13-postgres-soak-benchmark-report.json'
            beta_suite_path = tmp_path / 'e13-release-gate-beta-suite-plan.json'
            ga_suite_path = tmp_path / 'e13-release-gate-ga-suite-plan.json'
            roadmap_suite_path = tmp_path / 'e13-release-gate-roadmap-suite-plan.json'
            release_gate_path = tmp_path / 'e13-release-gate-validation-plan.json'
            standard_path = tmp_path / 'v2-release-switch-standard.md'
            decision_path = tmp_path / 'release-switch-decision.json'

            doc_sync_path.write_text(
                json.dumps(
                    {
                        'status': 'pass',
                        'failed_count': 0,
                        'checks': [
                            {'name': 'release_switch_standard_completeness', 'status': 'pass'},
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + '\n',
                encoding='utf-8',
            )
            quality_path.write_text(
                json.dumps({'regressed_count': 0}, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            perf_path.write_text(
                json.dumps({'regressed_count': 0}, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            postgres_soak_path.write_text(
                json.dumps(
                    {
                        'run_postgres': True,
                        'runs': {
                            'dual_write': {
                                'summary': {'count': 3},
                            }
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + '\n',
                encoding='utf-8',
            )
            beta_suite_path.write_text(
                json.dumps(
                    _plan_payload(
                        [
                            'ci',
                            'container_smoke',
                            'doc_sync',
                            'quality_regression',
                            'perf_cost_baseline',
                        ]
                    ),
                    ensure_ascii=False,
                    indent=2,
                )
                + '\n',
                encoding='utf-8',
            )
            ga_suite_path.write_text(
                json.dumps(
                    _plan_payload(
                        [
                            'postgres_soak',
                            'postgres_ga',
                            'worker_ga',
                            'review_queue_ga',
                            'provider_ga',
                            'calibration_ga',
                        ]
                    ),
                    ensure_ascii=False,
                    indent=2,
                )
                + '\n',
                encoding='utf-8',
            )
            roadmap_suite_path.write_text(
                json.dumps(
                    _plan_payload(['roadmap_extension']),
                    ensure_ascii=False,
                    indent=2,
                )
                + '\n',
                encoding='utf-8',
            )
            release_gate_path.write_text(
                json.dumps(
                    _plan_payload(
                        ['beta_gate', 'ga_gate', 'roadmap_gate'],
                        include_command=False,
                    ),
                    ensure_ascii=False,
                    indent=2,
                )
                + '\n',
                encoding='utf-8',
            )
            standard_path.write_text(
                '\n'.join(
                    [
                        '# V2 Release Switch Standard',
                        '- graph_is_source_of_truth',
                        '- review_queue_operational',
                        '- publication_view_count>=2',
                        '- postgres_repository_stable',
                        '- regression_beats_v1',
                    ]
                )
                + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(doc_sync_path),
                    '--quality-report',
                    str(quality_path),
                    '--perf-report',
                    str(perf_path),
                    '--postgres-soak-benchmark-report',
                    str(postgres_soak_path),
                    '--beta-suite-output',
                    str(beta_suite_path),
                    '--ga-suite-output',
                    str(ga_suite_path),
                    '--roadmap-suite-output',
                    str(roadmap_suite_path),
                    '--release-gate-output',
                    str(release_gate_path),
                    '--release-standard-doc',
                    str(standard_path),
                    '--decision-output',
                    str(decision_path),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(decision_path.read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_stage_pack_executable'))
            self.assertFalse(summary.get('release_gate_evidence_pack_complete'))
            missing_paths = {item.get('path') for item in decision.get('missing_or_invalid_evidence', [])}
            self.assertNotIn(str(release_gate_path.resolve()), missing_paths)

    def test_script_decision_only_holds_when_evidence_files_are_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            stale_timestamp = time.time() - (6 * 3600)
            os.utime(bundle['quality_path'], (stale_timestamp, stale_timestamp))

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--max-evidence-age-hours',
                    '1',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('freshness_check_enabled'))
            self.assertFalse(summary.get('evidence_freshness_gate_pass'))
            stale_files = set(summary.get('stale_evidence_files', []))
            self.assertIn(str(bundle['quality_path'].resolve()), stale_files)
            freshness_gate = next(
                (item for item in decision.get('gates', []) if item.get('name') == 'evidence_freshness'),
                None,
            )
            self.assertIsNotNone(freshness_gate)
            self.assertEqual(freshness_gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_evidence_freshness_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            stale_timestamp = time.time() - (6 * 3600)
            os.utime(bundle['quality_path'], (stale_timestamp, stale_timestamp))

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--max-evidence-age-hours',
                    '0',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('freshness_check_enabled'))
            self.assertTrue(summary.get('evidence_freshness_gate_pass'))

    def test_script_decision_only_holds_when_evidence_files_are_future_skewed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            future_timestamp = time.time() + (6 * 3600)
            os.utime(bundle['quality_path'], (future_timestamp, future_timestamp))

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--max-evidence-future-skew-hours',
                    '1',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('future_skew_check_enabled'))
            self.assertFalse(summary.get('evidence_freshness_gate_pass'))
            future_files = set(summary.get('future_evidence_files', []))
            self.assertIn(str(bundle['quality_path'].resolve()), future_files)
            freshness_gate = next(
                (item for item in decision.get('gates', []) if item.get('name') == 'evidence_freshness'),
                None,
            )
            self.assertIsNotNone(freshness_gate)
            self.assertEqual(freshness_gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_future_skew_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            future_timestamp = time.time() + (6 * 3600)
            os.utime(bundle['quality_path'], (future_timestamp, future_timestamp))

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--max-evidence-future-skew-hours',
                    '0',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('future_skew_check_enabled'))
            self.assertTrue(summary.get('evidence_freshness_gate_pass'))

    def test_script_decision_only_holds_when_evidence_cohort_age_spread_is_too_large(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            stale_but_not_expired_timestamp = time.time() - (20 * 3600)
            os.utime(bundle['quality_path'], (stale_but_not_expired_timestamp, stale_but_not_expired_timestamp))

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--max-evidence-age-hours',
                    '24',
                    '--max-evidence-cohort-skew-hours',
                    '1',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('cohort_skew_check_enabled'))
            self.assertFalse(summary.get('evidence_cohort_skew_gate_pass'))
            self.assertIsNotNone(summary.get('evidence_cohort_age_spread_hours'))
            self.assertGreater(float(summary.get('evidence_cohort_age_spread_hours', 0.0)), 1.0)
            violation_files = set(summary.get('cohort_skew_violation_files', []))
            self.assertIn(str(bundle['quality_path'].resolve()), violation_files)
            cohort_gate = next(
                (item for item in decision.get('gates', []) if item.get('name') == 'evidence_cohort_skew'),
                None,
            )
            self.assertIsNotNone(cohort_gate)
            self.assertEqual(cohort_gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_evidence_cohort_skew_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            stale_but_not_expired_timestamp = time.time() - (20 * 3600)
            os.utime(bundle['quality_path'], (stale_but_not_expired_timestamp, stale_but_not_expired_timestamp))

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--max-evidence-age-hours',
                    '24',
                    '--max-evidence-cohort-skew-hours',
                    '0',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('cohort_skew_check_enabled'))
            self.assertTrue(summary.get('evidence_cohort_skew_gate_pass'))

    def test_script_decision_only_holds_when_release_gate_stage_outputs_do_not_match_evidence_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            wrong_beta_output = tmp_path / 'wrong-beta-suite-plan.json'

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                if stage.get('name') != 'beta_gate':
                    continue
                stage['command'] = [
                    'python3',
                    'scripts/run_linux_validation_suite.py',
                    '--python',
                    'python3',
                    '--stages',
                    'ci',
                    'container_smoke',
                    'doc_sync',
                    'quality_regression',
                    'perf_cost_baseline',
                    '--output',
                    str(wrong_beta_output.resolve()),
                ]
                break
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_binding_check_enabled'))
            self.assertFalse(summary.get('release_gate_output_binding_pass'))
            self.assertGreaterEqual(int(summary.get('release_gate_binding_mismatch_count', 0)), 1)
            mismatches = summary.get('release_gate_binding_mismatches', [])
            self.assertTrue(any(item.get('stage') == 'beta_gate' for item in mismatches))
            binding_gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_evidence_binding'
                ),
                None,
            )
            self.assertIsNotNone(binding_gate)
            self.assertEqual(binding_gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_output_binding_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)
            wrong_beta_output = tmp_path / 'wrong-beta-suite-plan.json'

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                if stage.get('name') != 'beta_gate':
                    continue
                stage['command'] = [
                    'python3',
                    'scripts/run_linux_validation_suite.py',
                    '--python',
                    'python3',
                    '--stages',
                    'ci',
                    'container_smoke',
                    'doc_sync',
                    'quality_regression',
                    'perf_cost_baseline',
                    '--output',
                    str(wrong_beta_output.resolve()),
                ]
                break
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--skip-release-gate-output-binding-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_binding_check_enabled'))
            self.assertTrue(summary.get('release_gate_output_binding_pass'))
            self.assertEqual(int(summary.get('release_gate_binding_mismatch_count', 0)), 0)
            self.assertTrue(summary.get('release_gate_stage_contract_pass'))
            binding_gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_evidence_binding'
                ),
                None,
            )
            self.assertIsNotNone(binding_gate)
            self.assertEqual(binding_gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_contract_mismatches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                if stage.get('name') != 'beta_gate':
                    continue
                stage['command'] = [
                    'python3',
                    'scripts/run_linux_validation_suite.py',
                    '--python',
                    'python3',
                    '--stages',
                    'ci',
                    '--output',
                    str(bundle['beta_suite_path'].resolve()),
                ]
                break
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_stage_contract_check_enabled'))
            self.assertFalse(summary.get('release_gate_stage_contract_pass'))
            self.assertGreaterEqual(int(summary.get('release_gate_stage_contract_mismatch_count', 0)), 1)
            mismatches = summary.get('release_gate_stage_contract_mismatches', [])
            self.assertTrue(any(item.get('check') == '--stages' for item in mismatches))
            stage_contract_gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_stage_contract'
                ),
                None,
            )
            self.assertIsNotNone(stage_contract_gate)
            self.assertEqual(stage_contract_gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_stage_contract_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                if stage.get('name') != 'beta_gate':
                    continue
                stage['command'] = [
                    'python3',
                    'scripts/run_linux_validation_suite.py',
                    '--python',
                    'python3',
                    '--stages',
                    'ci',
                    '--output',
                    str(bundle['beta_suite_path'].resolve()),
                ]
                break
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--skip-release-gate-stage-contract-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_stage_contract_check_enabled'))
            self.assertTrue(summary.get('release_gate_stage_contract_pass'))
            self.assertEqual(int(summary.get('release_gate_stage_contract_mismatch_count', 0)), 0)
            stage_contract_gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_stage_contract'
                ),
                None,
            )
            self.assertIsNotNone(stage_contract_gate)
            self.assertEqual(stage_contract_gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_script_position_is_decoy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                if stage.get('name') != 'beta_gate':
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    break
                stage['command'] = [
                    'python3',
                    'scripts/run_release_gate_validation.py',
                    'scripts/run_linux_validation_suite.py',
                    *command[2:],
                ]
                break
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_stage_contract_pass'))
            self.assertTrue(summary.get('release_gate_script_position_check_enabled'))
            self.assertFalse(summary.get('release_gate_script_position_pass'))
            self.assertGreaterEqual(int(summary.get('release_gate_script_position_mismatch_count', 0)), 1)
            mismatches = summary.get('release_gate_script_position_mismatches', [])
            self.assertTrue(any(item.get('check') == 'script-position' for item in mismatches))
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_script_position'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_script_position_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                if stage.get('name') != 'beta_gate':
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    break
                stage['command'] = [
                    'python3',
                    'scripts/run_release_gate_validation.py',
                    'scripts/run_linux_validation_suite.py',
                    *command[2:],
                ]
                break
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--skip-release-gate-script-position-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_script_position_check_enabled'))
            self.assertTrue(summary.get('release_gate_script_position_pass'))
            self.assertEqual(int(summary.get('release_gate_script_position_mismatch_count', 0)), 0)
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_script_position'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_script_path_is_not_repo_canonical(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            decoy_script = str(
                (tmp_path / 'decoy' / 'scripts' / 'run_linux_validation_suite.py').resolve()
            )
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                if stage.get('name') != 'beta_gate':
                    continue
                command = stage.get('command')
                if not isinstance(command, list) or len(command) < 2:
                    break
                command[1] = decoy_script
                break
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_stage_contract_pass'))
            self.assertTrue(summary.get('release_gate_script_position_pass'))
            self.assertTrue(summary.get('release_gate_script_anchor_check_enabled'))
            self.assertFalse(summary.get('release_gate_script_anchor_pass'))
            self.assertGreaterEqual(int(summary.get('release_gate_script_anchor_mismatch_count', 0)), 1)
            mismatches = summary.get('release_gate_script_anchor_mismatches', [])
            self.assertTrue(
                any(
                    item.get('stage') == 'beta_gate' and item.get('check') == 'script-anchor'
                    for item in mismatches
                )
            )
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_script_anchor'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_script_anchor_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            decoy_script = str(
                (tmp_path / 'decoy' / 'scripts' / 'run_linux_validation_suite.py').resolve()
            )
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                if stage.get('name') != 'beta_gate':
                    continue
                command = stage.get('command')
                if not isinstance(command, list) or len(command) < 2:
                    break
                command[1] = decoy_script
                break
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--skip-release-gate-script-anchor-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_script_anchor_check_enabled'))
            self.assertTrue(summary.get('release_gate_script_anchor_pass'))
            self.assertEqual(int(summary.get('release_gate_script_anchor_mismatch_count', 0)), 0)
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_script_anchor'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_python_binding_mismatches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                if stage.get('name') != 'beta_gate':
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    break
                python_option_index = command.index('--python')
                command[python_option_index + 1] = 'python3.11'
                break
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_stage_contract_pass'))
            self.assertTrue(summary.get('release_gate_script_anchor_pass'))
            self.assertTrue(summary.get('release_gate_python_binding_check_enabled'))
            self.assertFalse(summary.get('release_gate_python_binding_pass'))
            self.assertGreaterEqual(int(summary.get('release_gate_python_binding_mismatch_count', 0)), 1)
            mismatches = summary.get('release_gate_python_binding_mismatches', [])
            self.assertTrue(any(item.get('check') == '--python-value' for item in mismatches))
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_python_binding'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_python_binding_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                if stage.get('name') != 'beta_gate':
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    break
                python_option_index = command.index('--python')
                command[python_option_index + 1] = 'python3.11'
                break
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--skip-release-gate-python-binding-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_python_binding_check_enabled'))
            self.assertTrue(summary.get('release_gate_python_binding_pass'))
            self.assertEqual(int(summary.get('release_gate_python_binding_mismatch_count', 0)), 0)
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_python_binding'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_uses_python_optimization_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list) or not command:
                    continue
                command.insert(1, '-O')
                python_option_index = command.index('--python')
                command[python_option_index + 1] = 'python3 -O'
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    'python3 -O',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_python_binding_pass'))
            self.assertTrue(summary.get('release_gate_python_optimization_check_enabled'))
            self.assertFalse(summary.get('release_gate_python_optimization_pass'))
            self.assertGreaterEqual(int(summary.get('release_gate_python_optimization_mismatch_count', 0)), 1)
            mismatches = summary.get('release_gate_python_optimization_mismatches', [])
            self.assertTrue(any(item.get('option') in ('-O', '-OO', '-O*') for item in mismatches))
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_python_optimization'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_python_optimization_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                command = stage.get('command')
                if not isinstance(command, list) or not command:
                    continue
                command.insert(1, '-O')
                python_option_index = command.index('--python')
                command[python_option_index + 1] = 'python3 -O'
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--python',
                    'python3 -O',
                    '--skip-release-gate-python-optimization-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_python_optimization_check_enabled'))
            self.assertTrue(summary.get('release_gate_python_optimization_pass'))
            self.assertEqual(int(summary.get('release_gate_python_optimization_mismatch_count', 0)), 0)
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_python_optimization'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_coverage_floor_is_downgraded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                if stage.get('name') != 'beta_gate':
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    break
                coverage_option_index = command.index('--coverage-fail-under')
                command[coverage_option_index + 1] = '0'
                break
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_coverage_floor_check_enabled'))
            self.assertFalse(summary.get('release_gate_coverage_floor_pass'))
            self.assertGreaterEqual(int(summary.get('release_gate_coverage_floor_mismatch_count', 0)), 1)
            mismatches = summary.get('release_gate_coverage_floor_mismatches', [])
            self.assertTrue(
                any(
                    item.get('check')
                    in ('--coverage-fail-under-floor', '--coverage-fail-under-binding')
                    for item in mismatches
                )
            )
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_coverage_floor'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_coverage_floor_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                if stage.get('name') != 'beta_gate':
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    break
                coverage_option_index = command.index('--coverage-fail-under')
                command[coverage_option_index + 1] = '0'
                break
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--skip-release-gate-coverage-floor-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_coverage_floor_check_enabled'))
            self.assertTrue(summary.get('release_gate_coverage_floor_pass'))
            self.assertEqual(int(summary.get('release_gate_coverage_floor_mismatch_count', 0)), 0)
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_coverage_floor'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_uses_inline_exec_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                if stage.get('name') != 'beta_gate':
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    break
                stage['command'] = [
                    command[0],
                    '-c',
                    'print("decoy-runner")',
                    *command[1:],
                ]
                break
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_stage_contract_pass'))
            self.assertTrue(summary.get('release_gate_script_position_pass'))
            self.assertTrue(summary.get('release_gate_inline_exec_check_enabled'))
            self.assertFalse(summary.get('release_gate_inline_exec_pass'))
            self.assertGreaterEqual(int(summary.get('release_gate_inline_exec_mismatch_count', 0)), 1)
            mismatches = summary.get('release_gate_inline_exec_mismatches', [])
            self.assertTrue(any(item.get('option') == '-c' for item in mismatches))
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_inline_exec'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_inline_exec_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                if stage.get('name') != 'beta_gate':
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    break
                stage['command'] = [
                    command[0],
                    '-c',
                    'print("decoy-runner")',
                    *command[1:],
                ]
                break
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--skip-release-gate-inline-exec-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_inline_exec_check_enabled'))
            self.assertTrue(summary.get('release_gate_inline_exec_pass'))
            self.assertEqual(int(summary.get('release_gate_inline_exec_mismatch_count', 0)), 0)
            gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_inline_exec'
                ),
                None,
            )
            self.assertIsNotNone(gate)
            self.assertEqual(gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_options_are_ambiguous(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                if stage.get('name') != 'beta_gate':
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    break
                output_index = command.index('--output')
                command[output_index:output_index] = ['--stages', 'ci']
                break
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_stage_contract_pass'))
            self.assertTrue(summary.get('release_gate_output_binding_pass'))
            self.assertTrue(summary.get('release_gate_option_override_check_enabled'))
            self.assertFalse(summary.get('release_gate_option_override_pass'))
            self.assertGreaterEqual(int(summary.get('release_gate_option_override_mismatch_count', 0)), 1)
            mismatches = summary.get('release_gate_option_override_mismatches', [])
            self.assertTrue(any(item.get('check') == '--stages-occurrence' for item in mismatches))
            option_override_gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_option_override'
                ),
                None,
            )
            self.assertIsNotNone(option_override_gate)
            self.assertEqual(option_override_gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_option_override_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                if stage.get('name') != 'beta_gate':
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    break
                output_index = command.index('--output')
                command[output_index:output_index] = ['--stages', 'ci']
                break
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--skip-release-gate-option-override-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_option_override_check_enabled'))
            self.assertTrue(summary.get('release_gate_option_override_pass'))
            self.assertEqual(int(summary.get('release_gate_option_override_mismatch_count', 0)), 0)
            option_override_gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_option_override'
                ),
                None,
            )
            self.assertIsNotNone(option_override_gate)
            self.assertEqual(option_override_gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_uses_dry_run_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                if stage.get('name') != 'beta_gate':
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    break
                command.append('--dry-run')
                break
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_stage_contract_pass'))
            self.assertTrue(summary.get('release_gate_option_override_pass'))
            self.assertTrue(summary.get('release_gate_dry_run_check_enabled'))
            self.assertFalse(summary.get('release_gate_dry_run_pass'))
            self.assertGreaterEqual(int(summary.get('release_gate_dry_run_mismatch_count', 0)), 1)
            mismatches = summary.get('release_gate_dry_run_mismatches', [])
            self.assertTrue(any(item.get('option') == '--dry-run' for item in mismatches))
            dry_run_gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_dry_run'
                ),
                None,
            )
            self.assertIsNotNone(dry_run_gate)
            self.assertEqual(dry_run_gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_dry_run_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                if stage.get('name') != 'beta_gate':
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    break
                command.append('--dry-run')
                break
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--skip-release-gate-dry-run-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_dry_run_check_enabled'))
            self.assertTrue(summary.get('release_gate_dry_run_pass'))
            self.assertEqual(int(summary.get('release_gate_dry_run_mismatch_count', 0)), 0)
            dry_run_gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_dry_run'
                ),
                None,
            )
            self.assertIsNotNone(dry_run_gate)
            self.assertEqual(dry_run_gate.get('status'), 'pass')

    def test_script_decision_only_holds_when_release_gate_stage_uses_relaxed_flags(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                if stage.get('name') != 'beta_gate':
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    break
                command.append('--allow-regression')
                break
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn('Release switch decision=HOLD', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'HOLD')
            summary = decision.get('evidence_summary', {})
            self.assertTrue(summary.get('release_gate_relaxed_flags_check_enabled'))
            self.assertFalse(summary.get('release_gate_relaxed_flags_pass'))
            self.assertGreaterEqual(int(summary.get('release_gate_relaxed_flags_mismatch_count', 0)), 1)
            mismatches = summary.get('release_gate_relaxed_flags_mismatches', [])
            self.assertTrue(any(item.get('option') == '--allow-regression' for item in mismatches))
            relaxed_gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_relaxed_flags'
                ),
                None,
            )
            self.assertIsNotNone(relaxed_gate)
            self.assertEqual(relaxed_gate.get('status'), 'hold')

    def test_script_decision_only_can_disable_release_gate_relaxed_flags_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle = _write_go_decision_evidence_bundle(tmp_path)

            release_gate_plan = json.loads(bundle['release_gate_path'].read_text(encoding='utf-8'))
            for stage in release_gate_plan.get('stages', []):
                if not isinstance(stage, dict):
                    continue
                if stage.get('name') != 'beta_gate':
                    continue
                command = stage.get('command')
                if not isinstance(command, list):
                    break
                command.append('--allow-regression')
                break
            bundle['release_gate_path'].write_text(
                json.dumps(release_gate_plan, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--skip-release-gate-relaxed-flags-check',
                    '--doc-sync-report',
                    str(bundle['doc_sync_path']),
                    '--quality-report',
                    str(bundle['quality_path']),
                    '--perf-report',
                    str(bundle['perf_path']),
                    '--postgres-soak-benchmark-report',
                    str(bundle['postgres_soak_path']),
                    '--beta-suite-output',
                    str(bundle['beta_suite_path']),
                    '--ga-suite-output',
                    str(bundle['ga_suite_path']),
                    '--roadmap-suite-output',
                    str(bundle['roadmap_suite_path']),
                    '--release-gate-output',
                    str(bundle['release_gate_path']),
                    '--release-standard-doc',
                    str(bundle['standard_path']),
                    '--decision-output',
                    str(bundle['decision_path']),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Release switch decision=GO', completed.stdout)

            decision = json.loads(bundle['decision_path'].read_text(encoding='utf-8'))
            self.assertEqual(decision.get('decision'), 'GO')
            summary = decision.get('evidence_summary', {})
            self.assertFalse(summary.get('release_gate_relaxed_flags_check_enabled'))
            self.assertTrue(summary.get('release_gate_relaxed_flags_pass'))
            self.assertEqual(int(summary.get('release_gate_relaxed_flags_mismatch_count', 0)), 0)
            relaxed_gate = next(
                (
                    item
                    for item in decision.get('gates', [])
                    if item.get('name') == 'release_gate_relaxed_flags'
                ),
                None,
            )
            self.assertIsNotNone(relaxed_gate)
            self.assertEqual(relaxed_gate.get('status'), 'pass')

    def test_script_decision_only_hold_is_nonzero_unless_allow_hold(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            decision_path = tmp_path / 'release-switch-decision.json'

            hold_completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--doc-sync-report',
                    str(tmp_path / 'missing-doc-sync.json'),
                    '--quality-report',
                    str(tmp_path / 'missing-quality.json'),
                    '--perf-report',
                    str(tmp_path / 'missing-perf.json'),
                    '--postgres-soak-benchmark-report',
                    str(tmp_path / 'missing-postgres.json'),
                    '--ga-suite-output',
                    str(tmp_path / 'missing-ga-suite.json'),
                    '--release-standard-doc',
                    str(tmp_path / 'missing-standard.md'),
                    '--decision-output',
                    str(decision_path),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(hold_completed.returncode, 1, hold_completed.stderr)
            self.assertIn('Release switch decision=HOLD', hold_completed.stdout)

            allow_hold_completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--decision-only',
                    '--allow-hold',
                    '--doc-sync-report',
                    str(tmp_path / 'missing-doc-sync.json'),
                    '--quality-report',
                    str(tmp_path / 'missing-quality.json'),
                    '--perf-report',
                    str(tmp_path / 'missing-perf.json'),
                    '--postgres-soak-benchmark-report',
                    str(tmp_path / 'missing-postgres.json'),
                    '--ga-suite-output',
                    str(tmp_path / 'missing-ga-suite.json'),
                    '--release-standard-doc',
                    str(tmp_path / 'missing-standard.md'),
                    '--decision-output',
                    str(decision_path),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(allow_hold_completed.returncode, 0, allow_hold_completed.stderr)
            self.assertIn('Release switch decision=HOLD', allow_hold_completed.stdout)


if __name__ == '__main__':
    unittest.main()
