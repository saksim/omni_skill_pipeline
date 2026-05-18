from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / 'scripts' / 'run_release_gate_validation.py'


class ReleaseGateValidationScriptTests(unittest.TestCase):
    def setUp(self) -> None:
        self._postgres_dsn = os.environ.pop('OMNI_TEST_POSTGRES_DSN', None)

    def tearDown(self) -> None:
        if self._postgres_dsn is not None:
            os.environ['OMNI_TEST_POSTGRES_DSN'] = self._postgres_dsn

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
            self.assertIn('--require-postgres', completed.stdout)
            self.assertIn('--postgres-soak-iterations 88', completed.stdout)
            self.assertIn('--postgres-ga-iterations 99', completed.stdout)
            self.assertIn('--allow-secondary-failures', completed.stdout)
            self.assertIn('--calibration-manifest %s' % str(manifest_path.resolve()), completed.stdout)
            self.assertIn('--calibration-report-output %s' % str(report_path.resolve()), completed.stdout)
            self.assertIn('--calibration-margin 0.06', completed.stdout)
            self.assertIn('--calibration-fail-on-mismatch', completed.stdout)
            self.assertNotIn('--keep-going', completed.stdout)
            self.assertNotIn('--stages ci container_smoke doc_sync', completed.stdout)

    def test_env_postgres_dsn_is_not_printed_in_ga_gate_command(self) -> None:
        env = os.environ.copy()
        env['OMNI_TEST_POSTGRES_DSN'] = 'postgresql://user:secret@127.0.0.1:5432/omni_test'
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                '--python',
                'python3',
                '--stages',
                'ga_gate',
                '--dry-run',
                '--output',
                '-',
            ],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn('Selected stages: ga_gate', completed.stdout)
        self.assertNotIn('postgresql://user:secret', completed.stdout)
        self.assertNotIn('--postgres-dsn', completed.stdout)

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
        with tempfile.TemporaryDirectory() as tmp_dir:
            launcher = Path(tmp_dir) / 'fail_launcher.py'
            launcher.write_text(
                "from __future__ import annotations\n"
                "import sys\n"
                "print('release-probe')\n"
                "raise SystemExit(9)\n",
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--python',
                    '%s %s' % (sys.executable, launcher),
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

    def test_postgres_dsn_only_reaches_ga_gate_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            launcher = Path(tmp_dir) / 'env_probe.py'
            launcher.write_text(
                "from __future__ import annotations\n"
                "import os\n"
                "import sys\n"
                "stage = sys.argv[sys.argv.index('--stages') + 1]\n"
                "dsn_visible = 'OMNI_TEST_POSTGRES_DSN' in os.environ\n"
                "print('%s dsn-visible=%s' % (stage, dsn_visible))\n"
                "if stage == 'postgres_soak':\n"
                "    raise SystemExit(0 if dsn_visible else 5)\n"
                "raise SystemExit(4 if dsn_visible else 0)\n",
                encoding='utf-8',
            )
            env = os.environ.copy()
            env['OMNI_TEST_POSTGRES_DSN'] = 'postgresql://user:secret@127.0.0.1:5432/omni_test'
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--python',
                    '%s %s' % (sys.executable, launcher),
                    '--stages',
                    'beta_gate',
                    'ga_gate',
                    'roadmap_gate',
                    '--keep-going',
                    '--output',
                    '-',
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
                env=env,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn('ci dsn-visible=False', completed.stdout)
        self.assertIn('postgres_soak dsn-visible=True', completed.stdout)
        self.assertIn('roadmap_extension dsn-visible=False', completed.stdout)


if __name__ == '__main__':
    unittest.main()
