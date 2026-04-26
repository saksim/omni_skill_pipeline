from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / 'scripts' / 'run_release_switch_validation.py'


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
            ga_suite_path = tmp_path / 'e13-release-gate-ga-suite-plan.json'
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
            ga_suite_path.write_text(
                json.dumps(
                    {
                        'stages': [
                            {'name': 'postgres_soak'},
                            {'name': 'review_queue_ga'},
                        ]
                    },
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
                    '--ga-suite-output',
                    str(ga_suite_path),
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
            self.assertEqual(decision.get('pass_count'), 5)


if __name__ == '__main__':
    unittest.main()
