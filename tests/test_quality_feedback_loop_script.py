from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / 'scripts' / 'run_quality_feedback_loop.py'


def _build_bundle(skill_id: str, decision: str, status: str, reason_codes: list[str], quality_scores: dict[str, float]) -> dict[str, object]:
    return {
        'skill': {'skill_id': skill_id},
        'adapter_metadata': {
            'quality_scores': quality_scores,
            'review_feedback': {
                'review_task_id': 'task-%s' % skill_id,
                'skill_id': skill_id,
                'decision': decision,
                'status': status,
                'reason_codes': reason_codes,
                'categories': ['manual_review'],
                'atom_actions': [],
                'graph_actions': [],
                'policy_actions': [
                    {
                        'action_code': 'POLICY_ESCALATE_MANUAL_REVIEW',
                        'target': 'policy',
                        'intent': 'escalate_manual_review',
                        'reason_code': 'MANUAL_REVIEW_FALLBACK',
                        'params': {'priority': 'medium'},
                    }
                ],
                'revision_suggestions': ['S_MANUAL_REVIEW_REQUIRED'],
                'follow_up_checks': ['CHECK_MANUAL_REVIEW_OUTCOME'],
                'score_snapshot': {'overall_score': quality_scores.get('overall_score', 0.0)},
                'thresholds': {'auto_publish_min_overall': 0.82},
            },
            'review_task': {
                'review_task_id': 'task-%s' % skill_id,
                'skill_id': skill_id,
                'decision': decision,
                'status': status,
                'reason_codes': reason_codes,
            },
        },
    }


class QualityFeedbackLoopScriptTests(unittest.TestCase):
    def test_script_generates_feedback_loop_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bundle_a_path = tmp_path / 'bundle-a.json'
            bundle_b_path = tmp_path / 'bundle-b.json'
            bundle_a_path.write_text(
                json.dumps(
                    _build_bundle(
                        'skill-a',
                        'review_required',
                        'review_pending',
                        ['Q_TRACEABILITY_LOW'],
                        {
                            'traceability_score': 0.7,
                            'actionability_score': 0.75,
                            'coverage_score': 0.71,
                            'consistency_score': 0.78,
                            'noise_score': 0.72,
                            'novelty_score': 0.61,
                            'overall_score': 0.74,
                        },
                    ),
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding='utf-8',
            )
            bundle_b_path.write_text(
                json.dumps(
                    _build_bundle(
                        'skill-b',
                        'reject',
                        'rejected',
                        ['R_TRACEABILITY_CRITICAL'],
                        {
                            'traceability_score': 0.2,
                            'actionability_score': 0.25,
                            'coverage_score': 0.2,
                            'consistency_score': 0.27,
                            'noise_score': 0.2,
                            'novelty_score': 0.43,
                            'overall_score': 0.22,
                        },
                    ),
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding='utf-8',
            )
            run_report_path = tmp_path / 'controlled-trial-run-report.json'
            run_report_path.write_text(
                json.dumps(
                    {
                        'run_id': 'run-feedback-loop-test',
                        'samples': [
                            {
                                'sample_id': 'sample-a',
                                'modality': 'text',
                                'approved_bundle_path': str(bundle_a_path),
                                'loop_metrics': {
                                    'review_outcome': 'approved',
                                    'reviewer_edit_distance_pct': 33.0,
                                },
                            },
                            {
                                'sample_id': 'sample-b',
                                'modality': 'video',
                                'approved_bundle_path': str(bundle_b_path),
                                'loop_metrics': {
                                    'review_outcome': 'rejected',
                                    'reviewer_edit_distance_pct': 41.0,
                                },
                            },
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding='utf-8',
            )

            report_path = tmp_path / 'quality-feedback-loop-report.json'
            summary_path = tmp_path / 'quality-feedback-loop-summary.md'
            calibration_path = tmp_path / 'quality-feedback-loop-calibration-manifest.json'

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    '--run-report',
                    str(run_report_path),
                    '--output',
                    str(report_path),
                    '--summary-output',
                    str(summary_path),
                    '--calibration-output',
                    str(calibration_path),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('Quality feedback loop samples=2', completed.stdout)
            self.assertTrue(report_path.is_file())
            self.assertTrue(summary_path.is_file())
            self.assertTrue(calibration_path.is_file())

            report_payload = json.loads(report_path.read_text(encoding='utf-8'))
            self.assertEqual(report_payload.get('schema_version'), 'quality_feedback_loop.v1')
            self.assertEqual(report_payload.get('summary', {}).get('sample_count'), 2)
            self.assertEqual(report_payload.get('summary', {}).get('calibration_sample_count'), 2)
            self.assertTrue(report_payload.get('regression_cases'))

            calibration_payload = json.loads(calibration_path.read_text(encoding='utf-8'))
            self.assertEqual(calibration_payload.get('manifest_id'), 'quality-feedback-loop-calibration')
            self.assertEqual(len(calibration_payload.get('samples', [])), 2)

            summary_text = summary_path.read_text(encoding='utf-8')
            self.assertIn('Quality Feedback Loop Summary', summary_text)
            self.assertIn('Samples analyzed: `2`', summary_text)


if __name__ == '__main__':
    unittest.main()
