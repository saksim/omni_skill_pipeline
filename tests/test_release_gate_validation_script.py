from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / 'scripts' / 'run_release_gate_validation.py'


class ReleaseGateValidationScriptTests(unittest.TestCase):
    def test_script_dry_run_emits_default_release_gate_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / 'release-gate-plan.json'
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--python',
                    'python3',
                    '--dry-run',
                    '--output',
                    str(output_path),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Selected stages: beta_gate, ga_gate, roadmap_gate', completed.stdout)
            self.assertIn('scripts/run_linux_validation_suite.py', completed.stdout)
            self.assertIn(
                '--stages ci container_smoke doc_sync quality_regression perf_cost_baseline',
                completed.stdout,
            )
            self.assertIn(
                '--stages postgres_soak postgres_ga worker_ga review_queue_ga provider_ga calibration_ga',
                completed.stdout,
            )
            self.assertIn('--stages roadmap_extension', completed.stdout)

            report = json.loads(output_path.read_text(encoding='utf-8'))
            self.assertEqual(report.get('stage_count'), 3)
            self.assertEqual(
                [item.get('name') for item in report.get('stages', [])],
                ['beta_gate', 'ga_gate', 'roadmap_gate'],
            )

    def test_script_respects_beta_stage_selection_and_option_forwarding(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                '--python',
                'python3',
                '--stages',
                'beta_gate',
                '--coverage-fail-under',
                '72.5',
                '--no-coverage',
                '--allow-regression',
                '--container-image-tag',
                'omni-skill-pipeline:rc',
                '--container-name',
                'omni-release-gate',
                '--container-host',
                '0.0.0.0',
                '--container-port',
                '19090',
                '--container-timeout-seconds',
                '41',
                '--container-interval-seconds',
                '2',
                '--container-skip-build',
                '--dry-run',
                '--output',
                '-',
            ],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn('Selected stages: beta_gate', completed.stdout)
        self.assertIn('--coverage-fail-under 72.5', completed.stdout)
        self.assertIn('--no-coverage', completed.stdout)
        self.assertIn('--allow-regression', completed.stdout)
        self.assertIn('--container-image-tag omni-skill-pipeline:rc', completed.stdout)
        self.assertIn('--container-name omni-release-gate', completed.stdout)
        self.assertIn('--container-host 0.0.0.0', completed.stdout)
        self.assertIn('--container-port 19090', completed.stdout)
        self.assertIn('--container-timeout-seconds 41.0', completed.stdout)
        self.assertIn('--container-interval-seconds 2.0', completed.stdout)
        self.assertIn('--container-skip-build', completed.stdout)
        self.assertNotIn('--keep-going', completed.stdout)
        self.assertNotIn('--stages postgres_soak', completed.stdout)
        self.assertNotIn('--stages roadmap_extension', completed.stdout)

    def test_script_forwards_ga_stage_options(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            manifest_path = tmp_path / 'calibration-manifest.json'
            report_path = tmp_path / 'calibration-report.json'
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--python',
                    'python3',
                    '--stages',
                    'ga_gate',
                    '--postgres-dsn',
                    'postgresql://validator',
                    '--postgres-soak-iterations',
                    '88',
                    '--postgres-ga-iterations',
                    '99',
                    '--allow-secondary-failures',
                    '--calibration-manifest',
                    str(manifest_path),
                    '--calibration-report-output',
                    str(report_path),
                    '--calibration-margin',
                    '0.06',
                    '--calibration-fail-on-mismatch',
                    '--dry-run',
                    '--output',
                    '-',
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Selected stages: ga_gate', completed.stdout)
            self.assertIn(
                '--stages postgres_soak postgres_ga worker_ga review_queue_ga provider_ga calibration_ga',
                completed.stdout,
            )
            self.assertIn('--postgres-dsn postgresql://validator', completed.stdout)
            self.assertIn('--postgres-soak-iterations 88', completed.stdout)
            self.assertIn('--postgres-ga-iterations 99', completed.stdout)
            self.assertIn('--allow-secondary-failures', completed.stdout)
            self.assertIn('--calibration-manifest %s' % str(manifest_path.resolve()), completed.stdout)
            self.assertIn('--calibration-report-output %s' % str(report_path.resolve()), completed.stdout)
            self.assertIn('--calibration-margin 0.06', completed.stdout)
            self.assertIn('--calibration-fail-on-mismatch', completed.stdout)
            self.assertNotIn('--keep-going', completed.stdout)
            self.assertNotIn('--stages ci container_smoke doc_sync', completed.stdout)

    def test_keep_going_is_forwarded_to_nested_linux_suites(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                '--python',
                'python3',
                '--stages',
                'beta_gate',
                'ga_gate',
                '--keep-going',
                '--dry-run',
                '--output',
                '-',
            ],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        command_lines = [
            line
            for line in completed.stdout.splitlines()
            if 'scripts/run_linux_validation_suite.py' in line
        ]
        self.assertEqual(len(command_lines), 2)
        for line in command_lines:
            self.assertIn('--keep-going', line)

    def test_keep_going_runs_later_release_gates_after_failure_and_summarizes_failures(self) -> None:
        command = (
            "import sys; print('release-probe'); "
            "raise SystemExit(9 if '--stages' in sys.argv else 0)"
        )
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                '--python',
                '%s -c "%s"' % (sys.executable, command),
                '--stages',
                'beta_gate',
                'roadmap_gate',
                '--beta-suite-output',
                'beta',
                '--roadmap-suite-output',
                'roadmap',
                '--keep-going',
                '--output',
                '-',
            ],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 9)
        self.assertIn('Running stage: beta_gate', completed.stdout)
        self.assertIn('Running stage: roadmap_gate', completed.stdout)
        self.assertIn('Stage failures summary:', completed.stderr)
        self.assertIn('- beta_gate (exit=9)', completed.stderr)


if __name__ == '__main__':
    unittest.main()
