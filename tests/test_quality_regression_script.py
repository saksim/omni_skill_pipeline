from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / 'scripts' / 'quality_regression.py'


def _manifest_payload() -> dict[str, object]:
    return {
        'manifest_id': 'e11-quality-regression-test',
        'manifest_version': '1.0',
        'samples': [
            {
                'sample_id': 'S-TEXT-01',
                'modality': 'text',
                'baseline_metrics': {
                    'traceability_rate': 0.9,
                    'reviewer_edit_distance': {
                        'step_edits': 1,
                        'rule_edits': 0,
                        'verification_edits': 0,
                        'summary_rewritten': False,
                    },
                },
                'thresholds': {
                    'max_traceability_drop': 0.05,
                    'max_reviewer_edit_increase': 1,
                },
            },
            {
                'sample_id': 'S-VIDEO-01',
                'modality': 'video',
                'baseline_metrics': {
                    'traceability_rate': 0.4,
                    'reviewer_edit_distance': {
                        'step_edits': 3,
                        'rule_edits': 1,
                        'verification_edits': 1,
                        'summary_rewritten': True,
                    },
                },
                'thresholds': {
                    'max_traceability_drop': 0.08,
                    'max_reviewer_edit_increase': 2,
                },
            },
        ],
    }


class QualityRegressionScriptTests(unittest.TestCase):
    def test_script_smoke_compares_traceability_and_edit_distance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            manifest_path = tmp_path / 'manifest.json'
            candidate_path = tmp_path / 'candidate.json'
            output_path = tmp_path / 'quality-regression-report.json'
            manifest_path.write_text(json.dumps(_manifest_payload(), ensure_ascii=False, indent=2), encoding='utf-8')
            candidate_path.write_text(
                json.dumps(
                    {
                        'samples': [
                            {
                                'sample_id': 'S-TEXT-01',
                                'traceability_rate': 0.88,
                                'reviewer_edit_distance': {
                                    'step_edits': 1,
                                    'rule_edits': 0,
                                    'verification_edits': 0,
                                    'summary_rewritten': False,
                                },
                            },
                            {
                                'sample_id': 'S-VIDEO-01',
                                'traceability_rate': 0.37,
                                'reviewer_edit_distance': {
                                    'step_edits': 3,
                                    'rule_edits': 1,
                                    'verification_edits': 2,
                                    'summary_rewritten': True,
                                },
                            },
                        ]
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--manifest',
                    str(manifest_path),
                    '--candidate',
                    str(candidate_path),
                    '--output',
                    str(output_path),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Quality regression samples=2', completed.stdout)
            self.assertIn('Regressed samples: none', completed.stdout)
            payload = json.loads(output_path.read_text(encoding='utf-8'))
            self.assertEqual(payload.get('sample_count'), 2)
            self.assertEqual(payload.get('regressed_count'), 0)
            self.assertEqual(payload.get('compared_metrics'), ['traceability_rate', 'reviewer_edit_distance'])

    def test_script_fail_on_regression_returns_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            manifest_path = tmp_path / 'manifest.json'
            candidate_path = tmp_path / 'candidate.json'
            manifest_path.write_text(json.dumps(_manifest_payload(), ensure_ascii=False, indent=2), encoding='utf-8')
            candidate_path.write_text(
                json.dumps(
                    {
                        'samples': [
                            {
                                'sample_id': 'S-TEXT-01',
                                'traceability_rate': 0.81,
                                'reviewer_edit_distance': {
                                    'step_edits': 3,
                                    'rule_edits': 1,
                                    'verification_edits': 0,
                                    'summary_rewritten': False,
                                },
                            },
                            {
                                'sample_id': 'S-VIDEO-01',
                                'traceability_rate': 0.39,
                                'reviewer_edit_distance': {
                                    'step_edits': 3,
                                    'rule_edits': 1,
                                    'verification_edits': 1,
                                    'summary_rewritten': True,
                                },
                            },
                        ]
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding='utf-8',
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--manifest',
                    str(manifest_path),
                    '--candidate',
                    str(candidate_path),
                    '--output',
                    '-',
                    '--fail-on-regression',
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1)
            self.assertIn('Regressed samples: S-TEXT-01', completed.stdout)


if __name__ == '__main__':
    unittest.main()
