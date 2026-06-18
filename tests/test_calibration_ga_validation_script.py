from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / 'scripts' / 'ga_calibration.py'


class CalibrationGaValidationScriptTests(unittest.TestCase):
    def test_script_dry_run_emits_default_calibration_ga_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / 'calibration-ga-plan.json'
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
                'Selected stages: calibration_contract, review_policy_contract, calibration_report',
                completed.stdout,
            )
            self.assertIn(
                'tests.test_tune_review_policy.TuneReviewPolicyScriptTests.test_script_rejects_invalid_manifest',
                completed.stdout,
            )
            self.assertIn('tests.test_review_policy.ReviewPolicyTests', completed.stdout)
            self.assertIn('scripts/tune_review.py', completed.stdout)

            report = json.loads(output_path.read_text(encoding='utf-8'))
            self.assertEqual(report.get('stage_count'), 3)
            self.assertEqual(
                [item.get('name') for item in report.get('stages', [])],
                [
                    'calibration_contract',
                    'review_policy_contract',
                    'calibration_report',
                ],
            )

    def test_script_respects_stage_selection_and_calibration_options(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            manifest_path = tmp_path / 'manifest.json'
            calibration_report_path = tmp_path / 'calibration-report.json'
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--python',
                    'python3',
                    '--stages',
                    'calibration_report',
                    '--manifest',
                    str(manifest_path),
                    '--calibration-report-output',
                    str(calibration_report_path),
                    '--margin',
                    '0.08',
                    '--fail-on-mismatch',
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
            self.assertIn('Selected stages: calibration_report', completed.stdout)
            self.assertIn('scripts/tune_review.py', completed.stdout)
            self.assertIn('--manifest %s' % str(manifest_path.resolve()), completed.stdout)
            self.assertIn('--output %s' % str(calibration_report_path.resolve()), completed.stdout)
            self.assertIn('--margin 0.08', completed.stdout)
            self.assertIn('--fail-on-mismatch', completed.stdout)
            self.assertNotIn('tests.test_review_policy.ReviewPolicyTests', completed.stdout)
            self.assertNotIn(
                'tests.test_tune_review_policy.TuneReviewPolicyScriptTests.test_script_rejects_invalid_manifest',
                completed.stdout,
            )


if __name__ == '__main__':
    unittest.main()
