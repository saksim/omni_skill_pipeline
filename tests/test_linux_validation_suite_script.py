from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / 'scripts' / 'run_linux_validation_suite.py'


class LinuxValidationSuiteScriptTests(unittest.TestCase):
    def test_script_dry_run_emits_default_linux_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / 'linux-validation-plan.json'
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
            self.assertIn(
                'Selected stages: ci, container_smoke, doc_sync, quality_regression, perf_cost_baseline, postgres_soak, postgres_ga, worker_ga, review_queue_ga, provider_ga, calibration_ga, roadmap_extension',
                completed.stdout,
            )
            self.assertIn('scripts/run_ci.py', completed.stdout)
            self.assertIn('scripts/run_container_smoke.py', completed.stdout)
            self.assertIn('scripts/run_doc_sync_check.py', completed.stdout)
            self.assertIn('scripts/run_quality_regression.py', completed.stdout)
            self.assertIn('scripts/run_perf_cost_baseline.py', completed.stdout)
            self.assertIn('scripts/run_postgres_soak_validation.py', completed.stdout)
            self.assertIn('scripts/run_postgres_ga_validation.py', completed.stdout)
            self.assertIn('scripts/run_worker_ga_validation.py', completed.stdout)
            self.assertIn('scripts/run_review_queue_ga_validation.py', completed.stdout)
            self.assertIn('scripts/run_provider_ga_validation.py', completed.stdout)
            self.assertIn('scripts/run_calibration_ga_validation.py', completed.stdout)
            self.assertIn('scripts/run_roadmap_extension_validation.py', completed.stdout)

            report = json.loads(output_path.read_text(encoding='utf-8'))
            self.assertEqual(report.get('stage_count'), 12)
            self.assertEqual(
                [item.get('name') for item in report.get('stages', [])],
                [
                    'ci',
                    'container_smoke',
                    'doc_sync',
                    'quality_regression',
                    'perf_cost_baseline',
                    'postgres_soak',
                    'postgres_ga',
                    'worker_ga',
                    'review_queue_ga',
                    'provider_ga',
                    'calibration_ga',
                    'roadmap_extension',
                ],
            )

    def test_script_respects_stage_selection_and_regression_flag(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                '--python',
                'python3',
                '--stages',
                'doc_sync',
                'quality_regression',
                '--allow-regression',
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
        self.assertIn('Selected stages: doc_sync, quality_regression', completed.stdout)
        self.assertNotIn('scripts/run_ci.py', completed.stdout)
        self.assertNotIn('scripts/run_container_smoke.py', completed.stdout)
        self.assertNotIn('scripts/run_perf_cost_baseline.py', completed.stdout)
        self.assertNotIn('scripts/run_postgres_soak_validation.py', completed.stdout)
        self.assertNotIn('scripts/run_postgres_ga_validation.py', completed.stdout)
        self.assertNotIn('scripts/run_worker_ga_validation.py', completed.stdout)
        self.assertNotIn('scripts/run_review_queue_ga_validation.py', completed.stdout)
        self.assertNotIn('scripts/run_provider_ga_validation.py', completed.stdout)
        self.assertNotIn('scripts/run_calibration_ga_validation.py', completed.stdout)
        self.assertNotIn('scripts/run_roadmap_extension_validation.py', completed.stdout)
        self.assertIn('scripts/run_doc_sync_check.py', completed.stdout)
        self.assertIn('scripts/run_quality_regression.py', completed.stdout)

        quality_command_lines = [
            line
            for line in completed.stdout.splitlines()
            if 'scripts/run_quality_regression.py' in line
        ]
        self.assertTrue(quality_command_lines)
        for line in quality_command_lines:
            self.assertNotIn('--fail-on-regression', line)

    def test_container_smoke_stage_forwards_container_options(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                '--python',
                'python3',
                '--stages',
                'container_smoke',
                '--container-image-tag',
                'omni-skill-pipeline:test',
                '--container-name',
                'omni-linux-suite-smoke',
                '--container-host',
                '0.0.0.0',
                '--container-port',
                '19090',
                '--container-timeout-seconds',
                '45',
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
        self.assertIn('Selected stages: container_smoke', completed.stdout)
        self.assertIn('scripts/run_container_smoke.py', completed.stdout)
        self.assertIn('--image-tag omni-skill-pipeline:test', completed.stdout)
        self.assertIn('--container-name omni-linux-suite-smoke', completed.stdout)
        self.assertIn('--host 0.0.0.0', completed.stdout)
        self.assertIn('--port 19090', completed.stdout)
        self.assertIn('--timeout-seconds 45.0', completed.stdout)
        self.assertIn('--interval-seconds 2.0', completed.stdout)
        self.assertIn('--skip-build', completed.stdout)
        self.assertNotIn('scripts/run_ci.py', completed.stdout)
        self.assertNotIn('scripts/run_doc_sync_check.py', completed.stdout)
        self.assertNotIn('scripts/run_postgres_ga_validation.py', completed.stdout)
        self.assertNotIn('scripts/run_worker_ga_validation.py', completed.stdout)
        self.assertNotIn('scripts/run_review_queue_ga_validation.py', completed.stdout)
        self.assertNotIn('scripts/run_provider_ga_validation.py', completed.stdout)
        self.assertNotIn('scripts/run_calibration_ga_validation.py', completed.stdout)
        self.assertNotIn('scripts/run_roadmap_extension_validation.py', completed.stdout)

    def test_postgres_soak_stage_forwards_postgres_options(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            soak_plan_path = tmp_path / 'postgres-soak-plan.json'
            benchmark_output_path = tmp_path / 'postgres-soak-benchmark.json'
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--python',
                    'python3',
                    '--stages',
                    'postgres_soak',
                    '--postgres-dsn',
                    'postgresql://validator',
                    '--postgres-soak-iterations',
                    '77',
                    '--postgres-soak-output',
                    str(soak_plan_path),
                    '--postgres-soak-benchmark-output',
                    str(benchmark_output_path),
                    '--allow-secondary-failures',
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
            self.assertIn('Selected stages: postgres_soak', completed.stdout)
            self.assertNotIn('scripts/run_ci.py', completed.stdout)
            self.assertIn('scripts/run_postgres_soak_validation.py', completed.stdout)
            self.assertIn('--postgres-dsn postgresql://validator', completed.stdout)
            self.assertIn('--benchmark-iterations 77', completed.stdout)
            self.assertIn('--allow-secondary-failures', completed.stdout)
            self.assertIn('--output %s' % str(soak_plan_path.resolve()), completed.stdout)
            self.assertIn('--benchmark-output %s' % str(benchmark_output_path.resolve()), completed.stdout)
            self.assertNotIn('scripts/run_calibration_ga_validation.py', completed.stdout)
            self.assertNotIn('scripts/run_postgres_ga_validation.py', completed.stdout)
            self.assertNotIn('scripts/run_roadmap_extension_validation.py', completed.stdout)

    def test_worker_ga_stage_forwards_worker_options(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            worker_output_path = Path(tmp_dir) / 'worker-ga-plan.json'
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--python',
                    'python3',
                    '--stages',
                    'worker_ga',
                    '--worker-ga-output',
                    str(worker_output_path),
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
            self.assertIn('Selected stages: worker_ga', completed.stdout)
            self.assertIn('scripts/run_worker_ga_validation.py', completed.stdout)
            self.assertIn('--python python3', completed.stdout)
            self.assertIn('--output %s' % str(worker_output_path.resolve()), completed.stdout)
            self.assertNotIn('scripts/run_ci.py', completed.stdout)
            self.assertNotIn('scripts/run_postgres_ga_validation.py', completed.stdout)
            self.assertNotIn('scripts/run_postgres_soak_validation.py', completed.stdout)
            self.assertNotIn('scripts/run_review_queue_ga_validation.py', completed.stdout)
            self.assertNotIn('scripts/run_provider_ga_validation.py', completed.stdout)
            self.assertNotIn('scripts/run_calibration_ga_validation.py', completed.stdout)
            self.assertNotIn('scripts/run_roadmap_extension_validation.py', completed.stdout)

    def test_postgres_ga_stage_forwards_postgres_options(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            postgres_ga_output_path = tmp_path / 'postgres-ga-plan.json'
            benchmark_output_path = tmp_path / 'postgres-ga-benchmark.json'
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--python',
                    'python3',
                    '--stages',
                    'postgres_ga',
                    '--postgres-dsn',
                    'postgresql://validator',
                    '--postgres-ga-iterations',
                    '91',
                    '--postgres-ga-output',
                    str(postgres_ga_output_path),
                    '--postgres-ga-benchmark-output',
                    str(benchmark_output_path),
                    '--allow-secondary-failures',
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
            self.assertIn('Selected stages: postgres_ga', completed.stdout)
            self.assertIn('scripts/run_postgres_ga_validation.py', completed.stdout)
            self.assertIn('--postgres-dsn postgresql://validator', completed.stdout)
            self.assertIn('--benchmark-iterations 91', completed.stdout)
            self.assertIn(
                '--benchmark-output %s' % str(benchmark_output_path.resolve()),
                completed.stdout,
            )
            self.assertIn('--allow-secondary-failures', completed.stdout)
            self.assertIn('--output %s' % str(postgres_ga_output_path.resolve()), completed.stdout)
            self.assertNotIn('scripts/run_postgres_soak_validation.py', completed.stdout)
            self.assertNotIn('scripts/run_worker_ga_validation.py', completed.stdout)
            self.assertNotIn('scripts/run_review_queue_ga_validation.py', completed.stdout)
            self.assertNotIn('scripts/run_provider_ga_validation.py', completed.stdout)
            self.assertNotIn('scripts/run_calibration_ga_validation.py', completed.stdout)
            self.assertNotIn('scripts/run_roadmap_extension_validation.py', completed.stdout)

    def test_review_queue_ga_stage_forwards_review_queue_options(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            review_queue_output_path = Path(tmp_dir) / 'review-queue-ga-plan.json'
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--python',
                    'python3',
                    '--stages',
                    'review_queue_ga',
                    '--review-queue-ga-output',
                    str(review_queue_output_path),
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
            self.assertIn('Selected stages: review_queue_ga', completed.stdout)
            self.assertIn('scripts/run_review_queue_ga_validation.py', completed.stdout)
            self.assertIn('--python python3', completed.stdout)
            self.assertIn('--output %s' % str(review_queue_output_path.resolve()), completed.stdout)
            self.assertNotIn('scripts/run_ci.py', completed.stdout)
            self.assertNotIn('scripts/run_postgres_ga_validation.py', completed.stdout)
            self.assertNotIn('scripts/run_worker_ga_validation.py', completed.stdout)
            self.assertNotIn('scripts/run_provider_ga_validation.py', completed.stdout)
            self.assertNotIn('scripts/run_calibration_ga_validation.py', completed.stdout)
            self.assertNotIn('scripts/run_roadmap_extension_validation.py', completed.stdout)

    def test_provider_ga_stage_forwards_provider_options(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            provider_output_path = Path(tmp_dir) / 'provider-ga-plan.json'
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--python',
                    'python3',
                    '--stages',
                    'provider_ga',
                    '--provider-ga-output',
                    str(provider_output_path),
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
            self.assertIn('Selected stages: provider_ga', completed.stdout)
            self.assertIn('scripts/run_provider_ga_validation.py', completed.stdout)
            self.assertIn('--python python3', completed.stdout)
            self.assertIn('--output %s' % str(provider_output_path.resolve()), completed.stdout)
            self.assertNotIn('scripts/run_ci.py', completed.stdout)
            self.assertNotIn('scripts/run_postgres_ga_validation.py', completed.stdout)
            self.assertNotIn('scripts/run_worker_ga_validation.py', completed.stdout)
            self.assertNotIn('scripts/run_review_queue_ga_validation.py', completed.stdout)
            self.assertNotIn('scripts/run_postgres_soak_validation.py', completed.stdout)
            self.assertNotIn('scripts/run_calibration_ga_validation.py', completed.stdout)
            self.assertNotIn('scripts/run_roadmap_extension_validation.py', completed.stdout)

    def test_calibration_ga_stage_forwards_calibration_options(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            manifest_path = tmp_path / 'calibration-manifest.json'
            calibration_report_path = tmp_path / 'calibration-report.json'
            calibration_ga_output_path = tmp_path / 'calibration-ga-plan.json'
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--python',
                    'python3',
                    '--stages',
                    'calibration_ga',
                    '--calibration-manifest',
                    str(manifest_path),
                    '--calibration-report-output',
                    str(calibration_report_path),
                    '--calibration-margin',
                    '0.08',
                    '--calibration-fail-on-mismatch',
                    '--calibration-ga-output',
                    str(calibration_ga_output_path),
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
            self.assertIn('Selected stages: calibration_ga', completed.stdout)
            self.assertIn('scripts/run_calibration_ga_validation.py', completed.stdout)
            self.assertIn('--manifest %s' % str(manifest_path.resolve()), completed.stdout)
            self.assertIn(
                '--calibration-report-output %s' % str(calibration_report_path.resolve()),
                completed.stdout,
            )
            self.assertIn('--margin 0.08', completed.stdout)
            self.assertIn('--fail-on-mismatch', completed.stdout)
            self.assertIn('--output %s' % str(calibration_ga_output_path.resolve()), completed.stdout)
            self.assertNotIn('scripts/run_ci.py', completed.stdout)
            self.assertNotIn('scripts/run_postgres_ga_validation.py', completed.stdout)
            self.assertNotIn('scripts/run_provider_ga_validation.py', completed.stdout)
            self.assertNotIn('scripts/run_roadmap_extension_validation.py', completed.stdout)

    def test_roadmap_extension_stage_forwards_output_options(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            roadmap_output_path = Path(tmp_dir) / 'roadmap-extension-plan.json'
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--python',
                    'python3',
                    '--stages',
                    'roadmap_extension',
                    '--roadmap-extension-output',
                    str(roadmap_output_path),
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
            self.assertIn('Selected stages: roadmap_extension', completed.stdout)
            self.assertIn('scripts/run_roadmap_extension_validation.py', completed.stdout)
            self.assertIn('--python python3', completed.stdout)
            self.assertIn('--output %s' % str(roadmap_output_path.resolve()), completed.stdout)
            self.assertNotIn('scripts/run_ci.py', completed.stdout)
            self.assertNotIn('scripts/run_postgres_ga_validation.py', completed.stdout)
            self.assertNotIn('scripts/run_provider_ga_validation.py', completed.stdout)


if __name__ == '__main__':
    unittest.main()
